# Dynamic UI with Eraser Support

Complete guide for lamp with eraser capabilities - enables truly dynamic, self-clearing UI.

## 🎉 Breakthrough: Eraser Support

Based on evtest revealing `BTN_TOOL_RUBBER` events, we've forked lamp to add full eraser emulation!

### What Changed

**Original lamp:**
- ✅ Pen drawing only
- ❌ No eraser - UI persists forever

**Enhanced lamp:**
- ✅ Pen drawing
- ✅ **Eraser support** - programmatic clearing!
- ✅ Dynamic UI - draw, erase, redraw
- ✅ State-based menus with transitions

## New Eraser Commands

### Basic Eraser Operations

```bash
# Erase a line
echo "eraser line 100 100 500 500" | lamp

# Erase a rectangle outline
echo "eraser rectangle 100 100 500 500" | lamp

# Fill/clear an entire area (with horizontal strokes)
echo "eraser fill 100 100 500 500 20" | lamp
# Parameters: x1 y1 x2 y2 [spacing]
# spacing: gap between eraser strokes (default: 20px)

# Dense clearing (tight spacing for complete erase)
echo "eraser clear 100 100 500 500" | lamp
# Uses 10px spacing for thorough erasure

# Low-level control
echo "eraser down 100 100" | lamp  # Start erasing
echo "eraser move 200 200" | lamp  # Erase to position
echo "eraser up" | lamp            # Stop erasing
```

### Comparison: Pen vs Eraser

```bash
# DRAWING
echo "pen line 100 100 500 100" | lamp
echo "pen rectangle 100 200 500 400" | lamp

# ERASING (same syntax, different tool)
echo "eraser line 100 100 500 100" | lamp
echo "eraser rectangle 100 200 500 400" | lamp
```

## Dynamic UI Implementation

### Example: Menu with Clear/Redraw

```bash
#!/bin/bash
# dynamic_menu.sh - Self-clearing menu system

LAMP="/opt/bin/lamp"

# Define UI region
UI_X1=50
UI_Y1=1400
UI_X2=1350
UI_Y2=1850

# Clear UI region
clear_ui() {
    echo "eraser fill $UI_X1 $UI_Y1 $UI_X2 $UI_Y2 15" | $LAMP
}

# Draw main menu
draw_main_menu() {
    clear_ui

    # Menu container
    echo "pen rectangle $UI_X1 $UI_Y1 $((UI_X1+300)) $UI_Y2" | $LAMP

    # Category items
    local y=$((UI_Y1 + 80))
    for i in 1 2 3 4; do
        echo "pen rectangle $((UI_X1+10)) $y $((UI_X1+290)) $((y+70))" | $LAMP
        y=$((y + 90))
    done
}

# Draw category submenu
draw_category_menu() {
    # Clear only the submenu area (not main menu)
    echo "eraser fill $((UI_X1+320)) $UI_Y1 $((UI_X1+620)) $UI_Y2 15" | $LAMP

    # Draw submenu
    echo "pen rectangle $((UI_X1+320)) $UI_Y1 $((UI_X1+620)) $UI_Y2" | $LAMP

    # Items
    local y=$((UI_Y1 + 80))
    for i in 1 2 3; do
        echo "pen rectangle $((UI_X1+330)) $y $((UI_X1+610)) $((y+60))" | $LAMP
        y=$((y + 80))
    done
}

# Example usage
draw_main_menu
sleep 1
draw_category_menu
sleep 2
clear_ui  # Clean slate
```

### Updated Component Library UI

