#!/usr/bin/env python3
"""
Comprehensive Coordinate System Testing Suite

Generates test patterns to diagnose coordinate system issues:
- Mirroring (horizontal/vertical flip)
- Rotation (0°, 90°, 180°, 270°)
- Orientation problems

Tests all 8 possible transformations to find the correct one.
"""

import sys
from pathlib import Path

# Wacom coordinate system
WACOM_MAX_X = 20966
WACOM_MAX_Y = 15725

# Test pattern dimensions (in Wacom coordinates)
MARGIN = 1000
CENTER_X = WACOM_MAX_X // 2
CENTER_Y = WACOM_MAX_Y // 2
CROSS_SIZE = 2000


def generate_test_pattern(name, description):
    """Generate a comprehensive test pattern."""
    commands = []
    commands.append(f"# Test: {name}")
    commands.append(f"# {description}")
    commands.append("")

    # Test 1: Corner markers (identify which corner is which)
    commands.append("# Test 1: Corner Markers")
    commands.append("# Top-Left corner: Small L shape")
    commands.append(f"PEN_DOWN {MARGIN} {MARGIN}")
    commands.append(f"PEN_MOVE {MARGIN + 500} {MARGIN}")
    commands.append("PEN_UP")
    commands.append(f"PEN_DOWN {MARGIN} {MARGIN}")
    commands.append(f"PEN_MOVE {MARGIN} {MARGIN + 500}")
    commands.append("PEN_UP")
    commands.append("")

    # Top-Right corner: Small T shape
    commands.append("# Top-Right corner: Small T shape")
    commands.append(f"PEN_DOWN {WACOM_MAX_X - MARGIN - 500} {MARGIN}")
    commands.append(f"PEN_MOVE {WACOM_MAX_X - MARGIN + 500} {MARGIN}")
    commands.append("PEN_UP")
    commands.append(f"PEN_DOWN {WACOM_MAX_X - MARGIN} {MARGIN}")
    commands.append(f"PEN_MOVE {WACOM_MAX_X - MARGIN} {MARGIN + 500}")
    commands.append("PEN_UP")
    commands.append("")

    # Bottom-Left corner: Vertical line
    commands.append("# Bottom-Left corner: Vertical line")
    commands.append(f"PEN_DOWN {MARGIN} {WACOM_MAX_Y - MARGIN - 500}")
    commands.append(f"PEN_MOVE {MARGIN} {WACOM_MAX_Y - MARGIN}")
    commands.append("PEN_UP")
    commands.append("")

    # Bottom-Right corner: Diagonal
    commands.append("# Bottom-Right corner: Diagonal")
    commands.append(f"PEN_DOWN {WACOM_MAX_X - MARGIN - 500} {WACOM_MAX_Y - MARGIN - 500}")
    commands.append(f"PEN_MOVE {WACOM_MAX_X - MARGIN} {WACOM_MAX_Y - MARGIN}")
    commands.append("PEN_UP")
    commands.append("")

    # Test 2: Center cross (verify centering)
    commands.append("# Test 2: Center Cross")
    commands.append(f"PEN_DOWN {CENTER_X - CROSS_SIZE} {CENTER_Y}")
    commands.append(f"PEN_MOVE {CENTER_X + CROSS_SIZE} {CENTER_Y}")
    commands.append("PEN_UP")
    commands.append(f"PEN_DOWN {CENTER_X} {CENTER_Y - CROSS_SIZE}")
    commands.append(f"PEN_MOVE {CENTER_X} {CENTER_Y + CROSS_SIZE}")
    commands.append("PEN_UP")
    commands.append("")

    # Test 3: Directional arrows
    commands.append("# Test 3: Direction Indicators")
    commands.append("# Arrow pointing RIGHT (positive X direction)")
    commands.append(f"PEN_DOWN {CENTER_X - 1500} {CENTER_Y - 3000}")
    commands.append(f"PEN_MOVE {CENTER_X + 1500} {CENTER_Y - 3000}")
    commands.append("PEN_UP")
    commands.append(f"PEN_DOWN {CENTER_X + 1500} {CENTER_Y - 3000}")
    commands.append(f"PEN_MOVE {CENTER_X + 1000} {CENTER_Y - 3300}")
    commands.append("PEN_UP")
    commands.append(f"PEN_DOWN {CENTER_X + 1500} {CENTER_Y - 3000}")
    commands.append(f"PEN_MOVE {CENTER_X + 1000} {CENTER_Y - 2700}")
    commands.append("PEN_UP")
    commands.append("")

    # Arrow pointing DOWN (positive Y direction)
    commands.append("# Arrow pointing DOWN (positive Y direction)")
    commands.append(f"PEN_DOWN {CENTER_X} {CENTER_Y + 1000}")
    commands.append(f"PEN_MOVE {CENTER_X} {CENTER_Y + 3000}")
    commands.append("PEN_UP")
    commands.append(f"PEN_DOWN {CENTER_X} {CENTER_Y + 3000}")
    commands.append(f"PEN_MOVE {CENTER_X - 300} {CENTER_Y + 2500}")
    commands.append("PEN_UP")
    commands.append(f"PEN_DOWN {CENTER_X} {CENTER_Y + 3000}")
    commands.append(f"PEN_MOVE {CENTER_X + 300} {CENTER_Y + 2500}")
    commands.append("PEN_UP")
    commands.append("")

    # Test 4: Rectangle border
    commands.append("# Test 4: Border Rectangle")
    commands.append(f"PEN_DOWN {MARGIN} {MARGIN}")
    commands.append(f"PEN_MOVE {WACOM_MAX_X - MARGIN} {MARGIN}")
    commands.append(f"PEN_MOVE {WACOM_MAX_X - MARGIN} {WACOM_MAX_Y - MARGIN}")
    commands.append(f"PEN_MOVE {MARGIN} {WACOM_MAX_Y - MARGIN}")
    commands.append(f"PEN_MOVE {MARGIN} {MARGIN}")
    commands.append("PEN_UP")
    commands.append("")

    # Test 5: Letter "F" at top-left (should be readable)
    commands.append("# Test 5: Letter 'F' at top-left (should be readable)")
    base_x = MARGIN + 2000
    base_y = MARGIN + 2000
    commands.append(f"PEN_DOWN {base_x} {base_y}")
    commands.append(f"PEN_MOVE {base_x} {base_y + 1500}")
    commands.append("PEN_UP")
    commands.append(f"PEN_DOWN {base_x} {base_y}")
    commands.append(f"PEN_MOVE {base_x + 1000} {base_y}")
    commands.append("PEN_UP")
    commands.append(f"PEN_DOWN {base_x} {base_y + 750}")
    commands.append(f"PEN_MOVE {base_x + 800} {base_y + 750}")
    commands.append("PEN_UP")
    commands.append("")

    return commands


