## SVG Component Injection System

Complete system for using custom SVG electrical symbols with lamp.

## Key Capabilities & Limitations

### ✅ What lamp CAN Do:
- ✅ Draw vector paths (lines, beziers, arcs)
- ✅ Inject pen input events recognized by xochitl
- ✅ Convert SVG paths to native strokes
- ✅ Render text as vector strokes
- ✅ Create complex custom symbols
- ✅ Runtime injection (no pre-compilation)

### ❌ What lamp CANNOT Do:
- ❌ **Erase strokes** - Can only draw, not erase
- ❌ **Render bitmap text** - Text must be vectors
- ❌ **Fill shapes** - Only outlines/strokes
- ❌ **Detect existing strokes** - No feedback from xochitl

## Workarounds for Limitations

### Erasing UI Elements

Since lamp cannot erase, we have options:

**Option 1: Manual Erasure (Recommended)**
- Draw UI at bottom of page
- User manually erases UI when done
- Simple and reliable

**Option 2: Non-Conflicting UI Design**
- Use dedicated region user never draws in
- Bottom 400px reserved for library UI
- Main circuit area: 0-1400px
- Library UI area: 1400-1872px
- User won't accidentally draw over UI

**Option 3: Redraw-Based UI (Advanced)**
- Each state transition redraws entire UI
- Previous UI becomes "background noise"
- User erases periodically
- Works but creates clutter

**Recommendation:** Use Option 2 - dedicated non-conflicting region

## SVG Component Library Setup

### 1. Create SVG Symbol Files

Create SVG files for your electrical components:

```xml
<!-- resistor.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40">
  <path d="M 0 20 L 20 20 L 25 10 L 35 30 L 45 10 L 55 30 L 65 10 L 75 30 L 80 20 L 100 20"
        stroke="black" fill="none" stroke-width="2"/>
</svg>

<!-- capacitor.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 60">
  <line x1="0" y1="30" x2="45" y2="30" stroke="black" stroke-width="2"/>
  <line x1="45" y1="10" x2="45" y2="50" stroke="black" stroke-width="2"/>
  <line x1="55" y1="10" x2="55" y2="50" stroke="black" stroke-width="2"/>
  <line x1="55" y1="30" x2="100" y2="30" stroke="black" stroke-width="2"/>
</svg>

<!-- transistor_npn.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 100">
  <circle cx="40" cy="50" r="30" stroke="black" fill="none" stroke-width="2"/>
  <line x1="25" y1="30" x2="25" y2="70" stroke="black" stroke-width="3"/>
  <line x1="0" y1="50" x2="25" y2="50" stroke="black" stroke-width="2"/>
  <line x1="25" y1="35" x2="50" y2="20" stroke="black" stroke-width="2"/>
  <line x1="25" y1="65" x2="50" y2="80" stroke="black" stroke-width="2"/>
  <line x1="50" y1="20" x2="50" y2="0" stroke="black" stroke-width="2"/>
  <line x1="50" y1="80" x2="50" y2="100" stroke="black" stroke-width="2"/>
  <!-- Arrow for emitter -->
  <polygon points="50,80 45,75 45,85" fill="black"/>
</svg>
```

### 2. Organize Component Library

```bash
mkdir -p /opt/electrical_symbols/
cd /opt/electrical_symbols/

# Passive components
mkdir passive
# resistor.svg, capacitor.svg, inductor.svg

# Active components
mkdir active
# transistor_npn.svg, transistor_pnp.svg, mosfet_n.svg, opamp.svg

# Diodes
mkdir diodes
# diode.svg, led.svg, zener.svg, schottky.svg

# Power symbols
mkdir power
# ground.svg, vcc.svg, battery.svg, ac_source.svg

# ICs and complex
mkdir ics
# 555_timer.svg, 741_opamp.svg, logic_gates.svg
```

### 3. Deploy Tools

```bash
# Copy SVG converter
scp svg_to_lamp.py root@10.11.99.1:/opt/bin/
scp text_to_lamp.py root@10.11.99.1:/opt/bin/
chmod +x /opt/bin/{svg_to_lamp.py,text_to_lamp.py}

# Copy SVG library
scp -r /path/to/your/svg/library/* root@10.11.99.1:/opt/electrical_symbols/
```

## Usage Examples

### Basic SVG Injection

```bash
# Inject resistor at position (500, 800) with scale 2.0
python3 /opt/bin/svg_to_lamp.py \
    /opt/electrical_symbols/passive/resistor.svg \
    500 800 2.0 | /opt/bin/lamp

# Inject transistor at (700, 900) default scale
python3 /opt/bin/svg_to_lamp.py \
    /opt/electrical_symbols/active/transistor_npn.svg \
    700 900 | /opt/bin/lamp
```

### With Text Labels

```bash
# Draw resistor with "10kΩ" label
python3 /opt/bin/svg_to_lamp.py \
    /opt/electrical_symbols/passive/resistor.svg \
    500 800 2.0 | /opt/bin/lamp

python3 /opt/bin/text_to_lamp.py "10kΩ" 520 870 0.5 | /opt/bin/lamp
```

### Integrated Component Function

Create wrapper script:

