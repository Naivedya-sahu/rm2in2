#!/usr/bin/env python3
"""
RM2 Pen Event Analyzer

Parses raw evtest output, extracts strokes, visualizes data,
and derives coordinate transformation parameters.

Usage:
    python analyze_pen_events.py pen_shapes.txt [output_prefix]
"""

import re
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

# Hardware limits from evtest header
WACOM_X_MAX = 20966
WACOM_Y_MAX = 15725
PRESSURE_MAX = 4095

# Empirical usable bounds (from corner capture)
WACOM_X_MIN_USABLE = 211
WACOM_X_MAX_USABLE = 20820
WACOM_Y_MIN_USABLE = 90
WACOM_Y_MAX_USABLE = 15712

# Display dimensions
DISPLAY_WIDTH = 1404
DISPLAY_HEIGHT = 1872


@dataclass
class PenPoint:
    """Point in a stroke."""
    x: int
    y: int
    pressure: int
    timestamp: float


@dataclass
class Stroke:
    """Complete pen stroke from touch-down to touch-up."""
    points: List[PenPoint] = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0
    
    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000
    
    @property
    def x_min(self) -> int:
        return min(p.x for p in self.points) if self.points else 0
    
    @property
    def x_max(self) -> int:
        return max(p.x for p in self.points) if self.points else 0
    
    @property
    def y_min(self) -> int:
        return min(p.y for p in self.points) if self.points else 0
    
    @property
    def y_max(self) -> int:
        return max(p.y for p in self.points) if self.points else 0
    
    @property
    def pressure_avg(self) -> float:
        return sum(p.pressure for p in self.points) / len(self.points) if self.points else 0


class PenEventParser:
    """Parse evtest output into structured stroke data."""
    
    EVENT_PATTERN = re.compile(
        r'Event: time (\d+\.\d+), type \d+ \((\w+)\), code \d+ \((\w+)\), value (-?\d+)'
    )
    SYN_PATTERN = re.compile(r'Event: time (\d+\.\d+), -+ SYN_REPORT -+')
    
    def __init__(self):
        self.strokes: List[Stroke] = []
        self.current_stroke: Optional[Stroke] = None
        self.pen_down = False
        self.state_x = 0
        self.state_y = 0
        self.state_pressure = 0
    
    def parse_file(self, filepath: str) -> List[Stroke]:
        """Parse evtest output file and return list of strokes."""
        with open(filepath, 'r') as f:
            for line in f:
                self._parse_line(line.strip())
        
        if self.current_stroke and self.current_stroke.points:
            self.strokes.append(self.current_stroke)
        
        return self.strokes
    
    def _parse_line(self, line: str):
        """Parse a single line of evtest output."""
        syn_match = self.SYN_PATTERN.match(line)
        if syn_match:
            timestamp = float(syn_match.group(1))
            self._process_syn(timestamp)
            return
        
        event_match = self.EVENT_PATTERN.match(line)
        if event_match:
            timestamp = float(event_match.group(1))
            event_type = event_match.group(2)
            event_code = event_match.group(3)
            value = int(event_match.group(4))
            
            if event_type == 'EV_ABS':
                if event_code == 'ABS_X':
                    self.state_x = value
                elif event_code == 'ABS_Y':
                    self.state_y = value
                elif event_code == 'ABS_PRESSURE':
                    self.state_pressure = value
            
            elif event_type == 'EV_KEY':
                if event_code == 'BTN_TOUCH':
                    if value == 1:
                        self.pen_down = True
                        self.current_stroke = Stroke()
                        self.current_stroke.start_time = timestamp
                    elif value == 0:
                        self.pen_down = False
                        if self.current_stroke:
                            self.current_stroke.end_time = timestamp
                            if self.current_stroke.points:
                                self.strokes.append(self.current_stroke)
                            self.current_stroke = None
    
    def _process_syn(self, timestamp: float):
        """Process SYN_REPORT - commit current event state."""
        if self.pen_down and self.current_stroke is not None:
            point = PenPoint(
                x=self.state_x,
                y=self.state_y,
                pressure=self.state_pressure,
                timestamp=timestamp
            )
            self.current_stroke.points.append(point)


