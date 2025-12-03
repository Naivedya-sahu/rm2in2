## Coordinate System Fix Guide

This guide helps you diagnose and fix coordinate mirroring/orientation issues.

### Problem

Text or drawings appear:
- Mirrored (flipped horizontally or vertically)
- In wrong location (wrong corner)
- Rotated incorrectly

### Solution: Test Suite

A comprehensive test suite identifies the exact coordinate transformation needed.

---

## Step 1: Generate Test Files

```bash
cd testing-tools
python coord_test.py
python visual_test.py
```

This creates test files in `testing-tools/coord_tests/`:
- `main_test.txt` - Comprehensive diagnostic pattern
- `visual_test.txt` - Quick visual test with numbers 1-4 in corners
- `transform_1.txt` through `transform_8.txt` - All 8 possible transformations

---

## Step 2: Deploy Current inject.so

```bash
# In WSL
cd rm2-server
arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread
scp inject.so root@10.11.99.1:/opt/
ssh root@10.11.99.1 systemctl restart xochitl
```

---

## Step 3: Test Visual Pattern

```bash
./send.sh testing-tools/coord_tests/visual_test.txt
```

**On RM2:**
- Open drawing app
- Tap pen anywhere
- Observe the pattern

**Expected result:**
```
1 -----> [cross] <----- 2
^                       |
|                       |
|      [center]         |
|       cross           |
|                       v
4 <----- [cross] -----> 3
```

- Number `1` should be in **top-left** corner with arrow pointing to center
- Number `2` should be in **top-right** corner with arrow pointing to center
- Number `3` should be in **bottom-right** corner with arrow pointing to center
- Number `4` should be in **bottom-left** corner with arrow pointing to center
- Center cross in middle

**If wrong:**
- Note which number appears in which actual corner
- Note arrow directions

---

## Step 4: Test Comprehensive Pattern

```bash
./send.sh testing-tools/coord_tests/main_test.txt
```

**Expected markers:**
- **Top-Left**: Small L shape (┗)
- **Top-Right**: Small T shape (┳)
- **Bottom-Left**: Vertical line (│)
- **Bottom-Right**: Diagonal line (╱)
- **Center**: Large cross (+)
- **Arrows**: RIGHT arrow points right, DOWN arrow points down
- **Border**: Rectangle around entire screen
- **Letter F**: Readable "F" in top-left area

---

## Step 5: Test All 8 Transformations

Try each transformation until one produces correct output:

```bash
./send.sh testing-tools/coord_tests/transform_1.txt
# Tap pen on RM2, observe L shape location

./send.sh testing-tools/coord_tests/transform_2.txt
# Tap pen, observe

# ... continue through transform_8.txt
```

**Transformation reference:**
1. Identity (no transform) - `x, y` unchanged
2. Flip horizontal - `WACOM_MAX_X - x, y`
3. Flip vertical - `x, WACOM_MAX_Y - y`
4. Flip both (180° rotation) - `WACOM_MAX_X - x, WACOM_MAX_Y - y`
5. Swap X/Y (90° rotation) - `y, x`
6. Swap + flip Y - `WACOM_MAX_Y - y, x`
7. Swap + flip X - `y, WACOM_MAX_X - x`
8. Swap + flip both - `WACOM_MAX_Y - y, WACOM_MAX_X - x`

**Find the one where:**
- L shape appears at top-left
- Pattern is correctly oriented
- Not mirrored or flipped

---

## Step 6: Apply the Fix

Once you've identified the correct transformation (e.g., #6):

### Automatic Fix (for transformations 1-4):

```bash
cd testing-tools
python fix_transform.py 6
```

This automatically updates inject.c with the correct transformation.

### Manual Fix (for transformations 5-8 with swap):

Transformations 5-8 require swapping X and Y, which needs manual code changes.

**Edit `rm2-server/inject.c`:**

Find these lines:
```c
// PEN commands already use Wacom coordinates - pass through directly
static inline int to_wacom_x(int x) { return x; }
static inline int to_wacom_y(int y) { return y; }
```

Replace with transformation code. For example, transformation #6:

```c
// Transformation 6: Swap + flip Y
static inline int to_wacom_x(int x, int y) { return WACOM_MAX_Y - y; }
static inline int to_wacom_y(int x, int y) { return x; }
```

**Then update all calls** in the file:
```c
// Before:
int wx = to_wacom_x(x);
int wy = to_wacom_y(y);

// After (for swap transformations):
int wx = to_wacom_x(x, y);
int wy = to_wacom_y(x, y);
```

