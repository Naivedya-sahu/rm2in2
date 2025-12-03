# Deployment Guide

Complete guide for deploying and managing the RM2 injection system.

## Overview

The deployment system uses a **service-based approach** with:
- ✅ Systemd service override (clean integration)
- ✅ Automatic backups before deployment
- ✅ Safety checks and validation
- ✅ Easy start/stop/restore operations
- ✅ Complete rollback capability

## Prerequisites

### On PC/Workstation
- ARM cross-compiler: `arm-linux-gnueabihf-gcc`
- SSH access to RM2 configured
- Make and standard build tools

### On RM2
- SSH enabled (default on RM2)
- Root access (default password: no password)
- Sufficient space in `/opt` (~1MB needed)

## Quick Start

### 1. Build
```bash
make clean
make server
```

This creates `Rm2/build/inject.so` (~15KB).

### 2. Deploy
```bash
make deploy RM2_IP=10.11.99.1
```

This will:
- Test connectivity
- Check for existing installation
- Create backups
- Deploy files to `/opt/rm2in2/`
- Set up uninstall script
- Show next steps

### 3. Start Service
```bash
make start
```

Or manually on RM2:
```bash
ssh root@10.11.99.1
/opt/rm2in2/server.sh start
```

### 4. Check Status
```bash
make status
```

### 5. Test
```bash
make test-patterns
./Rm2in2/scripts/send.sh test-output/corners_A_Direct.txt
```

## Detailed Deployment Process

### Build Phase

```bash
make server
```

**What it does:**
- Compiles `Rm2/src/inject.c` using ARM cross-compiler
- Creates shared library with LD_PRELOAD hooks
- Outputs to `Rm2/build/inject.so`

**Compiler flags:**
- `-shared -fPIC` - Create position-independent shared library
- `-O2` - Optimize for performance
- `-Wall -Wextra` - Enable all warnings
- `-ldl -lpthread` - Link dynamic loader and threading libs

### Deployment Phase

```bash
make deploy
# Or with custom IP:
make deploy RM2_IP=192.168.1.100
```

**What it does:**

1. **Prerequisites Check**
   - Verifies inject.so exists locally
   - Checks all required scripts present

2. **Connectivity Test**
   - Tests SSH connection to RM2
   - Provides troubleshooting if fails

3. **Existing Installation Check**
   - Checks if already installed
   - Prompts to stop running service
   - Offers to continue or abort

4. **Backup Creation**
   - Backs up old inject.so (timestamped)
   - Backs up old scripts
   - Stores in `/opt/rm2in2/backup/`

5. **File Deployment**
   - Copies inject.so to RM2
   - Copies server.sh (service manager)
   - Copies capture_pen_events.sh (optional)
   - Sets correct permissions

6. **Verification**
   - Checks files exist on RM2
   - Verifies file sizes match
   - Ensures no corruption

7. **Uninstall Script Creation**
   - Generates `/opt/rm2in2/uninstall.sh`
   - Provides complete removal capability

## Service Management

The injection system uses **systemd service override** for clean integration.

### How It Works

1. Creates `/etc/systemd/system/xochitl.service.d/rm2in2.conf`
2. Sets `Environment="LD_PRELOAD=/opt/rm2in2/inject.so"`
3. Reloads systemd configuration
4. Restarts xochitl service

This approach:
- ✅ Integrates with system services
- ✅ Survives reboots (if you want)
- ✅ Clean enable/disable
- ✅ Proper cleanup
- ✅ Easy restoration

### Start Service

```bash
make start
```

**What happens:**
1. Checks prerequisites (files exist)
2. Creates backup of current config
3. Creates systemd override
4. Reloads systemd
5. Restarts xochitl with LD_PRELOAD
6. Verifies FIFO creation
7. Shows status

**Output:**
```
✓ Service started successfully
✓ Injection hook is active (FIFO created)

Status: ACTIVE
FIFO:   /tmp/rm2_inject

To send commands:
  cat commands.txt > /tmp/rm2_inject
```

### Stop Service

```bash
make stop
```

**What happens:**
1. Stops xochitl
2. Removes systemd override
3. Reloads systemd
4. Restarts xochitl normally
5. Cleans up FIFO

**Result:** RM2 returns to normal operation.

### Check Status

```bash
make status
```

**Shows:**
- Xochitl service status (ACTIVE/INACTIVE)
- Injection override status (ENABLED/NOT ENABLED)
- Injection library status (file info)
- FIFO status (ACTIVE/NOT FOUND)
- LD_PRELOAD configuration
- Recent logs (last 5 lines)

### Restart Service

```bash
make restart
```

Equivalent to `make stop && make start`.

## Emergency Procedures

### Restore Original Configuration

If something breaks:

```bash
make restore
```

**What it does:**
1. Stops xochitl immediately
2. Removes our systemd override
3. Restores backed-up config (if exists)
4. Reloads systemd
5. Starts xochitl normally
6. Cleans up temporary files