class StrokeAnalyzer:
    """Analyze strokes to derive coordinate mapping."""
    
    def __init__(self, strokes: List[Stroke]):
        self.strokes = strokes
    
    def get_bounds(self) -> dict:
        """Get overall coordinate bounds from all strokes."""
        if not self.strokes:
            return {}
        
        all_points = [p for s in self.strokes for p in s.points]
        
        return {
            'wacom_x_min': min(p.x for p in all_points),
            'wacom_x_max': max(p.x for p in all_points),
            'wacom_y_min': min(p.y for p in all_points),
            'wacom_y_max': max(p.y for p in all_points),
            'pressure_min': min(p.pressure for p in all_points),
            'pressure_max': max(p.pressure for p in all_points),
            'total_points': len(all_points),
            'total_strokes': len(self.strokes),
        }
    
    def get_stroke_summary(self) -> List[dict]:
        """Get summary of each stroke."""
        summaries = []
        for i, stroke in enumerate(self.strokes):
            summaries.append({
                'index': i,
                'points': len(stroke.points),
                'duration_ms': round(stroke.duration_ms, 1),
                'x_range': f"{stroke.x_min}-{stroke.x_max}",
                'y_range': f"{stroke.y_min}-{stroke.y_max}",
                'pressure_avg': round(stroke.pressure_avg, 0),
                'start': (stroke.points[0].x, stroke.points[0].y) if stroke.points else None,
                'end': (stroke.points[-1].x, stroke.points[-1].y) if stroke.points else None,
            })
        return summaries


