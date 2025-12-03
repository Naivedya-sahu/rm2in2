#!/usr/bin/env python3
"""
Text to PEN Commands Converter
Converts text strings into handwriting-style PEN commands
"""

import sys
import argparse
from letter_strokes import LETTERS, LETTER_SPACING, WORD_SPACING, get_letter_strokes, get_letter_width


def text_to_pen(text, start_x=100, start_y=200, scale=1.0, line_height=100):
    """
    Convert text string to PEN commands

    Args:
        text: Input text string
        start_x: Starting X position
        start_y: Starting Y position
        scale: Scale factor for letters
        line_height: Vertical spacing for newlines

    Returns:
        List of PEN command strings
    """
    commands = []
    cursor_x = start_x
    cursor_y = start_y

    for char in text:
        # Handle newline
        if char == '\n':
            cursor_x = start_x
            cursor_y += int(line_height * scale)
            continue

        # Get letter strokes
        strokes = get_letter_strokes(char)

        if strokes is None:
            # Unknown character, skip
            cursor_x += int(30 * scale)
            continue

        if char == ' ':
            # Space
            cursor_x += int(WORD_SPACING * scale)
            continue

        # Draw each stroke
        for stroke in strokes:
            if not stroke:
                continue

            # First point: PEN_DOWN
            x, y = stroke[0]
            abs_x = cursor_x + int(x * scale)
            abs_y = cursor_y + int(y * scale)
            commands.append(f"PEN_DOWN {abs_x} {abs_y}")

            # Remaining points: PEN_MOVE
            for x, y in stroke[1:]:
                abs_x = cursor_x + int(x * scale)
                abs_y = cursor_y + int(y * scale)
                commands.append(f"PEN_MOVE {abs_x} {abs_y}")

            # End stroke
            commands.append("PEN_UP")

        # Advance cursor
        cursor_x += int(get_letter_width(char) * scale)

    return commands


def calculate_text_bounds(text, scale=1.0, line_height=100):
    """Calculate the bounding box of rendered text"""

    if not text:
        return 0, 0

    lines = text.split('\n')

    # Width: longest line
    max_width = 0
    for line in lines:
        width = 0
        for char in line:
            width += get_letter_width(char)
        max_width = max(max_width, width)

    # Height: number of lines
    height = 70 + (len(lines) - 1) * line_height

    return int(max_width * scale), int(height * scale)


def center_text(text, display_width=1404, display_height=1872, scale=1.0, line_height=100):
    """Calculate start position to center text on display"""

    width, height = calculate_text_bounds(text, scale, line_height)

    start_x = (display_width - width) // 2
    start_y = (display_height - height) // 2

    return start_x, start_y


def main():
    parser = argparse.ArgumentParser(
        description='Convert text to PEN commands for RM2 injection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Simple text
  python text2pen.py "Hello World" -o hello.txt

  # Centered text with scaling
  python text2pen.py "Hello RM2!" --center --scale 1.5 -o hello.txt

  # Multi-line text
  python text2pen.py "Line 1\\nLine 2\\nLine 3" --center -o lines.txt

  # Custom position
  python text2pen.py "Test" --pos 200 300 --scale 2.0 -o test.txt

  # Show bounds (no output)
  python text2pen.py "Hello World" --bounds

Supported characters:
  - Uppercase: A-Z
  - Lowercase: a-z
  - Numbers: 0-9
  - Special: . , ! ? - ' "
  - Space and newline
        '''
    )

    parser.add_argument('text', help='Text to convert')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--scale', type=float, default=1.0, help='Scale factor (default: 1.0)')
    parser.add_argument('--pos', nargs=2, type=int, metavar=('X', 'Y'),
                        help='Start position (default: 100 200)')
    parser.add_argument('--center', action='store_true', help='Center text on display')
    parser.add_argument('--line-height', type=int, default=100,
                        help='Line height for multi-line text (default: 100)')
    parser.add_argument('--bounds', action='store_true', help='Show text bounds and exit')
    parser.add_argument('--stats', action='store_true', help='Show statistics')

    args = parser.parse_args()

    # Handle escape sequences in text
    text = args.text.replace('\\n', '\n').replace('\\t', '    ')

    # Calculate bounds if requested
    if args.bounds:
        width, height = calculate_text_bounds(text, args.scale, args.line_height)
        print(f"Text: {repr(args.text)}")
        print(f"Bounds: {width}x{height} pixels")
        print(f"Scale: {args.scale}")
        if args.center:
            start_x, start_y = center_text(text, scale=args.scale, line_height=args.line_height)
            print(f"Centered position: ({start_x}, {start_y})")
        return 0

    # Determine start position
    if args.center:
        start_x, start_y = center_text(text, scale=args.scale, line_height=args.line_height)
    elif args.pos:
        start_x, start_y = args.pos
    else:
        start_x, start_y = 100, 200

    # Generate commands
    commands = text_to_pen(text, start_x, start_y, args.scale, args.line_height)

    if not commands:
        print("Error: No commands generated (empty text or unsupported characters)", file=sys.stderr)
        return 1

    # Output
    output = '\n'.join(commands) + '\n'

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)

        # Show stats
        if args.stats or True:  # Always show stats for file output
            char_count = len([c for c in text if c != '\n' and c != ' '])
            print(f"✓ Text: {repr(text)}", file=sys.stderr)
            print(f"✓ Characters: {char_count}", file=sys.stderr)
            print(f"✓ Commands: {len(commands)}", file=sys.stderr)
            print(f"✓ Position: ({start_x}, {start_y})", file=sys.stderr)
            print(f"✓ Scale: {args.scale}", file=sys.stderr)
            print(f"✓ Saved to: {args.output}", file=sys.stderr)
    else:
        print(output)

        if args.stats:
            char_count = len([c for c in text if c != '\n' and c != ' '])
            print(f"# Characters: {char_count}, Commands: {len(commands)}", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
