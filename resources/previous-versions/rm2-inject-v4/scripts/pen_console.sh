#!/bin/bash
# pen_console.sh - Interactive Pen Command Console
# Send pen commands directly to RM2 injection server
# Debug tool for testing coordinate transformation

if [ -z "$1" ]; then
    echo "Usage: pen_console.sh <rm2_ip>"
    echo "Example: pen_console.sh 10.11.99.1"
    exit 1
fi

RM2_IP="$1"
FIFO_PATH="/tmp/lamp_inject"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  RM2 Pen Command Console - Interactive Debugger        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Commands:"
echo "  down <x> <y>    - Pen down at (x, y)"
echo "  move <x> <y>    - Move pen to (x, y)"
echo "  up              - Pen up"
echo "  line <x1> <y1> <x2> <y2> - Draw line"
echo "  rect <x> <y> <w> <h>     - Draw rectangle"
echo "  circle <x> <y> <r> [seg] - Draw circle (segments, default 32)"
echo "  clear           - Clear screen (pen up, move to 0,0)"
echo "  status          - Show server status"
echo "  help            - Show this help"
echo "  quit            - Exit"
echo ""
echo "Examples:"
echo "  down 100 100    - Touch at (100, 100)"
echo "  move 200 100    - Draw to (200, 100)"
echo "  up              - Release"
echo "  line 100 100 200 200 - Draw diagonal line"
echo "  rect 100 100 200 200   - Draw rectangle at (100,100) 200x200"
echo ""

# Function to send command to RM2
send_cmd() {
    local cmd="$1"
    echo -n "  Sending: $cmd ... "
    if ssh root@$RM2_IP "echo '$cmd' > $FIFO_PATH 2>/dev/null" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

# Function to draw line
draw_line() {
    local x1=$1 y1=$2 x2=$3 y2=$4
    local steps=10
    local dx=$((x2 - x1))
    local dy=$((y2 - y1))
    
    # Calculate steps based on distance
    local dist=$(( (dx*dx + dy*dy) ))
    if [ $dist -gt 10000 ]; then
        steps=50
    elif [ $dist -gt 1000 ]; then
        steps=20
    fi
    
    send_cmd "PEN_DOWN $x1 $y1"
    sleep 0.1
    
    for ((i=1; i<=steps; i++)); do
        local x=$(( x1 + (dx * i) / steps ))
        local y=$(( y1 + (dy * i) / steps ))
        send_cmd "PEN_MOVE $x $y"
        sleep 0.05
    done
    
    send_cmd "PEN_UP"
}

# Function to draw rectangle
draw_rect() {
    local x=$1 y=$2 w=$3 h=$4
    local x2=$((x + w))
    local y2=$((y + h))
    
    echo -e "${CYAN}Drawing rectangle: ($x,$y) to ($x2,$y2)${NC}"
    
    # Top line
    draw_line $x $y $x2 $y
    sleep 0.2
    
    # Right line
    draw_line $x2 $y $x2 $y2
    sleep 0.2
    
    # Bottom line
    draw_line $x2 $y2 $x $y2
    sleep 0.2
    
    # Left line
    draw_line $x $y2 $x $y
    sleep 0.2
}

# Function to draw circle
draw_circle() {
    local cx=$1 cy=$2 r=$3 seg=${4:-32}
    local pi=3141592653589793
    
    echo -e "${CYAN}Drawing circle: center($cx,$cy) radius=$r segments=$seg${NC}"
    
    send_cmd "PEN_DOWN $((cx + r)) $cy"
    sleep 0.1
    
    for ((i=1; i<=seg; i++)); do
        # Simple approximation: calculate angle
        local angle=$((i * 360 / seg))
        
        # Simplified trig (approximate)
        case $angle in
            0)   local x=$((cx + r)); local y=$cy ;;
            45)  local x=$((cx + r*7/10)); local y=$((cy + r*7/10)) ;;
            90)  local x=$cx; local y=$((cy + r)) ;;
            135) local x=$((cx - r*7/10)); local y=$((cy + r*7/10)) ;;
            180) local x=$((cx - r)); local y=$cy ;;
            225) local x=$((cx - r*7/10)); local y=$((cy - r*7/10)) ;;
            270) local x=$cx; local y=$((cy - r)) ;;
            315) local x=$((cx + r*7/10)); local y=$((cy - r*7/10)) ;;
            *)   
                # Use floating point approximation
                local rad=$(echo "scale=4; $angle * 3.14159 / 180" | bc 2>/dev/null)
                if [ -z "$rad" ]; then
                    local x=$((cx + r)); local y=$cy
                else
                    local x=$((cx + r)); local y=$cy
                fi
                ;;
        esac
        
        send_cmd "PEN_MOVE $x $y"
        sleep 0.05
    done
    
    send_cmd "PEN_UP"
}

# Main interactive loop
while true; do
    echo -n -e "${YELLOW}> ${NC}"
    read -r input
    
    # Parse input
    set -- $input
    cmd="$1"
    
    case "$cmd" in
        down)
            if [ -z "$2" ] || [ -z "$3" ]; then
                echo -e "${RED}Usage: down <x> <y>${NC}"
            else
                send_cmd "PEN_DOWN $2 $3"
            fi
            ;;
        move)
            if [ -z "$2" ] || [ -z "$3" ]; then
                echo -e "${RED}Usage: move <x> <y>${NC}"
            else
                send_cmd "PEN_MOVE $2 $3"
            fi
            ;;
        up)
            send_cmd "PEN_UP"
            ;;
        line)
            if [ -z "$4" ]; then
                echo -e "${RED}Usage: line <x1> <y1> <x2> <y2>${NC}"
            else
                draw_line "$2" "$3" "$4" "$5"
            fi
            ;;
        rect)
            if [ -z "$4" ]; then
                echo -e "${RED}Usage: rect <x> <y> <width> <height>${NC}"
            else
                draw_rect "$2" "$3" "$4" "$5"
            fi
            ;;
        circle)
            if [ -z "$3" ]; then
                echo -e "${RED}Usage: circle <x> <y> <radius> [segments]${NC}"
            else
                draw_circle "$2" "$3" "$4" "${5:-32}"
            fi
            ;;
        clear)
            echo -e "${CYAN}Clearing (pen up, moving to 0,0)${NC}"
            send_cmd "PEN_UP"
            sleep 0.1
            send_cmd "PEN_MOVE 0 0"
            ;;
        status)
            echo -e "${CYAN}Server status:${NC}"
            ssh root@$RM2_IP '/opt/rm2-inject/server.sh status' 2>/dev/null || echo "Failed to get status"
            ;;
        help)
            echo ""
            echo "Commands:"
            echo "  down <x> <y>    - Pen down at (x, y)"
            echo "  move <x> <y>    - Move pen to (x, y)"
            echo "  up              - Pen up"
            echo "  line <x1> <y1> <x2> <y2> - Draw line"
            echo "  rect <x> <y> <w> <h>     - Draw rectangle"
            echo "  circle <x> <y> <r> [seg] - Draw circle"
            echo "  clear           - Clear screen"
            echo "  status          - Show server status"
            echo "  help            - Show this help"
            echo "  quit            - Exit"
            echo ""
            ;;
        quit|exit|q)
            echo "Exiting..."
            break
            ;;
        "")
            # Empty input, just show prompt
            ;;
        *)
            echo -e "${RED}Unknown command: $cmd${NC}"
            echo "Type 'help' for commands"
            ;;
    esac
done

echo ""
echo "Done."
