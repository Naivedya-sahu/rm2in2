#!/usr/bin/env python3
"""
SVG to PEN Command Converter
Converts SVG circuit diagrams to PEN_DOWN/PEN_MOVE/PEN_UP format
Outputs directly as pen commands—ready to inject into RM2

Usage:
    svg2pen.py <input.svg> <scale> [output.txt]

Examples:
    svg2pen.py circuit.svg 2.5
    svg2pen.py circuit.svg 2.5 commands.txt
"""

import sys
import numpy as np
from typing import List, Tuple

try:
    from svgpathtools import svg2paths, Path, Line, CubicBezier, QuadraticBezier, Arc
except ImportError:
    print("ERROR: svgpathtools not installed")
    print("Install: pip install svgpathtools shapely numpy --break-system-packages")
    sys.exit(1)


class SVGToPenCommands:
    """Convert SVG paths to PEN_* command sequence"""
    
    def __init__(self, scale=1.0, max_error=1.0):
        """
        Args:
            scale: Scale factor for all coordinates
            max_error: Max error for adaptive bezier sampling (pixels)
        """
        self.scale = scale
        self.max_error = max_error
        self.commands = []
    
    def adaptive_bezier_sample(self, curve, max_error=1.0, depth=0, max_depth=10):
        """
        Adaptive bezier curve sampling.
        Recursively subdivides curve until error below threshold.
        Returns list of (x, y) points.
        """
        if depth > max_depth:
            point = curve.point(1)
            return [(point.real, point.imag)]
        
        # Evaluate curve at endpoints and midpoint
        p0 = curve.point(0)
        pm = curve.point(0.5)
        p1 = curve.point(1)
        
        # Check if midpoint is close to straight line
        line_midpoint = (p0 + p1) / 2
        error = abs(pm - line_midpoint)
        
        if error <= max_error:
            # Good approximation
            return [(p1.real, p1.imag)]
        else:
            # Subdivide recursively
            left, right = curve.split(0.5)
            points = []
            points.append((pm.real, pm.imag))
            points.extend(self.adaptive_bezier_sample(right, max_error, depth + 1, max_depth))
            return points
    
    def path_to_points(self, svg_path):
        """Convert SVG path object to list of (x, y) points"""
        if not svg_path or len(svg_path) == 0:
            return []
        
        points = []
        
        # Add starting point
        start = svg_path[0].start
        points.append((start.real, start.imag))
        
        # Process each path segment
        for segment in svg_path:
            if isinstance(segment, Line):
                # Straight line—just add endpoint
                end = segment.end
                points.append((end.real, end.imag))
            
            elif isinstance(segment, (CubicBezier, QuadraticBezier)):
                # Bezier curve—sample adaptively
                segment_points = self.adaptive_bezier_sample(segment, self.max_error)
                points.extend(segment_points)
            
            elif isinstance(segment, Arc):
                # Arc—sample uniformly with many points
                for t in np.linspace(0, 1, 30)[1:]:  # Skip first (duplicate)
                    point = segment.point(t)
                    points.append((point.real, point.imag))
            
            else:
                # Fallback: unknown segment type, try to get endpoint
                try:
                    end = segment.end
                    points.append((end.real, end.imag))
                except:
                    pass
        
        return points
    
    def convert_svg_file(self, svg_file):
        """
        Main conversion: SVG file → PEN_* commands
        """
        print(f"Reading SVG: {svg_file}", file=sys.stderr)
        
        try:
            paths, attributes = svg2paths(svg_file)
        except Exception as e:
            print(f"ERROR: Failed to parse SVG: {e}", file=sys.stderr)
            return []
        
        print(f"Found {len(paths)} paths", file=sys.stderr)
        
        total_points = 0
        
        for i, (svg_path, attr) in enumerate(zip(paths, attributes)):
            # Convert path to points
            points = self.path_to_points(svg_path)
            
            if not points:
                continue
            
            total_points += len(points)
            
            # Scale all points
            scaled_points = [(x * self.scale, y * self.scale) for x, y in points]
            
            # Generate pen commands (only for strokes—no fill for simplicity)
            if len(scaled_points) > 1:
                # Move to first point and pen down
                x0, y0 = int(scaled_points[0][0]), int(scaled_points[0][1])
                self.commands.append(f"PEN_DOWN {x0} {y0}")
                
                # Draw remaining points
                for x, y in scaled_points[1:]:
                    ix, iy = int(x), int(y)
                    self.commands.append(f"PEN_MOVE {ix} {iy}")
                
                # Pen up at end
                self.commands.append("PEN_UP")
        
        print(f"Generated {total_points} points → {len(self.commands)} commands", file=sys.stderr)
        return self.commands
    
    def to_string(self):
        """Return commands as newline-separated string"""
        return '\n'.join(self.commands)


def main():
    if len(sys.argv) < 2:
        print("SVG to PEN Command Converter")
        print()
        print("Usage: svg2pen.py <input.svg> [scale] [output.txt]")
        print()
        print("Arguments:")
        print("  input.svg  - SVG circuit file (from KiCAD export)")
        print("  scale      - Scale factor (default: 1.0, try 2.5 for readability)")
        print("  output.txt - Output file (default: stdout)")
        print()
        print("Examples:")
        print("  svg2pen.py circuit.svg")
        print("  svg2pen.py circuit.svg 2.5")
        print("  svg2pen.py circuit.svg 2.5 commands.txt")
        print()
        print("Output is PEN_DOWN/PEN_MOVE/PEN_UP format, ready for injection:")
        print("  PEN_DOWN 100 200")
        print("  PEN_MOVE 150 250")
        print("  PEN_UP")
        sys.exit(1)
    
    svg_file = sys.argv[1]
    scale = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Validate scale
    if scale <= 0:
        print("ERROR: Scale must be positive", file=sys.stderr)
        sys.exit(1)
    
    # Convert
    converter = SVGToPenCommands(scale=scale, max_error=1.0)
    converter.convert_svg_file(svg_file)
    
    # Get output
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
        # stdout for piping
        print(output)


if __name__ == '__main__':
    main()
