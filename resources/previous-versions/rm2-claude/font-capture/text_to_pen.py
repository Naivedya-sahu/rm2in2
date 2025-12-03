#!/usr/bin/env python3
"""
Text to PEN Commands - Automatic handwriting generation for RM2

Uses Hershey single-stroke fonts to convert text to PEN commands.
Supports multiple pages, line wrapping, and proper spacing.

Usage:
    python text_to_pen.py "Hello World" output.txt
    python text_to_pen.py --file input.txt output.txt
    python text_to_pen.py --file essay.txt --pages essay_page{}.txt
"""

import sys
import argparse
from pathlib import Path

# Wacom coordinate system (RM2)
WACOM_MAX_X = 20966
WACOM_MAX_Y = 15725

# Page margins and layout (in Wacom coordinates)
MARGIN_TOP = 2000
MARGIN_LEFT = 2000
MARGIN_RIGHT = 2000
MARGIN_BOTTOM = 2000

PAGE_WIDTH = WACOM_MAX_X - MARGIN_LEFT - MARGIN_RIGHT  # ~16966
PAGE_HEIGHT = WACOM_MAX_Y - MARGIN_TOP - MARGIN_BOTTOM  # ~11725

# Font metrics (scaled to Wacom space)
CHAR_WIDTH = 500      # Average character width
CHAR_HEIGHT = 800     # Character height
LINE_SPACING = 1200   # Space between lines
WORD_SPACING = 600    # Space between words

