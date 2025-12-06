#!/bin/bash
# Complete setup: Install toolchain + build lamp
set -e

echo "=========================================="
echo "  reMarkable Cross-Compilation Setup"
echo "=========================================="
echo ""

# Step 1: Install ARM toolchain
echo "Step 1/3: Installing ARM Cross-Compiler"
echo "----------------------------------------"

if [ -d "/opt/codex" ]; then
    echo "✓ Toolchain already installed"
else
    # Try package manager first (faster)
    if command -v apt-get &> /dev/null; then
        echo "Installing via apt..."
        sudo apt-get update
        sudo apt-get install -y gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf
    elif command -v pacman &> /dev/null; then
        echo "Installing via pacman..."
        sudo pacman -S --noconfirm arm-linux-gnueabihf-gcc
    else
        echo "Package manager not recognized. Download toolchain manually:"
        echo "wget https://remarkable.engineering/oecore-x86_64-cortexa7hf-neon-toolchain-zero-gravitas-1.8-23.9.2019.sh"
        echo "./toolchain.sh -d /opt/codex -y"
        exit 1
    fi
fi

# Verify
if command -v arm-linux-gnueabihf-g++ &> /dev/null; then
    echo "✓ ARM toolchain ready: $(which arm-linux-gnueabihf-g++)"
else
    echo "❌ ARM toolchain not found!"
    exit 1
fi

echo ""

# Step 2: Install okp
echo "Step 2/3: Installing okp Compiler"
echo "----------------------------------"

if command -v okp &> /dev/null; then
    echo "✓ okp already installed: $(which okp)"
else
    # Check for Go
    if ! command -v go &> /dev/null; then
        echo "Installing Go..."
        wget -q https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
        sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
        export PATH=$PATH:/usr/local/go/bin
        export GOPATH=$HOME/go
    fi

    echo "Installing okp..."
    go install github.com/raisjn/okp@latest

    # Copy to system path
    if [ -f "$HOME/go/bin/okp" ]; then
        sudo cp $HOME/go/bin/okp /usr/local/bin/ 2>/dev/null || \
        cp $HOME/go/bin/okp ~/bin/ 2>/dev/null || \
        export PATH="$HOME/go/bin:$PATH"
    fi
fi

# Verify
if command -v okp &> /dev/null; then
    echo "✓ okp ready: $(which okp)"
else
    echo "❌ okp not found!"
    echo "Add to PATH: export PATH=\$HOME/go/bin:\$PATH"
    exit 1
fi

echo ""

# Step 3: Build lamp
echo "Step 3/3: Building lamp"
echo "-----------------------"

cd /home/user/rm2in2

if [ ! -f "build_lamp.sh" ]; then
    echo "❌ build_lamp.sh not found!"
    exit 1
fi

./build_lamp.sh

echo ""
echo "=========================================="
echo "  ✓ Setup Complete!"
echo "=========================================="
echo ""
echo "lamp is ready at: resources/repos/rmkit/src/build/lamp"
echo ""
echo "To rebuild in future:"
echo "  cd /home/user/rm2in2"
echo "  ./build_lamp.sh"
