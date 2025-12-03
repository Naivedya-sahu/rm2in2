#!/usr/bin/env python3
"""
Quick Stroke Preview
Generates HTML preview of PEN commands without running a server
"""

import sys


def parse_pen_commands(filename):
    """Parse PEN commands into stroke list"""
    strokes = []
    current_stroke = []

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            cmd = parts[0]

            if cmd == "PEN_DOWN" and len(parts) == 3:
                current_stroke = [(int(parts[1]), int(parts[2]))]
            elif cmd == "PEN_MOVE" and len(parts) == 3:
                if current_stroke:
                    current_stroke.append((int(parts[1]), int(parts[2])))
            elif cmd == "PEN_UP":
                if current_stroke:
                    strokes.append(current_stroke)
                current_stroke = []

    return strokes


def generate_svg(strokes, width=1000, height=800):
    """Generate SVG preview"""

    # Calculate bounds
    all_points = [p for stroke in strokes for p in stroke]
    if not all_points:
        return ""

    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_y = max(p[1] for p in all_points)

    # Scale to fit
    padding = 50
    scale_x = (width - 2 * padding) / (max_x - min_x) if max_x > min_x else 1
    scale_y = (height - 2 * padding) / (max_y - min_y) if max_y > min_y else 1
    scale = min(scale_x, scale_y)

    def transform(x, y):
        cx = padding + (x - min_x) * scale
        cy = padding + (y - min_y) * scale
        return cx, cy

    # Build SVG
    svg_paths = []
    for stroke in strokes:
        if len(stroke) < 2:
            continue

        path_data = []
        x0, y0 = transform(*stroke[0])
        path_data.append(f"M {x0:.1f} {y0:.1f}")

        for x, y in stroke[1:]:
            cx, cy = transform(x, y)
            path_data.append(f"L {cx:.1f} {cy:.1f}")

        svg_paths.append(f'<path d="{" ".join(path_data)}" stroke="black" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />')

    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <rect width="{width}" height="{height}" fill="white"/>
    {chr(10).join(svg_paths)}
</svg>'''

    return svg


def generate_html_preview(strokes, filename):
    """Generate standalone HTML preview"""

    svg = generate_svg(strokes)

    total_points = sum(len(s) for s in strokes)
    bounds_info = ""

    all_points = [p for stroke in strokes for p in stroke]
    if all_points:
        min_x = min(p[0] for p in all_points)
        max_x = max(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)
        max_y = max(p[1] for p in all_points)
        bounds_info = f"X: {min_x}-{max_x} ({max_x-min_x}), Y: {min_y}-{max_y} ({max_y-min_y})"

    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Stroke Preview - {filename}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .info {{
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            font-size: 14px;
        }}
        .info strong {{
            color: #2196F3;
        }}
        .canvas {{
            border: 1px solid #ddd;
            margin: 20px 0;
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Stroke Preview</h1>
        <div class="info">
            <div><strong>File:</strong> {filename}</div>
            <div><strong>Strokes:</strong> {len(strokes)}</div>
            <div><strong>Total Points:</strong> {total_points}</div>
            <div><strong>Avg Points/Stroke:</strong> {total_points // len(strokes) if strokes else 0}</div>
            <div><strong>Bounds (Wacom):</strong> {bounds_info}</div>
        </div>
        {svg}
    </div>
</body>
</html>'''

    return html


def main():
    if len(sys.argv) < 2:
        print("Stroke Preview")
        print("=" * 70)
        print()
        print("Usage: python preview_strokes.py <input.txt> [output.html]")
        print()
        print("Generates standalone HTML preview of PEN commands")
        print()
        print("Examples:")
        print("  python preview_strokes.py commands.txt")
        print("  python preview_strokes.py commands.txt preview.html")
        print()
        return 1

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.txt', '_preview.html')

    print(f"Loading: {input_file}")
    strokes = parse_pen_commands(input_file)

    if not strokes:
        print("Error: No strokes found")
        return 1

    total_points = sum(len(s) for s in strokes)
    print(f"Found: {len(strokes)} strokes, {total_points} points")

    print(f"Generating: {output_file}")
    html = generate_html_preview(strokes, input_file)

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"Saved: {output_file}")
    print()
    print("Open the HTML file in your browser to view the strokes")

    return 0


if __name__ == '__main__':
    sys.exit(main())
