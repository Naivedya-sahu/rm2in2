#!/bin/bash
# Cross-Compilation Compatibility Test
# Run this in WSL to test what works when cross-compiling

set -e

echo "=========================================="
echo "  CROSS-COMPILATION COMPATIBILITY TEST"
echo "=========================================="
echo ""

# Check if cross-compiler is available
if ! command -v arm-linux-gnueabihf-gcc &> /dev/null; then
    echo "ERROR: arm-linux-gnueabihf-gcc not found!"
    echo ""
    echo "Install with:"
    echo "  sudo apt update && sudo apt install -y gcc-arm-linux-gnueabihf"
    exit 1
fi

echo "Cross-compiler found:"
arm-linux-gnueabihf-gcc --version | head -1
echo ""

# Create test directory
TEST_DIR="./rm2_compat_tests"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "Creating test programs..."
echo ""

# Test 1: Basic C program
cat > test_basic.c << 'EOF'
#include <stdio.h>
int main() {
    printf("Test 1: Basic C - PASS\n");
    return 0;
}
EOF

# Test 2: Math library
cat > test_math.c << 'EOF'
#include <stdio.h>
#include <math.h>
int main() {
    double result = sqrt(16.0);
    printf("Test 2: Math library - PASS (sqrt(16) = %.1f)\n", result);
    return 0;
}
EOF

# Test 3: String operations
cat > test_string.c << 'EOF'
#include <stdio.h>
#include <string.h>
int main() {
    char str[] = "Hello RM2";
    printf("Test 3: String ops - PASS (len=%zu)\n", strlen(str));
    return 0;
}
EOF

# Test 4: File I/O
cat > test_file.c << 'EOF'
#include <stdio.h>
int main() {
    FILE *f = fopen("/tmp/test.txt", "w");
    if (f) {
        fprintf(f, "test");
        fclose(f);
        remove("/tmp/test.txt");
        printf("Test 4: File I/O - PASS\n");
        return 0;
    }
    printf("Test 4: File I/O - FAIL\n");
    return 1;
}
EOF

# Test 5: Memory allocation
cat > test_memory.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
int main() {
    int *arr = malloc(100 * sizeof(int));
    if (arr) {
        arr[0] = 42;
        printf("Test 5: Dynamic memory - PASS (alloc OK)\n");
        free(arr);
        return 0;
    }
    printf("Test 5: Dynamic memory - FAIL\n");
    return 1;
}
EOF

# Test 6: Time functions
cat > test_time.c << 'EOF'
#include <stdio.h>
#include <time.h>
#include <sys/time.h>
int main() {
    time_t now = time(NULL);
    struct timeval tv;
    gettimeofday(&tv, NULL);
    printf("Test 6: Time functions - PASS\n");
    return 0;
}
EOF

# Test 7: Threading (pthread)
cat > test_pthread.c << 'EOF'
#include <stdio.h>
#include <pthread.h>
void* thread_func(void* arg) {
    return NULL;
}
int main() {
    pthread_t thread;
    if (pthread_create(&thread, NULL, thread_func, NULL) == 0) {
        pthread_join(thread, NULL);
        printf("Test 7: Pthread - PASS\n");
        return 0;
    }
    printf("Test 7: Pthread - FAIL\n");
    return 1;
}
EOF

# Test 8: Linux input subsystem (uinput)
cat > test_uinput.c << 'EOF'
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <linux/uinput.h>
int main() {
    int fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (fd >= 0) {
        close(fd);
        printf("Test 8: uinput access - PASS\n");
        return 0;
    }
    printf("Test 8: uinput access - FAIL (check if /dev/uinput exists)\n");
    return 1;
}
EOF

# Test 9: Network socket
cat > test_socket.c << 'EOF'
#include <stdio.h>
#include <sys/socket.h>
#include <unistd.h>
int main() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock >= 0) {
        close(sock);
        printf("Test 9: Socket creation - PASS\n");
        return 0;
    }
    printf("Test 9: Socket creation - FAIL\n");
    return 1;
}
EOF

# Test 10: Signal handling
cat > test_signal.c << 'EOF'
#include <stdio.h>
#include <signal.h>
void handler(int sig) {}
int main() {
    signal(SIGUSR1, handler);
    printf("Test 10: Signal handling - PASS\n");
    return 0;
}
EOF

echo "=========================================="
echo "Compiling tests..."
echo "=========================================="
echo ""

TESTS="basic math string file memory time pthread uinput socket signal"
SUCCESS=0
TOTAL=0

for test in $TESTS; do
    TOTAL=$((TOTAL + 1))
    echo -n "Compiling test_${test}.c ... "
    
    EXTRA_FLAGS=""
    if [ "$test" = "math" ]; then
        EXTRA_FLAGS="-lm"
    elif [ "$test" = "pthread" ]; then
        EXTRA_FLAGS="-lpthread"
    fi
    
    if arm-linux-gnueabihf-gcc -static -o test_${test} test_${test}.c $EXTRA_FLAGS 2>/dev/null; then
        echo "✓"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "✗ FAILED"
    fi
done

echo ""
echo "=========================================="
echo "Compilation Summary"
echo "=========================================="
echo "Successful: $SUCCESS / $TOTAL"
echo ""

if [ $SUCCESS -eq $TOTAL ]; then
    echo "All tests compiled successfully!"
else
    echo "Some tests failed to compile."
    echo "This may indicate missing libraries or headers."
fi

echo ""
echo "=========================================="
echo "Binary Analysis"
echo "=========================================="
echo ""

if [ -f test_basic ]; then
    echo "Sample binary info (test_basic):"
    file test_basic
    echo ""
    echo "Size: $(ls -lh test_basic | awk '{print $5}')"
    echo ""
    echo "Dependencies (ldd - may not work for cross-compiled):"
    ldd test_basic 2>/dev/null || echo "  (Static binary - no dynamic dependencies)"
    echo ""
fi

echo "=========================================="
echo "Deployment Instructions"
echo "=========================================="
echo ""
echo "To test these binaries on RM2:"
echo ""
echo "1. Transfer all test binaries:"
echo "   scp test_* root@10.11.99.1:/home/root/tests/"
echo ""
echo "2. SSH to RM2 and run:"
echo "   ssh root@10.11.99.1"
echo "   cd /home/root/tests"
echo "   chmod +x test_*"
echo "   for f in test_*; do ./$f; done"
echo ""
echo "3. Check which tests pass on the actual device"
echo ""

echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "Generated files in: $TEST_DIR/"
echo ""
echo "Run the RM2 diagnostic script on device:"
echo "  ./rm2_diagnostic.sh"
echo ""
echo "Compare results to identify:"
echo "  - Which libraries work at compile time"
echo "  - Which features work at runtime"
echo "  - Any compatibility issues"
echo ""

# Create deployment helper script
cat > deploy_tests.sh << 'DEPLOY_EOF'
#!/bin/bash
RM2_IP="10.11.99.1"
echo "Deploying tests to RM2..."
ssh root@${RM2_IP} "mkdir -p /home/root/tests"
scp test_* root@${RM2_IP}:/home/root/tests/
echo ""
echo "Running tests on RM2..."
ssh root@${RM2_IP} "cd /home/root/tests && chmod +x test_* && for f in test_*; do ./$f; done"
DEPLOY_EOF

chmod +x deploy_tests.sh

echo "Created deployment script: deploy_tests.sh"
echo "Run it to automatically deploy and test on RM2"
echo ""
