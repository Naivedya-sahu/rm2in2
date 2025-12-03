#!/usr/bin/env python3
"""
Generate test patterns using different coordinate transformations.

This tool creates PEN command files with various transformation formulas
to empirically determine which one produces correct output on the RM2.

Usage:
    python test_transformations.py <pattern> <output_dir>

Patterns:
    corners    - Four corners of screen
    cross      - Centered crosshair
    grid       - 3x3 grid
    circle     - Circle in center
    all        - Generate all patterns
"""

import sys
from pathlib import Path
import math

# Display dimensions (SVG/design space) - portrait orientation
DISPLAY_WIDTH = 1404
DISPLAY_HEIGHT = 1872

# NOTE: inject.c now handles the transformation to Wacom coordinates
# We generate coordinates in DISPLAY space (1404×1872)


class Transform:
    """Base class for coordinate transformations.

    NOW: We just pass through display coordinates.
    The inject.c on the RM2 handles the actual transformation to Wacom space.
    """

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def transform(self, svg_x, svg_y):
        """Pass through display coordinates - inject.c will transform."""
        return svg_x, svg_y

    def to_pen_command(self, svg_x, svg_y):
        """Convert SVG coordinates to PEN command (display space)."""
        x, y = self.transform(svg_x, svg_y)
        return int(round(x)), int(round(y))


class TransformA(Transform):
    """Pass through - inject.c handles transformation."""

    def __init__(self):
        super().__init__("CORRECT", "Display coordinates (inject.c transforms)")

    def transform(self, svg_x, svg_y):
        # Pass through display coordinates
        return svg_x, svg_y


class TransformB(Transform):
    """Swap X/Y axes."""

    def __init__(self):
        super().__init__("B_Swap", "Swap X and Y axes")

    def transform(self, svg_x, svg_y):
        wacom_x = (svg_y / DISPLAY_HEIGHT) * WACOM_MAX_Y
        wacom_y = (svg_x / DISPLAY_WIDTH) * WACOM_MAX_X
        return wacom_x, wacom_y


class TransformC(Transform):
    """Swap X/Y and flip Y."""

    def __init__(self):
        super().__init__("C_SwapFlipY", "Swap axes + flip Y")

    def transform(self, svg_x, svg_y):
        wacom_x = ((DISPLAY_HEIGHT - svg_y) / DISPLAY_HEIGHT) * WACOM_MAX_Y
        wacom_y = (svg_x / DISPLAY_WIDTH) * WACOM_MAX_X
        return wacom_x, wacom_y


class TransformD(Transform):
    """Swap X/Y and flip X."""

    def __init__(self):
        super().__init__("D_SwapFlipX", "Swap axes + flip X")

    def transform(self, svg_x, svg_y):
        wacom_x = (svg_y / DISPLAY_HEIGHT) * WACOM_MAX_Y
        wacom_y = ((DISPLAY_WIDTH - svg_x) / DISPLAY_WIDTH) * WACOM_MAX_X
        return wacom_x, wacom_y


class TransformE(Transform):
    """Swap X/Y and flip both."""

    def __init__(self):
        super().__init__("E_SwapFlipBoth", "Swap axes + flip both")

    def transform(self, svg_x, svg_y):
        wacom_x = ((DISPLAY_HEIGHT - svg_y) / DISPLAY_HEIGHT) * WACOM_MAX_Y
        wacom_y = ((DISPLAY_WIDTH - svg_x) / DISPLAY_WIDTH) * WACOM_MAX_X
        return wacom_x, wacom_y


class TransformF(Transform):
    """Direct mapping with flipped Y."""

    def __init__(self):
        super().__init__("F_DirectFlipY", "Direct scale + flip Y")

    def transform(self, svg_x, svg_y):
        wacom_x = (svg_x / DISPLAY_WIDTH) * WACOM_MAX_X
        wacom_y = ((DISPLAY_HEIGHT - svg_y) / DISPLAY_HEIGHT) * WACOM_MAX_Y
        return wacom_x, wacom_y


class TransformG(Transform):
    """Direct mapping with flipped X."""

    def __init__(self):
        super().__init__("G_DirectFlipX", "Direct scale + flip X")

    def transform(self, svg_x, svg_y):
        wacom_x = ((DISPLAY_WIDTH - svg_x) / DISPLAY_WIDTH) * WACOM_MAX_X
        wacom_y = (svg_y / DISPLAY_HEIGHT) * WACOM_MAX_Y
        return wacom_x, wacom_y


class TransformH(Transform):
    """Direct mapping with both flipped."""

    def __init__(self):
        super().__init__("H_DirectFlipBoth", "Direct scale + flip both")

    def transform(self, svg_x, svg_y):
        wacom_x = ((DISPLAY_WIDTH - svg_x) / DISPLAY_WIDTH) * WACOM_MAX_X
        wacom_y = ((DISPLAY_HEIGHT - svg_y) / DISPLAY_HEIGHT) * WACOM_MAX_Y
        return wacom_x, wacom_y


