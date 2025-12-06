/*
 * lamp-test-v2.c - Improved version with adaptive interpolation
 * 
 * Fixes the "large circles skewed" issue by using adaptive interpolation
 * based on actual distance traveled, not fixed point count.
 * 
 * Target: ~5 pixels between interpolation points for smooth curves
 * 
 * Compile: arm-linux-gnueabihf-gcc -o lamp-test-v2 lamp-test-v2.c -lm -static
 */

#include <linux/input.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

#define WACOMWIDTH 15725.0
#define WACOMHEIGHT 20967.0
#define DISPLAYWIDTH 1404.0
#define DISPLAYHEIGHT 1872.0
#define WACOM_X_SCALAR ((float)DISPLAYWIDTH / (float)WACOMWIDTH)
#define WACOM_Y_SCALAR ((float)DISPLAYHEIGHT / (float)WACOMHEIGHT)

// Target distance between interpolation points (pixels)
#define TARGET_STEP_SIZE 5.0

int get_pen_x(int x) {
    return (int)(x / WACOM_X_SCALAR);
}

int get_pen_y(int y) {
    return (int)(WACOMHEIGHT - (y / WACOM_Y_SCALAR));
}

void pen_down(int fd, int x, int y) {
    struct input_event ev[7];
    memset(ev, 0, sizeof(ev));
    
    ev[0].type = EV_KEY; ev[0].code = BTN_TOOL_PEN; ev[0].value = 1;
    ev[1].type = EV_KEY; ev[1].code = BTN_TOUCH; ev[1].value = 1;
    ev[2].type = EV_ABS; ev[2].code = ABS_Y; ev[2].value = get_pen_x(x);
    ev[3].type = EV_ABS; ev[3].code = ABS_X; ev[3].value = get_pen_y(y);
    ev[4].type = EV_ABS; ev[4].code = ABS_DISTANCE; ev[4].value = 0;
    ev[5].type = EV_ABS; ev[5].code = ABS_PRESSURE; ev[5].value = 4000;
    ev[6].type = EV_SYN; ev[6].code = SYN_REPORT; ev[6].value = 1;
    
    write(fd, ev, sizeof(ev));
}

void pen_move(int fd, int x, int y) {
    struct input_event ev[3];
    memset(ev, 0, sizeof(ev));
    
    ev[0].type = EV_ABS; ev[0].code = ABS_Y; ev[0].value = get_pen_x(x);
    ev[1].type = EV_ABS; ev[1].code = ABS_X; ev[1].value = get_pen_y(y);
    ev[2].type = EV_SYN; ev[2].code = SYN_REPORT; ev[2].value = 1;
    
    write(fd, ev, sizeof(ev));
}

void pen_up(int fd) {
    struct input_event ev[3];
    memset(ev, 0, sizeof(ev));
    
    ev[0].type = EV_KEY; ev[0].code = BTN_TOOL_PEN; ev[0].value = 0;
    ev[1].type = EV_KEY; ev[1].code = BTN_TOUCH; ev[1].value = 0;
    ev[2].type = EV_SYN; ev[2].code = SYN_REPORT; ev[2].value = 1;
    
    write(fd, ev, sizeof(ev));
}

// Calculate optimal number of interpolation points based on distance
int calculate_interpolation_points(double distance) {
    int points = (int)(distance / TARGET_STEP_SIZE);
    
    // Minimum points for very short lines
    if (points < 10) points = 10;
    
    // Maximum to prevent excessive processing
    if (points > 1000) points = 1000;
    
    return points;
}

void draw_line_interpolated(int fd, int x1, int y1, int x2, int y2) {
    int dx = x2 - x1;
    int dy = y2 - y1;
    double distance = sqrt(dx*dx + dy*dy);
    int points = calculate_interpolation_points(distance);
    
    printf("  Line (%d,%d)->(%d,%d): dist=%.1f, points=%d (%.2fpx/point)\n",
           x1, y1, x2, y2, distance, points, distance/points);
    
    pen_down(fd, x1, y1);
    usleep(1000);
    
    for (int i = 1; i <= points; i++) {
        float t = (float)i / points;
        int x = x1 + (int)(t * dx);
        int y = y1 + (int)(t * dy);
        pen_move(fd, x, y);
        usleep(500);
    }
    
    pen_up(fd);
}

