# Makefile for rm2in2 project

.PHONY: all clean server deploy undeploy start stop status test-patterns help

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
	@echo ""
	@ls -lh $@ | awk '{print "  Size: " $$5 " bytes"}'
	@echo ""

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf Rm2/build test-output
	@echo "✓ Clean complete"

deploy: server
	@echo ""
	@./Rm2/scripts/deploy.sh $(RM2_IP)

undeploy:
	@echo "Uninstalling from RM2 at $(RM2_IP)..."
	@ssh root@$(RM2_IP) "$(RM2_INSTALL_DIR)/uninstall.sh" || echo "Uninstall script not found or failed"

# Service management shortcuts (run on RM2 via SSH)
start:
	@echo "Starting injection service on RM2..."
	@ssh root@$(RM2_IP) "$(RM2_INSTALL_DIR)/server.sh start"

stop:
	@echo "Stopping injection service on RM2..."
	@ssh root@$(RM2_IP) "$(RM2_INSTALL_DIR)/server.sh stop"

restart:
	@echo "Restarting injection service on RM2..."
	@ssh root@$(RM2_IP) "$(RM2_INSTALL_DIR)/server.sh restart"

status:
	@ssh root@$(RM2_IP) "$(RM2_INSTALL_DIR)/server.sh status"

restore:
	@echo "Restoring original configuration on RM2..."
	@ssh root@$(RM2_IP) "$(RM2_INSTALL_DIR)/server.sh restore"

test-injection:
	@echo "Testing injection system on RM2..."
	@ssh root@$(RM2_IP) "$(RM2_INSTALL_DIR)/server.sh test"

test-patterns:
	@echo "Generating test patterns..."
	@mkdir -p test-output
	@cd Rm2in2/tests && python3 test_transformations.py all ../../test-output
	@echo "✓ Test patterns generated in test-output/"
	@echo ""
	@echo "Test files created:"
	@ls -1 test-output/ | head -8
	@echo "  ... ($(shell ls test-output/ 2>/dev/null | wc -l) files total)"
	@echo ""

logs:
	@echo "Showing xochitl logs from RM2 (Ctrl+C to exit)..."
	@ssh root@$(RM2_IP) "journalctl -u xochitl -f"

help:
	@echo "rm2in2 - Remarkable 2 Input Injection"
	@echo ""
	@echo "Build Targets:"
	@echo "  make all            - Build everything (currently just server)"
	@echo "  make server         - Build injection hook for RM2"
	@echo "  make clean          - Remove build artifacts"
	@echo ""
	@echo "Deployment Targets:"
	@echo "  make deploy         - Deploy to RM2 with safety checks and backups"
	@echo "  make undeploy       - Completely remove from RM2"
	@echo ""
	@echo "Service Management (via SSH):"
	@echo "  make start          - Start injection service on RM2"
	@echo "  make stop           - Stop injection service on RM2"
	@echo "  make restart        - Restart injection service"
	@echo "  make status         - Check service status"
	@echo "  make restore        - Restore original configuration (emergency)"
	@echo "  make test-injection - Send test pattern to RM2"
	@echo ""
	@echo "Testing:"
	@echo "  make test-patterns  - Generate coordinate test patterns"
	@echo "  make logs           - View xochitl logs from RM2"
	@echo ""
	@echo "Configuration:"
	@echo "  RM2_IP=$(RM2_IP)    - Change with: make deploy RM2_IP=192.168.1.100"
	@echo ""
	@echo "Complete Workflow:"
	@echo "  1. Build and deploy:"
	@echo "       make clean && make server && make deploy"
	@echo ""
	@echo "  2. Start service:"
	@echo "       make start"
	@echo ""
	@echo "  3. Check status:"
	@echo "       make status"
	@echo ""
	@echo "  4. Generate and test patterns:"
	@echo "       make test-patterns"
	@echo "       ./Rm2in2/scripts/send.sh test-output/corners_A_Direct.txt"
	@echo ""
	@echo "  5. Stop when done:"
	@echo "       make stop"
	@echo ""
	@echo "Emergency Restore:"
	@echo "  make restore        - If something breaks, restore original config"
	@echo "  make undeploy       - Complete removal"
