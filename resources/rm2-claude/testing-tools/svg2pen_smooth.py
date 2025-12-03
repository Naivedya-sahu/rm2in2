#!/usr/bin/env python3
"""
SVG to PEN - Smooth Single Stroke Version
Generates pen commands that mimic natural handwriting
- More curve sampling for smoothness
- Single continuous stroke per path
- No duplicate/coincident points
"""

import sys
import xml.etree.ElementTree as ET
import math

def parse_number(s, i):
    """Parse a number from string starting at index i"""
    while i < len(s) and s[i] in ' \t\n,':
        i += 1

    if i >= len(s):
        return None, i

    start = i
    if s[i] in '+-':
        i += 1

    has_dot = False
    while i < len(s) and (s[i].isdigit() or s[i] == '.'):
        if s[i] == '.':
            if has_dot:
                break
            has_dot = True
        i += 1

    if i > start:
        return float(s[start:i]), i
    return None, start

def parse_svg_path(d, curve_steps=10):
    """
    Parse SVG path with high-quality curve sampling

    Args:
        d: SVG path 'd' attribute
        curve_steps: Number of steps for sampling curves (higher = smoother)
    """

    if not d:
        return []

    points = []
    i = 0
    current_x, current_y = 0.0, 0.0
    last_cmd = None
    start_x, start_y = 0.0, 0.0

    while i < len(d):
        # Skip whitespace
        while i < len(d) and d[i] in ' \t\n,':
            i += 1

        if i >= len(d):
            break

        # Check for command letter
        if d[i].isalpha():
            last_cmd = d[i]
            i += 1

            # M command
            if last_cmd in 'Mm':
                x, i = parse_number(d, i)
                y, i = parse_number(d, i)

                if x is None or y is None:
                    continue

                if last_cmd == 'M':
                    current_x, current_y = x, y
                else:
                    current_x += x
                    current_y += y

                start_x, start_y = current_x, current_y
                points.append((current_x, current_y))

                last_cmd = 'L' if last_cmd == 'M' else 'l'
                continue

        # L - Line
        if last_cmd in 'Ll':
            x, i = parse_number(d, i)
            y, i = parse_number(d, i)

            if x is None or y is None:
                break

            if last_cmd == 'L':
                current_x, current_y = x, y
            else:
                current_x += x
                current_y += y

            points.append((current_x, current_y))

        # H - Horizontal line
        elif last_cmd in 'Hh':
            x, i = parse_number(d, i)
            if x is None:
                break

            if last_cmd == 'H':
                current_x = x
            else:
                current_x += x

            points.append((current_x, current_y))

        # V - Vertical line
        elif last_cmd in 'Vv':
            y, i = parse_number(d, i)
            if y is None:
                break

            if last_cmd == 'V':
                current_y = y
            else:
                current_y += y

            points.append((current_x, current_y))

        # C - Cubic Bezier (HIGH QUALITY SAMPLING)
        elif last_cmd in 'Cc':
            coords = []
            for _ in range(6):
                num, i = parse_number(d, i)
                if num is None:
                    break
                coords.append(num)

            if len(coords) == 6:
                if last_cmd == 'C':
                    x1, y1, x2, y2, x, y = coords
                else:
                    x1 = current_x + coords[0]
                    y1 = current_y + coords[1]
                    x2 = current_x + coords[2]
                    y2 = current_y + coords[3]
                    x = current_x + coords[4]
                    y = current_y + coords[5]

                # Sample cubic Bezier with high quality
                for t_i in range(1, curve_steps + 1):
                    t = t_i / curve_steps
                    # Cubic Bezier formula
                    bx = (1-t)**3 * current_x + 3*(1-t)**2*t * x1 + 3*(1-t)*t**2 * x2 + t**3 * x
                    by = (1-t)**3 * current_y + 3*(1-t)**2*t * y1 + 3*(1-t)*t**2 * y2 + t**3 * y
                    points.append((bx, by))

                current_x, current_y = x, y

        # S - Smooth cubic Bezier
        elif last_cmd in 'Ss':
            coords = []
            for _ in range(4):
                num, i = parse_number(d, i)
                if num is None:
                    break
                coords.append(num)

            if len(coords) == 4:
                if last_cmd == 'S':
                    x2, y2, x, y = coords
                else:
                    x2 = current_x + coords[0]
                    y2 = current_y + coords[1]
                    x = current_x + coords[2]
                    y = current_y + coords[3]

                # Sample smooth curve
                for t_i in range(1, curve_steps + 1):
                    t = t_i / curve_steps
                    bx = (1-t)**2 * current_x + 2*(1-t)*t * x2 + t**2 * x
                    by = (1-t)**2 * current_y + 2*(1-t)*t * y2 + t**2 * y
                    points.append((bx, by))

                current_x, current_y = x, y

        # Q - Quadratic Bezier
        elif last_cmd in 'Qq':
            coords = []
            for _ in range(4):
                num, i = parse_number(d, i)
                if num is None:
                    break
                coords.append(num)

            if len(coords) == 4:
                if last_cmd == 'Q':
                    cx, cy, x, y = coords
                else:
                    cx = current_x + coords[0]
                    cy = current_y + coords[1]
                    x = current_x + coords[2]
                    y = current_y + coords[3]

                # Sample quadratic Bezier
                for t_i in range(1, curve_steps + 1):
                    t = t_i / curve_steps
                    bx = (1-t)**2 * current_x + 2*(1-t)*t * cx + t**2 * x
                    by = (1-t)**2 * current_y + 2*(1-t)*t * cy + t**2 * y
                    points.append((bx, by))

                current_x, current_y = x, y

        # Z - Close path
        elif last_cmd in 'Zz':
            if (current_x, current_y) != (start_x, start_y):
                points.append((start_x, start_y))
            current_x, current_y = start_x, start_y
            i += 1

        else:
            i += 1

    return points