```bash
#!/bin/bash
# inject_component.sh <category> <component> <x> <y> [scale] [label]

CATEGORY=$1
COMPONENT=$2
X=$3
Y=$4
SCALE=${5:-1.0}
LABEL=$6

SVG_PATH="/opt/electrical_symbols/${CATEGORY}/${COMPONENT}.svg"

# Inject SVG
python3 /opt/bin/svg_to_lamp.py "$SVG_PATH" "$X" "$Y" "$SCALE" | /opt/bin/lamp

# Add label if provided
if [ -n "$LABEL" ]; then
    LABEL_Y=$((Y + 70))
    python3 /opt/bin/text_to_lamp.py "$LABEL" "$X" "$LABEL_Y" 0.4 | /opt/bin/lamp
fi
```

Usage:
```bash
inject_component.sh passive resistor 500 800 1.5 "4.7kΩ"
inject_component.sh active transistor_npn 700 900 1.0 "2N3904"
```

## UI System Integration

### SVG-Based Component Library UI

Updated component_library_ui.sh to use SVG:

```bash
draw_component() {
    local component=$1
    local x=$COMPONENT_ZONE_X
    local y=$COMPONENT_ZONE_Y
    local svg_file=""
    local label=""

    case "$component" in
        "Resistor")
            svg_file="/opt/electrical_symbols/passive/resistor.svg"
            label="R"
            ;;
        "Capacitor")
            svg_file="/opt/electrical_symbols/passive/capacitor.svg"
            label="C"
            ;;
        "NPN Trans")
            svg_file="/opt/electrical_symbols/active/transistor_npn.svg"
            label="Q"
            ;;
        # ... more components
    esac

    if [ -n "$svg_file" ]; then
        python3 /opt/bin/svg_to_lamp.py "$svg_file" $x $y 1.5 | /opt/bin/lamp

        # Add label
        if [ -n "$label" ]; then
            python3 /opt/bin/text_to_lamp.py "$label" $x $((y+80)) 0.5 | /opt/bin/lamp
        fi
    fi
}
```

### Genie Integration

Update genie.conf to use SVG injection:

```bash
# Resistor gesture
gesture=swipe
direction=up
command=python3 /opt/bin/svg_to_lamp.py /opt/electrical_symbols/passive/resistor.svg 750 1600 1.5 | /opt/bin/lamp
zone=0 0.75 0.1 1
fingers=1
```

## Advanced Features

### Parameterized Components

Create SVG templates with placeholders:

```python
# component_injector.py
def inject_resistor(x, y, value="10k", scale=1.0):
    # Inject resistor SVG
    svg_to_lamp("resistor.svg", x, y, scale)

    # Calculate label position and size based on value length
    label_x = x - len(value) * 7
    label_y = y + 70

    text_to_lamp(value + "Ω", label_x, label_y, 0.4)
```

### Component Rotation

Add rotation parameter to SVG conversion:

```python
def parse_svg_file(self, svg_path, scale=1.0, offset_x=0, offset_y=0, rotation=0):
    # Apply rotation transformation
    # rotation in degrees, 0=horizontal, 90=vertical
```

### Symbol Libraries

Build comprehensive libraries:

```
/opt/electrical_symbols/
├── ieee_std/          # IEEE standard symbols
├── iec_std/           # IEC standard symbols
├── custom/            # Your custom symbols
├── circuits/          # Common circuit blocks
│   ├── amplifier_stage.svg
│   ├── power_supply.svg
│   └── filter_lpf.svg
└── templates/         # Parameterized templates
```

## Best Practices

### 1. SVG Design Guidelines

- **Keep it simple:** Use paths, not complex effects
- **Use viewBox:** Enables proper scaling
- **Stroke only:** No fills (lamp can't fill)
- **Reasonable complexity:** < 100 path segments
- **Test scaling:** Verify at different sizes

### 2. Non-Conflicting UI Design

```
Screen Layout (1404 x 1872):

┌──────────────────────────────────┐
│                                  │ 0
│                                  │
│        Circuit Drawing           │
│        Area                      │
│        (User Space)              │
│                                  │
│                                  │ 1400
├──────────────────────────────────┤
│  [Category] [Items] [Component]  │
│  Library UI (Reserved Space)     │ 1872
└──────────────────────────────────┘

Rules:
- User draws circuits in 0-1400
- Library UI only uses 1400-1872
- No overlap = no conflicts
- User can erase UI area separately
```

### 3. Component Naming Convention

```
<type>_<variant>_<orientation>.svg

Examples:
resistor_std_h.svg          # Standard resistor, horizontal
resistor_var_h.svg          # Variable resistor, horizontal
capacitor_electrolytic_v.svg # Electrolytic capacitor, vertical
transistor_npn_std.svg      # NPN transistor, standard
```

### 4. Performance Optimization

```bash
# Cache compiled commands
svg_to_lamp.py resistor.svg 0 0 1.0 > /tmp/resistor_cmds.txt

# Inject from cache
cat /tmp/resistor_cmds.txt | /opt/bin/lamp
```

## Troubleshooting

**SVG not rendering:**
- Check viewBox attribute
- Verify path syntax
- Test with simple shapes first

**Text not readable:**
- Increase size parameter
- Use shorter strings
- Check stroke font rendering

**Component position wrong:**
- Verify coordinate system
- Check offset parameters
- Test with known coordinates

**UI conflicts with drawings:**
- Ensure UI uses bottom region only
- Verify y-coordinates > 1400
- Check genie gesture zones

## Future Enhancements

- [ ] Component rotation support
- [ ] SVG fill-to-outline conversion
- [ ] Bitmap-to-vector text rendering
- [ ] Component value annotations
- [ ] Multi-page symbol catalogs
- [ ] Search/filter functionality
- [ ] Favorites system
- [ ] Export circuit as combined SVG

This system gives you full control over component appearance while working within lamp's capabilities!
