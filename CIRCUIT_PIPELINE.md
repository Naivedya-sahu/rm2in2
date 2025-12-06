# Circuit Photo to Graphics Pipeline

**End Goal:** Draw circuits from photos on RM2

---

## Pipeline Overview

```
Photo of Circuit
    ↓
Option A: Computer Vision → Schematic Recognition → Netlist → Parametric Circuit → SVG
Option B: Computer Vision → Edge Detection → SVG Trace → Direct SVG
    ↓
SVG Optimization & Simplification
    ↓
SVG → Pen Commands (adaptive interpolation)
    ↓
Direct Write to /dev/input/event1
    ↓
Rendered on RM2
```

---

## Option A: Netlist-Based (Semantic Understanding)

### Step 1: Circuit Recognition

**Tools:**
- **CircuitSeeker** (Python, ML-based) - https://github.com/circuitSeeker/circuitSeeker
  - Detects components (resistors, capacitors, ICs, etc.)
  - Identifies connections
  - Outputs netlist format

- **Electrical Circuit Recognition** (Computer Vision) - Research papers
  - ICDAR 2019 competition on circuit recognition
  - Multiple ML models available

**Challenges:**
- ❌ Requires training data
- ❌ Component recognition accuracy varies
- ❌ Handwritten circuits harder than printed
- ❌ Complex for first iteration

### Step 2: Netlist → Parametric Circuit

**Tools:**
- **schemdraw** (Python) - https://schemdraw.readthedocs.io/
  - Programmatic circuit drawing
  - Netlist-like input
  - SVG output

```python
import schemdraw
import schemdraw.elements as elm

with schemdraw.Drawing() as d:
    d += elm.Resistor().label('R1\n1kΩ')
    d += elm.Capacitor().label('C1\n10μF')
    d += elm.Ground()
```

- **PySpice** - Circuit simulation with schematic generation
- **Qucs** (Qt-based) - Has netlist import

**Advantages:**
- ✅ Clean, parametric output
- ✅ Standard component library
- ✅ Easy to modify/annotate

**Disadvantages:**
- ❌ Requires accurate netlist extraction
- ❌ Layout might differ from original photo
- ❌ Complex pipeline

---

## Option B: Direct SVG Trace (Image Processing)

### Step 1: Image Preprocessing

```python
import cv2
import numpy as np

def preprocess_circuit_image(image_path):
    # Load image
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Increase contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(enhanced)
    
    # Threshold
    _, binary = cv2.threshold(denoised, 0, 255, 
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Invert if needed (black lines on white)
    if np.mean(binary) > 127:
        binary = cv2.bitwise_not(binary)
    
    return binary
```

### Step 2: Edge Detection & Skeleton

```python
def extract_circuit_lines(binary_image):
    # Morphological operations to clean up
    kernel = np.ones((3,3), np.uint8)
    cleaned = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
    
    # Skeletonize to get centerlines
    from skimage.morphology import skeletonize
    skeleton = skeletonize(cleaned // 255)
    
    # Find contours
    skeleton_uint8 = (skeleton * 255).astype(np.uint8)
    contours, _ = cv2.findContours(skeleton_uint8, 
                                   cv2.RETR_LIST, 
                                   cv2.CHAIN_APPROX_SIMPLE)
    
    return contours
```

### Step 3: Contours → SVG

**Tools:**
- **autotrace** - Bitmap to vector (CLI tool)
  ```bash
  autotrace -output-file circuit.svg -output-format svg input.png
  ```

- **potrace** - Bitmap tracing (CLI tool)
  ```bash
  potrace -s -o circuit.svg input.pbm
  ```

- **OpenCV → SVG** (Python)
  ```python
  import svgwrite
  
  def contours_to_svg(contours, filename, width=1404, height=1872):
      dwg = svgwrite.Drawing(filename, size=(width, height))
      
      for contour in contours:
          # Simplify contour
          epsilon = 0.01 * cv2.arcLength(contour, True)
          approx = cv2.approxPolyDP(contour, epsilon, True)
          
          # Convert to SVG path
          points = [(p[0][0], p[0][1]) for p in approx]
          dwg.add(dwg.polyline(points, 
                               stroke='black', 
                               fill='none', 
                               stroke_width=2))
      
      dwg.save()
  ```