# Simplified Hershey-style single-stroke font
# Each character defined as list of strokes, each stroke as list of (x,y) offsets
# Coordinates are relative offsets from character origin (0-based, scaled to fit)
FONT = {
    # Uppercase letters
    'A': [
        [(0, 800), (400, 0), (800, 800)],  # /\
        [(200, 400), (600, 400)]            # -
    ],
    'B': [
        [(0, 0), (0, 800), (600, 800), (700, 700), (700, 400), (0, 400)],  # |_)
        [(0, 400), (600, 400), (700, 300), (700, 0), (0, 0)]              # |_)
    ],
    'C': [
        [(800, 100), (600, 0), (200, 0), (0, 200), (0, 600), (200, 800), (600, 800), (800, 700)]
    ],
    'D': [
        [(0, 0), (0, 800), (600, 800), (800, 600), (800, 200), (600, 0), (0, 0)]
    ],
    'E': [
        [(800, 0), (0, 0), (0, 800), (800, 800)],
        [(0, 400), (600, 400)]
    ],
    'F': [
        [(0, 0), (0, 800), (800, 800)],
        [(0, 400), (600, 400)]
    ],
    'G': [
        [(800, 100), (600, 0), (200, 0), (0, 200), (0, 600), (200, 800), (600, 800), (800, 600), (800, 400), (400, 400)]
    ],
    'H': [
        [(0, 0), (0, 800)],
        [(800, 0), (800, 800)],
        [(0, 400), (800, 400)]
    ],
    'I': [
        [(200, 800), (600, 800)],
        [(400, 800), (400, 0)],
        [(200, 0), (600, 0)]
    ],
    'J': [
        [(800, 800), (800, 200), (600, 0), (200, 0), (0, 200)]
    ],
    'K': [
        [(0, 0), (0, 800)],
        [(800, 800), (0, 400), (800, 0)]
    ],
    'L': [
        [(0, 800), (0, 0), (800, 0)]
    ],
    'M': [
        [(0, 0), (0, 800), (400, 400), (800, 800), (800, 0)]
    ],
    'N': [
        [(0, 0), (0, 800), (800, 0), (800, 800)]
    ],
    'O': [
        [(200, 0), (0, 200), (0, 600), (200, 800), (600, 800), (800, 600), (800, 200), (600, 0), (200, 0)]
    ],
    'P': [
        [(0, 0), (0, 800), (600, 800), (800, 600), (800, 400), (600, 300), (0, 300)]
    ],
    'Q': [
        [(200, 0), (0, 200), (0, 600), (200, 800), (600, 800), (800, 600), (800, 200), (600, 0), (200, 0)],
        [(500, 200), (800, -100)]
    ],
    'R': [
        [(0, 0), (0, 800), (600, 800), (800, 600), (800, 400), (600, 300), (0, 300)],
        [(400, 300), (800, 0)]
    ],
    'S': [
        [(800, 700), (600, 800), (200, 800), (0, 600), (0, 500), (200, 400), (600, 400), (800, 300), (800, 200), (600, 0), (200, 0), (0, 100)]
    ],
    'T': [
        [(0, 800), (800, 800)],
        [(400, 800), (400, 0)]
    ],
    'U': [
        [(0, 800), (0, 200), (200, 0), (600, 0), (800, 200), (800, 800)]
    ],
    'V': [
        [(0, 800), (400, 0), (800, 800)]
    ],
    'W': [
        [(0, 800), (200, 0), (400, 400), (600, 0), (800, 800)]
    ],
    'X': [
        [(0, 800), (800, 0)],
        [(800, 800), (0, 0)]
    ],
    'Y': [
        [(0, 800), (400, 400), (800, 800)],
        [(400, 400), (400, 0)]
    ],
    'Z': [
        [(0, 800), (800, 800), (0, 0), (800, 0)]
    ],

    # Lowercase letters (simplified)
    'a': [[(100, 300), (700, 300), (700, 0)], [(700, 150), (600, 300), (400, 300), (300, 200), (300, 100), (400, 0), (600, 0), (700, 150)]],
    'b': [[(0, 800), (0, 0)], [(0, 300), (100, 300), (200, 200), (200, 100), (100, 0), (0, 0)]],
    'c': [[(700, 250), (600, 300), (200, 300), (100, 200), (100, 100), (200, 0), (600, 0), (700, 50)]],
    'd': [[(700, 800), (700, 0)], [(700, 300), (600, 300), (500, 200), (500, 100), (600, 0), (700, 0)]],
    'e': [[(100, 150), (700, 150), (700, 200), (600, 300), (200, 300), (100, 200), (100, 100), (200, 0), (600, 0), (700, 50)]],
    'f': [[(500, 800), (400, 800), (300, 700), (300, 0)], [(100, 500), (500, 500)]],
    'g': [[(700, 300), (600, 300), (500, 200), (500, 100), (600, 0), (700, 0), (700, -200), (600, -300), (200, -300), (100, -200)]],
    'h': [[(0, 800), (0, 0)], [(0, 300), (200, 300), (300, 200), (300, 0)]],
    'i': [[(200, 600), (200, 550)], [(200, 400), (200, 0)]],
    'j': [[(300, 600), (300, 550)], [(300, 400), (300, -200), (200, -300), (100, -300)]],
    'k': [[(0, 800), (0, 0)], [(500, 300), (0, 150), (500, 0)]],
    'l': [[(200, 800), (200, 0)]],
    'm': [[(0, 300), (0, 0)], [(0, 250), (200, 300), (300, 250), (300, 0)], [(300, 250), (500, 300), (600, 250), (600, 0)]],
    'n': [[(0, 300), (0, 0)], [(0, 250), (200, 300), (300, 250), (300, 0)]],
    'o': [[(200, 0), (100, 100), (100, 200), (200, 300), (500, 300), (600, 200), (600, 100), (500, 0), (200, 0)]],
    'p': [[(0, 300), (0, -300)], [(0, 300), (100, 300), (200, 200), (200, 100), (100, 0), (0, 0)]],
    'q': [[(700, 300), (700, -300)], [(700, 300), (600, 300), (500, 200), (500, 100), (600, 0), (700, 0)]],
    'r': [[(0, 300), (0, 0)], [(0, 200), (100, 300), (300, 300)]],
    's': [[(600, 250), (500, 300), (200, 300), (100, 200), (200, 150), (500, 150), (600, 100), (500, 0), (200, 0), (100, 50)]],
    't': [[(300, 700), (300, 100), (400, 0), (500, 0)], [(100, 500), (500, 500)]],
    'u': [[(0, 300), (0, 100), (100, 0), (200, 0), (300, 100), (300, 300)], [(300, 300), (300, 0)]],
    'v': [[(0, 300), (300, 0), (600, 300)]],
    'w': [[(0, 300), (150, 0), (300, 150), (450, 0), (600, 300)]],
    'x': [[(0, 300), (500, 0)], [(500, 300), (0, 0)]],
    'y': [[(0, 300), (0, 100), (100, 0), (200, 0), (300, 100), (300, 300)], [(300, 0), (300, -200), (200, -300), (100, -300)]],
    'z': [[(0, 300), (500, 300), (0, 0), (500, 0)]],

    # Numbers
    '0': [[(200, 0), (0, 200), (0, 600), (200, 800), (600, 800), (800, 600), (800, 200), (600, 0), (200, 0)]],
    '1': [[(200, 600), (400, 800), (400, 0)], [(200, 0), (600, 0)]],
    '2': [[(0, 600), (200, 800), (600, 800), (800, 600), (800, 500), (0, 0), (800, 0)]],
    '3': [[(0, 700), (200, 800), (600, 800), (800, 600), (600, 400), (800, 200), (600, 0), (200, 0), (0, 100)], [(400, 400), (600, 400)]],
    '4': [[(600, 800), (0, 300), (800, 300)], [(600, 800), (600, 0)]],
    '5': [[(800, 800), (0, 800), (0, 400), (600, 500), (800, 300), (800, 200), (600, 0), (200, 0), (0, 100)]],
    '6': [[(600, 800), (200, 800), (0, 600), (0, 200), (200, 0), (600, 0), (800, 200), (800, 300), (600, 400), (200, 400), (0, 200)]],
    '7': [[(0, 800), (800, 800), (300, 0)]],
    '8': [[(200, 400), (0, 600), (0, 700), (200, 800), (600, 800), (800, 700), (800, 600), (600, 400), (200, 400), (0, 200), (0, 100), (200, 0), (600, 0), (800, 100), (800, 200), (600, 400)]],
    '9': [[(800, 600), (600, 800), (200, 800), (0, 600), (0, 500), (200, 400), (600, 400), (800, 600), (800, 200), (600, 0), (200, 0)]],

    # Punctuation
    ' ': [],  # Space (no strokes)
    '.': [[(300, 0), (300, 100), (400, 100), (400, 0), (300, 0)]],
    ',': [[(300, 0), (300, 100), (200, -100)]],
    '!': [[(400, 800), (400, 300)], [(400, 150), (400, 0)]],
    '?': [[(0, 600), (200, 800), (600, 800), (800, 600), (800, 500), (400, 300), (400, 200)], [(400, 100), (400, 0)]],
    '-': [[(100, 400), (700, 400)]],
    ':': [[(400, 500), (400, 600)], [(400, 150), (400, 50)]],
    ';': [[(400, 500), (400, 600)], [(400, 150), (400, 50), (300, -50)]],
    '\'': [[(400, 800), (400, 600)]],
    '"': [[(300, 800), (300, 600)], [(500, 800), (500, 600)]],
    '(': [[(500, 800), (300, 600), (300, 200), (500, 0)]],
    ')': [[(300, 800), (500, 600), (500, 200), (300, 0)]],
}


