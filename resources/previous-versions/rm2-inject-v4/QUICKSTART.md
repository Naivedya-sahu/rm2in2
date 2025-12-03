# RM2 Injection System v4 - Quick Start

**Version:** 4.0 (Fixed Coordinates & Reliable Deployment)  
**Status:** Production Ready

---

## What's Fixed

✓ **Coordinate mirroring fixed** - No more backwards text or inverted circuits  
✓ **Deployment workflow improved** - Better verification and error messages  
✓ **Hook loading reliable** - Direct process launch instead of systemd  
✓ **Comprehensive error handling** - Clear next steps when issues occur

---

## Setup (5 Minutes One-Time)

### 1. Prerequisites
```bash
# Python dependencies
pip install svgpathtools

# ARM cross-compiler
sudo apt-get install gcc-arm-linux-gnueabihf

# Verify
python3 -c "import svgpathtools; print('OK')"
arm-linux-gnueabihf-gcc --version
```

### 2. Build
```bash
cd C:\Users\NAVY\Documents\Arduino\rm2-inject-v4
./scripts/build.sh
```

Expected output:
```
✓ Found: arm-linux-gnueabihf-gcc
✓ Found: inject_hook.c
✓ Compilation successful
✓ Output file: ./build/inject_hook.so (14K)
```

### 3. Deploy
```bash
./scripts/deploy.sh 192.168.1.137
```

Expected output:
```
✓ Hook library ready
✓ SSH connectivity verified
✓ Deployed inject_hook.so
✓ Deployed server.sh
✓ Deployment verified
```

### 4. Verify Deployment
```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh check'
```

Expected output:
```
✓ Hook library deployed
✓ Server script deployed
✓ Xochitl installed
✓ Deployment complete and verified
```

---

## Daily Use (2 Minutes Per Circuit)

### Step 1: Start Server
```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh start'
```

### Step 2: Convert Circuit
```bash
python3 ./tools/svg2pen.py my_circuit.svg 2.5 commands.txt
```

Output: `commands.txt` with pen commands

### Step 3: Inject
```bash
./scripts/pen_inject.sh commands.txt 192.168.1.137
```

Follow prompts:
1. Press Enter to confirm
2. When ready, tap your pen on RM2 screen
3. Circuit appears!

### Step 4: Stop Server
```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh stop'
```

---

## Common Commands

```bash
# Check server status
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh status'

# Restart server
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh restart'

# View logs
ssh root@192.168.1.137 'tail -20 /var/log/rm2-inject.log'

# Convert SVG (different scales)
python3 ./tools/svg2pen.py circuit.svg 1.5 small.txt   # Smaller
python3 ./tools/svg2pen.py circuit.svg 2.5 normal.txt  # Recommended
python3 ./tools/svg2pen.py circuit.svg 3.0 large.txt   # Larger
```

---

## Coordinate System

RM2 Display:
```
(0, 0) ─────────────────────→ (1404, 0)
  │
  │  1872 pixels tall
  │
  ↓
(0, 1872) ─────────────────→ (1404, 1872)
```

Coordinates are display pixels. Axis transformation handled internally (FIXED).

---

## What's Different from v3

| Aspect | v3 | v4 | Benefit |
|--------|----|----|---------|
| Coordinates | Mirrored | Correct | ✓ Text not backwards |
| Hook loading | systemctl | Direct launch | ✓ More reliable |
| Verification | None | Comprehensive | ✓ Clear errors |
| Error messages | Minimal | Detailed | ✓ Know what to do |

---

## Troubleshooting

### "Hook: NOT LOADED"
```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh restart'
```

### "Cannot reach RM2"
```bash
ping 192.168.1.137
ssh root@192.168.1.137 "echo OK"
```

### SVG conversion fails
```bash
# Verify SVG is valid
python3 -c "from svgpathtools import svg2paths; svg2paths('circuit.svg')"
```

### Coordinates still wrong (shouldn't happen in v4)
1. Rebuild: `./scripts/build.sh`
2. Redeploy: `./scripts/deploy.sh 192.168.1.137`
3. Restart: `ssh root@192.168.1.137 '/opt/rm2-inject/server.sh restart'`

---

## File Structure

```
rm2-inject-v4/
├─ src/
│  └─ inject_hook.c         ← Fixed coordinates
├─ build/
│  └─ inject_hook.so        ← Compiled ARM binary (after build)
├─ tools/
│  ├─ server.sh             ← Improved lifecycle
│  └─ svg2pen.py            ← SVG converter
├─ scripts/
│  ├─ build.sh              ← Build verification
│  ├─ deploy.sh             ← Deploy verification
│  └─ pen_inject.sh         ← Command injector
├─ examples/
│  └─ example.svg           ← Test file
├─ README.md                ← Overview
└─ QUICKSTART.md            ← This file
```

---

## Test It

Create a simple test file (test.txt):
```
PEN_DOWN 100 100
PEN_MOVE 200 100
PEN_MOVE 200 200
PEN_MOVE 100 200
PEN_MOVE 100 100
PEN_UP
```

Inject:
```bash
./scripts/pen_inject.sh test.txt 192.168.1.137
```

**Expected:** Square appears at correct position, not mirrored.

---

## Performance

- SVG conversion: 1-3 seconds
- Injection: 30-60 seconds
- Total workflow: ~2 minutes

---

## Next Steps

1. Follow setup steps above (5 min)
2. Run test to verify coordinates are correct (1 min)
3. Use for your circuit documentation

---

## Support

Check server status:
```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh status'
```

View logs:
```bash
ssh root@192.168.1.137 'tail -50 /var/log/rm2-inject.log'
```

For detailed information, see README.md.
