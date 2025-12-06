# RM2 Backup and Cleanup Strategy

**Date:** December 4, 2024  
**Goal:** Clean slate for production development

---

## Current State Assessment

**What's on your RM2 now:**
- ✅ Firmware 3.24.0.147 (beta, working with direct write)
- ❓ Old rm2in2 deployment (LD_PRELOAD version)
- ❓ Test files and artifacts
- ❓ System modifications (systemd overrides, etc.)

**What needs backup:**
- Your notebook files (.rm format)
- Any custom templates
- SSH keys (if customized)
- System configuration (if modified)

---

## Comprehensive Backup Plan

### Step 1: Backup Notebooks and Documents

```bash
#!/bin/bash
# backup-documents.sh

BACKUP_DIR="rm2-backup-$(date +%Y%m%d-%H%M%S)"
RM_IP="10.11.99.1"

mkdir -p "$BACKUP_DIR"

echo "=== Backing up reMarkable documents ==="

# Backup entire xochitl directory
echo "Backing up notebooks and metadata..."
scp -r "root@${RM_IP}:/home/root/.local/share/remarkable/xochitl" \
    "$BACKUP_DIR/xochitl-backup/"

# Backup templates
echo "Backing up templates..."
scp -r "root@${RM_IP}:/usr/share/remarkable/templates" \
    "$BACKUP_DIR/templates/"

# Backup custom templates (if any)
if ssh "root@${RM_IP}" "[ -d /home/root/.local/share/remarkable/templates ]"; then
    scp -r "root@${RM_IP}:/home/root/.local/share/remarkable/templates" \
        "$BACKUP_DIR/custom-templates/"
fi

# Backup SSH keys
echo "Backing up SSH configuration..."
scp -r "root@${RM_IP}:/home/root/.ssh" \
    "$BACKUP_DIR/ssh-backup/"

# Document count
NOTEBOOK_COUNT=$(ssh "root@${RM_IP}" "ls -1 /home/root/.local/share/remarkable/xochitl/*.metadata 2>/dev/null | wc -l")
echo "Backed up $NOTEBOOK_COUNT notebooks"

echo "Backup complete: $BACKUP_DIR"
```

### Step 2: Document Current System State

```bash
#!/bin/bash
# document-system.sh

BACKUP_DIR="$1"
RM_IP="10.11.99.1"

echo "=== Documenting system state ==="

# Firmware version
ssh "root@${RM_IP}" "cat /etc/version" > "$BACKUP_DIR/firmware-version.txt"

# Installed packages (if any)
ssh "root@${RM_IP}" "opkg list-installed 2>/dev/null || echo 'No opkg'" > "$BACKUP_DIR/installed-packages.txt"

# Running processes
ssh "root@${RM_IP}" "ps aux" > "$BACKUP_DIR/processes.txt"

# Systemd services
ssh "root@${RM_IP}" "systemctl list-units --type=service" > "$BACKUP_DIR/services.txt"

# Network configuration
ssh "root@${RM_IP}" "ifconfig" > "$BACKUP_DIR/network.txt"

# Disk usage
ssh "root@${RM_IP}" "df -h" > "$BACKUP_DIR/disk-usage.txt"

# Input devices
ssh "root@${RM_IP}" "ls -l /dev/input/" > "$BACKUP_DIR/input-devices.txt"

# Custom modifications
ssh "root@${RM_IP}" "find /home/root -type f -name '*.so'" > "$BACKUP_DIR/custom-libraries.txt"
ssh "root@${RM_IP}" "systemctl show xochitl" > "$BACKUP_DIR/xochitl-service.txt"

echo "System documentation complete"
```

### Step 3: Backup rm2in2 Deployment

```bash
#!/bin/bash
# backup-rm2in2.sh

BACKUP_DIR="$1"
RM_IP="10.11.99.1"

echo "=== Backing up rm2in2 deployment ==="

mkdir -p "$BACKUP_DIR/rm2in2-old"

# Check for inject_hook.so
if ssh "root@${RM_IP}" "[ -f /opt/inject_hook.so ]"; then
    scp "root@${RM_IP}:/opt/inject_hook.so" "$BACKUP_DIR/rm2in2-old/"
fi

# Check for server script
if ssh "root@${RM_IP}" "[ -f /opt/rm2_inject_server.sh ]"; then
    scp "root@${RM_IP}:/opt/rm2_inject_server.sh" "$BACKUP_DIR/rm2in2-old/"
fi

# Check for FIFO
if ssh "root@${RM_IP}" "[ -p /tmp/rm2_inject ]"; then
    echo "/tmp/rm2_inject (FIFO exists)" > "$BACKUP_DIR/rm2in2-old/fifo-status.txt"
fi

# Check for systemd override
if ssh "root@${RM_IP}" "[ -d /etc/systemd/system/xochitl.service.d ]"; then
    scp -r "root@${RM_IP}:/etc/systemd/system/xochitl.service.d" \
        "$BACKUP_DIR/rm2in2-old/"
fi

# Check for any test files
ssh "root@${RM_IP}" "find /opt -name 'lamp-test*' -o -name '*inject*' -o -name '*rm2*'" \
    > "$BACKUP_DIR/rm2in2-old/deployed-files.txt"

echo "rm2in2 backup complete"
```

