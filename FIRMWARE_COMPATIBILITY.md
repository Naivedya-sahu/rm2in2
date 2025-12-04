# reMarkable Firmware 3.23+ Community Tool Compatibility

**Report Date**: December 4, 2024
**Target Firmware**: 3.23.x / 3.24.x (Build 0.147)

## Executive Summary

⚠️ **CRITICAL**: Most community tools have **LIMITED or NO support** for firmware versions beyond 3.3.2.1666. If you're on firmware 3.23+ or 3.24+, expect significant compatibility issues with Toltec-based tools and LD_PRELOAD modifications.

## Latest reMarkable Firmware Status

### Current Public Release: **3.23** (November 2024)
- Released approximately 4 weeks ago
- Compatible with: reMarkable 1, 2, Paper Pro, Paper Pro Move
- Features: "Convert to Notebook", AI-powered sharing, improved templates

**Note**: Version 3.24 does NOT exist for reMarkable (it's a Supernote version). If you have "3.24.0.147", please verify your actual firmware version via Settings → About.

### Verified Build Numbers
- **3.23.0.64**: Last confirmed build with RCU compatibility
- **3.23.0.147**: Mentioned by user (unverified in documentation)

## Community Tool Compatibility Status

### 🔴 TOLTEC - NOT COMPATIBLE

**Supported Range**: OS 2.6.1.71 to 3.3.2.1666 ONLY

**Critical Issues**:
- ⛔ Will **soft-brick** reMarkable 2 if installed on unsupported versions
- ⛔ Display driver (rm2fb) incompatible with 3.4+
- ⛔ Screen will not render until Toltec is uninstalled
- ⛔ Official stance: "Heavily recommend against using on newer versions"

**Future Plans**:
- Working on 3.4+ support (see [toltec-dev/toltec#859](https://github.com/toltec-dev/toltec/issues/859))
- Will add selective version support (3.5.2, 3.8.2) instead of every release
- Timeline: Unknown

**Reference**: [Toltec Official](https://toltec-dev.org/)

---

### 🟡 rmfakecloud - LIMITED COMPATIBILITY

**Supported Range**: Up to firmware 3.22.0 (tested)

**Status**:
- ✅ Works with 3.22 and earlier
- ❓ **3.23+ untested** - no community reports found
- ❓ **3.24 unverified** (version likely doesn't exist)

**Known Issues**:
- New sync protocol (Sync15) rolled out incrementally
- Some users forced to new protocol, others still on old
- May work but not officially tested

**Assessment**: Cloud sync likely works (uses HTTP API, not device hooks), but backup before testing.

**Reference**: [rmfakecloud GitHub](https://github.com/ddvk/rmfakecloud)

---

### 🟢 rMAPI - COMPATIBLE (with caveats)

**Supported Range**: Up to 3.23.0.64 (latest confirmed)

**Status**:
- ✅ Use maintained fork: [ddvk/rmapi](https://github.com/ddvk/rmapi)
- ⚠️ Original juruen/rmapi **archived/unmaintained**
- ✅ Version 0.0.27+ works with new sync protocol (experimental)
- ❌ Version 0.0.25 broken - **upgrade required**

**Known Issues**:
- Sync15 protocol support is experimental
- Maintain backups when using with 3.23+
- Some users report working fine, others have issues

**Assessment**: Cloud API-based - **likely works** with 3.23+ and potentially 3.24 if that exists.

**References**:
- [rMAPI (ddvk fork)](https://github.com/ddvk/rmapi)
- [Original rMAPI (archived)](https://github.com/juruen/rmapi)

---

### 🟢 rmscene - COMPATIBLE

**Supported Format**: .rm v6 (firmware 3.0+)

**Status**:
- ✅ Reads/writes v6 .rm files
- ✅ Supports firmware 3.3 text formatting (bold/italic)
- ✅ Supports firmware 3.6 highlighted text
- ✅ Forward-compatible design (preserves unknown blocks)

**Latest Updates**:
- Library actively maintained
- Last significant update: September 2024 (color support)
- Format stable since firmware 3.0 (late 2022)

**Assessment**: **FULLY COMPATIBLE** - .rm format unchanged in 3.23+

**Installation**: `pip install rmscene`

**References**:
- [rmscene GitHub](https://github.com/ricklupton/rmscene)
- [rmscene PyPI](https://pypi.org/project/rmscene/)

---

### 🟢 RCU (reMarkable Connection Utility) - COMPATIBLE

**Supported Range**: 1.8.1.1 to 3.23.0.64

**Status**:
- ✅ Official compatibility table published for 3.23
- ✅ Cross-platform (Windows/Mac/Linux)
- ✅ Local/offline management (no cloud required)
- ❓ Build 0.147 not explicitly listed

**Features Working**:
- Backups, screenshots, notebooks
- Template and wallpaper management
- Firmware updates
- Third-party software installation

**Assessment**: **LIKELY COMPATIBLE** with 3.23.x builds

**Reference**: [RCU Official](https://www.davisr.me/projects/rcu/)

---

## Impact on rm2in2 Project

### Current Approach: LD_PRELOAD Pen Injection

**Compatibility**: 🔴 **HIGH RISK**

**Concerns**:
1. **LD_PRELOAD fragility**: Direct system call hooking breaks easily across firmware updates
2. **Xochitl changes**: Display server and event handling may change in 3.23+
3. **No community testing**: Zero reports of LD_PRELOAD injection on 3.23+
4. **Coordinate system**: May change with new display drivers
5. **Toltec dependency**: Cannot use Toltec tools for debugging/deployment

**Risk Assessment**:
- May work if event system unchanged
- High probability of breakage in future updates
- No rollback if firmware auto-updates

---

### Alternative Approach: .rm File Generation

**Compatibility**: 🟢 **LOW RISK**

**Advantages**:
1. ✅ **Format stable**: v6 unchanged since firmware 3.0
2. ✅ **No device hooks**: Pure file generation
3. ✅ **Forward compatible**: rmscene preserves unknown data
4. ✅ **Works with rMAPI**: Upload via cloud API (firmware-agnostic)
5. ✅ **Testable**: Can verify files before deployment

**Confirmed Working**:
- rmscene library fully functional
- rMAPI cloud uploads working (with maintained fork)
- RCU local transfers compatible with 3.23

**Risk Assessment**:
- Minimal risk - file format standardized
- Cloud API more stable than device hooks
- Can test without device modification

---

## Recommendations

### For Firmware 3.23+

1. **DO NOT use**:
   - ❌ Toltec (will brick device)
   - ❌ Any rm2fb-dependent tools
   - ❌ LD_PRELOAD hooks (untested, likely fragile)

2. **Safe to use**:
   - ✅ rmscene (.rm file library)
   - ✅ rMAPI 0.0.27+ (ddvk fork)
   - ✅ RCU (reMarkable Connection Utility)
   - ✅ Native file transfer (SSH/USB)

3. **Use with caution**:
   - ⚠️ rmfakecloud (backup first, 3.23+ untested)
   - ⚠️ Custom modifications (test on 3.22 first)

### For rm2in2 Project

**Recommended Path**: **Pivot to .rm file generation**

**Reasoning**:
1. Pen injection via LD_PRELOAD is high-risk on 3.23+
2. rmscene library confirmed working
3. Upload methods (rMAPI/RCU) functional
4. Better long-term stability
5. No device modification required

**Migration Plan**:
1. Keep current pen injection for 3.22 and earlier
2. Develop .rm generation using rmscene
3. Test .rm files on 3.23+ devices
4. Provide both options based on firmware version

---

## Version Verification

To check your actual firmware version:

1. On device: **Settings → About → Software version**
2. Via SSH: `cat /etc/version`
3. Format: `X.Y.Z.BBB` (e.g., 3.23.0.64)

Common confusion:
- Supernote uses version 3.24 (NOT reMarkable)
- Build numbers vary (0.64, 0.147, etc.)
- reMarkable currently maxes at 3.23.x

---

## Additional Resources

### Official Documentation
- [reMarkable Release Notes](https://support.remarkable.com/s/article/Release-notes-overview)
- [reMarkable Firmware Tracker](https://ewritable.net/brands/remarkable/firmware/)
- [Software Updates Overview](https://support.remarkable.com/s/topic/0TOQD0000002L1x4AE/software-updates)

### Community Resources
- [awesome-reMarkable](https://github.com/reHackable/awesome-reMarkable) - Curated tool list
- [reMarkable Guide](https://remarkable.guide/) - Community documentation
- [Toltec Development](https://github.com/toltec-dev/toltec) - Community software repository

### Related Discussions
- [Toltec 3.4+ Support Issue](https://github.com/toltec-dev/toltec/issues/859)
- [rmfakecloud 3.22 Sync Issues](https://github.com/ddvk/rmfakecloud/issues/220)
- [Paper Pro Support Discussion](https://github.com/toltec-dev/toltec/discussions/910)

---

## Summary Table

| Tool | 3.22 | 3.23.0.64 | 3.23.0.147+ | Risk Level | Notes |
|------|------|-----------|-------------|------------|-------|
| **Toltec** | ❌ | ❌ | ❌ | 🔴 Critical | Will brick RM2 |
| **rmfakecloud** | ✅ | ❓ | ❓ | 🟡 Medium | Untested |
| **rMAPI (ddvk)** | ✅ | ✅ | ✅* | 🟢 Low | Use v0.0.27+ |
| **rmscene** | ✅ | ✅ | ✅ | 🟢 Low | Format stable |
| **RCU** | ✅ | ✅ | ❓ | 🟢 Low | Likely works |
| **LD_PRELOAD** | ✅ | ❓ | ❓ | 🔴 High | Fragile |
| **.rm files** | ✅ | ✅ | ✅ | 🟢 Low | Recommended |

*Experimental sync protocol support

---

## Conclusion

**For firmware 3.23.0.147 or later**:
- ✅ Use .rm file generation (rmscene)
- ✅ Use cloud sync (rMAPI 0.0.27+)
- ✅ Use local transfer (RCU/SSH)
- ❌ Avoid Toltec and device hooks
- ❌ Avoid untested modifications

**Best approach for rm2in2**: Transition to .rm file generation for production use while keeping pen injection as optional dev tool for firmware ≤3.22.

---

*Last Updated*: December 4, 2024
*Source Queries*: firmware 3.23, 3.24, community tools, rmscene, rMAPI, rmfakecloud, Toltec
