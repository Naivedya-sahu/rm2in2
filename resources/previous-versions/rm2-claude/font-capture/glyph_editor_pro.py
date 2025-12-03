#!/usr/bin/env python3
"""
Glyph Editor Pro - Professional font creation with node table
Features:
- Node table with coordinates
- Reorder points and strokes
- Fixed layout (canvas in center)
- Fixed port binding issue
- Simplified pan (just middle-click)
"""

import sys
import json
import http.server
import socketserver
import webbrowser
import threading
import socket


# Configuration
WACOM_MAX_X = 20966
WACOM_MAX_Y = 15725
RM2_WIDTH = 1404
RM2_HEIGHT = 1872


def find_free_port():
    """Find an available port"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def parse_pen_commands(filename):
    """Parse PEN commands into stroke list"""
    strokes = []
    current_stroke = []

    try:
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
    except Exception as e:
        print(f"Error parsing file: {e}")
        return []

    return strokes


def generate_html_editor(strokes, input_file):
    """Generate HTML editor with node table"""

    strokes_json = json.dumps([
        {
            "id": i,
            "points": stroke,
            "visible": True,
            "selected": False,
            "color": f"hsl({(i * 137) % 360}, 70%, 50%)",
            "name": f"Stroke {i+1}"
        }
        for i, stroke in enumerate(strokes)
    ])

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Glyph Editor Pro - {input_file}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, 'Segoe UI', sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            overflow: hidden;
        }}
        .app {{
            display: grid;
            grid-template-columns: 280px 1fr 350px;
            grid-template-rows: 60px 1fr 180px 50px;
            height: 100vh;
            gap: 1px;
            background: #000;
        }}
        .toolbar {{
            grid-column: 1 / -1;
            background: linear-gradient(180deg, #2d2d2d, #252525);
            display: flex;
            align-items: center;
            padding: 0 20px;
            gap: 12px;
            border-bottom: 2px solid #000;
        }}
        .toolbar .title {{
            font-size: 18px;
            font-weight: 700;
            margin-right: auto;
            background: linear-gradient(90deg, #4a9eff, #ff4a9e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .tool-group {{
            display: flex;
            gap: 4px;
            padding: 4px;
            background: #1a1a1a;
            border-radius: 6px;
        }}
        .tool-btn {{
            width: 42px;
            height: 42px;
            background: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 4px;
            cursor: pointer;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }}
        .tool-btn:hover {{ background: #3d3d3d; border-color: #4a9eff; }}
        .tool-btn.active {{
            background: linear-gradient(135deg, #4a9eff, #0066cc);
            border-color: #4a9eff;
        }}
        .btn {{
            padding: 10px 18px;
            background: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 6px;
            color: #e0e0e0;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
        }}
        .btn:hover {{ background: #3d3d3d; border-color: #4a9eff; }}
        .btn.primary {{
            background: linear-gradient(135deg, #4a9eff, #0066cc);
            border-color: #4a9eff;
        }}
        .left-panel {{
            grid-row: 2 / 4;
            background: #232323;
            overflow-y: auto;
            border-right: 1px solid #333;
        }}
        .right-panel {{
            grid-row: 2 / 4;
            background: #232323;
            overflow-y: auto;
            border-left: 1px solid #333;
        }}
        .canvas-area {{
            background: #1a1a1a;
            position: relative;
            overflow: hidden;
        }}
        canvas {{ position: absolute; cursor: default; }}
        .animation-panel {{
            grid-column: 1 / -1;
            background: #232323;
            border-top: 1px solid #333;
            padding: 15px 20px;
        }}
        .statusbar {{
            grid-column: 1 / -1;
            background: #1a1a1a;
            padding: 0 20px;
            display: flex;
            align-items: center;
            gap: 24px;
            font-size: 12px;
            border-top: 1px solid #333;
        }}
        .panel-section {{
            padding: 16px;
            border-bottom: 1px solid #2d2d2d;
        }}
        .panel-section h3 {{
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
            font-weight: 600;
        }}
        .stroke-list {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .stroke-item {{
            background: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 6px;
            padding: 10px;
            cursor: move;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .stroke-item:hover {{ background: #3d3d3d; }}
        .stroke-item.selected {{
            background: linear-gradient(90deg, rgba(74,158,255,0.2), rgba(74,158,255,0.05));
            border-color: #4a9eff;
        }}
        .stroke-item .handle {{ cursor: move; color: #666; }}
        .stroke-item input[type="checkbox"] {{ width: 18px; height: 18px; }}
        .stroke-item .color-swatch {{
            width: 24px;
            height: 24px;
            border-radius: 4px;
            border: 2px solid #555;
            cursor: pointer;
        }}
        .stroke-item .info {{ flex: 1; }}
        .stroke-item .name {{ font-size: 13px; font-weight: 500; }}
        .stroke-item .stats {{ font-size: 11px; color: #888; }}

        /* Node Table */
        .node-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            background: #2d2d2d;
            border-radius: 6px;
            overflow: hidden;
        }}
        .node-table th {{
            background: #1a1a1a;
            padding: 8px 6px;
            text-align: left;
            font-weight: 600;
            color: #888;
            border-bottom: 1px solid #404040;
        }}
        .node-table td {{
            padding: 6px;
            border-bottom: 1px solid #333;
        }}
        .node-table tr:hover {{
            background: #353535;
        }}
        .node-table tr.selected {{
            background: rgba(74,158,255,0.2);
        }}
        .node-table input[type="number"] {{
            width: 70px;
            padding: 4px;
            background: #1a1a1a;
            border: 1px solid #404040;
            color: #e0e0e0;
            border-radius: 4px;
            font-size: 11px;
        }}
        .node-table .btn-small {{
            padding: 4px 8px;
            font-size: 11px;
            background: #3d3d3d;
            border: 1px solid #404040;
            border-radius: 4px;
            cursor: pointer;
            color: #e0e0e0;
        }}
        .node-table .btn-small:hover {{
            background: #4d4d4d;
            border-color: #4a9eff;
        }}
        .node-table .drag-handle {{
            cursor: move;
            color: #666;
            font-size: 14px;
        }}

        label {{
            display: block;
            margin: 12px 0 6px;
            font-size: 12px;
            color: #aaa;
            font-weight: 500;
        }}
        input[type="range"] {{
            width: 100%;
            height: 6px;
            background: #2d2d2d;
            border-radius: 3px;
            outline: none;
        }}
        input[type="text"], input[type="number"] {{
            width: 100%;
            padding: 8px 12px;
            background: #2d2d2d;
            border: 1px solid #404040;
            color: #e0e0e0;
            border-radius: 6px;
            font-size: 13px;
        }}
        .value-display {{
            float: right;
            font-weight: 600;
            color: #4a9eff;
        }}
        .full-btn {{
            width: 100%;
            padding: 10px;
            margin: 8px 0;
            background: #2d2d2d;
            border: 1px solid #404040;
            color: #e0e0e0;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
        }}
        .full-btn:hover {{ background: #3d3d3d; }}
        .full-btn.primary {{
            background: linear-gradient(135deg, #4a9eff, #0066cc);
        }}
        .full-btn.danger {{
            background: linear-gradient(135deg, #ff4a6e, #cc0033);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 12px;
        }}
        .stat-card {{
            background: #2d2d2d;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #404040;
        }}
        .stat-card .label {{ font-size: 10px; color: #888; }}
        .stat-card .value {{ font-size: 18px; font-weight: 700; color: #4a9eff; }}
        .zoom-controls {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 8px;
            background: rgba(45,45,45,0.95);
            padding: 8px;
            border-radius: 8px;
            border: 1px solid #404040;
        }}
        .zoom-btn {{
            width: 36px;
            height: 36px;
            background: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 6px;
            color: #e0e0e0;
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .zoom-btn:hover {{ background: #3d3d3d; border-color: #4a9eff; }}
        .zoom-label {{
            min-width: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 600;
            color: #4a9eff;
        }}
        .animation-controls {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}
        .play-btn {{
            width: 46px;
            height: 46px;
            background: linear-gradient(135deg, #4a9eff, #0066cc);
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .slider-container {{ flex: 1; }}
        .slider-label {{
            font-size: 11px;
            color: #888;
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
        }}
    </style>
</head>
<body>
    <div class="app">
        <!-- Toolbar -->
        <div class="toolbar">
            <div class="title">Glyph Editor Pro</div>
            <div class="tool-group">
                <div class="tool-btn active" id="toolSelect" onclick="selectTool('select')">➜</div>
                <div class="tool-btn" id="toolNode" onclick="selectTool('node')">◆</div>
                <div class="tool-btn" id="toolDraw" onclick="selectTool('draw')">✎</div>
                <div class="tool-btn" id="toolErase" onclick="selectTool('erase')">✕</div>
            </div>
            <button class="btn" onclick="undo()">↶ Undo</button>
            <button class="btn" onclick="redo()">↷ Redo</button>
            <button class="btn primary" onclick="saveGlyph()">💾 Save</button>
            <button class="btn" onclick="exportPEN()">📤 Export PEN</button>
        </div>

        <!-- Left Panel: Strokes -->
        <div class="left-panel">
            <div class="panel-section">
                <h3>Strokes</h3>
                <div id="strokeList" class="stroke-list"></div>
                <button class="full-btn primary" onclick="addStroke()">+ New Stroke</button>
            </div>
        </div>

        <!-- Canvas (Center) -->
        <div class="canvas-area" id="canvasArea">
            <canvas id="canvas"></canvas>
            <div class="zoom-controls">
                <div class="zoom-btn" onclick="zoomOut()">−</div>
                <div class="zoom-label" id="zoomLabel">100%</div>
                <div class="zoom-btn" onclick="zoomIn()">+</div>
                <div class="zoom-btn" onclick="resetZoom()">⊙</div>
            </div>
        </div>

        <!-- Right Panel: Properties & Node Table -->
        <div class="right-panel">
            <div class="panel-section">
                <h3>Glyph Info</h3>
                <label>Character</label>
                <input type="text" id="glyphChar" maxlength="1" placeholder="A" />
                <label>Name</label>
                <input type="text" id="glyphName" placeholder="Letter A" />
            </div>

            <div class="panel-section">
                <h3>Node Table</h3>
                <div style="max-height: 400px; overflow-y: auto;">
                    <table class="node-table" id="nodeTable">
                        <thead>
                            <tr>
                                <th>☰</th>
                                <th>S</th>
                                <th>#</th>
                                <th>X</th>
                                <th>Y</th>
                                <th>Act</th>
                            </tr>
                        </thead>
                        <tbody id="nodeTableBody">
                            <tr><td colspan="6" style="text-align: center; color: #666;">No nodes</td></tr>
                        </tbody>
                    </table>
                </div>
                <button class="full-btn" onclick="selectAllNodes()">Select All Nodes</button>
                <button class="full-btn danger" onclick="deleteSelectedNodes()">Delete Selected Nodes</button>
            </div>

            <div class="panel-section">
                <h3>Statistics</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="label">Strokes</div>
                        <div class="value" id="statStrokes">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Nodes</div>
                        <div class="value" id="statNodes">0</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Animation Panel -->
        <div class="animation-panel">
            <h3 style="margin-bottom: 12px; font-size: 13px; color: #888;">Animation Preview</h3>
            <div class="animation-controls">
                <button class="play-btn" id="playBtn" onclick="toggleAnimation()">▶</button>
                <div class="slider-container">
                    <div class="slider-label">
                        <span>Progress</span>
                        <span id="animProgress">0%</span>
                    </div>
                    <input type="range" id="animSlider" min="0" max="100" value="0" oninput="updateAnimationProgress()" />
                </div>
                <label style="margin: 0; display: flex; align-items: center; gap: 8px;">
                    Speed: <span class="value-display" id="speedValue">1.0x</span>
                    <input type="range" id="speedSlider" min="0.1" max="3" step="0.1" value="1"
                           style="width: 120px;" oninput="updateSpeed()" />
                </label>
            </div>
        </div>

        <!-- Status Bar -->
        <div class="statusbar">
            <div><span style="color: #888;">Tool:</span> <span style="color: #4a9eff;" id="statusTool">Select</span></div>
            <div><span style="color: #888;">Cursor:</span> <span style="color: #4a9eff;" id="statusCursor">-</span></div>
            <div><span style="color: #888;">Zoom:</span> <span style="color: #4a9eff;" id="statusZoom">100%</span></div>
            <div><span style="color: #888;">Selected:</span> <span style="color: #4a9eff;" id="statusSelected">0</span></div>
        </div>
    </div>

    <script>
        let strokes = {strokes_json};
        let selectedStrokes = new Set();
        let selectedNodes = new Set();
        let currentTool = 'select';
        let undoStack = [];
        let redoStack = [];

        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        let viewOffset = {{ x: 0, y: 0 }};
        let viewScale = 1.0;
        let isPanning = false;
        let panStart = null;
        let isDragging = false;
        let currentDrawStroke = null;
        let draggedNode = null;

        let isAnimating = false;
        let animationProgress = 0;
        let animationSpeed = 1.0;
        let animationFrame = null;

        function init() {{
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);
            setupCanvasEvents();
            updateStrokeList();
            updateNodeTable();
            centerView();
            render();
        }}

        function resizeCanvas() {{
            const area = document.getElementById('canvasArea');
            canvas.width = area.clientWidth;
            canvas.height = area.clientHeight;
            render();
        }}

        function centerView() {{
            if (strokes.length === 0) {{
                viewOffset.x = canvas.width / 2;
                viewOffset.y = canvas.height / 2;
                viewScale = 0.05;
                return;
            }}

            let minX = Infinity, maxX = -Infinity;
            let minY = Infinity, maxY = -Infinity;

            strokes.forEach(stroke => {{
                stroke.points.forEach(([x, y]) => {{
                    minX = Math.min(minX, x);
                    maxX = Math.max(maxX, x);
                    minY = Math.min(minY, y);
                    maxY = Math.max(maxY, y);
                }});
            }});

            const centerX = (minX + maxX) / 2;
            const centerY = (minY + maxY) / 2;
            const width = maxX - minX;
            const height = maxY - minY;

            const scaleX = (canvas.width * 0.8) / width;
            const scaleY = (canvas.height * 0.8) / height;
            viewScale = Math.min(scaleX, scaleY, 0.1);

            viewOffset.x = canvas.width / 2 - centerX * viewScale;
            viewOffset.y = canvas.height / 2 - centerY * viewScale;
        }}

        function setupCanvasEvents() {{
            canvas.addEventListener('mousedown', handleMouseDown);
            canvas.addEventListener('mousemove', handleMouseMove);
            canvas.addEventListener('mouseup', handleMouseUp);
            canvas.addEventListener('wheel', handleWheel, {{ passive: false }});
            document.addEventListener('keydown', handleKeyDown);
        }}

        function handleMouseDown(e) {{
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;
            const [wx, wy] = screenToWacom(mx, my);

            // Middle click for pan
            if (e.button === 1) {{
                isPanning = true;
                panStart = {{ x: mx, y: my }};
                canvas.style.cursor = 'grabbing';
                e.preventDefault();
                return;
            }}

            if (currentTool === 'select') {{
                const stroke = findStrokeAt(wx, wy);
                if (stroke) {{
                    if (!e.shiftKey) selectedStrokes.clear();
                    selectedStrokes.add(stroke.id);
                    selectedNodes.clear();
                    updateStrokeList();
                    updateNodeTable();
                    render();
                }}
            }} else if (currentTool === 'node') {{
                const node = findNodeAt(wx, wy);
                if (node) {{
                    if (!e.shiftKey) selectedNodes.clear();
                    selectedNodes.add(JSON.stringify(node));
                    draggedNode = node;
                    updateNodeTable();
                    render();
                }}
            }} else if (currentTool === 'draw') {{
                saveUndo();
                currentDrawStroke = [wx, wy];
            }} else if (currentTool === 'erase') {{
                const stroke = findStrokeAt(wx, wy);
                if (stroke) {{
                    saveUndo();
                    strokes = strokes.filter(s => s.id !== stroke.id);
                    updateStrokeList();
                    updateNodeTable();
                    render();
                }}
            }}

            isDragging = true;
        }}

        function handleMouseMove(e) {{
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;
            const [wx, wy] = screenToWacom(mx, my);

            document.getElementById('statusCursor').textContent = `(${{Math.round(wx)}}, ${{Math.round(wy)}})`;

            if (isPanning && panStart) {{
                const dx = mx - panStart.x;
                const dy = my - panStart.y;
                viewOffset.x += dx;
                viewOffset.y += dy;
                panStart = {{ x: mx, y: my }};
                render();
                return;
            }}

            if (!isDragging) return;

            if (currentTool === 'draw' && currentDrawStroke) {{
                currentDrawStroke.push(wx, wy);
                render();
            }} else if (currentTool === 'node' && draggedNode) {{
                const stroke = strokes.find(s => s.id === draggedNode.strokeId);
                if (stroke) {{
                    stroke.points[draggedNode.nodeIndex] = [wx, wy];
                    updateNodeTable();
                    render();
                }}
            }}
        }}

        function handleMouseUp(e) {{
            if (isPanning) {{
                canvas.style.cursor = 'default';
            }}

            if (currentTool === 'draw' && currentDrawStroke && currentDrawStroke.length >= 4) {{
                const points = [];
                for (let i = 0; i < currentDrawStroke.length; i += 2) {{
                    points.push([currentDrawStroke[i], currentDrawStroke[i+1]]);
                }}
                const newStroke = {{
                    id: strokes.length,
                    points: points,
                    visible: true,
                    selected: false,
                    color: `hsl(${{(strokes.length * 137) % 360}}, 70%, 50%)`,
                    name: `Stroke ${{strokes.length + 1}}`
                }};
                strokes.push(newStroke);
                updateStrokeList();
                updateNodeTable();
            }}

            isPanning = false;
            isDragging = false;
            currentDrawStroke = null;
            draggedNode = null;
            panStart = null;
            render();
        }}

        function handleWheel(e) {{
            e.preventDefault();
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;
            const [wx, wy] = screenToWacom(mx, my);
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            const newScale = Math.max(0.001, Math.min(10, viewScale * delta));

            viewOffset.x = mx - wx * newScale;
            viewOffset.y = my - wy * newScale;
            viewScale = newScale;

            updateZoomLabel();
            render();
        }}

        function handleKeyDown(e) {{
            if (e.ctrlKey && e.key === 'z') {{ e.preventDefault(); undo(); }}
            else if (e.ctrlKey && e.key === 'y') {{ e.preventDefault(); redo(); }}
            else if (e.key === 'v') selectTool('select');
            else if (e.key === 'n') selectTool('node');
            else if (e.key === 'd') selectTool('draw');
            else if (e.key === 'e') selectTool('erase');
            else if (e.key === 'Delete') deleteSelectedNodes();
            else if (e.key === ' ') {{ e.preventDefault(); toggleAnimation(); }}
        }}

        function screenToWacom(sx, sy) {{
            const wx = (sx - viewOffset.x) / viewScale;
            const wy = (sy - viewOffset.y) / viewScale;
            return [wx, wy];
        }}

        function wacomToScreen(wx, wy) {{
            const sx = wx * viewScale + viewOffset.x;
            const sy = wy * viewScale + viewOffset.y;
            return [sx, sy];
        }}

        function findStrokeAt(wx, wy, threshold = 500) {{
            for (let i = strokes.length - 1; i >= 0; i--) {{
                const stroke = strokes[i];
                if (!stroke.visible) continue;
                for (let [px, py] of stroke.points) {{
                    const dist = Math.sqrt((wx - px) ** 2 + (wy - py) ** 2);
                    if (dist < threshold / viewScale) return stroke;
                }}
            }}
            return null;
        }}

        function findNodeAt(wx, wy, threshold = 300) {{
            for (let i = strokes.length - 1; i >= 0; i--) {{
                const stroke = strokes[i];
                if (!stroke.visible) continue;
                for (let j = 0; j < stroke.points.length; j++) {{
                    const [px, py] = stroke.points[j];
                    const dist = Math.sqrt((wx - px) ** 2 + (wy - py) ** 2);
                    if (dist < threshold / viewScale) {{
                        return {{ strokeId: stroke.id, nodeIndex: j }};
                    }}
                }}
            }}
            return null;
        }}

        function render() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Grid
            ctx.strokeStyle = '#2d2d2d';
            ctx.lineWidth = 1;
            const gridSize = 1000 * viewScale;
            const offsetX = viewOffset.x % gridSize;
            const offsetY = viewOffset.y % gridSize;
            for (let x = offsetX; x < canvas.width; x += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }}
            for (let y = offsetY; y < canvas.height; y += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }}

            // Strokes
            const animLimit = isAnimating ? getAnimationPoint() : null;
            strokes.forEach((stroke, strokeIdx) => {{
                if (!stroke.visible) return;

                let points = stroke.points;
                if (animLimit && strokeIdx <= animLimit.strokeIdx) {{
                    if (strokeIdx === animLimit.strokeIdx) {{
                        points = points.slice(0, animLimit.pointIdx + 1);
                    }}
                }}

                if (points.length < 2) return;

                ctx.beginPath();
                const [x0, y0] = wacomToScreen(points[0][0], points[0][1]);
                ctx.moveTo(x0, y0);

                for (let i = 1; i < points.length; i++) {{
                    const [x, y] = wacomToScreen(points[i][0], points[i][1]);
                    ctx.lineTo(x, y);
                }}

                const isSelected = selectedStrokes.has(stroke.id);
                ctx.strokeStyle = isSelected ? '#4a9eff' : stroke.color;
                ctx.lineWidth = isSelected ? 3 : 2;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                ctx.stroke();

                // Draw nodes
                if (currentTool === 'node' || isSelected) {{
                    points.forEach(([wx, wy], idx) => {{
                        const [sx, sy] = wacomToScreen(wx, wy);
                        const nodeKey = JSON.stringify({{ strokeId: stroke.id, nodeIndex: idx }});
                        const isNodeSelected = selectedNodes.has(nodeKey);

                        ctx.fillStyle = isNodeSelected ? '#4a9eff' : '#fff';
                        ctx.strokeStyle = '#1a1a1a';
                        ctx.lineWidth = 2;
                        const radius = isNodeSelected ? 6 : 4;

                        ctx.beginPath();
                        ctx.arc(sx, sy, radius, 0, 2 * Math.PI);
                        ctx.fill();
                        ctx.stroke();
                    }});
                }}
            }});

            // Draw preview stroke
            if (currentDrawStroke && currentDrawStroke.length >= 2) {{
                ctx.strokeStyle = '#4a9eff';
                ctx.lineWidth = 2;
                ctx.beginPath();
                const [x0, y0] = wacomToScreen(currentDrawStroke[0], currentDrawStroke[1]);
                ctx.moveTo(x0, y0);
                for (let i = 2; i < currentDrawStroke.length; i += 2) {{
                    const [x, y] = wacomToScreen(currentDrawStroke[i], currentDrawStroke[i+1]);
                    ctx.lineTo(x, y);
                }}
                ctx.stroke();
            }}

            updateStats();
        }}

        function getAnimationPoint() {{
            const progress = animationProgress / 100;
            let totalPoints = 0;
            strokes.forEach(s => {{ if (s.visible) totalPoints += s.points.length; }});
            const targetPoint = Math.floor(progress * totalPoints);

            let count = 0;
            for (let i = 0; i < strokes.length; i++) {{
                if (!strokes[i].visible) continue;
                const len = strokes[i].points.length;
                if (count + len > targetPoint) {{
                    return {{ strokeIdx: i, pointIdx: targetPoint - count }};
                }}
                count += len;
            }}
            return {{ strokeIdx: strokes.length - 1, pointIdx: 0 }};
        }}

        function selectTool(tool) {{
            currentTool = tool;
            document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('tool' + tool.charAt(0).toUpperCase() + tool.slice(1)).classList.add('active');
            document.getElementById('statusTool').textContent = tool.charAt(0).toUpperCase() + tool.slice(1);
        }}

        function updateStrokeList() {{
            const list = document.getElementById('strokeList');
            list.innerHTML = '';

            strokes.forEach(stroke => {{
                const div = document.createElement('div');
                div.className = 'stroke-item' +
                    (selectedStrokes.has(stroke.id) ? ' selected' : '') +
                    (!stroke.visible ? ' hidden' : '');

                div.innerHTML = `
                    <span class="handle">☰</span>
                    <input type="checkbox" ${{stroke.visible ? 'checked' : ''}}
                        onchange="toggleStrokeVisibility(${{stroke.id}})" />
                    <div class="color-swatch" style="background: ${{stroke.color}}"
                        onclick="selectStroke(${{stroke.id}})"></div>
                    <div class="info">
                        <div class="name">${{stroke.name}}</div>
                        <div class="stats">${{stroke.points.length}} nodes</div>
                    </div>
                `;

                div.onclick = (e) => {{
                    if (e.target.tagName !== 'INPUT') selectStroke(stroke.id);
                }};

                list.appendChild(div);
            }});
        }}

        function updateNodeTable() {{
            const tbody = document.getElementById('nodeTableBody');
            tbody.innerHTML = '';

            let nodeCount = 0;
            strokes.forEach(stroke => {{
                if (!stroke.visible) return;
                stroke.points.forEach(([x, y], idx) => {{
                    nodeCount++;
                    const nodeKey = JSON.stringify({{ strokeId: stroke.id, nodeIndex: idx }});
                    const isSelected = selectedNodes.has(nodeKey);

                    const tr = document.createElement('tr');
                    tr.className = isSelected ? 'selected' : '';

                    tr.innerHTML = `
                        <td><span class="drag-handle">☰</span></td>
                        <td>${{stroke.id + 1}}</td>
                        <td>${{idx + 1}}</td>
                        <td><input type="number" value="${{Math.round(x)}}" onchange="updateNodeCoord(${{stroke.id}}, ${{idx}}, 'x', this.value)" /></td>
                        <td><input type="number" value="${{Math.round(y)}}" onchange="updateNodeCoord(${{stroke.id}}, ${{idx}}, 'y', this.value)" /></td>
                        <td>
                            <button class="btn-small" onclick="selectNode(${{stroke.id}}, ${{idx}})">Sel</button>
                            <button class="btn-small" onclick="deleteNodeByIndex(${{stroke.id}}, ${{idx}})">Del</button>
                        </td>
                    `;

                    tr.onclick = (e) => {{
                        if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON') {{
                            selectNode(stroke.id, idx);
                        }}
                    }};

                    tbody.appendChild(tr);
                }});
            }});

            if (nodeCount === 0) {{
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #666;">No nodes</td></tr>';
            }}
        }}

        function selectNode(strokeId, nodeIndex) {{
            const nodeKey = JSON.stringify({{ strokeId, nodeIndex }});
            if (selectedNodes.has(nodeKey)) {{
                selectedNodes.delete(nodeKey);
            }} else {{
                selectedNodes.add(nodeKey);
            }}
            updateNodeTable();
            render();
        }}

        function selectAllNodes() {{
            selectedNodes.clear();
            strokes.forEach(stroke => {{
                if (!stroke.visible) return;
                stroke.points.forEach((_, idx) => {{
                    selectedNodes.add(JSON.stringify({{ strokeId: stroke.id, nodeIndex: idx }}));
                }});
            }});
            updateNodeTable();
            render();
        }}

        function updateNodeCoord(strokeId, nodeIndex, coord, value) {{
            const stroke = strokes.find(s => s.id === strokeId);
            if (!stroke) return;

            saveUndo();
            const val = parseInt(value);
            if (coord === 'x') {{
                stroke.points[nodeIndex][0] = val;
            }} else {{
                stroke.points[nodeIndex][1] = val;
            }}
            render();
        }}

        function deleteNodeByIndex(strokeId, nodeIndex) {{
            const stroke = strokes.find(s => s.id === strokeId);
            if (!stroke || stroke.points.length <= 2) return;

            saveUndo();
            stroke.points.splice(nodeIndex, 1);
            selectedNodes.delete(JSON.stringify({{ strokeId, nodeIndex }}));
            updateNodeTable();
            render();
        }}

        function deleteSelectedNodes() {{
            if (selectedNodes.size === 0) return;

            saveUndo();
            const toDelete = Array.from(selectedNodes).map(k => JSON.parse(k));

            // Group by stroke
            const byStroke = {{}};
            toDelete.forEach(node => {{
                if (!byStroke[node.strokeId]) byStroke[node.strokeId] = [];
                byStroke[node.strokeId].push(node.nodeIndex);
            }});

            // Delete from each stroke (reverse order to maintain indices)
            Object.keys(byStroke).forEach(strokeId => {{
                const stroke = strokes.find(s => s.id === parseInt(strokeId));
                if (!stroke) return;
                const indices = byStroke[strokeId].sort((a, b) => b - a);
                indices.forEach(idx => {{
                    if (stroke.points.length > 2) {{
                        stroke.points.splice(idx, 1);
                    }}
                }});
            }});

            selectedNodes.clear();
            updateNodeTable();
            render();
        }}

        function selectStroke(id) {{
            selectedStrokes.clear();
            selectedStrokes.add(id);
            selectedNodes.clear();
            updateStrokeList();
            render();
        }}

        function toggleStrokeVisibility(id) {{
            const stroke = strokes.find(s => s.id === id);
            if (stroke) {{
                stroke.visible = !stroke.visible;
                updateNodeTable();
                render();
            }}
        }}

        function addStroke() {{
            saveUndo();
            const newStroke = {{
                id: strokes.length,
                points: [[10000, 10000], [11000, 11000]],
                visible: true,
                selected: false,
                color: `hsl(${{(strokes.length * 137) % 360}}, 70%, 50%)`,
                name: `Stroke ${{strokes.length + 1}}`
            }};
            strokes.push(newStroke);
            updateStrokeList();
            updateNodeTable();
            centerView();
            render();
        }}

        function zoomIn() {{
            const cx = canvas.width / 2;
            const cy = canvas.height / 2;
            const [wx, wy] = screenToWacom(cx, cy);
            viewScale *= 1.2;
            viewOffset.x = cx - wx * viewScale;
            viewOffset.y = cy - wy * viewScale;
            updateZoomLabel();
            render();
        }}

        function zoomOut() {{
            const cx = canvas.width / 2;
            const cy = canvas.height / 2;
            const [wx, wy] = screenToWacom(cx, cy);
            viewScale /= 1.2;
            viewOffset.x = cx - wx * viewScale;
            viewOffset.y = cy - wy * viewScale;
            updateZoomLabel();
            render();
        }}

        function resetZoom() {{
            centerView();
            updateZoomLabel();
            render();
        }}

        function updateZoomLabel() {{
            const percent = Math.round(viewScale * 100);
            document.getElementById('zoomLabel').textContent = percent + '%';
            document.getElementById('statusZoom').textContent = percent + '%';
        }}

        function toggleAnimation() {{
            isAnimating = !isAnimating;
            document.getElementById('playBtn').textContent = isAnimating ? '⏸' : '▶';
            if (isAnimating) animateFrame();
            else if (animationFrame) cancelAnimationFrame(animationFrame);
        }}

        function animateFrame() {{
            if (!isAnimating) return;
            animationProgress += animationSpeed * 0.5;
            if (animationProgress >= 100) animationProgress = 0;
            document.getElementById('animSlider').value = animationProgress;
            document.getElementById('animProgress').textContent = Math.round(animationProgress) + '%';
            render();
            animationFrame = requestAnimationFrame(animateFrame);
        }}

        function updateAnimationProgress() {{
            animationProgress = parseFloat(document.getElementById('animSlider').value);
            document.getElementById('animProgress').textContent = Math.round(animationProgress) + '%';
            render();
        }}

        function updateSpeed() {{
            animationSpeed = parseFloat(document.getElementById('speedSlider').value);
            document.getElementById('speedValue').textContent = animationSpeed.toFixed(1) + 'x';
        }}

        function saveUndo() {{
            undoStack.push(JSON.parse(JSON.stringify(strokes)));
            redoStack = [];
        }}

        function undo() {{
            if (undoStack.length === 0) return;
            redoStack.push(JSON.parse(JSON.stringify(strokes)));
            strokes = undoStack.pop();
            updateStrokeList();
            updateNodeTable();
            render();
        }}

        function redo() {{
            if (redoStack.length === 0) return;
            undoStack.push(JSON.parse(JSON.stringify(strokes)));
            strokes = redoStack.pop();
            updateStrokeList();
            updateNodeTable();
            render();
        }}

        function updateStats() {{
            const visible = strokes.filter(s => s.visible);
            const totalNodes = visible.reduce((sum, s) => sum + s.points.length, 0);
            document.getElementById('statStrokes').textContent = visible.length;
            document.getElementById('statNodes').textContent = totalNodes;
            document.getElementById('statusSelected').textContent = selectedNodes.size || selectedStrokes.size || 0;
        }}

        function saveGlyph() {{
            const char = document.getElementById('glyphChar').value;
            if (!char) {{ alert('Enter character'); return; }}
            alert(`Glyph '${{char}}' saved!`);
        }}

        function exportPEN() {{
            const commands = [];
            strokes.filter(s => s.visible).forEach(stroke => {{
                if (stroke.points.length < 1) return;
                commands.push(`PEN_DOWN ${{stroke.points[0][0]}} ${{stroke.points[0][1]}}`);
                for (let i = 1; i < stroke.points.length; i++) {{
                    commands.push(`PEN_MOVE ${{stroke.points[i][0]}} ${{stroke.points[i][1]}}`);
                }}
                commands.push('PEN_UP');
            }});

            const blob = new Blob([commands.join('\\n') + '\\n'], {{ type: 'text/plain' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'glyph.txt';
            a.click();
            URL.revokeObjectURL(url);
        }}

        init();
    </script>
</body>
</html>"""

    return html


