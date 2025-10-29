#!/bin/bash
set -e

# Get version from pyproject.toml
VERSION=$(grep "^version" pyproject.toml | cut -d'"' -f2)

# Get platform info
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Package name
PACKAGE_NAME="d-v${VERSION}-${OS}-${ARCH}"

echo "📦 Packaging d-dns-debugger..."
echo "   Version: $VERSION"
echo "   Platform: $OS-$ARCH"
echo ""

# Check if binary exists
if [ ! -f "dist/d" ]; then
    echo "❌ Binary not found. Run ./build_binary.sh first"
    exit 1
fi

# Create package directory
mkdir -p "packages"

# Create tarball
echo "Creating tarball..."
cd dist
tar -czf "../packages/${PACKAGE_NAME}.tar.gz" d
cd ..

# Create checksum
echo "Creating checksum..."
shasum -a 256 "packages/${PACKAGE_NAME}.tar.gz" > "packages/${PACKAGE_NAME}.sha256"

echo ""
echo "✅ Package created successfully!"
echo ""
echo "Files created:"
echo "  - packages/${PACKAGE_NAME}.tar.gz"
echo "  - packages/${PACKAGE_NAME}.sha256"
echo ""
echo "Binary size: $(du -h dist/d | cut -f1)"
echo "Package size: $(du -h packages/${PACKAGE_NAME}.tar.gz | cut -f1)"
echo ""
echo "To share, upload these files to GitHub Releases or your distribution method of choice."
