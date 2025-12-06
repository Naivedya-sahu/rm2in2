# Component Library UI - Complete Guide

## Concept

A **visual menu system drawn with lamp** that provides a hierarchical component library. The UI is entirely made of pen strokes, so it integrates naturally with notebooks while providing menu-like functionality.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Main Drawing Area                  │
│                  (User's Circuit)                   │
│                                                     │
│                    y: 0-1400                        │
│                                                     │
│                                                     │
├─────────────────────────────────────────────────────┤
│  UI Region (Bottom 400px)          Component Zone  │
│  ┌──────────┐  ┌──────────┐       ┌──────────┐   │
│  │ Category │  │   Items  │       │ Selected │   │
│  │  Menu    │  │   Menu   │       │Component │   │
│  │          │  │          │       │  Preview │   │
│  │ Power    │  │ Battery  │       │    ⚡    │   │
│  │ Passives │  │ Ground   │       │          │   │
│  │ Actives  │  │ VCC      │       │          │   │
│  │ Diodes   │  │ AC Src   │       │          │   │
│  └──────────┘  └──────────┘       └──────────┘   │
│                                                     │
│                    y: 1400-1872                     │
└─────────────────────────────────────────────────────┘
```

## Features

✨ **Hierarchical Menu** - Categories expand to show components
✨ **State Machine** - Tracks current menu, category, selection
✨ **Visual Feedback** - UI drawn as boxes and lines
✨ **Dedicated Zone** - Components appear at y:1600 (bottom)
✨ **Gesture Navigation** - No button pressing needed
✨ **Native Integration** - All drawn elements can be selected/moved

## Installation

### 1. Deploy Files

```bash
cd /mnt/c/Users/NAVY/Documents/Github/rm2in2

# Copy UI script
scp component_library_ui.sh root@10.11.99.1:/opt/bin/
ssh root@10.11.99.1 'chmod +x /opt/bin/component_library_ui.sh'

# Copy genie configuration
scp genie_library_ui.conf root@10.11.99.1:/home/root/.config/genie/genie.conf

# Restart genie
ssh root@10.11.99.1 'killall genie 2>/dev/null; /opt/bin/genie &'
```

### 2. Verify Installation

```bash
ssh root@10.11.99.1

# Test state machine
/opt/bin/component_library_ui.sh toggle_menu

# Check state file
cat /tmp/component_ui_state
```

## Usage Workflow

### Step 1: Open Library UI

**Gesture:** 3-finger tap anywhere

**Result:** Main category menu draws at bottom-left:
- Power
- Passives
- Actives
- Diodes

### Step 2: Select Category

**Gestures in bottom-left zone:**
- Swipe UP → Power
- Swipe RIGHT → Passives
- Swipe DOWN → Actives
- Swipe LEFT → Diodes

**Result:** Item menu draws next to category menu

### Step 3: Select Component

**Gestures in bottom-center zone:**
- Tap top quarter → Item 1
- Tap second quarter → Item 2
- Tap third quarter → Item 3
- Tap bottom quarter → Item 4

**Result:** Component draws at x:750, y:1600 (bottom-center)

### Step 4: Move Component to Circuit

1. Switch to lasso selection tool
2. Select the drawn component
3. Drag it up to your circuit area
4. Repeat for more components

### Step 5: Close UI (when done)

**Gesture:** 3-finger tap (toggles closed)

**Cleanup:** Use eraser to remove the UI drawings

## Category Contents

### Power (Swipe UP)
1. Battery
2. Ground
3. VCC (power rail)
4. AC Source

### Passives (Swipe RIGHT)
1. Resistor
2. Capacitor
3. Inductor

### Actives (Swipe DOWN)
1. NPN Transistor
2. PNP Transistor
3. OpAmp
4. MOSFET

### Diodes (Swipe LEFT)
1. Diode
2. LED
3. Zener Diode
4. Schottky Diode

## Quick Access (Bypass Menu)

**Frequently used components:**

- Swipe DOWN on left edge → Resistor at y:1600
- Swipe DOWN on right edge → Ground at y:1600

## Advanced Gestures

**Navigation:**
- 2-finger swipe left (in bottom area) → Back to category menu

**Utility:**
- 4-finger tap → Draw circle at component zone (marking for erase)

## Example Session

```
1. Open notebook
2. 3-finger tap → Menu appears
3. Swipe UP (bottom-left) → Power category opens
4. Tap (bottom-center, top quarter) → Battery appears at y:1600
5. Use lasso tool → Select battery
6. Drag battery to circuit → Position at y:500
7. Swipe UP (bottom-left) → Power menu still open
8. Tap (bottom-center, second quarter) → Ground appears at y:1600
9. Use lasso → Move ground to circuit
10. 2-finger swipe left → Back to main menu
11. Swipe RIGHT (bottom-left) → Passives opens
12. Tap (bottom-center, top quarter) → Resistor at y:1600
13. Continue building circuit...
14. 3-finger tap → Close menu
15. Erase UI drawings from bottom
```

## Customization

### Add New Components

Edit `/opt/bin/component_library_ui.sh`:

```bash
# In draw_category_menu(), add new category:
"Sensors")
    items=("LDR" "Thermistor" "Pressure")
    ;;

