# Building lamp for reMarkable 3.24 (No FBInk/rm2fb)

## Quick Start

```bash
cd /home/user/rm2in2
./setup_and_build.sh
```

This will:
1. Install ARM cross-compiler
2. Install okp compiler
3. Build lamp without FBInk
4. Optionally deploy to device

---

## Manual Steps

### 1. Install ARM Toolchain

**Option A: Via Package Manager (Fastest)**
```bash
# Debian/Ubuntu
sudo apt-get install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf

# Arch
sudo pacman -S arm-linux-gnueabihf-gcc

# Verify
arm-linux-gnueabihf-g++ --version
```

**Option B: Official reMarkable Toolchain**
```bash
wget https://remarkable.engineering/oecore-x86_64-cortexa7hf-neon-toolchain-zero-gravitas-1.8-23.9.2019.sh
chmod +x oecore-*.sh
sudo ./oecore-*.sh -d /opt/codex -y
export PATH="/opt/codex/bin:$PATH"
```

### 2. Install okp Compiler

```bash
# Install Go (if not installed)
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin

# Install okp
go install github.com/raisjn/okp@latest

# Add to PATH
export PATH=$HOME/go/bin:$PATH

# Or copy to system path
sudo cp ~/go/bin/okp /usr/local/bin/
```

### 3. Build lamp

```bash
cd /home/user/rm2in2
./build_lamp.sh
```

The script will:
- Build rmkit.h
- Build STB library
- Build lamp (skipping FBInk)
- Offer to deploy to device

---

## Troubleshooting

### "okp: command not found"
```bash
export PATH=$HOME/go/bin:$PATH
# Or install to system:
sudo cp ~/go/bin/okp /usr/local/bin/
```

### "arm-linux-gnueabihf-g++: command not found"
```bash
# Install via package manager (see above)
# Or add toolchain to PATH:
export PATH="/opt/codex/bin:$PATH"
```

### Build fails with FBInk error
The `build_lamp.sh` script bypasses FBInk entirely. If you see FBInk errors:
```bash
# Don't use 'make lamp'
# Use ./build_lamp.sh instead
```

### Can't connect to device
```bash
# Check SSH access
ssh root@10.11.99.1 'echo connected'

# Update IP in build_lamp.sh if needed
export HOST=<your-rm-ip>
```

---

## Building Other rmkit Apps

Once toolchain is set up, you can build other apps:

### Build iago (shape UI)
```bash
cd /home/user/rm2in2/resources/repos/rmkit
TARGET=rm make iago
scp src/build/iago root@10.11.99.1:/opt/bin/
```

### Build genie (gestures)
```bash
TARGET=rm make genie
scp src/build/genie root@10.11.99.1:/opt/bin/
```

### Build remux (app launcher)
```bash
TARGET=rm make remux
scp src/build/remux root@10.11.99.1:/opt/bin/
```

**Note:** All these work WITHOUT rm2fb/FBInk on 3.24 (may show warning but function correctly)

---

## Why No FBInk?

- FBInk is a text rendering library (separate from rm2fb)
- It's **optional** for rmkit apps
- lamp doesn't use it (only draws shapes via input events)
- Skipping it avoids build complexity

---

## Next Steps

After building lamp:

1. **Test basic functionality**
   ```bash
   ssh root@10.11.99.1 'echo "pen circle 700 900 100 100" | lamp'
   ```

2. **Build symbol library**
   - Create files like `resistor.lamp` with commands
   - Use genie gestures to trigger them

3. **Consider building iago**
   - Provides actual UI for shape insertion
   - Works on 3.24 without rm2fb

4. **Build custom toolbar**
   - Fork iago source
   - Add electrical symbols
   - Customize UI
