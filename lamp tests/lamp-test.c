/*
 * lamp-test.c - Standalone test of lamp's coordinate transformation
 * 
 * This is a minimal implementation to test if lamp's proven coordinate
 * transformation works on firmware 3.23+/3.24+ without any dependencies.
 * 
 * NO rm2fb required. NO Toltec required. NO rmkit libraries required.
 * Just direct input event injection using lamp's battle-tested transform.
 * 
 * Compile: arm-linux-gnueabihf-gcc -o lamp-test lamp-test.c -lm -static
 * Deploy:  scp lamp-test root@10.11.99.1:/opt/
 * Run:     ssh root@10.11.99.1 /opt/lamp-test
 *          Then tap pen on screen to trigger render
 */

#include <linux/input.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

// lamp's proven coordinate transformation (from rmkit)
// These values are CORRECT and battle-tested by rmkit community
#define WACOMWIDTH 15725.0
#define WACOMHEIGHT 20967.0
#define DISPLAYWIDTH 1404.0
#define DISPLAYHEIGHT 1872.0

#define WACOM_X_SCALAR ((float)DISPLAYWIDTH / (float)WACOMWIDTH)
#define WACOM_Y_SCALAR ((float)DISPLAYHEIGHT / (float)WACOMHEIGHT)

// Display coordinates -> Wacom sensor coordinates
// Note the axis swap: Display X -> Wacom Y, Display Y -> Wacom X
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
    ev[2].type = EV_ABS; ev[2].code = ABS_Y; ev[2].value = get_pen_x(x);  // X -> Y axis
    ev[3].type = EV_ABS; ev[3].code = ABS_X; ev[3].value = get_pen_y(y);  // Y -> X axis
    ev[4].type = EV_ABS; ev[4].code = ABS_DISTANCE; ev[4].value = 0;
    ev[5].type = EV_ABS; ev[5].code = ABS_PRESSURE; ev[5].value = 4000;
    ev[6].type = EV_SYN; ev[6].code = SYN_REPORT; ev[6].value = 1;
    
    write(fd, ev, sizeof(ev));
}

void pen_move(int fd, int x, int y) {
    struct input_event ev[3];
    memset(ev, 0, sizeof(ev));
    
    ev[0].type = EV_ABS; ev[0].code = ABS_Y; ev[0].value = get_pen_x(x);  // X -> Y axis
    ev[1].type = EV_ABS; ev[1].code = ABS_X; ev[1].value = get_pen_y(y);  // Y -> X axis
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

void draw_circle(int fd, int cx, int cy, int radius) {
    int points = 100;
    double angle_step = 2.0 * M_PI / points;
    
    printf("Drawing circle: center (%d, %d), radius %d\n", cx, cy, radius);
    printf("Wacom coordinates: center (%d, %d)\n", 
           get_pen_x(cx), get_pen_y(cy));
    
    // Start at first point
    int x = cx + radius;
    int y = cy;
    pen_down(fd, x, y);
    usleep(1000);
    
    // Draw circle
    for (int i = 1; i <= points; i++) {
        double angle = i * angle_step;
        x = cx + (int)(radius * cos(angle));
        y = cy + (int)(radius * sin(angle));
        pen_move(fd, x, y);
        usleep(1000);
    }
    
    pen_up(fd);
    printf("Circle complete!\n");
}

void draw_rectangle(int fd, int x1, int y1, int x2, int y2) {
    printf("Drawing rectangle: (%d, %d) to (%d, %d)\n", x1, y1, x2, y2);
    
    pen_down(fd, x1, y1);
    usleep(10000);
    
    pen_move(fd, x1, y2);
    usleep(10000);
    
    pen_move(fd, x2, y2);
    usleep(10000);
    
    pen_move(fd, x2, y1);
    usleep(10000);
    
    pen_move(fd, x1, y1);
    usleep(10000);
    
    pen_up(fd);
    printf("Rectangle complete!\n");
}

void draw_cross(int fd, int cx, int cy, int size) {
    printf("Drawing cross at center (%d, %d), size %d\n", cx, cy, size);
    
    // Vertical line
    pen_down(fd, cx, cy - size);
    usleep(10000);
    pen_move(fd, cx, cy + size);
    usleep(10000);
    pen_up(fd);
    
    usleep(50000);
    
    // Horizontal line
    pen_down(fd, cx - size, cy);
    usleep(10000);
    pen_move(fd, cx + size, cy);
    usleep(10000);
    pen_up(fd);
    
    printf("Cross complete!\n");
}

int main(int argc, char **argv) {
    printf("=== lamp-test: Coordinate Transformation Test ===\n");
    printf("Display: %dx%d\n", (int)DISPLAYWIDTH, (int)DISPLAYHEIGHT);
    printf("Wacom:   %dx%d\n", (int)WACOMWIDTH, (int)WACOMHEIGHT);
    printf("Scalars: X=%.6f, Y=%.6f\n", WACOM_X_SCALAR, WACOM_Y_SCALAR);
    printf("\n");
    
    int fd = open("/dev/input/event1", O_RDWR);
    if (fd < 0) {
        printf("ERROR: Cannot open /dev/input/event1\n");
        printf("Make sure you have write access to input devices.\n");
        return 1;
    }
    
    printf("Opened /dev/input/event1 successfully\n");
    printf("\n");
    
    // Test pattern 1: Circle at center
    printf("Test 1: Circle at center\n");
    draw_circle(fd, 702, 936, 200);
    sleep(1);
    
    // Test pattern 2: Rectangle
    printf("\nTest 2: Rectangle (100,100) to (1300,1700)\n");
    draw_rectangle(fd, 100, 100, 1300, 1700);
    sleep(1);
    
    // Test pattern 3: Cross at center
    printf("\nTest 3: Cross at center\n");
    draw_cross(fd, 702, 936, 300);
    sleep(1);
    
    // Test pattern 4: Four corners
    printf("\nTest 4: Four corner dots\n");
    int corner_size = 50;
    
    // Top-left
    draw_circle(fd, corner_size, corner_size, 30);
    usleep(500000);
    
    // Top-right
    draw_circle(fd, 1404 - corner_size, corner_size, 30);
    usleep(500000);
    
    // Bottom-left
    draw_circle(fd, corner_size, 1872 - corner_size, 30);
    usleep(500000);
    
    // Bottom-right
    draw_circle(fd, 1404 - corner_size, 1872 - corner_size, 30);
    usleep(500000);
    
    printf("\n=== All tests complete! ===\n");
    printf("Tap pen on screen to trigger render.\n");
    printf("Expected results:\n");
    printf("  - Circle should be ROUND (not oval)\n");
    printf("  - Rectangle should be rectangular\n");
    printf("  - Cross should be centered\n");
    printf("  - Corner dots should appear at corners\n");
    
    close(fd);
    return 0;
}
