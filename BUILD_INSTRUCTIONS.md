# Building D DNS Debugger

This document explains how to build the D DNS Debugger as a macOS application.

## Overview

The project uses **Tauri** to bundle the Vue.js frontend with a Rust backend into a native macOS application.

## Prerequisites

### Required Tools
- **Node.js** (v16 or later)
- **Rust** (latest stable)
- **Xcode Command Line Tools** (macOS only)

### Install Dependencies

```bash
# Install Node dependencies
npm install

# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## Quick Start

### Development Build
```bash
# Run in development mode
npm run tauri dev
```

### Production Build
```bash
# Build for current architecture (Apple Silicon or Intel)
npm run tauri build
```

This will:
1. Build the Vue.js frontend with Vite
2. Compile the Rust backend
3. Create a macOS application bundle (.app)
4. Create a DMG installer (if successful)

### Build Output

After building, you'll find:
- `src-tauri/target/release/bundle/macos/D.app` - Application bundle
- `src-tauri/target/release/bundle/dmg/D_*.dmg` - DMG installer (if created)

## Creating a DMG Installer

If Tauri's automatic DMG creation fails, create it manually:

```bash
# Copy app bundle to dist
mkdir -p dist
cp -r src-tauri/target/release/bundle/macos/D.app dist/

# Create DMG
DMG_DIR=$(mktemp -d)
cp -r dist/D.app "$DMG_DIR/"
hdiutil create -volname "D DNS Debugger v0.2.1" \
  -srcfolder "$DMG_DIR" \
  -ov -format UDZO \
  dist/D_v0.2.1_aarch64.dmg
rm -rf "$DMG_DIR"

echo "DMG created at dist/D_v0.2.1_aarch64.dmg"
```

## How It Works

### Tauri Build Process

1. **Frontend Build**: Vite compiles the Vue.js application
   - TypeScript compilation
   - Asset optimization
   - CSS processing
   - Output to `dist/` directory

2. **Rust Compilation**: Cargo builds the Tauri backend
   - Compiles Rust code from `src-tauri/`
   - Links with system frameworks
   - Bundles the web assets

3. **App Bundling**: Creates macOS application bundle
   - Packages executable and resources
   - Creates Info.plist
   - Adds icon and metadata

4. **DMG Creation**: Creates disk image installer (optional)
   - Uses macOS `hdiutil` tool
   - Creates mountable disk image
   - Optimized for distribution

### Project Structure

```
d/
├── src/                    # Vue.js frontend
│   ├── components/         # Vue components
│   ├── stores/            # Pinia state management
│   └── main.ts            # Entry point
├── src-tauri/             # Rust backend
│   ├── src/
│   │   ├── main.rs        # Tauri entry point
│   │   ├── adapters/      # DNS, HTTP, WHOIS, etc.
│   │   └── models/        # Data models
│   ├── Cargo.toml         # Rust dependencies
│   └── tauri.conf.json    # Tauri configuration
├── package.json           # Node.js dependencies
└── vite.config.ts         # Vite configuration
```

## Testing the Application

```bash
# Run in development mode (live reload)
npm run tauri dev

# Test the built application
open dist/D.app

# Or from the target directory
open src-tauri/target/release/bundle/macos/D.app
```

## Distribution

### What to Distribute

For GitHub releases, distribute:
- **DMG Installer**: `D_v0.2.1_aarch64.dmg` (~4MB)
  - Easy installation for users
  - Double-click to mount, drag to Applications
  
**Alternative:**
- **Application Bundle**: `D.app`
  - Can be zipped for distribution
  - Users copy directly to Applications

### Installation Methods

**Method 1: DMG Installer (Recommended)**
```bash
# User downloads DMG
# Double-click to mount
# Drag D.app to Applications folder
# Eject DMG
```

**Method 2: Direct App Bundle**
```bash
# User downloads D.app.zip
# Unzip
# Copy D.app to /Applications
```

### GitHub Releases

See `GITHUB_RELEASE_STEPS.md` for detailed release instructions.

Quick steps:
1. Build for the release tag
2. Create DMG installer
3. Upload to GitHub releases
4. Users download and install

## Platform-Specific Builds

### Building for Different Architectures

**Apple Silicon (M1/M2/M3) - Default**
```bash
npm run tauri build
# Creates: D_0.2.0_aarch64.dmg
```

**Intel Macs**
```bash
npm run tauri build -- --target x86_64-apple-darwin
# Creates: D_0.2.0_x64.dmg
```

**Universal Binary (Both Architectures)**
```bash
# Install both targets first
rustup target add aarch64-apple-darwin
rustup target add x86_64-apple-darwin

# Build universal binary
npm run tauri build -- --target universal-apple-darwin
# Creates: D_0.2.0_universal.dmg
```

**Note:** Universal binary builds may fail on some systems. If that happens, build for each architecture separately.

## Troubleshooting Build Issues

### Frontend Build Errors
If the Vue/Vite build fails:
```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install

# Check for TypeScript errors
npm run build
```

### Rust Compilation Errors
If Cargo fails to compile:
```bash
# Clean Rust build cache
cd src-tauri
cargo clean

# Update dependencies
cargo update

# Try building Rust only
cargo build --release
```

### DMG Creation Fails
If Tauri can't create the DMG:
1. Build with `--bundles app` only
2. Create DMG manually (see "Creating a DMG Installer" section)

### Universal Binary Build Fails
This is common - the build may hang during compilation for the second architecture:
- Build separately for each architecture instead
- Or build only for your current architecture

### Code Signing / Gatekeeper Issues
If users can't open the app ("damaged" error):
```bash
# Remove quarantine attribute
xattr -cr /Applications/D.app
```

For production:
- Sign the app with an Apple Developer certificate
- Notarize with Apple for distribution

## Technical Details

### Application Stack
- **Frontend**: Vue 3 + TypeScript + Tailwind CSS
- **Backend**: Rust + Tauri
- **Build Tools**: Vite (frontend), Cargo (backend)
- **State Management**: Pinia
- **UI Components**: Custom Vue components

### Dependencies
- **Rust crates**: See `src-tauri/Cargo.toml`
  - tauri
  - serde
  - tokio (async runtime)
  - chrono (date/time)
  - regex
  
- **Node packages**: See `package.json`
  - vue
  - vue-router
  - pinia
  - @tauri-apps/api
  - tailwindcss
  - heroicons

### System Requirements
- **macOS**: 10.15 (Catalina) or later
- **Architecture**: Apple Silicon or Intel
- **Disk Space**: ~10MB installed

## Continuous Integration

For automated builds with GitHub Actions:

```yaml
# .github/workflows/build.yml
name: Build macOS App
on: [push, release]
jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - uses: dtolnay/rust-toolchain@stable
      - name: Install dependencies
        run: npm install
      - name: Build app
        run: npm run tauri build
      - uses: actions/upload-artifact@v3
        with:
          name: macos-dmg
          path: src-tauri/target/release/bundle/dmg/*.dmg
```

## Version Updates

When releasing a new version:
1. Update version in `src-tauri/tauri.conf.json`
2. Update version in `package.json`
3. Create release notes
4. Build for the release tag
5. Upload DMG to GitHub releases

See `GITHUB_RELEASE_STEPS.md` for detailed release process.