def generate_html_visualization(strokes: List[Stroke], bounds: dict, output_path: str):
    """Generate HTML file with interactive stroke visualization."""
    
    stroke_data = []
    for stroke in strokes:
        stroke_data.append({
            'points': [(p.x, p.y, p.pressure) for p in stroke.points]
        })
    
    # Use empirical full-screen bounds for proper visualization
    wx_min = WACOM_X_MIN_USABLE
    wx_max = WACOM_X_MAX_USABLE
    wy_min = WACOM_Y_MIN_USABLE
    wy_max = WACOM_Y_MAX_USABLE
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>RM2 Pen Capture Visualization</title>
    <style>
        body {{ font-family: monospace; margin: 20px; background: #1a1a1a; color: #fff; }}
        .container {{ display: flex; gap: 20px; flex-wrap: wrap; }}
        .panel {{ background: #2a2a2a; padding: 15px; border-radius: 8px; }}
        canvas {{ border: 1px solid #444; background: #fff; }}
        h2 {{ margin-top: 0; color: #4a9eff; }}
        .stats {{ font-size: 12px; line-height: 1.6; }}
        .controls {{ margin: 10px 0; }}
        button {{ padding: 8px 16px; margin-right: 10px; cursor: pointer; }}
        #info {{ position: fixed; top: 10px; right: 10px; background: rgba(0,0,0,0.8); 
                 padding: 10px; border-radius: 4px; font-size: 11px; }}
        table {{ border-collapse: collapse; font-size: 11px; }}
        td, th {{ padding: 4px 8px; border: 1px solid #444; }}
    </style>
</head>
<body>
    <h1>RM2 Pen Capture Analysis</h1>
    
    <div id="info">Move mouse over canvas</div>
    
    <div class="container">
        <div class="panel">
            <h2>Wacom Coordinate Space (Raw Hardware)</h2>
            <canvas id="wacomCanvas" width="628" height="471"></canvas>
            <p style="font-size:11px">Wacom X: 0-20966 (vertical), Y: 0-15725 (horizontal)</p>
            <div class="controls">
                <button onclick="playStrokes()">Play Animation</button>
                <button onclick="resetView()">Reset</button>
            </div>
        </div>
        
        <div class="panel">
            <h2>Display Space (Transformed)</h2>
            <canvas id="displayCanvas" width="351" height="468"></canvas>
            <p style="font-size:11px">Display: 1404×1872 (portrait)</p>
        </div>
        
        <div class="panel">
            <h2>Capture Statistics</h2>
            <div class="stats">
                <table>
                    <tr><th>Metric</th><th>This Capture</th><th>Full Screen*</th></tr>
                    <tr><td>Wacom X min</td><td>{bounds['wacom_x_min']}</td><td>{wx_min}</td></tr>
                    <tr><td>Wacom X max</td><td>{bounds['wacom_x_max']}</td><td>{wx_max}</td></tr>
                    <tr><td>Wacom Y min</td><td>{bounds['wacom_y_min']}</td><td>{wy_min}</td></tr>
                    <tr><td>Wacom Y max</td><td>{bounds['wacom_y_max']}</td><td>{wy_max}</td></tr>
                    <tr><td>Pressure</td><td>{bounds['pressure_min']}-{bounds['pressure_max']}</td><td>0-4095</td></tr>
                    <tr><td>Strokes</td><td>{bounds['total_strokes']}</td><td>-</td></tr>
                    <tr><td>Points</td><td>{bounds['total_points']}</td><td>-</td></tr>
                </table>
                <p style="margin-top:10px">*From corner calibration capture</p>
            </div>
            
            <h2 style="margin-top:20px">Transformation</h2>
            <div class="stats">
                <p><strong>Wacom → Display:</strong></p>
                <code>
                display_x = (wacom_y - {wy_min}) × {DISPLAY_WIDTH} / {wy_max - wy_min}<br>
                display_y = ({wx_max} - wacom_x) × {DISPLAY_HEIGHT} / {wx_max - wx_min}
                </code>
                <p style="margin-top:10px"><strong>Display → Wacom:</strong></p>
                <code>
                wacom_x = {wx_max} - display_y × {wx_max - wx_min} / {DISPLAY_HEIGHT}<br>
                wacom_y = {wy_min} + display_x × {wy_max - wy_min} / {DISPLAY_WIDTH}
                </code>
            </div>
        </div>
    </div>
    
    <script>
    const strokes = {json.dumps(stroke_data)};
    
    // Empirical full-screen bounds
    const WX_MIN = {wx_min};
    const WX_MAX = {wx_max};
    const WY_MIN = {wy_min};
    const WY_MAX = {wy_max};
    const DISPLAY_W = {DISPLAY_WIDTH};
    const DISPLAY_H = {DISPLAY_HEIGHT};
    
    const wacomCanvas = document.getElementById('wacomCanvas');
    const wacomCtx = wacomCanvas.getContext('2d');
    const displayCanvas = document.getElementById('displayCanvas');
    const displayCtx = displayCanvas.getContext('2d');
    
    // Wacom to canvas scaling
    const wacomScaleX = wacomCanvas.width / {WACOM_X_MAX};
    const wacomScaleY = wacomCanvas.height / {WACOM_Y_MAX};
    
    // Display to canvas scaling
    const displayScaleX = displayCanvas.width / DISPLAY_W;
    const displayScaleY = displayCanvas.height / DISPLAY_H;
    
    function wacomToDisplay(wx, wy) {{
        const dx = (wy - WY_MIN) * DISPLAY_W / (WY_MAX - WY_MIN);
        const dy = (WX_MAX - wx) * DISPLAY_H / (WX_MAX - WX_MIN);
        return [dx, dy];
    }}
    
    function displayToWacom(dx, dy) {{
        const wx = WX_MAX - dy * (WX_MAX - WX_MIN) / DISPLAY_H;
        const wy = WY_MIN + dx * (WY_MAX - WY_MIN) / DISPLAY_W;
        return [wx, wy];
    }}
    
    function drawWacomSpace() {{
        wacomCtx.fillStyle = '#fff';
        wacomCtx.fillRect(0, 0, wacomCanvas.width, wacomCanvas.height);
        
        // Draw usable area boundary
        wacomCtx.strokeStyle = '#ccc';
        wacomCtx.lineWidth = 1;
        wacomCtx.strokeRect(
            WX_MIN * wacomScaleX, WY_MIN * wacomScaleY,
            (WX_MAX - WX_MIN) * wacomScaleX, (WY_MAX - WY_MIN) * wacomScaleY
        );
        
        // Draw strokes
        strokes.forEach((stroke, idx) => {{
            if (stroke.points.length < 2) return;
            
            wacomCtx.beginPath();
            wacomCtx.strokeStyle = `hsl(${{idx * 40 % 360}}, 70%, 40%)`;
            wacomCtx.lineWidth = 1.5;
            
            stroke.points.forEach((p, i) => {{
                const x = p[0] * wacomScaleX;
                const y = p[1] * wacomScaleY;
                if (i === 0) wacomCtx.moveTo(x, y);
                else wacomCtx.lineTo(x, y);
            }});
            wacomCtx.stroke();
        }});
    }}
    
    function drawDisplaySpace() {{
        displayCtx.fillStyle = '#fff';
        displayCtx.fillRect(0, 0, displayCanvas.width, displayCanvas.height);
        
        // Draw strokes transformed to display space
        strokes.forEach((stroke, idx) => {{
            if (stroke.points.length < 2) return;
            
            displayCtx.beginPath();
            displayCtx.strokeStyle = `hsl(${{idx * 40 % 360}}, 70%, 40%)`;
            displayCtx.lineWidth = 1.5;
            
            stroke.points.forEach((p, i) => {{
                const [dx, dy] = wacomToDisplay(p[0], p[1]);
                const x = dx * displayScaleX;
                const y = dy * displayScaleY;
                if (i === 0) displayCtx.moveTo(x, y);
                else displayCtx.lineTo(x, y);
            }});
            displayCtx.stroke();
        }});
    }}
    
    function resetView() {{
        drawWacomSpace();
        drawDisplaySpace();
    }}
    
    let animationId = null;
    function playStrokes() {{
        if (animationId) cancelAnimationFrame(animationId);
        
        wacomCtx.fillStyle = '#fff';
        wacomCtx.fillRect(0, 0, wacomCanvas.width, wacomCanvas.height);
        displayCtx.fillStyle = '#fff';
        displayCtx.fillRect(0, 0, displayCanvas.width, displayCanvas.height);
        
        let strokeIdx = 0;
        let pointIdx = 0;
        
        function animate() {{
            if (strokeIdx >= strokes.length) return;
            
            const stroke = strokes[strokeIdx];
            const color = `hsl(${{strokeIdx * 40 % 360}}, 70%, 40%)`;
            
            if (pointIdx < stroke.points.length) {{
                const p = stroke.points[pointIdx];
                const wx = p[0] * wacomScaleX;
                const wy = p[1] * wacomScaleY;
                const [dx, dy] = wacomToDisplay(p[0], p[1]);
                const dxs = dx * displayScaleX;
                const dys = dy * displayScaleY;
                
                if (pointIdx === 0) {{
                    wacomCtx.beginPath();
                    wacomCtx.strokeStyle = color;
                    wacomCtx.lineWidth = 1.5;
                    wacomCtx.moveTo(wx, wy);
                    
                    displayCtx.beginPath();
                    displayCtx.strokeStyle = color;
                    displayCtx.lineWidth = 1.5;
                    displayCtx.moveTo(dxs, dys);
                }} else {{
                    wacomCtx.lineTo(wx, wy);
                    wacomCtx.stroke();
                    wacomCtx.beginPath();
                    wacomCtx.moveTo(wx, wy);
                    
                    displayCtx.lineTo(dxs, dys);
                    displayCtx.stroke();
                    displayCtx.beginPath();
                    displayCtx.moveTo(dxs, dys);
                }}
                pointIdx++;
            }} else {{
                strokeIdx++;
                pointIdx = 0;
            }}
            
            animationId = requestAnimationFrame(animate);
        }}
        animate();
    }}
    
    wacomCanvas.addEventListener('mousemove', (e) => {{
        const rect = wacomCanvas.getBoundingClientRect();
        const wx = Math.round((e.clientX - rect.left) / wacomScaleX);
        const wy = Math.round((e.clientY - rect.top) / wacomScaleY);
        const [dx, dy] = wacomToDisplay(wx, wy);
        
        document.getElementById('info').innerHTML = 
            `<b>Wacom:</b> (${{wx}}, ${{wy}})<br>` +
            `<b>Display:</b> (${{Math.round(dx)}}, ${{Math.round(dy)}})`;
    }});
    
    displayCanvas.addEventListener('mousemove', (e) => {{
        const rect = displayCanvas.getBoundingClientRect();
        const dx = (e.clientX - rect.left) / displayScaleX;
        const dy = (e.clientY - rect.top) / displayScaleY;
        const [wx, wy] = displayToWacom(dx, dy);
        
        document.getElementById('info').innerHTML = 
            `<b>Display:</b> (${{Math.round(dx)}}, ${{Math.round(dy)}})<br>` +
            `<b>Wacom:</b> (${{Math.round(wx)}}, ${{Math.round(wy)}})`;
    }});
    
    resetView();
    </script>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Created visualization: {output_path}")


def generate_replay_commands(strokes: List[Stroke], output_path: str):
    """Generate PEN commands to replay captured strokes (raw Wacom coords)."""
    lines = [
        "# Replay of captured pen events (RAW WACOM COORDINATES)",
        "# These are direct hardware coordinates, NOT display coordinates",
        "# Use this to test if raw replay works before transformation",
        "#",
        f"# Total strokes: {len(strokes)}",
        "#",
        ""
    ]
    
    for i, stroke in enumerate(strokes):
        if not stroke.points:
            continue
        
        lines.append(f"# Stroke {i+1} ({len(stroke.points)} points, {stroke.duration_ms:.0f}ms)")
        
        p = stroke.points[0]
        lines.append(f"PEN_DOWN {p.x} {p.y}")
        
        for p in stroke.points[1:]:
            lines.append(f"PEN_MOVE {p.x} {p.y}")
        
        lines.append("PEN_UP")
        lines.append("DELAY 50")
        lines.append("")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Created replay commands: {output_path}")


def generate_inject_constants(bounds: dict, output_path: str):
    """Generate C header constants for inject.c."""
    
    content = f'''/*
 * RM2 Coordinate Transformation Constants
 * Generated from empirical pen capture analysis
 * 
 * Coordinate System:
 *   Display: 1404×1872 portrait (X=left-right, Y=top-bottom, origin top-left)
 *   Wacom:   Rotated 90° and Y-inverted relative to display
 *   
 * Mapping:
 *   Display X (0-1404) → Wacom Y ({WACOM_Y_MIN_USABLE} to {WACOM_Y_MAX_USABLE})
 *   Display Y (0-1872) → Wacom X ({WACOM_X_MAX_USABLE} down to {WACOM_X_MIN_USABLE}) [inverted]
 */

#ifndef RM2_COORD_H
#define RM2_COORD_H

// Display dimensions
#define DISPLAY_WIDTH   {DISPLAY_WIDTH}
#define DISPLAY_HEIGHT  {DISPLAY_HEIGHT}

// Wacom hardware limits (from evtest)
#define WACOM_HW_X_MAX  {WACOM_X_MAX}
#define WACOM_HW_Y_MAX  {WACOM_Y_MAX}

// Empirical usable bounds (from corner calibration)
#define WACOM_X_MIN     {WACOM_X_MIN_USABLE}
#define WACOM_X_MAX     {WACOM_X_MAX_USABLE}
#define WACOM_Y_MIN     {WACOM_Y_MIN_USABLE}
#define WACOM_Y_MAX     {WACOM_Y_MAX_USABLE}

// Calculated ranges
#define WACOM_X_RANGE   (WACOM_X_MAX - WACOM_X_MIN)  // {WACOM_X_MAX_USABLE - WACOM_X_MIN_USABLE}
#define WACOM_Y_RANGE   (WACOM_Y_MAX - WACOM_Y_MIN)  // {WACOM_Y_MAX_USABLE - WACOM_Y_MIN_USABLE}

// Pressure
#define PRESSURE_MAX    {PRESSURE_MAX}
#define PRESSURE_DEFAULT 2000

/*
 * Transform display coordinates to Wacom coordinates
 * 
 * display_x: 0 (left) to 1404 (right)
 * display_y: 0 (top) to 1872 (bottom)
 */
static inline int display_to_wacom_x(int display_x, int display_y) {{
    // Display Y maps to Wacom X (inverted)
    return WACOM_X_MAX - (display_y * WACOM_X_RANGE / DISPLAY_HEIGHT);
}}

static inline int display_to_wacom_y(int display_x, int display_y) {{
    // Display X maps to Wacom Y
    return WACOM_Y_MIN + (display_x * WACOM_Y_RANGE / DISPLAY_WIDTH);
}}

/*
 * Bounds checking
 */
static inline int clamp_wacom_x(int x) {{
    if (x < WACOM_X_MIN) return WACOM_X_MIN;
    if (x > WACOM_X_MAX) return WACOM_X_MAX;
    return x;
}}

static inline int clamp_wacom_y(int y) {{
    if (y < WACOM_Y_MIN) return WACOM_Y_MIN;
    if (y > WACOM_Y_MAX) return WACOM_Y_MAX;
    return y;
}}

#endif // RM2_COORD_H
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created C header: {output_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else Path(input_file).stem
    
    print(f"Parsing: {input_file}")
    
    parser = PenEventParser()
    strokes = parser.parse_file(input_file)
    
    print(f"Found {len(strokes)} strokes")
    
    analyzer = StrokeAnalyzer(strokes)
    bounds = analyzer.get_bounds()
    
    print("\n" + "="*60)
    print("COORDINATE BOUNDS (this capture)")
    print("="*60)
    print(f"Wacom X: {bounds['wacom_x_min']} to {bounds['wacom_x_max']} (range: {bounds['wacom_x_max'] - bounds['wacom_x_min']})")
    print(f"Wacom Y: {bounds['wacom_y_min']} to {bounds['wacom_y_max']} (range: {bounds['wacom_y_max'] - bounds['wacom_y_min']})")
    print(f"Pressure: {bounds['pressure_min']} to {bounds['pressure_max']}")
    print(f"Total points: {bounds['total_points']}")
    
    print("\n" + "="*60)
    print("EMPIRICAL FULL-SCREEN BOUNDS (from corner calibration)")
    print("="*60)
    print(f"Wacom X: {WACOM_X_MIN_USABLE} to {WACOM_X_MAX_USABLE} (range: {WACOM_X_MAX_USABLE - WACOM_X_MIN_USABLE})")
    print(f"Wacom Y: {WACOM_Y_MIN_USABLE} to {WACOM_Y_MAX_USABLE} (range: {WACOM_Y_MAX_USABLE - WACOM_Y_MIN_USABLE})")
    
    summaries = analyzer.get_stroke_summary()
    print("\n" + "="*60)
    print("STROKE SUMMARY")
    print("="*60)
    for s in summaries[:15]:
        print(f"  Stroke {s['index']}: {s['points']} pts, {s['duration_ms']}ms, "
              f"X:{s['x_range']}, Y:{s['y_range']}")
    if len(summaries) > 15:
        print(f"  ... and {len(summaries) - 15} more strokes")
    
    output_dir = Path(input_file).parent
    
    generate_html_visualization(strokes, bounds, str(output_dir / f"{output_prefix}_visualization.html"))
    generate_replay_commands(strokes, str(output_dir / f"{output_prefix}_replay.txt"))
    generate_inject_constants(bounds, str(output_dir / f"{output_prefix}_constants.h"))
    
    analysis = {
        'bounds': bounds,
        'empirical_bounds': {
            'wacom_x_min': WACOM_X_MIN_USABLE,
            'wacom_x_max': WACOM_X_MAX_USABLE,
            'wacom_y_min': WACOM_Y_MIN_USABLE,
            'wacom_y_max': WACOM_Y_MAX_USABLE,
        },
        'strokes': summaries
    }
    json_path = output_dir / f"{output_prefix}_analysis.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2)
    print(f"Created analysis JSON: {json_path}")
    
    print("\n" + "="*60)
    print("DERIVED TRANSFORMATION FOR inject.c")
    print("="*60)
    print(f"""
Display → Wacom:
  wacom_x = {WACOM_X_MAX_USABLE} - (display_y * {WACOM_X_MAX_USABLE - WACOM_X_MIN_USABLE} / {DISPLAY_HEIGHT})
  wacom_y = {WACOM_Y_MIN_USABLE} + (display_x * {WACOM_Y_MAX_USABLE - WACOM_Y_MIN_USABLE} / {DISPLAY_WIDTH})

Key insight:
- Display Y axis maps to Wacom X axis (INVERTED - high to low)
- Display X axis maps to Wacom Y axis (normal - low to high)
- Must use empirical bounds, not hardware max (0-20966)
""")


if __name__ == "__main__":
    main()