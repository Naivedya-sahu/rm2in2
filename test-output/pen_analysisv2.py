#!/usr/bin/env python3
"""
RM2 Pen Event Analyzer v3 - Improved stroke detection

Usage:
    python analyze_pen_events_v3.py pen_shapes.txt [output_prefix]
"""

import re
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# Hardware limits
WACOM_X_MAX = 20966
WACOM_Y_MAX = 15725
PRESSURE_MAX = 4095

# Empirical usable bounds
WACOM_X_MIN_USABLE = 211
WACOM_X_MAX_USABLE = 20820
WACOM_Y_MIN_USABLE = 90
WACOM_Y_MAX_USABLE = 15712

# Display dimensions
DISPLAY_WIDTH = 1404
DISPLAY_HEIGHT = 1872


@dataclass
class RawEvent:
    """Raw parsed event."""
    timestamp: float
    event_type: str
    event_code: str
    value: int


@dataclass
class SynFrame:
    """All events between two SYN_REPORTs."""
    timestamp: float
    x: Optional[int] = None
    y: Optional[int] = None
    pressure: Optional[int] = None
    distance: Optional[int] = None
    btn_touch: Optional[int] = None  # 1=down, 0=up, None=no change
    btn_tool_pen: Optional[int] = None


@dataclass
class PenPoint:
    """Point in a stroke."""
    x: int
    y: int
    pressure: int
    timestamp: float


@dataclass 
class Stroke:
    """Complete pen stroke."""
    points: List[PenPoint] = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0
    
    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000 if self.end_time > self.start_time else 0
    
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
    def pressure_max(self) -> int:
        return max((p.pressure for p in self.points), default=0)
    
    @property
    def pressure_avg(self) -> float:
        pressures = [p.pressure for p in self.points if p.pressure > 0]
        return sum(pressures) / len(pressures) if pressures else 0


class RawEventParser:
    """First pass: parse raw events into SynFrames."""
    
    EVENT_PATTERN = re.compile(
        r'Event: time (\d+\.\d+), type \d+ \((\w+)\), code \d+ \((\w+)\), value (-?\d+)'
    )
    SYN_PATTERN = re.compile(r'Event: time (\d+\.\d+), -+ SYN_REPORT -+')
    
    def parse_file(self, filepath: str) -> Tuple[List[SynFrame], dict]:
        """Parse file into list of SynFrames."""
        frames = []
        current_frame = SynFrame(timestamp=0)
        
        # Running state (events only report changes)
        state_x = 0
        state_y = 0
        state_pressure = 0
        state_distance = 0
        
        stats = {
            'total_lines': 0,
            'event_lines': 0,
            'syn_lines': 0,
            'btn_touch_down': 0,
            'btn_touch_up': 0,
            'btn_pen_in': 0,
            'btn_pen_out': 0,
            'pressure_nonzero_frames': 0,
            'max_pressure_seen': 0,
            'min_nonzero_pressure': PRESSURE_MAX,
        }
        
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                stats['total_lines'] += 1
                line = line.strip()
                
                # Check for SYN_REPORT
                syn_match = self.SYN_PATTERN.match(line)
                if syn_match:
                    stats['syn_lines'] += 1
                    timestamp = float(syn_match.group(1))
                    
                    # Complete current frame with running state
                    current_frame.timestamp = timestamp
                    if current_frame.x is None:
                        current_frame.x = state_x
                    else:
                        state_x = current_frame.x
                    if current_frame.y is None:
                        current_frame.y = state_y
                    else:
                        state_y = current_frame.y
                    if current_frame.pressure is None:
                        current_frame.pressure = state_pressure
                    else:
                        state_pressure = current_frame.pressure
                    if current_frame.distance is None:
                        current_frame.distance = state_distance
                    else:
                        state_distance = current_frame.distance
                    
                    # Track stats
                    if current_frame.pressure > 0:
                        stats['pressure_nonzero_frames'] += 1
                        stats['max_pressure_seen'] = max(stats['max_pressure_seen'], current_frame.pressure)
                        stats['min_nonzero_pressure'] = min(stats['min_nonzero_pressure'], current_frame.pressure)
                    
                    frames.append(current_frame)
                    current_frame = SynFrame(timestamp=0)
                    continue
                
                # Check for event
                event_match = self.EVENT_PATTERN.match(line)
                if event_match:
                    stats['event_lines'] += 1
                    event_type = event_match.group(2)
                    event_code = event_match.group(3)
                    value = int(event_match.group(4))
                    
                    if event_type == 'EV_ABS':
                        if event_code == 'ABS_X':
                            current_frame.x = value
                        elif event_code == 'ABS_Y':
                            current_frame.y = value
                        elif event_code == 'ABS_PRESSURE':
                            current_frame.pressure = value
                        elif event_code == 'ABS_DISTANCE':
                            current_frame.distance = value
                    
                    elif event_type == 'EV_KEY':
                        if event_code == 'BTN_TOUCH':
                            current_frame.btn_touch = value
                            if value == 1:
                                stats['btn_touch_down'] += 1
                            else:
                                stats['btn_touch_up'] += 1
                        elif event_code == 'BTN_TOOL_PEN':
                            current_frame.btn_tool_pen = value
                            if value == 1:
                                stats['btn_pen_in'] += 1
                            else:
                                stats['btn_pen_out'] += 1
        
        if stats['min_nonzero_pressure'] == PRESSURE_MAX:
            stats['min_nonzero_pressure'] = 0
            
        return frames, stats


