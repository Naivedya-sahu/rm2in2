# Quick Start: Test Custom Toolbar Approaches

Run these tests in order to find what works on your 3.24 device.

## 🚀 Fast Track (Copy-Paste Commands)

```bash
# 1. Build tests locally
cd /home/user/rm2in2/test-scripts
gcc -o test_fb0 01_test_fb0_direct.c
gcc -o test_swtfb 02_test_swtfb_shm.c

# 2. Deploy everything to device
scp test_fb0 test_swtfb 05_inspect_xochitl_ui.sh root@10.11.99.1:/home/root/

# 3. Run inspection script first (most informative)
ssh root@10.11.99.1 './05_inspect_xochitl_ui.sh > xochitl_info.txt 2>&1'
scp root@10.11.99.1:/home/root/xochitl_info.txt ./

# 4. Review the output
cat xochitl_info.txt
```

## 📊 What to Look For

From the inspection output (`xochitl_info.txt`):

### ✅ Good Signs:
- Qt version shown in ldd output
- QML files found in `/usr/share/remarkable/`
- D-Bus services available
- Environment variables: `QT_QPA_PLATFORM`, `QT_PLUGIN_PATH`

### 🎯 Key Information:
1. **Qt Version** → Tells us which Qt to use for overlay
2. **QML Files** → Might be able to modify native UI
3. **Plugin Path** → Where to put custom Qt plugins
4. **D-Bus** → Could communicate with xochitl

## 🧪 Run Individual Tests

### Test 1: Direct Framebuffer
```bash
ssh root@10.11.99.1 './test_fb0'
# Look at screen - do you see rectangles?
```

**If YES:** Can use fb0 for temporary UI overlay
**If NO:** Try Test 2

### Test 2: Shared Memory
```bash
ssh root@10.11.99.1 './test_swtfb'
```

**If YES:** Shared memory approach works!
**If NO:** Expected on 3.24 (no rm2fb)

### Test 3: Check Display Devices
```bash
ssh root@10.11.99.1 << 'EOF'
echo "=== Framebuffer devices ==="
ls -la /dev/fb*

echo -e "\n=== Shared memory ==="
ls -la /dev/shm/

echo -e "\n=== Current framebuffer settings ==="
fbset

echo -e "\n=== Can we write to fb0? ==="
dd if=/dev/urandom of=/dev/fb0 bs=1024 count=100 2>&1
sleep 2
EOF
```

## 🔍 Analyze Results

### Scenario A: fb0 Shows Output
→ **Can build simple overlay UI**
→ Use fb0 for toolbar, lamp for drawing
→ Next: Build minimal Qt app or direct framebuffer UI

### Scenario B: Found QML Files
→ **Might modify native xochitl UI**
→ Could inject custom toolbar buttons
→ Next: Reverse engineer QML structure

### Scenario C: Qt Libraries Present
→ **Can build Qt overlay app**
→ Best option for full-featured toolbar
→ Next: Build Test 4 (Qt overlay)

### Scenario D: Nothing Works
→ **Hardware button + lamp approach**
→ Or: Reverse engineer xochitl 3.24
→ Or: External control via SSH

## 📝 Report Your Findings

Create an issue with:
```
OS Version: 3.24.x.xxx (from /etc/version)
Test 1 (fb0): PASS/FAIL
Test 2 (swtfb): PASS/FAIL
Qt Version: (from xochitl_info.txt)
QML Files: YES/NO
Screen Output: (photo if possible)
```

## 🎯 Most Likely Outcome

Based on 3.24 architecture:
1. **fb0 direct write**: Likely works (visual only)
2. **Qt overlay**: Should work (recommended approach)
3. **Native UI mod**: Unknown, needs investigation

## ⚡ Next Steps If Qt Works

1. Build Test 4 (Qt overlay) - requires cross-compiler
2. Create symbol palette UI in Qt
3. Integrate with lamp for actual drawing
4. Add clipboard/library management
5. Deploy as systemd service

---

**TL;DR:** Run the inspection script first, then decide which test to build based on available features.
