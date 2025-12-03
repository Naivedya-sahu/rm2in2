# RM2 Circuit Injection System - Installation & Usage Guide

**Version:** 2.0  
**Date:** November 2025  
**Status:** Production-ready

---

## Overview

This is a complete circuit injection system for the reMarkable 2 e-ink tablet. It allows you to inject SVG circuit diagrams from your PC directly into Xochitl notebooks as synthetic stylus strokes, enabling rapid circuit documentation without manual drawing.

### Key Facts

- **What it does:** Converts SVG circuit files to pen stroke commands and injects them into RM2 at specified coordinates
- **How it works:** Uses LD_PRELOAD hook to intercept Wacom device reads and inject synthetic events
- **System split:** SVG conversion runs on PC (Python); injection runs on RM2 (C hook + bash server)
- **Setup time:** ~15 minutes (one-time)
- **Daily use:** 30 seconds to start, then interactive injection

---

## System Requirements

### On Your PC

- **Python 3.10+** with pip
- **Bash 4+**
- **SSH client**
- **curl** (for copying files)

### On RM2

- **OS:** Codex Linux (any recent version, tested on 20251010153257)
- **Bash:** ✓ (already installed)
- **GCC/Make:** ✗ (not needed—you'll cross-compile on PC)

### Network

- **PC and RM2 on same network** (or VPN tunnel via SSH)
- **SSH access to RM2 as root**
- **Default RM2 IP:** `192.168.1.137` (you may need to adjust)

---

## Part 1: One-Time Setup (PC)

### Step 1: Install Python Dependencies

```bash
# Install required Python packages
pip install svgpathtools shapely numpy --break-system-packages
```

Verify installation:
```bash
python3 -c "import svgpathtools, shapely; print('OK')"
```

### Step 2: Set Up Cross-Compilation Toolchain

The C hook requires ARM cross-compiler. Install on PC:

**Ubuntu/Debian:**
```bash
sudo apt-get install gcc-arm-linux-gnueabihf
```

**macOS (via Homebrew):**
```bash
brew install arm-linux-gnueabihf-binutils
```

**Windows (WSL2):**
```bash
sudo apt-get install gcc-arm-linux-gnueabihf
```

Verify installation:
```bash
arm-linux-gnueabihf-gcc --version
```

Should show something like:
```
arm-linux-gnueabihf-gcc (GCC) 10.2.1 20210110
```

### Step 3: Build the Injection Hook

Navigate to your project directory:

```bash
cd C:\Users\NAVY\Documents\Arduino\rm2-inject-v3
```

Build the ARM binary:

```bash
./scripts/build.sh
```

Output:
```
Building RM2 injection system...
Build complete: ./build/inject_hook.so
Size: 14K
```

The compiled binary is at: `./build/inject_hook.so`

### Step 4: Find Your RM2 IP Address

Connect RM2 to WiFi, then find its IP:

```bash
# Scan your network (replace with your subnet)
nmap -sn 192.168.1.0/24 | grep -i remarkable

# Or check RM2's network settings directly via SSH
ssh root@192.168.1.137 "hostname -I"
```

Note the IP address. We'll use it throughout.

---

## Part 2: Deploy to RM2 (One-Time)

### Step 1: Deploy Build Artifacts

```bash
./scripts/deploy.sh 192.168.1.137
```

This copies:
- `inject_hook.so` (14 KB ARM binary)
- `server.sh` (bash server daemon)

Output:
```
Deploying to RM2 at 192.168.1.137...
✓ Copying inject_hook.so...
✓ Copying server.sh...
✓ Files verified on RM2

Files on RM2:
total 24K
-rwxr-xr-x 1 root root 14K inject_hook.so
-rwxr-xr-x 1 root root 4.5K server.sh
```

### Step 2: Test SSH Access

Verify you can SSH to RM2:

```bash
ssh root@192.168.1.137 "echo 'SSH OK'; uname -a"
```

Expected output:
```
SSH OK
Linux remarkable 5.4.70-v1.6.2-rm11x #1 SMP ... GNU/Linux
```

### Step 3: Add RM2 IP to Your Console Script

Edit `./scripts/console.sh` and set your RM2 IP:

```bash
#!/bin/bash
RM2_IP="192.168.1.137"  # ← Change this to your RM2 IP
# Rest of script...
```

Or create an alias in your `.bashrc`:

```bash
alias rm2-console='./scripts/console.sh 192.168.1.137'
```

---

## Part 3: Daily Workflow

### Starting the Server

Before each work session, start the injection server on RM2:

```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh start'
```

Wait for output:
```
[2025-11-24 10:30:45] Starting RM2 injection server...
[2025-11-24 10:30:45] Created FIFO at /tmp/lamp_inject
[2025-11-24 10:30:47] Xochitl started (PID: 1234)
[2025-11-24 10:30:48] Hook successfully loaded ✓
[2025-11-24 10:30:48] Server started
```

Approximately **2-3 seconds**. Xochitl will briefly black out and restart.

### Converting SVG to Injection Commands

Before injecting, convert your SVG circuit file to pen commands:

```bash
python3 ./tools/svg2inject_pro.py examples/No.svg 2.5 out.txt
```

This produces `out.txt` with PEN_* commands:

```
PEN_DOWN 100 200
PEN_MOVE 150 250
PEN_MOVE 200 240
PEN_UP
PEN_DOWN 300 100
...
```

### Injecting Commands

Use the dedicated injection script to send all commands:

```bash
./scripts/inject_pen_commands.sh out.txt 192.168.1.137
```

Output:
```
========================================
RM2 PEN Command Injection
========================================
File:      out.txt
Target:    192.168.1.137
Commands:  2847

Checking RM2 server status...
✓ Server is running

Estimated time: 0m 28s (at 100 events/sec)

Ready to inject? Press Enter to continue, Ctrl+C to cancel...

============================================
IMPORTANT: Tap pen on RM2 screen NOW
============================================

Sending commands...
✓ Injection complete!
Sent 2847 commands
```

**Critical:** Tap your pen on the RM2 screen after the "Tap pen NOW" message appears. This triggers Xochitl to start processing the queued events.

### Stopping the Server

After you're done, return RM2 to normal mode:

```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh stop'
```

Output:
```
[2025-11-24 11:15:30] Stopping RM2 injection server...
[2025-11-24 11:15:30] Clearing LD_PRELOAD from systemd...
[2025-11-24 11:15:31] Xochitl restarted in normal mode
[2025-11-24 11:15:33] Server stopped
```

---

## Complete Workflow Example

Start-to-finish example with a real circuit:

### 1. Prepare SVG File

Export your circuit from KiCAD as SVG (File → Export → SVG).

Say: `my_filter.svg`

### 2. Start Injection Server

```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh start'
# Wait 3 seconds...
```

### 3. Convert SVG to Commands

```bash
# Scale 2.5x to make it readable
python3 ./tools/svg2inject_pro.py my_filter.svg 2.5 commands.txt

# Output: commands.txt with 3000+ pen commands
```

### 4. Inject into RM2

```bash
./scripts/inject_pen_commands.sh commands.txt 192.168.1.137

# Script waits for your input...
# YOU press Enter
# Script prints: "IMPORTANT: Tap pen on RM2 screen NOW"
# YOU tap your pen on RM2 screen (anywhere)
# Circuit appears in Xochitl!
```

### 5. Annotate with Stylus

Now you can annotate the injected circuit with your pen just like a normal sketch.

### 6. Stop Server (When Done)

```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh stop'
```

---

## Understanding the Commands

The system uses three basic commands:

| Command | Format | Meaning |
|---------|--------|---------|
| `PEN_DOWN` | `PEN_DOWN <x> <y>` | Lower pen to screen at (x, y) |
| `PEN_MOVE` | `PEN_MOVE <x> <y>` | Move pen to (x, y) while drawing |
| `PEN_UP` | `PEN_UP` | Lift pen from screen |

A typical sequence:
```
PEN_DOWN 100 200    # Start drawing at (100, 200)
PEN_MOVE 150 200    # Draw to (150, 200)
PEN_MOVE 200 250    # Draw to (200, 250)
PEN_UP              # Stop drawing

PEN_DOWN 250 100    # Start a new stroke at (250, 100)
PEN_MOVE 300 150    # Draw to (300, 150)
PEN_UP              # Stop
```

---

## Coordinate System

The RM2 display is **1404 × 1872 pixels** in portrait mode.

```
(0,0)                    (1404,0)
  ┌────────────────────────┐
  │                        │
  │    Drawing Area        │ 1872 pixels
  │                        │
  └────────────────────────┘
(0,1872)                (1404,1872)
```

**All coordinates are automatic:** The conversion script and server handle the Wacom digitizer's axis swap internally. You always work with standard display coordinates.

---

## Troubleshooting

### "SSH: Permission denied (publickey)"

Set up key-based SSH to avoid password prompts:

```bash
# On your PC, create SSH key (if you don't have one)
ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa

# Copy to RM2
ssh-copy-id -i ~/.ssh/id_rsa root@192.168.1.137

# Verify
ssh root@192.168.1.137 "echo 'OK'"
```

### "arm-linux-gnueabihf-gcc: command not found"

Install cross-compiler:

```bash
# Ubuntu/Debian
sudo apt-get install gcc-arm-linux-gnueabihf

# macOS
brew install arm-linux-gnueabihf-binutils

# Verify
which arm-linux-gnueabihf-gcc
```

### "FIFO: MISSING" in status

The FIFO (`/tmp/lamp_inject`) is missing on RM2. Create it:

```bash
ssh root@192.168.1.137 "mkfifo /tmp/lamp_inject; chmod 666 /tmp/lamp_inject"
```

Or restart the server:

```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh restart'
```

### "Hook: NOT LOADED" in status

The LD_PRELOAD hook isn't being loaded. Check:

```bash
# Verify hook file exists
ssh root@192.168.1.137 "ls -l /opt/rm2-inject/inject_hook.so"

# Check Xochitl's loaded libraries
ssh root@192.168.1.137 "cat /proc/\$(pidof xochitl)/maps | grep inject"
```

If grep returns nothing, the hook isn't loaded. Restart:

```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh restart'
```

### SVG Conversion is Slow or Memory Issues

For very large SVGs (>500 paths), use the fast converter with reduced detail:

```bash
# Fast mode with path simplification
python3 ./tools/svg2inject_pro.py large_circuit.svg 2.0 out.txt

# If still slow, reduce max_error in svg2inject_pro.py
# Lower max_error = fewer points = faster (but less accurate)
```

### Injected Circuit Looks Wrong

Common causes:

1. **Scale too small:** Increase scale parameter (try 2.5 instead of 1.0)
2. **Wrong coordinates:** Check if paths are off-screen. Adjust x/y in conversion
3. **SVG has text:** Text rendering is basic. Re-export SVG without text labels

---

## File Structure

After setup, your project looks like:

```
rm2-inject-v3/
├── src/
│   └── inject_hook.c           ← C source (hook logic)
├── build/
│   └── inject_hook.so          ← Compiled ARM binary
├── tools/
│   ├── server.sh               ← RM2 bash server daemon
│   ├── svg2inject_pro.py       ← SVG → PEN commands converter
│   └── console.sh              ← Old interactive console (legacy)
├── scripts/
│   ├── build.sh                ← Build cross-compiler binary
│   ├── deploy.sh               ← Deploy to RM2
│   ├── console.sh              ← Launcher for console
│   └── inject_pen_commands.sh  ← Inject PEN_* commands (MAIN)
├── examples/
│   └── No.svg                  ← Example circuit
├── INSTALL_AND_USAGE.md        ← You are here
└── DEVELOPMENT_HISTORY.md      ← Technical deep-dive (optional reading)
```

---

## Advanced Usage

### Using Different Scales

```bash
# Small (fits more on page but harder to read)
python3 ./tools/svg2inject_pro.py circuit.svg 1.5 out.txt

# Large (fewer paths, easier to read)
python3 ./tools/svg2inject_pro.py circuit.svg 3.0 out.txt
```

### Positioning on Page

The converters place your circuit at (0,0). To place elsewhere, edit the output file:

```bash
# This will place circuit starting at (100, 100)
sed 's/PEN_DOWN \([0-9]*\) \([0-9]*\)/PEN_DOWN $((\1+100)) $((\2+100))/g' out.txt > positioned.txt
```

Or modify the Python converter directly (lines in `svg2inject_pro.py`).

### Checking Injection Status in Real-Time

Watch RM2's log while injecting:

```bash
# Terminal 1: Start injection
./scripts/inject_pen_commands.sh commands.txt 192.168.1.137

# Terminal 2: Watch RM2 logs
ssh root@192.168.1.137 "tail -f /var/log/rm2-inject.log"
```

### Manual Command Testing

Send individual commands directly:

```bash
# Start server
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh start'

# Send a test stroke
ssh root@192.168.1.137 "echo 'PEN_DOWN 500 500' > /tmp/lamp_inject"
ssh root@192.168.1.137 "echo 'PEN_MOVE 600 600' > /tmp/lamp_inject"
ssh root@192.168.1.137 "echo 'PEN_UP' > /tmp/lamp_inject"

# Tap pen on RM2 to see it
```

---

## Performance Notes

- **SVG conversion:** 1-3 seconds for typical circuits (<300 paths)
- **Command injection:** ~25ms per command (100 commands/second)
- **Total circuit injection:** 30-120 seconds depending on path count
- **Pen tap response:** Immediate (queued commands execute on tap)

---

## Known Limitations

1. **Text rendering:** SVG text is not supported. Re-export without text labels.
2. **Complex fills:** Fill patterns use simple hatching, not solid fills.
3. **Single injection per session:** Complete one injection before starting another (or restart server).

---

## Next Steps

1. ✓ Install Python dependencies
2. ✓ Set up cross-compiler
3. ✓ Build injection hook
4. ✓ Deploy to RM2
5. **→ Use the system:** Export circuit as SVG → Convert → Inject

For technical details on how the system works, see `DEVELOPMENT_HISTORY.md`.

---

## Getting Help

**Common issues:**

- `SSH: Permission denied` → Set up SSH key (see Troubleshooting)
- `Hook: NOT LOADED` → Restart server
- `Circuit looks wrong` → Check scale and position parameters
- `No output from conversion` → Check SVG file with `inkscape` or other SVG tool

**For detailed understanding of the architecture, command flow, and design decisions, refer to `DEVELOPMENT_HISTORY.md`.**
