# Framebuffer and Overlay Tests for reMarkable 2 (OS 3.24)

These tests determine which approach works for creating a custom toolbar overlay that can render symbols using lamp.

## Test Summary

| Test | What it Tests | Expected Result on 3.24 |
|------|---------------|-------------------------|
| 01 | Direct `/dev/fb0` write | ⚠️ May display but xochitl won't acknowledge |
| 02 | Shared memory `/dev/shm/swtfb.01` | ❌ Requires rm2fb (not supported) |
| 03 | rMlib UI framework | ❌ Requires rm2fb (not supported) |
| 04 | Qt overlay window | ✅ Should work (uses system Qt) |

## Test 1: Direct Framebuffer (`/dev/fb0`)

**Purpose:** Check if direct pixel manipulation displays anything

```bash
# Compile
gcc -o test_fb0 01_test_fb0_direct.c

# Deploy
scp test_fb0 root@10.11.99.1:/home/root/

# Run
ssh root@10.11.99.1
./test_fb0
```

**Expected:** Rectangles may appear on screen briefly, but xochitl won't save them.

**If it works:** We can use this for temporary UI overlays (not notebook content)

---

## Test 2: Shared Memory Framebuffer

**Purpose:** Test rm2fb-style shared memory approach

```bash
gcc -o test_swtfb 02_test_swtfb_shm.c
scp test_swtfb root@10.11.99.1:/home/root/
ssh root@10.11.99.1 ./test_swtfb
```

**Expected:** Will fail unless rm2fb is running (which it can't be on 3.24)

**Alternative:** Check what paths exist:
```bash
ssh root@10.11.99.1 "ls -la /dev/shm/"
```

---

## Test 3: rMlib UI Framework

**Purpose:** Test if rMlib can create UI without rm2fb

**Build:**
```bash
cd resources/repos/rM2-stuff
mkdir -p build && cd build

# Configure
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build rMlib
make rMlib

# Compile test
cd ../../..
arm-remarkable-linux-gnueabihf-g++ \
  -o test_rmlib_ui \
  test-scripts/03_test_rmlib_ui.cpp \
  -I resources/repos/rM2-stuff/libs/rMlib/include \
  -L resources/repos/rM2-stuff/build/libs/rMlib \
  -lrMlib \
  -std=c++17

# Deploy
scp test_rmlib_ui root@10.11.99.1:/home/root/
```

**Expected:** Will likely fail without rm2fb support

---

## Test 4: Qt Overlay Window ⭐ MOST PROMISING

**Purpose:** Create Qt window using system libraries

**Build:**
```bash
# Create Qt project file
cat > test_qt.pro << 'EOF'
QT += core gui widgets
CONFIG += c++11
TARGET = test_qt_overlay
SOURCES += test-scripts/04_test_qt_overlay.cpp
EOF

# Build (requires Qt cross-compiler)
qmake test_qt.pro
make

# Deploy
scp test_qt_overlay root@10.11.99.1:/home/root/
```

**Run on device:**
```bash
ssh root@10.11.99.1

# Try running alongside xochitl
export QT_QPA_PLATFORM=linuxfb
./test_qt_overlay

# If that conflicts, try stopping xochitl first
systemctl stop xochitl
./test_qt_overlay
systemctl start xochitl
```

**Expected:** Should create a visible overlay window!

**If successful:** This is our path forward for the toolbar.

---

## Quick Test All (in order)

```bash
# Build all tests
gcc -o test_fb0 test-scripts/01_test_fb0_direct.c
gcc -o test_swtfb test-scripts/02_test_swtfb_shm.c

# Deploy
scp test_fb0 test_swtfb root@10.11.99.1:/home/root/

# Test on device
ssh root@10.11.99.1 << 'EOF'
echo "=== Test 1: Direct fb0 ==="
./test_fb0
sleep 2

echo -e "\n=== Test 2: Shared memory ==="
./test_swtfb
sleep 2

echo -e "\n=== Checking display devices ==="
ls -la /dev/fb*
ls -la /dev/shm/

echo -e "\n=== Qt libraries available ==="
ls -la /usr/lib/*Qt5* | head -20
EOF
```

---

## What Each Success Means

### ✅ Test 1 Success (fb0 direct)
- Can draw temporary UI overlays
- **But:** Won't be saved in xochitl notebook
- **Use:** Toolbar UI only, use lamp for actual drawing

### ✅ Test 2 Success (swtfb)
- Shared memory approach works
- Might mean rm2fb compatibility exists
- **Use:** Could build rm2fb-style integration

### ✅ Test 3 Success (rMlib)
- Full UI framework available
- **Use:** Can build complex toolbar with rMlib widgets

### ✅ Test 4 Success (Qt) ⭐
- **BEST CASE:** Native Qt overlay works
- Can create full-featured toolbar
- Integrates with lamp for drawing
- **Use:** Build production toolbar with Qt

---

## Next Steps Based on Results

### If Qt works (Test 4 success):
→ Build full toolbar using Qt + lamp integration

### If only fb0 works (Test 1 success):
→ Build simple overlay, pipe to lamp for drawing

### If nothing works:
→ Options:
  1. Reverse engineer xochitl 3.24 for rm2fb support
  2. Use hardware buttons + lamp (no UI)
  3. External PC control via SSH + lamp

---

## Debugging Tips

**If tests crash:**
```bash
# Check dmesg for errors
dmesg | tail -20

# Check running processes
ps aux | grep -E "xochitl|test"

# Check framebuffer status
cat /sys/class/graphics/fb0/virtual_size
fbset
```

**If nothing displays:**
```bash
# Force full screen refresh
echo 1 > /sys/class/graphics/fb0/force_refresh

# Or use lamp to trigger display update
echo "pen down 100 100" | lamp
echo "pen up" | lamp
```

**Check Qt environment:**
```bash
# List Qt libraries
ldconfig -p | grep Qt

# Check Qt platform plugins
ls -la /usr/lib/qt/plugins/platforms/

# Test basic Qt
QT_DEBUG_PLUGINS=1 ./test_qt_overlay
```

---

## Expected Outcome

Based on 3.24 architecture, **Test 4 (Qt)** has the highest chance of success because:
- ✅ Qt is native to reMarkable (xochitl uses it)
- ✅ Doesn't depend on rm2fb
- ✅ Has its own display backend
- ✅ Can run alongside xochitl

If Qt works, we can build a production-ready toolbar!
