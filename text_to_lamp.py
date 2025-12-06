#!/usr/bin/env python3
"""
Text to lamp converter - Renders text as vector strokes
Simple stroke-based font for labels in electrical diagrams
"""

import sys

class StrokeFontRenderer:
    """Simple 7-segment style stroke font for lamp"""

    def __init__(self, char_width=30, char_height=50, stroke_width=4):
        self.char_width = char_width
        self.char_height = char_height
        self.stroke_width = stroke_width
        self.char_spacing = 10

        # Define characters as stroke segments
        # Each segment is a line: (x1, y1, x2, y2) in normalized 0-1 coords
        self.glyphs = {
            'A': [(0, 1, 0.5, 0), (0.5, 0, 1, 1), (0.2, 0.5, 0.8, 0.5)],
            'B': [(0, 0, 0, 1), (0, 0, 0.7, 0), (0.7, 0, 0.7, 0.5),
                  (0, 0.5, 0.7, 0.5), (0.7, 0.5, 0.7, 1), (0, 1, 0.7, 1)],
            'C': [(1, 0, 0, 0), (0, 0, 0, 1), (0, 1, 1, 1)],
            'D': [(0, 0, 0, 1), (0, 0, 0.7, 0), (0.7, 0, 1, 0.3),
                  (1, 0.3, 1, 0.7), (1, 0.7, 0.7, 1), (0.7, 1, 0, 1)],
            'E': [(1, 0, 0, 0), (0, 0, 0, 1), (0, 1, 1, 1), (0, 0.5, 0.7, 0.5)],
            'F': [(1, 0, 0, 0), (0, 0, 0, 1), (0, 0.5, 0.7, 0.5)],
            'G': [(1, 0, 0, 0), (0, 0, 0, 1), (0, 1, 1, 1),
                  (1, 1, 1, 0.5), (1, 0.5, 0.5, 0.5)],
            'H': [(0, 0, 0, 1), (1, 0, 1, 1), (0, 0.5, 1, 0.5)],
            'I': [(0, 0, 1, 0), (0.5, 0, 0.5, 1), (0, 1, 1, 1)],
            'L': [(0, 0, 0, 1), (0, 1, 1, 1)],
            'M': [(0, 1, 0, 0), (0, 0, 0.5, 0.4), (0.5, 0.4, 1, 0), (1, 0, 1, 1)],
            'N': [(0, 1, 0, 0), (0, 0, 1, 1), (1, 1, 1, 0)],
            'O': [(0, 0, 1, 0), (1, 0, 1, 1), (1, 1, 0, 1), (0, 1, 0, 0)],
            'P': [(0, 1, 0, 0), (0, 0, 1, 0), (1, 0, 1, 0.5), (1, 0.5, 0, 0.5)],
            'R': [(0, 1, 0, 0), (0, 0, 1, 0), (1, 0, 1, 0.5),
                  (1, 0.5, 0, 0.5), (0.5, 0.5, 1, 1)],
            'S': [(1, 0, 0, 0), (0, 0, 0, 0.5), (0, 0.5, 1, 0.5),
                  (1, 0.5, 1, 1), (1, 1, 0, 1)],
            'T': [(0, 0, 1, 0), (0.5, 0, 0.5, 1)],
            'U': [(0, 0, 0, 1), (0, 1, 1, 1), (1, 1, 1, 0)],
            'V': [(0, 0, 0.5, 1), (0.5, 1, 1, 0)],
            'W': [(0, 0, 0, 1), (0, 1, 0.5, 0.6), (0.5, 0.6, 1, 1), (1, 1, 1, 0)],
            'Y': [(0, 0, 0.5, 0.5), (1, 0, 0.5, 0.5), (0.5, 0.5, 0.5, 1)],
            'Z': [(0, 0, 1, 0), (1, 0, 0, 1), (0, 1, 1, 1)],

            # Numbers
            '0': [(0, 0, 1, 0), (1, 0, 1, 1), (1, 1, 0, 1), (0, 1, 0, 0), (0, 0, 1, 1)],
            '1': [(0.5, 0, 0.5, 1), (0, 1, 1, 1)],
            '2': [(0, 0, 1, 0), (1, 0, 1, 0.5), (1, 0.5, 0, 0.5),
                  (0, 0.5, 0, 1), (0, 1, 1, 1)],
            '3': [(0, 0, 1, 0), (1, 0, 1, 0.5), (0.3, 0.5, 1, 0.5),
                  (1, 0.5, 1, 1), (1, 1, 0, 1)],
            '4': [(0, 0, 0, 0.5), (0, 0.5, 1, 0.5), (1, 0, 1, 1)],
            '5': [(1, 0, 0, 0), (0, 0, 0, 0.5), (0, 0.5, 1, 0.5),
                  (1, 0.5, 1, 1), (1, 1, 0, 1)],
            '6': [(1, 0, 0, 0), (0, 0, 0, 1), (0, 1, 1, 1),
                  (1, 1, 1, 0.5), (1, 0.5, 0, 0.5)],
            '7': [(0, 0, 1, 0), (1, 0, 1, 1)],
            '8': [(0, 0, 1, 0), (1, 0, 1, 1), (1, 1, 0, 1), (0, 1, 0, 0), (0, 0.5, 1, 0.5)],
            '9': [(0, 1, 0, 0.5), (0, 0.5, 1, 0.5), (1, 0.5, 1, 1),
                  (1, 1, 0, 1), (0, 1, 0, 0.5), (1, 0, 1, 0.5)],

            # Special characters
            '+': [(0.5, 0.2, 0.5, 0.8), (0.2, 0.5, 0.8, 0.5)],
            '-': [(0.2, 0.5, 0.8, 0.5)],
            'Ω': [(0.2, 0, 0, 0.3), (0, 0.3, 0, 0.7), (0, 0.7, 0.2, 1),
                  (0.2, 1, 0.8, 1), (0.8, 1, 1, 0.7), (1, 0.7, 1, 0.3),
                  (1, 0.3, 0.8, 0), (0.2, 1, 0.2, 0.8), (0.8, 1, 0.8, 0.8)],
            'μ': [(0, 0, 0, 1), (0, 1, 0.5, 0.9), (0.5, 0.9, 1, 1),
                  (1, 1, 1, 0), (0.5, 0.4, 0.5, 1.2)],
        }

    def render_text(self, text, x, y, lamp_path="/opt/bin/lamp"):
        """Render text at position (x, y) and return lamp commands"""
        commands = []
        current_x = x

        for char in text.upper():
            if char == ' ':
                current_x += self.char_width + self.char_spacing
                continue

            if char not in self.glyphs:
                # Unknown character, skip
                current_x += self.char_width + self.char_spacing
                continue

            # Draw character
            for stroke in self.glyphs[char]:
                x1 = int(current_x + stroke[0] * self.char_width)
                y1 = int(y + stroke[1] * self.char_height)
                x2 = int(current_x + stroke[2] * self.char_width)
                y2 = int(y + stroke[3] * self.char_height)

                commands.append(f"pen line {x1} {y1} {x2} {y2}")

            current_x += self.char_width + self.char_spacing

        return commands

    def get_text_width(self, text):
        """Calculate total width of rendered text"""
        char_count = len([c for c in text if c != ' '])
        space_count = text.count(' ')
        return (char_count * self.char_width +
                (char_count - 1) * self.char_spacing +
                space_count * (self.char_width + self.char_spacing))

def main():
    if len(sys.argv) < 4:
        print("Usage: text_to_lamp.py <text> <x> <y> [size]")
        print("  text: Text to render")
        print("  x, y: Position on screen")
        print("  size: Optional size multiplier (default: 1.0)")
        sys.exit(1)

    text = sys.argv[1]
    x = int(sys.argv[2])
    y = int(sys.argv[3])
    size = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0

    renderer = StrokeFontRenderer(
        char_width=int(30 * size),
        char_height=int(50 * size)
    )

    commands = renderer.render_text(text, x, y)

    # Output lamp commands
    for cmd in commands:
        print(cmd)

if __name__ == "__main__":
    main()
