#!/usr/bin/env python3
"""
Interactive Stroke Editor
Web-based visual editor for tweaking PEN commands and stroke interpolation
"""

import sys
import json
import re
import math
import http.server
import socketserver
import webbrowser
import threading
from urllib.parse import parse_qs, urlparse


# Global state
current_strokes = []
wacom_max_x = 20966
wacom_max_y = 15725


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


def interpolate_stroke(stroke, factor):
    """Add interpolated points between stroke points"""
    if factor <= 1 or len(stroke) < 2:
        return stroke

    result = []
    for i in range(len(stroke) - 1):
        x1, y1 = stroke[i]
        x2, y2 = stroke[i + 1]

        result.append((x1, y1))

        for j in range(1, factor):
            t = j / factor
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))
            result.append((x, y))

    result.append(stroke[-1])
    return result


def smooth_stroke(stroke, window=3):
    """Apply moving average smoothing"""
    if len(stroke) < window or window < 2:
        return stroke

    smoothed = [stroke[0]]

    for i in range(1, len(stroke) - 1):
        start = max(0, i - window // 2)
        end = min(len(stroke), i + window // 2 + 1)

        avg_x = sum(p[0] for p in stroke[start:end]) / (end - start)
        avg_y = sum(p[1] for p in stroke[start:end]) / (end - start)

        smoothed.append((int(avg_x), int(avg_y)))

    smoothed.append(stroke[-1])
    return smoothed


def strokes_to_pen_commands(strokes):
    """Convert strokes back to PEN commands"""
    commands = []

    for stroke in strokes:
        if not stroke:
            continue

        commands.append(f"PEN_DOWN {stroke[0][0]} {stroke[0][1]}")
        for x, y in stroke[1:]:
            commands.append(f"PEN_MOVE {x} {y}")
        commands.append("PEN_UP")

    return commands


def generate_html_editor(strokes):
    """Generate HTML editor interface"""

    # Calculate canvas dimensions
    all_points = [p for stroke in strokes for p in stroke]
    if all_points:
        min_x = min(p[0] for p in all_points)
        max_x = max(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)
        max_y = max(p[1] for p in all_points)
    else:
        min_x, max_x = 0, wacom_max_x
        min_y, max_y = 0, wacom_max_y

    # Prepare stroke data for JavaScript
    strokes_json = json.dumps([
        {"points": stroke, "selected": True, "interpolation": 1, "smoothing": 0}
        for stroke in strokes
    ])

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Stroke Editor</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        h1 {{
            margin: 0 0 20px 0;
            color: #333;
        }}
        .editor {{
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 20px;
        }}
        .canvas-container {{
            border: 2px solid #ddd;
            border-radius: 4px;
            background: white;
            position: relative;
            overflow: auto;
        }}
        canvas {{
            display: block;
            cursor: crosshair;
        }}
        .controls {{
            background: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
        }}
        .control-group {{
            margin-bottom: 20px;
        }}
        .control-group h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
        }}
        .stroke-list {{
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .stroke-item {{
            padding: 8px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .stroke-item:hover {{
            background: #f0f0f0;
        }}
        .stroke-item.selected {{
            background: #e3f2fd;
        }}
        .stroke-item.hidden {{
            opacity: 0.3;
        }}
        label {{
            display: block;
            margin: 10px 0 5px 0;
            font-size: 13px;
            color: #555;
        }}
        input[type="range"] {{
            width: 100%;
        }}
        .value {{
            display: inline-block;
            float: right;
            font-weight: bold;
            color: #333;
        }}
        button {{
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: none;
            border-radius: 4px;
            background: #2196F3;
            color: white;
            cursor: pointer;
            font-size: 14px;
        }}
        button:hover {{
            background: #1976D2;
        }}
        button.secondary {{
            background: #757575;
        }}
        button.secondary:hover {{
            background: #616161;
        }}
        .stats {{
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            font-size: 12px;
            margin-top: 10px;
        }}
        .stats div {{
            margin: 5px 0;
        }}
        .checkbox {{
            display: inline-block;
            margin-right: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Stroke Editor</h1>
        <div class="editor">
            <div class="canvas-container">
                <canvas id="canvas" width="1000" height="800"></canvas>
            </div>
            <div class="controls">
                <div class="control-group">
                    <h3>Strokes</h3>
                    <div id="strokeList" class="stroke-list"></div>
                </div>

                <div class="control-group" id="strokeControls">
                    <h3>Selected Stroke</h3>
                    <label>
                        Interpolation: <span class="value" id="interpValue">1x</span>
                        <input type="range" id="interpSlider" min="1" max="30" value="1" />
                    </label>
                    <label>
                        Smoothing: <span class="value" id="smoothValue">0</span>
                        <input type="range" id="smoothSlider" min="0" max="10" value="0" />
                    </label>
                </div>

                <div class="control-group">
                    <h3>Global Settings</h3>
                    <label>
                        Apply to all: <span class="value" id="globalInterpValue">15x</span>
                        <input type="range" id="globalInterp" min="1" max="30" value="15" />
                    </label>
                    <button onclick="applyGlobalInterpolation()">Apply Interpolation to All</button>
                    <label>
                        Global smoothing: <span class="value" id="globalSmoothValue">3</span>
                        <input type="range" id="globalSmooth" min="0" max="10" value="3" />
                    </label>
                    <button onclick="applyGlobalSmoothing()">Apply Smoothing to All</button>
                </div>

                <div class="control-group">
                    <h3>Actions</h3>
                    <button onclick="resetAll()">Reset All Changes</button>
                    <button onclick="exportCommands()" class="secondary">Export PEN Commands</button>
                </div>

                <div class="stats" id="stats">
                    <div>Total strokes: <strong id="totalStrokes">0</strong></div>
                    <div>Total points: <strong id="totalPoints">0</strong></div>
                    <div>Selected points: <strong id="selectedPoints">0</strong></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let strokes = {strokes_json};
        let selectedStroke = 0;
        let originalStrokes = JSON.parse(JSON.stringify(strokes));

        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        const bounds = {{
            minX: {min_x},
            maxX: {max_x},
            minY: {min_y},
            maxY: {max_y}
        }};

        function wacomToCanvas(wx, wy) {{
            const padding = 50;
            const scaleX = (canvas.width - 2 * padding) / (bounds.maxX - bounds.minX);
            const scaleY = (canvas.height - 2 * padding) / (bounds.maxY - bounds.minY);
            const scale = Math.min(scaleX, scaleY);

            const cx = padding + (wx - bounds.minX) * scale;
            const cy = padding + (wy - bounds.minY) * scale;
            return [cx, cy];
        }}

        function interpolateStroke(points, factor) {{
            if (factor <= 1 || points.length < 2) return points;

            const result = [];
            for (let i = 0; i < points.length - 1; i++) {{
                const [x1, y1] = points[i];
                const [x2, y2] = points[i + 1];

                result.push([x1, y1]);

                for (let j = 1; j < factor; j++) {{
                    const t = j / factor;
                    const x = Math.round(x1 + t * (x2 - x1));
                    const y = Math.round(y1 + t * (y2 - y1));
                    result.push([x, y]);
                }}
            }}
            result.push(points[points.length - 1]);
            return result;
        }}

        function smoothStroke(points, window) {{
            if (points.length < window || window < 2) return points;

            const smoothed = [points[0]];

            for (let i = 1; i < points.length - 1; i++) {{
                const start = Math.max(0, i - Math.floor(window / 2));
                const end = Math.min(points.length, i + Math.floor(window / 2) + 1);

                let sumX = 0, sumY = 0;
                for (let j = start; j < end; j++) {{
                    sumX += points[j][0];
                    sumY += points[j][1];
                }}

                const avgX = Math.round(sumX / (end - start));
                const avgY = Math.round(sumY / (end - start));
                smoothed.push([avgX, avgY]);
            }}

            smoothed.push(points[points.length - 1]);
            return smoothed;
        }}

        function getProcessedStroke(stroke) {{
            let points = stroke.points;
            points = interpolateStroke(points, stroke.interpolation);
            points = smoothStroke(points, stroke.smoothing);
            return points;
        }}

        function drawStrokes() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw grid
            ctx.strokeStyle = '#f0f0f0';
            ctx.lineWidth = 1;
            for (let i = 0; i < canvas.width; i += 50) {{
                ctx.beginPath();
                ctx.moveTo(i, 0);
                ctx.lineTo(i, canvas.height);
                ctx.stroke();
            }}
            for (let i = 0; i < canvas.height; i += 50) {{
                ctx.beginPath();
                ctx.moveTo(0, i);
                ctx.lineTo(canvas.width, i);
                ctx.stroke();
            }}

            // Draw strokes
            strokes.forEach((stroke, idx) => {{
                if (!stroke.selected) return;

                const points = getProcessedStroke(stroke);
                if (points.length < 2) return;

                ctx.beginPath();
                const [x0, y0] = wacomToCanvas(points[0][0], points[0][1]);
                ctx.moveTo(x0, y0);

                for (let i = 1; i < points.length; i++) {{
                    const [x, y] = wacomToCanvas(points[i][0], points[i][1]);
                    ctx.lineTo(x, y);
                }}

                ctx.strokeStyle = idx === selectedStroke ? '#2196F3' : '#333';
                ctx.lineWidth = idx === selectedStroke ? 3 : 2;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                ctx.stroke();

                // Draw points for selected stroke
                if (idx === selectedStroke) {{
                    points.forEach(([wx, wy]) => {{
                        const [cx, cy] = wacomToCanvas(wx, wy);
                        ctx.fillStyle = '#2196F3';
                        ctx.beginPath();
                        ctx.arc(cx, cy, 2, 0, 2 * Math.PI);
                        ctx.fill();
                    }});
                }}
            }});

            updateStats();
        }}

        function updateStrokeList() {{
            const list = document.getElementById('strokeList');
            list.innerHTML = '';

            strokes.forEach((stroke, idx) => {{
                const div = document.createElement('div');
                div.className = 'stroke-item' +
                    (idx === selectedStroke ? ' selected' : '') +
                    (!stroke.selected ? ' hidden' : '');

                const points = getProcessedStroke(stroke);
                div.innerHTML = `
                    <span>
                        <input type="checkbox" class="checkbox"
                            ${{stroke.selected ? 'checked' : ''}}
                            onchange="toggleStroke(${{idx}})" />
                        Stroke ${{idx + 1}}
                    </span>
                    <span>${{points.length}} pts</span>
                `;
                div.onclick = (e) => {{
                    if (e.target.type !== 'checkbox') selectStroke(idx);
                }};
                list.appendChild(div);
            }});
        }}

        function selectStroke(idx) {{
            selectedStroke = idx;
            const stroke = strokes[idx];

            document.getElementById('interpSlider').value = stroke.interpolation;
            document.getElementById('interpValue').textContent = stroke.interpolation + 'x';
            document.getElementById('smoothSlider').value = stroke.smoothing;
            document.getElementById('smoothValue').textContent = stroke.smoothing;

            updateStrokeList();
            drawStrokes();
        }}

        function toggleStroke(idx) {{
            strokes[idx].selected = !strokes[idx].selected;
            updateStrokeList();
            drawStrokes();
        }}

        function updateStats() {{
            const totalStrokes = strokes.filter(s => s.selected).length;
            const totalPoints = strokes.filter(s => s.selected)
                .reduce((sum, s) => sum + getProcessedStroke(s).length, 0);
            const selectedPoints = getProcessedStroke(strokes[selectedStroke]).length;

            document.getElementById('totalStrokes').textContent = totalStrokes;
            document.getElementById('totalPoints').textContent = totalPoints;
            document.getElementById('selectedPoints').textContent = selectedPoints;
        }}

        function applyGlobalInterpolation() {{
            const factor = parseInt(document.getElementById('globalInterp').value);
            strokes.forEach(s => s.interpolation = factor);
            selectStroke(selectedStroke);  // Refresh UI
        }}

        function applyGlobalSmoothing() {{
            const window = parseInt(document.getElementById('globalSmooth').value);
            strokes.forEach(s => s.smoothing = window);
            selectStroke(selectedStroke);  // Refresh UI
        }}

        function resetAll() {{
            strokes = JSON.parse(JSON.stringify(originalStrokes));
            selectStroke(0);
        }}

        function exportCommands() {{
            const commands = [];
            strokes.forEach(stroke => {{
                if (!stroke.selected) return;

                const points = getProcessedStroke(stroke);
                if (points.length < 1) return;

                commands.push(`PEN_DOWN ${{points[0][0]}} ${{points[0][1]}}`);
                for (let i = 1; i < points.length; i++) {{
                    commands.push(`PEN_MOVE ${{points[i][0]}} ${{points[i][1]}}`);
                }}
                commands.push('PEN_UP');
            }});

            const blob = new Blob([commands.join('\\n') + '\\n'], {{type: 'text/plain'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'edited_strokes.txt';
            a.click();
            URL.revokeObjectURL(url);
        }}

        // Event listeners
        document.getElementById('interpSlider').oninput = function() {{
            const val = parseInt(this.value);
            document.getElementById('interpValue').textContent = val + 'x';
            strokes[selectedStroke].interpolation = val;
            drawStrokes();
        }};

        document.getElementById('smoothSlider').oninput = function() {{
            const val = parseInt(this.value);
            document.getElementById('smoothValue').textContent = val;
            strokes[selectedStroke].smoothing = val;
            drawStrokes();
        }};

        document.getElementById('globalInterp').oninput = function() {{
            document.getElementById('globalInterpValue').textContent = this.value + 'x';
        }};

        document.getElementById('globalSmooth').oninput = function() {{
            document.getElementById('globalSmoothValue').textContent = this.value;
        }};

        // Initialize
        selectStroke(0);
    </script>
</body>
</html>
"""
    return html


class EditorHandler(http.server.SimpleHTTPRequestHandler):
    html_content = None

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.html_content.encode())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # Suppress logging


def main():
    if len(sys.argv) < 2:
        print("Stroke Editor")
        print("=" * 70)
        print()
        print("Usage: python stroke_editor.py <input.txt>")
        print()
        print("Opens interactive web-based editor for PEN commands")
        print()
        print("Features:")
        print("  - Visual stroke display")
        print("  - Adjustable interpolation (1-30x)")
        print("  - Smoothing controls")
        print("  - Show/hide individual strokes")
        print("  - Export modified commands")
        print()
        return 1

    input_file = sys.argv[1]

    print("Loading strokes from:", input_file)
    strokes = parse_pen_commands(input_file)
    print(f"Loaded {len(strokes)} strokes")

    if not strokes:
        print("Error: No strokes found in file")
        return 1

    total_points = sum(len(s) for s in strokes)
    print(f"Total points: {total_points}")
    print()
    print("Generating editor interface...")

    html = generate_html_editor(strokes)
    EditorHandler.html_content = html

    port = 8000
    print(f"Starting editor on http://localhost:{port}")
    print()
    print("Opening browser...")

    # Start server in thread
    server = socketserver.TCPServer(("", port), EditorHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Open browser
    webbrowser.open(f'http://localhost:{port}')

    print()
    print("Editor running. Press Ctrl+C to stop.")
    print()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print()
        print("Shutting down...")
        server.shutdown()

    return 0


if __name__ == '__main__':
    sys.exit(main())
