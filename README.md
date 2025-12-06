# rm2in2: Circuit Injection System for reMarkable 2

**Purpose:** Inject SVG circuit diagrams from PC to reMarkable 2 as synthetic stylus strokes for electronics documentation workflows.

**Firmware:** 3.24.0.147 (Beta)  
**Status:** Production-ready architecture identified, implementation in progress

---

## Quick Start

### What Works Now

```bash
# Test coordinate transformation (proven working)
arm-linux-gnueabihf-gcc -o lamp-test-v2 lamp-test-v2.c -lm -static
scp lamp-test-v2 root@10.11.99.1:/opt/
ssh root@10.11.99.1 /opt/lamp-test-v2
```

### Architecture (Simplified)

```
Circuit Diagram (SVG/Photo)
    ↓
Parse & Convert (PC)
    ↓
Generate Pen Commands with Adaptive Interpolation
    ↓
Send to RM2 Daemon (Socket/FIFO)
    ↓
Direct Write to /dev/input/event1
    ↓
Renders in real-time on RM2
```

**Key Insight:** No LD_PRELOAD hooking needed. Direct write to input device works.

---

## Critical Discoveries

### 1. Direct Input Write Works

lamp-test proved that writing directly to `/dev/input/event1` works without:
- ❌ LD_PRELOAD hooks
- ❌ xochitl restart  
- ❌ Input suppression
- ❌ Manual tap to trigger render

**Just open the device and write events. That's it.**

### 2. Coordinate Transformation from lamp (rmkit)

```c
#define WACOMWIDTH 15725.0   // NOT 20966!
#define WACOMHEIGHT 20967.0  // NOT 15725!
#define WACOM_X_SCALAR ((float)DISPLAYWIDTH / (float)WACOMWIDTH)
#define WACOM_Y_SCALAR ((float)DISPLAYHEIGHT / (float)WACOMHEIGHT)

int get_pen_x(int x) {
    return (int)(x / WACOM_X_SCALAR);
}

int get_pen_y(int y) {
    return (int)(WACOMHEIGHT - (y / WACOM_Y_SCALAR));
}

// Event structure (note axis swap):
ev.code = ABS_Y; ev.value = get_pen_x(display_x);  // X → Y
ev.code = ABS_X; ev.value = get_pen_y(display_y);  // Y → X (inverted)
```

**Proven by community, tested on your device, works correctly.**

### 3. Adaptive Interpolation Required

Fixed 100 points causes skewed large circles. Solution:

```c
int calculate_interpolation_points(double distance) {
    int points = (int)(distance / 5.0);  // ~5px between points
    if (points < 10) points = 10;
    if (points > 1000) points = 1000;
    return points;
}
```

**Result:** Smooth curves, endpoints meet properly.

---

## Implementation Status

### Completed ✅

- [x] lamp coordinate transformation identified and tested
- [x] Direct write method proven
- [x] Adaptive interpolation algorithm designed
- [x] Test binaries (lamp-test.c, lamp-test-v2.c)
- [x] Comprehensive documentation
- [x] Repository compatibility analysis

### In Progress 🔄

- [ ] Simple rm2inject daemon (direct write + socket interface)
- [ ] Circuit photo → SVG pipeline (OpenCV)
- [ ] SVG → pen commands with adaptive interpolation
- [ ] PC client tools

### Not Started ⏳

- [ ] Production deployment scripts
- [ ] Sudoku interactive game (optional)
- [ ] genie gesture launcher integration (optional)

---

## Repository Compatibility (Firmware 3.24.0.147)

**Works:**
- ✅ lamp (input injection) - TESTED
- ✅ genie (gesture launcher) - should work
- ✅ pipes-and-paper (screen sharing) - should work
- ✅ Direct injection approach

**Doesn't Work:**
- ❌ rm2fb (max firmware 3.20-3.22)
- ❌ harmony, iago, remux (need rm2fb)
- ❌ yaft, tilem, rocket (need rm2fb)

**See:** REPOS_COMPATIBILITY_ANALYSIS.md

---

## Development Plan

### Phase 1: Core Daemon (2-3 hours)

