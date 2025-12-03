#!/bin/bash
# Console client - sends commands to RM2 via SSH

if [ -z "$1" ]; then
    echo "Usage: console.sh <rm2_ip>"
    exit 1
fi

RM2_IP="$1"
FIFO_PATH="/tmp/lamp_inject"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

send_cmd() {
    echo "$1" | ssh root@$RM2_IP "cat > $FIFO_PATH"
}

inject_svg() {
    local svg_file="$1"
    local x="$2"
    local y="$3"
    local scale="${4:-auto}"
    
    if [ ! -f "$svg_file" ]; then
        echo "Error: File not found: $svg_file"
        return 1
    fi
    
    if ! which python3 >/dev/null 2>&1; then
        echo "Error: python3 not found (needed for SVG conversion)"
        return 1
    fi
    
    echo "Converting SVG..."
    local commands=$(python3 "$PROJECT_ROOT/tools/svg2inject.py" "$svg_file" "$scale" "$x" "$y")
    
    if [ -z "$commands" ]; then
        echo "Error: SVG conversion failed"
        return 1
    fi
    
    local line_count=$(echo "$commands" | wc -l)
    echo "Sending $line_count commands..."
    
    echo "$commands" | while IFS= read -r cmd; do
        send_cmd "$cmd"
    done
    
    echo "Injected $svg_file at ($x, $y) with scale=$scale"
}

draw_line() {
    send_cmd "PEN_DOWN $1 $2"
    send_cmd "PEN_MOVE $3 $4"
    send_cmd "PEN_UP"
    echo "Drew line from ($1,$2) to ($3,$4)"
}

draw_rect() {
    local x=$1 y=$2 w=$3 h=$4
    send_cmd "PEN_DOWN $x $y"
    send_cmd "PEN_MOVE $((x+w)) $y"
    send_cmd "PEN_MOVE $((x+w)) $((y+h))"
    send_cmd "PEN_MOVE $x $((y+h))"
    send_cmd "PEN_MOVE $x $y"
    send_cmd "PEN_UP"
    echo "Drew rectangle at ($x,$y) size ${w}×${h}"
}

draw_text() {
    local text="$1"
    local x="$2"
    local y="$3"
    local scale="${4:-2.0}"
    
    if ! which python3 >/dev/null 2>&1; then
        echo "Error: python3 not found (needed for text rendering)"
        return 1
    fi
    
    echo "Converting text to strokes..."
    local commands=$(python3 "$PROJECT_ROOT/tools/text2inject.py" "$text" "$x" "$y" "$scale")
    
    if [ -z "$commands" ]; then
        echo "Error: Text conversion failed"
        return 1
    fi
    
    echo "$commands" | while IFS= read -r cmd; do
        send_cmd "$cmd"
    done
    
    echo "Wrote text '$text' at ($x,$y) scale=$scale"
}

show_help() {
    cat << 'EOF'
RM2 Injection Console Commands:

  inject <svg> <x> <y> [scale]     - Inject SVG file
  text "<text>" <x> <y> [scale]    - Write handwritten text
  line <x1> <y1> <x2> <y2>         - Draw line
  rect <x> <y> <w> <h>             - Draw rectangle
  cursor                           - Get cursor position
  status                           - Check server status
  coords                           - Show coordinate system
  help                             - This help
  quit                             - Exit

Examples:
  inject examples/No.svg 100 200 3.0
  text "HELLO WORLD" 100 100 2.5
  line 0 0 500 500
  rect 100 100 300 200

Note: Touch pen to RM2 screen after commands to trigger injection.
EOF
}

show_coords() {
    cat << 'EOF'
RM2 Coordinate System:

Display: 1404 × 1872 pixels (portrait)

    (0,0) ──────────────────> X (1404)
      │
      │      Drawing area
      │
      ▼ Y (1872)

Axes are swapped internally (handled automatically).
EOF
}

check_status() {
    ssh root@$RM2_IP "pidof xochitl >/dev/null && echo 'Xochitl: RUNNING' || echo 'Xochitl: STOPPED'; [ -p /tmp/lamp_inject ] && echo 'FIFO: OK' || echo 'FIFO: MISSING'"
}

echo "RM2 Injection Console - Connected to $RM2_IP"
echo "Type 'help' for commands"
echo ""

while true; do
    echo -n "> "
    read -r line
    
    [ -z "$line" ] && continue
    
    # Handle quoted text for text command
    if [[ "$line" =~ ^text[[:space:]]+ ]]; then
        # Extract quoted string
        if [[ "$line" =~ \"([^\"]+)\"[[:space:]]+([0-9]+)[[:space:]]+([0-9]+)([[:space:]]+([0-9.]+))? ]]; then
            text="${BASH_REMATCH[1]}"
            x="${BASH_REMATCH[2]}"
            y="${BASH_REMATCH[3]}"
            scale="${BASH_REMATCH[5]:-2.0}"
            draw_text "$text" "$x" "$y" "$scale"
        else
            echo 'Usage: text "YOUR TEXT" <x> <y> [scale]'
        fi
        continue
    fi
    
    set -- $line
    cmd="$1"
    shift
    
    case "$cmd" in
        quit|exit)
            echo "Goodbye"
            break
            ;;
        help)
            show_help
            ;;
        coords)
            show_coords
            ;;
        status)
            check_status
            ;;
        cursor)
            send_cmd "GET_CURSOR"
            echo "Check RM2 logs for cursor position"
            ;;
        inject)
            if [ $# -lt 3 ]; then
                echo "Usage: inject <svg> <x> <y> [scale]"
                continue
            fi
            svg="$1"
            x="$2"
            y="$3"
            scale="${4:-auto}"
            
            [ ! -f "$svg" ] && [ -f "$PROJECT_ROOT/$svg" ] && svg="$PROJECT_ROOT/$svg"
            inject_svg "$svg" "$x" "$y" "$scale"
            ;;
        line)
            [ $# -ne 4 ] && echo "Usage: line <x1> <y1> <x2> <y2>" && continue
            draw_line "$1" "$2" "$3" "$4"
            ;;
        rect)
            [ $# -ne 4 ] && echo "Usage: rect <x> <y> <w> <h>" && continue
            draw_rect "$1" "$2" "$3" "$4"
            ;;
        *)
            echo "Unknown command: $cmd (type 'help')"
            ;;
    esac
done