class StrokeExtractor:
    """Extract strokes from SynFrames using various methods."""
    
    def __init__(self, frames: List[SynFrame]):
        self.frames = frames
    
    def extract_by_pressure(self, threshold: int = 1, merge_gap_ms: float = 50) -> List[Stroke]:
        """
        Extract strokes based on pressure threshold.
        Merges strokes separated by less than merge_gap_ms.
        """
        strokes = []
        current_stroke: Optional[Stroke] = None
        
        for frame in self.frames:
            is_drawing = frame.pressure is not None and frame.pressure >= threshold
            
            if is_drawing:
                if current_stroke is None:
                    # Start new stroke
                    current_stroke = Stroke()
                    current_stroke.start_time = frame.timestamp
                
                # Add point
                point = PenPoint(
                    x=frame.x,
                    y=frame.y,
                    pressure=frame.pressure,
                    timestamp=frame.timestamp
                )
                current_stroke.points.append(point)
            else:
                if current_stroke is not None and current_stroke.points:
                    # End stroke
                    current_stroke.end_time = current_stroke.points[-1].timestamp
                    strokes.append(current_stroke)
                    current_stroke = None
        
        # Don't forget last stroke
        if current_stroke is not None and current_stroke.points:
            current_stroke.end_time = current_stroke.points[-1].timestamp
            strokes.append(current_stroke)
        
        # Merge strokes that are close together
        if merge_gap_ms > 0 and len(strokes) > 1:
            strokes = self._merge_close_strokes(strokes, merge_gap_ms)
        
        return strokes
    
    def extract_by_btn_touch(self) -> List[Stroke]:
        """Extract strokes based on BTN_TOUCH events."""
        strokes = []
        current_stroke: Optional[Stroke] = None
        is_touching = False
        
        for frame in self.frames:
            # Check for touch state change
            if frame.btn_touch == 1:
                is_touching = True
                current_stroke = Stroke()
                current_stroke.start_time = frame.timestamp
            elif frame.btn_touch == 0:
                is_touching = False
                if current_stroke is not None and current_stroke.points:
                    current_stroke.end_time = frame.timestamp
                    strokes.append(current_stroke)
                    current_stroke = None
            
            # Add points while touching
            if is_touching and current_stroke is not None:
                point = PenPoint(
                    x=frame.x,
                    y=frame.y,
                    pressure=frame.pressure if frame.pressure else 0,
                    timestamp=frame.timestamp
                )
                current_stroke.points.append(point)
        
        # Handle unclosed stroke
        if current_stroke is not None and current_stroke.points:
            current_stroke.end_time = current_stroke.points[-1].timestamp
            strokes.append(current_stroke)
        
        return strokes
    
    def extract_by_distance(self, touch_threshold: int = 10) -> List[Stroke]:
        """
        Extract strokes based on ABS_DISTANCE.
        Pen is touching when distance < threshold.
        """
        strokes = []
        current_stroke: Optional[Stroke] = None
        
        for frame in self.frames:
            is_touching = frame.distance is not None and frame.distance < touch_threshold
            
            if is_touching and frame.pressure and frame.pressure > 0:
                if current_stroke is None:
                    current_stroke = Stroke()
                    current_stroke.start_time = frame.timestamp
                
                point = PenPoint(
                    x=frame.x,
                    y=frame.y,
                    pressure=frame.pressure,
                    timestamp=frame.timestamp
                )
                current_stroke.points.append(point)
            else:
                if current_stroke is not None and current_stroke.points:
                    current_stroke.end_time = current_stroke.points[-1].timestamp
                    strokes.append(current_stroke)
                    current_stroke = None
        
        if current_stroke is not None and current_stroke.points:
            current_stroke.end_time = current_stroke.points[-1].timestamp
            strokes.append(current_stroke)
        
        return strokes
    
    def _merge_close_strokes(self, strokes: List[Stroke], gap_ms: float) -> List[Stroke]:
        """Merge strokes separated by less than gap_ms milliseconds."""
        if not strokes:
            return strokes
        
        merged = [strokes[0]]
        
        for stroke in strokes[1:]:
            gap = (stroke.start_time - merged[-1].end_time) * 1000
            
            if gap < gap_ms:
                # Merge with previous stroke
                merged[-1].points.extend(stroke.points)
                merged[-1].end_time = stroke.end_time
            else:
                merged.append(stroke)
        
        return merged
    
    def analyze_gaps(self) -> List[dict]:
        """Analyze pressure gaps to understand stroke boundaries."""
        gaps = []
        in_pressure = False
        pressure_start = 0
        last_pressure_end = 0
        
        for i, frame in enumerate(self.frames):
            has_pressure = frame.pressure is not None and frame.pressure > 0
            
            if has_pressure and not in_pressure:
                # Pressure started
                in_pressure = True
                pressure_start = frame.timestamp
                if last_pressure_end > 0:
                    gap_ms = (frame.timestamp - last_pressure_end) * 1000
                    gaps.append({
                        'gap_ms': round(gap_ms, 2),
                        'frame_index': i,
                        'timestamp': frame.timestamp
                    })
            elif not has_pressure and in_pressure:
                # Pressure ended
                in_pressure = False
                last_pressure_end = frame.timestamp
        
        return gaps


