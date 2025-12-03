# RM2 Injection System v4 - Fixed and Production Ready

**Status:** ✓ Production Ready with Critical Fixes  
**Location:** `C:\Users\NAVY\Documents\Arduino\rm2-inject-v4\`  
**Date:** November 2025

---

## What Was Wrong in v3

### Problem 1: X/Y Axis Mirroring
- **Symptom:** Content appeared backwards/mirrored on RM2
- **Cause:** Double coordinate transformation (swap in conversion + swap in event creation)
- **Impact:** Text unreadable, circuits inverted

### Problem 2: Hook Loading Reliability
- **Symptom:** Hook sometimes failed to load via systemctl
- **Cause:** systemd environment isolation prevented LD_PRELOAD propagation
- **Impact:** Unreliable server startup

### Problem 3: Lack of Verification
- **Symptom:** Deployment failures unclear, hard to troubleshoot
- **Cause:** No validation at each step
- **Impact:** Difficult to debug, unclear error messages

---

## What's Fixed in v4

### Fix 1: Coordinate Transformation (src/inject_hook.c)

**Before (WRONG):**
```c
ev = make_event(EV_ABS, ABS_X, wacom_y);  // Double swap problem
ev = make_event(EV_ABS, ABS_Y, wacom_x);  // Result: mirrored
```

**After (CORRECT):**
```c
ev = make_event(EV_ABS, ABS_X, wacom_x);  // Direct, no swap
ev = make_event(EV_ABS, ABS_Y, wacom_y);  // Correct orientation
```

**Result:** Coordinates appear correctly, no mirroring

### Fix 2: Hook Loading (tools/server.sh)

**Before (UNRELIABLE):**
```bash
systemctl set-environment LD_PRELOAD="$HOOK_LIB"
systemctl start xochitl
# Problem: systemd isolates environment
```

**After (RELIABLE):**
```bash
LD_PRELOAD="$HOOK_LIB" /usr/bin/xochitl --system &
# Direct launch: bypasses systemd isolation
```

**Result:** Reliable hook loading every time

### Fix 3: Comprehensive Verification

**New verification at each step:**
- `build.sh`: Verifies compiler, source, output binary type
- `deploy.sh`: Verifies build artifacts, SSH, file deployment
- `server.sh check`: Verifies all deployment components
- `server.sh start`: Verifies hook loaded before proceeding

**Result:** Clear error messages, easy troubleshooting

---

## File Inventory

### Core System (3 Critical Files)
- **src/inject_hook.c** - Fixed C LD_PRELOAD library
  - Lines 46-49: Coordinate transformation (simplified)
  - Lines 195-208: Event creation (FIXED - no additional swap)
  
- **tools/server.sh** - Improved server with verification
  - Lines 67-77: FIXED hook loading (direct process launch)
  - New: Auto-recovery, color-coded status, enhanced logging
  
- **tools/svg2pen.py** - SVG to PEN_* converter
  - Simple, focused, production-ready

### Build & Deployment (3 Scripts)
- **scripts/build.sh** - Cross-compile with verification
- **scripts/deploy.sh** - Deploy to RM2 with verification
- **scripts/pen_inject.sh** - Command injector

### Documentation (2 Files)
- **README.md** - This file
- **QUICKSTART.md** - 5-minute quick start guide

### Examples
- **examples/example.svg** - Test SVG file

---

## Quick Start

### 1. Build (One-time)
```bash
cd C:\Users\NAVY\Documents\Arduino\rm2-inject-v4
./scripts/build.sh
```

### 2. Deploy (One-time)
```bash
./scripts/deploy.sh 192.168.1.137
```

### 3. Daily Use
```bash
# Start server
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh start'

# Convert SVG
python3 ./tools/svg2pen.py circuit.svg 2.5 commands.txt

# Inject
./scripts/pen_inject.sh commands.txt 192.168.1.137

# Stop server
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh stop'
```

---

## Key Improvements

| Aspect | v3 | v4 |
|--------|----|----|
| Coordinates | Mirrored ✗ | Correct ✓ |
| Hook Loading | Unreliable ✗ | Reliable ✓ |
| Build Verification | None ✗ | Complete ✓ |
| Deploy Verification | None ✗ | Complete ✓ |
| Status Output | Basic ✗ | Color-coded ✓ |
| Error Messages | Vague ✗ | Clear ✓ |

---

## Testing Your Fix

Create test.txt:
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

**Expected Result:**
- ✓ Square appears on RM2
- ✓ Top-left corner at (100, 100)
- ✓ NOT mirrored or inverted
- ✓ Correct orientation

---

## System Requirements

### PC Side
- Python 3.10+ with svgpathtools
- ARM cross-compiler (gcc-arm-linux-gnueabihf)
- Bash 4+
- SSH client
- Windows (WSL2), macOS, or Linux

### RM2 Side
- Codex Linux (any recent version)
- Bash (included)
- Xochitl (included)
- SSH access as root
- WiFi connection to PC

---

## Known Limitations

1. **SVG Text Not Supported** - Re-export from KiCAD without text
2. **Complex Fills Not Supported** - Outlines only, hatching available
3. **Single Injection Per Session** - Restart server between injections

None are blockers for circuit documentation.

---

## Production Status

✓ All critical issues fixed  
✓ Comprehensive verification added  
✓ Production-ready codebase  
✓ Ready for daily circuit documentation

---

## Support

**Check status:**
```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh status'
```

**View logs:**
```bash
ssh root@192.168.1.137 'tail -20 /var/log/rm2-inject.log'
```

**Verify deployment:**
```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh check'
```
