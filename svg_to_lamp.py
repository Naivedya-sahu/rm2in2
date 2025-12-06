#!/usr/bin/env python3
"""
SVG to lamp converter - Injects SVG vector graphics using lamp
Converts SVG paths to lamp pen commands for runtime injection
"""

import re
import math
import sys
import xml.etree.ElementTree as ET
from typing import List, Tuple

class SVGToLamp:
    def __init__(self, lamp_path="/opt/bin/lamp"):
        self.lamp_path = lamp_path
        self.commands = []

    def parse_svg_file(self, svg_path: str, scale: float = 1.0,
                       offset_x: float = 0, offset_y: float = 0):
        """Parse SVG file and convert to lamp commands"""
        tree = ET.parse(svg_path)
        root = tree.getroot()

        # Handle SVG namespace
        ns = {'svg': 'http://www.w3.org/2000/svg'}

        # Extract viewBox for scaling
        viewbox = root.get('viewBox')
        svg_width = float(root.get('width', 100))
        svg_height = float(root.get('height', 100))

        if viewbox:
            parts = viewbox.split()
            vb_width = float(parts[2])
            vb_height = float(parts[3])
            # Auto-scale to fit
            scale_x = scale * (svg_width / vb_width if vb_width > 0 else 1)
            scale_y = scale * (svg_height / vb_height if vb_height > 0 else 1)
        else:
            scale_x = scale_y = scale

        # Process all path elements
        for path in root.findall('.//svg:path', ns):
            d = path.get('d')
            if d:
                self.parse_path(d, scale_x, scale_y, offset_x, offset_y)

        # Process shapes (circle, rect, line, etc.)
        for circle in root.findall('.//svg:circle', ns):
            self.parse_circle(circle, scale_x, scale_y, offset_x, offset_y)

        for rect in root.findall('.//svg:rect', ns):
            self.parse_rect(rect, scale_x, scale_y, offset_x, offset_y)

        for line in root.findall('.//svg:line', ns):
            self.parse_line(line, scale_x, scale_y, offset_x, offset_y)

        return self.commands

    def transform_point(self, x, y, scale_x, scale_y, offset_x, offset_y):
        """Apply scaling and offset transformation"""
        return (
            int(x * scale_x + offset_x),
            int(y * scale_y + offset_y)
        )

    def parse_circle(self, circle, scale_x, scale_y, offset_x, offset_y):
        """Convert SVG circle to lamp circle command"""
        cx = float(circle.get('cx', 0))
        cy = float(circle.get('cy', 0))
        r = float(circle.get('r', 0))

        tx, ty = self.transform_point(cx, cy, scale_x, scale_y, offset_x, offset_y)
        tr = int(r * (scale_x + scale_y) / 2)  # Average scale for radius

        self.commands.append(f"pen circle {tx} {ty} {tr}")

    def parse_rect(self, rect, scale_x, scale_y, offset_x, offset_y):
        """Convert SVG rect to lamp rectangle command"""
        x = float(rect.get('x', 0))
        y = float(rect.get('y', 0))
        width = float(rect.get('width', 0))
        height = float(rect.get('height', 0))

        x1, y1 = self.transform_point(x, y, scale_x, scale_y, offset_x, offset_y)
        x2, y2 = self.transform_point(x + width, y + height,
                                       scale_x, scale_y, offset_x, offset_y)

        self.commands.append(f"pen rectangle {x1} {y1} {x2} {y2}")

    def parse_line(self, line, scale_x, scale_y, offset_x, offset_y):
        """Convert SVG line to lamp line command"""
        x1 = float(line.get('x1', 0))
        y1 = float(line.get('y1', 0))
        x2 = float(line.get('x2', 0))
        y2 = float(line.get('y2', 0))

        tx1, ty1 = self.transform_point(x1, y1, scale_x, scale_y, offset_x, offset_y)
        tx2, ty2 = self.transform_point(x2, y2, scale_x, scale_y, offset_x, offset_y)

        self.commands.append(f"pen line {tx1} {ty1} {tx2} {ty2}")

    def parse_path(self, path_data: str, scale_x, scale_y, offset_x, offset_y):
        """Convert SVG path to lamp commands"""
        # Parse SVG path commands
        # Supports: M (moveto), L (lineto), H (horizontal), V (vertical),
        # C (cubic bezier), Q (quadratic bezier), Z (closepath)

        commands = re.findall(r'[MmLlHhVvCcSsQqTtAaZz][^MmLlHhVvCcSsQqTtAaZz]*', path_data)

        current_x, current_y = 0, 0
        start_x, start_y = 0, 0
        pen_down = False

        for cmd in commands:
            cmd_type = cmd[0]
            params = re.findall(r'-?\d+\.?\d*', cmd[1:])
            params = [float(p) for p in params]

            # Moveto
            if cmd_type in 'Mm':
                if cmd_type == 'M':  # Absolute
                    current_x, current_y = params[0], params[1]
                else:  # Relative
                    current_x += params[0]
                    current_y += params[1]
                start_x, start_y = current_x, current_y
                pen_down = False

            # Lineto
            elif cmd_type in 'Ll':
                if not pen_down:
                    tx, ty = self.transform_point(current_x, current_y,
                                                   scale_x, scale_y, offset_x, offset_y)
                    self.commands.append(f"pen down {tx} {ty}")
                    pen_down = True

                for i in range(0, len(params), 2):
                    if cmd_type == 'L':  # Absolute
                        next_x, next_y = params[i], params[i+1]
                    else:  # Relative
                        next_x = current_x + params[i]
                        next_y = current_y + params[i+1]

                    tx, ty = self.transform_point(next_x, next_y,
                                                   scale_x, scale_y, offset_x, offset_y)
                    self.commands.append(f"pen move {tx} {ty}")
                    current_x, current_y = next_x, next_y

            # Horizontal line
            elif cmd_type in 'Hh':
                if not pen_down:
                    tx, ty = self.transform_point(current_x, current_y,
                                                   scale_x, scale_y, offset_x, offset_y)
                    self.commands.append(f"pen down {tx} {ty}")
                    pen_down = True

                for x in params:
                    next_x = x if cmd_type == 'H' else current_x + x
                    tx, ty = self.transform_point(next_x, current_y,
                                                   scale_x, scale_y, offset_x, offset_y)
                    self.commands.append(f"pen move {tx} {ty}")
                    current_x = next_x

            # Vertical line
            elif cmd_type in 'Vv':
                if not pen_down:
                    tx, ty = self.transform_point(current_x, current_y,
                                                   scale_x, scale_y, offset_x, offset_y)
                    self.commands.append(f"pen down {tx} {ty}")
                    pen_down = True

                for y in params:
                    next_y = y if cmd_type == 'V' else current_y + y
                    tx, ty = self.transform_point(current_x, next_y,
                                                   scale_x, scale_y, offset_x, offset_y)
                    self.commands.append(f"pen move {tx} {ty}")
                    current_y = next_y

            # Cubic Bezier (approximate with line segments)
            elif cmd_type in 'Cc':
                if not pen_down:
                    tx, ty = self.transform_point(current_x, current_y,
                                                   scale_x, scale_y, offset_x, offset_y)
                    self.commands.append(f"pen down {tx} {ty}")
                    pen_down = True

                for i in range(0, len(params), 6):
                    if cmd_type == 'C':
                        cp1x, cp1y = params[i], params[i+1]
                        cp2x, cp2y = params[i+2], params[i+3]
                        end_x, end_y = params[i+4], params[i+5]
                    else:
                        cp1x = current_x + params[i]
                        cp1y = current_y + params[i+1]
                        cp2x = current_x + params[i+2]
                        cp2y = current_y + params[i+3]
                        end_x = current_x + params[i+4]
                        end_y = current_y + params[i+5]

                    # Approximate bezier with line segments
                    steps = 10
                    for t in range(1, steps + 1):
                        t_norm = t / steps
                        # Cubic bezier formula
                        bx = (1-t_norm)**3 * current_x + \
                             3 * (1-t_norm)**2 * t_norm * cp1x + \
                             3 * (1-t_norm) * t_norm**2 * cp2x + \
                             t_norm**3 * end_x
                        by = (1-t_norm)**3 * current_y + \
                             3 * (1-t_norm)**2 * t_norm * cp1y + \
                             3 * (1-t_norm) * t_norm**2 * cp2y + \
                             t_norm**3 * end_y

                        tx, ty = self.transform_point(bx, by, scale_x, scale_y,
                                                       offset_x, offset_y)
                        self.commands.append(f"pen move {tx} {ty}")

                    current_x, current_y = end_x, end_y

            # Close path
            elif cmd_type in 'Zz':
                if pen_down:
                    tx, ty = self.transform_point(start_x, start_y,
                                                   scale_x, scale_y, offset_x, offset_y)
                    self.commands.append(f"pen move {tx} {ty}")
                    self.commands.append("pen up")
                    pen_down = False

        if pen_down:
            self.commands.append("pen up")

    def inject(self):
        """Send all commands to lamp"""
        import subprocess
        for cmd in self.commands:
            subprocess.run(
                f"echo '{cmd}' | {self.lamp_path}",
                shell=True
            )

    def save_script(self, output_path: str):
        """Save commands as a shell script"""
        with open(output_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"# Generated lamp script from SVG\n\n")
            for cmd in self.commands:
                f.write(f"echo '{cmd}' | {self.lamp_path}\n")

def main():
    if len(sys.argv) < 4:
        print("Usage: svg_to_lamp.py <svg_file> <x> <y> [scale]")
        print("  svg_file: Path to SVG file")
        print("  x, y: Position to draw on screen")
        print("  scale: Optional scale factor (default: 1.0)")
        sys.exit(1)

    svg_file = sys.argv[1]
    x = float(sys.argv[2])
    y = float(sys.argv[3])
    scale = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0

    converter = SVGToLamp()
    converter.parse_svg_file(svg_file, scale=scale, offset_x=x, offset_y=y)

    # Print commands (can be piped to lamp)
    for cmd in converter.commands:
        print(cmd)

if __name__ == "__main__":
    main()
