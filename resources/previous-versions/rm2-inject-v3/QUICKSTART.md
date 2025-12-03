# RM2 Injection System - Quick Reference

## One-Time Setup

```bash
# 1. Install dependencies
pip install svgpathtools shapely numpy --break-system-packages

# 2. Install cross-compiler
sudo apt-get install gcc-arm-linux-gnueabihf

# 3. Build injection hook
cd /path/to/rm2-inject-v3
./scripts/build.sh

# 4. Deploy to RM2
./scripts/deploy.sh 192.168.1.137
```

---

## Daily Workflow (4 Steps)

### 1. Start Injection Server

```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh start'
```

Wait for: `✓ Hook successfully loaded`

### 2. Convert SVG to PEN Commands

```bash
python3 ./tools/svg2pen.py my_circuit.svg 2.5 commands.txt
```

Output: `commands.txt` with PEN_DOWN/PEN_MOVE/PEN_UP

### 3. Inject Commands

```bash
./scripts/pen_inject.sh commands.txt 192.168.1.137
```

When prompted: **Tap your pen on RM2 screen**

### 4. Stop Server (When Done)

```bash
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh stop'
```

---

## Complete Example

```bash
# Start server
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh start'

# Convert circuit to commands (2.5x scale)
python3 ./tools/svg2pen.py my_filter.svg 2.5 circuit_commands.txt

# Inject and follow prompts
./scripts/pen_inject.sh circuit_commands.txt 192.168.1.137
# → Press Enter
# → Tap pen on RM2
# → Circuit appears!

# When done, stop server
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh stop'
```

---

## Key Parameters

| Parameter | Values | Notes |
|-----------|--------|-------|
| `scale` | 1.0 - 3.0 | 2.5 is readable, 1.0 is tiny, 3.0 may not fit |
| `RM2_IP` | 192.168.x.x | Find with: `nmap -sn 192.168.1.0/24` |
| Input format | PEN_DOWN x y | Coordinates in display pixels (0-1404, 0-1872) |

---

## Coordinate System

```
(0, 0)                                    (1404, 0)
  ┌─────────────────────────────────────────┐
  │                                         │
  │  1404 × 1872 pixels (portrait mode)    │
  │                                         │
  └─────────────────────────────────────────┘
(0, 1872)                            (1404, 1872)
```

---

## Troubleshooting Commands

```bash
# Check RM2 connectivity
ping 192.168.1.137

# Check SSH access
ssh root@192.168.1.137 "echo OK"

# Check server status
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh status'

# View injection logs
ssh root@192.168.1.137 "tail -f /var/log/rm2-inject.log"

# Restart server (fixes most issues)
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh restart'

# Check if hook is loaded
ssh root@192.168.1.137 "grep inject_hook /proc/\$(pidof xochitl)/maps"
```

---

## File Descriptions

### PC Side

| File | Purpose |
|------|---------|
| `svg2pen.py` | SVG → PEN_* command converter (MAIN) |
| `scripts/pen_inject.sh` | Send PEN_* commands to RM2 (MAIN) |
| `scripts/build.sh` | Cross-compile C hook |
| `scripts/deploy.sh` | Deploy binaries to RM2 |
| `src/inject_hook.c` | C hook source (LD_PRELOAD) |
| `build/inject_hook.so` | Compiled ARM binary |

### RM2 Side (at `/opt/rm2-inject/`)

| File | Purpose |
|------|---------|
| `inject_hook.so` | Loaded via LD_PRELOAD, intercepts Wacom input |
| `server.sh` | Bash daemon managing Xochitl lifecycle |

---

## Common Scale Values

| Scale | Use Case |
|-------|----------|
| 1.0 | Very detailed, small circuits (hard to read) |
| 1.5 | Normal size, detailed components |
| 2.0 | Readable, good balance |
| 2.5 | Large, very readable (default recommended) |
| 3.0 | Very large, but may not fit on page |

---

## Input/Output Format

### PEN Command Format

```
PEN_DOWN 100 200      # Lower pen at (100, 200)
PEN_MOVE 150 200      # Draw line to (150, 200)
PEN_MOVE 200 250      # Continue to (200, 250)
PEN_UP                # Lift pen

PEN_DOWN 300 100      # Start new stroke
PEN_MOVE 350 150      # Draw
PEN_UP                # Stop
```

### SVG Conversion Output

```bash
$ python3 ./tools/svg2pen.py circuit.svg 2.5
Reading SVG: circuit.svg
Found 47 paths
Generated 2847 points → 5694 commands
```

Output to stdout or file:
```
PEN_DOWN 0 0
PEN_MOVE 10 5
PEN_MOVE 20 10
PEN_UP
...
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| SVG conversion | 1-3 seconds |
| Command rate | ~100 cmds/sec |
| Typical circuit | 2000-5000 commands |
| Total injection | 20-60 seconds |
| Latency (pen tap to drawing) | Immediate |

---

## Architecture Overview

```
PC (your computer)
├─ svg2pen.py       (Python SVG → PEN_* conversion)
│  │
│  └─→ commands.txt (PEN_DOWN/MOVE/UP format)
│
└─ pen_inject.sh    (bash script)
   │
   └─→ SSH tunnel to RM2
       │
       └─→ /tmp/lamp_inject (named pipe/FIFO)
           │
           └─→ inject_hook.so (C LD_PRELOAD library)
               │
               └─→ Wacom digitizer (/dev/input/event1)
                   │
                   └─→ Xochitl (receives synthetic stylus events)
```

---

## System Assumptions

✓ RM2 running recent Codex Linux
✓ SSH access as root
✓ Xochitl running
✓ Wacom digitizer at `/dev/input/event1`
✓ PC and RM2 on same network (or SSH tunnel)

---

## For More Details

- **Installation & Usage:** See `INSTALL_AND_USAGE.md`
- **Technical Deep-Dive:** See `DEVELOPMENT_HISTORY.md`
- **Architecture Details:** See `DEVELOPMENT_HISTORY.md` → Why This Architecture section
