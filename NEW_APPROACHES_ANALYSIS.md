# rm2in2 Project: New Approaches Analysis

**Date:** December 5, 2025
**Status:** Strategic Re-evaluation with New Community Resources

---

## Executive Summary

After analyzing the newly added community repositories, **three distinct alternative approaches** have emerged that could solve the fundamental problems plaguing the pen injection method. The most promising is **rm2fb's direct framebuffer approach**, which bypasses the pen input system entirely.

---

## Problems with Current LD_PRELOAD Pen Injection Approach

### What We've Learned from Failed Attempts

The project history documents **three failed iterations** (v3, v4, rm2-claude) and the current attempt faces the same fundamental issues:

1. **Coordinate Transformation Hell**
   - Display: 1404×1872 portrait
   - Wacom sensor: 20966×15725 with 90° rotation + flip
   - Multiple attempts all failed due to transformation bugs
   - Circles become ovals, grids don't align, crosses render 3x

2. **Architecture Mismatch** (Critical Issue)
   - reMarkable was NOT designed for programmatic pen injection
   - Events must be triggered by actual screen taps to render
   - No automatic buffer flushing
   - No feedback mechanism (can't verify if drawing succeeded)
   - Race conditions between real pen and synthetic events

3. **Limited Feature Support**
   - No native support for layers, colors, brushes
   - Pressure and tilt may not work correctly
   - Curve sampling has precision issues
   - Quote from user: *"lots of bugs and calculations are not supported by rm2 architecture"*

4. **Version Fragility**
   - LD_PRELOAD is fragile across firmware updates
   - Internal event structures can change
   - Hooks might break with any update

### Why It Doesn't Work

The fundamental issue: **We're trying to fake pen input, but the system only renders when it detects actual physical pen events.**

The reMarkable architecture is:
```
Physical Pen → Wacom Digitizer → /dev/input/event1 → xochitl → Display Updates
```

Our injection happens at the digitizer level, but **xochitl doesn't trust synthetic events the same way**. It requires additional triggers (screen taps) to actually render the injected data.

---

## Three New Approaches from Community Repositories

### Approach 1: rm2fb - Direct Framebuffer Access ⭐ RECOMMENDED

**Repository:** `resources/repos/rM2-stuff/libs/rm2fb/`

#### What It Is

rm2fb is a **framebuffer shim layer** that uses LD_PRELOAD to hook into xochitl's display update functions, NOT the input system.

**Key Insight:** Instead of faking pen input, we draw directly to a framebuffer that rm2fb synchronizes with the screen.

#### Architecture

```
Your App → Shared Framebuffer → rm2fb (LD_PRELOAD) → xochitl Display Updates → Screen
```

Instead of:
```
Your App → Fake Pen Events → /dev/input/event1 → xochitl → Screen (❌ doesn't render)
```

#### How It Works

1. **Server Component** (`resources/repos/rM2-stuff/libs/rm2fb/Server.cpp`)
   - Runs as systemd service or standalone
   - Creates shared memory buffer (1404×1872 pixels)
   - Hooks xochitl's framebuffer update functions using LD_PRELOAD
   - Listens on UNIX socket for client connections

2. **Client Component** (`resources/repos/rM2-stuff/libs/rm2fb/Client.cpp`)
   - Your app connects to rm2fb via UNIX socket
   - Gets access to shared framebuffer memory
   - Draws directly to buffer using simple pixel operations
   - Sends update messages to trigger screen refresh

3. **No Coordinate Transformation Needed**
   - Direct 1404×1872 coordinate space
   - No rotation, no flipping, no scaling
   - What you draw is what you see

#### Advantages

✅ **No Coordinate Transformation** - Direct display coordinates
✅ **Automatic Rendering** - No need for screen taps, rm2fb handles updates
✅ **Version Stable** - Supports firmware 2.15 through 3.23+ (actively maintained)
✅ **Full Feature Access** - Can draw anything: pixels, lines, images, text
✅ **Proven Technology** - Used by multiple community apps (Yaft, Rocket, Tilem)
✅ **Active Development** - Last updated supports latest firmware
✅ **Feedback Available** - Can read back framebuffer to verify drawing
✅ **No Architecture Mismatch** - Works WITH the system, not against it

#### Disadvantages

⚠️ **Still requires LD_PRELOAD** - Needs root access and systemd integration
⚠️ **Not True Vector** - Raster drawing, not native .rm format
⚠️ **More Setup** - Need to run rm2fb server alongside your app
⚠️ **Shared Buffer Management** - Need to coordinate updates properly

#### Implementation Effort

**Estimated Complexity:** Medium

1. **Deploy rm2fb** (1-2 days)
   - Build rm2fb from rM2-stuff repo
   - Set up systemd service
   - Test basic framebuffer access

2. **Adapt Your Code** (3-5 days)
   - Replace pen event injection with framebuffer drawing
   - Implement drawing primitives (lines, curves, fills)
   - Add update region management

3. **Testing & Refinement** (2-3 days)
   - Verify all drawing operations work correctly
   - Test across different firmware versions
   - Optimize performance

**Total:** 1-2 weeks

#### Example Code Pattern

```c
// Connect to rm2fb
int sock = socket(AF_UNIX, SOCK_STREAM, 0);
connect(sock, "/var/run/rm2fb.sock");

// Get framebuffer pointer
uint16_t* fb = rm2fb_get_framebuffer(sock);

// Draw directly (no coordinate transformation!)
void draw_line(int x0, int y0, int x1, int y1) {
    // Bresenham's line algorithm
    // fb[y * 1404 + x] = color;
    // Direct pixel access!
}

// Trigger update
rm2fb_update(sock, x, y, width, height);
```

Compare to current pen injection:
```c
// Current approach - complex and fragile
void inject_pen_event(float display_x, float display_y) {
    // Complex transformation
    int sensor_x = transform_x(display_x, display_y);  // ❌ buggy
    int sensor_y = transform_y(display_x, display_y);  // ❌ buggy

    // Create synthetic event
    inject_event(sensor_x, sensor_y);

    // Hope it renders (❌ requires screen tap)
}
```

---

### Approach 2: rmkit - Native reMarkable App Framework

**Repository:** `resources/repos/rmkit/`

#### What It Is

rmkit is a **C++ development framework** for building native reMarkable applications with proper UI, input handling, and drawing APIs.

#### What It Offers

- **UI Framework** - Declarative UI based on Flutter architecture
- **Input Handling** - Proper pen/touch event management
- **Drawing APIs** - Native drawing primitives with e-ink optimization
- **Framebuffer Access** - Built-in framebuffer management
- **Example Apps** - Working examples (drawing_demo, minesweeper, calculator)

#### Example: Drawing Demo

From `resources/repos/rmkit/src/drawing_demo/main.cpy`:

```cpp
class Note: public ui::Widget:
  framebuffer::FileFB *vfb

  void on_mouse_move(input::SynMotionEvent &ev):
    if prevx != -1:
      vfb->draw_line(prevx, prevy, ev.x, ev.y, 1, BLACK)
      self.dirty = 1
    prevx = ev.x
    prevy = ev.y
```

**Key Point:** Direct drawing with proper event handling - no coordinate transformation issues!

#### Advantages

✅ **Native Platform Integration** - Works perfectly with reMarkable OS
✅ **Full Feature Access** - Proper UI, input, drawing, everything
✅ **No Coordinate Issues** - Framework handles all transformations
✅ **Example Code Available** - Multiple working apps to learn from
✅ **Active Community** - Well-documented, maintained project

#### Disadvantages

❌ **Not a Client-Server Model** - Can't control from external PC
❌ **Native App Required** - Need to build full reMarkable app
❌ **C++ Development** - Requires cross-compilation, toolchain setup
❌ **Different Goal** - This is for building standalone apps, not remote drawing

#### Use Case

This approach is ideal if you want to create a **native reMarkable app** that runs ON the device. Not suitable for remote control from a PC.

---

### Approach 3: .rm File Format Generation (Previously Analyzed)

**Tools:** `rmscene` Python library

This approach was thoroughly analyzed in `ANALYSIS_AND_ALTERNATIVES.md`.

#### Summary

Generate native `.rm` files programmatically, upload via rMAPI or cloud sync.

#### Advantages

✅ **Version Stable** - Format documented and stable since firmware 3.0
✅ **Full Feature Support** - Layers, colors, brushes, text
✅ **No Root Required** - Works via cloud sync
✅ **Simple Coordinates** - Direct 1404×1872 space
✅ **Community Tools Available** - rmscene library handles complexity

#### Disadvantages

❌ **Not Real-Time** - Must create file, sync, then view
❌ **Sync Delay** - Cloud sync can take seconds to minutes
❌ **File Management** - Need UUIDs, metadata, thumbnails
❌ **No Interactive Feedback** - Can't see drawing as it happens

#### Use Case

Perfect for **batch processing** or **non-interactive scenarios**:
- Convert SVG files to reMarkable notebooks
- Generate technical drawings programmatically
- Batch import text as handwriting
- Create template notebooks

---

## Comparison Matrix

| Feature | Pen Injection (Current) | rm2fb (Framebuffer) | rmkit (Native App) | .rm File Generation |
|---------|------------------------|---------------------|-------------------|---------------------|
| **Real-time** | ✅ Yes (if it worked) | ✅ Yes | ✅ Yes | ❌ No |
| **Coordinate System** | ❌ Complex, buggy | ✅ Simple (1404×1872) | ✅ Framework handles | ✅ Simple (1404×1872) |
| **Rendering Reliability** | ❌ Requires taps | ✅ Automatic | ✅ Automatic | ✅ Native format |
| **Version Stability** | ❌ Fragile | ✅ Maintained (2.15-3.23+) | ✅ Active framework | ✅ Stable format |
| **Feature Support** | ❌ Limited | ⚠️ Raster only | ✅ Full native | ✅ Full native |
| **Root Required** | ✅ Yes | ✅ Yes | ⚠️ For deployment | ❌ No |
| **Remote Control** | ✅ Yes | ✅ Yes | ❌ No | ⚠️ Via cloud |
| **Complexity** | ⚠️ High | ⚠️ Medium | ⚠️ High | ⚠️ Medium |
| **Working Examples** | ❌ Multiple failures | ✅ Yaft, Rocket, Tilem | ✅ Multiple apps | ✅ rmscene, Drawj2d |
| **Community Support** | ❌ Minimal | ✅ Active | ✅ Active | ✅ Active |
| **Architecture Alignment** | ❌ Fighting system | ✅ Works with system | ✅ Native | ✅ Native |

---

## Recommended Path Forward

### 🎯 Primary Recommendation: Pivot to rm2fb

**Why:** rm2fb solves ALL the fundamental problems with pen injection:
- ✅ No coordinate transformation issues
- ✅ No "tap to render" requirement
- ✅ Version stable and actively maintained
- ✅ Proven by multiple working apps
- ✅ Works WITH the system architecture, not against it

**Strategy:**

1. **Proof of Concept (Week 1)**
   - Build and deploy rm2fb from rM2-stuff repo
   - Create simple test client that draws basic shapes
   - Verify framebuffer access and updates work correctly

2. **Core Drawing Engine (Week 2-3)**
   - Implement drawing primitives using framebuffer API
   - Port existing coordinate testing code (should be trivial now!)
   - Add stroke rendering with proper antialiasing

3. **Feature Parity (Week 4-5)**
   - Implement all desired features (SVG import, text rendering, etc.)
   - Add command interface (keep FIFO system or switch to socket)
   - Test across firmware versions

4. **Polish & Deploy (Week 6)**
   - Optimize performance
   - Create deployment scripts
   - Write documentation

### 🎯 Secondary Recommendation: Hybrid Approach

**Combine rm2fb (real-time) + .rm files (production)**

1. **Use rm2fb for Development & Testing**
   - Immediate visual feedback
   - Quick iteration on drawing algorithms
   - Interactive testing

2. **Use .rm File Generation for Production**
   - Convert tested drawings to native .rm format
   - Upload via rMAPI for proper archiving
   - Full feature support (layers, colors, etc.)
   - No need to keep rm2fb running long-term

This gives you the best of both worlds!

### 🎯 Alternative: Pure .rm File Approach

If real-time display isn't critical, skip rm2fb entirely and focus on `.rm` file generation:

1. **Prototype with rmscene** (Week 1-2)
   - Install rmscene library: `pip install rmscene`
   - Create simple test files
   - Verify format across firmware versions

2. **Build Conversion Tools** (Week 3-4)
   - SVG → .rm converter
   - Text → .rm with fonts
   - Coordinate systems (trivial with .rm format!)

3. **Delivery System** (Week 5-6)
   - rMAPI integration for cloud upload
   - Optional: rmfakecloud for local testing
   - Web interface for generation

---

## Why rm2fb Is Better Than Pen Injection

### Technical Comparison

| Aspect | Pen Injection | rm2fb Framebuffer |
|--------|--------------|-------------------|
| **Hook Point** | `/dev/input/event1` (input) | xochitl display functions |
| **Coordinate Space** | 20966×15725 rotated | 1404×1872 direct |
| **Rendering** | Requires physical tap | Automatic via display hook |
| **Feedback** | None (blind injection) | Can read framebuffer |
| **Trust Model** | Synthetic events (untrusted) | Display buffer (trusted) |
| **Firmware Coupling** | Input event structure | Display API (more stable) |
| **Working Examples** | 0 successful (4 failed) | 3+ active apps using it |

### Architecture Alignment

**Pen Injection tries to:**
```
Fake Input → Hope System Renders
```

**rm2fb does:**
```
Draw → Update Display (Direct)
```

rm2fb works WITH the reMarkable architecture instead of fighting against it.

---

## Implementation Plan: rm2fb Approach

### Phase 1: Setup & Proof of Concept (Week 1)

**Goal:** Get rm2fb running and verify basic functionality

1. **Build rm2fb** (Day 1-2)
   ```bash
   cd resources/repos/rM2-stuff
   cmake --preset dev-toltec
   cmake --build build/dev --target rm2fb
   ```

2. **Deploy to Device** (Day 2-3)
   ```bash
   # Copy to reMarkable
   scp build/dev/libs/rm2fb/librm2fb.so.1 root@10.11.99.1:/opt/lib/

   # Set up systemd service
   # (Use existing deployment scripts as reference)
   ```

3. **Test Basic Access** (Day 3-5)
   - Write minimal C client that connects to rm2fb
   - Draw a single pixel
   - Draw a line
   - Verify display updates work
   - Test update regions

**Success Criteria:**
- ✅ rm2fb server runs on device
- ✅ Can connect from client
- ✅ Can draw pixels and lines
- ✅ Screen updates automatically (no taps needed!)
- ✅ Coordinates are correct (1404×1872 direct)

### Phase 2: Core Drawing Engine (Week 2-3)

**Goal:** Implement all drawing primitives

1. **Drawing Library** (Day 6-10)
   - Line drawing (Bresenham's algorithm)
   - Circle/ellipse (midpoint algorithm)
   - Bezier curves (De Casteljau's algorithm)
   - Polygon fill (scanline algorithm)
   - Text rendering (freetype integration?)

2. **Update Optimization** (Day 11-12)
   - Dirty rectangle tracking
   - Batch updates for multiple strokes
   - Minimize screen refreshes (e-ink optimization)

3. **Testing Suite** (Day 13-15)
   - Port existing test patterns (corners, cross, grid, circle)
   - Should work immediately with correct coordinates!
   - Add new tests for curves, text, etc.

**Success Criteria:**
- ✅ All test patterns render correctly
- ✅ No coordinate transformation bugs
- ✅ Circles are circular, grids align
- ✅ Performance acceptable for real-time drawing

### Phase 3: Feature Implementation (Week 4-5)

**Goal:** Match current project goals

1. **SVG Import** (Day 16-20)
   - Parse SVG paths
   - Convert to framebuffer drawing operations
   - Handle transforms, viewBox, etc.

2. **Text Rendering** (Day 21-23)
   - Font loading (existing Hershey fonts?)
   - Text to strokes conversion
   - Layout and positioning

3. **Command Interface** (Day 24-25)
   - Keep existing FIFO system or migrate to sockets
   - Command parsing
   - Response/status reporting

**Success Criteria:**
- ✅ Can render SVG files on screen
- ✅ Text rendering works
- ✅ Command interface functional
- ✅ Feature parity with original project goals

### Phase 4: Polish & Deploy (Week 6)

**Goal:** Production-ready system

1. **Error Handling** (Day 26-27)
   - Graceful failures
   - Connection recovery
   - Logging and diagnostics

2. **Documentation** (Day 28-29)
   - Update README
   - Deployment guide
   - API documentation

3. **Testing & Validation** (Day 30)
   - Test on actual device
   - Verify across firmware versions
   - Performance testing

**Success Criteria:**
- ✅ System is stable and reliable
- ✅ Documentation complete
- ✅ Ready for use

---

## Migration Path from Current Code

### What to Keep

✅ **Command interface** - FIFO system works fine
✅ **Testing framework** - Test patterns are great
✅ **Deployment scripts** - Can adapt for rm2fb
✅ **Project structure** - Client/server architecture is sound

### What to Replace

❌ **inject.c** - Entire pen injection system
❌ **Coordinate transformation** - No longer needed!
❌ **Event synthesis** - Use framebuffer drawing instead
❌ **Manual tap requirement** - rm2fb handles rendering

### Code Reuse Estimate

- **Keep:** ~40% (structure, testing, deployment)
- **Adapt:** ~30% (command interface, utilities)
- **Rewrite:** ~30% (core drawing engine)

**Key Insight:** The hard parts (coordinate transformation, rendering triggers) go away completely!

---

## Resources for Implementation

### rm2fb Documentation

- **Main README:** `resources/repos/rM2-stuff/README.md`
- **rm2fb README:** `resources/repos/rM2-stuff/libs/rm2fb/README.md`
- **Server Code:** `resources/repos/rM2-stuff/libs/rm2fb/Server.cpp`
- **Client Code:** `resources/repos/rM2-stuff/libs/rm2fb/Client.cpp`

### Example Apps Using rm2fb

1. **Yaft Terminal** - `resources/repos/rM2-stuff/apps/yaft/`
   - Text rendering
   - Framebuffer updates

2. **Rocket Launcher** - `resources/repos/rM2-stuff/apps/rocket/`
   - UI rendering
   - Interactive graphics

3. **Tilem Calculator** - `resources/repos/rM2-stuff/apps/tilem/`
   - Complex graphics
   - Real-time updates

### rmkit Drawing Examples

- **Drawing Demo:** `resources/repos/rmkit/src/drawing_demo/main.cpy`
  - Shows proper drawing patterns
  - Input event handling
  - Dirty region management

### Community Resources

- **rM2-stuff GitHub:** https://github.com/timower/rM2-stuff
- **rmkit GitHub:** https://github.com/rmkit-dev/rmkit
- **reMarkable Community:** https://github.com/reHackable/awesome-reMarkable

---

## Questions to Consider

### 1. Do you need real-time display?

- **YES** → Use rm2fb approach (recommended)
- **NO** → Use .rm file generation approach (simpler, no root)

### 2. Do you need remote control from PC?

- **YES** → rm2fb or .rm files with rMAPI
- **NO** → Could build native app with rmkit

### 3. What firmware versions must you support?

- **2.15-3.23** → rm2fb is proven
- **3.24+ beta** → May need testing/updates
- **Future versions** → .rm files most stable

### 4. What features are essential?

- **Just drawing** → rm2fb sufficient
- **Layers, colors, annotations** → Consider .rm files
- **Both** → Hybrid approach

---

## Conclusion

The newly added community repositories have revealed a **better path forward**. The pen injection approach has fundamental architectural problems that have caused four consecutive failed attempts. It's time to pivot.

**rm2fb provides the solution we've been looking for:**
- ✅ Direct framebuffer access (no coordinate transformation)
- ✅ Automatic rendering (no tap requirement)
- ✅ Proven technology (multiple working apps)
- ✅ Active maintenance (supports latest firmware)
- ✅ Works WITH the system, not against it

**Estimated timeline to working prototype:** 2-3 weeks
**Estimated timeline to production-ready:** 6 weeks

The question isn't "should we pivot?" but "how quickly can we get started?"

---

## Next Steps

1. **Decision:** Choose approach (rm2fb recommended)
2. **Setup:** Build and deploy rm2fb to device
3. **Prototype:** Create minimal drawing client
4. **Validate:** Verify approach solves coordinate/rendering issues
5. **Implement:** Build full feature set
6. **Deploy:** Package and document

Ready to move forward?
