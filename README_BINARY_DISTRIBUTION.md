# d-dns-debugger - Binary Distribution

✅ **Your binary is ready to share!**

## What You Have

### 📦 Distributable Package
- **Location**: `packages/d-v0.1.0-darwin-arm64.tar.gz` (17MB)
- **Checksum**: `packages/d-v0.1.0-darwin-arm64.sha256`
- **Platform**: macOS ARM64 (M1/M2/M3 Macs)

### 🔨 Build System
All scripts and configurations are ready:
- `build_binary.sh` - Build the binary
- `package.sh` - Create distribution package
- `build_and_package.sh` - Do both in one command
- `d.spec` - PyInstaller configuration

### 📚 Documentation
Complete documentation for different audiences:
- **QUICK_REFERENCE.md** - Quick commands & cheat sheet
- **BINARY_INSTALL.md** - For end users installing the binary
- **BUILD_INSTRUCTIONS.md** - For developers building from source
- **DISTRIBUTION.md** - Distribution strategies & CI/CD

## Next Steps

### Option 1: Share Directly
Just share these two files with users:
```
packages/d-v0.1.0-darwin-arm64.tar.gz
packages/d-v0.1.0-darwin-arm64.sha256
```

And provide them with `BINARY_INSTALL.md` for installation instructions.

### Option 2: GitHub Releases (Recommended)
1. Create a release tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. Go to GitHub → Releases → Create New Release

3. Upload as assets:
   - `packages/d-v0.1.0-darwin-arm64.tar.gz`
   - `packages/d-v0.1.0-darwin-arm64.sha256`

4. Copy content from `BINARY_INSTALL.md` into release notes

### Option 3: Multi-Platform Releases
To support all platforms:

1. **On macOS (ARM)**: `./build_and_package.sh` → creates darwin-arm64 package
2. **On macOS (Intel)**: `./build_and_package.sh` → creates darwin-x86_64 package
3. **On Linux**: `./build_and_package.sh` → creates linux-x86_64 package
4. **On Windows**: `./build_and_package.sh` → creates windows-x86_64 package

Upload all packages to GitHub Releases.

## Quick Test

Before distributing, verify the binary works:

```bash
# Test locally
./dist/d --version
./dist/d --help

# Extract and test the package
cd /tmp
tar -xzf ~/apps/dns/d/packages/d-v0.1.0-darwin-arm64.tar.gz
./d example.com --no-tui
```

## User Installation (1-2-3)

Users install with three simple commands:

```bash
# 1. Extract
tar -xzf d-v0.1.0-darwin-arm64.tar.gz

# 2. Make executable
chmod +x d

# 3. Run
./d example.com
```

Optional: Install system-wide
```bash
sudo mv d /usr/local/bin/
```

## What's Included

The binary includes:
- ✅ Python runtime (3.13.7)
- ✅ All Python dependencies (textual, click, httpx, etc.)
- ✅ Your application code
- ✅ SSL/TLS certificate checking
- ✅ WHOIS/RDAP support
- ✅ Interactive TUI

Users need to install separately:
- ⚠️ DNS query tools (`dog` or `dig`) - required for DNS queries

## File Reference

### Created Files
```
d.spec                              # PyInstaller config
build_binary.sh                     # Build script
package.sh                          # Package script
build_and_package.sh               # Combined script
dist/d                              # The binary (17MB)
packages/d-v0.1.0-darwin-arm64.tar.gz  # Distribution package
packages/d-v0.1.0-darwin-arm64.sha256  # Checksum
```

### Documentation
```
QUICK_REFERENCE.md                  # Quick commands
BINARY_INSTALL.md                   # User installation guide
BUILD_INSTRUCTIONS.md               # Developer build guide
DISTRIBUTION.md                     # Distribution strategies
README_BINARY_DISTRIBUTION.md       # This file
```

## Rebuilding

Anytime you update the code:

```bash
./build_and_package.sh
```

This creates a fresh binary and package ready to distribute.

## Support

### Build Issues
- Check `BUILD_INSTRUCTIONS.md` → Troubleshooting section
- Review PyInstaller logs in `build/d/warn-d.txt`

### User Issues
- Direct users to `BINARY_INSTALL.md`
- Common issues covered in documentation

## Version Management

Current version: **0.1.0** (from `pyproject.toml`)

To release a new version:
1. Update version in `pyproject.toml`
2. Run `./build_and_package.sh`
3. Package name automatically updates to new version
4. Create new Git tag and GitHub release

## Summary

🎉 **You're all set!**

- ✅ Binary built: `dist/d` (17MB)
- ✅ Package created: `packages/d-v0.1.0-darwin-arm64.tar.gz`
- ✅ Checksum generated: `packages/d-v0.1.0-darwin-arm64.sha256`
- ✅ Documentation ready: Multiple guides for users and developers
- ✅ Build system complete: Easy to rebuild and update

**Share the package and `BINARY_INSTALL.md` with your users!**

---

For detailed information, see:
- **Quick Start**: `QUICK_REFERENCE.md`
- **User Guide**: `BINARY_INSTALL.md`
- **Developer Guide**: `BUILD_INSTRUCTIONS.md`
- **Distribution**: `DISTRIBUTION.md`
