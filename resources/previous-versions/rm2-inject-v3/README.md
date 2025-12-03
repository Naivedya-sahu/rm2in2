# RM2 Circuit Injection System

**Inject SVG circuit diagrams directly into your reMarkable 2 e-ink tablet as native pen strokes.**

---

## What This Does

Export circuit diagrams from KiCAD as SVG → Inject into RM2 notebook → Annotate with pen

No manual drawing. Full stylus annotation support.

---

## Quick Start (5 Minutes)

### 1. Install & Build (One-Time)

```bash
# Install Python packages
pip install svgpathtools shapely numpy --break-system-packages

# Install ARM cross-compiler
sudo apt-get install gcc-arm-linux-gnueabihf

# Build and deploy to RM2
./scripts/build.sh
./scripts/deploy.sh 192.168.1.137
```

See **INSTALL_AND_USAGE.md** for detailed setup.

### 2. Daily Workflow

```bash
# Start server on RM2
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh start'

# Convert your circuit to pen commands
python3 ./tools/svg2pen.py my_circuit.svg 2.5 commands.txt

# Inject into RM2
./scripts/pen_inject.sh commands.txt 192.168.1.137
# → Follow prompts
# → Tap pen on RM2 screen when prompted
# → Circuit appears!

# When done
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh stop'
```

See **QUICKSTART.md** for reference.

---

## How It Works

### Architecture

```
Your PC                                    Your RM2
─────────────────────────────────────────────────────

SVG file (from KiCAD)
    │
    ▼
svg2pen.py (Python)
Convert to PEN_* commands
    │
    ▼
commands.txt (plain text)
    │
    ├──→ [Can save/reuse/debug]
    │
    ▼
pen_inject.sh (Bash)
Send over SSH to RM2
    │
    └──→ /tmp/lamp_inject (FIFO)
            │
            ▼
        inject_hook.so (C LD_PRELOAD)
        Intercepts Wacom input
            │
            ▼
        Xochitl (note-taking app)
        Displays injected circuit
            │
            ▼
        Your Notebook
        ✓ Ready for annotation
```

**Why this approach?**
- LD_PRELOAD bypasses Xochitl's input filtering
- Works on newest RM2 OS versions
- Reliable, tested, production-ready
- Allows full stylus annotation after injection

See **ARCHITECTURE.md** for technical details.

---

## System Requirements

### PC
- Python 3.10+
- Bash 4+
- ARM cross-compiler (gcc-arm-linux-gnueabihf)
- SSH client
- Supported: Windows (WSL2), macOS, Linux

### RM2
- Codex Linux (any recent version)
- Bash (already installed)
- SSH access as root
- WiFi connectivity to PC

### Network
- PC and RM2 on same network (or VPN/SSH tunnel)
- Default RM2 IP: 192.168.1.137 (may vary)

---

## Files Overview

| Component | Files | Purpose |
|-----------|-------|---------|
| **SVG Processing** | `tools/svg2pen.py` | Convert SVG circuits to pen commands |
| **Pen Injection** | `scripts/pen_inject.sh` | Send commands to RM2 |
| **RM2 Server** | `tools/server.sh` | Manage Xochitl on RM2 |
| **C Hook** | `src/inject_hook.c` | LD_PRELOAD intercepts Wacom input |
| **Build** | `scripts/build.sh` | Cross-compile C hook |
| **Deploy** | `scripts/deploy.sh` | Copy binaries to RM2 |

See file structure at end of **ARCHITECTURE.md**.

---

## Documentation

### For Setup
→ **INSTALL_AND_USAGE.md** - Complete step-by-step guide
- One-time setup
- Deploy to RM2
- Daily workflow with examples
- Troubleshooting

### For Quick Reference
→ **QUICKSTART.md** - At-a-glance reference
- 4-step workflow
- Common parameters
- Coordinate system
- Commands list

### For Technical Details
→ **ARCHITECTURE.md** - How it all works
- Component breakdown
- Data flow diagrams
- Design decisions
- Extension points

### For Context
→ **DEVELOPMENT_HISTORY.md** - How it was built
- Lessons learned
- Design iterations
- Why certain choices were made
- Troubleshooting history

→ **REFACTORING_SUMMARY.md** - What changed
- Before/after comparison
- New vs deprecated files
- Migration guide

---

## Example Workflow

### 1. Design Circuit in KiCAD
```
Your design → Export as SVG
```

### 2. Convert to Pen Commands
```bash
python3 ./tools/svg2pen.py circuit.svg 2.5 cmds.txt
```
Output: `cmds.txt` with 2000-5000 PEN_* commands

### 3. Inject into RM2
```bash
./scripts/pen_inject.sh cmds.txt 192.168.1.137
```
Output: Circuit appears in RM2 notebook

### 4. Annotate with Pen
Use your RM2 stylus to:
- Add labels
- Circle important areas
- Add notes and calculations
- Mark component values

### 5. Export
Screenshot or export notebook as PDF from RM2

---

## Key Concepts

