# Quick Start Guide

## Installation

### Prerequisites

**On your PC:**
- WSL or Linux with ARM cross-compiler
- Python 3.6+
- SSH access to your RM2
- Inkscape (optional, for font creation)

**On RM2:**
- SSH enabled (usually 10.11.99.1 via USB)
- Root access

### Step 1: Install ARM Compiler (WSL/Linux)

```bash
sudo apt update
sudo apt install gcc-arm-linux-gnueabihf
```

### Step 2: Clone/Download Project

```bash
cd ~/Documents/Arduino/RM2
# (Assuming you have rm2-claude directory)
cd rm2-claude
```

### Step 3: Compile Injection Hook

```bash
cd rm2-server
arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread
```

**Expected output:** `inject.so` file created (no errors)

### Step 4: Deploy to RM2

```bash
scp inject.so root@10.11.99.1:/opt/
```

**Password:** Default is blank (just press Enter) or your custom password

### Step 5: Enable Injection on RM2

```bash
ssh root@10.11.99.1
cd /opt
echo "LD_PRELOAD=/opt/inject.so /usr/bin/xochitl" > /opt/bin/xochitl_inject
chmod +x /opt/bin/xochitl_inject

# Modify systemd service (optional but recommended)
systemctl stop xochitl
# Edit /lib/systemd/system/xochitl.service to use /opt/bin/xochitl_inject
systemctl daemon-reload
systemctl start xochitl
```

**Or just test manually:**
```bash
LD_PRELOAD=/opt/inject.so /usr/bin/xochitl
```

### Step 6: Test Installation

On your PC:

```bash
cd ~/Documents/Arduino/RM2/rm2-claude
echo "PEN_DOWN 10000 8000
PEN_MOVE 15000 8000
PEN_UP" > test.txt

./send.sh test.txt
```

On RM2:
- Open Xochitl (drawing app)
- Tap pen on screen
- You should see a horizontal line appear!

---

## Basic Usage

### Convert SVG to PEN

```bash
cd font-capture
python svg_to_pen.py input.svg output.txt
```

### Send to RM2

```bash
cd ..
./send.sh font-capture/output.txt
```

### Trigger Drawing

On RM2, open drawing app and tap pen anywhere on screen. The strokes will be drawn.

---

## Creating Fonts from Bitmaps

### Workflow Overview

1. Create/obtain character as bitmap image
2. Trace in Inkscape
3. Convert to PEN commands
4. Test on RM2
5. Repeat for all characters

### Detailed Steps

#### 1. Create Bitmap Character

**Option A: From font**
```bash
# Use any font editor or image editor
# Type character (e.g., "A")
# Export as PNG/JPG at high resolution (300+ DPI)
```

**Option B: Handwrite**
```bash
# Write character on paper
# Scan or photograph
# Crop to single character
```

#### 2. Trace in Inkscape

```bash
inkscape
```

**In Inkscape:**

1. **Import bitmap**
   - File → Import
   - Select your image
   - Click OK

2. **Trace bitmap**
   - Select the imported image
   - Path → Trace Bitmap
   - Choose detection mode:
     - **Single scan** → Brightness cutoff
     - Adjust threshold (0.45 is good starting point)
   - Click **Update** to preview
   - Click **OK** when satisfied
   - Close dialog

3. **Clean up**
   - Delete original bitmap (select and press Delete)
   - Select traced path
   - **Path → Simplify** (Ctrl+L) to reduce nodes
   - **Path → Break Apart** if multiple components

4. **Verify**
   - Press **N** (node tool)
   - Check that you have clean strokes
   - Manually delete extra nodes if needed

5. **Save**
   - File → Save As
   - Choose "Plain SVG" (not Inkscape SVG)
   - Save as `character_A.svg`

#### 3. Convert to PEN Commands

```bash
cd font-capture
python svg_to_pen.py character_A.svg letter_A.txt
```

**Output:**
```
[INFO] Reading SVG from: character_A.svg
[INFO] Found 3 paths
[INFO] Processing stroke_1
[INFO]   -> 15 points
[INFO] Processing stroke_2
[INFO]   -> 8 points
[INFO] Processing stroke_3
[INFO]   -> 12 points
[INFO] Total strokes: 3
[INFO] Total points: 35
[OK] PEN commands saved: letter_A.txt
```

#### 4. Test on RM2

```bash
cd ..
./send.sh font-capture/letter_A.txt
```

On RM2:
- Open drawing app
- Tap pen
- Character appears!

#### 5. Iterate if Needed

If character doesn't look right:

**Problem: Too many nodes**
```bash
# In Inkscape: Path → Simplify multiple times
# Or manually delete nodes (N key, select nodes, Delete)
```

**Problem: Wrong stroke order**
```bash
# In Inkscape:
# - Open Layers panel (Ctrl+Shift+L)
# - Reorder paths (drag up/down)
# - Top = drawn first, bottom = drawn last
```

