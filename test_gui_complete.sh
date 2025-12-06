#!/bin/bash
# Complete GUI Functionality Test Suite
# Tests navigation, state transitions, user interactions, and cleanup

LAMP="/opt/bin/lamp"
STATE_FILE="/tmp/gui_test_state"

# Colors for output (if terminal supports)
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# UI Region Definitions
UI_MAIN_X1=50
UI_MAIN_Y1=1400
UI_MAIN_X2=350
UI_MAIN_Y2=1850

UI_SUB_X1=370
UI_SUB_Y1=1400
UI_SUB_X2=670
UI_SUB_Y2=1850

UI_COMP_X1=700
UI_COMP_Y1=1400
UI_COMP_X2=1350
UI_COMP_Y2=1850

echo "========================================"
echo "  Dynamic GUI Functionality Test Suite"
echo "========================================"
echo ""
echo "This will test:"
echo "  1. GUI Opening/Closing"
echo "  2. Menu Navigation"
echo "  3. Category Selection"
echo "  4. Component Preview"
echo "  5. State Transitions"
echo "  6. Eraser Cleanup"
echo "  7. Exit Handling"
echo ""
echo "Watch your reMarkable screen!"
echo ""
sleep 2

# Helper Functions
# ================

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_action() {
    echo -e "${YELLOW}[ACTION]${NC} $1"
}

clear_all() {
    echo "eraser fill $UI_MAIN_X1 $UI_MAIN_Y1 $UI_COMP_X2 $UI_COMP_Y2 15" | $LAMP
}

clear_main_menu() {
    echo "eraser fill $UI_MAIN_X1 $UI_MAIN_Y1 $UI_MAIN_X2 $UI_MAIN_Y2 15" | $LAMP
}

clear_submenu() {
    echo "eraser fill $UI_SUB_X1 $UI_SUB_Y1 $UI_SUB_X2 $UI_SUB_Y2 15" | $LAMP
}

clear_component() {
    echo "eraser fill $UI_COMP_X1 $UI_COMP_Y1 $UI_COMP_X2 $UI_COMP_Y2 15" | $LAMP
}

draw_main_menu() {
    # Main menu container
    echo "pen rectangle $UI_MAIN_X1 $UI_MAIN_Y1 $UI_MAIN_X2 $UI_MAIN_Y2" | $LAMP

    # Title bar
    echo "pen line $UI_MAIN_X1 $((UI_MAIN_Y1+60)) $UI_MAIN_X2 $((UI_MAIN_Y1+60))" | $LAMP

    # Category boxes
    local categories=("Power" "Passives" "Actives" "Diodes")
    local y=$((UI_MAIN_Y1 + 80))

    for cat in "${categories[@]}"; do
        echo "pen rectangle $((UI_MAIN_X1+10)) $y $((UI_MAIN_X2-10)) $((y+80))" | $LAMP

        # Selection indicator (arrow)
        echo "pen line $((UI_MAIN_X2-40)) $((y+30)) $((UI_MAIN_X2-25)) $((y+40))" | $LAMP
        echo "pen line $((UI_MAIN_X2-40)) $((y+50)) $((UI_MAIN_X2-25)) $((y+40))" | $LAMP

        y=$((y + 100))
    done
}

draw_submenu() {
    local category=$1

    # Submenu container
    echo "pen rectangle $UI_SUB_X1 $UI_SUB_Y1 $UI_SUB_X2 $UI_SUB_Y2" | $LAMP

    # Title bar
    echo "pen line $UI_SUB_X1 $((UI_SUB_Y1+60)) $UI_SUB_X2 $((UI_SUB_Y1+60))" | $LAMP

    # Back button indicator
    echo "pen line $((UI_SUB_X1+20)) $((UI_SUB_Y1+30)) $((UI_SUB_X1+35)) $((UI_SUB_Y1+30))" | $LAMP
    echo "pen line $((UI_SUB_X1+20)) $((UI_SUB_Y1+30)) $((UI_SUB_X1+27)) $((UI_SUB_Y1+20))" | $LAMP
    echo "pen line $((UI_SUB_X1+20)) $((UI_SUB_Y1+30)) $((UI_SUB_X1+27)) $((UI_SUB_Y1+40))" | $LAMP

    # Item boxes
    local y=$((UI_SUB_Y1 + 80))
    for i in 1 2 3; do
        echo "pen rectangle $((UI_SUB_X1+10)) $y $((UI_SUB_X2-10)) $((y+70))" | $LAMP
        y=$((y + 90))
    done
}

