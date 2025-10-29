#!/bin/bash
set -e

echo "🚀 d-dns-debugger - Complete Build & Package Script"
echo "=================================================="
echo ""

# Step 1: Build the binary
echo "Step 1: Building binary..."
./build_binary.sh

# Step 2: Package the binary
echo ""
echo "Step 2: Creating distribution package..."
./package.sh

echo ""
echo "=================================================="
echo "✅ All done! Your distributable package is ready."
echo ""
echo "📁 Distribution files:"
echo "   - dist/d (binary)"
echo "   - packages/d-v*.tar.gz (packaged binary)"
echo "   - packages/d-v*.sha256 (checksum)"
echo ""
echo "📖 Share BINARY_INSTALL.md with end users for installation instructions"
echo ""
