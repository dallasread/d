# GitHub Release Guide for D DNS Debugger

This guide walks through creating a GitHub release with the macOS application bundle and DMG installer.

## Pre-Release Checklist

Before creating a release, ensure:
- [ ] All changes are committed and pushed to main
- [ ] Version numbers are updated (if needed)
- [ ] Release notes document exists (e.g., `RELEASE_NOTES_v0.2.1.md`)

## Step 1: Build the Release Binaries

### Checkout the Release Tag

```bash
# Checkout the tag you want to release
git checkout v0.2.1

# Build for Apple Silicon (current architecture)
npm run tauri build -- --bundles app

# Create DMG manually
mkdir -p dist
cp -r src-tauri/target/release/bundle/macos/D.app dist/
DMG_DIR=$(mktemp -d)
cp -r dist/D.app "$DMG_DIR/"
hdiutil create -volname "D DNS Debugger v0.2.1" \
  -srcfolder "$DMG_DIR" \
  -ov -format UDZO \
  dist/D_v0.2.1_aarch64.dmg
rm -rf "$DMG_DIR"

# Return to main branch
git checkout main
```

**Build output:**
- `dist/D.app` - macOS application bundle (~4MB)
- `dist/D_v0.2.1_aarch64.dmg` - DMG installer (~4MB)

## Step 2: Create Git Tag (if not already created)

```bash
# Create and push the tag
git tag v0.2.1
git push origin v0.2.1
```

## Step 3: Create GitHub Release

### Option A: GitHub Web UI

1. Go to https://github.com/dallasread/d/releases/new
2. Select tag: **v0.2.1**
3. Release title: `v0.2.1 - [Brief Description]`
4. Description: Copy content from `RELEASE_NOTES_v0.2.1.md`
5. Attach binaries:
   - `dist/D_v0.2.1_aarch64.dmg`
6. Check "Set as the latest release"
7. Click "Publish release"

### Option B: GitHub CLI

```bash
# Create release with DMG file
gh release create v0.2.1 \
  dist/D_v0.2.1_aarch64.dmg \
  --title "v0.2.1 - [Brief Description]" \
  --notes-file RELEASE_NOTES_v0.2.1.md
```

## What Users Will See

When users visit the release page:
1. Release title and tag
2. Full description with features and installation instructions  
3. Downloadable DMG installer
4. Source code (zip & tar.gz) - automatically added by GitHub

## Installation Instructions for Users

Users can install by:

1. **Download the DMG:**
   - Click on `D_v0.2.1_aarch64.dmg` from the release assets
   
2. **Install:**
   - Double-click the DMG file
   - Drag `D.app` to Applications folder
   - Eject the DMG

3. **Run:**
   - Open from Applications folder
   - On first run, macOS may show security warning - go to System Settings → Privacy & Security to allow

## Platform Support

**Current builds:**
- macOS Apple Silicon (M1/M2/M3) - `aarch64.dmg`

**Future builds:**
- macOS Intel - Build with `--target x86_64-apple-darwin`
- Universal binary - Build with `--target universal-apple-darwin` (Intel + Apple Silicon)

## File Locations

```
d/
├── dist/
│   ├── D.app                      ← Application bundle
│   └── D_v0.2.1_aarch64.dmg      ← Upload to GitHub
├── RELEASE_NOTES_v0.2.1.md       ← Copy description from here
└── GITHUB_RELEASE_STEPS.md       ← This file
```

## Troubleshooting

### DMG Creation Failed
If Tauri's built-in DMG bundler fails, create manually with `hdiutil` (see Step 1).

### Universal Binary Build Issues
If building for both architectures fails, build separately for each:
- Apple Silicon: `npm run tauri build` (on Apple Silicon Mac)
- Intel: `npm run tauri build --target x86_64-apple-darwin` (on Intel Mac)

### Gatekeeper Issues
Users may see "D is damaged and can't be opened" if the app isn't code-signed. To fix:
```bash
# Users can run this to bypass Gatekeeper
xattr -cr /Applications/D.app
```

For production releases, consider code signing with an Apple Developer certificate.

## Share Your Release

Once published, share the release URL:
- Direct link: https://github.com/dallasread/d/releases/tag/v0.2.1
- Latest release: https://github.com/dallasread/d/releases/latest
