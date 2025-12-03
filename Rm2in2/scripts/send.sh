#!/bin/bash
# Send PEN commands to RM2 device

set -e

COMMAND_FILE="$1"
RM2_IP="${2:-10.11.99.1}"
FIFO_PATH="/tmp/rm2_inject"

if [ -z "$COMMAND_FILE" ]; then
    echo "Usage: $0 <command_file> [rm2_ip]"
    echo ""
    echo "Example:"
    echo "  $0 test.txt"
    echo "  $0 test.txt 10.11.99.1"
    exit 1
fi

if [ ! -f "$COMMAND_FILE" ]; then
    echo "ERROR: File not found: $COMMAND_FILE"
    exit 1
fi

echo "==================================="
echo "RM2 Command Sender"
echo "==================================="
echo ""
echo "Command file: $COMMAND_FILE"
echo "RM2 IP:       $RM2_IP"
echo "FIFO path:    $FIFO_PATH"
echo ""

# Check if file contains PEN commands
if ! grep -q "PEN_" "$COMMAND_FILE"; then
    echo "WARNING: File doesn't appear to contain PEN commands"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Test SSH connectivity
echo "Testing connection to RM2..."
if ! ssh -o ConnectTimeout=5 root@$RM2_IP "echo Connected" > /dev/null 2>&1; then
    echo "ERROR: Cannot connect to RM2 at $RM2_IP"
    echo "  - Check IP address"
    echo "  - Check USB/WiFi connection"
    echo "  - Check SSH access"
    exit 1
fi
echo "✓ Connected"

# Check if injection hook is running
echo "Checking if injection hook is running..."
if ssh root@$RM2_IP "[ -e $FIFO_PATH ]"; then
    echo "✓ FIFO exists - hook is running"
else
    echo "ERROR: FIFO not found at $FIFO_PATH"
    echo ""
    echo "The injection hook is not running. To start it:"
    echo "  1. SSH to RM2: ssh root@$RM2_IP"
    echo "  2. Stop xochitl: systemctl stop xochitl"
    echo "  3. Start with hook: LD_PRELOAD=/opt/rm2in2/inject.so /usr/bin/xochitl &"
    exit 1
fi

# Count commands
total_lines=$(wc -l < "$COMMAND_FILE")
pen_commands=$(grep -c "^PEN_" "$COMMAND_FILE" || true)

echo ""
echo "File stats:"
echo "  Total lines:   $total_lines"
echo "  PEN commands:  $pen_commands"
echo ""

# Send commands
echo "Sending commands to RM2..."
cat "$COMMAND_FILE" | ssh root@$RM2_IP "cat > $FIFO_PATH"

echo ""
echo "✓ Commands sent successfully!"
echo ""
echo "Check your RM2 screen to see the result."
echo "Open the notes app and tap the screen to trigger drawing."
