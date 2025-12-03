#!/bin/bash
# Send PEN commands to RM2 device

set -e

COMMAND_FILE="$1"
RM2_IP="${2:-10.11.99.1}"
FIFO_PATH="/tmp/rm2_inject"
INSTALL_DIR="/opt/rm2in2"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$COMMAND_FILE" ]; then
    echo "Usage: $0 <command_file> [rm2_ip]"
    echo ""
    echo "Example:"
    echo "  $0 test.txt"
    echo "  $0 test.txt 10.11.99.1"
    echo ""
    echo "Send coordinate test patterns:"
    echo "  $0 test-output/corners_A_Direct.txt"
    exit 1
fi

if [ ! -f "$COMMAND_FILE" ]; then
    echo -e "${RED}ERROR:${NC} File not found: $COMMAND_FILE"
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
    echo -e "${YELLOW}WARNING:${NC} File doesn't appear to contain PEN commands"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Test SSH connectivity
echo "Testing connection to RM2..."
if ! ssh -o ConnectTimeout=5 root@$RM2_IP "echo Connected" > /dev/null 2>&1; then
    echo -e "${RED}ERROR:${NC} Cannot connect to RM2 at $RM2_IP"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check IP address"
    echo "  - Check USB/WiFi connection"
    echo "  - Verify SSH access: ssh root@$RM2_IP"
    exit 1
fi
echo -e "${GREEN}✓${NC} Connected"

# Check if injection hook is running
echo "Checking if injection hook is running..."
if ssh root@$RM2_IP "[ -e $FIFO_PATH ]"; then
    echo -e "${GREEN}✓${NC} FIFO exists - hook is running"
else
    echo -e "${RED}ERROR:${NC} FIFO not found at $FIFO_PATH"
    echo ""
    echo "The injection service is not running."
    echo ""
    echo "Quick fix (from PC):"
    echo "  ${GREEN}make start${NC}"
    echo ""
    echo "Or manually on RM2:"
    echo "  ssh root@$RM2_IP '$INSTALL_DIR/server.sh start'"
    echo ""
    echo "Or check status:"
    echo "  ${GREEN}make status${NC}"
    exit 1
fi

# Count commands
total_lines=$(wc -l < "$COMMAND_FILE")
pen_commands=$(grep -c "^PEN_" "$COMMAND_FILE" || true)

# Extract transform type from filename if present
transform=""
if [[ "$COMMAND_FILE" =~ _([A-H]_[A-Za-z]+)\.txt$ ]]; then
    transform="${BASH_REMATCH[1]}"
fi

echo ""
echo "File stats:"
echo "  Total lines:   $total_lines"
echo "  PEN commands:  $pen_commands"
if [ -n "$transform" ]; then
    echo "  Transform:     $transform"
fi
echo ""

# Send commands
echo "Sending commands to RM2..."
cat "$COMMAND_FILE" | ssh root@$RM2_IP "cat > $FIFO_PATH"

echo ""
echo -e "${GREEN}✓ Commands sent successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Open the notes app on RM2 if not already open"
echo "  2. Tap anywhere on the screen to trigger drawing"
echo "  3. Observe the result"
echo ""
if [ -n "$transform" ]; then
    echo "Testing Transform: $transform"
    echo ""
    echo "Expected results for different patterns:"
    echo "  - corners: Four dots near screen corners"
    echo "  - cross:   Centered + shape (horizontal and vertical lines)"
    echo "  - grid:    3x3 evenly spaced dots"
    echo "  - circle:  Perfect circle (not elliptical)"
    echo ""
    echo "If this looks correct, this is the right transformation!"
    echo "If not, try the next transform variant."
    echo ""
fi
echo "To view logs:"
echo "  ${GREEN}make logs${NC}"
echo ""
