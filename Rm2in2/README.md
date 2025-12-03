# Rm2in2 - Client Side

Code that runs on your **PC/Linux workstation**.

## Purpose

This directory contains tools for:
- Converting graphics/text to PEN commands
- Sending commands to the RM2 device
- Testing and validation
- Coordinate system analysis

## Structure

```
Rm2in2/
├── tools/         - Conversion utilities (SVG, PNG, text to PEN)
├── scripts/       - Helper scripts for deployment and testing
├── tests/         - Client-side testing and validation
└── examples/      - Sample inputs and outputs
```

## Requirements

- Python 3.6+
- SSH/SCP access to RM2 device
- Optional: Inkscape (for SVG editing)

## Usage

```bash
# Convert graphics to PEN commands
python tools/svg_to_pen.py input.svg output.txt

# Send to RM2
./scripts/send.sh output.txt
```

## Status

⚠️ **In Development** - Coordinate system testing in progress. No conversion tools yet.
