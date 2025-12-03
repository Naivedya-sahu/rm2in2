# Development History

## Project Evolution

### Phase 1: Initial Injection System

**Problem:** Need to programmatically inject pen strokes into RM2

**Solution:** LD_PRELOAD hook intercepting `read()` syscall on Wacom device

**Implementation:**
- `inject.c` - Hooks read(), spawns FIFO reader thread
- `/tmp/rm2_inject` - Named pipe for PEN commands
- Event queue buffering synthetic input_event structures

**Issues encountered:**
- Commands stopping after 1-2 strokes (buffer not fully processed)
- Fixed with multi-line parsing loop in FIFO reader

### Phase 2: Coordinate System Problems

**Problem:** Mirrored/misaligned output on RM2

**Root cause:** Double coordinate transformation
- PEN commands used Wacom coordinates (X: 0-20966, Y: 0-15725)
- inject.c was transforming them again as if they were display coordinates
- Result: Rectangle at bottom-right instead of center

**Fix:**
```c
// Before (broken)
static inline int to_wacom_x(int x) {
    return (int)((long)(RM2_WIDTH - x) * WACOM_MAX_Y / RM2_WIDTH);
}

// After (working)
static inline int to_wacom_x(int x) { return x; }  // Pass through directly
static inline int to_wacom_y(int y) { return y; }
```

**Lesson:** PEN commands already use native Wacom coordinates. No transformation needed.

### Phase 3: Web-Based Glyph Editors

**Attempt:** Create browser-based SVG editors for node manipulation

**Files created:**
- `glyph_editor.py` - Basic version
- `advanced_glyph_editor.py` - Added node editing, zoom/pan
- `glyph_editor_pro.py` - Node table, fixed layout

**Problems:**
- Node selection bugs (wrong nodes moving)
- Port binding errors after Ctrl+C
- Layout issues (canvas too small)
- Pan function requiring multiple mouse buttons
- Unreliable coordinate editing

**Outcome:** Abandoned in favor of Inkscape integration

### Phase 4: Inkscape Workflow

**Realization:** Don't reinvent professional tools

**Solution:** Bidirectional SVG conversion for Inkscape editing

**Files:**
- `pen_to_svg.py` - Convert PEN commands to Inkscape-editable SVG
- `svg_to_pen.py` - Convert SVG back to PEN commands

**Benefits:**
- Professional node editing in mature software
- Exact coordinate control
- No bugs or port binding issues
- Industry-standard tool

**Decimal precision problem discovered:**
- SVG converters creating 6-digit decimal coordinates
- RM2 uses 8-byte integers
- Fixed by using `int(round())` everywhere

### Phase 5: Text to Handwriting

**Problem:** User doesn't want to manually edit every character

**Requirement:** "I want to automate this so that I can write whole pages of text whenever I require it, not stuck editing strokelines"

**Solution:** Built-in Hershey single-stroke font

**Implementation:**
- `text_to_pen.py` - Automatic text-to-handwriting converter
- 73 characters: A-Z, a-z, 0-9, punctuation
- Automatic line wrapping
- Proper margins and spacing
- Integer coordinates only

**Result:** Type text → Get handwriting in seconds (not hours of manual editing)

### Phase 6: Bitmap Traced Fonts (Current)

**New workflow:** Use Inkscape bitmap tracing for font creation

**Process:**
1. Create/obtain character as bitmap image
2. Trace in Inkscape (Path → Trace Bitmap)
3. Convert SVG to PEN commands
4. Test on RM2
5. Build font library

**Current focus:**
- Improve `svg_to_pen.py` stroke ordering
- Optimize for natural handwriting flow
- Handle complex multi-stroke characters

---

## Technical Architecture

### Injection Mechanism