# In draw_component(), add drawing code:
"LDR")
    echo "pen circle $x $y 50" | $LAMP
    echo "pen line $((x-60)) $((y-60)) $((x-40)) $((y-40))" | $LAMP
    ;;
```

### Adjust Component Zone

Edit variables in `component_library_ui.sh`:

```bash
COMPONENT_ZONE_X=750      # Horizontal position
COMPONENT_ZONE_Y=1600     # Vertical position
```

### Change UI Region

```bash
UI_REGION_TOP=1400        # Start of UI region
UI_REGION_BOTTOM=1822     # End of UI region
```

## Tips & Tricks

**Workflow Optimization:**
1. Keep component zone clear - move components up immediately
2. Build common sub-circuits, then copy-paste them
3. Use eraser to clear UI when switching notebooks
4. Quick access gestures for frequently used components

**Performance:**
- State machine runs fast (~100ms response)
- lamp drawing is instant
- No interference with xochitl

**Limitations:**
- Can't erase programmatically (use manual eraser)
- Text is simulated with lines (not readable as text)
- UI must be redrawn after erasure

## Troubleshooting

**Menu doesn't appear:**
```bash
# Check genie running
ssh root@10.11.99.1 'ps aux | grep genie'

# Test state machine directly
/opt/bin/component_library_ui.sh toggle_menu

# Check for lock file
rm /tmp/component_ui_lock
```

**Gestures not recognized:**
```bash
# Verify genie config
cat /home/root/.config/genie/genie.conf

# Restart genie
killall genie
/opt/bin/genie &
```

**Components draw in wrong location:**
```bash
# Check state file
cat /tmp/component_ui_state

# Reset state
rm /tmp/component_ui_state
```

## Architecture Details

### State Machine States

1. **CLOSED** - UI not visible
2. **MENU** - Main category menu visible
3. **CATEGORY** - Category expanded, items shown
4. **SELECTED** - Component drawn, ready to move

### State Transitions

```
CLOSED --[3-finger tap]--> MENU
MENU --[category gesture]--> CATEGORY
CATEGORY --[item tap]--> SELECTED
CATEGORY --[2-finger back]--> MENU
SELECTED --[any action]--> stays in state
ANY --[3-finger tap]--> CLOSED
```

### File Structure

```
/opt/bin/
  ├── component_library_ui.sh    # State machine & UI drawing
  ├── electrical_symbols.sh      # Component drawing functions
  ├── lamp                        # Input injection binary
  └── genie                       # Gesture recognition binary

/home/root/.config/genie/
  └── genie.conf                  # Gesture mappings

/tmp/
  ├── component_ui_state          # Current state storage
  └── component_ui_lock           # Concurrent access prevention
```

## Future Enhancements

**Possible additions:**
- [ ] Multi-page menus (more categories)
- [ ] Parameter selection (component values)
- [ ] Symbol rotation (horizontal/vertical)
- [ ] Component templates (common circuits)
- [ ] Favorites menu (most-used components)
- [ ] Search by gesture pattern

## Why This Approach Works

✅ **No rm2fb needed** - Pure input injection
✅ **Works on 3.24** - No firmware dependencies
✅ **No xochitl conflicts** - Seen as normal pen input
✅ **Native elements** - Full notebook integration
✅ **Persistent** - UI stays visible until erased
✅ **Extensible** - Easy to add components/categories

This is a creative workaround that turns the limitation (no UI apps) into a feature (UI becomes part of the notebook)!
