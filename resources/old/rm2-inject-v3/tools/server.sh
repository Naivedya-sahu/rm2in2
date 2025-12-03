#!/bin/bash
# RM2 Injection Server - Pure Bash Implementation
# Fixed: Properly load LD_PRELOAD with systemctl

set -e

HOOK_LIB="/opt/rm2-inject/inject_hook.so"
FIFO_PATH="/tmp/lamp_inject"
PIDFILE="/var/run/rm2-inject.pid"
LOGFILE="/var/log/rm2-inject.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"
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

start_server() {
    if is_running; then
        log "Server already running"
        return 1
    fi
    
    log "Starting RM2 injection server..."
    
    # Create FIFO
    rm -f "$FIFO_PATH"
    mkfifo "$FIFO_PATH"
    chmod 666 "$FIFO_PATH"
    log "Created FIFO at $FIFO_PATH"
    
    # Stop Xochitl completely
    log "Stopping Xochitl..."
    systemctl stop xochitl
    killall xochitl 2>/dev/null || true
    sleep 2
    
    # Start Xochitl with LD_PRELOAD hook
    # Method: Use systemctl set-environment to inject LD_PRELOAD
    log "Setting LD_PRELOAD environment for systemd..."
    systemctl set-environment LD_PRELOAD="$HOOK_LIB"
    
    log "Starting Xochitl with injection hook..."
    systemctl start xochitl
    sleep 3
    
    # Verify Xochitl started
    if ! pidof xochitl >/dev/null; then
        log "ERROR: Xochitl failed to start"
        systemctl unset-environment LD_PRELOAD
        return 1
    fi
    
    XOCHITL_PID=$(pidof xochitl)
    log "Xochitl started (PID: $XOCHITL_PID)"
    
    # Verify hook is loaded
    sleep 1
    if grep -q inject_hook "/proc/$XOCHITL_PID/maps" 2>/dev/null; then
        log "Hook successfully loaded ✓"
    else
        log "WARNING: Hook not detected in Xochitl memory maps"
    fi
    
    # Write PID file
    echo $$ > "$PIDFILE"
    
    log "Server started (PID: $$)"
    log "Ready to accept injection commands"
    
    # Keep running (server daemon stays alive)
    # The C hook handles FIFO reading in background thread
    # This process just maintains lifecycle
    
    while true; do
        sleep 10
        
        # Check if Xochitl crashed
        if ! pidof xochitl >/dev/null; then
            log "WARNING: Xochitl died, restarting..."
            systemctl start xochitl
            sleep 2
        fi
        
        # Check if someone killed us
        if [ ! -f "$PIDFILE" ]; then
            log "PID file removed, exiting..."
            break
        fi
    done
}

stop_server() {
    log "Stopping RM2 injection server..."
    
    if is_running; then
        PID=$(cat "$PIDFILE")
        log "Killing server process $PID..."
        kill "$PID" 2>/dev/null || true
        rm -f "$PIDFILE"
    fi
    
    # Clear LD_PRELOAD from systemd environment
    log "Clearing LD_PRELOAD from systemd..."
    systemctl unset-environment LD_PRELOAD
    
    # Restart Xochitl without hook
    log "Restarting Xochitl in normal mode..."
    systemctl restart xochitl
    sleep 2
    
    # Clean up FIFO
    rm -f "$FIFO_PATH"
    
    log "Server stopped"
}

status_server() {
    echo "================================"
    echo "RM2 Injection Server Status"
    echo "================================"
    echo ""
    
    if is_running; then
        PID=$(cat "$PIDFILE")
        echo "Server: RUNNING (PID: $PID)"
    else
        echo "Server: STOPPED"
    fi
    
    if pidof xochitl >/dev/null; then
        XOCHITL_PID=$(pidof xochitl)
        echo "Xochitl: RUNNING (PID: $XOCHITL_PID)"
        
        # Check if hook is loaded
        if grep -q inject_hook "/proc/$XOCHITL_PID/maps" 2>/dev/null; then
            echo "Hook: LOADED ✓"
            echo ""
            echo "Hook details:"
            grep inject_hook "/proc/$XOCHITL_PID/maps" | head -1
        else
            echo "Hook: NOT LOADED"
        fi
    else
        echo "Xochitl: NOT RUNNING"
    fi
    
    # Check systemd environment
    echo ""
    echo "Systemd LD_PRELOAD:"
    systemctl show-environment | grep LD_PRELOAD || echo "  (not set)"
    
    if [ -p "$FIFO_PATH" ]; then
        echo ""
        echo "FIFO: EXISTS ✓"
    else
        echo ""
        echo "FIFO: MISSING"
    fi
    
    echo ""
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
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
