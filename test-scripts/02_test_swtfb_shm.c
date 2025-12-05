/*
 * Test 2: Shared Memory Framebuffer (/dev/shm/swtfb.01)
 *
 * Tests writing to the shared memory framebuffer used by rm2fb
 * This is what community apps use instead of /dev/fb0
 *
 * Compile: gcc -o test_swtfb 02_test_swtfb_shm.c
 * Run: ./test_swtfb
 */

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <string.h>

#define SWTFB_PATH "/dev/shm/swtfb.01"
#define WIDTH 1404
#define HEIGHT 1872
#define BPP 2  // 16-bit color

void draw_test_pattern(uint16_t *fb) {
    // Top-left corner - white square
    for (int y = 10; y < 110; y++) {
        for (int x = 10; x < 110; x++) {
            fb[y * WIDTH + x] = 0xFFFF;
        }
    }

    // Top-right corner - gray square
    for (int y = 10; y < 110; y++) {
        for (int x = WIDTH - 110; x < WIDTH - 10; x++) {
            fb[y * WIDTH + x] = 0x7BEF;
        }
    }

    // Bottom-left corner - black square
    for (int y = HEIGHT - 110; y < HEIGHT - 10; y++) {
        for (int x = 10; x < 110; x++) {
            fb[y * WIDTH + x] = 0x0000;
        }
    }

    // Center - X pattern
    int cx = WIDTH / 2;
    int cy = HEIGHT / 2;
    for (int i = -100; i < 100; i++) {
        // Diagonal 1
        if (cy + i >= 0 && cy + i < HEIGHT && cx + i >= 0 && cx + i < WIDTH) {
            fb[(cy + i) * WIDTH + (cx + i)] = 0x0000;
        }
        // Diagonal 2
        if (cy + i >= 0 && cy + i < HEIGHT && cx - i >= 0 && cx - i < WIDTH) {
            fb[(cy + i) * WIDTH + (cx - i)] = 0x0000;
        }
    }
}

int main() {
    printf("Test 2: Shared Memory Framebuffer\n");
    printf("==================================\n\n");

    // Check if swtfb exists
    if (access(SWTFB_PATH, F_OK) != 0) {
        printf("⚠ %s does not exist\n", SWTFB_PATH);
        printf("This is expected if rm2fb is not running.\n");
        printf("Try creating it manually or check if another path is used.\n\n");

        printf("Checking /dev/shm/ contents:\n");
        system("ls -la /dev/shm/");
        return 1;
    }

    int fd = open(SWTFB_PATH, O_RDWR);
    if (fd < 0) {
        perror("Failed to open swtfb");
        return 1;
    }

    printf("✓ Opened %s\n", SWTFB_PATH);

    size_t size = WIDTH * HEIGHT * BPP;

    uint16_t *fbp = (uint16_t *)mmap(NULL, size, PROT_READ | PROT_WRITE,
                                      MAP_SHARED, fd, 0);

    if (fbp == MAP_FAILED) {
        perror("Failed to mmap swtfb");
        close(fd);
        return 1;
    }

    printf("✓ Mapped shared memory (%zu bytes)\n", size);
    printf("\nDrawing test pattern...\n");

    draw_test_pattern(fbp);

    printf("  - White square (top-left)\n");
    printf("  - Gray square (top-right)\n");
    printf("  - Black square (bottom-left)\n");
    printf("  - X pattern (center)\n");

    printf("\n✓ Test complete!\n");
    printf("Check screen for test pattern.\n");
    printf("Waiting 10 seconds...\n");

    sleep(10);

    munmap(fbp, size);
    close(fd);

    return 0;
}