**Advantages:**
- ✅ Simple pipeline
- ✅ Preserves original layout
- ✅ Fast processing

**Disadvantages:**
- ❌ No semantic understanding
- ❌ Noise artifacts
- ❌ May need manual cleanup

---

## Recommended Pipeline: Hybrid Approach

### Stage 1: Quick Preview (Option B)

```python
# photo_to_circuit.py

import cv2
import numpy as np
import svgwrite
from PIL import Image

def photo_to_svg(photo_path, output_svg, target_width=1404, target_height=1872):
    """Convert circuit photo to SVG for RM2 injection"""
    
    # 1. Load and preprocess
    img = cv2.imread(photo_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 3. Threshold to binary
    _, binary = cv2.threshold(enhanced, 0, 255, 
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Invert if background is darker
    if np.mean(binary) > 127:
        binary = cv2.bitwise_not(binary)
    
    # 4. Clean up noise
    kernel = np.ones((3,3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    # 5. Resize to RM2 resolution
    h, w = binary.shape
    scale = min(target_width/w, target_height/h)
    new_w, new_h = int(w*scale), int(h*scale)
    resized = cv2.resize(binary, (new_w, new_h), 
                        interpolation=cv2.INTER_AREA)
    
    # 6. Center on canvas
    canvas = np.ones((target_height, target_width), dtype=np.uint8) * 255
    y_offset = (target_height - new_h) // 2
    x_offset = (target_width - new_w) // 2
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    
    # 7. Extract contours
    contours, _ = cv2.findContours(255-canvas, cv2.RETR_LIST, 
                                   cv2.CHAIN_APPROX_SIMPLE)
    
    # 8. Convert to SVG
    dwg = svgwrite.Drawing(output_svg, size=(target_width, target_height))
    
    for contour in contours:
        # Skip tiny contours (noise)
        if cv2.contourArea(contour) < 10:
            continue
        
        # Simplify contour (Douglas-Peucker)
        epsilon = 0.5  # Adjust for smoothness vs accuracy
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Convert to path points
        points = [(float(p[0][0]), float(p[0][1])) for p in approx]
        
        if len(points) > 1:
            dwg.add(dwg.polyline(points, 
                                stroke='black', 
                                fill='none', 
                                stroke_width=2))
    
    dwg.save()
    print(f"SVG saved: {output_svg}")
    return output_svg

# Usage
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python photo_to_circuit.py <photo.jpg> [output.svg]")
        sys.exit(1)
    
    photo = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else 'circuit.svg'
    
    photo_to_svg(photo, output)
```

### Stage 2: SVG → Pen Commands

Reuse your existing SVG parsing (svg2inject_medium.py or svg2inject_pro.py) but update with adaptive interpolation:

```python
def svg_to_pen_commands_adaptive(svg_path, output_path):
    """Convert SVG to pen commands with adaptive interpolation"""
    
    from svgpathtools import svg2paths
    import math
    
    paths, _ = svg2paths(svg_path)
    commands = []
    
    TARGET_STEP = 5.0  # pixels between points
    
    for path in paths:
        if len(path) == 0:
            continue
        
        # Start path
        start = path.start
        commands.append(f"DOWN {int(start.real)} {int(start.imag)}")
        
        for segment in path:
            # Calculate segment length
            length = segment.length()
            
            # Adaptive point count
            points = max(10, min(1000, int(length / TARGET_STEP)))
            
            # Interpolate along segment
            for i in range(1, points + 1):
                t = i / points
                point = segment.point(t)
                commands.append(f"MOVE {int(point.real)} {int(point.imag)}")
        
        commands.append("UP")
    
    # Write commands
    with open(output_path, 'w') as f:
        f.write('\n'.join(commands))
    
    print(f"Pen commands saved: {output_path}")
    return output_path
```

### Stage 3: Deploy to RM2