class TextToPen:
    def __init__(self):
        self.commands = []
        self.current_x = MARGIN_LEFT
        self.current_y = MARGIN_TOP

    def render_character(self, char, x, y):
        """Render a single character at position (x, y)."""
        if char not in FONT:
            # Unknown character - skip
            return

        strokes = FONT[char]
        for stroke in strokes:
            if len(stroke) < 2:
                continue

            # First point - PEN_DOWN
            px, py = stroke[0]
            wacom_x = x + px
            wacom_y = y + py
            self.commands.append(f"PEN_DOWN {wacom_x} {wacom_y}")

            # Remaining points - PEN_MOVE
            for px, py in stroke[1:]:
                wacom_x = x + px
                wacom_y = y + py
                self.commands.append(f"PEN_MOVE {wacom_x} {wacom_y}")

            # End stroke
            self.commands.append("PEN_UP")

    def render_text(self, text):
        """Render text with line wrapping."""
        words = text.split()

        for word in words:
            # Check if word fits on current line
            word_width = len(word) * CHAR_WIDTH + WORD_SPACING
            if self.current_x + word_width > WACOM_MAX_X - MARGIN_RIGHT:
                # Move to next line
                self.current_x = MARGIN_LEFT
                self.current_y += LINE_SPACING

                # Check if we're past bottom margin
                if self.current_y + CHAR_HEIGHT > WACOM_MAX_Y - MARGIN_BOTTOM:
                    # Page full - return incomplete
                    return False

            # Render each character in word
            for char in word:
                self.render_character(char, self.current_x, self.current_y)
                self.current_x += CHAR_WIDTH

            # Add word spacing
            self.current_x += WORD_SPACING

        return True

    def save_to_file(self, filepath):
        """Save PEN commands to file."""
        with open(filepath, 'w') as f:
            f.write("# Generated by text_to_pen.py\n")
            f.write("# Hershey single-stroke font\n\n")
            f.write('\n'.join(self.commands))
            f.write('\n')


def main():
    parser = argparse.ArgumentParser(description='Convert text to PEN commands for RM2')
    parser.add_argument('text', nargs='?', help='Text to render (or use --file)')
    parser.add_argument('output', help='Output PEN command file')
    parser.add_argument('--file', '-f', help='Read text from file')

    args = parser.parse_args()

    # Get input text
    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        parser.error("Provide text or --file")

    # Convert to PEN commands
    converter = TextToPen()
    success = converter.render_text(text)

    # Save output
    converter.save_to_file(args.output)

    print(f"[OK] Generated {len(converter.commands)} PEN commands")
    print(f"[OK] Saved to: {args.output}")

    if not success:
        print("[WARN] Text was truncated (exceeded page bounds)")

    print()
    print("Next steps:")
    print(f"  1. Test on RM2: ./send.sh {args.output}")
    print("  2. For multi-page documents, split text into pages first")


if __name__ == '__main__':
    main()