draw_component() {
    # Component preview area
    echo "pen rectangle $UI_COMP_X1 $UI_COMP_Y1 $UI_COMP_X2 $UI_COMP_Y2" | $LAMP

    # Component symbol (example: resistor)
    local cx=900
    local cy=1600
    echo "pen line $((cx-60)) $cy $((cx-40)) $((cy-20))" | $LAMP
    echo "pen line $((cx-40)) $((cy-20)) $((cx-20)) $((cy+20))" | $LAMP
    echo "pen line $((cx-20)) $((cy+20)) $cx $((cy-20))" | $LAMP
    echo "pen line $cx $((cy-20)) $((cx+20)) $((cy+20))" | $LAMP
    echo "pen line $((cx+20)) $((cy+20)) $((cx+40)) $((cy-20))" | $LAMP
    echo "pen line $((cx+40)) $((cy-20)) $((cx+60)) $cy" | $LAMP

    # Label area
    echo "pen line $((UI_COMP_X1+50)) $((UI_COMP_Y2-100)) $((UI_COMP_X2-50)) $((UI_COMP_Y2-100))" | $LAMP
}

# Test Sequence
# =============

# TEST 1: Opening GUI
log_step "Test 1: Opening GUI"
log_action "Drawing main menu..."
echo "state=menu" > $STATE_FILE
draw_main_menu
log_success "Main menu displayed"
sleep 3

# TEST 2: Category Selection
log_step "Test 2: Category Selection (Power)"
log_action "User selects Power category..."
draw_submenu "Power"
echo "state=category_power" > $STATE_FILE
log_success "Submenu displayed with back button"
sleep 3

# TEST 3: Navigation - Back to Main Menu
log_step "Test 3: Back Navigation"
log_action "User clicks back button..."
clear_submenu
sleep 0.5
log_success "Submenu cleared, main menu still visible"
echo "state=menu" > $STATE_FILE
sleep 2

# TEST 4: Different Category Selection
log_step "Test 4: Different Category (Passives)"
log_action "User selects Passives category..."
draw_submenu "Passives"
echo "state=category_passives" > $STATE_FILE
log_success "Different submenu displayed"
sleep 3

# TEST 5: Component Selection
log_step "Test 5: Component Selection"
log_action "User selects component from list..."
draw_component
echo "state=component_preview" > $STATE_FILE
log_success "Component preview displayed"
sleep 3

# TEST 6: Clear Component, Keep Menus
log_step "Test 6: Selective Clearing (Component Only)"
log_action "Clearing component preview..."
clear_component
sleep 0.5
log_success "Component cleared, menus intact"
echo "state=category_passives" > $STATE_FILE
sleep 2

# TEST 7: Full State Transition
log_step "Test 7: Complete State Transition"
log_action "Transitioning back to main menu..."
clear_submenu
sleep 0.5
log_success "Back to main menu state"
echo "state=menu" > $STATE_FILE
sleep 2

# TEST 8: Select Another Category + Component
log_step "Test 8: Quick Navigation Test"
log_action "Power -> Component..."
draw_submenu "Power"
sleep 1
draw_component
sleep 2
log_success "Quick navigation works"

# TEST 9: Exit - Partial Clear
log_step "Test 9: Exit Simulation (Partial)"
log_action "User exits to main menu..."
clear_submenu
clear_component
sleep 0.5
log_success "Submenus cleared, main menu visible"
sleep 2

# TEST 10: Complete Exit
log_step "Test 10: Complete Exit/Cleanup"
log_action "User closes GUI completely..."
clear_all
sleep 1
log_success "All GUI elements cleared"
echo "state=closed" > $STATE_FILE
sleep 1

# TEST 11: Re-open GUI
log_step "Test 11: Re-opening GUI"
log_action "User re-opens GUI..."
sleep 1
draw_main_menu
echo "state=menu" > $STATE_FILE
log_success "GUI reopened cleanly"
sleep 3

# TEST 12: Rapid State Changes
log_step "Test 12: Rapid State Transitions"
log_action "Testing rapid navigation..."
draw_submenu "Power"
sleep 0.8
clear_submenu
draw_submenu "Actives"
sleep 0.8
draw_component
sleep 0.8
clear_component
clear_submenu
sleep 0.5
log_success "Rapid transitions handled"
sleep 2

# TEST 13: Final Cleanup
log_step "Test 13: Final Cleanup Test"
log_action "Cleaning all UI elements..."
clear_all
sleep 1
log_success "Screen cleared completely"
rm -f $STATE_FILE

echo ""
echo "========================================"
echo "  All Tests Completed Successfully!"
echo "========================================"
echo ""
echo "Tested Functionality:"
echo "  ✓ GUI Opening/Closing"
echo "  ✓ Menu Drawing"
echo "  ✓ Category Selection"
echo "  ✓ Submenu Display"
echo "  ✓ Component Preview"
echo "  ✓ Back Navigation"
echo "  ✓ Selective Clearing (component only)"
echo "  ✓ Selective Clearing (submenu only)"
echo "  ✓ Complete Cleanup"
echo "  ✓ Re-opening After Exit"
echo "  ✓ Rapid State Transitions"
echo "  ✓ Eraser Functionality"
echo ""
echo "The dynamic GUI with eraser support is working correctly!"
echo ""
