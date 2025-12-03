#!/bin/bash
# Send PEN commands to RM2 - Simple reliable method
# Usage: ./send.sh <commands.txt> [rm2_ip]

set -e

if [ $# -lt 1 ]; then
    cat << 'EOF'
Send PEN commands to RM2

Usage: ./send.sh <commands.txt> [rm2_ip]

Arguments:
  commands.txt  File with PEN commands
  rm2_ip        RM2 IP address (default: 10.11.99.1)

Example:
  ./send.sh commands.txt
  ./send.sh commands.txt 10.11.99.1

Method: Transfers file via SCP, then injects locally on RM2
EOF
    exit 1
fi

COMMANDS="$1"
RM2_IP="${2:-10.11.99.1}"
FIFO="/tmp/rm2_inject"
TEMP_FILE="/tmp/rm2_commands.txt"

# Check file exists
if [ ! -f "$COMMANDS" ]; then
    echo "Error: File not found: $COMMANDS"
    exit 1
fi

# Count commands
TOTAL=$(grep -c "^PEN_" "$COMMANDS" 2>/dev/null || echo 0)
if [ "$TOTAL" -eq 0 ]; then
    echo "Error: No PEN commands found in $COMMANDS"
    exit 1
fi

echo "Sending $TOTAL commands to $RM2_IP..."

# Test connection
if ! ping -c 1 -W 2 "$RM2_IP" > /dev/null 2>&1; then
    echo "Error: Cannot reach $RM2_IP"
    exit 1
fi

# Check SSH
if ! ssh -o ConnectTimeout=3 root@$RM2_IP "true" 2>/dev/null; then
    echo "Error: SSH connection failed"
    exit 1
fi

# Check server status
echo -n "Checking server... "
if ! ssh root@$RM2_IP "[ -p $FIFO ]" 2>/dev/null; then
    echo "not running"
    echo ""
    echo "Start server first:"
    echo "  ssh root@$RM2_IP '/opt/server start'"
    exit 1
fi
echo "OK"

# Transfer file
echo -n "Transferring file... "
if ! scp -q "$COMMANDS" root@$RM2_IP:$TEMP_FILE 2>/dev/null; then
    echo "failed"
    echo "Error: File transfer failed"
    exit 1
fi
echo "done"

# Inject commands
echo -n "Injecting commands... "
if ssh root@$RM2_IP "cat $TEMP_FILE > $FIFO && rm $TEMP_FILE" 2>/dev/null; then
    echo "done"
    echo ""
    echo "✓ Successfully sent $TOTAL commands"
    echo ""
    echo "Tap pen on RM2 screen to inject drawing"
else
    echo "failed"
    echo "Error: Command injection failed"
    exit 1
fi
