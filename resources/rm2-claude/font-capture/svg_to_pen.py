#!/usr/bin/env python3
"""
Convert Inkscape SVG (with edited nodes) back to PEN commands.

Usage:
    python svg_to_pen.py input.svg output.txt [--no-delay]

Reads SVG paths and converts coordinates back to Wacom PEN commands.
Compatible with SVGs created by pen_to_svg.py or hand-edited in Inkscape.
Automatically prevents stringing by ensuring proper pen lifting.
"""

import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse

# Wacom coordinate system (RM2 rotated 90°)
WACOM_MAX_X = 20966
WACOM_MAX_Y = 15725

# RM2 display dimensions
RM2_WIDTH = 1404
RM2_HEIGHT = 1872

# SVG dimensions (should match input)
SVG_WIDTH = 1404
SVG_HEIGHT = 1872


class SVGToPen:
    def __init__(self, add_delays=True):
        self.strokes = []
        self.stroke_metadata = []  # Store metadata for each stroke
        self.add_delays = add_delays  # Add delays between strokes to prevent stringing

    def svg_to_wacom(self, svg_x, svg_y):
        """Convert SVG coordinates to PEN command coordinates.

        SVG is in portrait 1404x1872 (standard orientation).
        PEN commands go through inject.c transformation #6:
          Wacom_X = WACOM_MAX_Y - PEN_Y
          Wacom_Y = PEN_X

        To reverse this, we need:
          PEN_X = Wacom_Y = svg_x scaled to Wacom space
          PEN_Y = svg_y scaled to Wacom space

        inject.c will then apply the final transform.
        """
        # Direct mapping: SVG portrait → PEN portrait coordinates
        # Scale SVG (1404x1872) to fit within Wacom space considering transform
        pen_x = int(round((svg_x / SVG_WIDTH) * WACOM_MAX_X))
        pen_y = int(round((svg_y / SVG_HEIGHT) * WACOM_MAX_Y))

        return pen_x, pen_y

    def parse_path_data(self, path_data):
        """Parse SVG path data (M/L commands) into points."""
        points = []

        # Remove extra whitespace and normalize
        path_data = re.sub(r'\s+', ' ', path_data.strip())

        # Split into commands
        tokens = re.findall(r'[MLHVCSQTAZmlhvcsqtaz]|[-+]?[0-9]*\.?[0-9]+', path_data)

        i = 0
        current_x, current_y = 0, 0
        command = None

        while i < len(tokens):
            token = tokens[i]

            # Check if it's a command letter
            if token in 'MLHVCSQTAZmlhvcsqtaz':
                command = token
                i += 1
                continue

            # Parse based on current command
            if command in ['M', 'm']:  # MoveTo
                x = float(token)
                y = float(tokens[i + 1])
                if command == 'm':  # Relative
                    x += current_x
                    y += current_y
                current_x, current_y = x, y
                points.append((x, y))
                i += 2
                # After M, implicit L commands
                command = 'L' if command == 'M' else 'l'

            elif command in ['L', 'l']:  # LineTo
                x = float(token)
                y = float(tokens[i + 1])
                if command == 'l':  # Relative
                    x += current_x
                    y += current_y
                current_x, current_y = x, y
                points.append((x, y))
                i += 2

            elif command in ['H', 'h']:  # Horizontal line
                x = float(token)
                if command == 'h':  # Relative
                    x += current_x
                current_x = x
                points.append((current_x, current_y))
                i += 1

            elif command in ['V', 'v']:  # Vertical line
                y = float(token)
                if command == 'v':  # Relative
                    y += current_y
                current_y = y
                points.append((current_x, current_y))
                i += 1

            elif command in ['C', 'c']:  # Cubic Bezier
                # C x1 y1 x2 y2 x y
                x1 = float(token)
                y1 = float(tokens[i + 1])
                x2 = float(tokens[i + 2])
                y2 = float(tokens[i + 3])
                x = float(tokens[i + 4])
                y = float(tokens[i + 5])

                if command == 'c':  # Relative
                    x1 += current_x
                    y1 += current_y
                    x2 += current_x
                    y2 += current_y
                    x += current_x
                    y += current_y

                # Sample the bezier curve
                curve_points = self.sample_cubic_bezier(
                    current_x, current_y, x1, y1, x2, y2, x, y
                )
                points.extend(curve_points)
                current_x, current_y = x, y
                i += 6

            elif command in ['S', 's']:  # Smooth cubic Bezier
                # S x2 y2 x y
                x2 = float(token)
                y2 = float(tokens[i + 1])
                x = float(tokens[i + 2])
                y = float(tokens[i + 3])

                if command == 's':  # Relative
                    x2 += current_x
                    y2 += current_y
                    x += current_x
                    y += current_y

                # First control point is reflection of previous
                # For simplicity, use current point
                x1, y1 = current_x, current_y

                curve_points = self.sample_cubic_bezier(
                    current_x, current_y, x1, y1, x2, y2, x, y
                )
                points.extend(curve_points)
                current_x, current_y = x, y
                i += 4

            elif command in ['Q', 'q']:  # Quadratic Bezier
                # Q x1 y1 x y
                x1 = float(token)
                y1 = float(tokens[i + 1])
                x = float(tokens[i + 2])
                y = float(tokens[i + 3])

                if command == 'q':  # Relative
                    x1 += current_x
                    y1 += current_y
                    x += current_x
                    y += current_y

                curve_points = self.sample_quadratic_bezier(
                    current_x, current_y, x1, y1, x, y
                )
                points.extend(curve_points)
                current_x, current_y = x, y
                i += 4

            elif command in ['Z', 'z']:  # Close path
                # Could optionally add line back to first point
                i += 1

            else:
                # Unknown command, skip
                i += 1

        return points

    def sample_cubic_bezier(self, x0, y0, x1, y1, x2, y2, x3, y3, steps=20):
        """Sample a cubic Bezier curve into line segments."""
        points = []
        for i in range(1, steps + 1):
            t = i / steps
            t2 = t * t
            t3 = t2 * t
            mt = 1 - t
            mt2 = mt * mt
            mt3 = mt2 * mt

            x = mt3 * x0 + 3 * mt2 * t * x1 + 3 * mt * t2 * x2 + t3 * x3
            y = mt3 * y0 + 3 * mt2 * t * y1 + 3 * mt * t2 * y2 + t3 * y3
            points.append((x, y))

        return points

    def sample_quadratic_bezier(self, x0, y0, x1, y1, x2, y2, steps=15):
        """Sample a quadratic Bezier curve into line segments."""
        points = []
        for i in range(1, steps + 1):
            t = i / steps
            t2 = t * t
            mt = 1 - t
            mt2 = mt * mt

            x = mt2 * x0 + 2 * mt * t * x1 + t2 * x2
            y = mt2 * y0 + 2 * mt * t * y1 + t2 * y2
            points.append((x, y))

        return points

    def parse_svg_file(self, filepath):
        """Parse SVG file and extract path data."""
        print(f"[INFO] Reading SVG from: {filepath}")

        # Parse with namespaces
        namespaces = {
            'svg': 'http://www.w3.org/2000/svg',
            'inkscape': 'http://www.inkscape.org/namespaces/inkscape'
        }

        tree = ET.parse(filepath)
        root = tree.getroot()

        # Find all path elements
        paths = root.findall('.//svg:path', namespaces)

        if not paths:
            # Try without namespace
            paths = root.findall('.//path')

        print(f"[INFO] Found {len(paths)} paths")

        for path_idx, path in enumerate(paths):
            path_data = path.get('d', '')
            if not path_data:
                continue

            path_id = path.get('id', f'path_{path_idx}')
            print(f"[INFO] Processing {path_id}")

            # Parse path data into points
            svg_points = self.parse_path_data(path_data)

            if len(svg_points) < 2:
                print(f"[WARN] Skipping path with < 2 points")
                continue

            # Convert to Wacom coordinates
            wacom_points = [self.svg_to_wacom(x, y) for x, y in svg_points]

            # Calculate stroke metadata for ordering
            metadata = self.calculate_stroke_metadata(wacom_points, path_id)

            self.strokes.append(wacom_points)
            self.stroke_metadata.append(metadata)

            print(f"[INFO]   -> {len(wacom_points)} points")

        print(f"[INFO] Total strokes: {len(self.strokes)}")
        total_points = sum(len(stroke) for stroke in self.strokes)
        print(f"[INFO] Total points: {total_points}")

        # Order strokes for natural handwriting flow
        self.order_strokes_for_handwriting()

    def calculate_stroke_metadata(self, points, path_id):
        """Calculate metadata for stroke ordering."""
        if not points:
            return None

        # Calculate bounding box
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # Calculate stroke properties
        width = max_x - min_x
        height = max_y - min_y
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # Determine stroke orientation
        is_horizontal = width > height
        is_vertical = height > width
        is_diagonal = abs(width - height) < min(width, height) * 0.3

        # Calculate stroke length (approximate)
        length = sum(
            ((points[i+1][0] - points[i][0])**2 + (points[i+1][1] - points[i][1])**2)**0.5
            for i in range(len(points) - 1)
        )

        # Detect if stroke is a dot (small circle/oval)
        # In Wacom coordinates, dots are typically:
        # - Small in both dimensions (< 200 units)
        # - Short total length (< 500 units)
        # - Roughly square aspect ratio
        aspect_ratio = width / height if height > 0 else 1
        is_dot = (width < 200 and height < 200 and length < 500) and \
                 (0.5 < aspect_ratio < 2.0)  # Roughly circular

        return {
            'id': path_id,
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'center_x': center_x,
            'center_y': center_y,
            'width': width,
            'height': height,
            'length': length,
            'is_horizontal': is_horizontal,
            'is_vertical': is_vertical,
            'is_diagonal': is_diagonal,
            'is_dot': is_dot,
        }

    def order_strokes_for_handwriting(self):
        """Order strokes to emulate natural handwriting flow."""
        if len(self.strokes) <= 1:
            return

        print(f"[INFO] Ordering {len(self.strokes)} strokes for handwriting flow")

        # Create list of (stroke, metadata, original_index) tuples
        stroke_data = list(zip(self.strokes, self.stroke_metadata, range(len(self.strokes))))

        # Separate dots from other strokes
        dots = []
        main_strokes = []

        for stroke, meta, idx in stroke_data:
            if meta['is_dot']:
                dots.append((stroke, meta, idx))
            else:
                main_strokes.append((stroke, meta, idx))

        # Sort main strokes by:
        # 1. Top coordinate (ascending) - draw upper parts first
        # 2. Left coordinate (ascending) - left-to-right for LTR
        # 3. Vertical before horizontal (for crossing strokes)
        # 4. Length (descending) - main strokes before details
        def stroke_sort_key(item):
            stroke, meta, idx = item
            return (
                meta['min_y'],           # Top position (lower Y = higher priority)
                meta['min_x'],           # Left position (lower X = higher priority)
                not meta['is_vertical'], # Vertical strokes first (True=0, False=1)
                -meta['length'],         # Longer strokes first (negative for descending)
            )

        main_strokes.sort(key=stroke_sort_key)

        # Sort dots by position (should come after their associated main stroke)
        # Place dots near their associated strokes based on proximity
        ordered_strokes = []
        used_dots = set()

        for stroke, meta, idx in main_strokes:
            ordered_strokes.append((stroke, meta, idx))

            # Find dots near this stroke (within reasonable distance)
            for dot_idx, (dot_stroke, dot_meta, dot_orig_idx) in enumerate(dots):
                if dot_idx in used_dots:
                    continue

                # Check if dot is within ~2000 units of this stroke
                # (dots for i, j typically appear above)
                if abs(dot_meta['center_x'] - meta['center_x']) < 2000:
                    # Dot should come after main stroke
                    ordered_strokes.append((dot_stroke, dot_meta, dot_orig_idx))
                    used_dots.add(dot_idx)

        # Add any remaining dots at the end
        for dot_idx, (dot_stroke, dot_meta, dot_orig_idx) in enumerate(dots):
            if dot_idx not in used_dots:
                ordered_strokes.append((dot_stroke, dot_meta, dot_orig_idx))

        # Update strokes and metadata with new order
        self.strokes = [s[0] for s in ordered_strokes]
        self.stroke_metadata = [s[1] for s in ordered_strokes]

        print(f"[INFO] Stroke ordering complete:")
        print(f"[INFO]   Main strokes: {len(main_strokes)}")
        print(f"[INFO]   Dots/accents: {len(dots)}")

    def generate_pen_commands(self, output_path):
        """Generate PEN command file with pen lifting to prevent stringing."""
        print(f"[INFO] Generating PEN commands: {output_path}")

        lines = []
        lines.append("# PEN commands generated from SVG")
        lines.append(f"# {len(self.strokes)} strokes")
        if self.add_delays:
            lines.append("# Pen lifting with delays enabled to prevent stringing")
        else:
            lines.append("# Pen lifting enabled (no delays)")
        lines.append("")

        # Track last position for stringing detection
        last_end_pos = None
        delay_count = 0

        for stroke_idx, stroke in enumerate(self.strokes):
            lines.append(f"# Stroke {stroke_idx + 1} ({len(stroke)} points)")

            # Check if we need pen lifting between this stroke and previous
            if last_end_pos is not None and len(stroke) > 0:
                stroke_start = stroke[0]
                distance = self.calculate_distance(last_end_pos, stroke_start)

                # If distance is significant, ensure clean pen lift
                # Threshold: ~500 Wacom units (prevents visible stringing)
                if distance > 500:
                    lines.append(f"# Pen lift: distance={int(distance)} units")

                    # Add small delay to ensure pen fully lifts before next stroke
                    # This prevents "stringing" artifacts where pen drags between strokes
                    if self.add_delays:
                        # DELAY command will be handled by inject.c (sleep for N ms)
                        # Longer delays for longer jumps
                        delay_ms = min(50, int(distance / 100))  # 10-50ms based on distance
                        lines.append(f"DELAY {delay_ms}")
                        delay_count += 1

            # Generate stroke commands
            for point_idx, (wx, wy) in enumerate(stroke):
                if point_idx == 0:
                    lines.append(f"PEN_DOWN {wx} {wy}")
                else:
                    lines.append(f"PEN_MOVE {wx} {wy}")

            lines.append("PEN_UP")

            # Track end position of this stroke
            if len(stroke) > 0:
                last_end_pos = stroke[-1]

            lines.append("")

        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))

        print(f"[OK] PEN commands saved: {output_path}")
        if self.add_delays:
            print(f"[INFO] Added {delay_count} delays to prevent stringing")
        print(f"[INFO] Pen lifting applied between distant strokes")

    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points."""
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        return (dx * dx + dy * dy) ** 0.5


def main():
    parser = argparse.ArgumentParser(
        description='Convert Inkscape SVG to PEN commands with stroke ordering and pen lifting'
    )
    parser.add_argument('input', help='Input SVG file')
    parser.add_argument('output', help='Output PEN command file')
    parser.add_argument('--no-delay', action='store_true',
                        help='Disable delay commands (faster but may cause stringing)')

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"[ERROR] Input file not found: {args.input}")
        sys.exit(1)

    # Create converter with delay option
    add_delays = not args.no_delay
    converter = SVGToPen(add_delays=add_delays)

    # Parse and convert
    converter.parse_svg_file(args.input)
    converter.generate_pen_commands(args.output)

    print("")
    print("Next steps:")
    print(f"  1. Test on RM2: ./send.sh {args.output}")
    print("  2. If stringing occurs, delays are automatically added")
    print("  3. Use --no-delay for faster rendering if stringing is acceptable")


if __name__ == '__main__':
    main()
