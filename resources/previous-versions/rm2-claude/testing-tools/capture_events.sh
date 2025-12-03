#!/bin/bash
# Capture Wacom events from RM2
# Run this on RM2 to record real pen input

OUTPUT="${1:-/tmp/pen_capture.txt}"
DURATION="${2:-10}"

echo "RM2 Event Capture Tool"
echo "======================"
echo ""
echo "Output: $OUTPUT"
echo "Duration: ${DURATION}s"
echo ""
echo "Instructions:"
echo "1. This script will capture pen events for ${DURATION} seconds"
echo "2. Write 'Hello' naturally on the screen"
echo "3. Events will be saved to $OUTPUT"
echo ""
echo "Starting in 3 seconds..."
sleep 1
echo "2..."
sleep 1
echo "1..."
sleep 1
echo "GO! Write 'Hello' now..."
echo ""

# Capture events using evtest (no timeout command needed)
evtest /dev/input/event1 > "$OUTPUT" 2>&1 &
EVTEST_PID=$!

# Wait for specified duration
sleep ${DURATION}

# Stop capture
kill $EVTEST_PID 2>/dev/null
wait $EVTEST_PID 2>/dev/null

echo ""
echo "Capture complete!"
echo "Events saved to: $OUTPUT"
echo ""
echo "To download:"
echo "  scp root@10.11.99.1:$OUTPUT ."