---

## Step 7: Recompile and Test

```bash
cd rm2-server
arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread
scp inject.so root@10.11.99.1:/opt/
ssh root@10.11.99.1 systemctl restart xochitl
```

**Test again:**
```bash
./send.sh testing-tools/coord_tests/visual_test.txt
```

Numbers 1-4 should now be in correct corners!

---

## Step 8: Verify with Real Content

```bash
cd font-capture
python svg_to_pen.py your_character.svg test.txt
cd ..
./send.sh font-capture/test.txt
```

Content should now appear correctly oriented and positioned.

---

## Troubleshooting

### Pattern still wrong after fix

- Double-check you applied the correct transformation number
- Ensure inject.so was recompiled and deployed
- Verify xochitl was restarted: `ssh root@10.11.99.1 systemctl status xochitl`

### Numbers appear scrambled

This usually means transformation is partially correct but needs adjustment:
- If 1,2,3,4 are clockwise but wrong starting corner → try rotations (transform 4, 5, etc.)
- If numbers are mirrored/backwards → try flip transforms (2, 3, 4)
- If numbers are in random order → recheck which transform you applied

### SVG to PEN conversion seems wrong

If inject.c is correct but SVG conversion produces wrong output:
- Check `svg_to_pen.py` coordinate conversion (lines 34-42)
- The svg_to_wacom function should match inject.c transformation
- May need to update both files to use same transform

---

## Understanding Coordinate Systems

### Wacom Sensor (Hardware)
```
(0,0) ────────────────────── (20966,0)
  │                               │
  │    Physical sensor            │
  │    (rotated 90° in device)    │
  │                               │
(0,15725) ──────────────── (20966,15725)
```

### RM2 Display (Software)
```
Portrait mode: 1404×1872 pixels
Sensor is rotated 90° relative to display
```

### Why Transformation Needed

The Wacom sensor is mounted rotated 90° in the RM2 device. Depending on:
- How PEN commands are generated (already rotated or not)
- How inject.c interprets coordinates
- How Xochitl expects coordinates

...a transformation may be needed to align everything correctly.

**Test suite finds this transformation empirically** rather than guessing.

---

## Reference: All 8 Transformations

| # | Name | Transform | Use Case |
|---|------|-----------|----------|
| 1 | Identity | `x, y` | Already correct |
| 2 | Flip H | `WACOM_MAX_X - x, y` | Horizontal mirror |
| 3 | Flip V | `x, WACOM_MAX_Y - y` | Vertical mirror |
| 4 | Flip Both | `WACOM_MAX_X - x, WACOM_MAX_Y - y` | 180° rotation |
| 5 | Swap | `y, x` | 90° rotation |
| 6 | Swap+FlipY | `WACOM_MAX_Y - y, x` | 90° + vertical flip |
| 7 | Swap+FlipX | `y, WACOM_MAX_X - x` | 90° + horizontal flip |
| 8 | Swap+Both | `WACOM_MAX_Y - y, WACOM_MAX_X - x` | 270° rotation |

---

## Quick Testing Workflow

```bash
# 1. Generate tests
cd testing-tools && python visual_test.py && cd ..

# 2. Deploy current version
cd rm2-server
arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread
scp inject.so root@10.11.99.1:/opt/
ssh root@10.11.99.1 systemctl restart xochitl
cd ..

# 3. Test
./send.sh testing-tools/coord_tests/visual_test.txt
# Tap on RM2, note which corner has "1"

# 4. Try transformations if wrong
./send.sh testing-tools/coord_tests/transform_2.txt
./send.sh testing-tools/coord_tests/transform_3.txt
# ... until correct

# 5. Apply fix
cd testing-tools
python fix_transform.py 6  # Use correct number
cd ..

# 6. Rebuild and test
cd rm2-server
arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread
scp inject.so root@10.11.99.1:/opt/
ssh root@10.11.99.1 systemctl restart xochitl
cd ..
./send.sh testing-tools/coord_tests/visual_test.txt
```

---

## Success Criteria

✅ Visual test shows 1-2-3-4 clockwise from top-left
✅ Arrows point toward center
✅ Letter F is readable (not mirrored)
✅ Center cross is centered
✅ SVG conversions appear correctly positioned
✅ No mirroring or flipping artifacts

Once achieved, coordinate system is correctly configured!
