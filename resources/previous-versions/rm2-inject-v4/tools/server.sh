#!/bin/bash
# RM2 Injection Server v5 - FIXED
# Hybrid approach: Use systemctl for Xochitl lifecycle, but with better verification
# 
# Based on v3 (proven working) but with v4 improvements

set -e

HOOK_LIB="/opt/rm2-inject/inject_hook.so"
FIFO_PATH="/tmp/lamp_inject"
PIDFILE="/var/run/rm2-inject.pid"
LOGFILE="/var/log/rm2-inject.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"
}

log_error() {
    echo -e "${RED}ERROR: $*${NC}" >&2
    log "ERROR: $*"
}

log_success() {
    echo -e "${GREEN}✓ $*${NC}"
    log "$*"
}

log_warn() {
    echo -e "${YELLOW}⚠ $*${NC}"
    log "WARNING: $*"
}

is_running() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            return 0
        fi
        rm -f "$PIDFILE"
    fi
    return 1
}

verify_hook() {
    if [ ! -f "$HOOK_LIB" ]; then
        log_error "Hook library not found: $HOOK_LIB"
        return 1
    fi
    
    # Check if it's executable
    if [ ! -x "$HOOK_LIB" ]; then
        log_warn "Hook not executable, fixing permissions..."
        chmod +x "$HOOK_LIB" || true
    fi
    
    log_success "Hook library verified: $HOOK_LIB"
    return 0
}

start_server() {
    if is_running; then
        log_warn "Server already running"
        return 0
    fi
    
    log "Starting RM2 injection server v5..."
    
    # Verify hook exists first
    if ! verify_hook; then
        return 1
    fi
    
    # Create FIFO
    log "Creating FIFO..."
    rm -f "$FIFO_PATH"
    mkfifo "$FIFO_PATH" || { log_error "Failed to create FIFO"; return 1; }
    chmod 666 "$FIFO_PATH"
    log_success "Created FIFO at $FIFO_PATH"
    
    # Stop Xochitl completely
    log "Stopping existing Xochitl..."
    systemctl stop xochitl 2>/dev/null || true
    killall -9 xochitl 2>/dev/null || true
    sleep 2
    
    # Set LD_PRELOAD in systemd environment
    log "Setting LD_PRELOAD environment for systemd..."
    systemctl set-environment LD_PRELOAD="$HOOK_LIB" || { log_error "Failed to set environment"; return 1; }
    
    # Start Xochitl via systemctl (proper lifecycle management)
    log "Starting Xochitl with injection hook via systemctl..."
    if ! systemctl start xochitl; then
        log_error "Failed to start Xochitl"
        systemctl unset-environment LD_PRELOAD
        return 1
    fi
    
    sleep 3
    
    # Verify Xochitl started
    if ! pidof xochitl >/dev/null; then
        log_error "Xochitl failed to start"
        systemctl unset-environment LD_PRELOAD
        return 1
    fi
    
    XOCHITL_PID=$(pidof xochitl | awk '{print $1}')
    log_success "Xochitl started (PID: $XOCHITL_PID)"
    
    # Verify hook is loaded
    sleep 1
    if grep -q inject_hook "/proc/$XOCHITL_PID/maps" 2>/dev/null; then
        log_success "Injection hook loaded in Xochitl"
    else
        log_warn "Hook not yet loaded in memory maps (may load lazily on first access)"
    fi
    
    # Write PID file
    echo $$ > "$PIDFILE"
    
    log_success "Server started (PID: $$)"
    log "Ready to accept injection commands via $FIFO_PATH"
    
    # Keep running as daemon
    # The C hook reads FIFO in background thread from Xochitl
    # This process monitors and restarts if needed
    while true; do
        sleep 10
        
        # Check if Xochitl crashed
        if ! pidof xochitl >/dev/null; then
            log_warn "Xochitl died, restarting..."
            systemctl start xochitl 2>/dev/null || true
            sleep 3
        fi
        
        # Check if someone killed us externally
        if [ ! -f "$PIDFILE" ]; then
            log "PID file removed, shutting down..."
            break
        fi
    done
    
    return 0
}

