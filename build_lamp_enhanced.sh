#!/bin/bash
# Build enhanced lamp with eraser support

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RMKIT_DIR="$SCRIPT_DIR/resources/repos/rmkit"
LAMP_DIR="$RMKIT_DIR/src/lamp"

echo "=== Building Enhanced lamp with Eraser Support ==="
echo ""

# Check for toolchain
if ! command -v arm-linux-gnueabihf-g++ &> /dev/null; then
    echo "❌ ARM toolchain not found"
    echo "Please install: apt-get install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf"
    echo "Or use the ARM toolchain from /opt/arm-toolchain"
    exit 1
fi

if ! command -v okp &> /dev/null; then
    echo "❌ okp not found"
    echo "Please install okp first"
    exit 1
fi

echo "✓ Toolchain found"
echo "  arm-linux-gnueabihf-g++: $(which arm-linux-gnueabihf-g++)"
echo "  okp: $(which okp)"
echo ""

# Backup original
cd "$LAMP_DIR"
if [ ! -f main.cpy.orig ]; then
    echo "=== Backing up original lamp source ==="
    cp main.cpy main.cpy.orig
    echo "✓ Backup created: main.cpy.orig"
fi

# Apply patch
echo ""
echo "=== Applying eraser support patch ==="
cd "$RMKIT_DIR"

# Create patched version
if [ -f "$SCRIPT_DIR/lamp_eraser.patch" ]; then
    cd "$LAMP_DIR"

    # Restore original first
    if [ -f main.cpy.orig ]; then
        cp main.cpy.orig main.cpy
    fi

    # Apply patch
    patch -p0 < "$SCRIPT_DIR/lamp_eraser.patch" || {
        echo "⚠ Patch failed, trying manual insertion..."

        # If patch fails, insert code manually
        if ! grep -q "BTN_TOOL_RUBBER" main.cpy; then
            echo "Adding eraser support manually..."

            # Find insertion point after pen_up() and add eraser functions
            # This is a simplified approach - actual implementation would use sed/awk
            echo "❌ Manual patch insertion not implemented yet"
            echo "Please apply lamp_eraser.patch manually"
            exit 1
        fi
    }

    echo "✓ Patch applied successfully"
else
    echo "❌ Patch file not found: $SCRIPT_DIR/lamp_eraser.patch"
    exit 1
fi

# Build rmkit.h if needed
cd "$RMKIT_DIR"
if [ ! -f src/build/rmkit.h ]; then
    echo ""
    echo "=== Building rmkit.h ==="
    cd src/rmkit
    export TARGET=rm
    make compile_remarkable
    cd ../..
fi

# Build STB library if needed
if [ ! -f src/build/stb.arm.o ]; then
    echo ""
    echo "=== Building STB library ==="
    arm-linux-gnueabihf-g++ -c src/vendor/stb/stb.cpp -o src/build/stb.arm.o -fPIC -Os
fi
echo "✓ STB built"

# Build enhanced lamp
echo ""
echo "=== Building enhanced lamp ==="
cd src/lamp

export TARGET=rm
make clean 2>/dev/null || true

CXX=arm-linux-gnueabihf-g++ make compile_remarkable

if [ -f ../build/lamp ]; then
    echo ""
    echo "✓ Enhanced lamp built successfully!"
    echo ""
    ls -lh ../build/lamp
    file ../build/lamp
    echo ""
    echo "New eraser commands available:"
    echo "  eraser line x1 y1 x2 y2"
    echo "  eraser rectangle x1 y1 x2 y2"
    echo "  eraser fill x1 y1 x2 y2 [spacing]"
    echo "  eraser clear x1 y1 x2 y2"
    echo "  eraser down x y"
    echo "  eraser move x y"
    echo "  eraser up"
    echo ""
    echo "Deploy with: scp ../build/lamp root@10.11.99.1:/opt/bin/"
else
    echo "❌ Build failed!"
    exit 1
fi
