#!/usr/bin/env python3
"""
RM2 Coordinate System Diagnostic Tests

Generates test pattern files to empirically determine coordinate mapping issues.
All coordinates are in DISPLAY space (1404×1872 portrait).
The inject.c on RM2 handles transformation to Wacom space.

Usage:
    python diagnostic_tests.py

Output:
    Creates .txt files in the same directory as this script.
"""

import os
import math
from pathlib import Path

# Display dimensions (portrait orientation)
DISPLAY_WIDTH = 1404
DISPLAY_HEIGHT = 1872

# Output directory = same as script location
OUTPUT_DIR = Path(__file__).parent


def write_test_file(filename, commands, description):
    """Write commands to a test file with header."""
    filepath = OUTPUT_DIR / filename
    
    lines = [
        f"# {filename}",
        f"# {description}",
        "#",
        "# Display coordinates (1404x1872 portrait)",
        "# X: 0=left, 1404=right",
        "# Y: 0=top, 1872=bottom",
        "#",
        ""
    ]
    lines.extend(commands)
    
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Created: {filepath}")


def make_dot(x, y, label=""):
    """Generate commands for a single dot/point."""
    cmds = []
    if label:
        cmds.append(f"# {label}")
    cmds.append(f"PEN_DOWN {x} {y}")
    cmds.append("DELAY 50")
    cmds.append("PEN_UP")
    cmds.append("DELAY 100")
    cmds.append("")
    return cmds


def make_line(x1, y1, x2, y2, label="", steps=20):
    """Generate commands for a line with interpolation."""
    cmds = []
    if label:
        cmds.append(f"# {label}")
    
    cmds.append(f"PEN_DOWN {x1} {y1}")
    
    for i in range(1, steps + 1):
        t = i / steps
        x = int(x1 + t * (x2 - x1))
        y = int(y1 + t * (y2 - y1))
        cmds.append(f"PEN_MOVE {x} {y}")
    
    cmds.append("PEN_UP")
    cmds.append("DELAY 100")
    cmds.append("")
    return cmds


def make_rectangle(x1, y1, x2, y2, label="", steps_per_side=10):
    """Generate commands for a rectangle (closed path)."""
    cmds = []
    if label:
        cmds.append(f"# {label}")
    
    # Start at top-left
    cmds.append(f"PEN_DOWN {x1} {y1}")
    
    # Top edge (left to right)
    for i in range(1, steps_per_side + 1):
        t = i / steps_per_side
        x = int(x1 + t * (x2 - x1))
        cmds.append(f"PEN_MOVE {x} {y1}")
    
    # Right edge (top to bottom)
    for i in range(1, steps_per_side + 1):
        t = i / steps_per_side
        y = int(y1 + t * (y2 - y1))
        cmds.append(f"PEN_MOVE {x2} {y}")
    
    # Bottom edge (right to left)
    for i in range(1, steps_per_side + 1):
        t = i / steps_per_side
        x = int(x2 - t * (x2 - x1))
        cmds.append(f"PEN_MOVE {x} {y2}")
    
    # Left edge (bottom to top, back to start)
    for i in range(1, steps_per_side + 1):
        t = i / steps_per_side
        y = int(y2 - t * (y2 - y1))
        cmds.append(f"PEN_MOVE {x1} {y}")
    
    cmds.append("PEN_UP")
    cmds.append("DELAY 100")
    cmds.append("")
    return cmds


def make_circle(cx, cy, radius, label="", steps=36):
    """Generate commands for a circle."""
    cmds = []
    if label:
        cmds.append(f"# {label}")
    
    # Start at angle 0
    start_x = int(cx + radius)
    start_y = int(cy)
    cmds.append(f"PEN_DOWN {start_x} {start_y}")
    
    for i in range(1, steps + 1):
        angle = (i / steps) * 2 * math.pi
        x = int(cx + radius * math.cos(angle))
        y = int(cy + radius * math.sin(angle))
        cmds.append(f"PEN_MOVE {x} {y}")
    
    cmds.append("PEN_UP")
    cmds.append("DELAY 100")
    cmds.append("")
    return cmds


