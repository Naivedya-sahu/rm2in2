#!/usr/bin/env python3
"""
Medium-weight SVG to RM2 Injection Converter
Supports bezier curves using simple linear approximation
No external libraries required (pure Python + built-in xml)

For best quality with fills, use svg2inject_pro.py with svgpathtools
"""

import sys
import re
import xml.etree.ElementTree as ET
from typing import List, Tuple


def cubic_bezier_points(p0, p1, p2, p3, num_points=20):
    """
    Generate points along a cubic bezier curve.
    p0, p1, p2, p3 are (x, y) tuples
    """
    points = []
    for i in range(num_points + 1):
        t = i / num_points
        # Cubic bezier formula
        x = ((1-t)**3 * p0[0] + 
             3*(1-t)**2*t * p1[0] + 
             3*(1-t)*t**2 * p2[0] + 
             t**3 * p3[0])
        y = ((1-t)**3 * p0[1] + 
             3*(1-t)**2*t * p1[1] + 
             3*(1-t)*t**2 * p2[1] + 
             t**3 * p3[1])
        points.append((x, y))
    return points


def quadratic_bezier_points(p0, p1, p2, num_points=15):
    """Generate points along a quadratic bezier curve"""
    points = []
    for i in range(num_points + 1):
        t = i / num_points
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
        points.append((x, y))
    return points


def parse_path_data(path_data: str) -> List[Tuple[float, float]]:
    """
    Parse SVG path d attribute and return list of (x, y) points.
    Supports: M, L, H, V, Z, C, S, Q, T
    """
    # Tokenize
    tokens = re.findall(
        r'[MLHVZCSQTAmlhvzcsqta]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?',
        path_data
    )
    
    points = []
    i = 0
    x, y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    last_cmd = None
    last_control_x, last_control_y = 0.0, 0.0
    
    while i < len(tokens):
        token = tokens[i]
        
        # Check if it's a command
        if token in 'MLHVZCSQTAmlhvzcsqta':
            last_cmd = token
            i += 1
            continue
        
        if last_cmd is None:
            i += 1
            continue
        
        try:
            # Move to
            if last_cmd in 'Mm':
                nx = float(tokens[i])
                ny = float(tokens[i+1])
                if last_cmd == 'm' and points:
                    nx += x
                    ny += y
                points.append((nx, ny))
                x, y = nx, ny
                start_x, start_y = x, y
                i += 2
            
            # Line to
            elif last_cmd in 'Ll':
                nx = float(tokens[i])
                ny = float(tokens[i+1])
                if last_cmd == 'l':
                    nx += x
                    ny += y
                points.append((nx, ny))
                x, y = nx, ny
                i += 2
            
            # Horizontal line
            elif last_cmd in 'Hh':
                nx = float(tokens[i])
                if last_cmd == 'h':
                    nx += x
                points.append((nx, y))
                x = nx
                i += 1
            
            # Vertical line
            elif last_cmd in 'Vv':
                ny = float(tokens[i])
                if last_cmd == 'v':
                    ny += y
                points.append((x, ny))
                y = ny
                i += 1
            
            # Close path
            elif last_cmd in 'Zz':
                points.append((start_x, start_y))
                x, y = start_x, start_y
                i += 1
            
            # Cubic bezier
            elif last_cmd in 'Cc':
                x1 = float(tokens[i])
                y1 = float(tokens[i+1])
                x2 = float(tokens[i+2])
                y2 = float(tokens[i+3])
                x3 = float(tokens[i+4])
                y3 = float(tokens[i+5])
                
                if last_cmd == 'c':
                    x1 += x
                    y1 += y
                    x2 += x
                    y2 += y
                    x3 += x
                    y3 += y
                
                # Generate bezier points
                curve_points = cubic_bezier_points(
                    (x, y), (x1, y1), (x2, y2), (x3, y3),
                    num_points=15
                )
                points.extend(curve_points[1:])  # Skip first (duplicate)
                
                last_control_x, last_control_y = x2, y2
                x, y = x3, y3
                i += 6
            
            # Smooth cubic bezier
            elif last_cmd in 'Ss':
                # First control point is reflection of last control point
                x1 = 2*x - last_control_x
                y1 = 2*y - last_control_y
                
                x2 = float(tokens[i])
                y2 = float(tokens[i+1])
                x3 = float(tokens[i+2])
                y3 = float(tokens[i+3])
                
                if last_cmd == 's':
                    x2 += x
                    y2 += y
                    x3 += x
                    y3 += y
                
                curve_points = cubic_bezier_points(
                    (x, y), (x1, y1), (x2, y2), (x3, y3),
                    num_points=15
                )
                points.extend(curve_points[1:])
                
                last_control_x, last_control_y = x2, y2
                x, y = x3, y3
                i += 4
            
            # Quadratic bezier
            elif last_cmd in 'Qq':
                x1 = float(tokens[i])
                y1 = float(tokens[i+1])
                x2 = float(tokens[i+2])
                y2 = float(tokens[i+3])
                
                if last_cmd == 'q':
                    x1 += x
                    y1 += y
                    x2 += x
                    y2 += y
                
                curve_points = quadratic_bezier_points(
                    (x, y), (x1, y1), (x2, y2),
                    num_points=12
                )
                points.extend(curve_points[1:])
                
                last_control_x, last_control_y = x1, y1
                x, y = x2, y2
                i += 4
            
            # Smooth quadratic bezier
            elif last_cmd in 'Tt':
                x1 = 2*x - last_control_x
                y1 = 2*y - last_control_y
                
                x2 = float(tokens[i])
                y2 = float(tokens[i+1])
                
                if last_cmd == 't':
                    x2 += x
                    y2 += y
                
                curve_points = quadratic_bezier_points(
                    (x, y), (x1, y1), (x2, y2),
                    num_points=12
                )
                points.extend(curve_points[1:])
                
                last_control_x, last_control_y = x1, y1
                x, y = x2, y2
                i += 2
            
            # Arc - approximate as line for now
            elif last_cmd in 'Aa':
                # Skip arc parameters, just use endpoint
                x2 = float(tokens[i+5])
                y2 = float(tokens[i+6])
                if last_cmd == 'a':
                    x2 += x
                    y2 += y
                points.append((x2, y2))
                x, y = x2, y2
                i += 7
            
            else:
                i += 1
        
        except (IndexError, ValueError) as e:
            print(f"Warning: Parse error at token {i}: {e}")
            break
    
    return points


