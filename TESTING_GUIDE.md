# Coordinate System Testing Guide

This guide explains how to empirically determine the correct coordinate transformation for the RM2 input injection system.

## Overview

The problem: We need to find the transformation that converts SVG coordinates (1404×1872 portrait) to Wacom hardware coordinates (0-20966 × 0-15725) such that drawings appear correctly on screen.

## Testing Strategy

We use a **two-pronged approach**:

1. **Capture Method** - Record real pen input to understand hardware behavior
2. **Injection Method** - Test different transformations to find what works

## Prerequisites

### Hardware
- Remarkable 2 tablet with SSH access
- USB or WiFi connection to RM2
- PC/Linux workstation for development

### Software
- ARM cross-compiler installed: `arm-linux-gnueabihf-gcc`
- Python 3.6+
- `evtest` installed on RM2 (if using capture method)
- SSH/SCP access configured

## Quick Start

### 1. Build and Deploy

```bash
# Build injection hook
make clean
make server

# Deploy to RM2 (adjust IP if needed)
make deploy RM2_IP=10.11.99.1
```

### 2. Start Injection Hook on RM2

SSH to your RM2:
```bash
ssh root@10.11.99.1
```

Stop xochitl and restart with hook:
```bash
systemctl stop xochitl
LD_PRELOAD=/opt/rm2in2/inject.so /usr/bin/xochitl &
```

You should see:
```
[RM2] Injection hook loaded - TESTING VERSION
[RM2] This version has NO coordinate transformation
```

### 3. Generate Test Patterns

On your PC:
```bash
# Generate all test patterns with all transformations
make test-patterns

# This creates test-output/ with files like:
#   corners_A_Direct.txt
#   corners_B_Swap.txt
#   corners_C_SwapFlipY.txt
#   ... (32 files total - 4 patterns × 8 transforms)
```

### 4. Test Each Transformation

Send test patterns one by one:

```bash
# Test Transform A (direct mapping)
./Rm2in2/scripts/send.sh test-output/corners_A_Direct.txt

# Open notes app on RM2 and tap screen
# Observe where the 4 dots appear

# Test Transform B (swap axes)
./Rm2in2/scripts/send.sh test-output/corners_B_Swap.txt

# Repeat for all transforms...
```

### 5. Identify Correct Transform

The **correct transformation** will produce:
- ✅ Four dots near the actual corners of the screen
- ✅ Cross pattern appears as centered + shape
- ✅ Circle appears circular (not elliptical)
- ✅ Grid is evenly spaced

## Method 1: Capture Real Pen Events

This method analyzes what the hardware actually reports when you draw.

### Step 1: Capture Events on RM2

```bash
# On RM2
cd /opt/rm2in2
./capture_pen_events.sh /tmp/pen_capture.txt
```

### Step 2: Draw Test Pattern

While capture is running, draw this pattern on screen:

```
1 ----------- 2
|             |
|             |
|      C      |
|             |
|             |
3 ----------- 4
```

Draw in order:
1. Tap top-left corner (mark "1")
2. Tap top-right corner (mark "2")
3. Tap bottom-left corner (mark "3")
4. Tap bottom-right corner (mark "4")
5. Tap center (mark "C")

Press Ctrl+C to stop capture.

### Step 3: Copy and Analyze

```bash
# Copy capture file to PC
scp root@10.11.99.1:/tmp/pen_capture.txt ./

# Parse the events
cd Rm2in2/tests
python parse_captured_events.py ../../pen_capture.txt
```

### Step 4: Analyze Results

The parser will show:
- Coordinate ranges (min/max X and Y)
- Event sequence
- Statistics

Look for patterns:
- Which axis has larger range? (should map to which display dimension)
- Do coordinates increase or decrease as you move right/down?
- What are the actual corner coordinates?

Compare these to expected screen positions to deduce the transformation.

## Method 2: Systematic Transform Testing

This method tries all reasonable transformations systematically.

### Transform Options Being Tested

| ID | Name | Formula |
|----|------|---------|
| A | Direct | `wacom_x = svg_x * scale_x`, `wacom_y = svg_y * scale_y` |
| B | Swap | `wacom_x = svg_y * scale_y`, `wacom_y = svg_x * scale_x` |
| C | SwapFlipY | `wacom_x = (HEIGHT - svg_y) * scale_y`, `wacom_y = svg_x * scale_x` |
| D | SwapFlipX | `wacom_x = svg_y * scale_y`, `wacom_y = (WIDTH - svg_x) * scale_x` |
| E | SwapFlipBoth | Both axes swapped and flipped |
| F | DirectFlipY | Direct with Y flipped |
| G | DirectFlipX | Direct with X flipped |
| H | DirectFlipBoth | Direct with both flipped |

### Test Patterns

#### 1. Corners Pattern

**Purpose:** Validate bounds and basic orientation

**Expected result:**
```
1 -------- 2
|          |
|          |
|          |
3 -------- 4
```

Four dots should appear near the actual screen corners.

#### 2. Cross Pattern

**Purpose:** Validate axis alignment and center position

**Expected result:**
```
    |
----+----
    |
```

Horizontal and vertical lines through center.

#### 3. Grid Pattern