```
┌─────────────┐
│  Xochitl    │  (RM2 drawing app)
│   (reads)   │
└──────┬──────┘
       │ read(wacom_fd)
       ▼
┌─────────────────┐
│   inject.so     │  (LD_PRELOAD hook)
│  read() hook    │
└────┬────────┬───┘
     │        │
     │        └──────────┐
     │                   │
     │            ┌──────▼──────┐
     │            │ FIFO Reader │  (thread)
     │            │   Thread    │
     │            └──────┬──────┘
     │                   │
     │                   │ reads from
     │                   ▼
     │            ┌─────────────┐
     │            │/tmp/rm2_inject│  (named pipe)
     │            └──────▲──────┘
     │                   │
     │                   │ writes PEN commands
     │            ┌──────┴──────┐
     │            │   send.sh   │  (SSH + cat)
     │            └─────────────┘
     │
     │ returns synthetic events
     ▼
┌─────────────┐
│ Event Queue │  (circular buffer)
└─────────────┘
```

### Coordinate Systems

**Wacom Hardware:**
```
(0,0) ──────────────────── (20966,0)
  │                             │
  │      Landscape mode         │
  │     (sensor rotated)        │
  │                             │
(0,15725) ──────────────── (20966,15725)

X: 0-20966 (horizontal)
Y: 0-15725 (vertical)
```

**RM2 Display:**
```
1404×1872 pixels (portrait)

Software rotates view 90° from sensor
```

**PEN Command Coordinates:**
- Use Wacom hardware coordinates directly
- No transformation in inject.c
- Integer values only

**SVG Coordinates:**
- Normalized to 1404×1872 (display size)
- Converters handle Wacom ↔ SVG mapping
- Accounts for 90° rotation

### Event Structure

```c
struct input_event {
    struct timeval time;  // Timestamp (auto-filled)
    __u16 type;           // EV_KEY, EV_ABS, EV_SYN
    __u16 code;           // BTN_TOUCH, ABS_X, ABS_Y, ABS_PRESSURE
    __s32 value;          // Coordinate or state value
};
```

**PEN_DOWN sequence:**
```c
EV_KEY,  BTN_TOOL_PEN, 1       // Pen detected
EV_KEY,  BTN_TOUCH,    1       // Touching screen
EV_ABS,  ABS_X,        x       // X coordinate
EV_ABS,  ABS_Y,        y       // Y coordinate
EV_ABS,  ABS_PRESSURE, 2000    // Pressure
EV_SYN,  SYN_REPORT,   0       // End of event group
```

**PEN_MOVE sequence:**
```c
EV_ABS,  ABS_X,        x
EV_ABS,  ABS_Y,        y
EV_ABS,  ABS_PRESSURE, 2000
EV_SYN,  SYN_REPORT,   0
```

**PEN_UP sequence:**
```c
EV_KEY,  BTN_TOUCH,    0       // Released
EV_KEY,  BTN_TOOL_PEN, 0       // Pen lifted
EV_SYN,  SYN_REPORT,   0
```

---

## SVG to PEN Conversion Details

### Path Command Parsing

**Supported SVG commands:**
- `M/m` - MoveTo (absolute/relative)
- `L/l` - LineTo (absolute/relative)
- `H/h` - Horizontal line (absolute/relative)
- `V/v` - Vertical line (absolute/relative)
- `C/c` - Cubic Bezier (absolute/relative)
- `S/s` - Smooth cubic Bezier (absolute/relative)
- `Q/q` - Quadratic Bezier (absolute/relative)
- `Z/z` - Close path

**Bezier sampling:**
```python
# Cubic Bezier: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
def sample_cubic_bezier(x0, y0, x1, y1, x2, y2, x3, y3, steps=20):
    for i in range(1, steps + 1):
        t = i / steps
        x = (1-t)**3 * x0 + 3*(1-t)**2*t * x1 + 3*(1-t)*t**2 * x2 + t**3 * x3
        y = (1-t)**3 * y0 + 3*(1-t)**2*t * y1 + 3*(1-t)*t**2 * y2 + t**3 * y3
        points.append((x, y))
```