# Single correct transformation (inject.c handles the rest)
ALL_TRANSFORMS = [
    TransformA()
]


class PatternGenerator:
    """Generate test patterns in SVG coordinate space."""

    @staticmethod
    def corners():
        """Four corners pattern with margin."""
        margin = 100  # Pixels from edge
        return [
            # Corner 1: Top-left
            [(margin, margin)],
            # Corner 2: Top-right
            [(DISPLAY_WIDTH - margin, margin)],
            # Corner 3: Bottom-left
            [(margin, DISPLAY_HEIGHT - margin)],
            # Corner 4: Bottom-right
            [(DISPLAY_WIDTH - margin, DISPLAY_HEIGHT - margin)]
        ]

    @staticmethod
    def cross():
        """Centered crosshair."""
        center_x = DISPLAY_WIDTH // 2
        center_y = DISPLAY_HEIGHT // 2
        size = 200  # Length of each arm

        return [
            # Horizontal line
            [(center_x - size, center_y), (center_x + size, center_y)],
            # Vertical line
            [(center_x, center_y - size), (center_x, center_y + size)]
        ]

    @staticmethod
    def grid():
        """3x3 grid of points."""
        points = []
        margin = 200

        for row in range(3):
            for col in range(3):
                x = margin + col * (DISPLAY_WIDTH - 2 * margin) // 2
                y = margin + row * (DISPLAY_HEIGHT - 2 * margin) // 2
                points.append([(x, y)])

        return points

    @staticmethod
    def circle(center_x=None, center_y=None, radius=None):
        """Circle pattern."""
        if center_x is None:
            center_x = DISPLAY_WIDTH // 2
        if center_y is None:
            center_y = DISPLAY_HEIGHT // 2
        if radius is None:
            radius = min(DISPLAY_WIDTH, DISPLAY_HEIGHT) // 4

        points = []
        steps = 36  # Points around circle

        for i in range(steps + 1):
            angle = (i / steps) * 2 * math.pi
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append((x, y))

        return [points]


def generate_pen_commands(strokes, transform, output_file):
    """Generate PEN command file from strokes using given transform."""

    lines = []
    lines.append(f"# Test Pattern - Transform: {transform.name}")
    lines.append(f"# Description: {transform.description}")
    lines.append(f"#")
    lines.append(f"# If this appears correctly on screen, this is the right transform!")
    lines.append("")

    for stroke_idx, stroke in enumerate(strokes):
        lines.append(f"# Stroke {stroke_idx + 1}")

        for point_idx, (svg_x, svg_y) in enumerate(stroke):
            wx, wy = transform.to_pen_command(svg_x, svg_y)

            # Clamp to valid display range
            wx = max(0, min(DISPLAY_WIDTH, wx))
            wy = max(0, min(DISPLAY_HEIGHT, wy))

            if point_idx == 0:
                lines.append(f"PEN_DOWN {wx} {wy}")
            else:
                lines.append(f"PEN_MOVE {wx} {wy}")

        lines.append("PEN_UP")
        lines.append("DELAY 50")
        lines.append("")

    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))

    print(f"  Generated: {output_file}")


def generate_pattern(pattern_name, output_dir):
    """Generate test pattern with all transformations."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get pattern strokes
    if pattern_name == "corners":
        strokes = PatternGenerator.corners()
    elif pattern_name == "cross":
        strokes = PatternGenerator.cross()
    elif pattern_name == "grid":
        strokes = PatternGenerator.grid()
    elif pattern_name == "circle":
        strokes = PatternGenerator.circle()
    else:
        print(f"Unknown pattern: {pattern_name}")
        return

    print(f"\nGenerating '{pattern_name}' pattern with all transforms...")

    # Generate file for each transformation
    for transform in ALL_TRANSFORMS:
        output_file = output_dir / f"{pattern_name}_{transform.name}.txt"
        generate_pen_commands(strokes, transform, output_file)

    print(f"\n✓ Generated {len(ALL_TRANSFORMS)} files in {output_dir}/")
    print(f"\nNext steps:")
    print(f"  1. Test each file on RM2:")
    print(f"     ./send.sh {output_dir}/{pattern_name}_<transform>.txt")
    print(f"  2. Observe which transform produces correct output")
    print(f"  3. Document the winning transform")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    pattern = sys.argv[1]
    output_dir = sys.argv[2]

    if pattern == "all":
        for p in ["corners", "cross", "grid", "circle"]:
            generate_pattern(p, output_dir)
    else:
        generate_pattern(pattern, output_dir)


if __name__ == '__main__':
    main()
