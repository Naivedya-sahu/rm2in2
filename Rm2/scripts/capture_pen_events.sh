#!/bin/bash
# Capture real pen events from Wacom digitizer on RM2
# Run this ON the Remarkable 2 device

set -e

OUTPUT_FILE="${1:-/tmp/pen_capture.txt}"
DEVICE="/dev/input/event1"

echo "==================================="
echo "RM2 Pen Event Capture Tool"
echo "==================================="
echo ""
echo "This will capture raw pen events from the Wacom digitizer."
echo "Output: $OUTPUT_FILE"
echo ""
echo "Instructions:"
echo "  1. Draw the following pattern on screen:"
echo "     - Touch top-left corner (mark '1')"
echo "     - Touch top-right corner (mark '2')"
echo "     - Touch bottom-left corner (mark '3')"
echo "     - Touch bottom-right corner (mark '4')"
echo "     - Touch center (mark 'C')"
echo ""
echo "  2. Press Ctrl+C when done"
echo ""
echo "Starting capture in 3 seconds..."
sleep 3

# Check if evtest is available
if ! command -v evtest &> /dev/null; then
    echo "ERROR: evtest not found"
    echo "Install with: opkg install evtest"
    exit 1
fi

# Capture events
echo "Capturing events from $DEVICE ..."
evtest "$DEVICE" | tee "$OUTPUT_FILE"