### Step 4: Full Backup Script

```bash
#!/bin/bash
# full-backup.sh

set -e

RM_IP="10.11.99.1"
BACKUP_DIR="rm2-backup-$(date +%Y%m%d-%H%M%S)"

echo "=== Full RM2 Backup ==="
echo "Target: root@${RM_IP}"
echo "Backup directory: $BACKUP_DIR"
echo ""

# Check connectivity
if ! ssh "root@${RM_IP}" "echo 'Connected'" >/dev/null 2>&1; then
    echo "ERROR: Cannot connect to RM2 at ${RM_IP}"
    exit 1
fi

mkdir -p "$BACKUP_DIR"

# Run backup steps
./backup-documents.sh "$BACKUP_DIR"
./document-system.sh "$BACKUP_DIR"
./backup-rm2in2.sh "$BACKUP_DIR"

# Create manifest
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
reMarkable 2 Backup
==================
Date: $(date)
Firmware: $(ssh "root@${RM_IP}" "cat /etc/version")

Contents:
- xochitl-backup/      : All notebooks and metadata
- templates/           : System templates
- custom-templates/    : User templates (if any)
- ssh-backup/          : SSH keys and config
- rm2in2-old/          : Old rm2in2 deployment
- *.txt                : System state documentation

Restoration:
1. Transfer xochitl-backup contents back to device
2. Reinstall any custom templates
3. Restore SSH keys if needed
4. Redeploy rm2in2 (new version)
EOF

# Create archive
echo ""
echo "Creating compressed archive..."
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"

echo ""
echo "=== Backup Complete ==="
echo "Directory: $BACKUP_DIR"
echo "Archive: ${BACKUP_DIR}.tar.gz"
echo "Size: $(du -sh "${BACKUP_DIR}.tar.gz" | cut -f1)"
echo ""
echo "Store this archive safely before cleanup!"
```

---

## Cleanup Plan

### Step 1: Remove Old rm2in2 Deployment

```bash
#!/bin/bash
# cleanup-rm2in2-old.sh

RM_IP="10.11.99.1"

echo "=== Removing old rm2in2 deployment ==="

# Remove inject_hook.so
ssh "root@${RM_IP}" "rm -f /opt/inject_hook.so"

# Remove server script
ssh "root@${RM_IP}" "rm -f /opt/rm2_inject_server.sh"

# Remove FIFO
ssh "root@${RM_IP}" "rm -f /tmp/rm2_inject"

# Remove systemd override
ssh "root@${RM_IP}" "rm -rf /etc/systemd/system/xochitl.service.d"

# Reload systemd
ssh "root@${RM_IP}" "systemctl daemon-reload"

# Remove test files
ssh "root@${RM_IP}" "rm -f /opt/lamp-test*"

# Remove any other rm2in2 artifacts
ssh "root@${RM_IP}" "find /opt -name '*rm2inject*' -delete"
ssh "root@${RM_IP}" "find /tmp -name '*rm2*' -delete"

echo "Old rm2in2 deployment removed"
echo "xochitl service restored to default"
```

### Step 2: Clean Test Data

```bash
#!/bin/bash
# cleanup-test-data.sh

RM_IP="10.11.99.1"

echo "=== Cleaning test notebooks ==="

# List test notebooks (be careful!)
ssh "root@${RM_IP}" "cd /home/root/.local/share/remarkable/xochitl && ls -lh *.metadata | head -20"

echo ""
echo "WARNING: This will delete notebooks!"
echo "Make sure you have backups!"
read -p "Continue? (type 'yes'): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted"
    exit 0
fi

# You'll need to identify test notebook UUIDs manually
# Example:
# ssh "root@${RM_IP}" "cd /home/root/.local/share/remarkable/xochitl && rm -f test-uuid.*"

echo "Manual cleanup required - identify test notebook UUIDs"
```

### Step 3: Verify Clean State

