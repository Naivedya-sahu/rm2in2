#!/bin/bash
#
# Test 5: Inspect xochitl UI Components
#
# Examines xochitl's structure to see if we can:
# 1. Find the native toolbar
# 2. Identify Qt resources
# 3. Check if we can inject custom toolbar items
#
# Run: ./05_inspect_xochitl_ui.sh

echo "Test 5: Inspecting xochitl UI Components"
echo "=========================================="
echo ""

echo "=== 1. xochitl Binary Information ==="
if [ -f /usr/bin/xochitl ]; then
    ls -lh /usr/bin/xochitl
    file /usr/bin/xochitl
    echo ""

    echo "Build ID:"
    readelf -n /usr/bin/xochitl | grep "Build ID" | head -1
    echo ""
else
    echo "❌ xochitl not found at /usr/bin/xochitl"
    exit 1
fi

echo "=== 2. Qt Resources in xochitl ==="
echo "Checking for embedded Qt resources..."
strings /usr/bin/xochitl | grep -i "\.qrc\|\.ui\|qml" | head -20
echo ""

echo "=== 3. Shared Libraries Used ==="
echo "Qt libraries:"
ldd /usr/bin/xochitl | grep Qt
echo ""

echo "Other libraries:"
ldd /usr/bin/xochitl | grep -v Qt | head -10
echo ""

echo "=== 4. xochitl Configuration Files ==="
echo "Config directory:"
ls -la /home/root/.config/remarkable/
echo ""

echo "xochitl.conf (first 20 lines):"
head -20 /home/root/.config/remarkable/xochitl.conf 2>/dev/null || echo "Not found"
echo ""

echo "=== 5. Qt Resources Directory ==="
if [ -d /usr/share/remarkable ]; then
    echo "Remarkable resources:"
    ls -la /usr/share/remarkable/
    echo ""
fi

if [ -d /usr/lib/qt ]; then
    echo "Qt plugins:"
    find /usr/lib/qt/plugins -type f 2>/dev/null | head -20
    echo ""
fi

echo "=== 6. Running xochitl Processes ==="
ps aux | grep xochitl | grep -v grep
echo ""

echo "=== 7. xochitl Environment Variables ==="
echo "Checking what environment xochitl runs with..."
if pgrep xochitl > /dev/null; then
    XOCHITL_PID=$(pgrep xochitl)
    echo "PID: $XOCHITL_PID"
    echo "Environment:"
    cat /proc/$XOCHITL_PID/environ | tr '\0' '\n' | grep -E "QT_|DISPLAY|WAYLAND" | head -10
    echo ""

    echo "Command line:"
    cat /proc/$XOCHITL_PID/cmdline | tr '\0' ' '
    echo -e "\n"
else
    echo "⚠ xochitl not running"
fi

echo "=== 8. D-Bus Services (if available) ==="
if command -v dbus-send &> /dev/null; then
    echo "Checking D-Bus for xochitl services..."
    dbus-send --system --print-reply --dest=org.freedesktop.DBus \
        /org/freedesktop/DBus org.freedesktop.DBus.ListNames 2>/dev/null | grep -i remarkable
else
    echo "D-Bus not available"
fi
echo ""

echo "=== 9. Systemd Service Configuration ==="
if [ -f /lib/systemd/system/xochitl.service ]; then
    echo "xochitl.service:"
    cat /lib/systemd/system/xochitl.service
    echo ""
fi

echo "=== 10. Toolbar/UI Hints ==="
echo "Searching for UI-related symbols in xochitl..."
strings /usr/bin/xochitl | grep -i "toolbar\|menu\|palette\|widget" | head -20
echo ""

echo "=== 11. QML/Qt Quick Files ==="
if [ -d /usr/share/remarkable ]; then
    find /usr/share/remarkable -name "*.qml" -o -name "*.js" 2>/dev/null
fi
echo ""

echo "=== 12. Screenshot Current Display ==="
if command -v lamp &> /dev/null; then
    echo "✓ lamp available for testing"
else
    echo "⚠ lamp not found - cannot test drawing integration"
fi
echo ""

echo "=== Summary ==="
echo ""
echo "Based on this information, we can determine:"
echo "  1. Which Qt version xochitl uses"
echo "  2. If there are QML/Qt Quick UI files we can modify"
echo "  3. What environment is needed for Qt overlay apps"
echo "  4. If D-Bus can be used for IPC with xochitl"
echo ""
echo "Save this output and analyze for toolbar modification possibilities."
