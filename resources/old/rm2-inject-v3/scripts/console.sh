#!/bin/bash
# Console launcher - updated for bash version

if [ -z "$1" ]; then
    echo "Usage: console.sh <rm2_ip>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

exec bash "$PROJECT_ROOT/tools/console.sh" "$1"
