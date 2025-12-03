# Rm2 - Server Side

Code that runs **ON** the Remarkable 2 tablet.

## Purpose

This directory contains the LD_PRELOAD injection hook and related tools that must be deployed to and executed on the RM2 device itself.

## Structure

```
Rm2/
├── src/           - Source code for injection hook
├── scripts/       - Deployment and server management scripts
└── tests/         - On-device testing utilities
```

## Requirements

- ARM cross-compiler: `arm-linux-gnueabihf-gcc`
- SSH access to RM2 device
- Root privileges on RM2

## Build

```bash
make
```

## Deploy

```bash
make deploy RM2_IP=10.11.99.1
```

## Status

⚠️ **In Development** - Coordinate system testing in progress. No production code yet.
