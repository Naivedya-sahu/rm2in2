# Complete GUI Testing Guide

Step-by-step guide to test all dynamic GUI functionality with eraser-enabled lamp.

## Prerequisites

Before testing, ensure:
- ✅ Enhanced lamp deployed to `/opt/bin/lamp`
- ✅ Test scripts deployed to reMarkable
- ✅ SSH access to reMarkable (10.11.99.1)

## Deploy Test Scripts

```bash
# From your computer
scp test_gui_complete.sh root@10.11.99.1:/home/root/
scp examples/dynamic_ui_demo.sh root@10.11.99.1:/home/root/

# Make executable
ssh root@10.11.99.1 'chmod +x /home/root/*.sh'
```

## Test Suite 1: Automated Functionality Test

```bash
ssh root@10.11.99.1
cd /home/root
./test_gui_complete.sh
```

**What to Watch For:**
1. Main menu appears at bottom of screen
2. Submenu appears next to main menu
3. Component preview appears on right
4. Each section clears when requested
5. Transitions are smooth
6. Final cleanup leaves screen blank

**Expected Duration:** ~60 seconds

**Success Criteria:**
- All 13 tests pass
- No visual artifacts remain
- No errors in terminal output

## Test Suite 2: Manual Interactive Testing

### Test 1: Basic Drawing and Erasing

```bash
ssh root@10.11.99.1

# Draw a rectangle
echo "pen rectangle 200 200 600 600" | /opt/bin/lamp

# Verify: Rectangle visible on screen?
# [Wait 2 seconds]

# Erase it
echo "eraser fill 200 200 600 600 15" | /opt/bin/lamp

# Verify: Rectangle completely erased?
```

**Success:** Rectangle disappears completely, no traces left.

### Test 2: GUI State Machine

```bash
# State 1: CLOSED
# Verify: Screen clear in UI region (y: 1400-1872)

# State 2: Open Main Menu
echo "pen rectangle 50 1400 350 1850" | /opt/bin/lamp
echo "pen rectangle 70 1480 330 1560" | /opt/bin/lamp  # Category 1
echo "pen rectangle 70 1600 330 1680" | /opt/bin/lamp  # Category 2

# Verify: Menu visible with 2 category boxes?

# State 3: Open Submenu (keep main menu)
echo "pen rectangle 370 1400 670 1850" | /opt/bin/lamp
echo "pen rectangle 390 1480 650 1550" | /opt/bin/lamp  # Item 1
echo "pen rectangle 390 1590 650 1660" | /opt/bin/lamp  # Item 2

# Verify: Both main menu and submenu visible side-by-side?

# State 4: Back to Main Menu (clear submenu only)
echo "eraser fill 370 1400 670 1850 15" | /opt/bin/lamp

# Verify: Submenu gone, main menu still visible?

# State 5: Complete Exit
echo "eraser fill 50 1400 1350 1850 15" | /opt/bin/lamp

# Verify: All UI cleared?
```

**Success:** Each state transition works correctly, selective clearing works.

### Test 3: Component Preview

```bash
# Open menu
echo "pen rectangle 50 1400 350 1850" | /opt/bin/lamp

# Show component preview
echo "pen circle 900 1600 80" | /opt/bin/lamp

# Verify: Circle appears while menu still visible?

# User "moves" component with lasso tool
# (Manually test on device with actual lasso tool)

# Clear preview area
echo "eraser fill 700 1400 1350 1850 15" | /opt/bin/lamp

# Verify: Circle erased, menu still visible?
```

**Success:** Component can be previewed and cleared independently.

### Test 4: Rapid Transitions

```bash
# Rapid menu switching
for i in {1..5}; do
    echo "pen rectangle 50 1400 350 1850" | /opt/bin/lamp
    sleep 0.5
    echo "eraser fill 50 1400 350 1850 15" | /opt/bin/lamp
    sleep 0.3
done

# Verify: No visual artifacts? Smooth transitions?
```

**Success:** No lag, no leftover pixels, clean transitions.

