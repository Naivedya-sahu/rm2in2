#!/usr/bin/env python3
"""
Convert PEN commands to Inkscape-compatible SVG with editable nodes.

Usage:
    python pen_to_svg.py input.txt output.svg

The output SVG will have:
- Each stroke as a separate path
- Nodes visible and editable in Inkscape
- Proper coordinate mapping from Wacom to SVG space
- Stroke colors for easy identification
"""

import sys
import re
from pathlib import Path

# Wacom coordinate system (RM2 rotated 90°)
WACOM_MAX_X = 20966
WACOM_MAX_Y = 15725

# RM2 display dimensions
RM2_WIDTH = 1404
RM2_HEIGHT = 1872

# SVG output dimensions (match RM2 portrait)
SVG_WIDTH = 1404
SVG_HEIGHT = 1872


class PenToSVG:
    def __init__(self):
        self.strokes = []
        self.current_stroke = []

    def wacom_to_svg(self, wacom_x, wacom_y):
        """Convert PEN command coordinates to SVG coordinates.

        PEN commands are in portrait orientation (before inject.c transform).
        Direct scaling to SVG portrait coordinates.
        """
        # Direct mapping: PEN portrait → SVG portrait
        svg_x = (wacom_x / WACOM_MAX_X) * SVG_WIDTH
        svg_y = (wacom_y / WACOM_MAX_Y) * SVG_HEIGHT
        return svg_x, svg_y

    def parse_pen_file(self, filepath):
        """Parse PEN command file."""
        print(f"[INFO] Reading PEN commands from: {filepath}")

        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if len(parts) < 1:
                    continue

                command = parts[0]

                if command == 'PEN_DOWN' and len(parts) >= 3:
                    # Start new stroke
                    if self.current_stroke:
                        self.strokes.append(self.current_stroke)
                    self.current_stroke = []

                    x = int(parts[1])
                    y = int(parts[2])
                    self.current_stroke.append((x, y))

                elif command == 'PEN_MOVE' and len(parts) >= 3:
                    # Add point to current stroke
                    x = int(parts[1])
                    y = int(parts[2])
                    self.current_stroke.append((x, y))

                elif command == 'PEN_UP':
                    # End current stroke
                    if self.current_stroke:
                        self.strokes.append(self.current_stroke)
                        self.current_stroke = []

        # Handle last stroke if file doesn't end with PEN_UP
        if self.current_stroke:
            self.strokes.append(self.current_stroke)

        print(f"[INFO] Parsed {len(self.strokes)} strokes")
        total_points = sum(len(stroke) for stroke in self.strokes)
        print(f"[INFO] Total points: {total_points}")

    def generate_svg(self, output_path):
        """Generate Inkscape-compatible SVG."""
        print(f"[INFO] Generating SVG: {output_path}")

        # Define stroke colors (cycle through them)
        colors = [
            '#0066CC', '#CC0066', '#00CC66', '#CC6600',
            '#6600CC', '#00CCCC', '#CC0000', '#0000CC'
        ]

        svg_lines = []
        svg_lines.append('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
        svg_lines.append('<svg')
        svg_lines.append('   xmlns:dc="http://purl.org/dc/elements/1.1/"')
        svg_lines.append('   xmlns:cc="http://creativecommons.org/ns#"')
        svg_lines.append('   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"')
        svg_lines.append('   xmlns:svg="http://www.w3.org/2000/svg"')
        svg_lines.append('   xmlns="http://www.w3.org/2000/svg"')
        svg_lines.append('   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"')
        svg_lines.append(f'   width="{SVG_WIDTH}"')
        svg_lines.append(f'   height="{SVG_HEIGHT}"')
        svg_lines.append(f'   viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}"')
        svg_lines.append('   version="1.1">')
        svg_lines.append('')
        svg_lines.append('  <metadata>')
        svg_lines.append('    <rdf:RDF>')
        svg_lines.append('      <cc:Work rdf:about="">')
        svg_lines.append('        <dc:format>image/svg+xml</dc:format>')
        svg_lines.append('        <dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage" />')
        svg_lines.append('        <dc:title>PEN Commands converted to SVG</dc:title>')
        svg_lines.append('      </cc:Work>')
        svg_lines.append('    </rdf:RDF>')
        svg_lines.append('  </metadata>')
        svg_lines.append('')
        svg_lines.append('  <g id="layer1" inkscape:label="Strokes" inkscape:groupmode="layer">')

        # Convert each stroke to a path
        for stroke_idx, stroke in enumerate(self.strokes):
            if len(stroke) < 2:
                continue

            color = colors[stroke_idx % len(colors)]

            # Build path data (use integers only - no decimals)
            path_data = []
            for point_idx, (wx, wy) in enumerate(stroke):
                sx, sy = self.wacom_to_svg(wx, wy)
                # Round to integers to avoid decimal precision issues
                sx = int(round(sx))
                sy = int(round(sy))
                if point_idx == 0:
                    path_data.append(f'M {sx},{sy}')
                else:
                    path_data.append(f'L {sx},{sy}')

            path_string = ' '.join(path_data)

            svg_lines.append(f'    <path')
            svg_lines.append(f'       id="stroke_{stroke_idx + 1}"')
            svg_lines.append(f'       inkscape:label="Stroke {stroke_idx + 1} ({len(stroke)} points)"')
            svg_lines.append(f'       style="fill:none;stroke:{color};stroke-width:2;stroke-linecap:round;stroke-linejoin:round"')
            svg_lines.append(f'       d="{path_string}" />')

        svg_lines.append('  </g>')
        svg_lines.append('</svg>')

        with open(output_path, 'w') as f:
            f.write('\n'.join(svg_lines))

        print(f"[OK] SVG saved: {output_path}")
        print(f"[INFO] Open in Inkscape to edit nodes")


def main():
    if len(sys.argv) != 3:
        print("Usage: python pen_to_svg.py input.txt output.svg")
        print("")
        print("Convert PEN commands to Inkscape-editable SVG")
        print("")
        print("Example:")
        print("  python pen_to_svg.py ../testing-tools/pen_hello.txt hello.svg")
        print("  inkscape hello.svg")
        print("  # Edit nodes in Inkscape")
        print("  # Save and convert back with svg_to_pen.py")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not Path(input_file).exists():
        print(f"[ERROR] Input file not found: {input_file}")
        sys.exit(1)

    converter = PenToSVG()
    converter.parse_pen_file(input_file)
    converter.generate_svg(output_file)

    print("")
    print("Next steps:")
    print(f"  1. Open in Inkscape: inkscape {output_file}")
    print("  2. Edit nodes (press N key in Inkscape)")
    print("  3. Move/delete/add nodes as needed")
    print("  4. Save the file")
    print(f"  5. Convert back: python svg_to_pen.py {output_file} output.txt")


if __name__ == '__main__':
    main()
