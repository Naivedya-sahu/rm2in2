# rm2in2 - Remarkable 2 Input Injection

Programmatic pen input injection tool for Remarkable 2 e-ink tablets, enabling automated drawing, handwriting, and graphics rendering.

## Project Status

🚧 **Under Active Development** - Coordinate system testing phase

### Current Focus
- **Coordinate System Analysis** - Testing multiple transformation approaches
- **Real Pen Behavior Capture** - Analyzing actual hardware input
- **Testing Framework** - Building validation tools before implementation

## Architecture

This project uses the **LD_PRELOAD** technique (inspired by [recept](https://github.com/funkey/recept)) to intercept input device reads and inject synthetic pen events.

### Components

- **Rm2/** - Server-side code (runs ON the Remarkable 2)
  - LD_PRELOAD injection hook
  - Event generation and queueing
  - FIFO command listener

- **Rm2in2/** - Client-side tools (runs on PC)
  - SVG/PNG to PEN command conversion
  - Text to handwriting generation
  - Command deployment scripts

- **resources/** - Archive of previous attempts and utilities

## Key Differences from Previous Attempts

### Problem with Previous Versions
All previous implementations (in `resources/previous-versions/`) have fundamental coordinate system issues:
- ✅ Simple lines work
- ❌ Curves don't render correctly
- ❌ Text appears distorted or wrong orientation
- ❌ Graphics are misaligned

### Root Cause
- Incorrect coordinate transformation between SVG space, PEN command space, and Wacom sensor space
- Decimal to integer conversion loses precision
- Orientation/axis mapping not properly verified against real pen behavior

### New Approach
1. **Test First** - Capture real pen behavior and analyze coordinate transformations
2. **Multiple Methods** - Try different transformation approaches systematically
3. **Validate Early** - Test with simple patterns before complex graphics
4. **Document Everything** - Record findings to prevent regression

## Hardware Details

- **Device:** Remarkable 2 e-ink tablet
- **Input:** Wacom EMR digitizer at `/dev/input/event1`
- **Resolution:** Wacom sensor provides coordinates in range X=0-20966, Y=0-15725
- **Display:** 1404×1872 pixels (portrait orientation)
- **Challenge:** Sensor is rotated 90° relative to display orientation

## Coordinate System (Under Investigation)

⚠️ **Current Status: Testing Multiple Approaches**

The relationship between these coordinate spaces needs verification:
- **SVG Space:** 1404×1872 (portrait, what you design in)
- **PEN Commands:** ??? (what format to use)
- **Wacom Hardware:** 0-20966 × 0-15725 (physical sensor)
- **Display Output:** 1404×1872 (portrait, what you see)

## Development Roadmap

### Phase 1: Coordinate System (Current)
- [ ] Build pen capture tools
- [ ] Test transformation approaches
- [ ] Validate with simple patterns
- [ ] Document verified coordinate system

### Phase 2: Injection System
- [ ] Implement verified coordinate transform in inject.c
- [ ] Build FIFO command parser
- [ ] Test with lines, curves, and complex shapes
- [ ] Deploy and validate on device

### Phase 3: Conversion Tools
- [ ] SVG to PEN converter
- [ ] PNG bitmap to PEN converter
- [ ] Text to handwriting generator
- [ ] Command optimization

### Phase 4: Polish
- [ ] Error handling and validation
- [ ] Performance optimization
- [ ] Documentation and examples
- [ ] Installation automation

## Building

```bash
# Not yet implemented - coordinate testing phase
make
```

## Testing

```bash
# Coordinate system testing (coming soon)
cd Rm2in2/tests
python coordinate_test.py
```

## Contributing

This is a clean-slate rewrite. Previous code is archived in `resources/previous-versions/` for reference only.

## License

MIT License (to be added)

## Credits

- Inspired by [recept](https://github.com/funkey/recept) by funkey
- Based on LD_PRELOAD input injection technique
- Built for the Remarkable 2 community