### Test 5: Edge Cases

```bash
# Test 5a: Erase non-existent UI (should not error)
echo "eraser fill 50 1400 350 1850 15" | /opt/bin/lamp
# Success: No error, screen stays clean

# Test 5b: Multiple erases (idempotent)
echo "pen rectangle 200 200 400 400" | /opt/bin/lamp
echo "eraser fill 200 200 400 400 15" | /opt/bin/lamp
echo "eraser fill 200 200 400 400 15" | /opt/bin/lamp  # Second erase
# Success: No error, no side effects

# Test 5c: Overlapping UI regions
echo "pen rectangle 100 1400 400 1850" | /opt/bin/lamp
echo "pen rectangle 300 1400 600 1850" | /opt/bin/lamp
echo "eraser fill 100 1400 600 1850 15" | /opt/bin/lamp
# Success: Both rectangles erased completely
```

**Success:** All edge cases handled gracefully.

## Test Suite 3: User Interaction Patterns

### Test 6: Complete User Flow

Simulate a real user session:

```bash
# 1. User opens GUI
echo "pen rectangle 50 1400 350 1850" | /opt/bin/lamp
echo "pen rectangle 70 1480 330 1560" | /opt/bin/lamp
sleep 1

# 2. User selects "Power" category
echo "pen rectangle 370 1400 670 1850" | /opt/bin/lamp
echo "pen rectangle 390 1480 650 1550" | /opt/bin/lamp
echo "pen rectangle 390 1590 650 1660" | /opt/bin/lamp
sleep 1

# 3. User selects "Battery" item
echo "pen circle 900 1600 60" | /opt/bin/lamp
echo "pen line 870 1570 870 1630" | /opt/bin/lamp  # Battery +
echo "pen line 930 1580 930 1620" | /opt/bin/lamp  # Battery -
sleep 2

# 4. User uses lasso tool to move battery to circuit
#    (Manual step - test with actual stylus)

# 5. User clears component preview
echo "eraser fill 700 1400 1350 1850 15" | /opt/bin/lamp
sleep 1

# 6. User goes back to main menu
echo "eraser fill 370 1400 670 1850 15" | /opt/bin/lamp
sleep 1

# 7. User selects different category
echo "pen rectangle 370 1400 670 1850" | /opt/bin/lamp
echo "pen rectangle 390 1480 650 1550" | /opt/bin/lamp
sleep 1

# 8. User exits completely
echo "eraser fill 50 1400 1350 1850 15" | /opt/bin/lamp
```

**Success:** Complete flow works smoothly, no errors, professional UX.

### Test 7: Navigation Patterns

```bash
# Forward navigation: Main -> Category -> Item
# Backward navigation: Item -> Category -> Main
# Jump navigation: Any state -> Main (exit)
# Re-entry: Closed -> Main -> Category

# All should work smoothly with proper clearing
```

## Test Suite 4: Performance & Stability

### Test 8: Stress Test

```bash
# Rapid state changes (50 iterations)
for i in {1..50}; do
    echo "pen rectangle $((50 + i*2)) 1400 350 1850" | /opt/bin/lamp
    echo "eraser fill $((50 + i*2)) 1400 350 1850 15" | /opt/bin/lamp
done

# Verify: System still responsive? No crashes?
```

**Success:** No slowdown, no memory issues, still responsive.

### Test 9: Large Area Clearing

```bash
# Clear entire screen
echo "eraser fill 0 0 1404 1872 20" | /opt/bin/lamp

# Verify: Completes in reasonable time (< 5 seconds)?
```

**Success:** Completes quickly, no timeout errors.

### Test 10: Memory Leak Test

```bash
# Long-running session (100 cycles)
for i in {1..100}; do
    echo "pen rectangle 100 1400 300 1600" | /opt/bin/lamp
    sleep 0.2
    echo "eraser fill 100 1400 300 1600 15" | /opt/bin/lamp
    sleep 0.2

    # Check memory every 25 iterations
    if [ $((i % 25)) -eq 0 ]; then
        echo "Cycle $i - checking memory..."
        free -h
    fi
done

# Verify: Memory usage stable? No gradual increase?
```