**Use when:**
- Service won't start
- xochitl is crashing
- Screen is unresponsive
- Need to get back to working state ASAP

### Complete Uninstallation

```bash
make undeploy
```

Or manually on RM2:
```bash
ssh root@10.11.99.1
/opt/rm2in2/uninstall.sh
```

**What it does:**
1. Stops injection service
2. Restores original xochitl service
3. Removes ALL installed files
4. Cleans up systemd overrides
5. Removes installation directory

**Result:** Complete removal, as if never installed.

## File Locations

### On RM2

```
/opt/rm2in2/
├── inject.so               - Injection library
├── server.sh               - Service manager
├── capture_pen_events.sh   - Pen capture tool (optional)
├── uninstall.sh            - Uninstaller (auto-generated)
└── backup/                 - Backup directory
    ├── inject.so.YYYYMMDD_HHMMSS
    ├── server.sh.YYYYMMDD_HHMMSS
    └── rm2in2.conf.bak

/etc/systemd/system/xochitl.service.d/
└── rm2in2.conf            - Systemd override (when active)

/tmp/
└── rm2_inject             - FIFO for commands (when running)
```

### On PC

```
rm2in2/
├── Rm2/
│   ├── build/inject.so    - Compiled library
│   ├── src/inject.c       - Source code
│   └── scripts/
│       ├── deploy.sh      - Deployment script
│       ├── server.sh      - Service manager (template)
│       └── capture_pen_events.sh - Capture tool
├── Rm2in2/
│   └── scripts/send.sh    - Command sender
└── test-output/           - Generated test patterns
```

## Troubleshooting

### Deployment Issues

**"Cannot connect to RM2"**
- Check USB cable connection
- Verify IP address: Settings > Help on RM2
- Test: `ssh root@<IP>`
- Try ping: `ping <IP>`

**"inject.so not found"**
- Run `make server` first
- Check build output for errors
- Verify ARM cross-compiler installed

**"File size mismatch"**
- Network issue during transfer
- Try deployment again
- Check available space on RM2: `df -h`

### Service Issues

**"FIFO not found"**
- Service may not have started
- Check logs: `make logs`
- Try restart: `make restart`
- Check status: `make status`

**"Service failed to start"**
- View errors: `make logs`
- Restore and retry: `make restore && make start`
- Check inject.so permissions
- Verify systemd override syntax

**"xochitl crashes immediately"**
- Emergency restore: `make restore`
- Check compatibility
- View crash logs: `journalctl -u xochitl -n 50`

### Testing Issues

**"No drawing appears"**
- Open notes app first
- Tap screen to trigger redraw
- Check FIFO: `make status`
- View logs: `make logs`

**"Commands sent but wrong output"**
- This is expected during coordinate testing!
- Try different transformations
- See TESTING_GUIDE.md

## Makefile Commands Reference

### Build
- `make server` - Build injection hook
- `make clean` - Remove build artifacts

### Deployment
- `make deploy` - Deploy to RM2 with safety checks
- `make undeploy` - Complete removal from RM2

### Service Management
- `make start` - Start injection service
- `make stop` - Stop injection service
- `make restart` - Restart injection service
- `make status` - Check service status
- `make restore` - Emergency restore original config

### Testing
- `make test-patterns` - Generate coordinate test patterns
- `make test-injection` - Send test dot to center
- `make logs` - View xochitl logs (live)

### Help
- `make help` - Show all available commands

## Best Practices

### Before Deployment
1. ✅ Build and verify locally first
2. ✅ Have RM2 plugged in and accessible
3. ✅ Close important documents on RM2
4. ✅ Know your RM2 IP address

### During Development
1. ✅ Use `make status` frequently
2. ✅ Keep `make logs` running in separate terminal
3. ✅ Stop service when done testing
4. ✅ Don't leave service running overnight

### After Testing
1. ✅ Run `make stop` to restore normal operation
2. ✅ Backups are kept in `/opt/rm2in2/backup/`
3. ✅ Can easily restart later with `make start`

### Emergency
1. 🚨 If anything breaks: `make restore`
2. 🚨 If restore fails: SSH to RM2 and reboot
3. 🚨 If all else fails: `make undeploy` and start over

## Security Considerations

- ⚠️ This modifies system services on your RM2
- ⚠️ Requires root access
- ⚠️ LD_PRELOAD can interfere with other processes
- ⚠️ Always use `make stop` when not testing
- ⚠️ Keep backups of important documents

## Next Steps

After successful deployment:

1. **Test the service:** `make test-injection`
2. **Generate test patterns:** `make test-patterns`
3. **Start coordinate testing:** See TESTING_GUIDE.md
4. **Find correct transformation:** Test all 8 variants
5. **Update inject.c:** With verified formula
6. **Build conversion tools:** After coordinate system is verified

---

For coordinate system testing, see: **TESTING_GUIDE.md**

For development details, see: **PROJECT_STATUS.md**
