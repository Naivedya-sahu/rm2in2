# RM2 Repository Compatibility Analysis

**Firmware:** 3.24.0.147 (Beta)  
**Date:** December 4, 2024

---

## Executive Summary

**Direct Write Method:**
- ✅ lamp works (input injection only, no rm2fb needed)
- ✅ genie should work (gesture launcher, input-only)
- ❌ harmony won't work (requires rm2fb, max firmware 3.20)
- ❌ Most rmkit GUI apps won't work (require rm2fb)
- ✅ Sudoku possible via direct UI injection (no rm2fb needed)

**rm2fb Status:** Not compatible with firmware 3.24.x

---

## Repository Analysis

### 1. rmkit (lamp, genie, harmony, etc.)

**Location:** `resources/repos/rmkit`

#### lamp ✅ WORKS

**What it does:** Input event injection (pen/touch)  
**Dependencies:** `/dev/input/eventX` access only  
**rm2fb required:** NO  

**Why it works:**
- Pure input injection
- No framebuffer operations
- Just opens `/dev/input/event1` and writes events
- You already tested this - it works on 3.24.0.147

**Compatibility:** ✅ ALL firmware versions

#### genie ✅ SHOULD WORK

**What it does:** Gesture-based launcher  
**Dependencies:** Input devices only  
**rm2fb required:** NO  

**How it works:**
```cpp
// From genie source
- Reads touch gestures from /dev/input/event0
- Matches against config file patterns
- Executes configured commands
```

**Config example:**
```
# Swipe from left edge -> Launch xochitl
gesture: swipe_right edge:left
action: systemctl restart xochitl

# Three finger tap -> Launch lamp
gesture: tap fingers:3
action: lamp < /opt/circuit.in
```

**Why it should work:**
- Input reading only (no display)
- No rm2fb dependency
- Works alongside xochitl

**Test plan:**
```bash
# 1. Compile genie for RM2
# 2. Deploy to /opt/genie
# 3. Create config file
# 4. Run: /opt/genie /opt/genie.conf
```

**Compatibility:** ✅ Likely works on 3.24.x

#### harmony ❌ WON'T WORK

**What it does:** Low-latency drawing app with procedural brushes  
**Dependencies:** rm2fb framebuffer library  
**rm2fb required:** YES  