**Problem: Overlapping paths**
```bash
# In Inkscape:
# - Path → Break Apart
# - Delete unwanted parts
# - Path → Union to merge if needed
```

---

## Text to Handwriting (Built-in Font)

For quick text without creating fonts:

### Simple Text

```bash
cd font-capture
python text_to_pen.py "Hello World" output.txt
cd ..
./send.sh font-capture/output.txt
```

### From File

Create `mytext.txt`:
```
This is my essay.

It has multiple paragraphs.

The converter handles line wrapping automatically.
```

Convert:
```bash
cd font-capture
python text_to_pen.py --file mytext.txt essay.txt
cd ..
./send.sh font-capture/essay.txt
```

### Supported Characters

- **Letters:** A-Z, a-z
- **Numbers:** 0-9
- **Punctuation:** . , ! ? - : ; ' " ( )

---

## Common Tasks

### Create Full Alphabet

```bash
# For each letter A-Z:
# 1. Create bitmap
# 2. Trace in Inkscape, save as letter_A.svg
# 3. Convert:
cd font-capture
python svg_to_pen.py letter_A.svg letter_A.txt
python svg_to_pen.py letter_B.svg letter_B.txt
# ... etc

# Test each:
cd ..
./send.sh font-capture/letter_A.txt
# (tap on RM2)
./send.sh font-capture/letter_B.txt
# (tap on RM2)
```

### Combine Multiple Characters

Create a text file with all PEN commands:

```bash
cat font-capture/letter_H.txt \
    font-capture/letter_E.txt \
    font-capture/letter_L.txt \
    font-capture/letter_L.txt \
    font-capture/letter_O.txt \
    > font-capture/hello.txt

./send.sh font-capture/hello.txt
```

**Note:** You need to adjust coordinates for spacing between letters manually (or use text_to_pen.py)

### Capture Real Handwriting

```bash
# On RM2:
ssh root@10.11.99.1
cd /tmp
evtest /dev/input/event1 > capture.txt
# Write with pen
# Ctrl+C when done
exit

# On PC:
scp root@10.11.99.1:/tmp/capture.txt testing-tools/
cd testing-tools
python parse_events.py capture.txt handwriting.txt

# Now you have PEN commands from real handwriting!
cd ..
./send.sh testing-tools/handwriting.txt
```

---

## Troubleshooting

### inject.so Not Working

**Symptoms:** No line appears when tapping pen

**Check:**
```bash
ssh root@10.11.99.1
ps aux | grep xochitl
# Should show LD_PRELOAD=/opt/inject.so

# Check if FIFO exists:
ls -la /tmp/rm2_inject
# Should show: prw-r--r-- (pipe)

# Check inject.so is loaded:
lsof -p $(pgrep xochitl) | grep inject
```

**Fix:**
```bash
# Restart xochitl with LD_PRELOAD:
systemctl stop xochitl
LD_PRELOAD=/opt/inject.so /usr/bin/xochitl &
```

### SVG Conversion Fails

**Symptoms:** `svg_to_pen.py` finds 0 paths

**Causes:**
1. SVG contains shapes, not paths
2. SVG is Inkscape format (too complex)
3. Paths are in groups/layers not parsed

**Fix:**
```bash
# In Inkscape:
# 1. Select all (Ctrl+A)
# 2. Object → Ungroup (repeatedly until no more groups)
# 3. Path → Object to Path (convert shapes to paths)
# 4. File → Save As → Plain SVG (not Inkscape SVG)
```

### Coordinates Wrong on RM2

**Symptoms:** Drawing appears in wrong location

**Check:**
```bash
# Verify inject.c has pass-through coordinates:
grep "return x;" rm2-server/inject.c
# Should show:
#   static inline int to_wacom_x(int x) { return x; }
```

**Fix:**
```bash
# Recompile inject.so:
cd rm2-server
arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread
scp inject.so root@10.11.99.1:/opt/

# Restart xochitl:
ssh root@10.11.99.1
systemctl restart xochitl
```

### Too Many Nodes

**Symptoms:** Character looks jagged or has too much detail

**Fix:**
```bash
# In Inkscape:
# 1. Select path
# 2. Path → Simplify (Ctrl+L)
# 3. Repeat until smooth
# 4. Or manually: Press N, select nodes, Delete
```

### Wrong Stroke Order

**Symptoms:** Character draws in unnatural order

**Fix:**
```bash
# In Inkscape:
# 1. View → Layers (Ctrl+Shift+L)
# 2. Each path is listed
# 3. Drag paths up/down to reorder
# 4. Top = drawn first
# 5. Save and re-convert
```

### send.sh Fails

**Symptoms:** Permission denied or connection refused