### Command Format
All commands follow this simple format:
```
PEN_DOWN <x> <y>    # Lower pen at coordinate
PEN_MOVE <x> <y>    # Move to coordinate while drawing
PEN_UP              # Lift pen
```

### Coordinate System
RM2 display is **1404 × 1872 pixels** (portrait):
```
(0,0) ─────────────────► (1404,0)
  │
  │  Drawing area
  │  1872 pixels tall
  │
  ▼
(0,1872) ──────────────► (1404,1872)
```

All coordinates automatically handled—you use display coordinates.

### Scalability
SVG converter supports scale factors 1.0–3.0:
- 1.0 = Very detailed, small (hard to read)
- 1.5 = Normal, balanced
- 2.5 = Large, very readable (recommended)
- 3.0 = Huge, may not fit on page

---

## Troubleshooting

### "SSH: Permission denied"
```bash
# Set up SSH key
ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
ssh-copy-id -i ~/.ssh/id_rsa root@192.168.1.137
```

### "Cannot reach RM2"
```bash
# Check IP
ping 192.168.1.137

# Find RM2 on network
nmap -sn 192.168.1.0/24 | grep remarkable

# Check RM2 is on WiFi
ssh root@192.168.1.137 "hostname -I"
```

### "Hook: NOT LOADED"
```bash
# Restart server
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh restart'

# Verify
ssh root@192.168.1.137 '/opt/rm2-inject/server.sh status'
```

### "SVG conversion error"
```bash
# Verify SVG is valid
python3 -c "from svgpathtools import svg2paths; svg2paths('circuit.svg')"

# Try simpler SVG (fewer paths)
# Re-export from KiCAD without text/annotations
```

See **INSTALL_AND_USAGE.md** → Troubleshooting section for more.

---

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| SVG parsing | 1-3 sec | Depends on path complexity |
| Command injection | 30-60 sec | Depends on command count |
| Stylus annotation | Immediate | After injection complete |

Typical complete workflow: 2-3 minutes (mostly waiting).

---

## What's Different From Competition

| Feature | This System | Other Tools |
|---------|---|---|
| Works on new RM2 OS | ✓ | ✗ (rm2fb not supported) |
| SVG circuits | ✓ | ✗ |
| Batch injection | ✓ | ✗ |
| Stylus annotation after | ✓ | Varies |
| Production-ready | ✓ | Partial |
| Documentation | ✓ | Limited |
| Extensible | ✓ | No |

---

## Limitations

- **Text rendering**: SVG text not supported (re-export without text)
- **Complex fills**: Uses hatching, not solid fills
- **Single injection per session**: Complete one before starting another

None are blockers for circuit documentation workflow.

---

## Next Steps

1. **Read** INSTALL_AND_USAGE.md for full setup
2. **Build** by running `./scripts/build.sh`
3. **Deploy** with `./scripts/deploy.sh 192.168.1.137`
4. **Use** with `svg2pen.py` + `pen_inject.sh`

---

## Technical Stack

- **SVG Processing**: Python 3 with svgpathtools, shapely, numpy
- **Injection**: Bash over SSH
- **RM2 Server**: Pure bash (no external dependencies)
- **Input Hook**: C with LD_PRELOAD, pthreads, Linux input subsystem
- **Architecture**: Cross-compiled ARM binary, runs on RM2

---

## Files in This Project

```
rm2-inject-v3/
├─ README.md (this file)
├─ INSTALL_AND_USAGE.md          ← Start here for setup
├─ QUICKSTART.md                 ← Daily use reference
├─ ARCHITECTURE.md               ← Technical details
├─ REFACTORING_SUMMARY.md        ← What changed
├─ DEVELOPMENT_HISTORY.md        ← Lessons learned
│
├─ src/
│  └─ inject_hook.c              ← C LD_PRELOAD library
├─ build/
│  └─ inject_hook.so             ← Compiled ARM binary
├─ tools/
│  ├─ svg2pen.py                 ← SVG converter (MAIN)
│  ├─ server.sh                  ← RM2 server daemon
│  └─ (deprecated converters)
├─ scripts/
│  ├─ pen_inject.sh              ← Command injector (MAIN)
│  ├─ build.sh                   ← Build script
│  ├─ deploy.sh                  ← Deploy to RM2
│  └─ (other scripts)
└─ examples/
   └─ No.svg                     ← Example circuit
```

---

## License & Attribution

This system was developed for personal circuit documentation and analysis workflows on the reMarkable 2.

Built with:
- LD_PRELOAD technique inspired by ReCept and other community tools
- Wacom device handling based on Linux input subsystem
- SVG parsing via svgpathtools

Designed for production use with emphasis on reliability and documentation.

---

## Getting Help

**Setup issues?** → INSTALL_AND_USAGE.md  
**How to use?** → QUICKSTART.md  
**How does it work?** → ARCHITECTURE.md  
**Troubleshooting?** → INSTALL_AND_USAGE.md section "Troubleshooting"  
**Technical deep-dive?** → DEVELOPMENT_HISTORY.md  

---

**Ready to inject your first circuit?**

Start with: INSTALL_AND_USAGE.md
