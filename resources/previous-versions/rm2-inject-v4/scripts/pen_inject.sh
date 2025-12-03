#!/bin/bash
# pen_inject.sh - Inject PEN_DOWN/MOVE/UP commands to RM2
# Sends commands from file to RM2 injection server

set -e

if [ $# -ne 2 ]; then
    cat << 'EOF'
pen_inject.sh - Inject PEN commands into RM2

Usage:
    pen_inject.sh <commands.txt> <rm2_ip>

Arguments:
    commands.txt  - File with PEN_DOWN/MOVE/UP commands
    rm2_ip        - RM2 IP address (e.g., 192.168.1.137)

Input format:
    PEN_DOWN <x> <y>    - Lower pen at (x, y)
    PEN_MOVE <x> <y>    - Move pen while drawing
    PEN_UP              - Lift pen

Example:
    ./pen_inject.sh commands.txt 192.168.1.137

EOF
    exit 1
fi

COMMANDS_FILE="$1"
RM2_IP="$2"
FIFO_PATH="/tmp/lamp_inject"

# Validate command file exists
if [ ! -f "$COMMANDS_FILE" ]; then
    echo "✗ Error: File not found: $COMMANDS_FILE"
    exit 1
fi

# Count commands
TOTAL_COMMANDS=$(wc -l < "$COMMANDS_FILE")

if [ "$TOTAL_COMMANDS" -eq 0 ]; then
    echo "✗ Error: $COMMANDS_FILE is empty"
    exit 1
fi

echo "╔════════════════════════════════════════════════════════╗"
echo "║  RM2 Pen Injection"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Commands file: $COMMANDS_FILE"
echo "Target RM2:    $RM2_IP"
echo "Command count: $TOTAL_COMMANDS"
echo ""

# Check connectivity
echo "Checking RM2 connectivity..."
if ! ssh -o ConnectTimeout=5 root@$RM2_IP "true" 2>/dev/null; then
    echo "✗ Cannot reach RM2 at $RM2_IP"
    exit 1
fi
echo "✓ RM2 is reachable"

# Check server running
echo "Checking injection server..."
if ! ssh root@$RM2_IP "[ -p $FIFO_PATH ]" 2>/dev/null; then
    echo "✗ Server not running or FIFO missing"
    echo ""
    echo "Start the server first:"
    echo "  ssh root@$RM2_IP '/opt/rm2-inject/server.sh start'"
    exit 1
fi
echo "✓ Server is running"
echo ""

# Estimate time
RATE=100
SECONDS=$((TOTAL_COMMANDS / RATE))
MINUTES=$((SECONDS / 60))
SECONDS=$((SECONDS % 60))

echo "Injection summary:"
echo "  Commands:      $TOTAL_COMMANDS"
echo "  Estimated time: ${MINUTES}m ${SECONDS}s"
echo ""

# Prompt for confirmation
read -p "Ready to inject? (yes/no) " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Sending Commands to RM2"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Send all commands
sent=0
while IFS= read -r cmd; do
    # Skip empty lines and comments
    [[ -z "$cmd" || "$cmd" =~ ^# ]] && continue
    
    # Send command
    echo "$cmd" | ssh root@$RM2_IP "cat > $FIFO_PATH 2>/dev/null" 2>/dev/null || true
    ((sent++))
    
    # Progress indicator
    if [ $((sent % 100)) -eq 0 ]; then
        echo "  ⟳ $sent/$TOTAL_COMMANDS commands sent..."
    fi
done < "$COMMANDS_FILE"

echo ""
echo "✓ All $TOTAL_COMMANDS commands sent to RM2"
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Ready for Injection"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "  TAP YOUR PEN ON THE RM2 SCREEN NOW"
echo "  (Tap anywhere to trigger injection)"
echo ""

read -p "Tap pen on RM2, then press Enter... "

echo ""
echo "Watch your RM2 screen as the circuit is drawn!"
echo ""
echo "✓ Injection complete"
echo ""
