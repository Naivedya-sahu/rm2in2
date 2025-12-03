#!/bin/bash
# Deployment script for RM2 injection system
# Safely deploys injection library and management scripts to RM2

set -e

# Configuration
RM2_IP="${1:-10.11.99.1}"
INSTALL_DIR="/opt/rm2in2"
LOCAL_BUILD_DIR="$(dirname "$0")/../build"
LOCAL_SCRIPTS_DIR="$(dirname "$0")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

check_prerequisites() {
    log_step "Checking prerequisites..."

    # Check if inject.so exists
    if [ ! -f "$LOCAL_BUILD_DIR/inject.so" ]; then
        log_error "inject.so not found at $LOCAL_BUILD_DIR/inject.so"
        log_error "Please run 'make server' first"
        exit 1
    fi

    # Check if scripts exist
    if [ ! -f "$LOCAL_SCRIPTS_DIR/server.sh" ]; then
        log_error "server.sh not found"
        exit 1
    fi

    log_info "✓ All files found locally"
}

test_connectivity() {
    log_step "Testing connectivity to RM2 at $RM2_IP..."

    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes root@"$RM2_IP" "echo Connected" > /dev/null 2>&1; then
        log_error "Cannot connect to RM2 at $RM2_IP"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check if RM2 is powered on"
        echo "  2. Verify IP address (check Settings > Help on RM2)"
        echo "  3. Ensure USB or WiFi connection is active"
        echo "  4. Test SSH: ssh root@$RM2_IP"
        echo ""
        exit 1
    fi

    log_info "✓ Connected to RM2"
}

check_existing_installation() {
    log_step "Checking for existing installation..."

    if ssh root@"$RM2_IP" "[ -d $INSTALL_DIR ]"; then
        log_warn "Existing installation found at $INSTALL_DIR"

        # Check if service is running
        if ssh root@"$RM2_IP" "systemctl is-active --quiet xochitl && [ -f /etc/systemd/system/xochitl.service.d/rm2in2.conf ]"; then
            log_warn "Injection service appears to be running"
            echo ""
            read -p "Stop service and proceed with update? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Deployment cancelled"
                exit 0
            fi

            log_info "Stopping existing service..."
            ssh root@"$RM2_IP" "$INSTALL_DIR/server.sh stop" || log_warn "Could not stop service cleanly"
        fi
    fi
}

create_backup() {
    log_step "Creating backup of current installation..."

    ssh root@"$RM2_IP" "mkdir -p $INSTALL_DIR/backup"

    # Backup old inject.so if exists
    if ssh root@"$RM2_IP" "[ -f $INSTALL_DIR/inject.so ]"; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        ssh root@"$RM2_IP" "cp $INSTALL_DIR/inject.so $INSTALL_DIR/backup/inject.so.$TIMESTAMP"
        log_info "✓ Backed up old inject.so"
    fi

    # Backup scripts
    if ssh root@"$RM2_IP" "[ -f $INSTALL_DIR/server.sh ]"; then
        ssh root@"$RM2_IP" "cp $INSTALL_DIR/server.sh $INSTALL_DIR/backup/server.sh.$(date +%Y%m%d_%H%M%S)"
        log_info "✓ Backed up old scripts"
    fi
}

deploy_files() {
    log_step "Deploying files to RM2..."

    # Create installation directory
    ssh root@"$RM2_IP" "mkdir -p $INSTALL_DIR"
    log_info "✓ Created installation directory"

    # Deploy inject.so
    log_info "Copying inject.so..."
    scp -q "$LOCAL_BUILD_DIR/inject.so" root@"$RM2_IP":"$INSTALL_DIR/"
    log_info "✓ Deployed inject.so"

    # Deploy server management script
    log_info "Copying server.sh..."
    scp -q "$LOCAL_SCRIPTS_DIR/server.sh" root@"$RM2_IP":"$INSTALL_DIR/"
    ssh root@"$RM2_IP" "chmod +x $INSTALL_DIR/server.sh"
    log_info "✓ Deployed server.sh"

    # Deploy capture script if exists
    if [ -f "$LOCAL_SCRIPTS_DIR/capture_pen_events.sh" ]; then
        log_info "Copying capture_pen_events.sh..."
        scp -q "$LOCAL_SCRIPTS_DIR/capture_pen_events.sh" root@"$RM2_IP":"$INSTALL_DIR/"
        ssh root@"$RM2_IP" "chmod +x $INSTALL_DIR/capture_pen_events.sh"
        log_info "✓ Deployed capture_pen_events.sh"
    fi
}

