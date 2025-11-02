#!/bin/bash

# Build script for D DNS Debugger - macOS binaries
# Builds universal binary (x86_64 + arm64) with native Tauri DMG bundling

set -e

echo "🔨 Building D DNS Debugger for macOS..."
echo ""

# Check if Rust targets are installed
echo "🔍 Checking Rust targets..."
if ! rustup target list | grep -q "aarch64-apple-darwin (installed)"; then
    echo "📥 Installing aarch64-apple-darwin target..."
    rustup target add aarch64-apple-darwin
fi

if ! rustup target list | grep -q "x86_64-apple-darwin (installed)"; then
    echo "📥 Installing x86_64-apple-darwin target..."
    rustup target add x86_64-apple-darwin
fi

echo "✅ Rust targets ready"
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf src-tauri/target/universal-apple-darwin/release/bundle
rm -rf dist
mkdir -p dist

echo ""
echo "📦 Building universal binary (Intel + Apple Silicon)..."
echo "   This may take a few minutes..."
echo ""

# Build universal binary with app bundle (skip DMG as it can be flaky)
npm run tauri build -- --target universal-apple-darwin --bundles app

# Copy outputs to dist directory
echo ""
echo "📋 Copying build artifacts to dist/..."

# Copy .app bundle
if [ -d "src-tauri/target/universal-apple-darwin/release/bundle/macos/D.app" ]; then
    cp -r src-tauri/target/universal-apple-darwin/release/bundle/macos/D.app dist/
    echo "   ✓ D.app"
fi

# Create DMG manually using hdiutil (more reliable than Tauri's bundler)
echo ""
echo "💿 Creating DMG installer..."
if [ -d "dist/D.app" ]; then
    # Create a temporary directory for DMG contents
    DMG_DIR=$(mktemp -d)
    cp -r dist/D.app "$DMG_DIR/"

    # Create DMG
    hdiutil create -volname "D DNS Debugger" \
        -srcfolder "$DMG_DIR" \
        -ov -format UDZO \
        dist/D_0.2.0_universal.dmg

    # Clean up temp directory
    rm -rf "$DMG_DIR"
    echo "   ✓ DMG installer created"
else
    echo "   ⚠️  D.app not found, skipping DMG creation"
fi

# Create a versioned zip archive
echo ""
echo "🗜️  Creating ZIP archive..."
cd dist
if [ -d "D.app" ]; then
    zip -r -q D-macos-universal.zip D.app
    echo "   ✓ ZIP archive created"
fi
cd ..

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Output files in dist/:"
ls -lh dist/ | grep -v "^total" | awk '{print "   - " $9 " (" $5 ")"}'
echo ""
echo "🚀 Installation options:"
echo "   1. Double-click dist/D_0.2.0_universal.dmg to install via DMG"
echo "   2. Copy dist/D.app to /Applications manually"
echo "   3. Distribute dist/D-macos-universal.zip"
echo ""
