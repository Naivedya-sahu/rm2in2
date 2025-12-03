#!/bin/bash
# pen_inject.sh - Simple, focused pen command injector
# Sends PEN_DOWN/PEN_MOVE/PEN_UP commands directly to RM2 injection hook
# Input: Text file with one command per line
# Output: Injected strokes on RM2 notebook

set -e

usage() {
    cat << 'EOF'
pen_inject.sh - Inject PEN commands into RM2

Usage:
    pen_inject.sh <commands.txt> <rm2_ip>

Arguments:
    commands.txt  - File with PEN_DOWN/PEN_MOVE/PEN_UP commands (one per line)
    rm2_ip        - RM2 device IP address (e.g., 192.168.1.137)

Input format:
    PEN_DOWN <x> <y>    - Lower pen at (x, y)
    PEN_MOVE <x> <y>    - Move pen to (x, y) while drawing
    PEN_UP              - Lift pen

Output:
    Injected strokes appear in Xochitl notebook after you tap the pen

Example:
    # Convert circuit.svg to commands
    python3 ./tools/svg2pen.py circuit.svg 2.5 cmds.txt
    
    # Inject the commands
    ./scripts/pen_inject.sh cmds.txt 192.168.1.137
    
    # When prompted, tap your pen on RM2 screen

Exit codes:
    0  - Success
    1  - Invalid arguments or RM2 unreachable
    2  - Server not running on RM2
EOF
}

# Validate arguments
if [ $# -ne 2 ]; then
    usage
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

# Count lines
TOTAL_COMMANDS=$(wc -l < "$COMMANDS_FILE")

if [ "$TOTAL_COMMANDS" -eq 0 ]; then
    echo "✗ Error: $COMMANDS_FILE is empty"
    exit 1
fi

# === Pre-injection checks ===

echo "==========================================="
echo "RM2 Pen Injection"
echo "==========================================="
echo ""
echo "Commands file: $COMMANDS_FILE"
echo "Target RM2:    $RM2_IP"
echo "Command count: $TOTAL_COMMANDS"
echo ""

# Check connectivity
echo "Checking RM2 connectivity..."
if ! ssh -o ConnectTimeout=5 root@$RM2_IP "true" 2>/dev/null; then
    echo "✗ Cannot reach RM2 at $RM2_IP"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check IP address: ping $RM2_IP"
    echo "  2. Check SSH: ssh root@$RM2_IP"
    echo "  3. Check network: RM2 and PC on same WiFi?"
    exit 1
fi
echo "✓ RM2 is reachable"

# Check server running
echo "Checking injection server..."
if ! ssh root@$RM2_IP "[ -p $FIFO_PATH ]" 2>/dev/null; then
    echo "✗ Server not running on RM2 or FIFO missing"
    echo ""
    echo "Start the server first:"
    echo "  ssh root@$RM2_IP '/opt/rm2-inject/server.sh start'"
    echo ""
    echo "Then verify:"
    echo "  ssh root@$RM2_IP '/opt/rm2-inject/server.sh status'"
    exit 2
fi
echo "✓ Server is running and FIFO exists"

# Check injection hook loaded
XOCHITL_PID=$(ssh root@$RM2_IP "pidof xochitl" 2>/dev/null || echo "")
if [ -z "$XOCHITL_PID" ]; then
    echo "✗ Xochitl not running"
    exit 2
fi

HOOK_LOADED=$(ssh root@$RM2_IP "grep -q inject_hook /proc/$XOCHITL_PID/maps 2>/dev/null && echo yes || echo no")
if [ "$HOOK_LOADED" != "yes" ]; then
    echo "⚠ Warning: Injection hook may not be loaded"
    echo "  Restart server: ssh root@$RM2_IP '/opt/rm2-inject/server.sh restart'"
fi

echo "✓ Xochitl is running"
echo ""

# === Injection summary ===

# Estimate injection time
RATE=100  # PEN commands per second (conservative)
SECONDS=$((TOTAL_COMMANDS / RATE))
MINUTES=$((SECONDS / 60))
SECONDS=$((SECONDS % 60))

if [ "$MINUTES" -gt 0 ]; then
    TIME_EST="${MINUTES}m ${SECONDS}s"
else
    TIME_EST="${SECONDS}s"
fi

echo "==========================================="
echo "Injection Summary"
echo "==========================================="
echo "Commands to send: $TOTAL_COMMANDS"
echo "Estimated time:  $TIME_EST (at $RATE cmds/sec)"
echo "Destination:     $RM2_IP:$FIFO_PATH"
echo ""

# === Pre-injection prompt ===

echo "IMPORTANT: Before proceeding:"
echo "  1. Have your RM2 ready with Xochitl open"
echo "  2. Open or create a new notebook page"
echo "  3. Position where you want the circuit to appear"
echo "  4. When script says 'TAP PEN', tap the pen on the screen"
echo ""

read -p "Ready to inject? (yes/no) " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""

# === Perform injection ===

echo "==========================================="
echo "INJECTING COMMANDS"
echo "==========================================="
echo ""
echo "▶ Sending PEN commands to RM2..."
echo "  (Xochitl is buffering commands)"
echo ""

# Count commands as we send them
sent=0
failed=0

while IFS= read -r cmd; do
    # Skip empty lines and comments
    [[ -z "$cmd" || "$cmd" =~ ^# ]] && continue
    
    # Validate command format (basic check)
    if ! [[ "$cmd" =~ ^PEN_(DOWN|MOVE|UP) ]]; then
        echo "  ⚠ Invalid command format: $cmd"
        ((failed++))
        continue
    fi
    
    # Send to RM2
    if echo "$cmd" | ssh root@$RM2_IP "cat > $FIFO_PATH 2>/dev/null" 2>/dev/null; then
        ((sent++))
    else
        ((failed++))
    fi
    
    # Progress indicator (every 100 commands)
    if [ $((sent % 100)) -eq 0 ]; then
        echo "  ⟳ $sent/$TOTAL_COMMANDS commands sent..."
    fi
    
done < "$COMMANDS_FILE"

echo ""
echo "==========================================="
echo "READY FOR INJECTION"
echo "==========================================="
echo ""
echo "✓ All $TOTAL_COMMANDS commands sent to RM2"
if [ "$failed" -gt 0 ]; then
    echo "  ($failed commands had errors—may affect quality)"
fi
echo ""
echo "Now for the critical step:"
echo ""
echo "  ╔════════════════════════════════════════╗"
echo "  ║  TAP YOUR PEN ON THE RM2 SCREEN NOW  ║"
echo "  ║  (Tap anywhere to trigger injection)  ║"
echo "  ╚════════════════════════════════════════╝"
echo ""

read -p "Tap pen on RM2, then press Enter here... "

echo ""
echo "Watch your RM2 screen as the circuit is drawn!"
echo ""

# Brief wait for injection to complete
sleep 2

echo "==========================================="
echo "INJECTION COMPLETE"
echo "==========================================="
echo ""
echo "✓ Your circuit should now be visible on RM2"
echo ""
echo "Next steps:"
echo "  - Annotate with pen to add notes"
echo "  - Take a screenshot (3-finger swipe)"
echo "  - Export notebook when done"
echo ""
echo "If something went wrong:"
echo "  1. Check RM2 logs:"
echo "     ssh root@$RM2_IP 'tail -20 /var/log/rm2-inject.log'"
echo "  2. Restart server:"
echo "     ssh root@$RM2_IP '/opt/rm2-inject/server.sh restart'"
echo "  3. Try injection again"
echo ""

exit 0
