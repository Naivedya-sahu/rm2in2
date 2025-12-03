# QUICK START: Using Your TXT File on RM2

## What You Have

✓ `test.txt` - Your converted G-code drawing (19,005 commands)
✓ RM2 injection system already deployed in `rm2-inject-v3/`

## What You Need to Do (3 Steps)

### Step 1: Copy injection scripts to your project

```bash
# Copy these files to your rm2-inject-v3/scripts/ folder:
cp inject_file.sh C:\Users\NAVY\Documents\Arduino\rm2-inject-v3\scripts\
cp inject_file_fast.sh C:\Users\NAVY\Documents\Arduino\rm2-inject-v3\scripts\
```

### Step 2: Start RM2 server

```bash
# SSH into your RM2
ssh root@10.11.99.1

# Start the injection server
/opt/rm2-inject/server.sh start

# Verify it's running
/opt/rm2-inject/server.sh status
```

Expected output:
```
Server: RUNNING ✓
Xochitl: RUNNING ✓
Hook: LOADED ✓
FIFO: EXISTS ✓
```

### Step 3: Inject your drawing

```bash
# On your PC
cd C:\Users\NAVY\Documents\Arduino\rm2-inject-v3

# Use the fast version (recommended)
bash scripts/inject_file_fast.sh test.txt 10.11.99.1
```

**Before pressing Enter:**
1. Open a notebook on RM2
2. Select Fineliner tool
3. Tap pen on screen where you want drawing to start
4. Return to PC and press Enter

## Expected Timeline

- **Your test.txt**: 19,005 commands
- **Injection rate**: ~100 commands/second
- **Total time**: ~3 minutes

You'll see the drawing appear in real-time on your RM2 screen!

## Command Reference

### inject_file_fast.sh (RECOMMENDED)
```bash
# Basic usage
bash scripts/inject_file_fast.sh test.txt 10.11.99.1

# With position offset
bash scripts/inject_file_fast.sh test.txt 10.11.99.1 1000 500

# Offset moves drawing by (1000, 500) pixels
```

### inject_file.sh (Slower, but more verbose)
```bash
bash scripts/inject_file.sh test.txt 10.11.99.1
```

## Troubleshooting

### "Server not running"
```bash
ssh root@10.11.99.1 '/opt/rm2-inject/server.sh start'
```

### "FIFO missing"
```bash
ssh root@10.11.99.1 '/opt/rm2-inject/server.sh restart'
```

### Drawing doesn't appear
1. Make sure you tapped pen on RM2 screen
2. Check server status: `/opt/rm2-inject/server.sh status`
3. Verify Xochitl is running with hook loaded

### Drawing is too large/small
Re-convert with different scale:
```bash
python3 gcode2inject.py test.ngc 50 test_small.txt   # 50% size
python3 gcode2inject.py test.ngc 150 test_large.txt  # 150% size
```

## Your Complete Workflow

```
KiCAD schematic
    ↓
Export as SVG
    ↓
Inkscape → Generate G-code (test.ngc)
    ↓
python3 gcode2inject.py test.ngc 100 test.txt
    ↓
bash inject_file_fast.sh test.txt 10.11.99.1
    ↓
Drawing appears on RM2! ✓
```

## File Locations

**On PC:**
```
C:\Users\NAVY\Documents\Arduino\rm2-inject-v3\
├── scripts/
│   ├── inject_file.sh         ← NEW
│   ├── inject_file_fast.sh    ← NEW (use this one)
│   ├── deploy.sh
│   └── console.sh
├── gcode2inject.py
├── test.ngc
└── test.txt
```

**On RM2:**
```
/opt/rm2-inject/
├── inject_hook.so     ← The injection library
└── server.sh          ← Server control script
```

## Next Steps

1. Test with your actual KiCAD circuits
2. Experiment with different scales
3. Try position offsets to place drawings precisely
4. Enjoy your automated circuit documentation! 🎉
