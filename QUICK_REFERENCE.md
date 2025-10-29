# Quick Reference: Building & Distributing d-dns-debugger Binary

## For Developers (Building)

### Complete Build & Package
```bash
./build_and_package.sh
```
**Output**: `packages/d-v0.1.0-darwin-arm64.tar.gz` + checksum

### Build Only
```bash
./build_binary.sh
```
**Output**: `dist/d` (17MB executable)

### Package Only
```bash
./package.sh
```
**Output**: Tarball in `packages/`

### Test Binary
```bash
./dist/d --version
./dist/d example.com --help
```

## For End Users (Installing)

### Download & Extract
```bash
tar -xzf d-v0.1.0-*.tar.gz
chmod +x d
```

### Install System-Wide
```bash
sudo mv d /usr/local/bin/
```

### Run
```bash
d example.com              # Interactive TUI
d example.com --no-tui     # CLI mode
```

## Files Created

| File | Purpose |
|------|---------|
| `d.spec` | PyInstaller configuration |
| `build_binary.sh` | Build script |
| `package.sh` | Packaging script |
| `build_and_package.sh` | Combined build + package |
| `dist/d` | The binary executable (17MB) |
| `packages/*.tar.gz` | Distribution package |
| `packages/*.sha256` | Checksum for verification |

## Documentation

| File | Audience | Content |
|------|----------|---------|
| `BUILD_INSTRUCTIONS.md` | Developers | Complete build guide |
| `BINARY_INSTALL.md` | End Users | Installation instructions |
| `DISTRIBUTION.md` | Developers | Distribution strategies |
| `QUICK_REFERENCE.md` | Everyone | This cheat sheet |

## Requirements

### Build Requirements (Developers)
- Python 3.8+
- pip & venv
- Internet connection (for dependencies)

### Runtime Requirements (End Users)
- **For DNS queries**: `dog` or `dig` command
- macOS 11+ / Linux with compatible GLIBC / Windows 10+

### Built-in Features (No External Tools Needed)
- SSL/TLS certificate checking
- WHOIS queries
- RDAP queries
- Interactive TUI

## Binary Details

- **Size**: ~17MB (includes Python runtime + all dependencies)
- **Format**: Single executable file
- **Platform**: Platform-specific (need separate builds for Mac/Linux/Windows)
- **Current**: `d-v0.1.0-darwin-arm64` (M1/M2 Mac)

## Common Commands

```bash
# Build everything
./build_and_package.sh

# Test the binary
./dist/d --version
./dist/d example.com --no-tui

# Verify checksum
shasum -a 256 -c packages/*.sha256

# Clean build artifacts
rm -rf build dist

# Create new build
./build_binary.sh
```

## Distribution Checklist

- [ ] Build binary: `./build_binary.sh`
- [ ] Test binary: `./dist/d example.com`
- [ ] Package: `./package.sh`
- [ ] Verify checksum
- [ ] Tag release: `git tag v0.1.0`
- [ ] Push tag: `git push origin v0.1.0`
- [ ] Create GitHub Release
- [ ] Upload `packages/*.tar.gz` and `packages/*.sha256`
- [ ] Include `BINARY_INSTALL.md` in release notes

## Quick Links

- Binary location: `dist/d`
- Packages: `packages/`
- Build config: `d.spec`
- User guide: `BINARY_INSTALL.md`
- Developer guide: `BUILD_INSTRUCTIONS.md`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No DNS tools available" | Install `dog` or `dig` |
| "Permission denied" | Run `chmod +x d` |
| Import errors in binary | Add to `hiddenimports` in `d.spec` |
| Binary won't run on macOS | Run `xattr -d com.apple.quarantine d` |
| Large file size | Expected (~17MB with all deps) |

---

**Version**: 0.1.0  
**Last Updated**: October 2024
