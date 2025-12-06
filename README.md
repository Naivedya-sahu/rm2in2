# lamp with Eraser Support

Enhanced version of [rmkit's lamp](https://github.com/rmkit-dev/rmkit) with programmatic eraser capabilities for reMarkable tablets.

## What This Is

This is a **fork of lamp** that adds eraser tool emulation via `BTN_TOOL_RUBBER` input events, enabling:
- ✅ Programmatic erasure of drawn strokes
- ✅ Dynamic self-clearing UI systems
- ✅ Menu transitions and animations
- ✅ Professional UX on reMarkable tablets

## The Discovery

Using `evtest`, we discovered that the reMarkable tablet recognizes `BTN_TOOL_RUBBER` events for the eraser. Just like lamp emulates `BTN_TOOL_PEN` for drawing, we can emulate `BTN_TOOL_RUBBER` for erasing.

## New Eraser Commands

```bash
# Erase a line
echo "eraser line x1 y1 x2 y2" | lamp

# Erase a rectangle outline
echo "eraser rectangle x1 y1 x2 y2" | lamp

# Fill/clear an entire area
echo "eraser fill x1 y1 x2 y2 [spacing]" | lamp

# Dense clearing (complete erasure)
echo "eraser clear x1 y1 x2 y2" | lamp

# Low-level eraser control
echo "eraser down x y" | lamp
echo "eraser move x y" | lamp
echo "eraser up" | lamp
```

## Build Instructions

### Prerequisites

- ARM cross-compiler: `gcc-arm-linux-gnueabihf` and `g++-arm-linux-gnueabihf`
- [okp](https://github.com/raisjn/okp) transpiler
- reMarkable tablet (tested on firmware 3.24)

### Quick Build

```bash
# Clone this repository
git clone <repo-url>
cd rm2in2

# Build enhanced lamp
./build_lamp_enhanced.sh

# Binary will be at: resources/repos/rmkit/src/build/lamp
```

### Deploy to reMarkable

```bash
# Copy to device
scp resources/repos/rmkit/src/build/lamp root@10.11.99.1:/opt/bin/

# Test
ssh root@10.11.99.1

# Draw something
echo "pen rectangle 100 100 500 500" | /opt/bin/lamp

# Erase it
echo "eraser fill 100 100 500 500 15" | /opt/bin/lamp
```

## Use Cases

### Dynamic UI Menus

```bash
# Draw menu
echo "pen rectangle 50 1400 350 1850" | lamp

# User makes selection...

# Clear menu and show next screen
echo "eraser fill 50 1400 350 1850 15" | lamp
echo "pen rectangle 370 1400 670 1850" | lamp
```

### Self-Clearing Component Library

```bash
# Show component
python3 svg_to_lamp.py resistor.svg 700 1600 1.5 | lamp
python3 text_to_lamp.py "10kΩ" 720 1680 0.5 | lamp

# User moves it with lasso tool...

# Clear the preview area
echo "eraser fill 700 1400 1350 1850 15" | lamp
```

### Animated Transitions

```bash
# Fade out effect
for spacing in 40 25 15 10; do
    echo "eraser fill 100 100 500 500 $spacing" | lamp
    sleep 0.1
done
```

## Technical Details

### How It Works

The patch adds eraser functions parallel to pen functions:
- `eraser_down()` uses `BTN_TOOL_RUBBER` instead of `BTN_TOOL_PEN`
- Same coordinate system and pressure values
- Same event injection mechanism via `/dev/input/event1`

### Patch Contents

- **eraser_down/move/up**: Low-level eraser events
- **eraser_draw_line**: Erase along a line
- **eraser_draw_rectangle**: Erase rectangle outline
- **eraser_fill_area**: Fill region with eraser strokes for complete clearing

### Files in This Repository

```
.
├── lamp_eraser.patch              # Patch to add eraser support
├── build_lamp_enhanced.sh         # Build script
├── DYNAMIC_UI_WITH_ERASER.md     # Complete documentation
├── svg_to_lamp.py                 # SVG to lamp converter (optional)
├── text_to_lamp.py                # Text renderer (optional)
└── resources/
    └── repos/
        └── rmkit/                 # rmkit source (submodule)
```

## Compatibility

- ✅ Tested on reMarkable 2 firmware 3.24
- ✅ Works without rm2fb (uses direct input injection)
- ✅ Compatible with xochitl (native stroke recognition)
- ✅ No root modifications required

## Documentation

See [DYNAMIC_UI_WITH_ERASER.md](DYNAMIC_UI_WITH_ERASER.md) for:
- Complete command reference
- Dynamic UI implementation patterns
- Animation techniques
- Optimization strategies
- Example code

## Utilities Included

### svg_to_lamp.py

Convert SVG files to lamp commands for custom symbols:

```bash
python3 svg_to_lamp.py resistor.svg 500 800 1.5 | lamp
```

### text_to_lamp.py

Render text as vector strokes:

```bash
python3 text_to_lamp.py "Hello" 500 800 0.5 | lamp
```

## Credits

- Based on [rmkit](https://github.com/rmkit-dev/rmkit) by rmkit-dev
- Eraser support added by analyzing reMarkable input events
- Inspired by the reMarkable community's amazing work

## License

This project maintains the same license as rmkit. See the original rmkit repository for license details.

## Related Work

- [rmkit](https://github.com/rmkit-dev/rmkit) - The original toolkit
- [lamp](https://rmkit.dev/apps/lamp) - Original lamp documentation
- [reMarkable](https://remarkable.com/) - The reMarkable tablet

---

**Note:** This is a development branch focused solely on lamp eraser enhancement. For complete project history, see the backup branch.
