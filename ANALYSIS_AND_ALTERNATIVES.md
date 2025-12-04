# rm2in2 Project Analysis: Current State & Alternative Approaches

**Date:** 2025-12-04
**Status:** Re-evaluation Phase

## Executive Summary

The pen injection approach (LD_PRELOAD hooking) works technically but has fundamental architectural limitations. The .rm file format approach may be more suitable for reliable, version-stable programmatic drawing.

---

## Current Approach: Pen Input Injection

### What We Built

**Architecture:**
- LD_PRELOAD hook on `/dev/input/event1` (Wacom digitizer)
- FIFO-based command system (`/tmp/rm2_inject`)
- Real-time event injection into `xochitl` process

**Achievements:**
- ✅ Successfully hooks into input system
- ✅ Can inject synthetic pen events
- ✅ Real-time drawing capability
- ✅ Verified coordinate transformation (from captured pen data)

### Fundamental Problems Discovered

#### 1. **Coordinate System Complexity**
- Multiple failed attempts (v3, v4, rm2-claude all had issues)
- Required extensive empirical testing to find correct transformation
- Display (1404×1872) → Sensor (20966×15725) with 90° rotation + flip
- Your testing showed: circles become ovals, grid/corners don't render, cross appears 3x

#### 2. **Architecture Mismatch**
The RM2 was NOT designed for programmatic pen injection:
- Events must be triggered by actual screen taps to render
- Buffer management issues (events queue but don't flush automatically)
- No feedback mechanism (can't verify if drawing succeeded)
- Race conditions between real pen input and synthetic events

#### 3. **Calculations Not Supported**
Quote from you: *"lots of bugs and calculations are not supported by rm2 architecture"*

This suggests:
- Pressure, tilt, or other pen attributes may not work as expected
- Curve sampling/interpolation may have precision issues
- No API for features like layers, undo, or drawing modes

#### 4. **Version Stability**
- LD_PRELOAD approach is fragile across OS updates
- Internal event structure could change
- Hooks might break with firmware updates

---

## Alternative Approach: .rm File Format

### What Is It?

The `.rm` file format is reMarkable's native vector notebook format:

**Format Evolution:**
- **Version 3-5**: Binary format with stroke data (older tablets)
- **Version 6**: Current format (firmware 3.0+, late 2022)
  - Supports drawn lines AND text
  - Proper vector representation
  - Color support (as of Sept 2024 for Paper Pro)

### File Structure (Version 6)

```
.rm file (binary)
├── Header (43 bytes)
│   └── "reMarkable .lines file, version=6"
├── Layer Count (int32)
└── For each layer:
    ├── Line Count (int32)
    └── For each line:
        ├── Brush type (int32)
        ├── Line color (int32)
        ├── Base brush size (float32)
        ├── Point count (int32)
        └── For each point:
            ├── X coordinate (float32, 0.0-1404.0)
            ├── Y coordinate (float32, 0.0-1872.0)
            ├── Speed (float32)
            ├── Direction (float32)
            ├── Width (float32)
            └── Pressure (float32)
```

### Advantages of .rm File Approach

✅ **Native Format** - No fighting against the system
✅ **Version Stable** - Format is documented and stable
✅ **Full Feature Support** - Layers, colors, brushes all supported
✅ **Batch Processing** - Create entire notebooks at once
✅ **Coordinates Simple** - Direct 1404×1872 space (no transformation!)
✅ **Verification** - Can read back and verify what was created
✅ **No Root Required** - Works via cloud sync or file transfer

### Disadvantages

❌ **Not Real-Time** - Must create file, then sync/transfer
❌ **Requires Sync** - Need rMAPI or rmfakecloud or manual transfer
❌ **More Complex Format** - Binary format more complex than text commands
❌ **File Management** - Need to handle UUIDs, metadata, thumbnails

---

## Community Tools & Solutions

### 1. **rMAPI** - Cloud API Access
[GitHub: juruen/rmapi](https://github.com/juruen/rmapi)

**Capabilities:**
- Upload/download files to/from reMarkable Cloud
- Shell or programmatic (Go SDK) access
- Can inject .rm files into cloud → sync to tablet

**Use Case:** Create .rm file locally, upload via rMAPI

### 2. **rmfakecloud** - Self-Hosted Cloud
[GitHub: ddvk/rmfakecloud](https://github.com/ddvk/rmfakecloud)

**Capabilities:**
- Host your own cloud sync server
- Full control over synced content
- Supports firmware up to 3.22.0

**Use Case:** Local cloud for development/testing

### 3. **rmscene** - Python Library for v6 Format
[GitHub: ricklupton/rmscene](https://github.com/ricklupton/rmscene)

**Capabilities:**
- Read/write v6 .rm files
- Python-based, easy to integrate
- Handles complex format details

**Use Case:** Programmatically generate .rm files in Python

### 4. **Drawj2d** - Technical Drawing Tool
[Sourceforge: drawj2d](https://sourceforge.net/p/drawj2d/wiki/reMarkable/)

**Capabilities:**
- Create technical line drawings
- Output as reMarkable notebook pages
- Updated Sept 2024 for color support

**Use Case:** Reference for .rm file generation

### 5. **awesome-reMarkable**
[GitHub: reHackable/awesome-reMarkable](https://github.com/reHackable/awesome-reMarkable)

**What:** Curated list of ALL community tools
**Value:** Central hub for discovering solutions

---

## Comparison Matrix

| Feature | Pen Injection | .rm File Format |
|---------|--------------|-----------------|
| **Real-time** | ✅ Yes | ❌ No (requires sync) |
| **Reliability** | ❌ Fragile | ✅ Stable |
| **Coordinate System** | ❌ Complex transform | ✅ Simple (1404×1872) |
| **Version Stability** | ❌ May break | ✅ Documented format |
| **Feature Support** | ❌ Limited | ✅ Full (layers, colors, etc) |
| **Root Access** | ⚠️ Required | ❌ Not required |
| **Implementation** | ⚠️ Complex (C, LD_PRELOAD) | ⚠️ Complex (binary format) |
| **Testing** | ❌ Difficult | ✅ Can verify offline |
| **Community Support** | ❌ Minimal | ✅ Multiple tools exist |

---

## Past Development Issues (From Previous Versions)

### Common Problems Across All Versions

1. **Coordinate Transformations** (ALL versions)
   - v3: Mirroring/rotation bugs
   - v4: "Fixed" but still had issues
   - rm2-claude: Claimed working but failed on curves
   - Current: Required empirical pen capture to get right

2. **Over-Engineering** (v3 especially)
   - Attempted custom web-based glyph editors
   - Port binding issues
   - Node selection bugs
   - Eventually abandoned for Inkscape

3. **Precision Issues**
   - Decimal coordinates causing problems
   - Required `int(round())` everywhere
   - Float precision loss in transformations

4. **Architecture Mismatch** (Current discovery)
   - System not designed for synthetic events
   - Requires manual screen taps to render
   - No proper event flushing

---

## Recommended Path Forward

### Option A: Hybrid Approach (Recommended)

**Use Both Methods for Different Use Cases:**

1. **For Development/Testing:**
   - Keep pen injection for debugging coordinates
   - Immediate visual feedback
   - Good for prototyping

2. **For Production:**
   - Generate .rm files directly
   - Use rMAPI or rmfakecloud for delivery
   - More reliable, feature-complete

### Option B: Full .rm File Approach

**Abandon pen injection, focus on .rm generation:**

**Phase 1:** Research & Prototype
- Use `rmscene` Python library
- Create simple test .rm files
- Verify format across OS versions

**Phase 2:** Conversion Tools
- SVG → .rm converter
- Text → .rm with fonts
- PNG/bitmap → .rm tracing

**Phase 3:** Delivery System
- rMAPI integration
- Optional: rmfakecloud for local testing
- Web interface for generation

### Option C: Continue Pen Injection (Not Recommended)

Only if real-time capability is ESSENTIAL and you can accept:
- Ongoing maintenance for coordinate issues
- Limited feature support
- Fragility across updates
- Manual screen taps required

---

## Technical Requirements for .rm Approach

### Libraries Needed
```python
rmscene  # Python library for v6 format
Pillow   # Image processing if doing bitmap tracing
svgpathtools  # SVG path parsing
```

### Implementation Steps
1. **Parse input** (SVG, text, or bitmap)
2. **Convert to strokes** (list of points with attributes)
3. **Build .rm structure** (layers, lines, points)
4. **Write binary format** (using rmscene or custom)
5. **Generate metadata** (UUID, thumbnails, .content file)
6. **Upload** (rMAPI or file copy)

### Coordinate System (Much Simpler!)
```python
# .rm files use direct display coordinates
x_rm = svg_x  # 0.0 to 1404.0 (display width)
y_rm = svg_y  # 0.0 to 1872.0 (display height)

# No complex transformation needed!
```

---

## Questions for Decision Making

1. **Is real-time injection critical?**
   - If NO → .rm file approach is better
   - If YES → Might need to accept injection limitations

2. **What features do you need?**
   - Just lines? → Either approach works
   - Layers, colors, text? → .rm file approach better

3. **What's your OS version strategy?**
   - Need to support updates? → .rm file (more stable)
   - Locked version? → Injection might be okay

4. **Who are your users?**
   - Technical users? → Either
   - General users? → .rm file (no root needed)

---

## Conclusion

The pen injection approach is technically impressive but architecturally mismatched. The .rm file format approach aligns with how the device actually works and has better community support.

**Recommendation:** Pivot to .rm file generation with optional pen injection for development/testing only.

---

## Sources

- [reMarkable .lines File Format](https://plasma.ninja/blog/devices/remarkable/binary/format/2017/12/26/reMarkable-lines-file-format.html)
- [GitHub: YakBarber/remarkable_file_format](https://github.com/YakBarber/remarkable_file_format)
- [GitHub: ricklupton/rmscene](https://github.com/ricklupton/rmscene)
- [GitHub: ddvk/rmfakecloud](https://github.com/ddvk/rmfakecloud)
- [GitHub: juruen/rmapi](https://github.com/juruen/rmapi)
- [GitHub: reHackable/awesome-reMarkable](https://github.com/reHackable/awesome-reMarkable)
- [Drawj2d reMarkable Wiki](https://sourceforge.net/p/drawj2d/wiki/reMarkable/)
