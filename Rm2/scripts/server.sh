#!/bin/bash
# Server management script for RM2 injection system
# This script manages the xochitl service with LD_PRELOAD injection

set -e

INSTALL_DIR="/opt/rm2in2"
INJECT_LIB="$INSTALL_DIR/inject.so"
BACKUP_DIR="$INSTALL_DIR/backup"
SERVICE_OVERRIDE="/etc/systemd/system/xochitl.service.d/rm2in2.conf"
XOCHITL_BIN="/usr/bin/xochitl"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    if [ ! -f "$INJECT_LIB" ]; then
        log_error "Injection library not found: $INJECT_LIB"
        log_error "Please run deployment first"
        exit 1
    fi

    if [ ! -f "$XOCHITL_BIN" ]; then
        log_error "Xochitl binary not found: $XOCHITL_BIN"
        exit 1
    fi
}

backup_config() {
    log_info "Creating backup..."
    mkdir -p "$BACKUP_DIR"

    # Backup systemd override if it exists
    if [ -f "$SERVICE_OVERRIDE" ]; then
        cp "$SERVICE_OVERRIDE" "$BACKUP_DIR/rm2in2.conf.bak"
        log_info "Backed up service override"
    fi

    # Save current xochitl service status
    systemctl show xochitl.service > "$BACKUP_DIR/xochitl.status.bak"
    log_info "Backed up service status"
}

start_service() {
    log_info "Starting RM2 injection service..."

    check_prerequisites
    backup_config

    # Create systemd override directory
    mkdir -p "$(dirname "$SERVICE_OVERRIDE")"

    # Create service override to inject our library
    log_info "Creating systemd service override..."
    cat > "$SERVICE_OVERRIDE" << 'EOF'
[Service]
Environment="LD_PRELOAD=/opt/rm2in2/inject.so"
EOF

    # Reload systemd to pick up changes
    log_info "Reloading systemd configuration..."
    systemctl daemon-reload

    # Restart xochitl with injection
    log_info "Restarting xochitl service..."
    systemctl restart xochitl

    # Wait a moment for service to start
    sleep 2

    # Check if service started successfully
    if systemctl is-active --quiet xochitl; then
        log_info "✓ Service started successfully"

        # Check if FIFO was created (indicates hook is working)
        sleep 1
        if [ -e "/tmp/rm2_inject" ]; then
            log_info "✓ Injection hook is active (FIFO created)"
        else
            log_warn "FIFO not found yet - hook may still be initializing"
        fi

        echo ""
        echo "==================================="
        echo "RM2 Injection Service Started"
        echo "==================================="
        echo ""
        echo "Status: ACTIVE"
        echo "FIFO:   /tmp/rm2_inject"
        echo ""
        echo "To send commands:"
        echo "  cat commands.txt > /tmp/rm2_inject"
        echo ""
        echo "To check logs:"
        echo "  journalctl -u xochitl -f"
        echo ""
        echo "To stop:"
        echo "  $0 stop"
        echo ""
    else
        log_error "Failed to start service"
        log_error "Attempting to restore..."
        restore_service
        exit 1
    fi
}

stop_service() {
    log_info "Stopping injection service..."

    # Stop xochitl
    log_info "Stopping xochitl..."
    systemctl stop xochitl

    # Remove systemd override
    if [ -f "$SERVICE_OVERRIDE" ]; then
        log_info "Removing service override..."
        rm "$SERVICE_OVERRIDE"
        rmdir "$(dirname "$SERVICE_OVERRIDE")" 2>/dev/null || true
    fi

    # Reload systemd
    log_info "Reloading systemd configuration..."
    systemctl daemon-reload

    # Start xochitl normally
    log_info "Starting xochitl normally..."
    systemctl start xochitl

    # Clean up FIFO if it exists
    if [ -e "/tmp/rm2_inject" ]; then
        rm -f "/tmp/rm2_inject"
        log_info "Cleaned up FIFO"
    fi

    sleep 2

    if systemctl is-active --quiet xochitl; then
        log_info "✓ Service stopped and restored to normal operation"
    else
        log_error "Failed to restart xochitl normally"
        exit 1
    fi
}

restore_service() {
    log_info "Restoring original configuration..."

    # Stop xochitl
    systemctl stop xochitl 2>/dev/null || true

    # Remove our override
    if [ -f "$SERVICE_OVERRIDE" ]; then
        rm "$SERVICE_OVERRIDE"
        rmdir "$(dirname "$SERVICE_OVERRIDE")" 2>/dev/null || true
    fi

    # Restore backup if available
    if [ -f "$BACKUP_DIR/rm2in2.conf.bak" ]; then
        log_info "Found backup, restoring..."
        mkdir -p "$(dirname "$SERVICE_OVERRIDE")"
        cp "$BACKUP_DIR/rm2in2.conf.bak" "$SERVICE_OVERRIDE"
    fi

    # Reload and restart
    systemctl daemon-reload
    systemctl start xochitl

    # Clean up
    rm -f "/tmp/rm2_inject"

    log_info "✓ Original configuration restored"
}

