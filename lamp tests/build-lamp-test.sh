#!/bin/bash
# Build and test lamp-test.c

set -e

echo "=== Building lamp-test ==="

# Check for cross-compiler
if ! command -v arm-linux-gnueabihf-gcc &> /dev/null; then
    echo "ERROR: arm-linux-gnueabihf-gcc not found"
    echo "Install with: sudo apt install gcc-arm-linux-gnueabihf"
    exit 1
fi

# Compile
echo "Compiling lamp-test.c..."
arm-linux-gnueabihf-gcc -o lamp-test lamp-test.c -lm -static -O2

if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

echo "Build successful: lamp-test"
ls -lh lamp-test

echo ""
echo "=== Deployment Instructions ==="
echo ""
echo "1. Deploy to RM2:"
echo "   scp lamp-test root@10.11.99.1:/opt/"
echo ""
echo "2. Run on RM2:"
echo "   ssh root@10.11.99.1 /opt/lamp-test"
echo ""
echo "3. Tap pen on screen to trigger render"
echo ""
echo "4. Observe results:"
echo "   - Circle should be ROUND (not oval)"
echo "   - Rectangle should have correct proportions"
echo "   - Cross should be centered"
echo "   - Corner dots should appear at actual corners"
echo ""
echo "If all shapes render correctly, lamp's transformation works on your firmware!"