verify_deployment() {
    log_step "Verifying deployment..."

    # Check if files exist
    if ! ssh root@"$RM2_IP" "[ -f $INSTALL_DIR/inject.so ] && [ -f $INSTALL_DIR/server.sh ]"; then
        log_error "Deployment verification failed - files not found on RM2"
        exit 1
    fi

    # Check file sizes
    LOCAL_SIZE=$(stat -f%z "$LOCAL_BUILD_DIR/inject.so" 2>/dev/null || stat -c%s "$LOCAL_BUILD_DIR/inject.so" 2>/dev/null)
    REMOTE_SIZE=$(ssh root@"$RM2_IP" "stat -c%s $INSTALL_DIR/inject.so")

    if [ "$LOCAL_SIZE" != "$REMOTE_SIZE" ]; then
        log_error "File size mismatch! Local: $LOCAL_SIZE, Remote: $REMOTE_SIZE"
        log_error "Deployment may be corrupted"
        exit 1
    fi

    log_info "✓ Deployment verified (size: $LOCAL_SIZE bytes)"
}

create_uninstall_script() {
    log_step "Creating uninstall script..."

    ssh root@"$RM2_IP" "cat > $INSTALL_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
# Uninstall RM2 injection system

INSTALL_DIR="/opt/rm2in2"

echo "==================================="
echo "RM2 Injection System - Uninstall"
echo "==================================="
echo ""
echo "This will:"
echo "  - Stop the injection service"
echo "  - Remove all installed files"
echo "  - Restore original xochitl service"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled"
    exit 0
fi

echo ""
echo "[1/4] Stopping service..."
if [ -f "$INSTALL_DIR/server.sh" ]; then
    "$INSTALL_DIR/server.sh" stop || echo "Warning: Could not stop service cleanly"
fi

echo "[2/4] Removing systemd override..."
rm -f /etc/systemd/system/xochitl.service.d/rm2in2.conf
rmdir /etc/systemd/system/xochitl.service.d 2>/dev/null || true
systemctl daemon-reload

echo "[3/4] Cleaning up files..."
rm -f /tmp/rm2_inject
rm -rf "$INSTALL_DIR"

echo "[4/4] Restarting xochitl..."
systemctl restart xochitl

echo ""
echo "✓ Uninstall complete"
echo ""
EOF

    ssh root@"$RM2_IP" "chmod +x $INSTALL_DIR/uninstall.sh"
    log_info "✓ Created uninstall script"
}

show_next_steps() {
    echo ""
    echo "==================================="
    echo "Deployment Complete!"
    echo "==================================="
    echo ""
    echo "Installation details:"
    echo "  Location:  $INSTALL_DIR"
    echo "  RM2 IP:    $RM2_IP"
    echo ""
    echo "Next steps:"
    echo ""
    echo "  1. Start the injection service:"
    echo "     ${GREEN}ssh root@$RM2_IP '$INSTALL_DIR/server.sh start'${NC}"
    echo ""
    echo "  2. Check service status:"
    echo "     ${GREEN}ssh root@$RM2_IP '$INSTALL_DIR/server.sh status'${NC}"
    echo ""
    echo "  3. Generate test patterns on PC:"
    echo "     ${GREEN}make test-patterns${NC}"
    echo ""
    echo "  4. Send test commands from PC:"
    echo "     ${GREEN}./Rm2in2/scripts/send.sh test-output/corners_A_Direct.txt $RM2_IP${NC}"
    echo ""
    echo "  5. View logs on RM2:"
    echo "     ${GREEN}ssh root@$RM2_IP 'journalctl -u xochitl -f'${NC}"
    echo ""
    echo "Service management (on RM2):"
    echo "  Start:     $INSTALL_DIR/server.sh start"
    echo "  Stop:      $INSTALL_DIR/server.sh stop"
    echo "  Status:    $INSTALL_DIR/server.sh status"
    echo "  Restore:   $INSTALL_DIR/server.sh restore"
    echo "  Test:      $INSTALL_DIR/server.sh test"
    echo ""
    echo "To uninstall:"
    echo "  ${YELLOW}ssh root@$RM2_IP '$INSTALL_DIR/uninstall.sh'${NC}"
    echo ""
    echo "Backup location on RM2:"
    echo "  $INSTALL_DIR/backup/"
    echo ""
}

# Main deployment flow
main() {
    echo "==================================="
    echo "RM2 Injection System - Deployment"
    echo "==================================="
    echo ""
    echo "Target: $RM2_IP"
    echo ""

    check_prerequisites
    test_connectivity
    check_existing_installation
    create_backup
    deploy_files
    verify_deployment
    create_uninstall_script
    show_next_steps
}

main