```bash
#!/bin/bash
# deploy-circuit.sh

PHOTO="$1"
RM_IP="10.11.99.1"

if [ -z "$PHOTO" ]; then
    echo "Usage: $0 <circuit-photo.jpg>"
    exit 1
fi

echo "=== Circuit Photo to RM2 Pipeline ==="

# 1. Photo → SVG
python3 photo_to_circuit.py "$PHOTO" circuit.svg

# 2. SVG → Pen Commands
python3 svg_to_commands.py circuit.svg circuit_commands.txt

# 3. Send to RM2 daemon
cat circuit_commands.txt | nc $RM_IP 9001

echo "Circuit injected to RM2!"
```

---

## Required Python Packages

```bash
pip install opencv-python numpy svgwrite svgpathtools shapely pillow scikit-image
```

---

## Alternative: Use Existing Tools

### LTSpice → SVG

If you have LTSpice schematics:
1. Export as image from LTSpice
2. Use photo_to_circuit.py
3. Or manually trace critical nets

### Eagle/KiCad → SVG

Modern EDA tools support SVG export:
```python
# KiCad: File → Plot → SVG
# Eagle: ULP script for SVG export
```

---

## Quality Considerations

### Image Quality Requirements

**Good photo characteristics:**
- ✅ High contrast (black lines on white)
- ✅ Good lighting (no shadows)
- ✅ Sharp focus
- ✅ Minimal noise
- ✅ Component labels readable

**Poor photo characteristics:**
- ❌ Low contrast (gray pencil on gray paper)
- ❌ Uneven lighting
- ❌ Blurry
- ❌ Handwritten with thick pen (will trace as filled shapes)

### Post-Processing

```python
# Optional: Clean up SVG manually
# Use Inkscape: Path → Simplify
# Or programmatically:

from svgpathtools import Path, Line, CubicBezier, QuadraticBezier, Arc

def simplify_svg(input_svg, output_svg, tolerance=2.0):
    """Remove unnecessary points from SVG paths"""
    paths, attrs = svg2paths(input_svg)
    
    simplified_paths = []
    for path in paths:
        # Your Douglas-Peucker or Ramer-Douglas-Peucker here
        simplified = simplify_path(path, tolerance)
        simplified_paths.append(simplified)
    
    # Write back
    wsvg(simplified_paths, attributes=attrs, filename=output_svg)
```

---

## Testing Strategy

### Test 1: Simple Circuit

1. Draw simple circuit by hand (resistor + LED)
2. Take photo
3. Process with pipeline
4. Inject to RM2
5. Verify readability

### Test 2: Printed Circuit

1. Find circuit diagram online
2. Print and photograph
3. Process
4. Compare output with original

### Test 3: Complex Circuit

1. Multi-stage amplifier or similar
2. Test component density limits
3. Evaluate if injection remains readable

---

## Recommended Approach

**Phase 1: Proof of Concept**
1. Use Option B (direct SVG trace)
2. Test with simple hand-drawn circuits
3. Validate end-to-end pipeline

**Phase 2: Optimization**
4. Add preprocessing filters
5. Tune contour simplification
6. Optimize injection speed

**Phase 3: Advanced (Optional)**
7. Add component recognition (Option A)
8. Generate parametric schematics
9. Add annotation capabilities

---

## Implementation Priority

```
HIGH PRIORITY (Core Pipeline):
1. photo_to_circuit.py (image → SVG)
2. svg_to_commands_adaptive.py (SVG → pen commands)
3. rm2inject daemon (direct write to /dev/input/event1)

MEDIUM PRIORITY (Quality):
4. Image preprocessing tuning
5. Contour simplification optimization
6. SVG cleanup scripts

LOW PRIORITY (Advanced):
7. Component recognition
8. Netlist generation
9. Parametric circuit rendering
```

---

## Summary

**Recommended pipeline:**
```
Photo → OpenCV preprocessing → Contour extraction → SVG → 
Adaptive pen commands → Direct write to /dev/input/event1
```

**All tools available:**
- OpenCV for image processing ✅
- svgpathtools for SVG parsing ✅
- Direct write approach proven ✅
- Adaptive interpolation tested ✅

**Estimated implementation time:**
- Basic pipeline: 2-3 hours
- Testing and tuning: 2-4 hours
- Total: ~6 hours to working prototype

**Start with simple hand-drawn circuits, then expand to complex schematics.**
