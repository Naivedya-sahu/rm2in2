#!/bin/bash
# Component Library UI - State machine driven UI using lamp
# Creates a visual menu system drawn as pen strokes

LAMP="/opt/bin/lamp"
STATE_FILE="/tmp/component_ui_state"
LOCK_FILE="/tmp/component_ui_lock"

# UI Layout Configuration
UI_REGION_TOP=1400        # Bottom region starts at y=1400
UI_REGION_LEFT=50
UI_REGION_RIGHT=1354
UI_REGION_BOTTOM=1822

MENU_WIDTH=300
MENU_HEIGHT=400
CATEGORY_HEIGHT=80
ITEM_HEIGHT=60

COMPONENT_ZONE_X=750      # Where selected components appear
COMPONENT_ZONE_Y=1600

# State machine states
STATE_CLOSED="closed"
STATE_MENU="menu"
STATE_CATEGORY="category"
STATE_SELECTED="selected"

# Initialize state
init_state() {
    echo "state=$STATE_CLOSED" > "$STATE_FILE"
    echo "category=" >> "$STATE_FILE"
    echo "selected=" >> "$STATE_FILE"
}

# Read current state
read_state() {
    if [ ! -f "$STATE_FILE" ]; then
        init_state
    fi
    source "$STATE_FILE"
}

# Update state
update_state() {
    local new_state=$1
    local new_category=$2
    local new_selected=$3

    echo "state=$new_state" > "$STATE_FILE"
    echo "category=$new_category" >> "$STATE_FILE"
    echo "selected=$new_selected" >> "$STATE_FILE"
}

# Drawing primitives using lamp
draw_box() {
    local x1=$1 y1=$2 x2=$3 y2=$4
    echo "pen rectangle $x1 $y1 $x2 $y2" | $LAMP
}

draw_line() {
    local x1=$1 y1=$2 x2=$3 y2=$4
    echo "pen line $x1 $y1 $x2 $y2" | $LAMP
}

draw_text_block() {
    # Simulate text with horizontal lines (readable as labels)
    local x=$1 y=$2 width=$3
    local line_count=${4:-3}
    local spacing=8

    for ((i=0; i<line_count; i++)); do
        local ypos=$((y + i * spacing))
        echo "pen line $x $ypos $((x + width)) $ypos" | $LAMP
    done
}

# Draw main menu
draw_main_menu() {
    local x=$UI_REGION_LEFT
    local y=$UI_REGION_TOP

    # Menu container
    draw_box $x $y $((x + MENU_WIDTH)) $UI_REGION_BOTTOM

    # Title area
    draw_line $x $((y + 60)) $((x + MENU_WIDTH)) $((y + 60))
    draw_text_block $((x + 20)) $((y + 20)) 100 2

    # Categories
    local categories=("Power" "Passives" "Actives" "Diodes")
    local cat_y=$((y + 80))

    for cat in "${categories[@]}"; do
        # Category box
        draw_box $((x + 10)) $cat_y $((x + MENU_WIDTH - 10)) $((cat_y + CATEGORY_HEIGHT - 10))

        # Category label (simulated with lines)
        draw_text_block $((x + 30)) $((cat_y + 25)) 120 2

        # Expansion indicator (arrow)
        draw_line $((x + MENU_WIDTH - 40)) $((cat_y + 30)) $((x + MENU_WIDTH - 25)) $((cat_y + 40)) | $LAMP
        draw_line $((x + MENU_WIDTH - 40)) $((cat_y + 50)) $((x + MENU_WIDTH - 25)) $((cat_y + 40)) | $LAMP

        cat_y=$((cat_y + CATEGORY_HEIGHT))
    done
}

# Draw category expanded view
draw_category_menu() {
    local category=$1
    local x=$((UI_REGION_LEFT + MENU_WIDTH + 20))
    local y=$UI_REGION_TOP

    # Submenu container
    draw_box $x $y $((x + MENU_WIDTH)) $UI_REGION_BOTTOM

    # Title
    draw_text_block $((x + 20)) $((y + 20)) 150 2
    draw_line $x $((y + 60)) $((x + MENU_WIDTH)) $((y + 60))

    # Get items for category
    local items=()
    case "$category" in
        "Power")
            items=("Battery" "Ground" "VCC" "AC Source")
            ;;
        "Passives")
            items=("Resistor" "Capacitor" "Inductor")
            ;;
        "Actives")
            items=("NPN Trans" "PNP Trans" "OpAmp" "MOSFET")
            ;;
        "Diodes")
            items=("Diode" "LED" "Zener" "Schottky")
            ;;
    esac

    # Draw items
    local item_y=$((y + 80))
    for item in "${items[@]}"; do
        draw_box $((x + 10)) $item_y $((x + MENU_WIDTH - 10)) $((item_y + ITEM_HEIGHT - 10))
        draw_text_block $((x + 30)) $((item_y + 20)) 100 2
        item_y=$((item_y + ITEM_HEIGHT))
    done
}

