# reMarkable 2 Beta Firmware & Community Repositories

**Report Date**: December 4, 2024
**Focus**: Beta firmware compatibility & comprehensive repository list

## Beta Firmware Information

### Official Beta Program

reMarkable operates an official beta testing program:
- **Enrollment**: [reMarkable Beta Program](https://support.remarkable.com/s/article/reMarkable-beta-program)
- **Release Overview**: [Beta Software Releases](https://support.remarkable.com/s/article/Overview-of-beta-software-releases)

**⚠️ Beta Program Restrictions**:
- EULA prohibits third-party software installation on beta devices
- Community tools may not be supported or tested on beta versions
- Risk of soft-bricking when using unauthorized modifications

### Known Beta Releases (2024-2025)

Based on community reports:
- **3.22 Beta**: Released ~August 2025 (skipped 3.21)
- **3.20.0.92**: Public release June 2025
- **3.23**: Current stable (November 2025)
- **3.24.x**: Unconfirmed - may be beta or misidentified version

**Note**: Beta versions often have higher build numbers (e.g., 0.147) than public releases.

### Sources
- [reMarkable OS 3.22 Beta announcement](https://einkist.wordpress.com/2025/08/01/remarkable-os-3-22-beta-the-time-has-come/)
- [Software Release 3.20](https://support.remarkable.com/s/article/Software-release-3-20)
- [Software Release 3.22](https://support.remarkable.com/s/article/Software-release-3-22)
- [Software Release 3.23](https://support.remarkable.com/s/article/Software-release-3-23)

---

## Device Information Commands

Run these SSH commands to gather complete device information:

```bash
# Connect to your device first
ssh root@10.11.99.1  # Replace with your device IP

# === FIRMWARE VERSION ===
cat /etc/version
# Shows: X.Y.Z.BBB (e.g., 3.23.0.64 or 3.24.0.147)

# === SYSTEM INFORMATION ===
cat /etc/os-release
# OS details and build info

uname -a
# Kernel version and architecture

# === DEVICE MODEL ===
cat /sys/devices/soc0/machine
# Should show "reMarkable 2.0" or similar

# === DISPLAY INFORMATION ===
fbset
# Framebuffer settings (resolution, depth)

cat /sys/class/graphics/fb0/virtual_size
# Display dimensions

# === XOCHITL VERSION ===
/usr/bin/xochitl --version
# Main UI software version

# === WACOM INPUT DEVICE ===
ls -l /dev/input/by-path/*Wacom*
# Stylus input device path

cat /sys/class/input/event0/device/name
cat /sys/class/input/event1/device/name
cat /sys/class/input/event2/device/name
# Identify which event device is Wacom

# === LIBRARY VERSIONS ===
ldconfig -v | grep libqsgepaper
# Qt e-paper library version

# === RUNNING PROCESSES ===
ps aux | grep xochitl
# Check xochitl process and arguments

# === FILE FORMAT VERSION ===
# Check a .rm file header to determine format version
hexdump -C ~/.local/share/remarkable/xochitl/*.rm | head -n 20
# Shows file format magic bytes

# === CLOUD SYNC STATUS ===
cat ~/.config/remarkable/xochitl.conf | grep DeviceId
# Device registration info

# === BETA PROGRAM STATUS ===
# Check if enrolled in beta
cat ~/.config/remarkable/xochitl.conf | grep -i beta
ls /home/root/.config/remarkable/ | grep -i beta

# === COMPLETE SYSTEM DUMP ===
# Create comprehensive report
cat << 'EOF' > /tmp/device_info.sh
#!/bin/bash
echo "=== DEVICE INFORMATION REPORT ==="
echo ""
echo "Date: $(date)"
echo ""
echo "--- Firmware Version ---"
cat /etc/version
echo ""
echo "--- OS Release ---"
cat /etc/os-release
echo ""
echo "--- Kernel ---"
uname -a
echo ""
echo "--- Device Model ---"
cat /sys/devices/soc0/machine
echo ""
echo "--- Display Info ---"
fbset
echo ""
echo "--- Xochitl Version ---"
/usr/bin/xochitl --version 2>&1
echo ""
echo "--- Input Devices ---"
ls -l /dev/input/by-path/
echo ""
echo "--- Event Devices ---"
for i in /sys/class/input/event*/device/name; do
  echo "$i: $(cat $i)"
done
echo ""
echo "--- Running Processes ---"
ps aux | grep -E "(xochitl|remarkable)"
echo ""
echo "=== END REPORT ==="
EOF
chmod +x /tmp/device_info.sh
/tmp/device_info.sh
```

**Copy output and paste here for analysis.**

---

## Comprehensive Repository List for reMarkable 2

### 🟢 File Format Libraries & Tools

#### **rmscene** - Python .rm v6 Library
- **Status**: ✅ Active (Sept 2024 update)
- **Purpose**: Read/write .rm v6 files
- **Language**: Python
- **Link**: https://github.com/ricklupton/rmscene
- **Install**: `pip install rmscene`
- **Firmware Support**: 3.0+ (v6 format)
- **Features**: Layers, text, highlights, forward-compatible
- **Best for**: Programmatic file generation

#### **lines-are-rusty** - Rust File API
- **Status**: ✅ Active
- **Purpose**: Binary .lines format processing
- **Language**: Rust
- **Link**: https://github.com/ax3l/lines-are-rusty
- **Firmware Support**: Format-dependent
- **Features**: Fast binary parsing
- **Best for**: High-performance file processing

#### **rmc** - reMarkable Cloud CLI
- **Status**: ✅ Active
- **Purpose**: File upload/download via cloud
- **Language**: Rust
- **Link**: https://github.com/adinkwok/rmc
- **Features**: Fast CLI for cloud operations
- **Best for**: Bulk file operations

---

### 🟢 Cloud Sync & API Tools

#### **rMAPI** - Cloud API Client
- **Status**: ✅ Active (use ddvk fork)
- **Purpose**: Cloud file management
- **Language**: Go
- **Link**: https://github.com/ddvk/rmapi (maintained)
- **Original**: https://github.com/juruen/rmapi (archived)
- **Version**: Use 0.0.27+
- **Firmware Support**: Up to 3.23+ (Sync15 experimental)
- **Features**: Upload, download, organize files
- **Best for**: Production cloud integration

#### **rmfakecloud** - Self-hosted Cloud
- **Status**: ✅ Active
- **Purpose**: Local cloud server
- **Language**: Go
- **Link**: https://github.com/ddvk/rmfakecloud
- **Firmware Support**: Up to 3.22 (tested)
- **Features**: Full cloud replacement
- **Best for**: Privacy, offline sync

#### **rmcl** - Async Python Cloud Library
- **Status**: ✅ Active
- **Purpose**: Python cloud API wrapper
- **Language**: Python (async)
- **Link**: https://github.com/rschroll/rmcl
- **Features**: High-level async interface
- **Best for**: Python integration projects

---

### 🟢 Document Conversion & Manipulation

#### **rmrl** - Rendering Library
- **Status**: ✅ Active
- **Purpose**: Convert annotated docs to PDF
- **Language**: Python
- **Link**: https://github.com/rschroll/rmrl
- **Features**: PDF export with annotations
- **Best for**: Backup, archiving with markup

#### **rm-pdf-tools** - PDF Editor
- **Status**: ✅ Active
- **Purpose**: Insert/delete pages from annotated PDFs
- **Language**: Python
- **Link**: https://github.com/skius/rm-pdf-tools
- **Features**: Page manipulation, preserves annotations
- **Best for**: PDF reorganization

#### **remarks** - Annotation Extractor
- **Status**: ✅ Active
- **Purpose**: Extract highlights/annotations
- **Language**: Python
- **Link**: https://github.com/lucasrla/remarks
- **Export**: Markdown, PDF, PNG, SVG
- **Best for**: Note export, digital garden

---

### 🟡 Drawing & Screen Access (rM2 Specific)

#### **remarkable2-framebuffer** - Screen Access
- **Status**: ⚠️ Depends on firmware
- **Purpose**: Direct framebuffer access
- **Language**: C
- **Link**: https://github.com/ddvk/remarkable2-framebuffer
- **Firmware Support**: Up to 3.3.x (Toltec limit)
- **Features**: rm2fb compatibility layer
- **Best for**: Third-party UI apps
- **⚠️ Warning**: May soft-brick on 3.4+

#### **ReCept** - Input Injection
- **Status**: ⚠️ Firmware-sensitive
- **Purpose**: Fix jagged lines, input modification
- **Language**: C
- **Link**: https://github.com/funkey/recept/
- **Method**: LD_PRELOAD hook
- **Firmware Support**: Tested on 2.x-3.x
- **Note**: Our rm2in2 project is forked from this
- **⚠️ Warning**: Fragile across updates

---

### 🟢 Screen Streaming

#### **goMarkableStream** - Go Streaming
- **Status**: ✅ Active
- **Purpose**: Screen streaming with color support
- **Language**: Go
- **Link**: https://github.com/owulveryck/goMarkableStream
- **Firmware Support**: 2.5+
- **Features**: Fast, color support
- **Best for**: Live demos, remote viewing

#### **rM-vnc-server** - VNC Server
- **Status**: ✅ Active
- **Purpose**: Efficient VNC streaming
- **Language**: C++
- **Link**: https://github.com/peter-sa/rM-vnc-server
- **Features**: Damage-tracking, region updates
- **Best for**: Remote access, lower bandwidth

#### **reStream** - Python Streaming
- **Status**: ⚠️ Older
- **Purpose**: Simple screen mirroring
- **Language**: Python
- **Link**: https://github.com/rien/reStream
- **Note**: Works but slower than Go alternatives

---

### 🟢 Development Frameworks

#### **rM2-stuff** - App Collection
- **Status**: ✅ Active (timower)
- **Purpose**: Collection of apps, utilities, libraries
- **Language**: C++
- **Link**: https://github.com/timower/rM2-stuff
- **Includes**: Custom launchers, system tools
- **Best for**: Learning rM2 development

#### **rmkit** - Development Kit
- **Status**: ✅ Active
- **Purpose**: Framework for building apps
- **Language**: C++
- **Link**: https://rmkit.dev/
- **GitHub**: https://github.com/rmkit-dev/rmkit
- **Features**: Drawing APIs, procedural brushes
- **Best for**: Native app development

---

### 🟢 Utility Tools

#### **RCU** - reMarkable Connection Utility
- **Status**: ✅ Active
- **Purpose**: All-in-one management tool
- **Platform**: Windows/Mac/Linux
- **Link**: https://www.davisr.me/projects/rcu/
- **Firmware Support**: Up to 3.23.0.64
- **Features**: Backups, templates, firmware updates
- **Best for**: Non-technical users

#### **reMarkable-hacks** - Tips & Tricks
- **Status**: ✅ Active
- **Purpose**: Curated collection of modifications
- **Link**: https://github.com/danielebruneo/remarkable2-hacks
- **Type**: Documentation, scripts
- **Best for**: Learning possibilities

---

### 🟢 Academic & Research Tools

#### **paper2remarkable** - Academic Papers
- **Status**: ✅ Active
- **Purpose**: Download papers, send to device
- **Language**: Python
- **Link**: https://github.com/GjjvdBurg/paper2reMarkable
- **Sources**: arXiv, PubMed, ACM, etc.
- **Best for**: Research workflows

#### **rmathlab** - Math Recognition
- **Status**: ✅ Active
- **Purpose**: Handwriting → LaTeX
- **Link**: https://github.com/simonguld/rmathlab
- **Features**: OCR math equations
- **Best for**: STEM notes

---

### 🟢 Drawing Applications

#### **Drawj2d** - Technical Drawing
- **Status**: ✅ Active (updated Sept 2024)
- **Purpose**: Create technical line drawings
- **Language**: Java
- **Link**: https://drawj2d.sourceforge.io/
- **Features**: Color support (3.6+)
- **Export**: .rm files
- **Best for**: Engineering diagrams
- **⭐ Highly relevant**: Generates .rm files programmatically!

---

### 🔴 Package Managers (Limited Firmware Support)

#### **Toltec** - Package Repository
- **Status**: ⚠️ Limited (3.3.2 max)
- **Purpose**: Third-party software repository
- **Link**: https://toltec-dev.org/
- **GitHub**: https://github.com/toltec-dev/toltec
- **Firmware Support**: 2.6.1.71 to 3.3.2.1666 ONLY
- **⚠️ Critical**: Will soft-brick rM2 on 3.4+
- **Future**: Working on 3.4+ support
- **Best for**: Older firmware users

---

## Repositories Specifically for .rm File Generation

These are most relevant for rm2in2 project pivot:

### Tier 1: Production-Ready

1. **rmscene** - Python library, v6 format, actively maintained
   - Direct programmatic control
   - Forward-compatible
   - Easy integration
   - **Status**: ✅ Recommended

2. **Drawj2d** - Java app, generates .rm files
   - Proven working with latest firmware
   - Color support
   - Technical drawing focus
   - **Status**: ✅ Reference implementation

### Tier 2: Reference/Research

3. **lines-are-rusty** - Rust implementation
   - Performance-oriented
   - Binary format details
   - **Status**: ✅ For learning format

4. **rmrl** - Rendering/export
   - PDF generation
   - Can study .rm structure
   - **Status**: ✅ For reference

---

## Recommended Stack for rm2in2 (Beta Firmware)

Given beta firmware 3.24.0.147:

### ✅ Safe to Use:
1. **rmscene** - File generation (firmware-agnostic)
2. **rMAPI (ddvk)** - Cloud upload (API-based, likely works)
3. **RCU** - Local transfer (likely compatible)
4. **SSH/rsync** - Direct file transfer (always works)

### ⚠️ Test Carefully:
- **rmfakecloud** - Untested on 3.24, backup first
- **Screen streaming** - May work, test non-destructively

### ❌ Avoid:
- **Toltec** - Will brick device
- **LD_PRELOAD hooks** - High risk of breakage
- **rm2fb-dependent apps** - Display driver incompatible

---

## Next Steps for rm2in2 Project

### Immediate Actions:

1. **Gather device info** using SSH commands above
2. **Test rmscene** on your beta firmware:
   ```bash
   pip install rmscene
   python3 -c "import rmscene; print(rmscene.__version__)"
   ```
3. **Create test .rm file** and transfer to device
4. **Verify rendering** on beta firmware

### Development Priority:

1. ✅ **Phase 1**: rmscene integration (low risk)
2. ✅ **Phase 2**: Test on 3.24.0.147 (validation)
3. ⚠️ **Phase 3**: Delivery method (rMAPI/RCU/SSH)
4. ❌ **Deprecated**: LD_PRELOAD injection (too risky)

---

## Beta Firmware Compatibility Assessment

**For version 3.24.0.147**:

| Approach | Risk | Confidence | Recommendation |
|----------|------|------------|----------------|
| .rm file generation | 🟢 Low | High | ✅ Proceed |
| rMAPI cloud upload | 🟡 Medium | Medium | ✅ Test |
| RCU local transfer | 🟡 Medium | Medium | ✅ Test |
| SSH file transfer | 🟢 Low | High | ✅ Use |
| LD_PRELOAD injection | 🔴 High | Low | ❌ Avoid |
| Toltec tools | 🔴 Critical | None | ❌ Never |

---

## Sources

### Official Documentation
- [reMarkable Beta Program](https://support.remarkable.com/s/article/reMarkable-beta-program)
- [Beta Software Overview](https://support.remarkable.com/s/article/Overview-of-beta-software-releases)
- [Software Release Notes](https://support.remarkable.com/s/article/Release-notes-overview)

### Community Resources
- [awesome-reMarkable](https://github.com/reHackable/awesome-reMarkable) - Curated tool list
- [reMarkable Guide](https://remarkable.guide/) - Community documentation
- [Toltec Development](https://github.com/toltec-dev/toltec)

### Key Repositories
- [rmscene](https://github.com/ricklupton/rmscene)
- [rMAPI (maintained)](https://github.com/ddvk/rmapi)
- [rmfakecloud](https://github.com/ddvk/rmfakecloud)
- [timower/rM2-stuff](https://github.com/timower/rM2-stuff)
- [Drawj2d](https://drawj2d.sourceforge.io/)

### Discussions
- [reMarkable OS 3.22 Beta](https://einkist.wordpress.com/2025/08/01/remarkable-os-3-22-beta-the-time-has-come/)
- [eWritable Firmware Tracker](https://ewritable.net/brands/remarkable/firmware/)

---

*Last Updated*: December 4, 2024
*Focus*: Beta firmware 3.24.0.147 compatibility
*Assessment*: .rm generation approach strongly recommended
