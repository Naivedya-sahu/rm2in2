#!/usr/bin/env python3
"""
Coordinate Transform Fixer

After testing transformations 1-8, use this script to update inject.c
with the correct transformation.

Usage:
    python fix_transform.py <transform_number>

Example:
    python fix_transform.py 5
"""

import sys
import re
from pathlib import Path


# All 8 possible transformations
TRANSFORMATIONS = {
    1: {
        'name': 'Identity (no transform)',
        'code': '''// PEN commands already use Wacom coordinates - pass through directly
static inline int to_wacom_x(int x) { return x; }
static inline int to_wacom_y(int y) { return y; }'''
    },
    2: {
        'name': 'Flip horizontal',
        'code': '''// Flip horizontal
static inline int to_wacom_x(int x) { return WACOM_MAX_X - x; }
static inline int to_wacom_y(int y) { return y; }'''
    },
    3: {
        'name': 'Flip vertical',
        'code': '''// Flip vertical
static inline int to_wacom_x(int x) { return x; }
static inline int to_wacom_y(int y) { return WACOM_MAX_Y - y; }'''
    },
    4: {
        'name': 'Flip both (180° rotation)',
        'code': '''// Flip both (180° rotation)
static inline int to_wacom_x(int x) { return WACOM_MAX_X - x; }
static inline int to_wacom_y(int y) { return WACOM_MAX_Y - y; }'''
    },
    5: {
        'name': 'Swap X/Y (90° rotation)',
        'code': '''// Swap X/Y (90° rotation)
static inline int to_wacom_x(int x) { return y; }  // Note: takes original y
static inline int to_wacom_y(int y) { return x; }  // Note: takes original x
// WARNING: This requires passing both x and y to each function'''
    },
    6: {
        'name': 'Swap + flip Y',
        'code': '''// Swap X/Y + flip Y
static inline int to_wacom_x(int x) { return WACOM_MAX_Y - y; }
static inline int to_wacom_y(int y) { return x; }
// WARNING: This requires passing both x and y to each function'''
    },
    7: {
        'name': 'Swap + flip X',
        'code': '''// Swap X/Y + flip X
static inline int to_wacom_x(int x) { return y; }
static inline int to_wacom_y(int y) { return WACOM_MAX_X - x; }
// WARNING: This requires passing both x and y to each function'''
    },
    8: {
        'name': 'Swap + flip both',
        'code': '''// Swap X/Y + flip both
static inline int to_wacom_x(int x) { return WACOM_MAX_Y - y; }
static inline int to_wacom_y(int y) { return WACOM_MAX_X - x; }
// WARNING: This requires passing both x and y to each function'''
    },
}


def update_inject_c(transform_num):
    """Update inject.c with the correct transformation."""
    inject_path = Path(__file__).parent.parent / "rm2-server" / "inject.c"

    if not inject_path.exists():
        print(f"[ERROR] inject.c not found at: {inject_path}")
        return False

    # Read current file
    with open(inject_path, 'r') as f:
        content = f.read()

    # Find and replace transformation functions
    pattern = r'// PEN commands already use Wacom coordinates - pass through directly\s*\nstatic inline int to_wacom_x\(int x\) \{ return x; \}\s*\nstatic inline int to_wacom_y\(int y\) \{ return y; \}'

    if transform_num in [1, 2, 3, 4]:
        # Simple transformations
        new_code = TRANSFORMATIONS[transform_num]['code']
        updated_content = re.sub(pattern, new_code, content)

        if updated_content == content:
            # Try alternative pattern (any existing transform)
            pattern = r'//[^\n]*\nstatic inline int to_wacom_x\([^)]+\)[^}]+}\s*\nstatic inline int to_wacom_y\([^)]+\)[^}]+}'
            updated_content = re.sub(pattern, new_code, content)

        with open(inject_path, 'w') as f:
            f.write(updated_content)

        print(f"[OK] Updated inject.c with transformation {transform_num}")
        print(f"     {TRANSFORMATIONS[transform_num]['name']}")
        return True

    else:
        # Swap transformations (5-8) - more complex, requires both x and y
        print(f"[WARN] Transformation {transform_num} requires swap (both x and y)")
        print(f"       {TRANSFORMATIONS[transform_num]['name']}")
        print()
        print("This transformation requires modifying the function signatures")
        print("to pass both x and y coordinates. Manual update needed.")
        print()
        print("Required changes:")
        print(TRANSFORMATIONS[transform_num]['code'])
        print()
        print("Also update all calls to to_wacom_x and to_wacom_y to pass both values.")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python fix_transform.py <transform_number>")
        print()
        print("Available transformations:")
        for num, info in TRANSFORMATIONS.items():
            print(f"  {num}: {info['name']}")
        print()
        print("Test each transformation first:")
        print("  ./send.sh testing-tools/coord_tests/transform_1.txt")
        print("  ./send.sh testing-tools/coord_tests/transform_2.txt")
        print("  ... etc")
        print()
        print("Find which one produces correct output, then:")
        print("  python fix_transform.py <number>")
        sys.exit(1)

    try:
        transform_num = int(sys.argv[1])
        if transform_num < 1 or transform_num > 8:
            raise ValueError()
    except ValueError:
        print(f"[ERROR] Invalid transformation number: {sys.argv[1]}")
        print("        Must be 1-8")
        sys.exit(1)

    print("=" * 70)
    print(f"Applying Transformation {transform_num}")
    print(f"{TRANSFORMATIONS[transform_num]['name']}")
    print("=" * 70)
    print()

    if update_inject_c(transform_num):
        print()
        print("Next steps:")
        print("  1. Recompile inject.so:")
        print("     cd rm2-server")
        print("     arm-linux-gnueabihf-gcc -shared -fPIC -O2 -o inject.so inject.c -ldl -lpthread")
        print("  2. Deploy to RM2:")
        print("     scp inject.so root@10.11.99.1:/opt/")
        print("  3. Restart xochitl:")
        print("     ssh root@10.11.99.1 systemctl restart xochitl")
        print("  4. Test again with visual_test.txt")
    else:
        print()
        print("Manual update required. See above for details.")


if __name__ == '__main__':
    main()
