#!/bin/bash
# Interactive test script for all coordinate transformations
# Sends each test pattern one by one, waiting for user confirmation

set -e

PATTERN="${1:-corners}"
RM2_IP="${2:-10.11.99.1}"
TEST_DIR="test-output"
SCRIPT_DIR="$(dirname "$0")"
SEND_SCRIPT="$SCRIPT_DIR/send.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Check if test-output directory exists
if [ ! -d "$TEST_DIR" ]; then
    echo -e "${RED}ERROR:${NC} Test directory not found: $TEST_DIR"
    echo ""
    echo "Please run: ${GREEN}make test-patterns${NC}"
    exit 1
fi

# Get all test files for the pattern
TEST_FILES=($(ls $TEST_DIR/${PATTERN}_*.txt 2>/dev/null | sort))

if [ ${#TEST_FILES[@]} -eq 0 ]; then
    echo -e "${RED}ERROR:${NC} No test files found for pattern: $PATTERN"
    echo ""
    echo "Available patterns:"
    ls $TEST_DIR/*.txt 2>/dev/null | sed 's/.*\/\([^_]*\)_.*/\1/' | sort -u | sed 's/^/  - /'
    echo ""
    echo "Usage: $0 <pattern> [rm2_ip]"
    echo "Example: $0 corners 10.11.99.1"
    exit 1
fi

# Show header
clear
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}  RM2 Coordinate Transform Testing${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""
echo -e "${CYAN}Pattern:${NC} $PATTERN"
echo -e "${CYAN}RM2 IP:${NC}  $RM2_IP"
echo -e "${CYAN}Tests:${NC}   ${#TEST_FILES[@]} transformations"
echo ""
echo -e "${YELLOW}Instructions:${NC}"
echo "  1. Open the notes app on RM2"
echo "  2. Keep a blank page ready"
echo "  3. After each test is sent, tap the screen ONCE to render"
echo "  4. Observe the result"
echo "  5. Clear the page (swipe or erase)"
echo "  6. Press Enter here to continue to next test"
echo ""
echo -e "${YELLOW}Expected results for '$PATTERN':${NC}"

case "$PATTERN" in
    corners)
        echo "  ✓ Four dots near the actual screen corners"
        echo "  ✗ Dots in wrong positions = incorrect transform"
        ;;
    cross)
        echo "  ✓ Centered + shape (horizontal and vertical lines)"
        echo "  ✗ Off-center or rotated = incorrect transform"
        ;;
    grid)
        echo "  ✓ 3×3 grid of evenly spaced dots"
        echo "  ✗ Uneven spacing or distortion = incorrect transform"
        ;;
    circle)
        echo "  ✓ Perfect circle (not elliptical)"
        echo "  ✗ Oval or distorted = incorrect transform"
        ;;
esac

echo ""
read -p "Press Enter to start testing..."
echo ""

# Test each transformation
CORRECT_TRANSFORM=""
for i in "${!TEST_FILES[@]}"; do
    FILE="${TEST_FILES[$i]}"
    FILENAME=$(basename "$FILE")

    # Extract transform name (e.g., A_Direct from corners_A_Direct.txt)
    TRANSFORM=$(echo "$FILENAME" | sed 's/.*_\([A-H]_[A-Za-z]*\)\.txt/\1/')

    # Clear screen and show progress
    clear
    echo -e "${BOLD}========================================${NC}"
    echo -e "${BOLD}  Test $((i+1))/${#TEST_FILES[@]}: Transform $TRANSFORM${NC}"
    echo -e "${BOLD}========================================${NC}"
    echo ""

    # Show transform description
    case "${TRANSFORM:0:1}" in
        A) DESC="Direct mapping (no rotation)" ;;
        B) DESC="Swap X/Y axes" ;;
        C) DESC="Swap axes + flip Y" ;;
        D) DESC="Swap axes + flip X" ;;
        E) DESC="Swap axes + flip both" ;;
        F) DESC="Direct + flip Y" ;;
        G) DESC="Direct + flip X" ;;
        H) DESC="Direct + flip both" ;;
        *) DESC="Unknown transformation" ;;
    esac

    echo -e "${CYAN}Transform:${NC} $TRANSFORM"
    echo -e "${CYAN}Formula:${NC}   $DESC"
    echo -e "${CYAN}File:${NC}      $FILENAME"
    echo ""

    # Send the test pattern
    echo -e "${BLUE}Sending test pattern...${NC}"
    "$SEND_SCRIPT" "$FILE" "$RM2_IP" 2>&1 | grep -E "(Connected|Commands sent|Testing Transform)" || true

    echo ""
    echo -e "${GREEN}✓ Test pattern sent!${NC}"
    echo ""
    echo -e "${YELLOW}Action Required:${NC}"
    echo "  1. Tap the screen ONCE on your RM2 to render"
    echo "  2. Observe the result - does it look correct?"
    echo "  3. Clear the page"
    echo ""

    # Ask if this transform is correct
    read -p "Was this transform CORRECT? (y/n/skip): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        CORRECT_TRANSFORM="$TRANSFORM"
        echo -e "${GREEN}✓ Marked as CORRECT!${NC}"
        echo ""
        read -p "Continue testing other transforms? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            break
        fi
    elif [[ $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${YELLOW}⊘ Skipped${NC}"
    else
        echo -e "${RED}✗ Marked as incorrect${NC}"
    fi

    # Wait before next test (unless it's the last one)
    if [ $((i+1)) -lt ${#TEST_FILES[@]} ]; then
        echo ""
        read -p "Press Enter to continue to next test..."
    fi
done

# Show summary
clear
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}  Testing Complete!${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""
echo -e "${CYAN}Pattern tested:${NC} $PATTERN"
echo -e "${CYAN}Tests run:${NC}      ${#TEST_FILES[@]} transformations"
echo ""

if [ -n "$CORRECT_TRANSFORM" ]; then
    echo -e "${GREEN}✓ Correct transformation found:${NC} ${BOLD}$CORRECT_TRANSFORM${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Test the SAME transformation with other patterns:"
    echo "     $0 cross $RM2_IP"
    echo "     $0 grid $RM2_IP"
    echo "     $0 circle $RM2_IP"
    echo ""
    echo "  2. If $CORRECT_TRANSFORM works for ALL patterns,"
    echo "     update Rm2/src/inject.c with the verified formula"
    echo ""
    echo "  3. Document the findings in a new file:"
    echo "     Rm2in2/COORDINATE_SYSTEM.md"
    echo ""
else
    echo -e "${YELLOW}⚠ No correct transformation identified${NC}"
    echo ""
    echo -e "${YELLOW}Suggestions:${NC}"
    echo "  - Try testing again more carefully"
    echo "  - Check if RM2 is in correct orientation"
    echo "  - Verify injection service is running: make status"
    echo "  - Check logs: make logs"
    echo ""
fi

echo -e "${CYAN}Available patterns to test:${NC}"
ls $TEST_DIR/*.txt 2>/dev/null | sed 's/.*\/\([^_]*\)_.*/\1/' | sort -u | sed 's/^/  - /'
echo ""
