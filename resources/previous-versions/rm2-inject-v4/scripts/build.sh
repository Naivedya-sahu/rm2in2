#!/bin/bash
# Build script for RM2 injection hook v4
# Compiles the LD_PRELOAD library for ARM architecture

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_ROOT/src"
BUILD_DIR="$PROJECT_ROOT/build"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Building RM2 Injection Hook                           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check for cross-compiler
echo "Checking for ARM cross-compiler..."
if ! which arm-linux-gnueabihf-gcc >/dev/null 2>&1; then
    echo -e "${RED}✗ Error: arm-linux-gnueabihf-gcc not found${NC}"
    echo ""
    echo "Install the cross-compiler:"
    echo "  Ubuntu/Debian: sudo apt-get install gcc-arm-linux-gnueabihf"
    echo "  macOS:         brew install arm-linux-gnueabihf-binutils"
    exit 1
fi

COMPILER_VERSION=$(arm-linux-gnueabihf-gcc --version | head -n 1)
echo -e "${GREEN}✓ Found: $COMPILER_VERSION${NC}"
echo ""

# Check source file
echo "Checking source code..."
if [ ! -f "$SRC_DIR/inject_hook.c" ]; then
    echo -e "${RED}✗ Error: Source file not found: $SRC_DIR/inject_hook.c${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Found: inject_hook.c${NC}"
echo ""

# Create build directory
echo "Preparing build directory..."
mkdir -p "$BUILD_DIR"
echo -e "${GREEN}✓ Build directory ready: $BUILD_DIR${NC}"
echo ""

# Compile
echo "Compiling for ARM architecture..."
echo "Command: arm-linux-gnueabihf-gcc -shared -fPIC -O2 \\"
echo "           -o $BUILD_DIR/inject_hook.so \\"
echo "           $SRC_DIR/inject_hook.c \\"
echo "           -ldl -lpthread"
echo ""

if arm-linux-gnueabihf-gcc -shared -fPIC -O2 \
    -o "$BUILD_DIR/inject_hook.so" \
    "$SRC_DIR/inject_hook.c" \
    -ldl -lpthread; then
    echo -e "${GREEN}✓ Compilation successful${NC}"
else
    echo -e "${RED}✗ Compilation failed${NC}"
    exit 1
fi

echo ""

# Verify output
echo "Verifying build output..."
if [ ! -f "$BUILD_DIR/inject_hook.so" ]; then
    echo -e "${RED}✗ Error: Output file not created${NC}"
    exit 1
fi

# Check file type
if ! file "$BUILD_DIR/inject_hook.so" | grep -q "ELF.*ARM"; then
    echo -e "${RED}✗ Error: Output is not an ARM ELF binary${NC}"
    file "$BUILD_DIR/inject_hook.so"
    exit 1
fi

# Get size
SIZE=$(du -h "$BUILD_DIR/inject_hook.so" | cut -f1)
echo -e "${GREEN}✓ Output file: $BUILD_DIR/inject_hook.so ($SIZE)${NC}"

# Show binary info
echo ""
echo "Binary information:"
file "$BUILD_DIR/inject_hook.so"

# Check symbol table
echo ""
echo "Exported symbols:"
arm-linux-gnueabihf-nm "$BUILD_DIR/inject_hook.so" | grep -E "^[0-9a-f]+ [Tt] " | head -5 || echo "  (no exported symbols - expected for LD_PRELOAD)"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Build Complete                                       ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Deploy to RM2:"
echo "     ./scripts/deploy.sh 192.168.1.137"
echo ""
echo "  2. Start server:"
echo "     ssh root@192.168.1.137 '/opt/rm2-inject/server.sh start'"
echo ""
