#!/bin/bash
# Quick test script for lamp eraser functionality
# Run this on your reMarkable device after deploying lamp

LAMP="/opt/bin/lamp"

echo "=== Testing lamp with Eraser Support ==="
echo ""

# Check if lamp exists
if [ ! -f "$LAMP" ]; then
    echo "❌ lamp not found at $LAMP"
    echo "Please deploy lamp first:"
    echo "  scp resources/repos/rmkit/src/build/lamp root@10.11.99.1:/opt/bin/"
    exit 1
fi

echo "✓ lamp found at $LAMP"
echo ""

# Test 1: Basic pen drawing
echo "Test 1: Drawing a rectangle..."
echo "pen rectangle 200 200 600 600" | $LAMP
echo "✓ Rectangle drawn at (200, 200) to (600, 600)"
sleep 2

# Test 2: Eraser line
echo ""
echo "Test 2: Erasing with a line..."
echo "eraser line 200 400 600 400" | $LAMP
echo "✓ Horizontal line erased through rectangle"
sleep 2

# Test 3: Draw another shape
echo ""
echo "Test 3: Drawing a circle..."
echo "pen circle 800 800 150" | $LAMP
echo "✓ Circle drawn at (800, 800) radius 150"
sleep 2

# Test 4: Eraser fill (clear area)
echo ""
echo "Test 4: Clearing with eraser fill..."
echo "eraser fill 650 650 950 950 15" | $LAMP
echo "✓ Area cleared around circle"
sleep 2

# Test 5: Draw and clear UI region
echo ""
echo "Test 5: Testing UI region clear (bottom of screen)..."
echo "pen rectangle 50 1400 350 1850" | $LAMP
echo "✓ UI rectangle drawn at bottom"
sleep 2

echo ""
echo "Clearing UI region..."
echo "eraser fill 50 1400 350 1850 15" | $LAMP
echo "✓ UI region cleared"
sleep 1

# Test 6: Dynamic redraw
echo ""
echo "Test 6: Dynamic UI - draw, erase, redraw..."
echo "pen rectangle 50 1400 350 1850" | $LAMP
sleep 1
echo "eraser fill 50 1400 350 1850 15" | $LAMP
sleep 0.5
echo "pen rectangle 370 1400 670 1850" | $LAMP
echo "✓ UI transition complete"

echo ""
echo "=== All Tests Complete ==="
echo ""
echo "Eraser commands tested:"
echo "  ✓ eraser line"
echo "  ✓ eraser fill"
echo "  ✓ Dynamic UI clearing"
echo ""
echo "Check your reMarkable screen for the results!"