stop_server() {
    log "Stopping RM2 injection server..."
    
    if is_running; then
        PID=$(cat "$PIDFILE")
        log "Stopping server process (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
        rm -f "$PIDFILE"
    fi
    
    # Clear LD_PRELOAD from systemd
    log "Clearing LD_PRELOAD from systemd..."
    systemctl unset-environment LD_PRELOAD 2>/dev/null || true
    
    # Restart Xochitl in normal mode
    log "Restarting Xochitl in normal mode..."
    systemctl restart xochitl 2>/dev/null || true
    sleep 2
    
    # Clean up FIFO
    if [ -e "$FIFO_PATH" ]; then
        rm -f "$FIFO_PATH"
        log_success "Removed FIFO: $FIFO_PATH"
    fi
    
    log_success "Server stopped"
    return 0
}

status_server() {
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║  RM2 Injection Server v5 Status                        ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    
    # Server process
    if is_running; then
        PID=$(cat "$PIDFILE")
        echo "Server Process: ✓ RUNNING (PID: $PID)"
    else
        echo "Server Process: ✗ STOPPED"
    fi
    
    # Xochitl
    if pidof xochitl >/dev/null; then
        XOCHITL_PID=$(pidof xochitl | awk '{print $1}')
        echo "Xochitl:        ✓ RUNNING (PID: $XOCHITL_PID)"
        
        # Check hook loaded
        if grep -q inject_hook "/proc/$XOCHITL_PID/maps" 2>/dev/null; then
            echo "Hook Status:    ✓ LOADED"
            HOOK_ADDR=$(grep inject_hook "/proc/$XOCHITL_PID/maps" | head -1 | awk '{print $1}')
            echo "Hook Address:   $HOOK_ADDR"
        else
            echo "Hook Status:    ✗ NOT LOADED (will load on first access)"
        fi
    else
        echo "Xochitl:        ✗ NOT RUNNING"
        echo "Hook Status:    - (N/A)"
    fi
    
    # FIFO
    if [ -p "$FIFO_PATH" ]; then
        echo "FIFO:           ✓ READY ($FIFO_PATH)"
    else
        echo "FIFO:           ✗ MISSING ($FIFO_PATH)"
    fi
    
    # Hook library
    if [ -f "$HOOK_LIB" ]; then
        SIZE=$(du -h "$HOOK_LIB" | cut -f1)
        echo "Hook Library:   ✓ PRESENT ($SIZE)"
    else
        echo "Hook Library:   ✗ MISSING ($HOOK_LIB)"
    fi
    
    # systemd environment
    echo ""
    echo "Systemd environment:"
    systemctl show-environment | grep LD_PRELOAD 2>/dev/null || echo "  LD_PRELOAD not set"
    
    echo ""
    echo "Log file: $LOGFILE"
    echo ""
}

check_deployment() {
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║  Deployment Status Check                               ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    
    local ok=true
    
    # Hook library
    if [ -f "$HOOK_LIB" ]; then
        echo "✓ Hook library deployed"
    else
        echo "✗ Hook library missing"
        ok=false
    fi
    
    # Server script
    if [ -f "/opt/rm2-inject/server.sh" ]; then
        echo "✓ Server script deployed"
    else
        echo "✗ Server script missing"
        ok=false
    fi
    
    # Xochitl
    if which xochitl >/dev/null 2>&1; then
        echo "✓ Xochitl installed"
    else
        echo "✗ Xochitl not found"
        ok=false
    fi
    
    # /tmp
    if [ -d "/tmp" ]; then
        echo "✓ /tmp directory exists"
    else
        echo "✗ /tmp not found"
        ok=false
    fi
    
    # systemd
    if systemctl --version >/dev/null 2>&1; then
        echo "✓ systemd available"
    else
        echo "✗ systemd not available"
        ok=false
    fi
    
    echo ""
    if [ "$ok" = true ]; then
        echo "✓ Deployment complete and verified"
        return 0
    else
        echo "✗ Deployment incomplete"
        return 1
    fi
}

case "${1:-}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 1
        start_server
        ;;
    status)
        status_server
        ;;
    check)
        check_deployment
        ;;
    *)
        cat << 'EOF'
RM2 Injection Server v5 - Stable

Usage: server.sh {start|stop|restart|status|check}

Commands:
  start       - Start injection server
  stop        - Stop injection server
  restart     - Restart injection server
  status      - Show detailed status
  check       - Check deployment

Examples:
  /opt/rm2-inject/server.sh start
  /opt/rm2-inject/server.sh status
  /opt/rm2-inject/server.sh stop

Log file: /var/log/rm2-inject.log

Notes:
  - v5 uses systemctl for proper Xochitl lifecycle
  - Hook loads with LD_PRELOAD environment variable
  - Server stays running to monitor and auto-restart Xochitl
EOF
        exit 1
        ;;
esac
