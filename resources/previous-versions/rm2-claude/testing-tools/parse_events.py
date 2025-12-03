#!/usr/bin/env python3
"""
Parse evtest output into PEN commands
Analyzes real pen input to understand stroke patterns
"""

import sys
import re

# Wacom coordinate system (from inject.c)
WACOM_MAX_X = 15725
WACOM_MAX_Y = 20967
RM2_WIDTH = 1404
RM2_HEIGHT = 1872

def wacom_to_display(wx, wy):
    """Convert Wacom coordinates to display coordinates"""
    # From inject.c: Display X → Wacom Y, Display Y → Wacom X (90° rotation)
    # Reverse: Wacom X → Display Y, Wacom Y → Display X
    x = int(wy * RM2_WIDTH / WACOM_MAX_Y)
    y = int(wx * RM2_HEIGHT / WACOM_MAX_X)
    return x, y

def parse_evtest(input_file):
    """Parse evtest output into strokes"""

    with open(input_file, 'r') as f:
        lines = f.readlines()

    strokes = []
    current_stroke = []
    current_x = None
    current_y = None
    pen_down = False

    for line in lines:
        # Look for event lines: "Event: time 1234.567890, type X (EV_ABS), code Y (ABS_X), value Z"
        match = re.search(r'type \d+ \(EV_ABS\), code \d+ \(ABS_([XY])\), value (\d+)', line)
        if match:
            axis = match.group(1)
            value = int(match.group(2))

            if axis == 'X':
                current_x = value
            elif axis == 'Y':
                current_y = value

        # Look for BTN_TOUCH events
        match_touch = re.search(r'type \d+ \(EV_KEY\), code \d+ \(BTN_TOUCH\), value (\d+)', line)
        if match_touch:
            touch_value = int(match_touch.group(1))

            if touch_value == 1:  # Pen down
                pen_down = True
                if current_x is not None and current_y is not None:
                    x, y = wacom_to_display(current_x, current_y)
                    current_stroke = [(x, y)]

            elif touch_value == 0:  # Pen up
                pen_down = False
                if current_stroke:
                    strokes.append(current_stroke)
                    current_stroke = []

        # Look for SYN_REPORT (marks end of event batch)
        if 'SYN_REPORT' in line:
            if pen_down and current_x is not None and current_y is not None:
                x, y = wacom_to_display(current_x, current_y)
                if not current_stroke or (x, y) != current_stroke[-1]:
                    current_stroke.append((x, y))

    # Add last stroke if exists
    if current_stroke:
        strokes.append(current_stroke)

    return strokes

def analyze_strokes(strokes):
    """Analyze stroke patterns"""

    print("Stroke Analysis")
    print("=" * 60)
    print(f"Total strokes: {len(strokes)}")
    print()

    for i, stroke in enumerate(strokes):
        print(f"Stroke {i + 1}:")
        print(f"  Points: {len(stroke)}")

        if len(stroke) >= 2:
            # Calculate stroke length
            total_length = 0
            for j in range(1, len(stroke)):
                x1, y1 = stroke[j - 1]
                x2, y2 = stroke[j]
                dx = x2 - x1
                dy = y2 - y1
                length = (dx*dx + dy*dy) ** 0.5
                total_length += length

            print(f"  Length: {total_length:.1f} pixels")

            # Calculate average point spacing
            avg_spacing = total_length / (len(stroke) - 1) if len(stroke) > 1 else 0
            print(f"  Avg point spacing: {avg_spacing:.2f} pixels")

            # Bounds
            xs = [p[0] for p in stroke]
            ys = [p[1] for p in stroke]
            print(f"  Bounds: ({min(xs)}, {min(ys)}) to ({max(xs)}, {max(ys)})")

        print()

def strokes_to_pen(strokes, output_file=None):
    """Convert strokes to PEN commands"""

    commands = []

    for stroke in strokes:
        if not stroke:
            continue

        # First point: PEN_DOWN
        x, y = stroke[0]
        commands.append(f"PEN_DOWN {x} {y}")

        # Middle points: PEN_MOVE
        for x, y in stroke[1:]:
            commands.append(f"PEN_MOVE {x} {y}")

        # End stroke
        commands.append("PEN_UP")

    output = '\n'.join(commands) + '\n'

    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"✓ Saved {len(commands)} commands to: {output_file}")
    else:
        print(output)

    return commands

def main():
    if len(sys.argv) < 2:
        print("Parse evtest output into PEN commands")
        print()
        print("Usage:")
        print("  python parse_events.py <evtest_output.txt> [options]")
        print()
        print("Options:")
        print("  -o <file>       Output PEN commands to file")
        print("  --analyze       Show stroke analysis")
        print()
        print("Workflow:")
        print("  1. On RM2: ./capture_events.sh")
        print("  2. Write 'Hello' on screen")
        print("  3. Download: scp root@10.11.99.1:/tmp/pen_capture.txt .")
        print("  4. Parse: python parse_events.py pen_capture.txt --analyze -o hello_real.txt")
        return 1

    input_file = sys.argv[1]
    output_file = None
    show_analysis = False

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '-o' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        elif arg == '--analyze':
            show_analysis = True
            i += 1
        else:
            print(f"Unknown argument: {arg}")
            return 1

    # Parse events
    strokes = parse_evtest(input_file)

    if not strokes:
        print("Error: No strokes found in input file")
        return 1

    # Show analysis if requested
    if show_analysis:
        analyze_strokes(strokes)
        print()

    # Convert to PEN commands
    strokes_to_pen(strokes, output_file)

    return 0

if __name__ == '__main__':
    sys.exit(main())
