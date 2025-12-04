# Complete guide to reMarkable 2 pen input parsing

**The reMarkable 2's Wacom digitizer exposes raw pen data via standard Linux evdev at `/dev/input/event1`, enabling direct stroke capture with 12-bit pressure sensitivity and centidegree tilt tracking.** The community has developed robust production-tested solutions spanning low-level evdev parsing in Rust and Python, coordinate transformation libraries, streaming tools, and comprehensive .rm file format parsers—providing everything needed for custom handwriting applications.

## Wacom digitizer event format and parsing

The RM2 uses a Wacom W9013 I2C digitizer (vendor ID 0x56a) that reports through the standard Linux input subsystem. Unlike RM1 which uses event0, the **RM2 pen input lives at `/dev/input/event1`**—a critical distinction for cross-device compatibility.

The digitizer reports these absolute axes via EV_ABS events:

| Axis | Range | Code | Notes |
|------|-------|------|-------|
| X position | 0–20967 | ABS_X (0x00) | Raw sensor units |
| Y position | 0–15725 | ABS_Y (0x01) | Raw sensor units |
| Pressure | 0–4095 | ABS_PRESSURE (0x18) | 12-bit, 4096 levels |
| Distance | 0–255 | ABS_DISTANCE (0x19) | Hover height |
| Tilt X/Y | ±9000 | ABS_TILT_X/Y (0x1a/0x1b) | Centidegrees (±90°) |

Button events (EV_KEY) track pen state: **BTN_TOOL_PEN** (0x140) indicates proximity detection, **BTN_TOUCH** (0x14a) signals physical contact, BTN_TOOL_RUBBER (0x141) activates eraser mode, and BTN_STYLUS/BTN_STYLUS2 handle side buttons. The kernel sends SYN_REPORT after each complete event packet.

**libremarkable** (github.com/canselcik/libremarkable) provides the most complete Rust implementation. Its `wacom.rs` accumulates axis values atomically and emits complete pen states only on SYN_REPORT, distinguishing Hover events (BTN_TOUCH=0, uses ABS_DISTANCE) from Draw events (BTN_TOUCH=1, uses ABS_PRESSURE):

```rust
// libremarkable pattern: accumulate then emit on sync
match ev.event_type().0 {
    EV_ABS => match ev.event_code() {
        ABS_X => state.last_x.store(ev.value() as u16),
        ABS_PRESSURE => state.last_pressure.store(ev.value() as u16),
        // ... accumulate other axes
    },
    EV_SYN => return Some(build_complete_event(&state)),
}
```

For Python, **remarkable_mouse** (github.com/Evidlo/remarkable_mouse) uses libevdev to parse events and recreate them on a virtual tablet device for desktop control.

## Stroke detection uses BTN_TOUCH, not pressure thresholds

The community consensus is clear: **stroke start/end detection relies on BTN_TOUCH events rather than pressure thresholds**. When BTN_TOUCH transitions to 1, the pen has made meaningful contact; when it returns to 0, the stroke ends. This approach is more reliable than pressure-based detection because the digitizer's contact sensor is independent of pressure measurement.

However, some projects like remouseable implement configurable pressure thresholds (typically **600–1000** on the 0–4095 scale) for click detection in mouse-control scenarios. The ReCept project adds a moving average filter for line smoothing—with window size N=16, positions trail by N/2 samples, adding approximately **8ms latency** at typical event rates.

Observed polling rates from timestamp analysis show events arriving every **3–6ms** (~166–333Hz). The oft-cited 500Hz figure likely represents the Wacom hardware's maximum capability rather than actual delivered rate.

## Coordinate transformation between sensor and display space

The transformation from Wacom sensor coordinates (0–20967 × 0–15725) to display pixels (1404 × 1872) requires both scaling and rotation handling. The core scaling is linear:

```python
# Basic transformation
display_x = wacom_x * (1404 / 20967)  # ~0.0670 scalar
display_y = wacom_y * (1872 / 15725)  # ~0.1190 scalar
```

**No empirical offsets or dead zones** have been documented—the transformation is purely linear. However, the Wacom sensor coordinate system is **rotated relative to the display**, requiring orientation-aware transforms based on tablet position:

| Orientation | Transform |
|-------------|-----------|
| Top (buttons up) | x = WACOM_WIDTH - x |
| Bottom (inverted) | y = WACOM_HEIGHT - y |
| Left (landscape CCW) | swap(x, y) |
| Right (landscape CW) | x = WACOM_HEIGHT - y; y = WACOM_WIDTH - x |

