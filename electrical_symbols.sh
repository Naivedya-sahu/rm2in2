#!/bin/bash
# Electrical symbol library using lamp
# Usage: ./electrical_symbols.sh <symbol_name> <x> <y> [size]

LAMP="/opt/bin/lamp"

draw_resistor() {
    local x=$1 y=$2 size=${3:-50}
    # Horizontal resistor (zigzag pattern)
    echo "pen line $x $y $((x+size/4)) $((y-size/4))" | $LAMP
    echo "pen line $((x+size/4)) $((y-size/4)) $((x+size/2)) $((y+size/4))" | $LAMP
    echo "pen line $((x+size/2)) $((y+size/4)) $((x+3*size/4)) $((y-size/4))" | $LAMP
    echo "pen line $((x+3*size/4)) $((y-size/4)) $((x+size)) $y" | $LAMP
}

draw_capacitor() {
    local x=$1 y=$2 size=${3:-50}
    # Two parallel lines
    echo "pen line $((x+size/2-5)) $((y-size/2)) $((x+size/2-5)) $((y+size/2))" | $LAMP
    echo "pen line $((x+size/2+5)) $((y-size/2)) $((x+size/2+5)) $((y+size/2))" | $LAMP
    # Connection lines
    echo "pen line $x $y $((x+size/2-5)) $y" | $LAMP
    echo "pen line $((x+size/2+5)) $y $((x+size)) $y" | $LAMP
}

draw_inductor() {
    local x=$1 y=$2 size=${3:-50}
    # Coil (series of arcs approximated with circles)
    for i in 0 1 2; do
        cx=$((x + i*size/3 + size/6))
        echo "pen circle $cx $y $((size/6))" | $LAMP
    done
}

draw_ground() {
    local x=$1 y=$2 size=${3:-50}
    # Ground symbol (vertical line with horizontal lines)
    echo "pen line $x $((y-size)) $x $y" | $LAMP
    echo "pen line $((x-size/2)) $y $((x+size/2)) $y" | $LAMP
    echo "pen line $((x-size/3)) $((y+10)) $((x+size/3)) $((y+10))" | $LAMP
    echo "pen line $((x-size/6)) $((y+20)) $((x+size/6)) $((y+20))" | $LAMP
}

draw_battery() {
    local x=$1 y=$2 size=${3:-50}
    # Positive terminal (long line)
    echo "pen line $((x+size/2-10)) $((y-size/3)) $((x+size/2-10)) $((y+size/3))" | $LAMP
    # Negative terminal (short line)
    echo "pen line $((x+size/2+10)) $((y-size/5)) $((x+size/2+10)) $((y+size/5))" | $LAMP
    # Connection lines
    echo "pen line $x $y $((x+size/2-10)) $y" | $LAMP
    echo "pen line $((x+size/2+10)) $y $((x+size)) $y" | $LAMP
}

draw_diode() {
    local x=$1 y=$2 size=${3:-50}
    # Triangle
    echo "pen line $((x+size/2)) $((y-size/3)) $((x+size/2)) $((y+size/3))" | $LAMP
    echo "pen line $x $y $((x+size/2)) $((y-size/3))" | $LAMP
    echo "pen line $x $y $((x+size/2)) $((y+size/3))" | $LAMP
    # Vertical line
    echo "pen line $((x+size)) $((y-size/3)) $((x+size)) $((y+size/3))" | $LAMP
}

# Main command dispatcher
case "$1" in
    resistor)   draw_resistor "$2" "$3" "$4" ;;
    capacitor)  draw_capacitor "$2" "$3" "$4" ;;
    inductor)   draw_inductor "$2" "$3" "$4" ;;
    ground)     draw_ground "$2" "$3" "$4" ;;
    battery)    draw_battery "$2" "$3" "$4" ;;
    diode)      draw_diode "$2" "$3" "$4" ;;
    *)
        echo "Usage: $0 {resistor|capacitor|inductor|ground|battery|diode} x y [size]"
        echo "Example: $0 resistor 500 800 100"
        exit 1
        ;;
esac
