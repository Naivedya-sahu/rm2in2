#!/usr/bin/env python3
"""
Visual Coordinate Test - Simple pattern to identify orientation

Draws:
1. An arrow in each corner pointing to center
2. Text "TOP" at top, "BOTTOM" at bottom
3. Numbers 1-4 in corners (clockwise from top-left)

This makes it immediately obvious which transformation is correct.
"""

# Wacom coordinates
WACOM_MAX_X = 20966
WACOM_MAX_Y = 15725

MARGIN = 2000


def draw_arrow(start_x, start_y, end_x, end_y):
    """Draw an arrow from start to end."""
    commands = []

    # Main line
    commands.append(f"PEN_DOWN {start_x} {start_y}")
    commands.append(f"PEN_MOVE {end_x} {end_y}")
    commands.append("PEN_UP")

    # Arrow head (simple V shape)
    dx = end_x - start_x
    dy = end_y - start_y
    length = (dx*dx + dy*dy) ** 0.5

    if length > 0:
        # Normalize
        dx /= length
        dy /= length

        # Arrow head size
        head_len = 500
        head_width = 300

        # Perpendicular vector
        perp_x = -dy
        perp_y = dx

        # Arrow head points
        back_x = end_x - dx * head_len
        back_y = end_y - dy * head_len

        left_x = int(back_x + perp_x * head_width)
        left_y = int(back_y + perp_y * head_width)
        right_x = int(back_x - perp_x * head_width)
        right_y = int(back_y - perp_y * head_width)

        commands.append(f"PEN_DOWN {left_x} {left_y}")
        commands.append(f"PEN_MOVE {end_x} {end_y}")
        commands.append(f"PEN_MOVE {right_x} {right_y}")
        commands.append("PEN_UP")

    return commands


def draw_number(base_x, base_y, number):
    """Draw a number (1-4) as strokes."""
    commands = []
    size = 800

    if number == 1:
        # Draw "1"
        commands.append(f"PEN_DOWN {base_x + size//2} {base_y}")
        commands.append(f"PEN_MOVE {base_x + size//2} {base_y + size}")
        commands.append("PEN_UP")
        commands.append(f"PEN_DOWN {base_x} {base_y + size}")
        commands.append(f"PEN_MOVE {base_x + size} {base_y + size}")
        commands.append("PEN_UP")

    elif number == 2:
        # Draw "2"
        commands.append(f"PEN_DOWN {base_x} {base_y + size//4}")
        commands.append(f"PEN_MOVE {base_x} {base_y}")
        commands.append(f"PEN_MOVE {base_x + size} {base_y}")
        commands.append(f"PEN_MOVE {base_x + size} {base_y + size//2}")
        commands.append(f"PEN_MOVE {base_x} {base_y + size}")
        commands.append(f"PEN_MOVE {base_x + size} {base_y + size}")
        commands.append("PEN_UP")

    elif number == 3:
        # Draw "3"
        commands.append(f"PEN_DOWN {base_x} {base_y}")
        commands.append(f"PEN_MOVE {base_x + size} {base_y}")
        commands.append(f"PEN_MOVE {base_x + size} {base_y + size//2}")
        commands.append(f"PEN_MOVE {base_x} {base_y + size//2}")
        commands.append("PEN_UP")
        commands.append(f"PEN_DOWN {base_x + size} {base_y + size//2}")
        commands.append(f"PEN_MOVE {base_x + size} {base_y + size}")
        commands.append(f"PEN_MOVE {base_x} {base_y + size}")
        commands.append("PEN_UP")

    elif number == 4:
        # Draw "4"
        commands.append(f"PEN_DOWN {base_x} {base_y}")
        commands.append(f"PEN_MOVE {base_x} {base_y + size//2}")
        commands.append(f"PEN_MOVE {base_x + size} {base_y + size//2}")
        commands.append("PEN_UP")
        commands.append(f"PEN_DOWN {base_x + size} {base_y}")
        commands.append(f"PEN_MOVE {base_x + size} {base_y + size}")
        commands.append("PEN_UP")

    return commands


def main():
    commands = []
    commands.append("# Visual Coordinate Test")
    commands.append("# Should see: Numbers 1,2,3,4 clockwise from top-left")
    commands.append("# Arrows pointing toward center from each corner")
    commands.append("")

    center_x = WACOM_MAX_X // 2
    center_y = WACOM_MAX_Y // 2

    # Corner 1: Top-Left (should show "1")
    commands.append("# Corner 1: Top-Left")
    commands.extend(draw_number(MARGIN, MARGIN, 1))
    commands.extend(draw_arrow(MARGIN + 400, MARGIN + 400, center_x - 2000, center_y - 2000))
    commands.append("")

    # Corner 2: Top-Right (should show "2")
    commands.append("# Corner 2: Top-Right")
    commands.extend(draw_number(WACOM_MAX_X - MARGIN - 800, MARGIN, 2))
    commands.extend(draw_arrow(
        WACOM_MAX_X - MARGIN - 400, MARGIN + 400,
        center_x + 2000, center_y - 2000
    ))
    commands.append("")

    # Corner 3: Bottom-Right (should show "3")
    commands.append("# Corner 3: Bottom-Right")
    commands.extend(draw_number(
        WACOM_MAX_X - MARGIN - 800,
        WACOM_MAX_Y - MARGIN - 800,
        3
    ))
    commands.extend(draw_arrow(
        WACOM_MAX_X - MARGIN - 400, WACOM_MAX_Y - MARGIN - 400,
        center_x + 2000, center_y + 2000
    ))
    commands.append("")

    # Corner 4: Bottom-Left (should show "4")
    commands.append("# Corner 4: Bottom-Left")
    commands.extend(draw_number(MARGIN, WACOM_MAX_Y - MARGIN - 800, 4))
    commands.extend(draw_arrow(
        MARGIN + 400, WACOM_MAX_Y - MARGIN - 400,
        center_x - 2000, center_y + 2000
    ))
    commands.append("")

    # Center cross for reference
    commands.append("# Center cross")
    commands.append(f"PEN_DOWN {center_x - 1500} {center_y}")
    commands.append(f"PEN_MOVE {center_x + 1500} {center_y}")
    commands.append("PEN_UP")
    commands.append(f"PEN_DOWN {center_x} {center_y - 1500}")
    commands.append(f"PEN_MOVE {center_x} {center_y + 1500}")
    commands.append("PEN_UP")
    commands.append("")

    # Save output
    output_file = "coord_tests/visual_test.txt"
    import os
    os.makedirs("coord_tests", exist_ok=True)

    with open(output_file, 'w') as f:
        f.write('\n'.join(commands))

    print(f"Visual test generated: {output_file}")
    print()
    print("Expected result:")
    print("  Top-Left corner:     Number '1' with arrow pointing to center")
    print("  Top-Right corner:    Number '2' with arrow pointing to center")
    print("  Bottom-Right corner: Number '3' with arrow pointing to center")
    print("  Bottom-Left corner:  Number '4' with arrow pointing to center")
    print("  Center:              Cross")
    print()
    print("Deploy with: ./send.sh testing-tools/coord_tests/visual_test.txt")
    print()
    print("If numbers/arrows are in wrong corners, that indicates")
    print("the coordinate transformation needed.")


if __name__ == '__main__':
    main()
