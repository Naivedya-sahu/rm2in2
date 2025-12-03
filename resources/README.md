# Resources Directory

This directory contains archived materials from previous development iterations and supporting utilities.

## Structure

### previous-versions/
Archive of all previous implementation attempts:
- **rm2-claude/** - Latest iteration (coordinate issues, needs revision)
- **rm2-inject-v3/** - Early version with mirroring bugs
- **rm2-inject-v4/** - Fixed version but still has orientation issues

These are kept for reference but should NOT be used as-is. They contain valuable insights but have fundamental coordinate system problems.

### documentation/
Standalone documentation files:
- **rm2-features.txt** - Comprehensive feature list and requirements

### testing-utilities/
Diagnostic and development tools:
- **rm2_diagnostic.sh** - RM2 system diagnostic script
- **test_crosscompile.sh** - Cross-compiler testing utility

### examples/
Sample files for testing:
- **segoe path.svg** - Font reference file

## Important Note

**All code in previous-versions/ has coordinate system issues that prevent curves, text, and graphics from working correctly.** The new implementation in the root `Rm2/` and `Rm2in2/` directories will start fresh with proper coordinate testing before proceeding to injection and conversion.
