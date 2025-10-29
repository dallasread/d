#!/bin/bash
set -e

echo "🔨 Building d-dns-debugger binary..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  No virtual environment found. Creating one...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install -q --upgrade pip setuptools wheel
pip install -q -e ".[dev]"

# Clean previous builds (but keep the spec file)
echo "🧹 Cleaning previous builds..."
rm -rf build dist 2>/dev/null || true

# Run PyInstaller
echo "🔧 Running PyInstaller..."
pyinstaller d.spec

# Check if build was successful
if [ -f "dist/d" ]; then
    echo ""
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo ""
    echo "Binary location: dist/d"
    echo "Binary size: $(du -h dist/d | cut -f1)"
    echo ""
    echo "To test the binary, run:"
    echo "  ./dist/d example.com"
    echo ""
    echo "To install system-wide (optional):"
    echo "  sudo cp dist/d /usr/local/bin/"
    echo ""
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi
