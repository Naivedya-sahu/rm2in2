/*
 * Test 1: Direct /dev/fb0 Manipulation
 *
 * Tests if we can write directly to framebuffer and if it displays
 * WITHOUT xochitl acknowledging it (visual test only)
 *
 * Compile: gcc -o test_fb0 01_test_fb0_direct.c
 * Run: ./test_fb0
 */

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <linux/fb.h>
#include <unistd.h>
#include <string.h>

#define FB_DEVICE "/dev/fb0"
#define WIDTH 1404
#define HEIGHT 1872

// MXCFB update structures
#define MXCFB_SEND_UPDATE 0x4048462E
#define WAVEFORM_MODE_GC16 2
#define UPDATE_MODE_PARTIAL 0

struct mxcfb_rect {
    uint32_t top;
    uint32_t left;
    uint32_t width;
    uint32_t height;
};

struct mxcfb_update_data {
    struct mxcfb_rect update_region;
    uint32_t waveform_mode;
    uint32_t update_mode;
    uint32_t update_marker;
    int temp;
    unsigned int flags;
    int dither_mode;
    int quant_bit;
    int alt_buffer_data;
};

void draw_rectangle(uint16_t *fb, int x, int y, int w, int h, uint16_t color) {
    for (int i = y; i < y + h && i < HEIGHT; i++) {
        for (int j = x; j < x + w && j < WIDTH; j++) {
            fb[i * WIDTH + j] = color;
        }
    }
}

void trigger_update(int fd, int x, int y, int w, int h) {
    struct mxcfb_update_data update = {0};
    update.update_region.top = y;
    update.update_region.left = x;
    update.update_region.width = w;
    update.update_region.height = h;
    update.waveform_mode = WAVEFORM_MODE_GC16;
    update.update_mode = UPDATE_MODE_PARTIAL;
    update.temp = 0x1018;
    update.update_marker = 1;
    update.flags = 0;

    if (ioctl(fd, MXCFB_SEND_UPDATE, &update) < 0) {
        perror("ioctl MXCFB_SEND_UPDATE failed");
    }
}

int main() {
    printf("Test 1: Direct /dev/fb0 Write\n");
    printf("==============================\n\n");

    int fd = open(FB_DEVICE, O_RDWR);
    if (fd < 0) {
        perror("Failed to open framebuffer");
        return 1;
    }

    struct fb_var_screeninfo vinfo;
    struct fb_fix_screeninfo finfo;

    if (ioctl(fd, FBIOGET_VSCREENINFO, &vinfo) < 0) {
        perror("Failed to get variable screen info");
        close(fd);
        return 1;
    }

    if (ioctl(fd, FBIOGET_FSCREENINFO, &finfo) < 0) {
        perror("Failed to get fixed screen info");
        close(fd);
        return 1;
    }

    printf("Screen Info:\n");
    printf("  Resolution: %dx%d\n", vinfo.xres, vinfo.yres);
    printf("  Bits per pixel: %d\n", vinfo.bits_per_pixel);
    printf("  Line length: %d\n", finfo.line_length);

    size_t screensize = vinfo.yres * finfo.line_length;

    uint16_t *fbp = (uint16_t *)mmap(0, screensize, PROT_READ | PROT_WRITE,
                                      MAP_SHARED, fd, 0);

    if (fbp == MAP_FAILED) {
        perror("Failed to mmap framebuffer");
        close(fd);
        return 1;
    }

    printf("\nDrawing test rectangles...\n");

    // Draw white rectangle (top-left)
    draw_rectangle(fbp, 50, 50, 200, 100, 0xFFFF);
    printf("  White rectangle at (50,50)\n");

    // Draw gray rectangle (top-right)
    draw_rectangle(fbp, 1150, 50, 200, 100, 0x7BEF);
    printf("  Gray rectangle at (1150,50)\n");

    // Draw black rectangle (bottom-left)
    draw_rectangle(fbp, 50, 1700, 200, 100, 0x0000);
    printf("  Black rectangle at (50,1700)\n");

    // Draw pattern (center)
    for (int i = 0; i < 10; i++) {
        draw_rectangle(fbp, 600 + i*15, 900 + i*15, 100, 10, 0x0000);
    }
    printf("  Pattern at center\n");

    printf("\nTriggering screen update...\n");
    trigger_update(fd, 0, 0, WIDTH, HEIGHT);

    printf("\n✓ Test complete!\n");
    printf("Check if rectangles are visible on screen.\n");
    printf("Press Ctrl+C when done viewing.\n");

    sleep(10);

    munmap(fbp, screensize);
    close(fd);

    return 0;
}
