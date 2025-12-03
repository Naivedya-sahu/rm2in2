#!/usr/bin/env python3
"""
Convert G-code (NGC format) to RM2 injection format.

G-code conventions:
- G00 = rapid move (pen up)
- G01 = linear move (pen down if Z < 0)
- G02/G03 = arc moves (pen down if Z < 0)
- Z > 0 = pen up
- Z < 0 = pen down

RM2 injection format:
- M x y = move to position (pen up)
- D x y = draw to position (pen down)
"""

import re
import sys
import math
from typing import List, Tuple, Optional

class GCodeConverter:
    def __init__(self, scale: float = 100.0):
        """
        Args:
            scale: Scale factor for coordinates (RM2 coords ~20k for full screen)
                   Default 100 converts mm to reasonable RM2 scale
        """
        self.scale = scale
        self.x = 0.0
        self.y = 0.0
        self.z = 5.0  # Start with pen up
        self.commands = []
        
    def parse_coordinates(self, line: str) -> dict:
        """Extract X, Y, Z, I, J from G-code line."""
        coords = {}
        # Match coordinate values
        for match in re.finditer(r'([XYZIJ])([-+]?\d+\.?\d*)', line):
            param = match.group(1)
            value = float(match.group(2))
            coords[param] = value
        return coords
    
    def add_move(self, x: float, y: float):
        """Add a move command (pen up)."""
        x_scaled = int(x * self.scale)
        y_scaled = int(y * self.scale)
        self.commands.append(f"M {x_scaled} {y_scaled}")
        
    def add_draw(self, x: float, y: float):
        """Add a draw command (pen down)."""
        x_scaled = int(x * self.scale)
        y_scaled = int(y * self.scale)
        self.commands.append(f"D {x_scaled} {y_scaled}")
    
    def interpolate_arc(self, end_x: float, end_y: float, 
                       center_i: float, center_j: float, 
                       clockwise: bool = False, segments: int = 20):
        """
        Interpolate arc into line segments.
        
        Args:
            end_x, end_y: End coordinates
            center_i, center_j: Relative center offsets from current position
            clockwise: True for G02, False for G03
            segments: Number of line segments to approximate arc
        """
        # Calculate center point (absolute coordinates)
        cx = self.x + center_i
        cy = self.y + center_j
        
        # Calculate start and end angles
        start_angle = math.atan2(self.y - cy, self.x - cx)
        end_angle = math.atan2(end_y - cy, end_x - cx)
        
        # Calculate radius
        radius = math.sqrt(center_i**2 + center_j**2)
        
        # Calculate angle sweep
        angle_diff = end_angle - start_angle
        
        # Normalize angle difference
        if clockwise:
            while angle_diff > 0:
                angle_diff -= 2 * math.pi
        else:
            while angle_diff < 0:
                angle_diff += 2 * math.pi
        
        # Generate intermediate points
        for i in range(1, segments + 1):
            t = i / segments
            angle = start_angle + angle_diff * t
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            self.add_draw(x, y)
    
    def process_line(self, line: str):
        """Process a single G-code line."""
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('(') or line.startswith('%') or line.startswith('M'):
            return
        
        coords = self.parse_coordinates(line)
        
        # Update Z if present
        if 'Z' in coords:
            self.z = coords['Z']
        
        # Handle different G-code commands
        if line.startswith('G00'):
            # Rapid move (pen up)
            if 'X' in coords:
                self.x = coords['X']
            if 'Y' in coords:
                self.y = coords['Y']
            if 'X' in coords or 'Y' in coords:
                self.add_move(self.x, self.y)
                
        elif line.startswith('G01'):
            # Linear interpolation
            new_x = coords.get('X', self.x)
            new_y = coords.get('Y', self.y)
            
            if self.z < 0:  # Pen down
                self.add_draw(new_x, new_y)
            else:  # Pen up
                self.add_move(new_x, new_y)
            
            self.x = new_x
            self.y = new_y
            
        elif line.startswith('G02') or line.startswith('G03'):
            # Arc interpolation
            if 'X' not in coords or 'Y' not in coords:
                return
            if 'I' not in coords or 'J' not in coords:
                return
            
            end_x = coords['X']
            end_y = coords['Y']
            center_i = coords['I']
            center_j = coords['J']
            clockwise = line.startswith('G02')
            
            if self.z < 0:  # Only draw if pen is down
                self.interpolate_arc(end_x, end_y, center_i, center_j, clockwise)
            
            self.x = end_x
            self.y = end_y
    
    def convert(self, gcode_lines: List[str]) -> List[str]:
        """Convert G-code lines to injection commands."""
        for line in gcode_lines:
            self.process_line(line)
        return self.commands
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Calculate bounding box of all coordinates."""
        if not self.commands:
            return (0, 0, 0, 0)
        
        x_coords = []
        y_coords = []
        
        for cmd in self.commands:
            parts = cmd.split()
            if len(parts) == 3:
                x_coords.append(int(parts[1]))
                y_coords.append(int(parts[2]))
        
        if not x_coords:
            return (0, 0, 0, 0)
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.ngc> [scale] [output.txt]")
        print(f"  scale: Scale factor (default: 100.0)")
        print(f"  output: Output file (default: stdout)")
        print(f"\nExample: {sys.argv[0]} test.ngc 100 output.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    scale = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Read G-code
    with open(input_file, 'r') as f:
        gcode_lines = f.readlines()
    
    # Convert
    converter = GCodeConverter(scale=scale)
    commands = converter.convert(gcode_lines)
    
    # Print statistics
    min_x, min_y, max_x, max_y = converter.get_bounds()
    print(f"# Converted {len(gcode_lines)} G-code lines to {len(commands)} injection commands", 
          file=sys.stderr)
    print(f"# Bounding box: ({min_x}, {min_y}) to ({max_x}, {max_y})", file=sys.stderr)
    print(f"# Dimensions: {max_x - min_x} x {max_y - min_y}", file=sys.stderr)
    
    # Output
    if output_file:
        with open(output_file, 'w') as f:
            for cmd in commands:
                f.write(cmd + '\n')
        print(f"# Written to {output_file}", file=sys.stderr)
    else:
        for cmd in commands:
            print(cmd)


if __name__ == '__main__':
    main()
