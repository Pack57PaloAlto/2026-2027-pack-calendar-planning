#!/bin/bash
# Local development script for Pack 57 Calendar
# Builds the JSON from YAML and starts a local web server
#
# Usage: ./scripts/dev.sh
# Then open http://localhost:8000 in your browser

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔨 Building calendar JSON from YAML..."
python3 "$SCRIPT_DIR/build-calendar-json.py"

echo ""
echo "🌐 Starting local server at http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

cd "$PROJECT_DIR/docs"
python3 -m http.server 8000
