# RM2 Pen Injection System

Inject custom pen strokes into Remarkable 2 (RM2) to programmatically draw handwriting, convert text to handwriting, and create custom fonts.

## Features

- **LD_PRELOAD injection hook** - Intercepts Wacom input to inject synthetic pen events
- **SVG to PEN conversion** - Convert SVG paths (including bitmap-traced fonts) to pen commands
- **Stroke ordering for natural handwriting** - Intelligent stroke sequencing
- **Text to handwriting** - Built-in Hershey single-stroke font for automatic text rendering
- **Wacom coordinate system** - Direct hardware coordinates (X: 0-20966, Y: 0-15725)

## Project Structure

```
rm2-claude/
├── README.md                 # This file
├── QUICKSTART.md            # Installation and usage guide
├── DEVELOPMENT.md           # Development history and technical details
├── send.sh                  # Deploy PEN files to RM2
├── rm2-server/
│   ├── inject.c             # LD_PRELOAD hook (main injection code)
│   └── inject.so            # Compiled library
├── font-capture/
│   ├── svg_to_pen.py        # SVG → PEN converter (main tool)
│   ├── pen_to_svg.py        # PEN → SVG converter (for editing)
│   └── text_to_pen.py       # Text → PEN using Hershey font
└── testing-tools/
    ├── capture_events.sh    # Capture real pen input
    └── parse_events.py      # Parse evtest output to PEN commands
```

## Quick Start

```bash
# 1. Compile injection hook (in WSL/Linux)
cd rm2-server
arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread
scp inject.so root@10.11.99.1:/opt/

# 2. Convert SVG to PEN commands
cd ../font-capture
python svg_to_pen.py input.svg output.txt

# 3. Send to RM2
cd ..
./send.sh font-capture/output.txt

# 4. Trigger on RM2
# Open drawing app (Xochitl) and tap pen on screen
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## Workflow: Bitmap Traced Fonts to Handwriting

The recommended workflow for creating fonts:

**1. Create/obtain font character as bitmap**
- Use any font editor or image editor
- Export as high-res image (PNG/JPG)

**2. Trace in Inkscape**
```bash
inkscape
# File → Import → select image
# Path → Trace Bitmap
# Adjust threshold for clean paths
# Path → Break Apart (if needed)
# Save as SVG
```

**3. Convert to PEN commands**
```bash
python font-capture/svg_to_pen.py character_A.svg letter_A.txt
```

**4. Test on RM2**
```bash
./send.sh font-capture/letter_A.txt
# Tap pen on RM2 screen
```

**5. Build font library**
Repeat for all characters (A-Z, a-z, 0-9, punctuation)

## SVG to PEN Conversion

The `svg_to_pen.py` converter:

- Parses SVG path data (M, L, H, V, C, S, Q, Z commands)
- Samples Bezier curves into line segments
- Converts SVG coordinates to Wacom coordinates
- **Orders strokes for natural handwriting flow**
- Outputs integer coordinates only (no decimals)

### Stroke Ordering

For natural handwriting emulation, strokes are ordered by:
1. Top-to-bottom (draw upper parts first)
2. Left-to-right (for LTR scripts)
3. Outside-to-inside (draw outlines before details)

This mimics how humans naturally write characters.

## Coordinate System

**Wacom Hardware:**
- X: 0-20966 (horizontal in landscape)
- Y: 0-15725 (vertical in landscape)
- Origin: top-left
- All coordinates are integers

**PEN Commands:**
```
PEN_DOWN x y    # Start stroke at (x,y)
PEN_MOVE x y    # Draw line to (x,y)
PEN_UP          # End stroke
```

**SVG to Wacom mapping:**
- SVG coordinates are normalized to 1404×1872 (RM2 display resolution)
- Converter handles rotation and scaling automatically
- Output uses native Wacom coordinates

## Text to Handwriting

For quick text rendering without SVG:

```bash
# Simple text
python font-capture/text_to_pen.py "Hello World" output.txt

# From file
python font-capture/text_to_pen.py --file essay.txt essay.txt

# Send to RM2
./send.sh font-capture/output.txt
```

Built-in Hershey font includes:
- Uppercase: A-Z
- Lowercase: a-z
- Numbers: 0-9
- Punctuation: . , ! ? - : ; ' " ( )

Automatically handles line wrapping and margins.

## How It Works

### Injection Mechanism

1. **LD_PRELOAD hook** - `inject.so` hooks the `read()` syscall
2. **FIFO pipe** - Listens on `/tmp/rm2_inject` for PEN commands
3. **Event queue** - Buffers synthetic Wacom events
4. **Event injection** - Returns synthetic events when Wacom device reads

```c
// inject.c core functions
read() → detect Wacom fd → spawn FIFO reader thread
FIFO reader → parse PEN commands → enqueue Wacom events
read(wacom_fd) → dequeue events if available → return to Xochitl
```

### send.sh Deployment

```bash
# send.sh workflow
1. SCP file to RM2 /tmp/
2. SSH to RM2
3. Cat file to /tmp/rm2_inject FIFO
4. Synthetic events injected when pen taps screen
```

## Troubleshooting

**Text appears in wrong location?**
- Ensure inject.so is recompiled with latest inject.c
- Coordinates should pass through directly (no transformation)

**SVG conversion produces wrong strokes?**
- Check SVG paths are not filled shapes (use stroke paths)
- Simplify paths in Inkscape (Path → Simplify)
- Ensure paths are broken apart (Path → Break Apart)

**Strokes draw in weird order?**
- svg_to_pen.py orders by position, but complex chars may need manual adjustment
- Use pen_to_svg.py → edit in Inkscape → svg_to_pen.py to reorder

**Decimal coordinates?**
- All converters output integers only
- If seeing decimals, ensure using latest svg_to_pen.py

## Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Technical architecture
- Coordinate system details
- Development history
- Future enhancements

## Requirements

- **RM2 device** with SSH access
- **WSL/Linux** for cross-compilation (arm-linux-gnueabihf-gcc)
- **Python 3.6+** for converter scripts
- **Inkscape** (optional, for SVG editing)

## License

Development tool for personal RM2 use. No warranty provided.

## Credits

- Hershey fonts originally from NIST
- Inspired by RM2 hacking community
