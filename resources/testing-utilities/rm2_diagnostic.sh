#!/bin/bash
# RM2 Environment Diagnostic Script
# Run this directly on your RM2 to check available libraries and tools

echo "=========================================="
echo "    RM2 ENVIRONMENT DIAGNOSTIC REPORT"
echo "=========================================="
echo ""
date
echo ""

# System Info
echo "=========================================="
echo "1. SYSTEM INFORMATION"
echo "=========================================="
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "OS: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2)"
echo ""

# Check for OS version
if [ -f /usr/bin/xochitl ]; then
    echo "Xochitl version:"
    strings /usr/bin/xochitl | grep -E "^[0-9]+\.[0-9]+\.[0-9]+" | head -1
fi
echo ""

# Available disk space
echo "Disk space:"
df -h / | tail -1
echo ""

# Memory
echo "Memory:"
free -h
echo ""

# CPU info
echo "CPU:"
cat /proc/cpuinfo | grep -E "model name|processor" | head -4
echo ""

echo "=========================================="
echo "2. DEVELOPMENT TOOLS"
echo "=========================================="

# Compilers
echo "Compilers:"
which gcc 2>/dev/null && gcc --version | head -1 || echo "  gcc: NOT FOUND"
which g++ 2>/dev/null && g++ --version | head -1 || echo "  g++: NOT FOUND"
which clang 2>/dev/null && clang --version | head -1 || echo "  clang: NOT FOUND"
echo ""

# Build tools
echo "Build tools:"
which make 2>/dev/null && make --version | head -1 || echo "  make: NOT FOUND"
which cmake 2>/dev/null && cmake --version | head -1 || echo "  cmake: NOT FOUND"
which qmake 2>/dev/null && echo "  qmake: FOUND" || echo "  qmake: NOT FOUND"
echo ""

# Scripting languages
echo "Scripting languages:"
which python 2>/dev/null && python --version || echo "  python: NOT FOUND"
which python3 2>/dev/null && python3 --version || echo "  python3: NOT FOUND"
which perl 2>/dev/null && perl --version | head -2 | tail -1 || echo "  perl: NOT FOUND"
which lua 2>/dev/null && lua -v || echo "  lua: NOT FOUND"
which node 2>/dev/null && node --version || echo "  node: NOT FOUND"
which bash 2>/dev/null && bash --version | head -1 || echo "  bash: NOT FOUND"
which sh 2>/dev/null && echo "  sh: FOUND" || echo "  sh: NOT FOUND"
echo ""

echo "=========================================="
echo "3. GRAPHICS & RENDERING LIBRARIES"
echo "=========================================="

echo "Qt libraries:"
ls /usr/lib/libQt*.so.* 2>/dev/null | sed 's/.*libQt/  libQt/' | head -10
echo "  Total Qt libs: $(ls /usr/lib/libQt*.so.* 2>/dev/null | wc -l)"
echo ""

echo "Graphics libraries:"
for lib in cairo pixman freetype fontconfig harfbuzz png jpeg tiff svg; do
    if ls /usr/lib/lib${lib}*.so* >/dev/null 2>&1; then
        echo "  lib${lib}: FOUND"
    else
        echo "  lib${lib}: NOT FOUND"
    fi
done
echo ""

echo "=========================================="
echo "4. SYSTEM LIBRARIES"
echo "=========================================="

echo "Core libraries:"
for lib in c m pthread dl rt gcc_s stdc++; do
    if ls /usr/lib/lib${lib}.so* >/dev/null 2>&1 || ls /lib/lib${lib}.so* >/dev/null 2>&1; then
        echo "  lib${lib}: FOUND"
    else
        echo "  lib${lib}: NOT FOUND"
    fi
done
echo ""

echo "Compression libraries:"
for lib in z bz2 lzma zstd; do
    if ls /usr/lib/lib${lib}.so* >/dev/null 2>&1; then
        echo "  lib${lib}: FOUND"
    else
        echo "  lib${lib}: NOT FOUND"
    fi
done
echo ""

echo "Network libraries:"
for lib in ssl crypto curl; do
    if ls /usr/lib/lib${lib}.so* >/dev/null 2>&1; then
        echo "  lib${lib}: FOUND"
    else
        echo "  lib${lib}: NOT FOUND"
    fi
done
echo ""