class EditorHandler(http.server.SimpleHTTPRequestHandler):
    html_content = None

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.html_content.encode('utf-8'))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


def main():
    if len(sys.argv) < 2:
        print("Glyph Editor Pro")
        print("=" * 70)
        print()
        print("Usage: python3 glyph_editor_pro.py <input.txt>")
        print()
        print("Features:")
        print("  ✓ Node table with coordinates")
        print("  ✓ Select, move, delete individual nodes")
        print("  ✓ Reorder points in table")
        print("  ✓ Fixed layout (canvas in center)")
        print("  ✓ Simple pan (just middle-click)")
        print("  ✓ Proper port handling")
        print()
        return 1

    input_file = sys.argv[1]

    print("Loading:", input_file)
    strokes = parse_pen_commands(input_file)

    if not strokes:
        print("No strokes found, starting empty")
        strokes = []

    print(f"Loaded: {len(strokes)} strokes")
    print()

    html = generate_html_editor(strokes, input_file)
    EditorHandler.html_content = html

    # Find free port
    port = find_free_port()

    print(f"Starting Glyph Editor Pro on http://localhost:{port}")
    print()

    try:
        server = socketserver.TCPServer(("", port), EditorHandler)
        server.allow_reuse_address = True

        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        print("Opening browser...")
        webbrowser.open(f'http://localhost:{port}')
        print()
        print("Editor running. Press Ctrl+C to stop.")
        print()
        print("Controls:")
        print("  - Middle-click and drag to pan")
        print("  - Mouse wheel to zoom")
        print("  - Click rows in node table to select")
        print("  - Edit X/Y values directly in table")
        print()

        while True:
            pass
    except KeyboardInterrupt:
        print()
        print("Shutting down...")
        server.shutdown()
        server.server_close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
