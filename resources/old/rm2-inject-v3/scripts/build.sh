#!/bin/bash
# Build script for RM2 injection system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_ROOT/src"
BUILD_DIR="$PROJECT_ROOT/build"

echo "Building RM2 injection system..."

mkdir -p "$BUILD_DIR"

# Cross-compile for ARM
arm-linux-gnueabihf-gcc -shared -fPIC -O2 \
    -o "$BUILD_DIR/inject_hook.so" \
    "$SRC_DIR/inject_hook.c" \
    -ldl -lpthread

echo "Build complete: $BUILD_DIR/inject_hook.so"
echo "Size: $(du -h "$BUILD_DIR/inject_hook.so" | cut -f1)"