```bash
#!/bin/bash
# verify-clean.sh

RM_IP="10.11.99.1"

echo "=== Verifying clean state ==="

echo "Checking for rm2in2 artifacts..."
ssh "root@${RM_IP}" "find /opt /tmp -name '*rm2*' -o -name '*inject*'" || echo "None found ✓"

echo "Checking systemd overrides..."
ssh "root@${RM_IP}" "[ -d /etc/systemd/system/xochitl.service.d ] && echo 'Override exists!' || echo 'Clean ✓'"

echo "Checking xochitl status..."
ssh "root@${RM_IP}" "systemctl status xochitl | head -10"

echo ""
echo "Clean state verification complete"
```

---

## Restoration Plan (If Needed)

```bash
#!/bin/bash
# restore-backup.sh

BACKUP_ARCHIVE="$1"

if [ -z "$BACKUP_ARCHIVE" ]; then
    echo "Usage: $0 <backup-archive.tar.gz>"
    exit 1
fi

RM_IP="10.11.99.1"

echo "=== Restoring from backup ==="
echo "Archive: $BACKUP_ARCHIVE"
echo ""

# Extract archive
tar -xzf "$BACKUP_ARCHIVE"
BACKUP_DIR="${BACKUP_ARCHIVE%.tar.gz}"

# Stop xochitl
ssh "root@${RM_IP}" "systemctl stop xochitl"

# Restore notebooks
echo "Restoring notebooks..."
scp -r "$BACKUP_DIR/xochitl-backup/"* \
    "root@${RM_IP}:/home/root/.local/share/remarkable/xochitl/"

# Restore templates
echo "Restoring templates..."
if [ -d "$BACKUP_DIR/custom-templates" ]; then
    scp -r "$BACKUP_DIR/custom-templates/"* \
        "root@${RM_IP}:/home/root/.local/share/remarkable/templates/"
fi

# Restore SSH keys
echo "Restoring SSH keys..."
scp -r "$BACKUP_DIR/ssh-backup/"* \
    "root@${RM_IP}:/home/root/.ssh/"

# Restart xochitl
ssh "root@${RM_IP}" "systemctl start xochitl"

echo ""
echo "Restoration complete!"
echo "Check your RM2 to verify notebooks are present"
```

---

## Recommended Execution Order

```bash
# 1. Create backup
chmod +x full-backup.sh backup-*.sh document-system.sh
./full-backup.sh

# 2. Verify backup
ls -lh rm2-backup-*.tar.gz
tar -tzf rm2-backup-*.tar.gz | head -20

# 3. Store backup safely
cp rm2-backup-*.tar.gz /safe/location/
# Or upload to cloud storage

# 4. Clean old deployment
chmod +x cleanup-rm2in2-old.sh
./cleanup-rm2in2-old.sh

# 5. Verify clean state
chmod +x verify-clean.sh
./verify-clean.sh

# 6. Ready for new development!
```

---

## Safety Checklist

Before cleanup:
- [ ] Backup created successfully
- [ ] Backup archive verified (can extract)
- [ ] Backup stored in safe location
- [ ] Backup includes all notebooks
- [ ] System state documented
- [ ] Old deployment documented

After cleanup:
- [ ] No rm2in2 artifacts remain
- [ ] xochitl runs normally
- [ ] Can create/edit notebooks normally
- [ ] No systemd overrides active
- [ ] Clean state verified

---

## Firmware Update Decision Tree

```
Current: 3.24.0.147 working
New: 3.24.0.179 available

Option 1: STAY (Recommended)
  ✓ Develop production system on known-working firmware
  ✓ No unknown variables during debugging
  ✓ Update after system is stable
  Risk: Miss new features temporarily
  
Option 2: UPDATE NOW
  ✓ Latest features
  ✓ Potential bug fixes
  Risk: Breaks direct write (unlikely but possible)
  Risk: Changes gesture recognition (toolbar drag issue)
  Risk: Unknown regressions in beta
  
Option 3: DUAL BOOT (Advanced)
  ✓ Install rm-version-switcher
  ✓ Keep 0.147 and install 0.179
  ✓ Switch between versions
  Risk: Violates beta EULA
  Risk: Adds complexity
  Risk: Potential soft-brick if misused
```

**My recommendation:** STAY on 0.147 until your circuit injection tool works. Then update and adapt if needed.

---

## Summary

**Backup strategy:**
1. Full document backup (notebooks, templates, SSH)
2. System state documentation
3. Old deployment archive
4. Compressed archive stored safely

**Cleanup strategy:**
1. Remove old LD_PRELOAD deployment
2. Remove systemd overrides
3. Clean test artifacts
4. Verify clean state

**Firmware decision:**
- Stay on 0.147 for now
- Develop production system
- Update to 0.179 after stability proven
- Or use rm-version-switcher for dual boot (risky)

**Next step:** Run backup, verify, then clean. Fresh slate for production development.
