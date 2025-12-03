#!/usr/bin/env python3
"""
Glyph Editor - Interactive stroke editor for creating font glyphs
Inkscape-like interface with real-time editing, stroke ordering, and font management
"""

import sys
import json
import math
import http.server
import socketserver
import webbrowser
import threading
from urllib.parse import parse_qs, urlparse


# Configuration
WACOM_MAX_X = 20966
WACOM_MAX_Y = 15725
RM2_WIDTH = 1404
RM2_HEIGHT = 1872


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
    """Generate advanced HTML editor with Inkscape-like features"""

    strokes_json = json.dumps([
        {
            "id": i,
            "points": stroke,
            "visible": True,
            "selected": False,
            "color": "#000000",
            "name": f"Stroke {i+1}"
        }
        for i, stroke in enumerate(strokes)
    ])

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Glyph Editor - {input_file}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #1e1e1e;
            color: #fff;
            overflow: hidden;
        }}
        .editor {{
            display: grid;
            grid-template-columns: 250px 1fr 300px;
            grid-template-rows: 50px 1fr 40px;
            height: 100vh;
            gap: 1px;
            background: #000;
        }}
        .toolbar {{
            grid-column: 1 / -1;
            background: #2d2d2d;
            display: flex;
            align-items: center;
            padding: 0 15px;
            gap: 10px;
            border-bottom: 1px solid #000;
        }}
        .toolbar button {{
            background: #3e3e3e;
            border: 1px solid #555;
            color: #fff;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
        }}
        .toolbar button:hover {{
            background: #4e4e4e;
        }}
        .toolbar button.active {{
            background: #0d6efd;
            border-color: #0d6efd;
        }}
        .toolbar .separator {{
            width: 1px;
            height: 30px;
            background: #555;
        }}
        .toolbar .title {{
            font-weight: 600;
            margin-right: auto;
        }}
        .left-panel {{
            background: #252525;
            padding: 15px;
            overflow-y: auto;
        }}
        .right-panel {{
            background: #252525;
            padding: 15px;
            overflow-y: auto;
        }}
        .canvas-area {{
            background: #1e1e1e;
            position: relative;
            overflow: hidden;
        }}
        canvas {{
            position: absolute;
            cursor: crosshair;
        }}
        .panel-section {{
            margin-bottom: 20px;
        }}
        .panel-section h3 {{
            font-size: 13px;
            color: #999;
            text-transform: uppercase;
            margin-bottom: 10px;
            border-bottom: 1px solid #3e3e3e;
            padding-bottom: 5px;
        }}
        .stroke-list {{
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}
        .stroke-item {{
            background: #2d2d2d;
            border: 1px solid #3e3e3e;
            border-radius: 4px;
            padding: 8px;
            cursor: move;
            user-select: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .stroke-item:hover {{
            background: #3e3e3e;
        }}
        .stroke-item.selected {{
            background: #0d6efd;
            border-color: #0d6efd;
        }}
        .stroke-item.hidden {{
            opacity: 0.3;
        }}
        .stroke-item input[type="checkbox"] {{
            margin: 0;
        }}
        .stroke-item .color-swatch {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
            border: 1px solid #555;
            cursor: pointer;
        }}
        .stroke-item .name {{
            flex: 1;
            font-size: 13px;
        }}
        .stroke-item .points {{
            font-size: 11px;
            color: #999;
        }}
        .stroke-item .handle {{
            cursor: move;
            color: #999;
        }}
        label {{
            display: block;
            margin: 10px 0 5px;
            font-size: 13px;
            color: #ccc;
        }}
        input[type="range"] {{
            width: 100%;
            margin: 5px 0;
        }}
        input[type="text"] {{
            width: 100%;
            padding: 6px;
            background: #2d2d2d;
            border: 1px solid #3e3e3e;
            color: #fff;
            border-radius: 4px;
            font-size: 13px;
        }}
        input[type="color"] {{
            width: 100%;
            height: 30px;
            border: none;
            background: none;
            cursor: pointer;
        }}
        .value-display {{
            float: right;
            font-weight: 600;
            color: #0d6efd;
        }}
        button.full-width {{
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            background: #3e3e3e;
            border: 1px solid #555;
            color: #fff;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
        }}
        button.full-width:hover {{
            background: #4e4e4e;
        }}
        button.primary {{
            background: #0d6efd;
            border-color: #0d6efd;
        }}
        button.primary:hover {{
            background: #0b5ed7;
        }}
        button.danger {{
            background: #dc3545;
            border-color: #dc3545;
        }}
        button.danger:hover {{
            background: #bb2d3b;
        }}
        .stats {{
            background: #2d2d2d;
            padding: 10px;
            border-radius: 4px;
            font-size: 12px;
            margin-top: 10px;
        }}
        .stats div {{
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
        }}
        .stats .label {{
            color: #999;
        }}
        .stats .value {{
            color: #0d6efd;
            font-weight: 600;
        }}
        .statusbar {{
            grid-column: 1 / -1;
            background: #2d2d2d;
            padding: 0 15px;
            display: flex;
            align-items: center;
            gap: 20px;
            font-size: 12px;
            border-top: 1px solid #000;
        }}
        .statusbar .item {{
            display: flex;
            gap: 5px;
        }}
        .statusbar .label {{
            color: #999;
        }}
        .statusbar .value {{
            color: #0d6efd;
        }}
        .glyph-preview {{
            background: #2d2d2d;
            border: 1px solid #3e3e3e;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
        }}
        .glyph-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
            gap: 5px;
            max-height: 200px;
            overflow-y: auto;
        }}
        .glyph-item {{
            background: #1e1e1e;
            border: 1px solid #3e3e3e;
            border-radius: 4px;
            padding: 5px;
            text-align: center;
            cursor: pointer;
            font-size: 11px;
        }}
        .glyph-item:hover {{
            background: #2d2d2d;
            border-color: #0d6efd;
        }}
        .glyph-item.active {{
            background: #0d6efd;
            border-color: #0d6efd;
        }}
        .tool-button {{
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #3e3e3e;
            border: 1px solid #555;
            border-radius: 4px;
            cursor: pointer;
            font-size: 18px;
        }}
        .tool-button:hover {{
            background: #4e4e4e;
        }}
        .tool-button.active {{
            background: #0d6efd;
            border-color: #0d6efd;
        }}
    </style>
