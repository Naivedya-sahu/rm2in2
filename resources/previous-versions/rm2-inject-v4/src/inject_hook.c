#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <linux/input.h>
#include <sys/stat.h>
#include <errno.h>
#include <pthread.h>
#include <time.h>

/*
 * RM2 Injection Hook - Corrected Coordinate Mapping
 *
 * Display coordinates (user perspective):
 *   Origin (0,0) at top-left
 *   X: 0-1404 (width, left to right)
 *   Y: 0-1872 (height, top to bottom)
 *
 * Wacom digitizer coordinates (hardware):
 *   Different axis orientation: rotated 90 degrees
 *   Range: X=0-15725, Y=0-20967
 *   Axis mapping: Display X → Wacom Y, Display Y → Wacom X
 *   No inversion needed (hardware calibration handles orientation)
 */

#define WACOM_MAX_X 15725  // Wacom X max (portrait mode)
#define WACOM_MAX_Y 20967  // Wacom Y max (portrait mode)

#define RM2_WIDTH  1404    // Display width (pixels)
#define RM2_HEIGHT 1872    // Display height (pixels)

/*
 * Coordinate transformation:
 * Convert display coordinates to Wacom digitizer coordinates
 *
 * Display (0,0) is top-left
 * Wacom has rotated axes (90-degree rotation)
 *
 * Mapping:
 *   Display X (0-1404) → scales to Wacom Y (0-20967)
 *   Display Y (0-1872) → scales to Wacom X (0-15725)
 */
static inline int display_to_wacom_x(int display_x) {
    // Display X maps to Wacom Y (vertical axis)
    return (int)((long)display_x * WACOM_MAX_Y / RM2_WIDTH);
}

static inline int display_to_wacom_y(int display_y) {
    // Display Y maps to Wacom X (horizontal axis)
    return (int)((long)display_y * WACOM_MAX_X / RM2_HEIGHT);
}

static inline struct input_event make_event(__u16 type, __u16 code, __s32 value) {
    struct input_event ev;
    memset(&ev, 0, sizeof(ev));
    ev.type = type;
    ev.code = code;
    ev.value = value;
    return ev;
}

static ssize_t (*original_read)(int fd, void *buf, size_t count) = NULL;

static int wacom_fd = -1;
static int last_pen_x = 0;
static int last_pen_y = 0;

#define MAX_QUEUE_SIZE 10000
static struct input_event event_queue[MAX_QUEUE_SIZE];
static int queue_head = 0;
static int queue_tail = 0;
static pthread_mutex_t queue_mutex = PTHREAD_MUTEX_INITIALIZER;

#define INJECT_FIFO "/tmp/lamp_inject"
#define SUPPRESSION_MS 150

static struct timespec last_injection_time = {0, 0};
static int suppress_input = 0;

static void get_current_time(struct timespec *ts) {
    clock_gettime(CLOCK_MONOTONIC, ts);
}

static long timediff_ms(struct timespec *start, struct timespec *end) {
    return (end->tv_sec - start->tv_sec) * 1000 + 
           (end->tv_nsec - start->tv_nsec) / 1000000;
}

static int is_wacom_device(int fd) {
    char path[256], link[256], name[256];
    snprintf(path, sizeof(path), "/proc/self/fd/%d", fd);
    
    ssize_t len = readlink(path, link, sizeof(link) - 1);
    if (len == -1) return 0;
    link[len] = '\0';
    
    if (strncmp(link, "/dev/input/event", 16) != 0) return 0;
    if (ioctl(fd, EVIOCGNAME(sizeof(name)), name) < 0) return 0;
    
    return (strstr(name, "Wacom") != NULL);
}

static void queue_event(struct input_event *ev) {
    pthread_mutex_lock(&queue_mutex);
    
    if ((queue_tail + 1) % MAX_QUEUE_SIZE == queue_head) {
        fprintf(stderr, "[INJECT] Queue full, dropping event\n");
        pthread_mutex_unlock(&queue_mutex);
        return;
    }
    
    event_queue[queue_tail] = *ev;
    queue_tail = (queue_tail + 1) % MAX_QUEUE_SIZE;
    
    pthread_mutex_unlock(&queue_mutex);
}

static int queue_has_events(void) {
    pthread_mutex_lock(&queue_mutex);
    int has = (queue_head != queue_tail);
    pthread_mutex_unlock(&queue_mutex);
    return has;
}

static int dequeue_event(struct input_event *ev) {
    pthread_mutex_lock(&queue_mutex);
    
    if (queue_head == queue_tail) {
        pthread_mutex_unlock(&queue_mutex);
        return 0;
    }
    
    *ev = event_queue[queue_head];
    queue_head = (queue_head + 1) % MAX_QUEUE_SIZE;
    
    pthread_mutex_unlock(&queue_mutex);
    return 1;
}

static void track_stylus_position(struct input_event *events, int count) {
    for (int i = 0; i < count; i++) {
        if (events[i].type == EV_ABS) {
            if (events[i].code == ABS_X) {
                last_pen_x = events[i].value;
            } else if (events[i].code == ABS_Y) {
                last_pen_y = events[i].value;
            }
        }
    }
}