libremarkable handles this through device-specific `WacomPlacement` configurations with `rotation`, `invert_x`, and `invert_y` parameters. A known calibration issue on RM2 (documented in GitHub Issue #13 on reMarkable/linux) causes ink to appear at ~0.5mm displacement from the actual nib position, varying in "patches" across the screen.

## Production tools for streaming and mirroring

**goMarkableStream** (github.com/owulveryck/goMarkableStream) offers the most complete solution: a self-contained Go binary that hosts an HTTP server exposing both framebuffer streaming and WebSocket pen event endpoints (`/events`). It reads display data directly from xochitl's process memory using RLE or ZSTD compression, achieving ~10% CPU at 200ms frame rate.

**Pipes and Paper** (gitlab.com/afandian/pipes-and-paper) takes a simpler approach: a Python script that SSH-tunnels to the tablet, reads `/dev/input/event1` remotely, parses binary evdev events, and streams decoded coordinates to a browser via WebSocket for canvas rendering. No tablet-side installation required.

**rMview** (github.com/bordaigorl/rmview) with **rM-vnc-server** provides the lowest latency screen mirroring using damage-tracking VNC. By only transmitting changed pixel regions and using ZRLE compression, updates often display on the client before the e-ink refresh completes. It uses libqsgepaper-snoop on RM2 to detect framebuffer changes.

For RM2 framebuffer access, **rm2fb** (github.com/ddvk/remarkable2-framebuffer) is essential—unlike RM1's direct /dev/fb access, RM2's framebuffer exists in xochitl's memory space, requiring rm2fb's shared memory/message queue approach with LD_PRELOAD injection.

## The .rm file format stores vector stroke data

reMarkable notebooks store strokes in proprietary `.rm` files at `/home/root/.local/share/remarkable/xochitl/{UUID}/{page-uuid}.rm`. The format has evolved significantly:

**V3–V5 structure** (pre-firmware 3.0):
- 43-byte header: `reMarkable .lines file, version=X` plus padding
- Layers containing strokes, each stroke with brush type, color, base size
- Points with: X (0–1404), Y (0–1872), speed, direction, width, pressure (0–1.0)

**V6 format** (firmware 3.0+) is a complete redesign:
- Block-based architecture with tagged data
- CRDT sequences for cloud sync
- Text support with formatting
- SceneTree structure for layers/groups

**rmscene + rmc** (github.com/ricklupton/rmscene) is the recommended Python stack for V6 files:
```bash
pip install rmc
rmc -t svg notebook.rm -o output.svg  # Convert to SVG
rmc -t pdf notebook.rm -o output.pdf  # Convert to PDF
```

**lines-are-beautiful** (github.com/ax3l/lines-are-beautiful) provides C++ parsing with `lines2svg` and `lines2png` utilities. Its Rust port **lines-are-rusty** offers the same functionality. For Kaitai Struct specifications, **remarkable_file_format** (github.com/YakBarber/remarkable_file_format) documents the complete V6 binary layout.

## SVG conversion and stroke replay tools

**rmc** handles SVG/PDF export from .rm files with full layer support. For real-time stroke capture and replay, the evdev approach used by Pipes and Paper records raw events that can be replayed later using Linux's uinput subsystem.

**rmrl** (github.com/rschroll/rmrl) specializes in high-quality PDF rendering with annotation overlays, useful for converting annotated documents. **rm2pdf** (github.com/rorycl/rm2pdf) in Go creates layered PDFs from notebooks, though it doesn't support V6 format.

For handwriting recognition, the community uses **MyScript** (official reMarkable Connect service), **rmathlab** for math recognition via Mathpix, and **armrest** which combines recognition with an Elm-inspired UI library.

## Critical implementation details and known issues

**Device detection**: Always verify device model—RM1 uses event0 for pen, RM2 uses event1. Query `/sys/devices` or check for button presence (RM2 has no physical buttons).

**SYN_DROPPED handling**: Per kernel documentation, discard all events until the next SYN_REPORT after receiving SYN_DROPPED, then query device state via EVIOCG* ioctls. Missing this causes stroke data corruption.

**Jagged line fix**: ReCept (github.com/funkey/recept) uses LD_PRELOAD to intercept reads and apply smoothing, eliminating the "wobbly lines" issue some users experience.

**Pressure baseline**: If the pen registers strokes while hovering, remove and reseat the nib to recalibrate the pressure sensor's zero point.

## Conclusion

The reMarkable 2's pen input system is well-documented through community reverse engineering. **libremarkable** provides the reference Rust implementation for evdev parsing with complete coordinate transformation. For .rm file parsing, **rmscene/rmc** handles current V6 format while **lines-are-beautiful** covers legacy versions. Screen streaming is best served by **goMarkableStream** for combined framebuffer and event streaming, or **rM-vnc-server** for lowest-latency mirroring. The 0–20967 × 0–15725 sensor space maps linearly to 1404 × 1872 display pixels with orientation-dependent rotation, and stroke boundaries are reliably detected via BTN_TOUCH state transitions rather than pressure thresholds.