def generate_html_visualization(strokes: List[Stroke], bounds: dict, stats: dict, 
                                gaps: List[dict], output_path: str):
    """Generate HTML visualization."""
    
    stroke_data = []
    for stroke in strokes:
        stroke_data.append({
            'points': [(p.x, p.y, p.pressure) for p in stroke.points],
        })
    
    wx_min = WACOM_X_MIN_USABLE
    wx_max = WACOM_X_MAX_USABLE
    wy_min = WACOM_Y_MIN_USABLE
    wy_max = WACOM_Y_MAX_USABLE
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>RM2 Pen Capture Analysis v3</title>
    <style>
        body {{ font-family: monospace; margin: 20px; background: #1a1a1a; color: #fff; }}
        .container {{ display: flex; gap: 20px; flex-wrap: wrap; }}
        .panel {{ background: #2a2a2a; padding: 15px; border-radius: 8px; }}
        canvas {{ border: 1px solid #444; background: #fff; cursor: crosshair; }}
        h2 {{ margin-top: 0; color: #4a9eff; font-size: 14px; }}
        h3 {{ color: #7ab; font-size: 12px; margin: 15px 0 5px 0; }}
        .stats {{ font-size: 11px; line-height: 1.6; }}
        button {{ padding: 6px 12px; margin: 2px; cursor: pointer; background: #4a9eff; 
                  border: none; color: #fff; border-radius: 4px; font-size: 11px; }}
        button:hover {{ background: #3a8eef; }}
        #info {{ position: fixed; top: 10px; right: 10px; background: rgba(0,0,0,0.9); 
                 padding: 10px; border-radius: 4px; font-size: 11px; min-width: 180px; }}
        table {{ border-collapse: collapse; font-size: 10px; width: 100%; }}
        td, th {{ padding: 3px 6px; border: 1px solid #444; text-align: left; }}
        th {{ background: #333; }}
        .stroke-list {{ max-height: 250px; overflow-y: auto; font-size: 10px; }}
        .stroke-item {{ padding: 3px 6px; cursor: pointer; border-left: 3px solid #666; margin: 1px 0; }}
        .stroke-item:hover {{ background: #444; }}
        code {{ background: #333; padding: 1px 4px; border-radius: 2px; font-size: 10px; }}
        .gap-list {{ max-height: 150px; overflow-y: auto; font-size: 9px; }}
    </style>
</head>
<body>
    <h1 style="font-size:18px">RM2 Pen Capture Analysis v3</h1>
    
    <div id="info">Hover over canvas</div>
    
    <div class="container">
        <div class="panel">
            <h2>Wacom Space</h2>
            <canvas id="wacomCanvas" width="524" height="393"></canvas>
            <div style="margin-top:8px">
                <button onclick="playStrokes()">Play</button>
                <button onclick="resetView()">Reset</button>
                <button onclick="togglePressure()">Pressure Colors</button>
            </div>
        </div>
        
        <div class="panel">
            <h2>Display Space</h2>
            <canvas id="displayCanvas" width="281" height="374"></canvas>
        </div>
        
        <div class="panel" style="min-width:240px">
            <h2>Parse Statistics</h2>
            <table>
                <tr><td>Total lines</td><td>{stats.get('total_lines', 0):,}</td></tr>
                <tr><td>SYN frames</td><td>{stats.get('syn_lines', 0):,}</td></tr>
                <tr><td>BTN_TOUCH down</td><td>{stats.get('btn_touch_down', 0)}</td></tr>
                <tr><td>BTN_TOUCH up</td><td>{stats.get('btn_touch_up', 0)}</td></tr>
                <tr><td>BTN_PEN in</td><td>{stats.get('btn_pen_in', 0)}</td></tr>
                <tr><td>BTN_PEN out</td><td>{stats.get('btn_pen_out', 0)}</td></tr>
                <tr><td>Pressure frames</td><td>{stats.get('pressure_nonzero_frames', 0):,}</td></tr>
                <tr><td>Min pressure</td><td>{stats.get('min_nonzero_pressure', 0)}</td></tr>
                <tr><td>Max pressure</td><td>{stats.get('max_pressure_seen', 0)}</td></tr>
            </table>
            
            <h3>Capture Bounds</h3>
            <table>
                <tr><td>Wacom X</td><td>{bounds.get('wacom_x_min', 0)} - {bounds.get('wacom_x_max', 0)}</td></tr>
                <tr><td>Wacom Y</td><td>{bounds.get('wacom_y_min', 0)} - {bounds.get('wacom_y_max', 0)}</td></tr>
                <tr><td>Pressure</td><td>{bounds.get('pressure_min', 0)} - {bounds.get('pressure_max', 0)}</td></tr>
            </table>
            <p style="font-size:10px"><b>{bounds.get('total_strokes', 0)}</b> strokes, <b>{bounds.get('total_points', 0):,}</b> points</p>
            
            <h3>Strokes</h3>
            <div class="stroke-list" id="strokeList"></div>
            
            <h3>Pressure Gaps (stroke boundaries)</h3>
            <div class="gap-list">
                {''.join(f'<div style="color:#888">{g["gap_ms"]}ms @ frame {g["frame_index"]}</div>' for g in gaps[:30])}
                {f'<div>... and {len(gaps)-30} more</div>' if len(gaps) > 30 else ''}
            </div>
        </div>
    </div>
    
    <script>
    const strokes = {json.dumps(stroke_data)};
    
    const WX_MIN = {wx_min}, WX_MAX = {wx_max};
    const WY_MIN = {wy_min}, WY_MAX = {wy_max};
    const WACOM_X_FULL = {WACOM_X_MAX}, WACOM_Y_FULL = {WACOM_Y_MAX};
    const DISPLAY_W = {DISPLAY_WIDTH}, DISPLAY_H = {DISPLAY_HEIGHT};
    
    const wc = document.getElementById('wacomCanvas');
    const wctx = wc.getContext('2d');
    const dc = document.getElementById('displayCanvas');
    const dctx = dc.getContext('2d');
    
    const wsx = wc.width / WACOM_X_FULL;
    const wsy = wc.height / WACOM_Y_FULL;
    const dsx = dc.width / DISPLAY_W;
    const dsy = dc.height / DISPLAY_H;
    
    let showPressure = false;
    let animId = null;
    
    function w2d(wx, wy) {{
        return [(wy - WY_MIN) * DISPLAY_W / (WY_MAX - WY_MIN),
                (WX_MAX - wx) * DISPLAY_H / (WX_MAX - WX_MIN)];
    }}
    
    function pColor(p, mx) {{ return `hsl(${{(1-p/mx)*240}}, 80%, 45%)`; }}
    function sColor(i) {{ return `hsl(${{i*37%360}}, 70%, 45%)`; }}
    
    function draw() {{
        wctx.fillStyle = '#fff'; wctx.fillRect(0,0,wc.width,wc.height);
        wctx.fillStyle = '#f8f8f8';
        wctx.fillRect(WX_MIN*wsx, WY_MIN*wsy, (WX_MAX-WX_MIN)*wsx, (WY_MAX-WY_MIN)*wsy);
        
        dctx.fillStyle = '#fff'; dctx.fillRect(0,0,dc.width,dc.height);
        
        const mx = Math.max(...strokes.flatMap(s=>s.points.map(p=>p[2]))) || 1;
        
        strokes.forEach((s,idx) => {{
            if (s.points.length < 2) return;
            [wctx,dctx].forEach((ctx,ci) => {{
                ctx.lineWidth = 1.5; ctx.lineCap = 'round';
                for (let i=1; i<s.points.length; i++) {{
                    const p0=s.points[i-1], p1=s.points[i];
                    ctx.beginPath();
                    ctx.strokeStyle = showPressure ? pColor(p1[2],mx) : sColor(idx);
                    if (ci===0) {{
                        ctx.moveTo(p0[0]*wsx, p0[1]*wsy);
                        ctx.lineTo(p1[0]*wsx, p1[1]*wsy);
                    }} else {{
                        const [x0,y0]=w2d(p0[0],p0[1]), [x1,y1]=w2d(p1[0],p1[1]);
                        ctx.moveTo(x0*dsx, y0*dsy);
                        ctx.lineTo(x1*dsx, y1*dsy);
                    }}
                    ctx.stroke();
                }}
            }});
        }});
    }}
    
    function resetView() {{ if(animId)cancelAnimationFrame(animId); draw(); }}
    function togglePressure() {{ showPressure=!showPressure; draw(); }}
    
    function playStrokes() {{
        if(animId)cancelAnimationFrame(animId);
        wctx.fillStyle='#fff'; wctx.fillRect(0,0,wc.width,wc.height);
        wctx.fillStyle='#f8f8f8';
        wctx.fillRect(WX_MIN*wsx,WY_MIN*wsy,(WX_MAX-WX_MIN)*wsx,(WY_MAX-WY_MIN)*wsy);
        dctx.fillStyle='#fff'; dctx.fillRect(0,0,dc.width,dc.height);
        
        let si=0, pi=1;
        const mx = Math.max(...strokes.flatMap(s=>s.points.map(p=>p[2]))) || 1;
        
        function anim() {{
            if(si>=strokes.length) return;
            const s=strokes[si];
            if(s.points.length<2) {{ si++; pi=1; animId=requestAnimationFrame(anim); return; }}
            if(pi<s.points.length) {{
                const p0=s.points[pi-1], p1=s.points[pi];
                const c = showPressure ? pColor(p1[2],mx) : sColor(si);
                wctx.beginPath(); wctx.strokeStyle=c; wctx.lineWidth=1.5;
                wctx.moveTo(p0[0]*wsx,p0[1]*wsy); wctx.lineTo(p1[0]*wsx,p1[1]*wsy); wctx.stroke();
                const [x0,y0]=w2d(p0[0],p0[1]), [x1,y1]=w2d(p1[0],p1[1]);
                dctx.beginPath(); dctx.strokeStyle=c; dctx.lineWidth=1.5;
                dctx.moveTo(x0*dsx,y0*dsy); dctx.lineTo(x1*dsx,y1*dsy); dctx.stroke();
                pi++;
            }} else {{ si++; pi=1; }}
            animId=requestAnimationFrame(anim);
        }}
        anim();
    }}
    
    // Stroke list
    const sl = document.getElementById('strokeList');
    strokes.forEach((s,i) => {{
        const d = document.createElement('div');
        d.className = 'stroke-item';
        d.style.borderLeftColor = sColor(i);
        d.innerHTML = `#${{i+1}}: ${{s.points.length}} pts, max P=${{Math.max(...s.points.map(p=>p[2]))}}`;
        d.onclick = () => {{ 
            draw();
            [wctx,dctx].forEach((ctx,ci) => {{
                ctx.strokeStyle='#f00'; ctx.lineWidth=3; ctx.beginPath();
                s.points.forEach((p,j) => {{
                    const [x,y] = ci===0 ? [p[0]*wsx,p[1]*wsy] : (([dx,dy])=>[dx*dsx,dy*dsy])(w2d(p[0],p[1]));
                    j===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
                }});
                ctx.stroke();
            }});
        }};
        sl.appendChild(d);
    }});
    
    wc.onmousemove = e => {{
        const r=wc.getBoundingClientRect();
        const wx=Math.round((e.clientX-r.left)/wsx), wy=Math.round((e.clientY-r.top)/wsy);
        const [dx,dy]=w2d(wx,wy);
        document.getElementById('info').innerHTML=`<b>Wacom:</b> ${{wx}}, ${{wy}}<br><b>Display:</b> ${{Math.round(dx)}}, ${{Math.round(dy)}}`;
    }};
    
    draw();
    </script>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Created: {output_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else Path(input_file).stem
    
    print(f"Parsing: {input_file}")
    
    # Phase 1: Parse raw events
    parser = RawEventParser()
    frames, stats = parser.parse_file(input_file)
    
    print(f"\n{'='*60}")
    print("RAW PARSE STATS")
    print(f"{'='*60}")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # Phase 2: Extract strokes with different methods
    extractor = StrokeExtractor(frames)
    
    print(f"\n{'='*60}")
    print("STROKE EXTRACTION COMPARISON")
    print(f"{'='*60}")
    
    # Try pressure-based with different thresholds
    for thresh in [1, 5, 10, 50]:
        strokes = extractor.extract_by_pressure(threshold=thresh, merge_gap_ms=0)
        print(f"  Pressure >= {thresh}: {len(strokes)} strokes")
    
    # Try with merge
    for merge in [0, 20, 50, 100]:
        strokes = extractor.extract_by_pressure(threshold=1, merge_gap_ms=merge)
        print(f"  Pressure >= 1, merge {merge}ms: {len(strokes)} strokes")
    
    # BTN_TOUCH based
    strokes_btn = extractor.extract_by_btn_touch()
    print(f"  BTN_TOUCH events: {len(strokes_btn)} strokes")
    
    # Distance based
    strokes_dist = extractor.extract_by_distance(touch_threshold=10)
    print(f"  Distance < 10: {len(strokes_dist)} strokes")
    
    # Analyze gaps
    gaps = extractor.analyze_gaps()
    print(f"\n  Pressure gaps found: {len(gaps)}")
    if gaps:
        gap_values = [g['gap_ms'] for g in gaps]
        print(f"  Gap range: {min(gap_values):.1f}ms - {max(gap_values):.1f}ms")
        print(f"  Gaps > 100ms: {sum(1 for g in gap_values if g > 100)}")
        print(f"  Gaps > 500ms: {sum(1 for g in gap_values if g > 500)}")
    
    # Use best method for final output
    # Based on stats, choose appropriate parameters
    if stats['btn_touch_down'] > 0 and stats['btn_touch_down'] == stats['btn_touch_up']:
        # BTN_TOUCH events seem reliable
        strokes = extractor.extract_by_btn_touch()
        method = "btn_touch"
    else:
        # Use pressure with small merge
        strokes = extractor.extract_by_pressure(threshold=1, merge_gap_ms=30)
        method = "pressure>=1, merge=30ms"
    
    print(f"\n  Selected method: {method}")
    print(f"  Final stroke count: {len(strokes)}")
    
    # Calculate bounds
    if strokes:
        all_points = [p for s in strokes for p in s.points]
        bounds = {
            'wacom_x_min': min(p.x for p in all_points),
            'wacom_x_max': max(p.x for p in all_points),
            'wacom_y_min': min(p.y for p in all_points),
            'wacom_y_max': max(p.y for p in all_points),
            'pressure_min': min(p.pressure for p in all_points),
            'pressure_max': max(p.pressure for p in all_points),
            'total_points': len(all_points),
            'total_strokes': len(strokes),
        }
    else:
        bounds = {'total_strokes': 0, 'total_points': 0}
    
    print(f"\n{'='*60}")
    print("STROKE DETAILS")
    print(f"{'='*60}")
    for i, s in enumerate(strokes[:25]):
        print(f"  #{i+1}: {len(s.points)} pts, {s.duration_ms:.0f}ms, "
              f"P={s.pressure_max}, X={s.x_min}-{s.x_max}, Y={s.y_min}-{s.y_max}")
    if len(strokes) > 25:
        print(f"  ... and {len(strokes)-25} more")
    
    # Generate outputs
    output_dir = Path(input_file).parent
    
    generate_html_visualization(strokes, bounds, stats, gaps,
                                str(output_dir / f"{output_prefix}_viz.html"))
    
    # Replay file
    replay_path = output_dir / f"{output_prefix}_replay.txt"
    with open(replay_path, 'w', encoding='utf-8') as f:
        f.write(f"# Strokes: {len(strokes)}, Method: {method}\n\n")
        for i, s in enumerate(strokes):
            if not s.points:
                continue
            f.write(f"# Stroke {i+1} ({len(s.points)} pts)\n")
            f.write(f"PEN_DOWN {s.points[0].x} {s.points[0].y}\n")
            for p in s.points[1:]:
                f.write(f"PEN_MOVE {p.x} {p.y}\n")
            f.write("PEN_UP\nDELAY 50\n\n")
    print(f"Created: {replay_path}")
    
    # JSON analysis
    json_path = output_dir / f"{output_prefix}_analysis.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'stats': stats,
            'bounds': bounds,
            'method': method,
            'gaps_summary': {
                'count': len(gaps),
                'min_ms': min(g['gap_ms'] for g in gaps) if gaps else 0,
                'max_ms': max(g['gap_ms'] for g in gaps) if gaps else 0,
            },
            'strokes': [{'points': len(s.points), 'duration_ms': s.duration_ms, 
                        'pressure_max': s.pressure_max} for s in strokes]
        }, f, indent=2)
    print(f"Created: {json_path}")
    
    print(f"\n{'='*60}")
    print("RECOMMENDATION")
    print(f"{'='*60}")
    print(f"BTN_TOUCH events: {stats['btn_touch_down']} down, {stats['btn_touch_up']} up")
    if stats['btn_touch_down'] != stats['btn_touch_up']:
        print("  WARNING: Mismatched BTN_TOUCH events - some strokes may be truncated")
    if stats['btn_touch_down'] < len(gaps):
        print(f"  NOTE: More pressure gaps ({len(gaps)}) than BTN_TOUCH events ({stats['btn_touch_down']})")
        print("        Some strokes may have brief pressure drops that split them")


if __name__ == "__main__":
    main()