status_service() {
    echo "==================================="
    echo "RM2 Injection Service Status"
    echo "==================================="
    echo ""

    # Check xochitl service status
    echo "Xochitl Service:"
    if systemctl is-active --quiet xochitl; then
        echo "  Status: ${GREEN}ACTIVE${NC}"
    else
        echo "  Status: ${RED}INACTIVE${NC}"
    fi

    # Check if override exists
    echo ""
    echo "Injection Override:"
    if [ -f "$SERVICE_OVERRIDE" ]; then
        echo "  Status: ${GREEN}ENABLED${NC}"
        echo "  File:   $SERVICE_OVERRIDE"
    else
        echo "  Status: ${YELLOW}NOT ENABLED${NC}"
    fi

    # Check injection library
    echo ""
    echo "Injection Library:"
    if [ -f "$INJECT_LIB" ]; then
        echo "  Status: ${GREEN}INSTALLED${NC}"
        echo "  File:   $INJECT_LIB"
        ls -lh "$INJECT_LIB" | awk '{print "  Size:   " $5 " (" $6 " " $7 " " $8 ")"}'
    else
        echo "  Status: ${RED}NOT FOUND${NC}"
    fi

    # Check FIFO
    echo ""
    echo "Command FIFO:"
    if [ -e "/tmp/rm2_inject" ]; then
        echo "  Status: ${GREEN}ACTIVE${NC}"
        echo "  Path:   /tmp/rm2_inject"
        ls -l /tmp/rm2_inject | awk '{print "  Type:   " $1}'
    else
        echo "  Status: ${YELLOW}NOT FOUND${NC}"
        if [ -f "$SERVICE_OVERRIDE" ]; then
            echo "  Note:   Hook may still be initializing"
        fi
    fi

    # Check if LD_PRELOAD is active
    echo ""
    echo "LD_PRELOAD Status:"
    if systemctl show xochitl.service | grep -q "LD_PRELOAD=/opt/rm2in2/inject.so"; then
        echo "  Status: ${GREEN}CONFIGURED${NC}"
    else
        echo "  Status: ${YELLOW}NOT CONFIGURED${NC}"
    fi

    # Recent logs
    echo ""
    echo "Recent Logs (last 5 lines):"
    journalctl -u xochitl -n 5 --no-pager | tail -5 | sed 's/^/  /'

    echo ""
}

test_injection() {
    log_info "Testing injection system..."

    if [ ! -e "/tmp/rm2_inject" ]; then
        log_error "FIFO not found - injection not active"
        exit 1
    fi

    log_info "Sending test pattern (single dot in center)..."

    # Calculate center coordinates (rough approximation)
    CENTER_X=10483  # WACOM_MAX_X / 2
    CENTER_Y=7862   # WACOM_MAX_Y / 2

    cat > /tmp/test_injection.txt << EOF
# Test pattern - single dot in center
PEN_DOWN $CENTER_X $CENTER_Y
DELAY 100
PEN_UP
EOF

    cat /tmp/test_injection.txt > /tmp/rm2_inject

    log_info "Test command sent!"
    log_info "Open the notes app and tap the screen to see the result"
    log_info "You should see a small dot appear in the center"

    rm /tmp/test_injection.txt
}

show_help() {
    cat << EOF
RM2 Injection Service Manager

Usage: $0 <command>

Commands:
  start      Start injection service (enable LD_PRELOAD)
  stop       Stop injection service (restore normal operation)
  restart    Restart injection service
  status     Show service status
  restore    Restore original configuration (emergency rollback)
  test       Send a test pattern
  help       Show this help message

Examples:
  $0 start          # Enable injection
  $0 status         # Check if running
  $0 stop           # Disable injection
  $0 restore        # Emergency restore if something breaks

Service Management:
  - Uses systemd service override
  - Automatically backs up configuration
  - Safe rollback if startup fails
  - Cleans up FIFO on stop

Files:
  Library:  $INJECT_LIB
  Override: $SERVICE_OVERRIDE
  Backup:   $BACKUP_DIR/
  FIFO:     /tmp/rm2_inject

Logs:
  journalctl -u xochitl -f
EOF
}

# Main command dispatcher
case "${1:-}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        start_service
        ;;
    status)
        status_service
        ;;
    restore)
        restore_service
        ;;
    test)
        test_injection
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