void draw_circle_adaptive(int fd, int cx, int cy, int radius) {
    // Calculate circumference
    double circumference = 2.0 * M_PI * radius;
    
    // Adaptive point count based on circumference
    int points = calculate_interpolation_points(circumference);
    double angle_step = 2.0 * M_PI / points;
    
    printf("  Circle center=(%d,%d) radius=%d: circum=%.1f, points=%d (%.2fpx/point)\n",
           cx, cy, radius, circumference, points, circumference/points);
    
    // Start at first point
    int x = cx + radius;
    int y = cy;
    pen_down(fd, x, y);
    usleep(1000);
    
    // Draw circle with adaptive interpolation
    for (int i = 1; i <= points; i++) {
        double angle = i * angle_step;
        x = cx + (int)(radius * cos(angle));
        y = cy + (int)(radius * sin(angle));
        pen_move(fd, x, y);
        usleep(500);
    }
    
    pen_up(fd);
}

void draw_rectangle_adaptive(int fd, int x1, int y1, int x2, int y2) {
    printf("  Rectangle (%d,%d) to (%d,%d)\n", x1, y1, x2, y2);
    
    // Draw four sides with interpolation
    draw_line_interpolated(fd, x1, y1, x1, y2);
    usleep(10000);
    draw_line_interpolated(fd, x1, y2, x2, y2);
    usleep(10000);
    draw_line_interpolated(fd, x2, y2, x2, y1);
    usleep(10000);
    draw_line_interpolated(fd, x2, y1, x1, y1);
}

void draw_cross_adaptive(int fd, int cx, int cy, int size) {
    printf("  Cross at (%d,%d) size=%d\n", cx, cy, size);
    
    // Vertical line
    draw_line_interpolated(fd, cx, cy - size, cx, cy + size);
    usleep(50000);
    
    // Horizontal line
    draw_line_interpolated(fd, cx - size, cy, cx + size, cy);
}

int main(int argc, char **argv) {
    printf("=== lamp-test-v2: Adaptive Interpolation Test ===\n");
    printf("Display: %dx%d\n", (int)DISPLAYWIDTH, (int)DISPLAYHEIGHT);
    printf("Wacom:   %dx%d\n", (int)WACOMWIDTH, (int)WACOMHEIGHT);
    printf("Target step size: %.1f pixels\n", TARGET_STEP_SIZE);
    printf("\n");
    
    int fd = open("/dev/input/event1", O_RDWR);
    if (fd < 0) {
        printf("ERROR: Cannot open /dev/input/event1\n");
        return 1;
    }
    
    printf("Opened /dev/input/event1 successfully\n\n");
    
    // Test 1: Circles of various sizes
    printf("Test 1: Circles with adaptive interpolation\n");
    
    printf("Small circle (r=50):\n");
    draw_circle_adaptive(fd, 350, 450, 50);
    sleep(1);
    
    printf("Medium circle (r=150):\n");
    draw_circle_adaptive(fd, 700, 900, 150);
    sleep(1);
    
    printf("Large circle (r=300):\n");
    draw_circle_adaptive(fd, 1050, 1350, 300);
    sleep(1);
    
    // Test 2: Rectangle with interpolated edges
    printf("\nTest 2: Rectangle with adaptive interpolation\n");
    draw_rectangle_adaptive(fd, 100, 100, 1300, 1700);
    sleep(1);
    
    // Test 3: Cross with interpolated lines
    printf("\nTest 3: Cross with adaptive interpolation\n");
    draw_cross_adaptive(fd, 702, 936, 300);
    sleep(1);
    
    // Test 4: Diagonal lines of various lengths
    printf("\nTest 4: Diagonal lines (testing distance calculation)\n");
    
    printf("Short diagonal:\n");
    draw_line_interpolated(fd, 100, 1700, 300, 1500);
    usleep(500000);
    
    printf("Medium diagonal:\n");
    draw_line_interpolated(fd, 400, 1700, 800, 1300);
    usleep(500000);
    
    printf("Long diagonal:\n");
    draw_line_interpolated(fd, 900, 1700, 1300, 100);
    usleep(500000);
    
    printf("\n=== All tests complete! ===\n");
    printf("\nExpected improvements over v1:\n");
    printf("  ✓ Large circles should have endpoints meeting\n");
    printf("  ✓ All circles should be round (not oval/skewed)\n");
    printf("  ✓ Long lines should be smooth\n");
    printf("  ✓ No jagged edges on large shapes\n");
    printf("\nCheck the rendered output on the RM2 screen.\n");
    
    close(fd);
    return 0;
}
