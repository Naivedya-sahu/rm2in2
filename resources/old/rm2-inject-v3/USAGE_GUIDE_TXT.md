# How to Use Your TXT File with RM2 Injection System

## Your System Uses Three Commands:

Your `inject_hook.c` accepts these commands via `/tmp/lamp_inject` FIFO:

```
PEN_DOWN x y    # Move to position and press pen down
PEN_MOVE x y    # Move pen to position (while down)
PEN_UP          # Lift pen up
```

## Your TXT File Format:

Your `test.txt` uses:
```
M x y    # Move (pen up)
D x y    # Draw (pen down)
```

## ⚠️ FORMAT MISMATCH ISSUE

Your `test.txt` format (`M`/`D`) does NOT match what `inject_hook.c` expects (`PEN_DOWN`/`PEN_MOVE`/`PEN_UP`).

## Solution: Convert TXT to Injection Commands

I'll create a script that reads your `M`/`D` format and sends proper `PEN_*` commands.

---

## USAGE: Method 1 - Direct File Injection (RECOMMENDED)

### Step 1: Deploy to RM2 (if not done yet)

```bash
cd C:\Users\NAVY\Documents\Arduino\rm2-inject-v3

# Build (if needed)
bash scripts/build.sh

# Deploy to RM2
bash scripts/deploy.sh 10.11.99.1
```

### Step 2: Start Server on RM2

```bash
# SSH into RM2
ssh root@10.11.99.1

# Start injection server
/opt/rm2-inject/server.sh start

# Verify it's running
/opt/rm2-inject/server.sh status
```

You should see:
```
Server: RUNNING (PID: xxxx)
Xochitl: RUNNING (PID: xxxx)
Hook: LOADED ✓
FIFO: EXISTS ✓
```

### Step 3: Prepare RM2 Device

**On the RM2 tablet (physical device):**
1. Open a notebook in Xochitl
2. Select **Fineliner** tool
3. Choose pen thickness (thin/medium/thick)
4. Tap pen on screen where you want drawing to start
5. **Keep pen lifted** - don't draw anything

### Step 4: Inject Your Drawing

**Back on your PC:**

```bash
cd C:\Users\NAVY\Documents\Arduino\rm2-inject-v3

# Use the injection script I'll create
bash scripts/inject_file.sh test.txt 10.11.99.1
```

---

## USAGE: Method 2 - Interactive Console

### Step 1: Start Console

```bash
cd C:\Users\NAVY\Documents\Arduino\rm2-inject-v3
bash scripts/console.sh 10.11.99.1
```

### Step 2: Use Console Commands

```
RM2 Injection Console - Connected to 10.11.99.1
Type 'help' for commands

> status          # Check if server is running
> inject test.txt 100 200    # Inject file at position
> quit
```

---

## I'll Create the Missing Script

Your system is almost complete, but you need a script to convert your `M`/`D` format to `PEN_*` commands and send them via the FIFO.

Creating `scripts/inject_file.sh` now...
