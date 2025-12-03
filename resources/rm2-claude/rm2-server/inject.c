/*
 * RM2 Injection Hook - Minimal Portable Version
 *
 * Single-file LD_PRELOAD hook for Remarkable 2 stylus input injection.
 * Reads PEN commands from FIFO and injects as synthetic Wacom events.
 *
 * Build: arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread
 * Deploy: scp inject.so root@10.11.99.1:/opt/
 *
 * Coordinate System:
 *   Wacom sensor:   X=0-20966, Y=0-15725 (hardware coordinates)
 *   Transformation: Swap X/Y + Flip Y (Transformation #6)
 *   PEN (x,y) -> Wacom: ABS_X = WACOM_MAX_Y - y, ABS_Y = x
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#include <linux/input.h>
#include <sys/stat.h>

#define WACOM_MAX_X 20966
#define WACOM_MAX_Y 15725

#define FIFO_PATH "/tmp/rm2_inject"
#define MAX_QUEUE 10000

// Transformation #6: Swap X/Y + Flip Y (fixes mirroring/rotation issue)
// PEN (x,y) -> Wacom: x_wacom = WACOM_MAX_Y - y, y_wacom = x
static inline int to_wacom_x(int x, int y) { return WACOM_MAX_Y - y; }
static inline int to_wacom_y(int x, int y) { return x; }

// Event creation
static struct input_event make_event(__u16 type, __u16 code, __s32 value) {
    struct input_event ev;
    memset(&ev, 0, sizeof(ev));
    ev.type = type;
    ev.code = code;
    ev.value = value;
    return ev;
}

// Global state
static ssize_t (*original_read)(int, void*, size_t) = NULL;
static int wacom_fd = -1;
static struct input_event queue[MAX_QUEUE];
static int q_head = 0, q_tail = 0;
static pthread_mutex_t q_lock = PTHREAD_MUTEX_INITIALIZER;

// Queue operations
static void enqueue(struct input_event ev) {
    pthread_mutex_lock(&q_lock);
    if ((q_tail + 1) % MAX_QUEUE != q_head) {
        queue[q_tail] = ev;
        q_tail = (q_tail + 1) % MAX_QUEUE;
    }
    pthread_mutex_unlock(&q_lock);
}

static int dequeue(struct input_event *ev) {
    pthread_mutex_lock(&q_lock);
    if (q_head == q_tail) {
        pthread_mutex_unlock(&q_lock);
        return 0;
    }
    *ev = queue[q_head];
    q_head = (q_head + 1) % MAX_QUEUE;
    pthread_mutex_unlock(&q_lock);
    return 1;
}

static int has_events(void) {
    pthread_mutex_lock(&q_lock);
    int result = (q_head != q_tail);
    pthread_mutex_unlock(&q_lock);
    return result;
}

// Check if fd is Wacom device
static int is_wacom(int fd) {
    char path[256], link[256], name[256];
    snprintf(path, sizeof(path), "/proc/self/fd/%d", fd);
    ssize_t len = readlink(path, link, sizeof(link) - 1);
    if (len == -1) return 0;
    link[len] = '\0';
    if (strncmp(link, "/dev/input/event", 16) != 0) return 0;
    if (ioctl(fd, EVIOCGNAME(sizeof(name)), name) < 0) return 0;
    return (strstr(name, "Wacom") != NULL);
}

// FIFO reader thread
static void* fifo_reader(void* arg) {
    (void)arg;
    fprintf(stderr, "[RM2] Injection hook active\n");

    mkfifo(FIFO_PATH, 0666);

    while (1) {
        int fd = open(FIFO_PATH, O_RDONLY);
        if (fd < 0) {
            sleep(1);
            continue;
        }

        char buf[4096];
        char leftover[256] = {0};
        ssize_t n;

        while ((n = read(fd, buf, sizeof(buf) - 1)) > 0) {
            buf[n] = '\0';

            // Combine leftover from previous read with new data
            char combined[4096 + 256];
            snprintf(combined, sizeof(combined), "%s%s", leftover, buf);
            leftover[0] = '\0';

            // Process all complete lines in the buffer
            char *line = combined;
            char *next_line;

            while ((next_line = strchr(line, '\n')) != NULL) {
                *next_line = '\0';  // Terminate current line

                char cmd[32];
                int x = 0, y = 0;

                if (sscanf(line, "%s %d %d", cmd, &x, &y) >= 1) {
                    if (strcmp(cmd, "PEN_DOWN") == 0) {
                        int wx = to_wacom_x(x, y);
                        int wy = to_wacom_y(x, y);

                        enqueue(make_event(EV_KEY, BTN_TOOL_PEN, 1));
                        enqueue(make_event(EV_KEY, BTN_TOUCH, 1));
                        enqueue(make_event(EV_ABS, ABS_X, wx));
                        enqueue(make_event(EV_ABS, ABS_Y, wy));
                        enqueue(make_event(EV_ABS, ABS_PRESSURE, 2000));
                        enqueue(make_event(EV_SYN, SYN_REPORT, 0));

                    } else if (strcmp(cmd, "PEN_MOVE") == 0) {
                        int wx = to_wacom_x(x, y);
                        int wy = to_wacom_y(x, y);

                        enqueue(make_event(EV_ABS, ABS_X, wx));
                        enqueue(make_event(EV_ABS, ABS_Y, wy));
                        enqueue(make_event(EV_ABS, ABS_PRESSURE, 2000));
                        enqueue(make_event(EV_SYN, SYN_REPORT, 0));

                    } else if (strcmp(cmd, "PEN_UP") == 0) {
                        enqueue(make_event(EV_KEY, BTN_TOUCH, 0));
                        enqueue(make_event(EV_KEY, BTN_TOOL_PEN, 0));
                        enqueue(make_event(EV_SYN, SYN_REPORT, 0));

                    } else if (strcmp(cmd, "DELAY") == 0) {
                        // DELAY command: sleep for specified milliseconds
                        // Format: DELAY <ms>
                        // This prevents stringing between distant strokes
                        int delay_ms = x;  // x contains the delay value
                        if (delay_ms > 0 && delay_ms <= 1000) {
                            usleep(delay_ms * 1000);  // Convert ms to microseconds
                        }
                    }
                }

                line = next_line + 1;  // Move to next line
            }

            // Save incomplete line for next read
            if (strlen(line) > 0 && strlen(line) < sizeof(leftover)) {
                strncpy(leftover, line, sizeof(leftover) - 1);
            }
        }

        close(fd);
    }

    return NULL;
}

// Hooked read() function
ssize_t read(int fd, void *buf, size_t count) {
    if (!original_read) {
        original_read = dlsym(RTLD_NEXT, "read");
    }

    // Detect Wacom device on first read
    if (wacom_fd == -1 && is_wacom(fd)) {
        wacom_fd = fd;
        fprintf(stderr, "[RM2] Wacom device detected (fd %d)\n", fd);

        pthread_t thread;
        pthread_create(&thread, NULL, fifo_reader, NULL);
        pthread_detach(thread);
    }

    // Inject queued events if available
    if (fd == wacom_fd && has_events()) {
        struct input_event *events = (struct input_event *)buf;
        int max_events = count / sizeof(struct input_event);
        int injected = 0;

        while (injected < max_events && dequeue(&events[injected])) {
            injected++;
        }

        if (injected > 0) {
            return injected * sizeof(struct input_event);
        }
    }

    // Call original read for real hardware events
    return original_read(fd, buf, count);
}

__attribute__((constructor))
static void init(void) {
    fprintf(stderr, "[RM2] Injection hook loaded\n");
}