```bash
#!/bin/bash
# component_library_ui_v2.sh - With eraser support

STATE_FILE="/tmp/component_ui_state"
LAMP="/opt/bin/lamp"

# UI regions
MENU_REGION="50 1400 350 1850"
SUBMENU_REGION="370 1400 670 1850"
COMPONENT_REGION="700 1400 1350 1850"

clear_menu() {
    echo "eraser fill $MENU_REGION 15" | $LAMP
}

clear_submenu() {
    echo "eraser fill $SUBMENU_REGION 15" | $LAMP
}

clear_component_zone() {
    echo "eraser fill $COMPONENT_REGION 15" | $LAMP
}

clear_all_ui() {
    echo "eraser fill 50 1400 1350 1850 15" | $LAMP
}

draw_main_menu() {
    clear_menu

    # Draw menu UI
    echo "pen rectangle 50 1400 350 1850" | $LAMP

    # Category boxes
    local categories=("Power" "Passives" "Actives" "Diodes")
    local y=1480

    for cat in "${categories[@]}"; do
        echo "pen rectangle 70 $y 330 $((y+80))" | $LAMP

        # Draw category label using text_to_lamp.py
        python3 /opt/bin/text_to_lamp.py "$cat" 90 $((y+20)) 0.4 | $LAMP

        y=$((y + 100))
    done
}

draw_category_items() {
    local category=$1
    clear_submenu

    # Draw submenu container
    echo "pen rectangle 370 1400 670 1850" | $LAMP

    # Get items for category
    case "$category" in
        "Power")
            items=("Battery" "Ground" "VCC")
            ;;
        "Passives")
            items=("Resistor" "Capacitor" "Inductor")
            ;;
        *)
            items=()
            ;;
    esac

    # Draw items
    local y=1480
    for item in "${items[@]}"; do
        echo "pen rectangle 390 $y 650 $((y+70))" | $LAMP
        python3 /opt/bin/text_to_lamp.py "$item" 410 $((y+15)) 0.35 | $LAMP
        y=$((y + 90))
    done
}

draw_component() {
    local component=$1
    clear_component_zone

    # Draw component using SVG
    local svg_file=""
    case "$component" in
        "Resistor")
            svg_file="/opt/electrical_symbols/passive/resistor.svg"
            ;;
        "Battery")
            svg_file="/opt/electrical_symbols/power/battery.svg"
            ;;
    esac

    if [ -n "$svg_file" ]; then
        python3 /opt/bin/svg_to_lamp.py "$svg_file" 900 1600 1.5 | $LAMP
    fi
}

# State machine with clearing
handle_action() {
    local action=$1

    case "$action" in
        "open_menu")
            draw_main_menu
            ;;
        "select_category")
            draw_category_items "$2"
            ;;
        "select_item")
            draw_component "$2"
            ;;
        "back")
            clear_submenu
            ;;
        "close")
            clear_all_ui
            ;;
    esac
}
```

## Advanced Eraser Techniques

### Selective Erasure

```bash
# Erase only specific UI element
erase_button() {
    local x=$1 y=$2 width=$3 height=$4
    # Add padding to ensure complete erasure
    echo "eraser fill $((x-5)) $((y-5)) $((x+width+5)) $((y+height+5)) 12" | lamp
}

# Erase and redraw (smooth transition)
update_button() {
    erase_button 100 1500 200 80
    usleep 50000  # 50ms delay
    echo "pen rectangle 100 1500 300 1580" | lamp
    python3 /opt/bin/text_to_lamp.py "Updated" 120 1520 0.4 | lamp
}
```

### Animated UI Transitions

```bash
# Fade out effect (progressive erasure)
fade_out_region() {
    local x1=$1 y1=$2 x2=$3 y2=$4

    # Multiple passes with increasing spacing
    for spacing in 40 25 15 10; do
        echo "eraser fill $x1 $y1 $x2 $y2 $spacing" | lamp
        usleep 100000  # 100ms between passes
    done
}

# Slide out effect (directional erase)
slide_out_left() {
    local x1=$1 y1=$2 x2=$3 y2=$4
    local step=20

    for ((x=$x1; x<=$x2; x+=step)); do
        echo "eraser fill $x $y1 $((x+step)) $y2 10" | lamp
        usleep 20000
    done
}
```

### UI State Persistence

```bash
# Save UI snapshot before clearing
save_ui_state() {
    local state=$1
    echo "$state" > /tmp/ui_snapshot
    # Optionally save positions of drawn elements
}

# Restore UI from snapshot
restore_ui_state() {
    local state=$(cat /tmp/ui_snapshot)
    case "$state" in
        "main_menu")
            draw_main_menu
            ;;
        "category_power")
            draw_main_menu
            draw_category_items "Power"
            ;;
    esac
}
```

## Eraser Optimization

### Efficient Region Clearing

```bash
# BAD: Too many small eraser strokes (slow)
for ((y=1400; y<1850; y+=5)); do
    echo "eraser line 50 $y 1350 $y" | lamp
done

# GOOD: Larger spacing, fewer strokes (fast)
echo "eraser fill 50 1400 1350 1850 15" | lamp

# OPTIMAL: Adaptive spacing based on area size
area_width=$((x2 - x1))
spacing=$((area_width / 50))  # ~50 strokes total
[ $spacing -lt 10 ] && spacing=10  # Minimum spacing
echo "eraser fill $x1 $y1 $x2 $y2 $spacing" | lamp
```

### Partial Updates