def generate_transformation_test(transform_id, transform_func, description):
    """Generate test with specific coordinate transformation."""
    commands = []
    commands.append(f"# Transformation Test {transform_id}: {description}")
    commands.append("")

    # Simple test pattern: L shape at what should be top-left
    test_points = [
        (1000, 1000, "origin"),
        (3000, 1000, "right"),
        (1000, 1000, "back to origin"),
        (1000, 3000, "down"),
    ]

    for i, (x, y, label) in enumerate(test_points):
        tx, ty = transform_func(x, y)
        if i == 0:
            commands.append(f"PEN_DOWN {tx} {ty}  # {label}")
        else:
            commands.append(f"PEN_MOVE {tx} {ty}  # {label}")
    commands.append("PEN_UP")
    commands.append("")

    # Add number indicator (transform_id as strokes)
    num_base_x, num_base_y = transform_func(5000, 5000)
    commands.append(f"# Number {transform_id}")

    # Draw the transform ID number
    if transform_id == 1:
        commands.append(f"PEN_DOWN {num_base_x} {num_base_y}")
        commands.append(f"PEN_MOVE {num_base_x} {num_base_y + 1000}")
        commands.append("PEN_UP")
    elif transform_id == 2:
        # Draw "2"
        commands.append(f"PEN_DOWN {num_base_x} {num_base_y}")
        commands.append(f"PEN_MOVE {num_base_x + 500} {num_base_y}")
        commands.append(f"PEN_MOVE {num_base_x + 500} {num_base_y + 500}")
        commands.append(f"PEN_MOVE {num_base_x} {num_base_y + 1000}")
        commands.append(f"PEN_MOVE {num_base_x + 500} {num_base_y + 1000}")
        commands.append("PEN_UP")
    # ... add more numbers as needed

    commands.append("")
    return commands


def main():
    output_dir = Path(__file__).parent / "coord_tests"
    output_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("Coordinate System Testing Suite")
    print("=" * 70)
    print()

    # Generate main test pattern
    print("[1/9] Generating main test pattern...")
    commands = generate_test_pattern(
        "Main Diagnostic Pattern",
        "Comprehensive pattern to identify coordinate issues"
    )

    output_file = output_dir / "main_test.txt"
    with open(output_file, 'w') as f:
        f.write('\n'.join(commands))
    print(f"      Saved: {output_file}")
    print()

    # Define all 8 possible transformations
    transformations = [
        (1, lambda x, y: (x, y), "No transform (identity)"),
        (2, lambda x, y: (WACOM_MAX_X - x, y), "Flip horizontal"),
        (3, lambda x, y: (x, WACOM_MAX_Y - y), "Flip vertical"),
        (4, lambda x, y: (WACOM_MAX_X - x, WACOM_MAX_Y - y), "Flip both (180° rotation)"),
        (5, lambda x, y: (y, x), "Swap X/Y (90° rotation)"),
        (6, lambda x, y: (WACOM_MAX_Y - y, x), "Swap + flip Y"),
        (7, lambda x, y: (y, WACOM_MAX_X - x), "Swap + flip X"),
        (8, lambda x, y: (WACOM_MAX_Y - y, WACOM_MAX_X - x), "Swap + flip both"),
    ]

    # Generate test for each transformation
    for idx, (tid, func, desc) in enumerate(transformations, start=2):
        print(f"[{idx}/9] Generating transformation {tid}: {desc}")
        commands = generate_transformation_test(tid, func, desc)
        output_file = output_dir / f"transform_{tid}.txt"
        with open(output_file, 'w') as f:
            f.write('\n'.join(commands))
        print(f"      Saved: {output_file}")

    print()
    print("=" * 70)
    print("Test Generation Complete!")
    print("=" * 70)
    print()
    print("How to use:")
    print()
    print("1. Start with the main test:")
    print(f"   ./send.sh {output_dir}/main_test.txt")
    print("   Observe which corners the markers appear in")
    print()
    print("2. Test each transformation:")
    print(f"   ./send.sh {output_dir}/transform_1.txt  # Try each 1-8")
    print("   Find which one produces correct orientation")
    print()
    print("3. Expected results:")
    print("   - Top-Left corner: Small L shape")
    print("   - Top-Right corner: Small T shape")
    print("   - Bottom-Left corner: Vertical line")
    print("   - Bottom-Right corner: Diagonal line")
    print("   - Center: Large cross")
    print("   - Arrows: RIGHT arrow points right, DOWN arrow points down")
    print("   - Border: Rectangle around edge")
    print("   - Letter F: Should be readable in top-left")
    print()
    print("4. Once you find the correct transformation:")
    print("   Update inject.c with that transformation function")
    print()


if __name__ == '__main__':
    main()
