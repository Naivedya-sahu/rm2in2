#!/usr/bin/env python3
"""
SVG to RM2 injection converter
Handles coordinate system, scaling, and path extraction
"""

import sys
import re
import xml.etree.ElementTree as ET

# RM2 display dimensions (portrait)
RM2_WIDTH = 1404
RM2_HEIGHT = 1872

def parse_path_data(path_str):
    """Parse SVG path d="" attribute into coordinates"""
    coords = []
    tokens = re.findall(r'[MLHVZmlhvz]|[-+]?[0-9]*\.?[0-9]+', path_str)
    
    i = 0
    x, y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    
    while i < len(tokens):
        cmd = tokens[i]
        
        if cmd in 'Mm':
            x = float(tokens[i+1])
            y = float(tokens[i+2])
            if cmd == 'm':
                x += coords[-1][0] if coords else 0
                y += coords[-1][1] if coords else 0
            coords.append((x, y, 'M'))
            start_x, start_y = x, y
            i += 3
            
        elif cmd in 'Ll':
            x = float(tokens[i+1])
            y = float(tokens[i+2])
            if cmd == 'l':
                x += coords[-1][0]
                y += coords[-1][1]
            coords.append((x, y, 'L'))
            i += 3
            
        elif cmd in 'Hh':
            x = float(tokens[i+1])
            if cmd == 'h':
                x += coords[-1][0]
            y = coords[-1][1] if coords else 0
            coords.append((x, y, 'L'))
            i += 2
            
        elif cmd in 'Vv':
            y = float(tokens[i+1])
            if cmd == 'v':
                y += coords[-1][1]
            x = coords[-1][0] if coords else 0
            coords.append((x, y, 'L'))
            i += 2
            
        elif cmd in 'Zz':
            coords.append((start_x, start_y, 'L'))
            i += 1
        else:
            i += 1
    
    return coords

def svg_to_commands(svg_file, scale=1.0, offset_x=0, offset_y=0):
    """Convert SVG to injection commands"""
    tree = ET.parse(svg_file)
    root = tree.getroot()
    
    # Get viewBox
    viewbox = root.get('viewBox')
    if viewbox:
        _, _, vb_w, vb_h = map(float, viewbox.split())
    else:
        vb_w = float(root.get('width', 300))
        vb_h = float(root.get('height', 300))
    
    # Auto-scale if requested
    if scale == 'auto':
        scale = min(RM2_WIDTH / vb_w, RM2_HEIGHT / vb_h) * 0.8
    
    commands = []
    
    # Process all <path> elements
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    for path in root.findall('.//svg:path', ns):
        d = path.get('d')
        if not d:
            continue
        
        coords = parse_path_data(d)
        
        for x, y, cmd_type in coords:
            # Apply transformations
            x = int(x * scale + offset_x)
            y = int(y * scale + offset_y)
            
            # Clamp to display
            x = max(0, min(RM2_WIDTH - 1, x))
            y = max(0, min(RM2_HEIGHT - 1, y))
            
            if cmd_type == 'M':
                if commands and not commands[-1].startswith('PEN_UP'):
                    commands.append('PEN_UP')
                commands.append(f'PEN_DOWN {x} {y}')
            else:
                commands.append(f'PEN_MOVE {x} {y}')
        
        if commands and not commands[-1].startswith('PEN_UP'):
            commands.append('PEN_UP')
    
    return commands

def main():
    if len(sys.argv) < 2:
        print("Usage: svg2inject.py <file.svg> [scale] [offset_x] [offset_y]")
        print("  scale: number or 'auto'")
        sys.exit(1)
    
    svg_file = sys.argv[1]
    scale = sys.argv[2] if len(sys.argv) > 2 else 'auto'
    offset_x = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    offset_y = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    
    if scale != 'auto':
        scale = float(scale)
    
    commands = svg_to_commands(svg_file, scale, offset_x, offset_y)
    
    for cmd in commands:
        print(cmd)

if __name__ == '__main__':
    main()