**Success:** Memory usage remains constant throughout.

## Test Suite 5: Visual Quality

### Test 11: Eraser Completeness

```bash
# Dense pattern
for y in $(seq 1400 20 1800); do
    echo "pen line 50 $y 350 $y" | /opt/bin/lamp
done

# Erase
echo "eraser fill 50 1400 350 1850 12" | /opt/bin/lamp

# Verify: All lines completely erased? No faint traces?
```

**Success:** Complete erasure, no visible remnants.

### Test 12: Eraser Spacing Test

```bash
# Draw grid
echo "pen rectangle 100 1400 500 1800" | /opt/bin/lamp

# Test different spacings
echo "eraser fill 100 1400 200 1800 30" | /opt/bin/lamp  # Wide (visible strokes)
sleep 2
echo "eraser fill 200 1400 300 1800 15" | /opt/bin/lamp  # Medium (clean)
sleep 2
echo "eraser fill 300 1400 400 1800 8" | /opt/bin/lamp   # Tight (very clean)
sleep 2
echo "eraser fill 400 1400 500 1800 5" | /opt/bin/lamp   # Very tight (overkill?)

# Verify: Which spacing gives best balance of speed vs cleanliness?
```

**Recommended:** spacing=15 for general use, spacing=10 for important areas.

## Checklist: GUI Functionality

### Core Features
- [ ] Menu opens correctly
- [ ] Menu closes/clears completely
- [ ] Categories can be selected
- [ ] Submenu appears correctly
- [ ] Component preview shows
- [ ] Back navigation works
- [ ] Exit clears everything
- [ ] Re-open after exit works

### Eraser Functionality
- [ ] Eraser line works
- [ ] Eraser rectangle works
- [ ] Eraser fill clears areas
- [ ] Eraser clear (dense) works
- [ ] No visual artifacts
- [ ] Complete erasure
- [ ] Fast enough for UX

### User Interactions
- [ ] Forward navigation smooth
- [ ] Backward navigation smooth
- [ ] State transitions clean
- [ ] No stuck states
- [ ] Error recovery works
- [ ] Multiple sessions work

### Performance
- [ ] No lag or slowdown
- [ ] No memory leaks
- [ ] Handles rapid changes
- [ ] Stable over time
- [ ] No crashes

### Integration
- [ ] Works with xochitl
- [ ] Lasso tool can select drawn elements
- [ ] Elements can be moved
- [ ] Elements can be copied
- [ ] Doesn't interfere with main drawing area

## Troubleshooting

### Issue: Eraser leaves traces

**Solution:** Reduce spacing value
```bash
# Instead of:
echo "eraser fill 100 100 500 500 20" | lamp

# Use:
echo "eraser fill 100 100 500 500 10" | lamp
```

### Issue: Eraser too slow

**Solution:** Increase spacing value
```bash
# Balance speed vs completeness
echo "eraser fill 100 100 500 500 15" | lamp  # Good balance
```

### Issue: Menu doesn't clear

**Check:** Coordinates match what was drawn
```bash
# Draw: 50 1400 350 1850
echo "pen rectangle 50 1400 350 1850" | lamp

# Must erase SAME coordinates (or larger)
echo "eraser fill 50 1400 350 1850 15" | lamp
```

### Issue: State confusion

**Reset:**
```bash
rm -f /tmp/gui_test_state /tmp/component_ui_state
echo "eraser fill 0 1400 1404 1872 15" | lamp
```

## Success Criteria Summary

Your dynamic GUI is fully functional if:

✅ All 13 automated tests pass
✅ All manual tests complete successfully
✅ No visual artifacts remain after clearing
✅ State transitions are smooth (< 1 second)
✅ Eraser clears completely (no traces)
✅ Performance is consistent over time
✅ User interactions feel natural
✅ System is stable (no crashes)

If all criteria met: **GUI is production-ready!** 🎉