def svg_to_injection(svg_file: str, scale: float = 1.0, flip_y: bool = True, 
                     svg_height: float = None) -> List[str]:
    """
    Convert SVG to injection commands
    
    Args:
        svg_file: Path to SVG file
        scale: Scale factor
        flip_y: Flip Y-axis (for RM2 coordinate system)
        svg_height: SVG height for Y-flip (auto-detected if None)
    """
    
    try:
        tree = ET.parse(svg_file)
        root = tree.getroot()
    except Exception as e:
        print(f"ERROR: Failed to parse SVG: {e}")
        return []
    
    # Handle namespaces
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    
    # Get SVG dimensions for Y-flip
    if flip_y and svg_height is None:
        try:
            height_str = root.get('height', '0')
            svg_height = float(height_str.replace('px', '').replace('mm', ''))
        except:
            svg_height = 1872  # Default RM2 height
    
    print(f"SVG height: {svg_height}")
    print(f"Y-axis flip: {flip_y}")
    
    all_commands = []
    path_count = 0
    total_points = 0
    
    # Find all path elements
    for path_elem in root.findall('.//svg:path', ns) or root.findall('.//path'):
        path_count += 1
        path_data = path_elem.get('d', '')
        
        if not path_data:
            continue
        
        # Get styling
        fill = path_elem.get('fill', 'none')
        stroke = path_elem.get('stroke', 'none')
        
        print(f"Path {path_count}: fill={fill}, stroke={stroke}")
        
        # Parse path to points
        points = parse_path_data(path_data)
        
        if not points:
            print(f"  No points generated")
            continue
        
        print(f"  Generated {len(points)} points")
        total_points += len(points)
        
        # Scale and flip Y if needed
        if flip_y:
            scaled_points = [(x * scale, (svg_height - y) * scale) for x, y in points]
        else:
            scaled_points = [(x * scale, y * scale) for x, y in points]
        
        # Convert to pen commands
        if scaled_points:
            # Start with pen up, move to first point
            x0, y0 = int(scaled_points[0][0]), int(scaled_points[0][1])
            all_commands.append(f"PEN_DOWN {x0} {y0}")
            
            # Draw remaining points
            for x, y in scaled_points[1:]:
                all_commands.append(f"PEN_MOVE {int(x)} {int(y)}")
            
            # Pen up at end
            all_commands.append("PEN_UP")
    
    print(f"\nTotal paths: {path_count}")
    print(f"Total points: {total_points}")
    print(f"Total commands: {len(all_commands)}")
    
    return all_commands


def main():
    if len(sys.argv) < 2:
        print("Medium-weight SVG to RM2 Injection Converter")
        print("Supports bezier curves with linear approximation")
        print()
        print("Usage: svg2inject_medium.py <input.svg> [scale] [output.txt] [--no-flip-y]")
        print()
        print("Options:")
        print("  --no-flip-y    Don't flip Y-axis (use if drawing appears upside-down)")
        print()
        print("Examples:")
        print("  svg2inject_medium.py text.svg 2.0")
        print("  svg2inject_medium.py circuit.svg 1.5 output.txt")
        print("  svg2inject_medium.py test.svg 2.0 test.txt --no-flip-y")
        sys.exit(1)
    
    svg_file = sys.argv[1]
    scale = 1.0
    output_file = None
    flip_y = True
    
    # Parse arguments
    for i in range(2, len(sys.argv)):
        arg = sys.argv[i]
        if arg == '--no-flip-y':
            flip_y = False
        elif arg.endswith('.txt'):
            output_file = arg
        else:
            try:
                scale = float(arg)
            except ValueError:
                pass
    
    print(f"Converting: {svg_file}")
    print(f"Scale: {scale}")
    print()
    
    commands = svg_to_injection(svg_file, scale=scale, flip_y=flip_y)
    
    if not commands:
        print("\nERROR: No commands generated!")
        sys.exit(1)
    
    # Output
    if output_file:
        with open(output_file, 'w') as f:
            for cmd in commands:
                f.write(cmd + '\n')
        print(f"\nWritten to: {output_file}")
    else:
        for cmd in commands:
            print(cmd)


if __name__ == '__main__':
    main()