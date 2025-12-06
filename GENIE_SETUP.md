# Genie + Lamp Electrical Symbols Setup

## Overview
Use gesture controls to insert electrical symbols that become native notebook elements you can select, move, and manipulate.

## Workflow
1. **Draw a gesture** (swipe/tap in designated zones)
2. **genie triggers lamp** to draw the symbol
3. **Symbol appears as native strokes** in xochitl
4. **Use lasso tool** to select, move, copy, resize the symbol

## Installation

### 1. Deploy files to reMarkable
```bash
# Copy configuration
scp genie.conf root@10.11.99.1:/home/root/.config/genie/

# Ensure binaries are in place
scp electrical_symbols.sh root@10.11.99.1:/opt/bin/
scp resources/repos/rmkit/src/build/genie root@10.11.99.1:/opt/bin/
scp resources/repos/rmkit/src/build/lamp root@10.11.99.1:/opt/bin/

# Set permissions
ssh root@10.11.99.1 'chmod +x /opt/bin/{genie,lamp,electrical_symbols.sh}'
```

### 2. Create config directory
```bash
ssh root@10.11.99.1 'mkdir -p /home/root/.config/genie'
```

### 3. Start genie
```bash
ssh root@10.11.99.1
killall genie 2>/dev/null  # Stop any running instance
/opt/bin/genie &
exit
```

## Gesture Map

### Edge Gestures (Symbol Insertion at x:700, y:900)

**Left Edge (top quarter):**
- Swipe UP → Resistor
- Swipe DOWN → Capacitor

**Top Edge:**
- Swipe RIGHT (left quarter) → Inductor
- Swipe LEFT (right quarter) → Ground

**Right Edge (top quarter):**
- Swipe UP → Battery
- Swipe DOWN → Diode

**Center Zone Gestures:**
- 2-finger TAP → Circle
- 3-finger TAP → Rectangle
- Swipe RIGHT (center) → Horizontal wire
- Swipe UP (center) → Vertical wire

## Usage Example

1. Open a notebook in xochitl
2. Perform gesture (e.g., swipe up on left edge)
3. Symbol appears at center screen (700, 900)
4. Switch to lasso selection tool
5. Select the symbol
6. Drag it to desired position in your circuit
7. Repeat for other components

## Customization

### Adjust Insertion Point
Edit `/home/root/.config/genie/genie.conf` and change coordinates in command lines:
```
command=/opt/bin/electrical_symbols.sh resistor X Y SIZE
```

Where:
- X: 0-1404 (horizontal position)
- Y: 0-1872 (vertical position)
- SIZE: component size in pixels (default: 100)

### Add More Symbols
Edit `electrical_symbols.sh` to add new component types:
```bash
draw_transistor() {
    # Your drawing code using lamp commands
}
```

Then add gesture to `genie.conf`:
```
gesture=swipe
direction=up
command=/opt/bin/electrical_symbols.sh transistor 700 900 100
zone=0.4 0 0.6 0.1
fingers=1
```

## Troubleshooting

**Genie not responding:**
```bash
ssh root@10.11.99.1
ps aux | grep genie  # Check if running
killall genie
/opt/bin/genie &
```

**Symbols not appearing:**
```bash
# Test lamp directly
echo 'pen circle 700 900 100' | /opt/bin/lamp
# Test symbol script
/opt/bin/electrical_symbols.sh resistor 700 900 100
```

**Check genie logs:**
```bash
ssh root@10.11.99.1
killall genie
/opt/bin/genie  # Run in foreground to see errors
```

## Advantages of This Approach

✅ **Native integration** - symbols are real strokes xochitl understands
✅ **Fully editable** - select, move, copy, delete like any drawing
✅ **No conflicts** - works perfectly on firmware 3.24 without rm2fb
✅ **Gesture-based** - quick insertion without switching apps
✅ **Reusable** - create symbol libraries, copy-paste components
✅ **Future-proof** - doesn't depend on xochitl internals

## Next Steps

1. Add more electrical symbols (transistors, transformers, switches, etc.)
2. Create template notebooks with common circuit layouts
3. Build symbol palette with multiple insertion zones
4. Add parameterized symbols (variable resistance values, etc.)
