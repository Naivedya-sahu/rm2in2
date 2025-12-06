#!/bin/bash
# Build lamp without FBInk dependency
set -e

echo "=== Building lamp for reMarkable ==="

# 1. Setup environment
export PATH="/opt/codex/bin:$PATH"
export TARGET=rm
export HOST=10.11.99.1

cd /home/user/rm2in2/resources/repos/rmkit

# 2. Check toolchain
if ! command -v arm-linux-gnueabihf-g++ &> /dev/null; then
    echo "❌ ARM toolchain not found!"
    echo "Run: /tmp/install_toolchain.sh"
    exit 1
fi

if ! command -v okp &> /dev/null; then
    echo "❌ okp compiler not found!"
    echo "Run: /tmp/install_okp.sh"
    exit 1
fi

echo "✓ Toolchain found"
echo "  arm-linux-gnueabihf-g++: $(which arm-linux-gnueabihf-g++)"
echo "  okp: $(which okp)"

# 3. Build rmkit.h first (required)
echo ""
echo "=== Building rmkit.h ==="
mkdir -p src/build
cd src/rmkit
make

cd ../..

# 4. Build stb (required dependency)
echo ""
echo "=== Building STB library ==="
if [ ! -f "src/build/stb.arm.o" ]; then
    arm-linux-gnueabihf-g++ -c src/vendor/stb/stb.cpp -o src/build/stb.arm.o -fPIC -Os
fi
echo "✓ STB built"

# 5. Build lamp (WITHOUT FBInk)
echo ""
echo "=== Building lamp ==="
cd src/lamp

# Direct build without make (to avoid FBInk checks)
okp \
    src/build/stb.arm.o \
    -ig RMKIT_IMPLEMENTATION \
    -ns \
    -ni \
    -for \
    -d ../.lamp_cpp/ \
    -o ../build/lamp \
    main.cpy \
    -- \
    -DREMARKABLE=1 \
    -DRMKIT_IMPLEMENTATION \
    -ldl \
    -pthread \
    -lpthread \
    -fdata-sections \
    -ffunction-sections \
    -Wl,--gc-sections \
    -O2

cd ../..

# 6. Verify binary
if [ -f "src/build/lamp" ]; then
    echo ""
    echo "✓ lamp built successfully!"
    ls -lh src/build/lamp
    file src/build/lamp

    # 7. Deploy to device
    echo ""
    read -p "Deploy to device at $HOST? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deploying..."
        scp src/build/lamp root@$HOST:/opt/bin/
        echo "✓ Deployed to /opt/bin/lamp"

        # Test
        echo ""
        echo "Testing lamp on device..."
        ssh root@$HOST 'echo "pen line 100 100 200 200" | /opt/bin/lamp && echo "✓ lamp works!"'
    fi
else
    echo "❌ Build failed!"
    exit 1
fi