# Draw component at dedicated zone
draw_component() {
    local component=$1
    local x=$COMPONENT_ZONE_X
    local y=$COMPONENT_ZONE_Y

    case "$component" in
        "Battery")
            /opt/bin/electrical_symbols.sh battery $x $y 100
            ;;
        "Ground")
            /opt/bin/electrical_symbols.sh ground $x $y 80
            ;;
        "VCC")
            # VCC symbol (arrow pointing up)
            echo "pen line $x $((y-50)) $x $y" | $LAMP
            echo "pen line $((x-30)) $y $((x+30)) $y" | $LAMP
            echo "pen line $((x-20)) $((y+10)) $((x+20)) $((y+10))" | $LAMP
            ;;
        "AC Source")
            # AC source (circle with sine wave)
            echo "pen circle $x $y 40" | $LAMP
            ;;
        "Resistor")
            /opt/bin/electrical_symbols.sh resistor $x $y 100
            ;;
        "Capacitor")
            /opt/bin/electrical_symbols.sh capacitor $x $y 100
            ;;
        "Inductor")
            /opt/bin/electrical_symbols.sh inductor $x $y 100
            ;;
        "Diode")
            /opt/bin/electrical_symbols.sh diode $x $y 100
            ;;
        "LED")
            # LED (diode with arrows)
            /opt/bin/electrical_symbols.sh diode $x $y 100
            echo "pen line $((x+60)) $((y-40)) $((x+80)) $((y-60))" | $LAMP
            ;;
        "NPN Trans"|"PNP Trans")
            # Transistor (circle with lines)
            echo "pen circle $x $y 40" | $LAMP
            echo "pen line $((x-20)) $((y-30)) $((x-20)) $((y+30))" | $LAMP
            echo "pen line $((x-20)) $((y-15)) $((x+20)) $((y-30))" | $LAMP
            echo "pen line $((x-20)) $((y+15)) $((x+20)) $((y+30))" | $LAMP
            ;;
        "OpAmp")
            # Op-amp (triangle)
            echo "pen line $((x-40)) $((y-40)) $((x+40)) $y" | $LAMP
            echo "pen line $((x-40)) $((y+40)) $((x+40)) $y" | $LAMP
            echo "pen line $((x-40)) $((y-40)) $((x-40)) $((y+40))" | $LAMP
            ;;
        *)
            # Default: small circle
            echo "pen circle $x $y 30" | $LAMP
            ;;
    esac

    # Draw label indicator
    draw_text_block $((x - 50)) $((y + 60)) 100 1
}

# Clear UI region
clear_ui() {
    # Note: Can't actually erase in lamp, but in real usage user can manually clear
    # or we draw over with white (not possible with lamp)
    # This is a limitation - user needs to manually erase the UI when done
    echo "UI drawn - use eraser to clear when done" >&2
}

# Main state machine
handle_action() {
    local action=$1

    # Prevent concurrent execution
    if [ -f "$LOCK_FILE" ]; then
        echo "UI busy, please wait" >&2
        return
    fi
    touch "$LOCK_FILE"

    read_state

    case "$action" in
        "toggle_menu")
            if [ "$state" = "$STATE_CLOSED" ]; then
                draw_main_menu
                update_state "$STATE_MENU" "" ""
            else
                # Close menu (user must erase manually)
                update_state "$STATE_CLOSED" "" ""
            fi
            ;;

        "select_power")
            draw_category_menu "Power"
            update_state "$STATE_CATEGORY" "Power" ""
            ;;

        "select_passives")
            draw_category_menu "Passives"
            update_state "$STATE_CATEGORY" "Passives" ""
            ;;

        "select_actives")
            draw_category_menu "Actives"
            update_state "$STATE_CATEGORY" "Actives" ""
            ;;

        "select_diodes")
            draw_category_menu "Diodes"
            update_state "$STATE_CATEGORY" "Diodes" ""
            ;;

        "select_item_"*)
            # Extract item number
            local item_num=${action#select_item_}
            local component=""

            case "$category" in
                "Power")
                    case $item_num in
                        1) component="Battery" ;;
                        2) component="Ground" ;;
                        3) component="VCC" ;;
                        4) component="AC Source" ;;
                    esac
                    ;;
                "Passives")
                    case $item_num in
                        1) component="Resistor" ;;
                        2) component="Capacitor" ;;
                        3) component="Inductor" ;;
                    esac
                    ;;
                "Actives")
                    case $item_num in
                        1) component="NPN Trans" ;;
                        2) component="PNP Trans" ;;
                        3) component="OpAmp" ;;
                        4) component="MOSFET" ;;
                    esac
                    ;;
                "Diodes")
                    case $item_num in
                        1) component="Diode" ;;
                        2) component="LED" ;;
                        3) component="Zener" ;;
                        4) component="Schottky" ;;
                    esac
                    ;;
            esac

            if [ -n "$component" ]; then
                draw_component "$component"
                update_state "$STATE_SELECTED" "$category" "$component"
            fi
            ;;

        "back")
            if [ "$state" = "$STATE_CATEGORY" ]; then
                update_state "$STATE_MENU" "" ""
            fi
            ;;
    esac

    rm -f "$LOCK_FILE"
}

# Execute action
if [ $# -eq 0 ]; then
    echo "Usage: $0 {toggle_menu|select_power|select_passives|select_actives|select_diodes|select_item_N|back}"
    exit 1
fi

handle_action "$1"
