#!/bin/bash
# inject_pen_commands.sh - Inject PEN_* format commands to RM2
# Works with output from svg2inject_medium.py and svg2inject_pro.py

set -e

if [ $# -lt 2 ]; then
    echo "Usage: inject_pen_commands.sh <commands.txt> <rm2_ip>"
    echo ""
    echo "Injects PEN_DOWN/PEN_MOVE/PEN_UP commands directly to RM2"
    echo ""
    echo "Examples:"
    echo "  inject_pen_commands.sh test.txt 10.11.99.1"
    echo ""
    exit 1
fi

COMMANDS_FILE="$1"
RM2_IP="$2"
FIFO_PATH="/tmp/lamp_inject"

if [ ! -f "$COMMANDS_FILE" ]; then
    echo "Error: File not found: $COMMANDS_FILE"
    exit 1
fi

echo "========================================"
echo "RM2 PEN Command Injection"
echo "========================================"
echo "File:      $COMMANDS_FILE"
echo "Target:    $RM2_IP"
echo ""

# Count commands
TOTAL_LINES=$(wc -l < "$COMMANDS_FILE")
echo "Commands:  $TOTAL_LINES"
echo ""

# Check server status
echo "Checking RM2 server status..."
if ! ssh root@$RM2_IP "[ -p $FIFO_PATH ]" 2>/dev/null; then
    echo "✗ Server not running or FIFO missing"
    echo ""
    echo "Start server first:"
    echo "  ssh root@$RM2_IP '/opt/rm2-inject/server.sh start'"
    exit 1
fi

echo "✓ Server is running"
echo ""

# Estimate time
RATE=100  # events per second
DURATION=$((TOTAL_LINES / RATE))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo "Estimated time: ${MINUTES}m ${SECONDS}s (at $RATE events/sec)"
echo ""

read -p "Ready to inject? Press Enter to continue, Ctrl+C to cancel..."
echo ""

echo "=============================================="
echo "IMPORTANT: Tap pen on RM2 screen NOW"
echo "=============================================="
echo ""
echo "Sending commands..."

# Send all commands directly - they're already in PEN_* format!
cat "$COMMANDS_FILE" | ssh root@$RM2_IP "while IFS= read -r cmd; do echo \"\$cmd\" > $FIFO_PATH; done"

echo ""
echo "=============================================="
echo "✓ Injection complete!"
echo "=============================================="
echo "Sent $TOTAL_LINES commands"
echo ""