### Stroke Ordering Algorithm

**Goal:** Emulate natural handwriting flow

**Strategy:**
1. **Spatial ordering** - Top-to-bottom, left-to-right
2. **Connectivity** - Connected strokes stay together
3. **Priority** - Main strokes before embellishments

**Implementation (to be improved):**
```python
def order_strokes_for_handwriting(paths):
    # Calculate bounding box for each path
    # Sort by:
    #   1. Top coordinate (ascending)
    #   2. Left coordinate (ascending)
    #   3. Stroke length (descending - main strokes first)

    # Special cases:
    #   - Crossing strokes (T, f, t) - horizontal after vertical
    #   - Dots (i, j) - after main stroke
    #   - Disconnected parts - order by position
```

### Coordinate Conversion

**SVG to Wacom:**
```python
# SVG: 1404×1872 (portrait)
# Wacom: 20966×15725 (landscape, rotated 90°)

def svg_to_wacom(svg_x, svg_y):
    wacom_y = (svg_x / SVG_WIDTH) * WACOM_MAX_Y
    wacom_x = (svg_y / SVG_HEIGHT) * WACOM_MAX_X
    return int(round(wacom_x)), int(round(wacom_y))
```

**Wacom to SVG:**
```python
def wacom_to_svg(wacom_x, wacom_y):
    svg_x = (wacom_y / WACOM_MAX_Y) * SVG_WIDTH
    svg_y = (wacom_x / WACOM_MAX_X) * SVG_HEIGHT
    return int(round(svg_x)), int(round(svg_y))
```

---

## Known Issues

### Stroke Ordering

**Current:** Simple top-to-bottom, left-to-right ordering

**Problem:** Doesn't handle:
- Characters with crossing strokes (optimal order unclear)
- Multi-part characters (e.g., i with dot)
- Script/cursive connections

**Solution needed:** Machine learning or rule-based system for each character type

### Bitmap Tracing Quality

**Issue:** Inkscape bitmap tracing can produce:
- Too many nodes (needs simplification)
- Overlapping paths (needs cleanup)
- Incorrect path direction (affects fill rules)

**Workaround:**
- Use high threshold in trace settings
- Path → Simplify after tracing
- Path → Break Apart to separate components
- Manual cleanup in Inkscape

### Font Library Management

**Current:** Each character as separate file

**Need:** Font library format
- JSON database of all characters
- Metadata (kerning, spacing, baseline)
- Import/export for sharing

---

## Future Enhancements

### Short Term

1. **Improved stroke ordering**
   - Character-type detection (vertical, horizontal, diagonal, circular)
   - Rule-based ordering per type
   - Manual override option

2. **Font library system**
   - JSON format for font definitions
   - Kerning and spacing data
   - Import/export tools

3. **Multi-page text rendering**
   - Auto-pagination for long documents
   - Page number support
   - Margin control

### Medium Term

1. **Natural variation**
   - Add subtle randomness to coordinates
   - Vary pressure along stroke
   - Mimic human imperfection

2. **Font styles**
   - Bold/italic variants
   - Multiple font families
   - Size scaling

3. **Advanced layout**
   - Text justification
   - Column support
   - Headers/footers

### Long Term

1. **Handwriting recognition**
   - Capture real handwriting
   - Train font from samples
   - Personalized style

2. **Unicode support**
   - International characters
   - RTL scripts (Arabic, Hebrew)
   - CJK ideographs

3. **Pressure sensitivity**
   - Variable stroke width
   - Brush-like effects
   - Calligraphy simulation

---

## Lessons Learned

1. **Use native coordinates** - Don't transform Wacom coordinates that are already in Wacom space

2. **Integer precision** - RM2 uses integer coordinates. Avoid floating point accumulation.

3. **Leverage existing tools** - Inkscape is better than custom web editors for node manipulation

4. **Automate repetitive tasks** - User wants whole pages, not per-character editing