**Purpose:** Validate uniform scaling across entire screen

**Expected result:**
```
1 - 2 - 3
|   |   |
4 - 5 - 6
|   |   |
7 - 8 - 9
```

3×3 grid of evenly spaced dots.

#### 4. Circle Pattern

**Purpose:** Validate aspect ratio and curve rendering

**Expected result:** A perfect circle centered on screen (not elliptical).

### Testing Workflow

For each pattern:

```bash
# Test all 8 transformations
for transform in A B C D E F G H; do
    echo "Testing transform $transform..."
    ./Rm2in2/scripts/send.sh test-output/corners_${transform}_*.txt

    # Open notes app on RM2, tap to draw
    # Take photo or note which transform looks correct

    read -p "Press enter for next transform..."
done
```

Keep notes:
```
Pattern: corners
  Transform A: ❌ dots in wrong corners
  Transform B: ❌ dots rotated 90°
  Transform C: ✅ CORRECT! Dots at corners
  Transform D: ❌ mirrored
  ...
```

## Finding the Winner

The **correct transformation** must pass ALL tests:

- ✅ Corners: Four dots at actual screen corners
- ✅ Cross: Centered + with horizontal/vertical arms
- ✅ Grid: 3×3 evenly spaced
- ✅ Circle: Circular (not elliptical or distorted)

**If multiple transforms pass simple tests but fail on circle/curves:**
- The issue may be in curve sampling, not transformation
- Focus on the transform that passes corners + cross + grid
- Debug curve rendering separately

## Documenting Results

Once you find the correct transformation:

### 1. Update inject.c

Edit `Rm2/src/inject.c` lines ~54-63:

```c
static inline int to_wacom_x(int pen_x, int pen_y) {
    // TODO: Replace with winning formula
    // Example: return WACOM_MAX_Y - pen_y;
}

static inline int to_wacom_y(int pen_x, int pen_y) {
    // TODO: Replace with winning formula
    // Example: return pen_x;
}
```

### 2. Create Documentation

Create `Rm2in2/COORDINATE_SYSTEM.md`:

```markdown
# Verified Coordinate System

## Winning Transformation

**Transform: C (SwapFlipY)**

### Formula
- `wacom_x = WACOM_MAX_Y - pen_y`
- `wacom_y = pen_x`

### Why It Works
[Explain the relationship between display and sensor]

### Test Results
- ✅ Corners test: PASS
- ✅ Cross test: PASS
- ✅ Grid test: PASS
- ✅ Circle test: PASS

### Scale Factors
- `scale_x = WACOM_MAX_X / DISPLAY_WIDTH = 14.93`
- `scale_y = WACOM_MAX_Y / DISPLAY_HEIGHT = 8.40`
```

### 3. Update Conversion Tools

When you create SVG/PNG converters, use the verified transformation.

## Troubleshooting

### Hook not loading
**Symptom:** No "[RM2]" messages when starting xochitl

**Solutions:**
- Check inject.so file exists: `ssh root@10.11.99.1 ls -l /opt/rm2in2/inject.so`
- Verify LD_PRELOAD path is correct
- Check stderr output: `LD_PRELOAD=/opt/rm2in2/inject.so /usr/bin/xochitl 2>&1 | grep RM2`

### FIFO not found
**Symptom:** send.sh reports "FIFO not found"

**Solutions:**
- Hook may not be running - check xochitl is running with LD_PRELOAD
- Wait a few seconds after starting xochitl
- Check: `ssh root@10.11.99.1 ls -l /tmp/rm2_inject`

### Nothing appears on screen
**Symptom:** Commands sent but no drawing appears

**Solutions:**
- Open the notes app first
- Tap the screen to trigger a redraw
- Check if events are queued: commands may appear after next pen interaction
- Check stderr for warnings: `ssh root@10.11.99.1 "systemctl status xochitl"`

### Coordinates out of bounds
**Symptom:** "[RM2] WARNING: Coordinates out of bounds"

**Solutions:**
- This is expected when testing wrong transformations
- The correct transform will not produce this warning
- Use this as a hint: transforms producing warnings are wrong

## Next Steps

After finding the correct transformation:

1. ✅ Update inject.c with verified formula
2. ✅ Test with complex patterns (text, curves)
3. ✅ Build SVG to PEN converter using verified transform
4. ✅ Build PNG bitmap converter
5. ✅ Add pressure variation support
6. ✅ Optimize performance

## Reference

### Key Files
- `Rm2/src/inject.c` - Injection hook (modify after testing)
- `Rm2in2/tests/test_transformations.py` - Pattern generator
- `Rm2in2/tests/parse_captured_events.py` - Event analyzer
- `Rm2in2/scripts/send.sh` - Command sender

### Coordinate Spaces
- **SVG space:** 1404 × 1872 (portrait, design coordinates)
- **Wacom hardware:** 0-20966 × 0-15725 (sensor coordinates)
- **Display:** 1404 × 1872 (portrait, what user sees)

### Known Issues with Previous Versions
All code in `resources/previous-versions/` has coordinate issues:
- Simple lines work
- Curves/text/graphics fail
- Various attempts at transformation (all incorrect)

This testing framework is designed to avoid those mistakes by empirical validation.