static void* fifo_reader_thread(void* arg) {
    fprintf(stderr, "[INJECT] Hook initialized, waiting for commands\n");
    
    // Create FIFO if it doesn't exist
    // (may already exist from server startup)
    mkfifo(INJECT_FIFO, 0666);
    
    while (1) {
        int fd = open(INJECT_FIFO, O_RDONLY);
        if (fd < 0) {
            sleep(1);
            continue;
        }
        
        char buf[4096];
        ssize_t n;
        
        while ((n = read(fd, buf, sizeof(buf) - 1)) > 0) {
            buf[n] = '\0';
            
            char cmd[32];
            int x, y;
            
            if (sscanf(buf, "%s %d %d", cmd, &x, &y) >= 1) {
                
                if (strcmp(cmd, "PEN_DOWN") == 0) {
                    struct input_event ev;
                    
                    // Convert display coords to Wacom coords
                    int wacom_x = display_to_wacom_x(x);
                    int wacom_y = display_to_wacom_y(y);
                    
                    // Pen tool detection
                    ev = make_event(EV_KEY, BTN_TOOL_PEN, 1);
                    queue_event(&ev);
                    
                    // Touch detection
                    ev = make_event(EV_KEY, BTN_TOUCH, 1);
                    queue_event(&ev);
                    
                    // Position (direct mapping, no additional swap)
                    ev = make_event(EV_ABS, ABS_X, wacom_x);
                    queue_event(&ev);
                    
                    ev = make_event(EV_ABS, ABS_Y, wacom_y);
                    queue_event(&ev);
                    
                    // Pressure
                    ev = make_event(EV_ABS, ABS_PRESSURE, 2000);
                    queue_event(&ev);
                    
                    // Sync
                    ev = make_event(EV_SYN, SYN_REPORT, 0);
                    queue_event(&ev);
                    
                    get_current_time(&last_injection_time);
                    suppress_input = 1;
                    
                } else if (strcmp(cmd, "PEN_MOVE") == 0) {
                    struct input_event ev;
                    
                    int wacom_x = display_to_wacom_x(x);
                    int wacom_y = display_to_wacom_y(y);
                    
                    // Position
                    ev = make_event(EV_ABS, ABS_X, wacom_x);
                    queue_event(&ev);
                    
                    ev = make_event(EV_ABS, ABS_Y, wacom_y);
                    queue_event(&ev);
                    
                    // Pressure
                    ev = make_event(EV_ABS, ABS_PRESSURE, 2000);
                    queue_event(&ev);
                    
                    // Sync
                    ev = make_event(EV_SYN, SYN_REPORT, 0);
                    queue_event(&ev);
                    
                } else if (strcmp(cmd, "PEN_UP") == 0) {
                    struct input_event ev;
                    
                    // Release touch
                    ev = make_event(EV_KEY, BTN_TOUCH, 0);
                    queue_event(&ev);
                    
                    // Release tool
                    ev = make_event(EV_KEY, BTN_TOOL_PEN, 0);
                    queue_event(&ev);
                    
                    // Sync
                    ev = make_event(EV_SYN, SYN_REPORT, 0);
                    queue_event(&ev);
                    
                    get_current_time(&last_injection_time);
                    
                } else if (strcmp(cmd, "GET_CURSOR") == 0) {
                    fprintf(stderr, "[INJECT] Wacom cursor: X=%d Y=%d\n", last_pen_x, last_pen_y);
                }
            }
        }
        
        close(fd);
    }
    
    return NULL;
}

ssize_t read(int fd, void *buf, size_t count) {
    if (!original_read) {
        original_read = dlsym(RTLD_NEXT, "read");
    }
    
    // Detect Wacom device on first read
    if (wacom_fd == -1 && is_wacom_device(fd)) {
        wacom_fd = fd;
        fprintf(stderr, "[INJECT] Wacom device detected (fd %d)\n", fd);
        
        // Start FIFO reader thread
        pthread_t thread;
        pthread_create(&thread, NULL, fifo_reader_thread, NULL);
        pthread_detach(thread);
    }
    
    // Inject queued events if we have any
    if (fd == wacom_fd && queue_has_events()) {
        struct input_event *events = (struct input_event *)buf;
        int max_events = count / sizeof(struct input_event);
        int injected = 0;
        
        // Dequeue all available events
        while (injected < max_events && dequeue_event(&events[injected])) {
            injected++;
        }
        
        if (injected > 0) {
            return injected * sizeof(struct input_event);
        }
    }
    
    // Call original read for real hardware events
    ssize_t result = original_read(fd, buf, count);
    
    // Handle input suppression and tracking
    if (fd == wacom_fd && result > 0) {
        // Suppress real input during injection window
        if (suppress_input) {
            struct timespec now;
            get_current_time(&now);
            
            if (timediff_ms(&last_injection_time, &now) > SUPPRESSION_MS) {
                suppress_input = 0;
            } else {
                // Drop this event (return 0 bytes read)
                return 0;
            }
        }
        
        // Track stylus position for GET_CURSOR command
        int event_count = result / sizeof(struct input_event);
        track_stylus_position((struct input_event *)buf, event_count);
    }
    
    return result;
}

__attribute__((constructor))
static void init(void) {
    fprintf(stderr, "[INJECT] LD_PRELOAD hook loaded successfully\n");
}
