# Coordinate System Analysis

## Goal

Determine the correct transformation between SVG coordinates and Wacom hardware coordinates through empirical testing.

## Known Facts

1. **Wacom Sensor Range:** X=0-20966, Y=0-15725 (hardware reports this)
2. **Display Resolution:** 1404×1872 pixels (portrait)
3. **Sensor Orientation:** Rotated 90° relative to display
4. **Event Format:** Linux `input_event` structure with `EV_ABS` (ABS_X, ABS_Y)

## Unknown / To Be Tested

1. **Exact transformation formula** between display and sensor coordinates
2. **Axis mapping** (which sensor axis maps to which display axis)
3. **Origin location** (top-left, bottom-left, etc.)
4. **Scale factors** and whether they're linear
5. **Precision requirements** (how integer rounding affects output)

## Testing Approach

### Method 1: Capture Real Pen Events

**Tool:** `capture_pen_events.sh` (runs on RM2)

1. Use `evtest` to monitor `/dev/input/event1`
2. Draw known patterns (corners, center, lines)
3. Record actual Wacom coordinates
4. Map to observed display positions

**Pattern to draw:**
```
1 -------- 2
|          |
|     C    |
|          |
3 -------- 4
```

Draw in order: corners 1→2→3→4, then center C

### Method 2: Inject Test Patterns

**Tool:** `test_transformations.py` (runs on PC)

Generate commands with different transformation formulas:

```python
# Approach A: Direct mapping
wacom_x = svg_x * (WACOM_MAX_X / SVG_WIDTH)
wacom_y = svg_y * (WACOM_MAX_Y / SVG_HEIGHT)

# Approach B: Swap axes
wacom_x = svg_y * scale_y
wacom_y = svg_x * scale_x

# Approach C: Swap + flip Y
wacom_x = (SVG_HEIGHT - svg_y) * scale_y
wacom_y = svg_x * scale_x

# Approach D: Swap + flip X
wacom_x = svg_y * scale_y
wacom_y = (SVG_WIDTH - svg_x) * scale_x

# ... (test more variations)
```

Inject each pattern and observe which one renders correctly.

### Method 3: Bisection Testing

1. Send pen to known display coordinates (e.g., dead center: 702, 936)
2. Test different Wacom coordinates using binary search
3. Find the exact Wacom coordinates that hit the target
4. Repeat for multiple test points
5. Derive transformation formula from collected data

## Test Patterns

### Simple Patterns

1. **Four Corners Test**
   - Expected: Touch all 4 corners of visible area
   - Validates: Bounds and orientation

2. **Cross Pattern**
   - Expected: Horizontal and vertical lines through center
   - Validates: Axis alignment

3. **Number Grid**
   - Expected: 3×3 grid with numbers 1-9
   - Validates: Scale uniformity

### Complex Patterns

4. **Circle**
   - Expected: Perfect circle in center
   - Validates: Aspect ratio, curvature handling

5. **Text "RM2"**
   - Expected: Readable text
   - Validates: Fine detail, curve accuracy

## Data Collection Format

```json
{
  "test_id": "corner_top_left",
  "svg_coords": [0, 0],
  "wacom_coords": [?, ?],
  "display_position": "top-left corner",
  "correct": true/false,
  "notes": "..."
}
```

## Success Criteria

✅ **Transformation is correct when:**
1. Four corners pattern touches all screen corners
2. Circle appears circular (not elliptical)
3. Text is readable and not mirrored
4. Coordinates are repeatable (same input = same output)
5. Curves render smoothly without distortion

## Next Steps

1. Create capture tool
2. Run Method 1 (capture real events)
3. Analyze data
4. Create test pattern generator
5. Run Method 2 (try transformations)
6. Document winning formula