Build minimal injection daemon:
```c
// rm2inject.c
- Open /dev/input/event1
- Listen on socket (port 9001)
- Parse commands (DOWN x y, MOVE x y, UP)
- Write events with lamp transformation
- Adaptive interpolation
```

### Phase 2: Circuit Pipeline (3-4 hours)

Photo → SVG → Pen Commands:
```python
# photo_to_circuit.py
- OpenCV preprocessing (contrast, threshold, denoise)
- Contour extraction
- SVG generation (1404x1872 canvas)

# svg_to_commands.py
- Parse SVG paths
- Adaptive interpolation (5px target)
- Generate pen commands
```

### Phase 3: Integration & Testing (2-3 hours)

- Deploy daemon to RM2
- Test with circuit photos
- Tune preprocessing parameters
- Measure performance

**Total: ~8-10 hours to working system**

---

## Files Reference

### Core Documentation

- **README.md** (this file) - Project overview
- **ARCHITECTURE_CORRECTION.md** - Why LD_PRELOAD was wrong, correct architecture
- **REPOS_COMPATIBILITY_ANALYSIS.md** - What works on firmware 3.24.x

### Implementation Guides

- **CIRCUIT_PIPELINE.md** - Photo → Circuit injection pipeline
- **CONCRETE_SOLUTION.md** - lamp transformation analysis
- **LAMP_ANALYSIS.md** - lamp dependencies and usage

### Reference

- **FIRMWARE_COMPATIBILITY.md** - Community tools compatibility matrix
- **BACKUP_AND_CLEANUP.md** - Backup scripts, cleanup procedures

### Test Code

- **lamp-test.c** - Basic coordinate transformation test
- **lamp-test-v2.c** - Adaptive interpolation version

### Deprecated (Old LD_PRELOAD Approach)

- **Rm2/src/inject.c** - Old LD_PRELOAD hook (obsolete)
- **PROJECT_STATUS.md** - Historical development notes
- **DEPLOYMENT_GUIDE.md** - Old deployment for LD_PRELOAD system
- **TESTING_GUIDE.md** - Old testing framework

---

## Usage (When Complete)

### Inject Circuit from Photo

```bash
# 1. Take photo of circuit diagram
# 2. Process and inject
python photo_to_circuit.py circuit_photo.jpg | \
python svg_to_commands.py | \
nc 10.11.99.1 9001
```

### Inject from SVG

```bash
python svg_to_commands.py circuit.svg | nc 10.11.99.1 9001
```

### Direct Command Injection

```bash
echo -e "DOWN 700 900\nMOVE 800 1000\nUP" | nc 10.11.99.1 9001
```

---

## Firmware Update Decision

**Current:** 3.24.0.147  
**Available:** 3.24.0.179  

**Recommendation:** STAY on 0.147 until production system working

**Reasons:**
1. Direct write approach proven on 0.147
2. Input subsystem unlikely to change
3. Update adds debugging complexity
4. rm2fb won't work on either version
5. Can update later if needed

---

## Key Learnings

1. **LD_PRELOAD was completely unnecessary** - Spent 2 weeks on wrong architecture
2. **lamp has the proven transformation** - Community-tested, battle-hardened
3. **Adaptive interpolation is critical** - Fixed point count causes artifacts
4. **rm2fb not needed for input injection** - Only needed for display apps
5. **Direct write is simple and stable** - ~200 lines of C code

---

## Next Actions

1. Build rm2inject daemon (core functionality)
2. Implement circuit photo pipeline (OpenCV)
3. Test end-to-end with sample circuits
4. Deploy to production
5. (Optional) Add sudoku game, genie integration

---

## Contributing

This is a personal project for electronics documentation workflow. If you find the direct injection approach useful:

- lamp transformation from: https://github.com/rmkit-dev/rmkit
- rm2fb analysis from: https://github.com/timower/rM2-stuff
- Community repos in: `resources/repos/`

---

## License

Project-specific code: MIT  
lamp transformation: From rmkit (MIT License)  
OpenCV, other dependencies: See respective licenses

---

**Last Updated:** December 4, 2024  
**Author:** NAVY  
**Contact:** Via GitHub issues
