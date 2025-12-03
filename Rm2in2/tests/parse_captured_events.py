#!/usr/bin/env python3
"""
Parse captured pen events and extract coordinate data.

Usage:
    python parse_captured_events.py pen_capture.txt

Analyzes evtest output and extracts ABS_X, ABS_Y coordinates
from pen down events.
"""

import sys
import re
from pathlib import Path

# Known display dimensions
DISPLAY_WIDTH = 1404
DISPLAY_HEIGHT = 1872

# Wacom sensor range
WACOM_MAX_X = 20966
WACOM_MAX_Y = 15725


def parse_evtest_output(filepath):
    """Parse evtest output and extract pen events."""

    print(f"Parsing: {filepath}\n")

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Track current pen state
    current_event = {
        'x': None,
        'y': None,
        'pressure': None,
        'touch': False
    }

    pen_events = []

    for line in lines:
        # Look for event lines
        # Format: Event: time 1234.567890, type 3 (EV_ABS), code 0 (ABS_X), value 12345

        match = re.search(r'type 3 \(EV_ABS\), code 0 \(ABS_X\), value (\d+)', line)
        if match:
            current_event['x'] = int(match.group(1))
            continue

        match = re.search(r'type 3 \(EV_ABS\), code 1 \(ABS_Y\), value (\d+)', line)
        if match:
            current_event['y'] = int(match.group(1))
            continue

        match = re.search(r'type 3 \(EV_ABS\), code 24 \(ABS_PRESSURE\), value (\d+)', line)
        if match:
            current_event['pressure'] = int(match.group(1))
            continue

        match = re.search(r'type 1 \(EV_KEY\), code 330 \(BTN_TOUCH\), value 1', line)
        if match:
            current_event['touch'] = True
            continue

        match = re.search(r'type 1 \(EV_KEY\), code 330 \(BTN_TOUCH\), value 0', line)
        if match:
            # Pen up - save event if we have coordinates
            if current_event['x'] is not None and current_event['y'] is not None:
                pen_events.append({
                    'x': current_event['x'],
                    'y': current_event['y'],
                    'pressure': current_event['pressure']
                })

            # Reset for next event
            current_event = {
                'x': None,
                'y': None,
                'pressure': None,
                'touch': False
            }
            continue

    return pen_events


def analyze_events(events):
    """Analyze captured events and provide insights."""

    print(f"Total pen events captured: {len(events)}\n")

    if len(events) == 0:
        print("No events found. Make sure you drew on the screen during capture.")
        return

    # Extract coordinate ranges
    x_coords = [e['x'] for e in events]
    y_coords = [e['y'] for e in events]

    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)

    print("=== Coordinate Ranges ===")
    print(f"X: {min_x} to {max_x} (range: {max_x - min_x})")
    print(f"Y: {min_y} to {max_y} (range: {max_y - min_y})")
    print(f"\nExpected Wacom ranges:")
    print(f"X: 0 to {WACOM_MAX_X}")
    print(f"Y: 0 to {WACOM_MAX_Y}")

    # Check if ranges match expected
    if max_x > WACOM_MAX_X * 1.1 or max_y > WACOM_MAX_Y * 1.1:
        print("\n⚠️  WARNING: Coordinates exceed expected Wacom range!")

    print("\n=== Captured Events ===")
    print("(Showing first 5 and last 5 events)\n")

    # Show first 5 events
    for i, event in enumerate(events[:5]):
        print(f"Event {i+1}: X={event['x']:5d}, Y={event['y']:5d}, Pressure={event['pressure']}")

    if len(events) > 10:
        print("...")
        # Show last 5 events
        for i, event in enumerate(events[-5:], start=len(events)-4):
            print(f"Event {i}: X={event['x']:5d}, Y={event['y']:5d}, Pressure={event['pressure']}")

    # Calculate statistics
    print("\n=== Statistics ===")
    avg_x = sum(x_coords) / len(x_coords)
    avg_y = sum(y_coords) / len(y_coords)
    print(f"Average position: X={avg_x:.1f}, Y={avg_y:.1f}")
    print(f"Center of Wacom space: X={WACOM_MAX_X/2:.1f}, Y={WACOM_MAX_Y/2:.1f}")

    # Suggest transformation tests
    print("\n=== Suggested Tests ===")
    print("If you drew the 4-corner + center pattern:")
    print("1. Corner 1 (top-left)")
    print("2. Corner 2 (top-right)")
    print("3. Corner 3 (bottom-left)")
    print("4. Corner 4 (bottom-right)")
    print("5. Center (C)")
    print("")
    print("Look for events that correspond to these positions.")
    print("This will reveal the axis mapping and orientation.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_captured_events.py <capture_file>")
        print("\nExample:")
        print("  python parse_captured_events.py pen_capture.txt")
        sys.exit(1)

    filepath = sys.argv[1]

    if not Path(filepath).exists():
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    events = parse_evtest_output(filepath)
    analyze_events(events)

    # Save parsed data
    output_file = Path(filepath).stem + "_parsed.txt"
    with open(output_file, 'w') as f:
        f.write("# Parsed pen events\n")
        f.write("# Format: X Y PRESSURE\n\n")
        for event in events:
            f.write(f"{event['x']} {event['y']} {event['pressure']}\n")

    print(f"\n✓ Parsed data saved to: {output_file}")


if __name__ == '__main__':
    main()