def remove_coincident_points(points, min_distance=0.5):
    """
    Remove points that are too close together

    Args:
        points: List of (x, y) tuples
        min_distance: Minimum distance between consecutive points
    """
    if not points:
        return []

    result = [points[0]]

    for x, y in points[1:]:
        last_x, last_y = result[-1]
        dx = x - last_x
        dy = y - last_y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance >= min_distance:
            result.append((x, y))

    return result

def smooth_stroke(points, window=3):
    """
    Apply smoothing filter to reduce jitter

    Args:
        points: List of (x, y) tuples
        window: Smoothing window size
    """
    if len(points) < window:
        return points

    smoothed = [points[0]]  # Keep first point

    for i in range(1, len(points) - 1):
        # Average with neighbors
        start = max(0, i - window // 2)
        end = min(len(points), i + window // 2 + 1)

        avg_x = sum(p[0] for p in points[start:end]) / (end - start)
        avg_y = sum(p[1] for p in points[start:end]) / (end - start)

        smoothed.append((avg_x, avg_y))

    smoothed.append(points[-1])  # Keep last point

    return smoothed

def svg_to_pen(svg_file, scale=1.0, curve_quality=10, smoothness=3, min_distance=0.5, output_file=None):
    """
    Convert SVG to smooth PEN commands

    Args:
        svg_file: Input SVG file
        scale: Scale factor
        curve_quality: Curve sampling steps (higher = smoother)
        smoothness: Smoothing window size
        min_distance: Minimum distance between points
        output_file: Output file (None for stdout)
    """

    try:
        tree = ET.parse(svg_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing SVG: {e}", file=sys.stderr)
        return 1

    commands = []
    path_count = 0
    total_points = 0

    # Find all path elements
    for path in root.iter():
        if path.tag.endswith('path'):
            d = path.get('d')
            if not d:
                continue

            # Parse with high quality
            points = parse_svg_path(d, curve_steps=curve_quality)

            if not points:
                continue

            # Remove coincident points
            points = remove_coincident_points(points, min_distance=min_distance)

            # Apply smoothing
            if smoothness > 0:
                points = smooth_stroke(points, window=smoothness)

            # Remove coincident again after smoothing
            points = remove_coincident_points(points, min_distance=min_distance)

            if not points:
                continue

            # Scale points
            scaled_points = [(int(x * scale), int(y * scale)) for x, y in points]

            # Remove integer duplicates
            unique_points = []
            for p in scaled_points:
                if not unique_points or p != unique_points[-1]:
                    unique_points.append(p)

            # Convert to PEN commands (SINGLE STROKE)
            if unique_points:
                x, y = unique_points[0]
                commands.append(f"PEN_DOWN {x} {y}")

                for x, y in unique_points[1:]:
                    commands.append(f"PEN_MOVE {x} {y}")

                commands.append("PEN_UP")
                path_count += 1
                total_points += len(unique_points)

    if not commands:
        print("Warning: No paths found in SVG", file=sys.stderr)
        return 1

    # Output
    output = '\n'.join(commands) + '\n'

    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"✓ Paths: {path_count}", file=sys.stderr)
        print(f"✓ Points: {total_points}", file=sys.stderr)
        print(f"✓ Commands: {len(commands)}", file=sys.stderr)
        print(f"✓ Avg points/stroke: {total_points/path_count:.1f}", file=sys.stderr)
        print(f"✓ Saved to: {output_file}", file=sys.stderr)
    else:
        print(output)

    return 0

def main():
    if len(sys.argv) < 2:
        print("SVG to PEN - Smooth Single Stroke Version")
        print()
        print("Usage:")
        print("  python svg2pen_smooth.py <input.svg> [options]")
        print()
        print("Options:")
        print("  --scale <n>       Scale factor (default: 1.0)")
        print("  --quality <n>     Curve sampling steps (default: 10)")
        print("  --smooth <n>      Smoothing window (default: 3, 0=off)")
        print("  --min-dist <n>    Min point distance (default: 0.5)")
        print("  -o <file>         Output file")
        print()
        print("Examples:")
        print("  # High quality smooth output")
        print("  python svg2pen_smooth.py drawing.svg --quality 15 --smooth 5 -o smooth.txt")
        print()
        print("  # Fast with less smoothing")
        print("  python svg2pen_smooth.py drawing.svg --quality 8 --smooth 2 -o fast.txt")
        print()
        print("Features:")
        print("  - High quality Bezier curve sampling")
        print("  - Coincident point removal")
        print("  - Smoothing filter")
        print("  - Single continuous stroke per path")
        return 1

    svg_file = sys.argv[1]
    scale = 1.0
    curve_quality = 10
    smoothness = 3
    min_distance = 0.5
    output_file = None

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--scale' and i + 1 < len(sys.argv):
            scale = float(sys.argv[i + 1])
            i += 2
        elif arg == '--quality' and i + 1 < len(sys.argv):
            curve_quality = int(sys.argv[i + 1])
            i += 2
        elif arg == '--smooth' and i + 1 < len(sys.argv):
            smoothness = int(sys.argv[i + 1])
            i += 2
        elif arg == '--min-dist' and i + 1 < len(sys.argv):
            min_distance = float(sys.argv[i + 1])
            i += 2
        elif arg == '-o' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        else:
            print(f"Error: Unknown argument: {arg}", file=sys.stderr)
            return 1

    return svg_to_pen(svg_file, scale, curve_quality, smoothness, min_distance, output_file)

if __name__ == '__main__':
    sys.exit(main())