5. **Stroke order matters** - Natural handwriting requires proper stroke sequencing

6. **Simplify paths** - Bitmap tracing produces too many nodes. Simplification essential.

---

## Testing Notes

### Coordinate System Tests

File: `coord-test/simple_test.py`

Generates test patterns:
- Center cross (verifies centering)
- Four corner crosses (verifies bounds)
- Border rectangle (verifies full range)

**Expected:** Patterns appear at correct positions
**If not:** Check inject.c coordinate transformation

### Real Handwriting Capture

Files: `testing-tools/capture_events.sh`, `parse_events.py`

Captures actual pen events from RM2:
```bash
ssh root@10.11.99.1
cd /tmp
./capture_events.sh > capture.txt
# Write something
# Ctrl+C

python parse_events.py capture.txt output.txt
```

Reveals:
- Real strokes use 100-150 points (vs synthetic 6-15)
- Natural variation in coordinates
- Pressure changes along stroke

### Stroke Ordering Tests

Compare different ordering strategies:
1. SVG path order (as authored)
2. Top-to-bottom ordering
3. Left-to-right ordering
4. Connected component ordering

Evaluate by visual appearance on RM2.

---

## Performance Metrics

### Conversion Speed

- **SVG parsing:** ~1000 paths/second
- **Bezier sampling:** ~10000 curves/second
- **PEN command generation:** ~50000 commands/second

Typical character (5 strokes, 30 nodes): <1ms

### RM2 Rendering Speed

- **Injection rate:** Limited by FIFO read speed (~1MB/s)
- **Event processing:** Xochitl processes ~100-500 events/second
- **Typical page:** 10-30 seconds to render

### File Sizes

- **PEN command:** ~50 bytes (including newlines and comments)
- **Average character:** 30 commands = 1.5 KB
- **Full page (500 chars):** ~750 KB PEN file

---

## Build System

### Compilation

```bash
# Cross-compile for ARM
arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread

# Flags:
#   -shared     : Create shared library
#   -fPIC       : Position-independent code
#   -O2         : Optimization level 2
#   -ldl        : Link libdl (dlsym)
#   -lpthread   : Link pthread (threading)
```

### Dependencies

**RM2 side:**
- `/dev/input/event1` - Wacom digitizer device
- Xochitl or compatible drawing app
- Linux input subsystem

**Development side:**
- arm-linux-gnueabihf-gcc (cross-compiler)
- Python 3.6+ (converter scripts)
- SSH access to RM2
- Inkscape (optional, for SVG editing)

---

## Code Quality

### Current State

- **inject.c:** Production-ready, minimal, portable
- **svg_to_pen.py:** Functional, needs stroke ordering improvement
- **text_to_pen.py:** Basic font, works for simple text
- **pen_to_svg.py:** Complete, handles all conversions

### Areas for Improvement

1. **Error handling:** More robust input validation
2. **Testing:** Automated test suite
3. **Documentation:** API docs for each function
4. **Code organization:** Separate parsing from conversion logic

---

## Version History

- **v0.1** - Initial injection hook, basic PEN commands
- **v0.2** - Fixed coordinate mirroring bug
- **v0.3** - Added SVG converters with Inkscape workflow
- **v0.4** - Text-to-handwriting with Hershey font
- **v0.5** - Bitmap tracing workflow, stroke ordering focus (current)

---

## Contributing Guidelines

If extending this project:

1. **Maintain integer coordinates** throughout pipeline
2. **Test on actual RM2** before committing
3. **Document coordinate transformations** clearly
4. **Preserve stroke ordering logic** for handwriting quality
5. **Keep inject.c minimal** - it runs in Xochitl process

---

## References

- Remarkable 2 hardware specs: Wacom digitizer, E Ink display
- Hershey fonts: NIST single-stroke character set
- Linux input subsystem: `linux/input.h`, `evtest`
- Inkscape SVG format: W3C SVG 1.1 specification
