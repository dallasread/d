# Distribution Guide for d-dns-debugger

This guide explains how to build and distribute the `d` DNS debugger as a standalone binary.

## Building the Binary

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment support

### Build Steps

1. **Clone or navigate to the project directory:**
   ```bash
   cd d
   ```

2. **Run the build script:**
   ```bash
   ./build_binary.sh
   ```

   This script will:
   - Create/activate a virtual environment
   - Install all dependencies including PyInstaller
   - Clean previous builds
   - Build a standalone binary using PyInstaller
   - Output the binary to `dist/d`

3. **Verify the build:**
   ```bash
   ./dist/d example.com
   ```

### Manual Build (Alternative)

If you prefer to build manually:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Build with PyInstaller
pyinstaller d.spec

# Binary will be in dist/d
```

## Distribution

### Single Binary Distribution

The build process creates a single standalone executable in `dist/d` that includes:
- All Python dependencies
- The Textual TUI framework
- DNS querying libraries
- SSL/TLS certificate validation tools
- WHOIS/RDAP clients

**File size:** Approximately 20-40 MB (varies by platform)

### Distribution Methods

#### 1. Direct Binary Sharing

Simply share the `dist/d` binary file. Users can:

```bash
# Make it executable
chmod +x d

# Run it
./d example.com

# Optional: Install system-wide
sudo mv d /usr/local/bin/
```

#### 2. Tarball/Archive

Create a compressed archive for easier distribution:

```bash
cd dist
tar -czf d-dns-debugger-$(uname -s)-$(uname -m).tar.gz d
```

Users can extract and use:

```bash
tar -xzf d-dns-debugger-*.tar.gz
chmod +x d
./d example.com
```

#### 3. GitHub Releases

Upload the binary to GitHub Releases:

1. Tag a release: `git tag v0.1.0`
2. Push the tag: `git push origin v0.1.0`
3. Create a release on GitHub
4. Upload `dist/d` as a release asset

Name the binary with platform information:
- `d-v0.1.0-macos-arm64` (M1/M2 Macs)
- `d-v0.1.0-macos-x86_64` (Intel Macs)
- `d-v0.1.0-linux-x86_64` (Linux)
- `d-v0.1.0-windows-x86_64.exe` (Windows)

## Platform-Specific Notes

### macOS

The binary is built for the architecture of the build machine. Users may need to:
- Grant execution permissions: `chmod +x d`
- Allow the app in System Preferences > Security & Privacy (first run only)
- For universal distribution, build on both Intel and Apple Silicon machines

### Linux

The binary includes most dependencies but requires:
- glibc version compatible with build machine or newer
- DNS tools (`dig` or `dog`) installed on user's system for DNS queries

### Windows

Windows builds require:
- Building on a Windows machine or using cross-compilation
- Output will be `d.exe` instead of `d`
- Users may need to add to PATH or run from specific directory

## Dependencies at Runtime

The binary is standalone and includes all Python dependencies. However, for full functionality, users should have:

### Required (for DNS queries)
- `dog` (recommended): https://dns.lookup.dog/
- OR `dig` (alternative): Usually in `bind-tools` or `dnsutils` package

### Optional
These features work without external tools:
- SSL/TLS certificate validation (built-in)
- WHOIS queries (built-in)
- RDAP queries (built-in)

## Testing the Binary

Before distribution, test the binary thoroughly:

```bash
# Basic functionality
./dist/d example.com

# CLI mode
./dist/d example.com --no-tui

# Different themes
./dist/d example.com --theme monokai

# Version check
./dist/d --version

# Help
./dist/d --help
```

## Troubleshooting Build Issues

### Import Errors

If the binary fails with import errors, add missing modules to `d.spec`:

```python
hiddenimports=[
    'your_missing_module',
    # ... other imports
]
```

### Missing Data Files

If Textual CSS or other data files are missing:

```python
datas=[
    ('path/to/data', 'destination'),
]
```

### Large Binary Size

To reduce binary size:
- Remove unused dependencies from `pyproject.toml`
- Use `--exclude-module` in PyInstaller
- Enable UPX compression (already enabled in `d.spec`)

### Platform-Specific Issues

- **macOS codesigning**: For distribution outside your machine, consider signing the binary
- **Linux GLIBC**: Build on the oldest supported Linux version
- **Windows antivirus**: Some AV software flags PyInstaller binaries; consider signing

## Continuous Integration

For automated builds across platforms, use GitHub Actions:

1. Create `.github/workflows/build.yml`
2. Set up build jobs for macOS, Linux, and Windows
3. Upload binaries as artifacts or release assets

## License Compliance

The binary includes the following open-source components:
- Textual (MIT License)
- Click (BSD License)
- httpx (BSD License)
- whodap (MIT License)
- python-whois (MIT License)
- cryptography (Apache 2.0 / BSD)

Ensure your distribution complies with all licenses (current setup is MIT-compatible).

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/d/issues
- Documentation: https://github.com/yourusername/d#readme

## Version Information

- Current version: 0.1.0
- Python version: 3.8+
- Build tool: PyInstaller 6.0.0+