echo "=========================================="
echo "5. INPUT/OUTPUT DEVICES"
echo "=========================================="

echo "Input devices:"
ls -la /dev/input/ 2>/dev/null || echo "  /dev/input: NOT FOUND"
echo ""

echo "uinput device:"
if [ -e /dev/uinput ]; then
    ls -la /dev/uinput
    echo "  Status: AVAILABLE"
else
    echo "  /dev/uinput: NOT FOUND"
fi
echo ""

echo "Framebuffer:"
if [ -e /dev/fb0 ]; then
    ls -la /dev/fb0
    echo "  Status: AVAILABLE"
else
    echo "  /dev/fb0: NOT FOUND"
fi
echo ""

echo "=========================================="
echo "6. PACKAGE MANAGEMENT"
echo "=========================================="

echo "Package managers:"
which opkg 2>/dev/null && echo "  opkg: FOUND (Toltec)" || echo "  opkg: NOT FOUND"
which apt 2>/dev/null && echo "  apt: FOUND" || echo "  apt: NOT FOUND"
which dpkg 2>/dev/null && echo "  dpkg: FOUND" || echo "  dpkg: NOT FOUND"
echo ""

if which opkg >/dev/null 2>&1; then
    echo "Installed packages via opkg:"
    opkg list-installed | wc -l
    echo ""
fi

echo "=========================================="
echo "7. FILE UTILITIES"
echo "=========================================="

echo "File manipulation tools:"
for tool in sed awk grep find xargs tar gzip bzip2 unzip dd cat cp mv rm; do
    if which $tool >/dev/null 2>&1; then
        echo "  $tool: FOUND"
    else
        echo "  $tool: NOT FOUND"
    fi
done
echo ""

echo "=========================================="
echo "8. NETWORK TOOLS"
echo "=========================================="

echo "Network utilities:"
for tool in ssh scp wget curl ping netstat ip ifconfig; do
    if which $tool >/dev/null 2>&1; then
        echo "  $tool: FOUND"
    else
        echo "  $tool: NOT FOUND"
    fi
done
echo ""

echo "=========================================="
echo "9. DEBUGGING TOOLS"
echo "=========================================="

echo "Debug utilities:"
for tool in strace gdb ldd objdump readelf hexdump evtest; do
    if which $tool >/dev/null 2>&1; then
        echo "  $tool: FOUND"
    else
        echo "  $tool: NOT FOUND"
    fi
done
echo ""

echo "=========================================="
echo "10. LIBRARY LINKAGE TEST"
echo "=========================================="

echo "Testing basic library linkage:"
echo ""

# Create minimal test program
cat > /tmp/test_libs.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
int main() {
    printf("C stdlib: OK\n");
    sqrt(16);
    printf("Math lib: OK\n");
    strlen("test");
    printf("String lib: OK\n");
    return 0;
}
EOF

if which gcc >/dev/null 2>&1; then
    gcc -o /tmp/test_libs /tmp/test_libs.c -lm 2>/dev/null
    if [ $? -eq 0 ]; then
        /tmp/test_libs
        rm /tmp/test_libs
    else
        echo "  Cannot compile test program (no gcc or libs missing)"
    fi
    rm /tmp/test_libs.c
else
    echo "  Cannot test (gcc not available)"
    rm /tmp/test_libs.c
fi
echo ""

echo "=========================================="
echo "11. XOCHITL STATUS"
echo "=========================================="

if pgrep -x xochitl > /dev/null; then
    echo "Xochitl: RUNNING"
    ps aux | grep xochitl | grep -v grep
else
    echo "Xochitl: NOT RUNNING"
fi
echo ""

echo "=========================================="
echo "12. ENVIRONMENT VARIABLES"
echo "=========================================="

echo "Key environment variables:"
echo "  PATH=$PATH"
echo "  LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
echo "  HOME=$HOME"
echo "  USER=$USER"
echo ""

echo "=========================================="
echo "DIAGNOSTIC COMPLETE"
echo "=========================================="
echo ""
echo "This report can help determine:"
echo "  1. What libraries are available for linking"
echo "  2. What tools can be used for development"
echo "  3. Whether uinput/framebuffer are accessible"
echo "  4. System capabilities and constraints"
echo ""
echo "Save this output for reference:"
echo "  ./rm2_diagnostic.sh > diagnostic_report.txt"
