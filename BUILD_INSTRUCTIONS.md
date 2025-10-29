# Building d-dns-debugger as a Binary

This document explains how to build and distribute `d` as a standalone binary executable.

## Overview

The project uses **PyInstaller** to bundle the Python application and all its dependencies into a single executable binary file.

## Quick Start

### One-Command Build & Package
```bash
./build_and_package.sh
```

This will:
1. Build the binary with PyInstaller
2. Create a distributable tarball
3. Generate SHA256 checksum

### Individual Steps

#### 1. Build Only
```bash
./build_binary.sh
```
Output: `dist/d` (17MB standalone executable)

#### 2. Package Only (after building)
```bash
./package.sh
```
Output: 
- `packages/d-v0.1.0-darwin-arm64.tar.gz`
- `packages/d-v0.1.0-darwin-arm64.sha256`

## Files Created

### Build Files
- **d.spec** - PyInstaller configuration file
- **build_binary.sh** - Script to build the binary
- **package.sh** - Script to package the binary for distribution
- **build_and_package.sh** - Combined build & package script

### Documentation
- **DISTRIBUTION.md** - Detailed distribution guide for developers
- **BINARY_INSTALL.md** - Installation guide for end users
- **BUILD_INSTRUCTIONS.md** - This file

### Output
- **dist/d** - The standalone binary executable
- **packages/*.tar.gz** - Compressed binary for distribution
- **packages/*.sha256** - Checksum file for verification

## How It Works

### PyInstaller Process

1. **Analysis**: PyInstaller analyzes `src/dns_debugger/__main__.py` and discovers all imports
2. **Collection**: Collects all Python modules, dependencies, and data files (like Textual CSS)
3. **Bundling**: Bundles everything into a single executable with:
   - Python interpreter
   - All dependencies (textual, click, httpx, etc.)
   - Your application code
   - Required data files
4. **Optimization**: Compresses with UPX and optimizes for size

### Configuration (d.spec)

The `d.spec` file configures:
- **Entry point**: `src/dns_debugger/__main__.py`
- **Hidden imports**: Textual modules and dns_debugger submodules
- **Data files**: Textual CSS and configuration files
- **Output name**: `d`
- **One-file mode**: All bundled into single executable
- **Console mode**: Runs in terminal (not GUI)

## Testing the Binary

```bash
# Test help
./dist/d --help

# Test version
./dist/d --version

# Test with a domain (CLI mode, doesn't require DNS tools)
./dist/d example.com --no-tui

# Test full TUI (requires dog or dig installed)
./dist/d example.com
```

## Distribution

### What to Share with Users

1. **The Package**:
   - `d-v0.1.0-darwin-arm64.tar.gz`
   - `d-v0.1.0-darwin-arm64.sha256`

2. **Installation Guide**:
   - Share `BINARY_INSTALL.md` with end users

3. **Platform Notes**:
   - Binary is built for the platform you're on (macOS arm64 in this case)
   - Users on different platforms need different builds:
     - macOS Intel: Build on Intel Mac
     - Linux: Build on Linux
     - Windows: Build on Windows (creates d.exe)

### GitHub Releases (Recommended)

1. Create a release tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. Go to GitHub → Releases → Create Release

3. Upload these files as assets:
   - `d-v0.1.0-darwin-arm64.tar.gz`
   - `d-v0.1.0-darwin-arm64.sha256`
   - `BINARY_INSTALL.md` (renamed to README.md for the release)

4. Users can download directly from releases page

## Platform-Specific Builds

### Current Platform
- **OS**: macOS (darwin)
- **Architecture**: ARM64 (M1/M2 Mac)
- **Binary name**: `d`

### Building for Other Platforms

You need to build on each target platform:

#### Linux (x86_64)
```bash
# On a Linux machine
./build_and_package.sh
# Creates: d-v0.1.0-linux-x86_64.tar.gz
```

#### macOS (Intel)
```bash
# On an Intel Mac
./build_and_package.sh
# Creates: d-v0.1.0-darwin-x86_64.tar.gz
```

#### Windows
```bash
# On Windows
.\build_binary.sh
# Creates: d.exe and d-v0.1.0-windows-x86_64.zip
```

## Troubleshooting Build Issues

### Import Errors
If the binary fails with missing module errors:
1. Activate venv: `source .venv/bin/activate`
2. Edit `d.spec` to add missing modules to `hiddenimports`
3. Rebuild: `pyinstaller d.spec`

### Missing Data Files
If CSS or other assets are missing:
1. Edit `d.spec` to add to `datas` list
2. Rebuild

### Large Binary Size
Current size (~17MB) is reasonable. To reduce:
- Remove unused dependencies from `pyproject.toml`
- Use `--exclude-module` in spec file
- UPX compression (already enabled)

### Build Script Issues
If `build_binary.sh` fails:
1. Check Python version: `python3 --version` (need 3.8+)
2. Check venv: `source .venv/bin/activate`
3. Install manually: `pip install pyinstaller`
4. Run manually: `pyinstaller d.spec`

## Technical Details

### Binary Contents
- Python 3.13.7 runtime
- All packages from pyproject.toml dependencies:
  - textual (TUI framework)
  - click (CLI framework)
  - httpx (HTTP client for RDAP)
  - whodap (RDAP client)
  - python-whois (WHOIS client)
  - cryptography (SSL/TLS validation)

### What's NOT Included
- DNS query tools (dog/dig) - users must install separately
- System libraries (users need compatible OS)

### Binary Compatibility
- **macOS ARM64**: Works on M1/M2/M3 Macs with macOS 11+
- **macOS x86_64**: Works on Intel Macs
- **Linux**: Requires GLIBC version compatible with build machine
- **Windows**: Requires Windows 10+

## Continuous Integration

For automated multi-platform builds, consider GitHub Actions:

```yaml
# .github/workflows/build.yml
name: Build Binaries
on: [push, release]
jobs:
  build:
    strategy:
      matrix:
        os: [macos-latest, ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: ./build_and_package.sh
      - uses: actions/upload-artifact@v2
        with:
          name: binaries
          path: packages/*
```

## Version Updates

When releasing a new version:

1. Update version in `pyproject.toml`
2. Run `./build_and_package.sh`
3. Package name automatically includes new version
4. Upload to GitHub releases

## Support

For build-related issues:
- Check `build/d/warn-d.txt` for PyInstaller warnings
- Check `build/d/xref-d.html` for dependency graph
- Review PyInstaller docs: https://pyinstaller.org/

## License

This build system is part of d-dns-debugger and uses the same MIT license.
