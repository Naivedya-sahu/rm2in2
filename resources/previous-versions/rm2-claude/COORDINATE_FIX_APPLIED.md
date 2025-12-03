# Coordinate Fix Applied - Transformation #6

## Problem Identified

Based on visual test results:
- Number **1** appeared at **bottom-left** (should be top-left)
- Number **2** appeared at **top-left** (should be top-right)
- Numbers arranged **counter-clockwise** (should be clockwise)
- Display **rotated** with base toward right

## Solution Applied

**Transformation #6: Swap X/Y + Flip Y**

### Mathematical Transform
```
Wacom_X = WACOM_MAX_Y - PEN_Y
Wacom_Y = PEN_X

Where:
  WACOM_MAX_X = 20966
  WACOM_MAX_Y = 15725
```

### Changes Made to inject.c

**Before:**
```c
static inline int to_wacom_x(int x) { return x; }
static inline int to_wacom_y(int y) { return y; }

// Calls:
int wx = to_wacom_x(x);
int wy = to_wacom_y(y);
```

**After:**
```c
static inline int to_wacom_x(int x, int y) { return WACOM_MAX_Y - y; }
static inline int to_wacom_y(int x, int y) { return x; }

// Calls:
int wx = to_wacom_x(x, y);
int wy = to_wacom_y(x, y);
```

## Next Steps

### 1. Recompile inject.so (in WSL)

```bash
cd rm2-server
arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread
```

**Expected output:** No errors, inject.so file created

### 2. Deploy to RM2

```bash
scp inject.so root@10.11.99.1:/opt/
```

### 3. Restart Xochitl

```bash
ssh root@10.11.99.1
systemctl restart xochitl
exit
```

### 4. Verify Fix

Test with visual pattern:
```bash
./send.sh testing-tools/coord_tests/visual_test.txt
```

**Expected result after fix:**
- Number **1** at **top-left** corner ✓
- Number **2** at **top-right** corner ✓
- Number **3** at **bottom-right** corner ✓
- Number **4** at **bottom-left** corner ✓
- Numbers arranged **clockwise** ✓
- Arrows pointing **toward center** ✓

### 5. Test with Real Content

```bash
cd font-capture
python svg_to_pen.py your_character.svg test.txt
cd ..
./send.sh font-capture/test.txt
```

**Expected:** Character appears correctly oriented, not mirrored

## What This Transformation Does

### Visual Explanation

**Before (Identity transform):**
```
Your PEN coords (1404×1872):        Wacom sensor (20966×15725):
┌─────────────┐                     ┌─────────────┐
│ (0,0)       │                     │ (0,0)       │
│             │  Direct mapping     │             │
│             │  ────────────────>  │   WRONG     │
│             │                     │ orientation │
│      (x,y)  │                     │             │
└─────────────┘                     └─────────────┘
        Appears mirrored/rotated on RM2
```

**After (Transformation #6):**
```
Your PEN coords (1404×1872):        Wacom sensor (20966×15725):
┌─────────────┐                     ┌─────────────┐
│ (0,0)       │                     │ (0,0)       │
│             │  Swap + Flip Y      │             │
│             │  ────────────────>  │   CORRECT   │
│             │  x→y, y→MAX_Y-x     │ orientation │
│      (x,y)  │                     │             │
└─────────────┘                     └─────────────┘
        Appears correctly on RM2
```

### Why This Specific Transform?

The RM2 Wacom sensor is physically mounted **rotated 90° counter-clockwise** relative to the display. Additionally, one axis needs flipping to correct the mirroring.

Transformation #6 corrects this by:
1. **Swapping X and Y** - Handles the 90° rotation
2. **Flipping Y** - Corrects the mirroring on that axis

## Impact on Other Files

### svg_to_pen.py

The svg_to_wacom() function in svg_to_pen.py already uses a similar transformation:

```python
def svg_to_wacom(self, svg_x, svg_y):
    # SVG X came from Wacom Y
    # SVG Y came from Wacom X
    wacom_y = (svg_x / SVG_WIDTH) * WACOM_MAX_Y
    wacom_x = (svg_y / SVG_HEIGHT) * WACOM_MAX_X
    return int(round(wacom_x)), int(round(wacom_y))
```

This is **compatible** with the inject.c transformation because:
- Both swap X and Y
- SVG converter generates PEN commands in expected coordinate space
- inject.c transforms to final Wacom coordinates

**No changes needed to svg_to_pen.py**

### pen_to_svg.py

The wacom_to_svg() function does the reverse:

```python
def wacom_to_svg(self, wacom_x, wacom_y):
    svg_x = (wacom_y / WACOM_MAX_Y) * SVG_WIDTH
    svg_y = (wacom_x / WACOM_MAX_X) * SVG_HEIGHT
    return int(round(svg_x)), int(round(svg_y))
```

This is also **compatible** - it reverses the swap.

**No changes needed to pen_to_svg.py**

## Verification Checklist

After deploying the fix, verify:

- [ ] Recompiled inject.so with no errors
- [ ] Deployed inject.so to /opt/ on RM2
- [ ] Restarted xochitl
- [ ] Visual test shows numbers 1-4 clockwise from top-left
- [ ] Arrows point toward center
- [ ] Real SVG content appears correctly oriented
- [ ] No mirroring artifacts
- [ ] Characters are readable (not backwards)

## If Issues Persist

If visual test still shows incorrect orientation:

1. **Double-check compilation:** Ensure inject.so was actually recompiled
   ```bash
   ls -la rm2-server/inject.so
   # Check timestamp is recent
   ```

2. **Verify deployment:** Confirm inject.so on RM2 is the new version
   ```bash
   ssh root@10.11.99.1
   ls -la /opt/inject.so
   # Check timestamp matches local file
   ```

3. **Check xochitl is using it:**
   ```bash
   ssh root@10.11.99.1
   ps aux | grep xochitl | grep LD_PRELOAD
   ```

4. **Try different transformation:** If #6 is close but not quite right, test #5 or #7:
   - #5: Swap only (no flip)
   - #7: Swap + Flip X (instead of Flip Y)

## Technical Notes

### Why Swap Transformations Need Both Parameters?

Simple transformations (flip, no swap) can work with single parameters:
```c
int to_wacom_x(int x) { return WACOM_MAX_X - x; }  // Just flip
```

But swap transformations need access to **both** x and y:
```c
int to_wacom_x(int x, int y) { return WACOM_MAX_Y - y; }  // Need y!
int to_wacom_y(int x, int y) { return x; }                // Need x!
```

This is why transformations 5-8 require signature changes.

### Performance Impact

Negligible. The transformation is two integer operations:
- One subtraction
- One assignment

Executed per point, but modern ARM CPUs handle this instantly.

## Success!

Once verified, the coordinate system is permanently fixed. All future:
- SVG conversions
- Text rendering
- Direct PEN commands

...will appear correctly oriented on the RM2!