```bash
# Only erase what changed
update_menu_selection() {
    local old_y=$1
    local new_y=$2

    # Erase old selection highlight
    echo "eraser rectangle 65 $old_y 335 $((old_y+85))" | lamp

    # Draw new selection highlight
    echo "pen rectangle 65 $new_y 335 $((new_y+85))" | lamp
}
```

## Complete Dynamic UI Example

```bash
#!/bin/bash
# Full dynamic component library with eraser

LAMP="/opt/bin/lamp"
STATE="closed"
CATEGORY=""

# UI coordinates
declare -A UI_REGIONS=(
    [menu_x1]=50 [menu_y1]=1400 [menu_x2]=350 [menu_y2]=1850
    [sub_x1]=370 [sub_y1]=1400 [sub_x2]=670 [sub_y2]=1850
    [comp_x1]=700 [comp_y1]=1400 [comp_x2]=1350 [comp_y2]=1850
)

clear_region() {
    local name=$1
    local x1=${UI_REGIONS[${name}_x1]}
    local y1=${UI_REGIONS[${name}_y1]}
    local x2=${UI_REGIONS[${name}_x2]}
    local y2=${UI_REGIONS[${name}_y2]}

    echo "eraser fill $x1 $y1 $x2 $y2 15" | $LAMP
}

open_library() {
    clear_region "menu"
    clear_region "sub"
    clear_region "comp"

    # Draw main menu
    echo "pen rectangle ${UI_REGIONS[menu_x1]} ${UI_REGIONS[menu_y1]} ${UI_REGIONS[menu_x2]} ${UI_REGIONS[menu_y2]}" | $LAMP

    # Draw categories
    python3 /opt/bin/text_to_lamp.py "Power" 80 1480 0.5 | $LAMP
    python3 /opt/bin/text_to_lamp.py "Passives" 80 1600 0.5 | $LAMP
    python3 /opt/bin/text_to_lamp.py "Actives" 80 1720 0.5 | $LAMP

    STATE="menu"
}

select_category() {
    CATEGORY=$1
    clear_region "sub"

    # Draw submenu
    echo "pen rectangle ${UI_REGIONS[sub_x1]} ${UI_REGIONS[sub_y1]} ${UI_REGIONS[sub_x2]} ${UI_REGIONS[sub_y2]}" | $LAMP

    # Draw items based on category
    # ... (implementation continues)

    STATE="category"
}

close_library() {
    clear_region "menu"
    clear_region "sub"
    clear_region "comp"
    STATE="closed"
}

# Gesture integration
# genie calls these functions based on gestures
case "$1" in
    open) open_library ;;
    category_power) select_category "Power" ;;
    close) close_library ;;
esac
```

## Benefits of Eraser Support

### ✅ True Dynamic UI
- Menus can transition smoothly
- No accumulation of old UI elements
- Clean state management

### ✅ Better UX
- Clear visual feedback
- Responsive UI updates
- Professional appearance

### ✅ Resource Efficient
- Reuse same screen area
- No need to manually erase
- Automated cleanup

### ✅ Advanced Features
- Animations and transitions
- Hover effects (erase/redraw)
- Loading indicators
- Progress bars

## Migration Guide

### From Static to Dynamic UI

**Before (static UI):**
```bash
# UI persists forever, user must manually erase
draw_menu() {
    echo "pen rectangle 50 1400 350 1850" | lamp
    # Menu stays visible until manual erasure
}
```

**After (dynamic UI):**
```bash
# UI can be cleared programmatically
draw_menu() {
    clear_ui_region
    echo "pen rectangle 50 1400 350 1850" | lamp
    # Can be cleared and redrawn anytime
}
```

## Build & Deploy

```bash
# Build enhanced lamp
cd /mnt/c/Users/NAVY/Documents/Github/rm2in2
chmod +x build_lamp_enhanced.sh
./build_lamp_enhanced.sh

# Deploy
scp resources/repos/rmkit/src/build/lamp root@10.11.99.1:/opt/bin/

# Test eraser
ssh root@10.11.99.1

# Draw something
echo "pen rectangle 100 100 500 500" | /opt/bin/lamp

# Erase it
echo "eraser fill 100 100 500 500 15" | /opt/bin/lamp
```

## Summary

With eraser support, lamp becomes a complete UI system:
- **Draw** UI elements with pen commands
- **Erase** UI elements with eraser commands
- **Update** UI dynamically with state machines
- **Animate** transitions and effects

This transforms lamp from a static drawing tool into a dynamic UI framework!
