# Makefile for rm2in2 project

.PHONY: all clean server client deploy help test

# Configuration
CC := arm-linux-gnueabihf-gcc
CFLAGS := -shared -fPIC -O2 -Wall -Wextra
LDFLAGS := -ldl -lpthread
RM2_IP := 10.11.99.1
RM2_INSTALL_DIR := /opt/rm2in2

# Targets
all: server

server: Rm2/build/inject.so

Rm2/build/inject.so: Rm2/src/inject.c
	@echo "Building injection hook..."
	@mkdir -p Rm2/build
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)
	@echo "✓ Built: $@"

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf Rm2/build
	@echo "✓ Clean complete"

deploy: server
	@echo "Deploying to RM2 at $(RM2_IP)..."
	@echo "  Creating directory: $(RM2_INSTALL_DIR)"
	@ssh root@$(RM2_IP) "mkdir -p $(RM2_INSTALL_DIR)"
	@echo "  Copying inject.so..."
	@scp Rm2/build/inject.so root@$(RM2_IP):$(RM2_INSTALL_DIR)/
	@echo "  Copying server scripts..."
	@scp Rm2/scripts/*.sh root@$(RM2_IP):$(RM2_INSTALL_DIR)/
	@ssh root@$(RM2_IP) "chmod +x $(RM2_INSTALL_DIR)/*.sh"
	@echo ""
	@echo "✓ Deployment complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. SSH to RM2: ssh root@$(RM2_IP)"
	@echo "  2. Stop xochitl: systemctl stop xochitl"
	@echo "  3. Start with hook: LD_PRELOAD=$(RM2_INSTALL_DIR)/inject.so /usr/bin/xochitl &"
	@echo "  4. Send commands: cat commands.txt > /tmp/rm2_inject"

test-patterns:
	@echo "Generating test patterns..."
	@mkdir -p test-output
	@cd Rm2in2/tests && python test_transformations.py all ../../test-output
	@echo "✓ Test patterns generated in test-output/"

help:
	@echo "rm2in2 - Remarkable 2 Input Injection"
	@echo ""
	@echo "Targets:"
	@echo "  make all         - Build everything (currently just server)"
	@echo "  make server      - Build injection hook for RM2"
	@echo "  make clean       - Remove build artifacts"
	@echo "  make deploy      - Deploy to RM2 device"
	@echo "  make test-patterns - Generate coordinate test patterns"
	@echo "  make help        - Show this help"
	@echo ""
	@echo "Configuration:"
	@echo "  RM2_IP=$(RM2_IP)"
	@echo ""
	@echo "Example workflow:"
	@echo "  make clean"
	@echo "  make server"
	@echo "  make deploy RM2_IP=10.11.99.1"
	@echo "  make test-patterns"
