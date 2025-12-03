#!/usr/bin/env python3
"""
SVG to PEN Command Converter for RM2
Converts SVG files to PEN_DOWN/PEN_MOVE/PEN_UP format for injection

Coordinate System:
  Display: (0,0) at top-left, 1404x1872 pixels
  Wacom: Axes rotated 90 degrees (hardware)
  Conversion handled by C hook - use display coordinates here

Usage:
    svg2pen.py <input.svg> [scale] [output.txt]

Examples:
    svg2pen.py circuit.svg 2.5
    svg2pen.py circuit.svg 2.5 commands.txt
"""

import sys
import math

try:
    from svgpathtools import svg2paths
except ImportError:
    print("ERROR: svgpathtools not installed", file=sys.stderr)
    print("Install: pip install svgpathtools", file=sys.stderr)
    sys.exit(1)


class SVGToPenCommands:
    def __init__(self, scale=1.0, max_step=2.0):
        self.scale = scale
        self.max_step = max_step  # max distance between sampled points
        self.commands = []
    
    def sample_path(self, path):
        """Sample a path to generate points for drawing"""
        length = path.length()
        if length == 0:
            return []
        
        # Calculate number of samples
        num_samples = max(1, int(length / self.max_step))
        
        points = []
        for i in range(num_samples + 1):
            t = i / num_samples
            point = path.point(t)
            x = int(round(point.real * self.scale))
            y = int(round(point.imag * self.scale))
            points.append((x, y))
        
        # Deduplicate consecutive points
        clean = [points[0]]
        for p in points[1:]:
            if p != clean[-1]:
                clean.append(p)
        
        return clean
    
    def convert_svg(self, svg_file):
        """Convert SVG file to pen commands"""
        print(f"Reading SVG: {svg_file}", file=sys.stderr)
        
        try:
            paths, attributes = svg2paths(svg_file)
        except Exception as e:
            print(f"ERROR: Failed to parse SVG: {e}", file=sys.stderr)
            return []
        
        print(f"Found {len(paths)} paths", file=sys.stderr)
        
        total_points = 0
        
        for i, path in enumerate(paths):
            # Sample path to points
            points = self.sample_path(path)
            
            if not points:
                continue
            
            total_points += len(points)
            
            # Generate PEN commands for this path
            if len(points) > 1:
                # Pen down at first point
                x0, y0 = points[0]
                self.commands.append(f"PEN_DOWN {x0} {y0}")
                
                # Move to remaining points
                for x, y in points[1:]:
                    self.commands.append(f"PEN_MOVE {x} {y}")
                
                # Pen up
                self.commands.append("PEN_UP")
        
        print(f"Generated {total_points} points → {len(self.commands)} commands", file=sys.stderr)
        return self.commands
    
    def to_string(self):
        """Return commands as newline-separated string"""
        return '\n'.join(self.commands)


def main():
    if len(sys.argv) < 2:
        print("SVG to PEN Command Converter", file=sys.stderr)
        print("", file=sys.stderr)
        print("Usage: svg2pen.py <input.svg> [scale] [output.txt]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Arguments:", file=sys.stderr)
        print("  input.svg  - SVG circuit file from KiCAD", file=sys.stderr)
        print("  scale      - Scale factor (default 1.0, try 2.5 for readability)", file=sys.stderr)
        print("  output.txt - Output file (default stdout)", file=sys.stderr)
        print("", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  svg2pen.py circuit.svg", file=sys.stderr)
        print("  svg2pen.py circuit.svg 2.5", file=sys.stderr)
        print("  svg2pen.py circuit.svg 2.5 commands.txt", file=sys.stderr)
        sys.exit(1)
    
    svg_file = sys.argv[1]
    scale = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    if scale <= 0:
        print("ERROR: Scale must be positive", file=sys.stderr)
        sys.exit(1)
    
    # Convert
    converter = SVGToPenCommands(scale=scale)
    converter.convert_svg(svg_file)
    
    output = converter.to_string()
    
    # Write
    if output_file:
        try:
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"✓ Wrote {len(converter.commands)} commands to {output_file}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Cannot write {output_file}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output)


if __name__ == '__main__':
    main()
