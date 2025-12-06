# lamp-eraser 🧹

Enhanced version of [rmkit's lamp](https://github.com/rmkit-dev/rmkit) with **programmatic eraser** support for reMarkable tablets.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![reMarkable](https://img.shields.io/badge/reMarkable-2-green.svg)](https://remarkable.com/)
[![Firmware](https://img.shields.io/badge/Firmware-3.24-blue.svg)]()

## ✨ Features

- 🎨 **Full eraser tool emulation** via `BTN_TOOL_RUBBER` input events
- 🔄 **Dynamic self-clearing UI** - menus can erase and redraw themselves
- 🎭 **Smooth transitions** - professional menu animations
- 📱 **No rm2fb required** - works on firmware 3.24+
- ✅ **Native integration** - xochitl recognizes all strokes
- 🎯 **Complete parity** - eraser has same capabilities as pen

## 🚀 Quick Start

### Build

```bash
# Clone repository
git clone https://github.com/yourusername/lamp-eraser.git
cd lamp-eraser

# Build enhanced lamp
./build_lamp_enhanced.sh
```

### Deploy

```bash
# Copy to reMarkable
scp resources/repos/rmkit/src/build/lamp root@10.11.99.1:/opt/bin/

# Test
ssh root@10.11.99.1
echo "pen rectangle 100 100 500 500" | /opt/bin/lamp
echo "eraser fill 100 100 500 500 15" | /opt/bin/lamp
```

## 📖 Usage

### Basic Commands

```bash
# Erase a line
echo "eraser line x1 y1 x2 y2" | lamp

# Erase rectangle outline
echo "eraser rectangle x1 y1 x2 y2" | lamp

# Clear entire area (fill with eraser strokes)
echo "eraser fill x1 y1 x2 y2 [spacing]" | lamp

# Dense clearing (complete erasure)
echo "eraser clear x1 y1 x2 y2" | lamp
```

### Low-Level Control

```bash
echo "eraser down x y" | lamp   # Start erasing
echo "eraser move x y" | lamp   # Erase to position
echo "eraser up" | lamp         # Stop erasing
```

## 🎯 Use Cases

### Dynamic Menus

```bash
# Draw menu
echo "pen rectangle 50 1400 350 1850" | lamp

# User makes selection...

# Transition to new screen
echo "eraser fill 50 1400 350 1850 15" | lamp
echo "pen rectangle 370 1400 670 1850" | lamp
```

### Self-Clearing Component Library

```bash
# Show component
python3 svg_to_lamp.py resistor.svg 700 1600 1.5 | lamp
python3 text_to_lamp.py "10kΩ" 720 1680 0.5 | lamp

# User moves it with lasso...

# Clear preview area
echo "eraser fill 700 1400 1350 1850 15" | lamp
```

## 🧪 Examples

### Run Demos

```bash
# Basic eraser tests
./test_eraser.sh

# Dynamic UI demo
./examples/dynamic_ui_demo.sh
```

### Try Example SVG Symbols

```bash
# Resistor
python3 svg_to_lamp.py examples/svg_symbols/resistor.svg 500 800 2.0 | lamp

# Capacitor
python3 svg_to_lamp.py examples/svg_symbols/capacitor.svg 500 800 2.0 | lamp

# Ground
python3 svg_to_lamp.py examples/svg_symbols/ground.svg 500 800 2.0 | lamp
```

## 🛠️ How It Works

### The Discovery

Using `evtest`, we discovered the reMarkable recognizes `BTN_TOOL_RUBBER` events:

```
Event: time 1234.567890, type 1 (EV_KEY), code 321 (BTN_TOOL_RUBBER), value 1
```

### The Implementation

Just like lamp emulates `BTN_TOOL_PEN` for drawing, we emulate `BTN_TOOL_RUBBER` for erasing:

```cpp
// Drawing
ev.push_back(input_event{ type:EV_KEY, code:BTN_TOOL_PEN, value: 1 })

// Erasing
ev.push_back(input_event{ type:EV_KEY, code:BTN_TOOL_RUBBER, value: 1 })
```

Same coordinate system, same pressure values, same event injection mechanism!

## 📁 Repository Structure

```
.
├── README.md                      # This file
├── LICENSE                        # MIT License
├── lamp_eraser.patch             # Patch adding eraser support
├── build_lamp_enhanced.sh        # Build script
├── test_eraser.sh                # Quick test suite
├── DYNAMIC_UI_WITH_ERASER.md    # Complete documentation
├── svg_to_lamp.py                # SVG to lamp converter
├── text_to_lamp.py               # Text renderer
├── examples/
│   ├── dynamic_ui_demo.sh        # Interactive UI demo
│   └── svg_symbols/              # Example SVG symbols
│       ├── resistor.svg
│       ├── capacitor.svg
│       └── ground.svg
└── resources/
    └── repos/
        └── rmkit/                # rmkit source (submodule)
```

## 🔧 Prerequisites

- ARM cross-compiler: `gcc-arm-linux-gnueabihf`, `g++-arm-linux-gnueabihf`
- [okp](https://github.com/raisjn/okp) transpiler
- reMarkable tablet (tested on firmware 3.24)

### Installing Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt-get install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf
```

**okp (via Go):**
```bash
# Install Go first, then:
git clone https://github.com/raisjn/okp.git
cd okp
# Follow okp installation instructions
```

## 📚 Documentation

- [DYNAMIC_UI_WITH_ERASER.md](DYNAMIC_UI_WITH_ERASER.md) - Complete guide
  - Command reference
  - Dynamic UI patterns
  - Animation techniques
  - Optimization strategies

## ✅ Compatibility

| Device | Firmware | Status |
|--------|----------|--------|
| reMarkable 2 | 3.24 | ✅ Tested |
| reMarkable 2 | 3.15-3.23 | ✅ Should work |
| reMarkable 1 | Any | ⚠️ Untested |

**Note:** Works without rm2fb - uses direct input injection.

## 🎨 Utilities

### svg_to_lamp.py

Convert SVG files to lamp commands:

```bash
python3 svg_to_lamp.py symbol.svg x y scale | lamp
```

### text_to_lamp.py

Render text as vector strokes:

```bash
python3 text_to_lamp.py "Hello" x y size | lamp
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on actual reMarkable hardware
5. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

This project includes [rmkit](https://github.com/rmkit-dev/rmkit) (MIT License).

## 🙏 Credits

- Based on [rmkit](https://github.com/rmkit-dev/rmkit) by rmkit-dev
- Eraser support inspired by reMarkable input event analysis
- Thanks to the amazing reMarkable community

## 🔗 Related Projects

- [rmkit](https://github.com/rmkit-dev/rmkit) - The original remarkable tablet toolkit
- [remarkable-hacks](https://github.com/ddvk/remarkable-hacks) - Patches for xochitl
- [reMarkable-tools](https://github.com/reHackable/awesome-reMarkable) - Community tools collection

## ⚠️ Disclaimer

This is an unofficial modification. Use at your own risk. Not affiliated with reMarkable AS.

---

**Made with ❤️ for the reMarkable community**