**Check:**
```bash
# Test SSH connection:
ssh root@10.11.99.1 echo "OK"

# Check if file exists:
ls -la font-capture/output.txt
```

**Fix:**
```bash
# Ensure RM2 is connected via USB
# Check IP is 10.11.99.1 (or adjust in send.sh)
# Ensure file path is correct
```

---

## Tips & Best Practices

### Inkscape Tracing

- **High threshold** (0.5-0.7) for clean fonts
- **Low threshold** (0.3-0.4) for handwritten scans
- Always **Simplify** after tracing
- **Preview** before accepting trace

### Stroke Ordering

Natural handwriting order:
1. **Top to bottom** - Draw upper parts first
2. **Left to right** - For LTR languages
3. **Main strokes first** - Vertical before horizontal
4. **Details last** - Dots, crosses after main shape

Examples:
- **i:** Vertical stroke, then dot
- **t:** Vertical stroke, then horizontal cross
- **A:** Left diagonal, right diagonal, horizontal bar
- **H:** Left vertical, right vertical, horizontal bar

### File Organization

```
font-capture/
├── fonts/
│   ├── uppercase/
│   │   ├── A.svg
│   │   ├── A.txt
│   │   ├── B.svg
│   │   ├── B.txt
│   │   └── ...
│   └── lowercase/
│       ├── a.svg
│       ├── a.txt
│       └── ...
└── text_to_pen.py
```

### Testing Strategy

1. **Test single characters** first
2. **Verify stroke order** looks natural
3. **Check spacing** between strokes
4. **Build library** incrementally
5. **Test words** to check spacing
6. **Test paragraphs** for layout

---

## Advanced Usage

### Custom Margins

Edit margins in `text_to_pen.py`:

```python
# Lines 20-23
MARGIN_TOP = 2000      # Increase for more top space
MARGIN_LEFT = 2000     # Increase for more left space
MARGIN_RIGHT = 2000    # Decrease for wider text area
MARGIN_BOTTOM = 2000   # Decrease for more lines per page
```

### Custom Font Metrics

Edit spacing in `text_to_pen.py`:

```python
# Lines 29-32
CHAR_WIDTH = 500       # Increase for wider spacing
CHAR_HEIGHT = 800      # Character height
LINE_SPACING = 1200    # Increase for more line space
WORD_SPACING = 600     # Increase for wider word gaps
```

### Batch Conversion

Convert multiple SVGs at once:

```bash
cd font-capture
for svg in letters/*.svg; do
    basename="${svg%.svg}"
    python svg_to_pen.py "$svg" "${basename}.txt"
done
```

### Coordinate Testing

Test coordinate system:

```bash
cd coord-test
python simple_test.py
cd ..
./send.sh coord-test/results/simple_test.txt
```

**Expected:** Cross at center, crosses at corners, rectangle border

---

## Next Steps

After basic setup:

1. **Create your font library**
   - Trace all characters A-Z, a-z, 0-9
   - Test each character
   - Organize in folders

2. **Improve stroke ordering**
   - Study `svg_to_pen.py` ordering logic
   - Customize for your font style
   - Test with complex characters

3. **Build text rendering**
   - Create font database (JSON)
   - Add kerning data
   - Implement proper spacing

4. **Add natural variation**
   - Random coordinate offsets
   - Variable pressure
   - Mimic handwriting imperfections

See [DEVELOPMENT.md](DEVELOPMENT.md) for technical details and future enhancements.

---

## Command Reference

```bash
# Compile injection hook
arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread

# Deploy to RM2
scp inject.so root@10.11.99.1:/opt/

# Convert SVG to PEN
python svg_to_pen.py input.svg output.txt

# Convert PEN to SVG (for editing)
python pen_to_svg.py input.txt output.svg

# Text to handwriting
python text_to_pen.py "text" output.txt
python text_to_pen.py --file input.txt output.txt

# Send to RM2
./send.sh file.txt

# Capture real handwriting
ssh root@10.11.99.1
evtest /dev/input/event1 > capture.txt
# Ctrl+C, then:
python parse_events.py capture.txt output.txt

# Test coordinates
cd coord-test && python simple_test.py && cd ..
./send.sh coord-test/results/simple_test.txt
```

---

## Getting Help

**Check logs on RM2:**
```bash
ssh root@10.11.99.1
journalctl -u xochitl -f
# Should show "[RM2] Injection hook loaded"
```

**Verify converter output:**
```bash
head -20 font-capture/output.txt
# Should show PEN_DOWN, PEN_MOVE, PEN_UP with integer coordinates
```

**Test basic injection:**
```bash
# Create simple test:
echo "PEN_DOWN 10000 8000
PEN_MOVE 15000 8000
PEN_UP" > test.txt
./send.sh test.txt
# Tap on RM2 - should see horizontal line
```

If issues persist, see [DEVELOPMENT.md](DEVELOPMENT.md) for technical details.
