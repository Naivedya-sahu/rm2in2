/*
 * RM2 Input Injection - Minimal Testing Version
 *
 * This is a TESTING version with NO coordinate transformation.
 * It passes PEN command coordinates directly to the Wacom device.
 *
 * Use this with test_transformations.py to empirically determine
 * the correct coordinate transformation.
 *
 * Build:
 *   arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread
 *
 * Deploy:
 *   scp inject.so root@10.11.99.1:/opt/
 *
 * Enable:
 *   ssh root@10.11.99.1
 *   systemctl stop xochitl
 *   LD_PRELOAD=/opt/inject.so /usr/bin/xochitl &
 *
 * Send commands:
 *   cat commands.txt > /tmp/rm2_inject
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

#define FIFO_PATH "/tmp/rm2_inject"
#define MAX_QUEUE 10000

// Wacom hardware limits (for validation only)
#define WACOM_MAX_X 20966
#define WACOM_MAX_Y 15725

/* ============================================================================
 * COORDINATE TRANSFORMATION
 * ============================================================================
 *
 * VERIFIED TRANSFORMATION (from captured pen events)
 *
 * Display coordinates (portrait 1404×1872) → Wacom sensor (20966×15725)
 *
 * The Wacom sensor is rotated 90° relative to the display AND vertically flipped:
 *   - Display X (horizontal) → Sensor Y
 *   - Display Y (vertical) → Inverted Sensor X
 *
 * Test results that confirmed this:
 *   Display Top-Left (0,0) → Sensor (20820, 90)
 *   Display Top-Right (1404,0) → Sensor (20822, 15551)
 *   Display Bottom-Left (0,1872) → Sensor (211, 138)
 *   Display Bottom-Right (1404,1872) → Sensor (269, 15712)
 *   Display Center (702,936) → Sensor (10875, 7366)
 */

#define DISPLAY_WIDTH 1404
#define DISPLAY_HEIGHT 1872

static inline int to_wacom_x(int pen_x, int pen_y) {
    // Display Y maps to inverted Sensor X
    return WACOM_MAX_X - (pen_y * WACOM_MAX_X / DISPLAY_HEIGHT);
}

static inline int to_wacom_y(int pen_x, int pen_y) {
    // Display X maps to Sensor Y
    return pen_x * WACOM_MAX_Y / DISPLAY_WIDTH;
}

/* ============================================================================
 * EVENT QUEUE
 * ============================================================================ */

static struct input_event queue[MAX_QUEUE];
static int q_head = 0;
static int q_tail = 0;
static pthread_mutex_t q_lock = PTHREAD_MUTEX_INITIALIZER;

static struct input_event make_event(__u16 type, __u16 code, __s32 value) {
    struct input_event ev;
    memset(&ev, 0, sizeof(ev));
    ev.type = type;
    ev.code = code;
    ev.value = value;
    return ev;
}

static void enqueue(struct input_event ev) {
    pthread_mutex_lock(&q_lock);
    if ((q_tail + 1) % MAX_QUEUE != q_head) {
        queue[q_tail] = ev;
        q_tail = (q_tail + 1) % MAX_QUEUE;
    } else {
        fprintf(stderr, "[RM2] WARNING: Queue full, dropping event\n");
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

/* ============================================================================
 * WACOM DEVICE DETECTION
 * ============================================================================ */

static int is_wacom(int fd) {
    char path[256], link[256], name[256];

    snprintf(path, sizeof(path), "/proc/self/fd/%d", fd);
    ssize_t len = readlink(path, link, sizeof(link) - 1);

    if (len == -1) return 0;
    link[len] = '\0';

    // Check if it's an input device
    if (strncmp(link, "/dev/input/event", 16) != 0) return 0;

    // Check device name contains "Wacom"
    if (ioctl(fd, EVIOCGNAME(sizeof(name)), name) < 0) return 0;

    return (strstr(name, "Wacom") != NULL);
}

/* ============================================================================
 * FIFO COMMAND READER
 * ============================================================================ */

static void* fifo_reader(void* arg) {
    (void)arg;

    fprintf(stderr, "[RM2] Injection hook active - TESTING MODE (no transform)\n");
    fprintf(stderr, "[RM2] FIFO: %s\n", FIFO_PATH);

    // Create FIFO if it doesn't exist
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

            // Combine leftover with new data
            char combined[4096 + 256];
            snprintf(combined, sizeof(combined), "%s%s", leftover, buf);
            leftover[0] = '\0';

            // Process complete lines
            char *line = combined;
            char *next_line;

            while ((next_line = strchr(line, '\n')) != NULL) {
                *next_line = '\0';

                // Skip comments and empty lines
                if (line[0] == '#' || line[0] == '\0') {
                    line = next_line + 1;
                    continue;
                }

                char cmd[32];
                int x = 0, y = 0;

                if (sscanf(line, "%s %d %d", cmd, &x, &y) >= 1) {

                    if (strcmp(cmd, "PEN_DOWN") == 0) {
                        int wx = to_wacom_x(x, y);
                        int wy = to_wacom_y(x, y);

                        // Validate coordinates
                        if (wx < 0 || wx > WACOM_MAX_X || wy < 0 || wy > WACOM_MAX_Y) {
                            fprintf(stderr, "[RM2] WARNING: Coordinates out of bounds: (%d, %d)\n", wx, wy);
                        }

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
                        int delay_ms = x;
                        if (delay_ms > 0 && delay_ms <= 1000) {
                            usleep(delay_ms * 1000);
                        }
                    }
                }

                line = next_line + 1;
            }

            // Save incomplete line
            if (strlen(line) > 0 && strlen(line) < sizeof(leftover)) {
                strncpy(leftover, line, sizeof(leftover) - 1);
            }
        }

        close(fd);
    }

    return NULL;
}

/* ============================================================================
 * READ() HOOK
 * ============================================================================ */

static ssize_t (*original_read)(int, void*, size_t) = NULL;
static int wacom_fd = -1;

ssize_t read(int fd, void *buf, size_t count) {
    if (!original_read) {
        original_read = dlsym(RTLD_NEXT, "read");
    }

    // Detect Wacom device on first read
    if (wacom_fd == -1 && is_wacom(fd)) {
        wacom_fd = fd;
        fprintf(stderr, "[RM2] Wacom device detected (fd %d)\n", fd);

        // Start FIFO reader thread
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

    // Fall through to real hardware
    return original_read(fd, buf, count);
}

/* ============================================================================
 * INITIALIZATION
 * ============================================================================ */

__attribute__((constructor))
static void init(void) {
    fprintf(stderr, "[RM2] Injection hook loaded - TESTING VERSION\n");
    fprintf(stderr, "[RM2] This version has NO coordinate transformation\n");
    fprintf(stderr, "[RM2] Use with test_transformations.py to find correct transform\n");
}