**From README:**
> NOTE: for remarkable2 support, [rm2fb](https://github.com/ddvk/remarkable2-framebuffer) is required

**rm2fb compatibility:**
- ✅ 2.15.x
- ✅ 3.5.x  
- ✅ 3.8.x
- ✅ 3.20.x
- ❌ 3.22.x+
- ❌ 3.24.x (your firmware)

**Why it won't work:**
```cpp
// harmony needs to:
1. Open framebuffer for display
2. Use rm2fb to hook xochitl's display updates
3. Draw procedural brushes with special effects
4. Cannot work without rm2fb on RM2
```

**Compatibility:** ❌ NOT compatible with 3.24.x

#### Other rmkit apps:

**mines** (minesweeper) - ❌ Needs rm2fb  
**iago** (shape overlay) - ❌ Needs rm2fb  
**remux** (app switcher) - ❌ Needs rm2fb  
**wordlet** (wordle clone) - ❌ Needs rm2fb  
**dumbskull** (card game) - ❌ Needs rm2fb  

---

### 2. rM2-stuff (rm2fb, yaft, tilem, rocket)

**Location:** `resources/repos/rM2-stuff`

#### rm2fb ❌ NOT COMPATIBLE

**Supported versions:**
```cpp
Version2.15.cpp  // Firmware 2.15.x
Version3.5.cpp   // Firmware 3.5.x
Version3.8.cpp   // Firmware 3.8.x
Version3.20.cpp  // Firmware 3.20.x
// NO Version3.24.cpp
```

**From rm2fb README:**
> Custom implementation for reMarkable 2 framebuffer
> Lower level hooking, removing the Qt dependence
> Supports less but newer xochitl versions

**Maximum supported:** 3.22 (beta support)  
**Your firmware:** 3.24.0.147  
**Status:** ❌ NOT SUPPORTED

#### yaft (terminal) ❌ WON'T WORK

**What it does:** Terminal emulator with on-screen keyboard  
**Dependencies:** rMlib UI framework → rm2fb  
**Compatibility:** ❌ Needs rm2fb

#### tilem (TI calculator) ❌ WON'T WORK

**What it does:** TI-84+ calculator emulator  
**Dependencies:** rMlib UI framework → rm2fb  
**Compatibility:** ❌ Needs rm2fb

#### rocket (launcher) ❌ WON'T WORK

**What it does:** Power button app launcher  
**Dependencies:** rMlib UI framework → rm2fb  
**Compatibility:** ❌ Needs rm2fb

---

### 3. pipes-and-paper-enhanced

**Location:** `resources/repos/pipes-and-paper-enhanced`

**What it does:** Browser-based screen sharing  
**Dependencies:** SSH + `/dev/input/event0` read access  
**rm2fb required:** NO  

**How it works:**
```python
# On PC:
python main.py --ssh-hostname rm2

# Streams pen input to browser in real-time
# NO display manipulation
# Just reads input events and forwards via websocket
```

**Compatibility:** ✅ Should work on 3.24.x

---

### 4. rm-version-switcher

**What it does:** Switch between installed firmware versions  
**Dependencies:** Boot partition access  
**Compatibility:** ✅ Works up to 3.24.x (tested)

**Risk:** May violate beta firmware EULA

---

## rm2fb Testing Strategy

### Quick Test (5 minutes)

**Goal:** Definitively determine if rm2fb CAN work on 3.24.0.147

```bash
#!/bin/bash
# test-rm2fb.sh

# Try to detect framebuffer device
echo "=== Checking framebuffer devices ==="
ssh root@10.11.99.1 "ls -l /dev/fb*"

# Check if rm2fb client library exists
ssh root@10.11.99.1 "ls -l /opt/lib/librm2fb_client.so*"

# Try to open framebuffer
ssh root@10.11.99.1 "cat > /tmp/fb_test.c << 'EOF'
#include <fcntl.h>
#include <stdio.h>
#include <sys/ioctl.h>
#include <linux/fb.h>

int main() {
    int fd = open(\"/dev/fb0\", O_RDWR);
    if (fd < 0) {
        printf(\"Cannot open /dev/fb0\\n\");
        return 1;
    }
    
    struct fb_var_screeninfo vinfo;
    if (ioctl(fd, FBIOGET_VSCREENINFO, &vinfo) < 0) {
        printf(\"Cannot get screen info\\n\");
        return 1;
    }
    
    printf(\"Framebuffer: %dx%d, %d bpp\\n\", 
           vinfo.xres, vinfo.yres, vinfo.bits_per_pixel);
    close(fd);
    return 0;
}
EOF
"

# Compile and run
ssh root@10.11.99.1 "gcc /tmp/fb_test.c -o /tmp/fb_test && /tmp/fb_test"
```

**Expected results:**
- ✅ If framebuffer accessible → rm2fb MIGHT work (need to compile for 3.24)
- ❌ If access denied / device missing → rm2fb CAN'T work

---

## Sudoku Implementation Options

### Option 1: Direct Injection (Like lamp) ✅ FEASIBLE

**Architecture:**
```
Sudoku Game Logic (PC or RM2)
    ↓
Generate grid + UI as pen commands
    ↓
lamp-style direct write to /dev/input/event1
    ↓
Renders in xochitl notebook
```

**Advantages:**
- ✅ No rm2fb needed
- ✅ Works on your firmware
- ✅ Uses proven lamp approach
- ✅ Can use adaptive interpolation

**Disadvantages:**
- ❌ Not interactive (read-only rendering)
- ❌ Needs separate input mechanism
- ❌ Can't detect user pen input in game

**Implementation:**
```python
# sudoku_to_lamp.py

def generate_sudoku_commands(puzzle, cell_size=100):
    """Generate lamp commands for sudoku grid"""
    commands = []
    
    # Draw grid
    for i in range(10):
        # Horizontal lines
        y = 200 + i * cell_size
        thick = 4 if i % 3 == 0 else 2
        commands.append(f"pen line 200 {y} 1100 {y}")
        
        # Vertical lines
        x = 200 + i * cell_size
        commands.append(f"pen line {x} 200 {x} 1100")
    
    # Draw numbers
    for row in range(9):
        for col in range(9):
            if puzzle[row][col] != 0:
                x = 200 + col * cell_size + 40
                y = 200 + row * cell_size + 60
                draw_number(commands, puzzle[row][col], x, y)
    
    return commands
```

**Deploy:**
```bash
python sudoku_to_lamp.py puzzle.txt | ssh root@10.11.99.1 lamp
```

### Option 2: Interactive via Touch Detection ✅ BETTER

**Architecture:**
```
Game State (on RM2 or PC)
    ↓
Render current state via lamp
    ↓
Monitor /dev/input/event1 for pen taps
    ↓
Detect which cell was tapped
    ↓
Update game state
    ↓
Re-render
```

**Daemon structure:**
```cpp
// sudoku_daemon.c

void render_sudoku_state() {
    // Use lamp functions to draw grid + numbers
}

void handle_pen_event(int x, int y) {
    // Calculate which cell was tapped
    int row = (y - 200) / 100;
    int col = (x - 200) / 100;
    
    if (row >= 0 && row < 9 && col >= 0 && col < 9) {
        // Update game state
        // Re-render
    }
}

int main() {
    int pen_fd = open("/dev/input/event1", O_RDWR);
    
    render_sudoku_state();
    
    while (1) {
        struct input_event ev;
        read(pen_fd, &ev, sizeof(ev));
        
        if (ev.type == EV_KEY && ev.code == BTN_TOUCH && ev.value == 1) {
            // Pen down event
            // Read coordinates from next ABS events
            handle_pen_event(pen_x, pen_y);
        }
    }
}
```

**Advantages:**
- ✅ Fully interactive
- ✅ No rm2fb needed
- ✅ Works on 3.24.x
- ✅ Can implement complete game logic

**Disadvantages:**
- ❌ More complex than Option 1
- ❌ Need number selection UI
- ❌ Requires game state management

### Option 3: Hybrid - Terminal + Visualization ✅ SIMPLEST

**Use yaft terminal for game logic, lamp for pretty display:**

```bash
# Terminal shows game state (text)
# lamp draws pretty visual grid
# Play via SSH commands
```

**But:** yaft needs rm2fb, so won't work on 3.24.x

### Option 4: Pure Terminal (No Graphics) ✅ WORKS NOW

**ASCII sudoku in SSH session:**
```
ssh root@10.11.99.1
python3 sudoku_cli.py
```

**No rm2fb needed, no graphics, pure text interface**

---

## Recommended Path Forward

### What You Can Use Now:

1. **lamp** - ✅ Works, tested
2. **genie** - ✅ Should work, test it
3. **pipes-and-paper** - ✅ Should work for screen sharing
4. **rm-version-switcher** - ✅ Works (if needed)

### What You CAN'T Use:

1. **harmony** - ❌ Needs rm2fb → 3.20 max
2. **yaft** - ❌ Needs rm2fb
3. **tilem** - ❌ Needs rm2fb  
4. **rocket** - ❌ Needs rm2fb
5. **All rmkit GUI apps** - ❌ Need rm2fb

### Sudoku Recommendation:

**Option 2: Interactive Direct Injection**

Build a sudoku daemon that:
1. Uses lamp's coordinate transformation
2. Renders grid via direct `/dev/input/event1` write
3. Monitors same device for pen taps
4. Implements full game logic
5. NO rm2fb, NO xochitl manipulation

**Estimated effort:** 6-8 hours

---

## Testing Checklist

```bash
# 1. Test lamp (already done ✓)
echo "pen circle 700 900 200 50" | ssh root@10.11.99.1 lamp

# 2. Test genie
scp genie root@10.11.99.1:/opt/
ssh root@10.11.99.1 /opt/genie /opt/genie.conf

# 3. Test framebuffer access
ssh root@10.11.99.1 "./fb_test"

# 4. Verify rm2fb NOT installed
ssh root@10.11.99.1 "ls -l /opt/lib/librm2fb*"

# 5. Test pipes-and-paper
python main.py --ssh-hostname rm2
# Open browser to localhost:8001
```

---

## Conclusion

**Can use:**
- ✅ lamp (tested working)
- ✅ genie (should work, test it)
- ✅ Direct injection approach (no rm2fb)
- ✅ Sudoku via Option 2 (interactive injection)

**Cannot use:**
- ❌ rm2fb (not compatible with 3.24.x)
- ❌ Any rmkit GUI apps (harmony, iago, etc.)
- ❌ rM2-stuff apps (yaft, tilem, rocket)

**Sudoku strategy:**
Build custom daemon using lamp's proven injection method + pen tap detection. No rm2fb. No notebook manipulation. Pure input injection.

---

## Firmware Update Decision

**Current:** 3.24.0.147 (working with direct injection)  
**Available:** 3.24.0.179

**Recommendation:** STAY on 0.147

**Reasoning:**
1. Direct injection proven working
2. rm2fb won't work either way (both > 3.22)
3. Update adds unknown variables
4. Develop production system first
5. Update only if 0.179 has critical features you need

**Alternative:** Use rm-version-switcher for dual boot (risky on beta)
