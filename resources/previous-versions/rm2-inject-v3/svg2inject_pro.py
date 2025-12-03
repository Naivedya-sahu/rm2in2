#!/usr/bin/env python3
"""
Professional SVG to RM2 Injection Converter
Uses svgpathtools for accurate bezier curve handling and adaptive sampling

Installation:
    pip install svgpathtools shapely numpy --break-system-packages
"""

import sys
import numpy as np
from typing import List, Tuple

try:
    from svgpathtools import svg2paths, Path, Line, CubicBezier, QuadraticBezier, Arc
    from shapely.geometry import Polygon, LineString, Point
    from shapely.ops import unary_union
except ImportError:
    print("ERROR: Required libraries not installed")
    print("Install with: pip install svgpathtools shapely numpy --break-system-packages")
    sys.exit(1)


class SVGToInjection:
    def __init__(self, scale=1.0, adaptive=True, max_error=1.0, 
                 fill_shapes=True, hatch_spacing=3.0, hatch_angle=45):
        """
        Args:
            scale: Scale factor for coordinates
            adaptive: Use adaptive sampling for curves
            max_error: Maximum error for adaptive sampling (smaller = more points)
            fill_shapes: Generate fill hatching for filled shapes
            hatch_spacing: Distance between hatch lines
            hatch_angle: Angle of hatch lines in degrees
        """
        self.scale = scale
        self.adaptive = adaptive
        self.max_error = max_error
        self.fill_shapes = fill_shapes
        self.hatch_spacing = hatch_spacing
        self.hatch_angle = hatch_angle
        self.commands = []
    
    def bezier_to_points_uniform(self, curve, num_points=20):
        """Convert bezier curve to points with uniform sampling"""
        points = []
        for t in np.linspace(0, 1, num_points):
            point = curve.point(t)
            points.append((point.real, point.imag))
        return points
    
    def bezier_to_points_adaptive(self, curve, max_error=1.0, depth=0, max_depth=10):
        """
        Adaptive bezier sampling based on curvature.
        Recursively subdivides curve until error is below threshold.
        """
        if depth > max_depth:
            return [curve.point(1)]
        
        # Sample at start, middle, end
        p0 = curve.point(0)
        pm = curve.point(0.5)
        p1 = curve.point(1)
        
        # Check if midpoint is close to straight line between endpoints
        line_mid = (p0 + p1) / 2
        error = abs(pm - line_mid)
        
        if error <= max_error:
            # Good enough approximation
            return [(p1.real, p1.imag)]
        else:
            # Subdivide
            left, right = curve.split(0.5)
            points = []
            points.append((pm.real, pm.imag))
            points.extend(self.bezier_to_points_adaptive(right, max_error, depth+1, max_depth))
            return points
    
    def arc_to_points(self, arc, num_points=30):
        """Convert arc to points"""
        points = []
        for t in np.linspace(0, 1, num_points):
            point = arc.point(t)
            points.append((point.real, point.imag))
        return points
    
    def path_to_polyline(self, path):
        """Convert SVG path to polyline with proper curve handling"""
        if not path:
            return []
        
        points = []
        
        # Add starting point
        if len(path) > 0:
            start = path[0].start
            points.append((start.real, start.imag))
        
        for segment in path:
            if isinstance(segment, Line):
                end = segment.end
                points.append((end.real, end.imag))
            
            elif isinstance(segment, (CubicBezier, QuadraticBezier)):
                if self.adaptive:
                    segment_points = [(segment.start.real, segment.start.imag)]
                    segment_points.extend(
                        self.bezier_to_points_adaptive(segment, self.max_error)
                    )
                else:
                    segment_points = self.bezier_to_points_uniform(segment, num_points=20)
                
                # Skip first point (duplicate of previous end)
                points.extend(segment_points[1:])
            
            elif isinstance(segment, Arc):
                arc_points = self.arc_to_points(segment, num_points=30)
                points.extend(arc_points[1:])  # Skip first
        
        return points
    
    def create_hatch_lines(self, polygon, angle_deg=45, spacing=5.0):
        """
        Create hatch fill lines for a polygon.
        Returns list of line segments that fill the polygon.
        """
        if polygon.is_empty or not polygon.is_valid:
            return []
        
        minx, miny, maxx, maxy = polygon.bounds
        
        # Convert angle to radians
        angle_rad = np.radians(angle_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        
        hatch_lines = []
        
        # Expand bounds for rotation
        diagonal = np.sqrt((maxx - minx)**2 + (maxy - miny)**2)
        
        # Generate parallel lines
        y = miny - diagonal
        while y <= maxy + diagonal:
            # Create line across bounding box
            x1, x2 = minx - diagonal, maxx + diagonal
            
            # Rotate line by angle
            p1 = (x1 * cos_a - y * sin_a, x1 * sin_a + y * cos_a)
            p2 = (x2 * cos_a - y * sin_a, x2 * sin_a + y * cos_a)
            
            line = LineString([p1, p2])
            
            # Intersect with polygon
            try:
                intersection = polygon.intersection(line)
                
                if not intersection.is_empty:
                    if intersection.geom_type == 'LineString':
                        coords = list(intersection.coords)
                        if len(coords) >= 2:
                            hatch_lines.append(coords)
                    
                    elif intersection.geom_type == 'MultiLineString':
                        for geom in intersection.geoms:
                            coords = list(geom.coords)
                            if len(coords) >= 2:
                                hatch_lines.append(coords)
            
            except Exception as e:
                print(f"Warning: Hatch line intersection failed: {e}")
            
            y += spacing
        
        return hatch_lines
    
    def convert_svg(self, svg_file):
        """Main conversion function"""
        print(f"Reading SVG: {svg_file}")
        
        try:
            paths, attributes = svg2paths(svg_file)
        except Exception as e:
            print(f"ERROR: Failed to parse SVG: {e}")
            return []
        
        print(f"Found {len(paths)} paths")
        
        for i, (path, attr) in enumerate(zip(paths, attributes)):
            # Get styling attributes
            stroke = attr.get('stroke', 'none')
            fill = attr.get('fill', 'none')
            
            # Convert path to points
            points = self.path_to_polyline(path)
            
            if not points:
                continue
            
            # Scale points
            scaled_points = [(x * self.scale, y * self.scale) for x, y in points]
            
            # Draw stroke (outline)
            if stroke != 'none' and len(scaled_points) > 1:
                self.commands.append(('M', scaled_points[0]))
                for point in scaled_points[1:]:
                    self.commands.append(('D', point))
            
            # Fill shape with hatching
            if fill != 'none' and self.fill_shapes and len(scaled_points) >= 3:
                try:
                    # Create polygon
                    poly = Polygon(scaled_points)
                    
                    if poly.is_valid and not poly.is_empty:
                        # Generate hatch lines
                        hatch_lines = self.create_hatch_lines(
                            poly,
                            angle_deg=self.hatch_angle,
                            spacing=self.hatch_spacing
                        )
                        
                        # Draw hatch lines
                        for line_coords in hatch_lines:
                            if len(line_coords) >= 2:
                                self.commands.append(('M', line_coords[0]))
                                for coord in line_coords[1:]:
                                    self.commands.append(('D', coord))
                
                except Exception as e:
                    print(f"Warning: Failed to fill shape {i}: {e}")
        
        print(f"Generated {len(self.commands)} commands")
        return self.commands
    
    def commands_to_pen_format(self):
        """Convert internal commands to PEN_* format for RM2"""
        output = []
        pen_down = False
        
        for cmd_type, point in self.commands:
            x, y = int(point[0]), int(point[1])
            
            if cmd_type == 'M':
                # Move (pen up)
                if pen_down:
                    output.append("PEN_UP")
                    pen_down = False
                # Don't issue move command, just track state
            
            elif cmd_type == 'D':
                # Draw (pen down)
                if not pen_down:
                    output.append(f"PEN_DOWN {x} {y}")
                    pen_down = True
                else:
                    output.append(f"PEN_MOVE {x} {y}")
        
        # Final pen up
        if pen_down:
            output.append("PEN_UP")
        
        return output


def main():
    if len(sys.argv) < 2:
        print("Usage: svg2inject_pro.py <input.svg> [scale] [output.txt]")
        print()
        print("Options:")
        print("  scale: Scale factor (default: 1.0)")
        print("  output: Output file (default: stdout)")
        print()
        print("Examples:")
        print("  svg2inject_pro.py circuit.svg")
        print("  svg2inject_pro.py circuit.svg 2.0")
        print("  svg2inject_pro.py circuit.svg 2.0 output.txt")
        sys.exit(1)
    
    svg_file = sys.argv[1]
    scale = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Create converter
    converter = SVGToInjection(
        scale=scale,
        adaptive=True,
        max_error=1.0,      # Smaller = more accurate but more points
        fill_shapes=True,
        hatch_spacing=3.0,  # Distance between fill lines
        hatch_angle=45      # Angle of fill lines
    )
    
    # Convert
    converter.convert_svg(svg_file)
    
    # Generate PEN_* commands
    pen_commands = converter.commands_to_pen_format()
    
    print(f"Output: {len(pen_commands)} PEN_* commands")
    
    # Write output
    if output_file:
        with open(output_file, 'w') as f:
            for cmd in pen_commands:
                f.write(cmd + '\n')
        print(f"Written to {output_file}")
    else:
        for cmd in pen_commands:
            print(cmd)


if __name__ == '__main__':
    main()