</head>
<body>
    <div class="editor">
        <!-- Toolbar -->
        <div class="toolbar">
            <div class="title">Glyph Editor</div>
            <div class="tool-button" id="toolSelect" title="Select (V)" onclick="selectTool('select')">→</div>
            <div class="tool-button" id="toolDraw" title="Draw (D)" onclick="selectTool('draw')">✎</div>
            <div class="tool-button" id="toolErase" title="Erase (E)" onclick="selectTool('erase')">✗</div>
            <div class="tool-button" id="toolNode" title="Edit Nodes (N)" onclick="selectTool('node')">◇</div>
            <div class="separator"></div>
            <button onclick="undoAction()">Undo (Ctrl+Z)</button>
            <button onclick="redoAction()">Redo (Ctrl+Y)</button>
            <div class="separator"></div>
            <button onclick="saveGlyph()">Save Glyph</button>
            <button onclick="exportPenCommands()">Export PEN</button>
            <button onclick="exportFont()">Export Font</button>
        </div>

        <!-- Left Panel: Stroke List -->
        <div class="left-panel">
            <div class="panel-section">
                <h3>Strokes</h3>
                <div id="strokeList" class="stroke-list"></div>
                <button class="full-width" onclick="addNewStroke()">+ New Stroke</button>
            </div>
        </div>

        <!-- Canvas Area -->
        <div class="canvas-area" id="canvasArea">
            <canvas id="canvas"></canvas>
        </div>

        <!-- Right Panel: Properties -->
        <div class="right-panel">
            <div class="panel-section">
                <h3>Current Glyph</h3>
                <label>
                    Character:
                    <input type="text" id="glyphChar" maxlength="1" value="" placeholder="A" />
                </label>
                <label>
                    Name:
                    <input type="text" id="glyphName" value="" placeholder="Letter A" />
                </label>
            </div>

            <div class="panel-section">
                <h3>Stroke Properties</h3>
                <div id="strokeProps">
                    <label>
                        Interpolation: <span class="value-display" id="interpValue">1x</span>
                        <input type="range" id="interpSlider" min="1" max="30" value="1" />
                    </label>
                    <label>
                        Smoothing: <span class="value-display" id="smoothValue">0</span>
                        <input type="range" id="smoothSlider" min="0" max="10" value="0" />
                    </label>
                    <label>
                        Color:
                        <input type="color" id="strokeColor" value="#000000" />
                    </label>
                    <button class="full-width danger" onclick="deleteSelectedStroke()">Delete Stroke</button>
                </div>
            </div>

            <div class="panel-section">
                <h3>Font Library</h3>
                <div class="glyph-grid" id="glyphGrid">
                    <!-- Populated by JS -->
                </div>
                <button class="full-width" onclick="newGlyph()">+ New Glyph</button>
                <button class="full-width" onclick="loadFont()">Load Font</button>
            </div>

            <div class="stats">
                <div><span class="label">Strokes:</span> <span class="value" id="statStrokes">0</span></div>
                <div><span class="label">Points:</span> <span class="value" id="statPoints">0</span></div>
                <div><span class="label">Selected:</span> <span class="value" id="statSelected">-</span></div>
            </div>
        </div>

        <!-- Status Bar -->
        <div class="statusbar">
            <div class="item">
                <span class="label">Tool:</span>
                <span class="value" id="statusTool">Select</span>
            </div>
            <div class="item">
                <span class="label">Cursor:</span>
                <span class="value" id="statusCursor">-</span>
            </div>
            <div class="item">
                <span class="label">Zoom:</span>
                <span class="value" id="statusZoom">100%</span>
            </div>
        </div>
    </div>

    <script>
        // Global state
        let strokes = {strokes_json};
        let selectedStrokeIds = new Set();
        let currentTool = 'select';
        let currentGlyph = '';
        let fontLibrary = {{}};
        let undoStack = [];
        let redoStack = [];
        let draggedStroke = null;

        // Canvas state
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        let canvasOffset = {{ x: 0, y: 0 }};
        let canvasScale = 1.0;
        let isDragging = false;
        let dragStart = null;
        let currentDrawStroke = null;
        let selectedNodes = new Set();

        // Initialize
        function init() {{
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);
            setupCanvasEvents();
            updateStrokeList();
            updateGlyphGrid();
            render();
            selectTool('select');
        }}

        function resizeCanvas() {{
            const area = document.getElementById('canvasArea');
            canvas.width = area.clientWidth;
            canvas.height = area.clientHeight;
            render();
        }}

        function setupCanvasEvents() {{
            canvas.addEventListener('mousedown', handleMouseDown);
            canvas.addEventListener('mousemove', handleMouseMove);
            canvas.addEventListener('mouseup', handleMouseUp);
            canvas.addEventListener('wheel', handleWheel);

            // Keyboard shortcuts
            document.addEventListener('keydown', handleKeyDown);
        }}

        function handleMouseDown(e) {{
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;
            const wx = screenToWacom(mx, my).x;
            const wy = screenToWacom(mx, my).y;

            if (currentTool === 'select') {{
                // Check if clicking on stroke
                const clickedStroke = findStrokeAt(wx, wy);
                if (clickedStroke !== null) {{
                    if (!e.shiftKey) {{
                        selectedStrokeIds.clear();
                    }}
                    selectedStrokeIds.add(clickedStroke.id);
                    updateStrokeList();
                    updateStrokeProperties();
                    render();
                }}
            }} else if (currentTool === 'draw') {{
                // Start new stroke
                currentDrawStroke = [wx, wy];
            }} else if (currentTool === 'erase') {{
                // Delete stroke at cursor
                const clickedStroke = findStrokeAt(wx, wy);
                if (clickedStroke !== null) {{
                    saveUndo();
                    strokes = strokes.filter(s => s.id !== clickedStroke.id);
                    updateStrokeList();
                    render();
                }}
            }} else if (currentTool === 'node') {{
                // Select node
                const node = findNodeAt(wx, wy);
                if (node) {{
                    if (!e.shiftKey) selectedNodes.clear();
                    selectedNodes.add(node);
                    render();
                }}
            }}

            isDragging = true;
            dragStart = {{ x: mx, y: my }};
        }}

        function handleMouseMove(e) {{
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;
            const wx = screenToWacom(mx, my).x;
            const wy = screenToWacom(mx, my).y;

            document.getElementById('statusCursor').textContent = `(${{wx}}, ${{wy}})`;

            if (!isDragging) return;

            if (currentTool === 'draw' && currentDrawStroke) {{
                currentDrawStroke.push(wx, wy);
                render();
                // Show preview
                ctx.strokeStyle = '#0d6efd';
                ctx.lineWidth = 2;
                ctx.beginPath();
                for (let i = 0; i < currentDrawStroke.length; i += 2) {{
                    const p = wacomToScreen(currentDrawStroke[i], currentDrawStroke[i+1]);
                    if (i === 0) ctx.moveTo(p.x, p.y);
                    else ctx.lineTo(p.x, p.y);
                }}
                ctx.stroke();
            }}
        }}

        function handleMouseUp(e) {{
            if (currentTool === 'draw' && currentDrawStroke && currentDrawStroke.length >= 4) {{
                // Convert to points array
                const points = [];
                for (let i = 0; i < currentDrawStroke.length; i += 2) {{
                    points.push([currentDrawStroke[i], currentDrawStroke[i+1]]);
                }}

                // Add new stroke
                saveUndo();
                const newStroke = {{
                    id: strokes.length,
                    points: points,
                    visible: true,
                    selected: false,
                    color: '#000000',
                    name: `Stroke ${{strokes.length + 1}}`
                }};
                strokes.push(newStroke);
                updateStrokeList();
            }}

            isDragging = false;
            currentDrawStroke = null;
            render();
        }}

        function handleWheel(e) {{
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            canvasScale *= delta;
            canvasScale = Math.max(0.1, Math.min(10, canvasScale));
            document.getElementById('statusZoom').textContent = Math.round(canvasScale * 100) + '%';
            render();
        }}

        function handleKeyDown(e) {{
            if (e.ctrlKey && e.key === 'z') {{
                e.preventDefault();
                undoAction();
            }} else if (e.ctrlKey && e.key === 'y') {{
                e.preventDefault();
                redoAction();
            }} else if (e.key === 'v') {{
                selectTool('select');
            }} else if (e.key === 'd') {{
                selectTool('draw');
            }} else if (e.key === 'e') {{
                selectTool('erase');
            }} else if (e.key === 'n') {{
                selectTool('node');
            }} else if (e.key === 'Delete') {{
                deleteSelectedStroke();
            }}
        }}

        function screenToWacom(sx, sy) {{
            const wx = Math.round((sx - canvasOffset.x) / canvasScale);
            const wy = Math.round((sy - canvasOffset.y) / canvasScale);
            return {{ x: wx, y: wy }};
        }}

        function wacomToScreen(wx, wy) {{
            const sx = wx * canvasScale + canvasOffset.x;
            const sy = wy * canvasScale + canvasOffset.y;
            return {{ x: sx, y: sy }};
        }}

        function findStrokeAt(wx, wy, threshold = 100) {{
            for (let stroke of strokes) {{
                if (!stroke.visible) continue;
                for (let [px, py] of stroke.points) {{
                    const dist = Math.sqrt((wx - px) ** 2 + (wy - py) ** 2);
                    if (dist < threshold) return stroke;
                }}
            }}
            return null;
        }}

        function findNodeAt(wx, wy, threshold = 50) {{
            for (let stroke of strokes) {{
                if (!stroke.visible) continue;
                for (let i = 0; i < stroke.points.length; i++) {{
                    const [px, py] = stroke.points[i];
                    const dist = Math.sqrt((wx - px) ** 2 + (wy - py) ** 2);
                    if (dist < threshold) return {{ stroke: stroke.id, index: i }};
                }}
            }}
            return null;
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
                    result.push([
                        Math.round(x1 + t * (x2 - x1)),
                        Math.round(y1 + t * (y2 - y1))
                    ]);
                }}
            }}
            result.push(points[points.length - 1]);
            return result;
        }}

        function render() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw grid
            ctx.strokeStyle = '#2d2d2d';
            ctx.lineWidth = 1;
            const gridSize = 100 * canvasScale;
            for (let x = canvasOffset.x % gridSize; x < canvas.width; x += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }}
            for (let y = canvasOffset.y % gridSize; y < canvas.height; y += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }}

            // Draw strokes
            strokes.forEach(stroke => {{
                if (!stroke.visible) return;

                const points = stroke.points;
                if (points.length < 2) return;

                ctx.beginPath();
                const p0 = wacomToScreen(points[0][0], points[0][1]);
                ctx.moveTo(p0.x, p0.y);

                for (let i = 1; i < points.length; i++) {{
                    const p = wacomToScreen(points[i][0], points[i][1]);
                    ctx.lineTo(p.x, p.y);
                }}

                ctx.strokeStyle = selectedStrokeIds.has(stroke.id) ? '#0d6efd' : (stroke.color || '#000000');
                ctx.lineWidth = selectedStrokeIds.has(stroke.id) ? 3 : 2;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                ctx.stroke();

                // Draw nodes if selected
                if (selectedStrokeIds.has(stroke.id) || currentTool === 'node') {{
                    points.forEach(([wx, wy], idx) => {{
                        const p = wacomToScreen(wx, wy);
                        ctx.fillStyle = '#0d6efd';
                        ctx.beginPath();
                        ctx.arc(p.x, p.y, 3, 0, 2 * Math.PI);
                        ctx.fill();
                    }});
                }}
            }});

            updateStats();
        }}

        function updateStrokeList() {{
            const list = document.getElementById('strokeList');
            list.innerHTML = '';

            strokes.forEach(stroke => {{
                const div = document.createElement('div');
                div.className = 'stroke-item' +
                    (selectedStrokeIds.has(stroke.id) ? ' selected' : '') +
                    (!stroke.visible ? ' hidden' : '');
                div.draggable = true;

                div.innerHTML = `
                    <span class="handle">☰</span>
                    <input type="checkbox" ${{stroke.visible ? 'checked' : ''}}
                        onchange="toggleStrokeVisibility(${{stroke.id}})" />
                    <div class="color-swatch" style="background: ${{stroke.color}}"
                        onclick="selectStroke(${{stroke.id}})"></div>
                    <span class="name">${{stroke.name}}</span>
                    <span class="points">${{stroke.points.length}}pts</span>
                `;

                div.onclick = (e) => {{
                    if (e.target.tagName !== 'INPUT') selectStroke(stroke.id);
                }};

                div.ondragstart = (e) => {{
                    draggedStroke = stroke.id;
                    e.dataTransfer.effectAllowed = 'move';
                }};

                div.ondragover = (e) => {{
                    e.preventDefault();
                    e.dataTransfer.dropEffect = 'move';
                }};

                div.ondrop = (e) => {{
                    e.preventDefault();
                    if (draggedStroke !== null && draggedStroke !== stroke.id) {{
                        reorderStrokes(draggedStroke, stroke.id);
                    }}
                }};

                list.appendChild(div);
            }});
        }}

        function reorderStrokes(fromId, toId) {{
            saveUndo();
            const fromIdx = strokes.findIndex(s => s.id === fromId);
            const toIdx = strokes.findIndex(s => s.id === toId);
            const [moved] = strokes.splice(fromIdx, 1);
            strokes.splice(toIdx, 0, moved);
            updateStrokeList();
            render();
        }}

        function selectStroke(id) {{
            selectedStrokeIds.clear();
            selectedStrokeIds.add(id);
            updateStrokeList();
            updateStrokeProperties();
            render();
        }}

        function toggleStrokeVisibility(id) {{
            const stroke = strokes.find(s => s.id === id);
            if (stroke) {{
                stroke.visible = !stroke.visible;
                render();
            }}
        }}

        function updateStrokeProperties() {{
            if (selectedStrokeIds.size !== 1) return;

            const id = Array.from(selectedStrokeIds)[0];
            const stroke = strokes.find(s => s.id === id);
            if (!stroke) return;

            document.getElementById('strokeColor').value = stroke.color || '#000000';
        }}

        function selectTool(tool) {{
            currentTool = tool;
            document.querySelectorAll('.tool-button').forEach(btn => btn.classList.remove('active'));
            document.getElementById('tool' + tool.charAt(0).toUpperCase() + tool.slice(1)).classList.add('active');
            document.getElementById('statusTool').textContent = tool.charAt(0).toUpperCase() + tool.slice(1);

            // Update cursor
            if (tool === 'draw') canvas.style.cursor = 'crosshair';
            else if (tool === 'erase') canvas.style.cursor = 'not-allowed';
            else if (tool === 'node') canvas.style.cursor = 'pointer';
            else canvas.style.cursor = 'default';
        }}

        function deleteSelectedStroke() {{
            if (selectedStrokeIds.size === 0) return;
            saveUndo();
            strokes = strokes.filter(s => !selectedStrokeIds.has(s.id));
            selectedStrokeIds.clear();
            updateStrokeList();
            render();
        }}

        function addNewStroke() {{
            saveUndo();
            const newStroke = {{
                id: strokes.length,
                points: [[5000, 5000], [6000, 6000]],
                visible: true,
                selected: false,
                color: '#000000',
                name: `Stroke ${{strokes.length + 1}}`
            }};
            strokes.push(newStroke);
            updateStrokeList();
            render();
        }}

        function saveUndo() {{
            undoStack.push(JSON.parse(JSON.stringify(strokes)));
            redoStack = [];
        }}

        function undoAction() {{
            if (undoStack.length === 0) return;
            redoStack.push(JSON.parse(JSON.stringify(strokes)));
            strokes = undoStack.pop();
            updateStrokeList();
            render();
        }}

        function redoAction() {{
            if (redoStack.length === 0) return;
            undoStack.push(JSON.parse(JSON.stringify(strokes)));
            strokes = redoStack.pop();
            updateStrokeList();
            render();
        }}

        function updateStats() {{
            const visible = strokes.filter(s => s.visible);
            const totalPoints = visible.reduce((sum, s) => sum + s.points.length, 0);
            document.getElementById('statStrokes').textContent = visible.length;
            document.getElementById('statPoints').textContent = totalPoints;
            document.getElementById('statSelected').textContent =
                selectedStrokeIds.size > 0 ? selectedStrokeIds.size : '-';
        }}

        function saveGlyph() {{
            const char = document.getElementById('glyphChar').value;
            if (!char) {{
                alert('Please enter a character');
                return;
            }}

            fontLibrary[char] = {{
                strokes: JSON.parse(JSON.stringify(strokes)),
                name: document.getElementById('glyphName').value || char
            }};

            updateGlyphGrid();
            alert(`Glyph '${{char}}' saved to library`);
        }}

        function loadGlyph(char) {{
            if (!fontLibrary[char]) return;
            strokes = JSON.parse(JSON.stringify(fontLibrary[char].strokes));
            document.getElementById('glyphChar').value = char;
            document.getElementById('glyphName').value = fontLibrary[char].name;
            updateStrokeList();
            render();
        }}

        function newGlyph() {{
            if (strokes.length > 0 && !confirm('Clear current strokes?')) return;
            strokes = [];
            selectedStrokeIds.clear();
            document.getElementById('glyphChar').value = '';
            document.getElementById('glyphName').value = '';
            updateStrokeList();
            render();
        }}

        function updateGlyphGrid() {{
            const grid = document.getElementById('glyphGrid');
            grid.innerHTML = '';

            Object.keys(fontLibrary).sort().forEach(char => {{
                const div = document.createElement('div');
                div.className = 'glyph-item';
                div.textContent = char;
                div.onclick = () => loadGlyph(char);
                grid.appendChild(div);
            }});
        }}

        function exportPenCommands() {{
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

        function exportFont() {{
            const json = JSON.stringify(fontLibrary, null, 2);
            const blob = new Blob([json], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'font.json';
            a.click();
            URL.revokeObjectURL(url);
        }}

        function loadFont() {{
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = (e) => {{
                const file = e.target.files[0];
                const reader = new FileReader();
                reader.onload = (ev) => {{
                    try {{
                        fontLibrary = JSON.parse(ev.target.result);
                        updateGlyphGrid();
                        alert('Font loaded successfully');
                    }} catch (err) {{
                        alert('Error loading font: ' + err.message);
                    }}
                }};
                reader.readAsText(file);
            }};
            input.click();
        }}

        // Event listeners for property controls
        document.getElementById('strokeColor').oninput = function() {{
            if (selectedStrokeIds.size !== 1) return;
            const id = Array.from(selectedStrokeIds)[0];
            const stroke = strokes.find(s => s.id === id);
            if (stroke) {{
                stroke.color = this.value;
                updateStrokeList();
                render();
            }}
        }};

        // Initialize on load
        init();
    </script>
</body>
</html>"""

    return html


class GlyphEditorHandler(http.server.SimpleHTTPRequestHandler):
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
        print("Glyph Editor - Advanced Interactive Font Creation Tool")
        print("=" * 70)
        print()
        print("Usage: python3 glyph_editor.py <input.txt>")
        print()
        print("Features:")
        print("  - Inkscape-like visual interface")
        print("  - Draw, select, edit, delete strokes")
        print("  - Drag & drop stroke reordering")
        print("  - Edit individual nodes")
        print("  - Real-time preview")
        print("  - Font library management")
        print("  - Undo/Redo support")
        print("  - Export PEN commands or complete fonts")
        print()
        print("Keyboard Shortcuts:")
        print("  V - Select tool")
        print("  D - Draw tool")
        print("  E - Erase tool")
        print("  N - Node edit tool")
        print("  Ctrl+Z - Undo")
        print("  Ctrl+Y - Redo")
        print("  Delete - Delete selected stroke")
        print()
        return 1

    input_file = sys.argv[1]

    print("Loading:", input_file)
    strokes = parse_pen_commands(input_file)

    if not strokes:
        print("Warning: No strokes found, starting with empty canvas")
        strokes = []

    print(f"Loaded: {len(strokes)} strokes")
    print()
    print("Generating advanced editor interface...")

    html = generate_html_editor(strokes, input_file)
    GlyphEditorHandler.html_content = html

    port = 8000
    print(f"Starting Glyph Editor on http://localhost:{port}")
    print()

    server = socketserver.TCPServer(("", port), GlyphEditorHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    print("Opening browser...")
    webbrowser.open(f'http://localhost:{port}')
    print()
    print("Glyph Editor running. Press Ctrl+C to stop.")
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
