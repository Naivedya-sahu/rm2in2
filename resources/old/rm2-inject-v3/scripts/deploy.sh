#!/bin/bash
# Deploy script - only copy files that RM2 can actually use

set -e

if [ -z "$1" ]; then
    echo "Usage: deploy.sh <rm2_ip>"
    exit 1
fi

RM2_IP="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"
TOOLS_DIR="$PROJECT_ROOT/tools"

echo "Deploying to RM2 at $RM2_IP..."

# Verify build exists
if [ ! -f "$BUILD_DIR/inject_hook.so" ]; then
    echo "Error: inject_hook.so not found. Run ./scripts/build.sh first"
    exit 1
fi

# Create target directory
ssh root@$RM2_IP "mkdir -p /opt/rm2-inject"

# Copy ONLY what RM2 needs (NO Python files)
echo "Copying inject_hook.so..."
scp "$BUILD_DIR/inject_hook.so" root@$RM2_IP:/opt/rm2-inject/

echo "Copying server.sh (bash server)..."
scp "$TOOLS_DIR/server.sh" root@$RM2_IP:/opt/rm2-inject/

# Set permissions
ssh root@$RM2_IP "chmod +x /opt/rm2-inject/server.sh"

# Clean up any Python files that shouldn't be there
echo "Cleaning up Python files on RM2 (not supported)..."
ssh root@$RM2_IP "rm -f /opt/rm2-inject/*.py" 2>/dev/null || true

echo ""
echo "Deployment complete!"
echo ""
echo "Files on RM2:"
ssh root@$RM2_IP "ls -lh /opt/rm2-inject/"
echo ""
echo "Next steps:"
echo "1. Start server: ssh root@$RM2_IP '/opt/rm2-inject/server.sh start'"
echo "2. Run console: ./scripts/console.sh $RM2_IP"