def make_triangle(x1, y1, x2, y2, x3, y3, label="", steps_per_side=15):
    """Generate commands for a closed triangle."""
    cmds = []
    if label:
        cmds.append(f"# {label}")
    
    cmds.append(f"PEN_DOWN {x1} {y1}")
    
    # Side 1: point1 to point2
    for i in range(1, steps_per_side + 1):
        t = i / steps_per_side
        x = int(x1 + t * (x2 - x1))
        y = int(y1 + t * (y2 - y1))
        cmds.append(f"PEN_MOVE {x} {y}")
    
    # Side 2: point2 to point3
    for i in range(1, steps_per_side + 1):
        t = i / steps_per_side
        x = int(x2 + t * (x3 - x2))
        y = int(y2 + t * (y3 - y2))
        cmds.append(f"PEN_MOVE {x} {y}")
    
    # Side 3: point3 back to point1
    for i in range(1, steps_per_side + 1):
        t = i / steps_per_side
        x = int(x3 + t * (x1 - x3))
        y = int(y3 + t * (y1 - y3))
        cmds.append(f"PEN_MOVE {x} {y}")
    
    cmds.append("PEN_UP")
    cmds.append("DELAY 100")
    cmds.append("")
    return cmds


# =============================================================================
# TEST 1: Axis Alignment
# =============================================================================

def test1_axis_alignment():
    """Test if horizontal and vertical lines appear straight."""
    cmds = []
    
    center_x = DISPLAY_WIDTH // 2   # 702
    center_y = DISPLAY_HEIGHT // 2  # 936
    
    # Horizontal line through center
    cmds.extend(make_line(200, center_y, 1200, center_y, 
                          label="Horizontal line (Y=936, X: 200->1200)"))
    
    # Vertical line through center
    cmds.extend(make_line(center_x, 200, center_x, 1672,
                          label="Vertical line (X=702, Y: 200->1672)"))
    
    write_test_file(
        "test1_axis_alignment.txt",
        cmds,
        "TEST 1: Axis Alignment - Should show perfectly straight cross"
    )


# =============================================================================
# TEST 2: Aspect Ratio
# =============================================================================

def test2_aspect_ratio():
    """Test if a square appears as a square."""
    cmds = []
    
    # 500x500 square centered on screen
    center_x = DISPLAY_WIDTH // 2
    center_y = DISPLAY_HEIGHT // 2
    half_size = 250
    
    x1 = center_x - half_size  # 452
    y1 = center_y - half_size  # 686
    x2 = center_x + half_size  # 952
    y2 = center_y + half_size  # 1186
    
    cmds.extend(make_rectangle(x1, y1, x2, y2,
                               label=f"Square 500x500 at center ({x1},{y1}) to ({x2},{y2})"))
    
    # Add reference: smaller square to compare
    small_half = 100
    sx1 = center_x - small_half
    sy1 = center_y - small_half
    sx2 = center_x + small_half
    sy2 = center_y + small_half
    
    cmds.extend(make_rectangle(sx1, sy1, sx2, sy2,
                               label=f"Inner square 200x200"))
    
    write_test_file(
        "test2_aspect_ratio.txt",
        cmds,
        "TEST 2: Aspect Ratio - Both shapes should be perfect squares"
    )


# =============================================================================
# TEST 3: Origin and Corners
# =============================================================================

def test3_corners():
    """Test corner positions with known margins."""
    cmds = []
    
    margin = 100
    
    # Four corner dots
    cmds.extend(make_dot(margin, margin, 
                         label=f"Top-Left ({margin}, {margin})"))
    cmds.extend(make_dot(DISPLAY_WIDTH - margin, margin,
                         label=f"Top-Right ({DISPLAY_WIDTH - margin}, {margin})"))
    cmds.extend(make_dot(margin, DISPLAY_HEIGHT - margin,
                         label=f"Bottom-Left ({margin}, {DISPLAY_HEIGHT - margin})"))
    cmds.extend(make_dot(DISPLAY_WIDTH - margin, DISPLAY_HEIGHT - margin,
                         label=f"Bottom-Right ({DISPLAY_WIDTH - margin}, {DISPLAY_HEIGHT - margin})"))
    
    # Center dot for reference
    cmds.extend(make_dot(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2,
                         label=f"Center ({DISPLAY_WIDTH // 2}, {DISPLAY_HEIGHT // 2})"))
    
    write_test_file(
        "test3_corners.txt",
        cmds,
        "TEST 3: Corners - 4 corners + center, each 100px from edge"
    )


# =============================================================================
# TEST 4: Closed Shape
# =============================================================================

