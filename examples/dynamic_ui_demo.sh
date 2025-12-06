#!/bin/bash
# Dynamic UI Demo - Shows eraser capabilities for menu transitions
# Run on reMarkable device

LAMP="/opt/bin/lamp"

echo "=== Dynamic UI Demo ==="
echo "This demo shows how eraser enables dynamic menus"
echo ""

# UI region coordinates (bottom of screen)
UI_X1=50
UI_Y1=1400
UI_X2=1350
UI_Y2=1850

clear_ui() {
    echo "eraser fill $UI_X1 $UI_Y1 $UI_X2 $UI_Y2 15" | $LAMP
}

# State 1: Main Menu
echo "Drawing main menu..."
echo "pen rectangle 50 1400 350 1850" | $LAMP
echo "pen rectangle 70 1480 330 1560" | $LAMP  # Category 1
echo "pen rectangle 70 1600 330 1680" | $LAMP  # Category 2
echo "pen rectangle 70 1720 330 1800" | $LAMP  # Category 3
sleep 2

# State 2: Category selected - show submenu
echo ""
echo "Showing submenu (notice: main menu stays)..."
echo "pen rectangle 370 1400 670 1850" | $LAMP
echo "pen rectangle 390 1480 650 1550" | $LAMP  # Item 1
echo "pen rectangle 390 1590 650 1660" | $LAMP  # Item 2
echo "pen rectangle 390 1700 650 1770" | $LAMP  # Item 3
sleep 2

# State 3: Clear submenu, show component
echo ""
echo "Clearing submenu area..."
echo "eraser fill 370 1400 670 1850 15" | $LAMP
sleep 1

echo "Showing component preview..."
echo "pen circle 900 1600 80" | $LAMP
sleep 2

# State 4: Back to main menu only
echo ""
echo "Clearing component area..."
echo "eraser fill 700 1400 1350 1850 15" | $LAMP
sleep 1

# State 5: Complete transition - new menu
echo ""
echo "Transitioning to different menu..."
clear_ui
sleep 0.5

echo "pen rectangle 50 1400 650 1850" | $LAMP
echo "pen rectangle 70 1480 630 1700" | $LAMP
sleep 2

# Final: Clean up
echo ""
echo "Cleaning up..."
clear_ui

echo ""
echo "=== Demo Complete ==="
echo ""
echo "This showed:"
echo "  ✓ Menu drawing"
echo "  ✓ Submenu expansion"
echo "  ✓ Selective clearing (submenu only)"
echo "  ✓ Component preview"
echo "  ✓ Full UI transition"
echo "  ✓ Complete cleanup"
