#!/bin/bash
# Deploy script for RM2 injection system v4
# Deploys compiled hook and server to RM2 device

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"
TOOLS_DIR="$PROJECT_ROOT/tools"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo "Usage: deploy.sh <rm2_ip>"
    echo ""
    echo "Arguments:"
    echo "  rm2_ip  - IP address of RM2 device (e.g., 192.168.1.137)"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh 192.168.1.137"
    echo "  ./deploy.sh 10.0.0.5"
    exit 1
}

if [ -z "$1" ]; then
    usage
fi

RM2_IP="$1"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Deploying to RM2 at $RM2_IP"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Verify hook is built
echo "Checking build artifacts..."
if [ ! -f "$BUILD_DIR/inject_hook.so" ]; then
    echo -e "${RED}✗ Error: inject_hook.so not found${NC}"
    echo ""
    echo "Build the hook first:"
    echo "  ./scripts/build.sh"
    exit 1
fi

SIZE=$(du -h "$BUILD_DIR/inject_hook.so" | cut -f1)
echo -e "${GREEN}✓ Hook library ready ($SIZE)${NC}"

if [ ! -f "$TOOLS_DIR/server.sh" ]; then
    echo -e "${RED}✗ Error: server.sh not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Server script ready${NC}"
echo ""

# Check SSH connectivity
echo "Checking SSH connectivity to $RM2_IP..."
if ! ssh -o ConnectTimeout=5 root@$RM2_IP "true" 2>/dev/null; then
    echo -e "${RED}✗ Cannot reach $RM2_IP via SSH${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check IP address: ping $RM2_IP"
    echo "  2. Verify SSH is working: ssh root@$RM2_IP"
    echo "  3. Set up SSH key (no password):"
    echo "     ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa"
    echo "     ssh-copy-id -i ~/.ssh/id_rsa root@$RM2_IP"
    exit 1
fi
echo -e "${GREEN}✓ SSH connectivity verified${NC}"
echo ""

# Create target directory
echo "Setting up target directory on RM2..."
if ! ssh root@$RM2_IP "mkdir -p /opt/rm2-inject && chmod 755 /opt/rm2-inject" 2>/dev/null; then
    echo -e "${RED}✗ Failed to create directory on RM2${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Created /opt/rm2-inject${NC}"
echo ""

# Deploy hook library
echo "Deploying hook library..."
if scp "$BUILD_DIR/inject_hook.so" root@$RM2_IP:/opt/rm2-inject/ 2>/dev/null; then
    echo -e "${GREEN}✓ Deployed inject_hook.so${NC}"
else
    echo -e "${RED}✗ Failed to deploy hook library${NC}"
    exit 1
fi

# Deploy server script
echo "Deploying server script..."
if scp "$TOOLS_DIR/server.sh" root@$RM2_IP:/opt/rm2-inject/ 2>/dev/null; then
    echo -e "${GREEN}✓ Deployed server.sh${NC}"
else
    echo -e "${RED}✗ Failed to deploy server script${NC}"
    exit 1
fi

# Set permissions
echo "Setting permissions..."
if ! ssh root@$RM2_IP "chmod +x /opt/rm2-inject/server.sh /opt/rm2-inject/inject_hook.so" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Failed to set execute permissions (may not be critical)${NC}"
fi
echo -e "${GREEN}✓ Permissions set${NC}"
echo ""

# Verify deployment
echo "Verifying deployment..."
HOOK_STATUS=$(ssh root@$RM2_IP "[ -f /opt/rm2-inject/inject_hook.so ] && echo yes || echo no" 2>/dev/null)
SERVER_STATUS=$(ssh root@$RM2_IP "[ -f /opt/rm2-inject/server.sh ] && echo yes || echo no" 2>/dev/null)

if [ "$HOOK_STATUS" = "yes" ] && [ "$SERVER_STATUS" = "yes" ]; then
    echo -e "${GREEN}✓ Deployment verified${NC}"
else
    echo -e "${RED}✗ Deployment verification failed${NC}"
    exit 1
fi

# List deployed files
echo ""
echo "Deployed files on RM2:"
ssh root@$RM2_IP "ls -lh /opt/rm2-inject/" 2>/dev/null || true

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Deployment Complete                                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Check deployment status:"
echo "   ssh root@$RM2_IP '/opt/rm2-inject/server.sh check'"
echo ""
echo "2. Start the injection server:"
echo "   ssh root@$RM2_IP '/opt/rm2-inject/server.sh start'"
echo ""
echo "3. Verify server is running:"
echo "   ssh root@$RM2_IP '/opt/rm2-inject/server.sh status'"
echo ""