def test4_closed_triangle():
    """Test if a closed triangle actually closes."""
    cmds = []
    
    # Equilateral-ish triangle centered on screen
    center_x = DISPLAY_WIDTH // 2
    center_y = DISPLAY_HEIGHT // 2
    
    # Triangle points
    top = (center_x, center_y - 300)           # Top vertex
    bottom_left = (center_x - 260, center_y + 150)   # Bottom-left
    bottom_right = (center_x + 260, center_y + 150)  # Bottom-right
    
    cmds.extend(make_triangle(
        top[0], top[1],
        bottom_left[0], bottom_left[1],
        bottom_right[0], bottom_right[1],
        label="Triangle - should close perfectly"
    ))
    
    write_test_file(
        "test4_closed_triangle.txt",
        cmds,
        "TEST 4: Closed Shape - Triangle should have no gap at vertices"
    )


# =============================================================================
# TEST 5: Circle (diagnostic for your current issue)
# =============================================================================

def test5_circle():
    """Test circle rendering with different step counts."""
    cmds = []
    
    center_x = DISPLAY_WIDTH // 2
    center_y = DISPLAY_HEIGHT // 2
    
    # Circle with 36 steps (current)
    cmds.extend(make_circle(center_x, center_y, 300,
                            label="Circle R=300, 36 steps", steps=36))
    
    # Smaller circle with more steps
    cmds.extend(make_circle(center_x, center_y, 150,
                            label="Circle R=150, 72 steps", steps=72))
    
    write_test_file(
        "test5_circle.txt",
        cmds,
        "TEST 5: Circle - Should be round, not oval. Should close."
    )


# =============================================================================
# TEST 6: Grid (uniformity check)
# =============================================================================

def test6_grid():
    """Test coordinate uniformity across screen."""
    cmds = []
    
    margin = 150
    cols = 5
    rows = 7
    
    x_step = (DISPLAY_WIDTH - 2 * margin) // (cols - 1)
    y_step = (DISPLAY_HEIGHT - 2 * margin) // (rows - 1)
    
    for row in range(rows):
        for col in range(cols):
            x = margin + col * x_step
            y = margin + row * y_step
            cmds.extend(make_dot(x, y, label=f"Grid [{row},{col}] = ({x}, {y})"))
    
    write_test_file(
        "test6_grid.txt",
        cmds,
        "TEST 6: Grid - 5x7 dots should be evenly spaced"
    )


# =============================================================================
# TEST 7: Diagonal Lines
# =============================================================================

def test7_diagonals():
    """Test diagonal lines for skew detection."""
    cmds = []
    
    margin = 100
    
    # Diagonal from top-left to bottom-right
    cmds.extend(make_line(margin, margin, 
                          DISPLAY_WIDTH - margin, DISPLAY_HEIGHT - margin,
                          label="Diagonal TL to BR", steps=40))
    
    # Diagonal from top-right to bottom-left
    cmds.extend(make_line(DISPLAY_WIDTH - margin, margin,
                          margin, DISPLAY_HEIGHT - margin,
                          label="Diagonal TR to BL", steps=40))
    
    write_test_file(
        "test7_diagonals.txt",
        cmds,
        "TEST 7: Diagonals - Should form an X, lines should be straight"
    )


# =============================================================================
# MAIN
# =============================================================================

def main():
    print(f"Generating diagnostic tests in: {OUTPUT_DIR}")
    print(f"Display: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT} (portrait)")
    print()
    
    test1_axis_alignment()
    test2_aspect_ratio()
    test3_corners()
    test4_closed_triangle()
    test5_circle()
    test6_grid()
    test7_diagonals()
    
    print()
    print("=" * 60)
    print("TESTING PROCEDURE")
    print("=" * 60)
    print("""
1. Deploy and start injection service on RM2
2. Open a blank note in Xochitl
3. Run each test file one at a time:
   
   ./Rm2in2/scripts/send.sh test1_axis_alignment.txt
   
4. Record observations for each test:

   TEST 1: Are lines perfectly horizontal/vertical or tilted?
   TEST 2: Are squares actually square or rectangular?
   TEST 3: Are dots in expected corners with equal margins?
   TEST 4: Does triangle close properly at all vertices?
   TEST 5: Is circle round or oval? Does it close?
   TEST 6: Is grid evenly spaced in both directions?
   TEST 7: Are diagonals straight and crossing at center?

5. Report findings before making code changes.
""")


if __name__ == "__main__":
    main()