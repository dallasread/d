# d-dns-debugger v0.1.0 - Binary Release

🚀 First binary release of `d` - an interactive TUI for debugging DNS, SSL/TLS certificates, and domain registration!

## 📦 Downloads

**macOS (Apple Silicon - M1/M2/M3):**
- Binary: `d-v0.1.0-darwin-arm64.tar.gz` (17 MB)
- Checksum: `d-v0.1.0-darwin-arm64.sha256`

*Note: For Intel Macs and Linux, you'll need to build from source (see BUILD_INSTRUCTIONS.md)*

## ⚡ Quick Install

```bash
# 1. Download and extract
tar -xzf d-v0.1.0-darwin-arm64.tar.gz

# 2. Make executable
chmod +x d

# 3. Run it!
./d example.com
```

### Install System-Wide (Optional)
```bash
sudo mv d /usr/local/bin/
d example.com
```

## ✨ Features

### DNS Queries
- Support for all major record types: A, AAAA, CNAME, MX, TXT, NS, SOA, CAA
- Works with `dog` (recommended) or `dig` DNS tools
- Fast, colorized output
- Query time tracking

### SSL/TLS Certificate Validation
- Certificate chain inspection
- Expiration date checking
- Issuer information
- Subject Alternative Names (SANs)

### Domain Registration
- WHOIS lookups
- RDAP (Registration Data Access Protocol) support
- Registrar information
- Registration and expiration dates

### Interactive TUI
- Beautiful terminal interface powered by Textual
- Multiple color themes (dark, light, monokai, solarized)
- Keyboard navigation
- Real-time updates

## 📋 Requirements

### For DNS Queries (Required)
Install one of these:

**dog** (recommended):
```bash
brew install dog
```

**dig** (alternative):
```bash
# macOS: Usually pre-installed
# Ubuntu/Debian: sudo apt-get install dnsutils
# Fedora/RHEL: sudo dnf install bind-utils
```

### Built-in Features (No External Tools Needed)
- ✅ SSL/TLS certificate validation
- ✅ WHOIS queries
- ✅ RDAP queries
- ✅ Interactive TUI

## 🎯 Usage Examples

### Interactive Mode (Default)
```bash
d example.com
```

### CLI Mode (Non-Interactive)
```bash
d example.com --no-tui
```

### Custom Theme
```bash
d example.com --theme monokai
```

Available themes: `dark`, `light`, `monokai`, `solarized`

### Version Check
```bash
d --version
```

## 🔒 Verification

Verify the download integrity:
```bash
shasum -a 256 -c d-v0.1.0-darwin-arm64.sha256
```

## 📚 Documentation

Full documentation included in this release:
- **BINARY_INSTALL.md** - Complete installation guide
- **QUICK_REFERENCE.md** - Quick command reference
- **BUILD_INSTRUCTIONS.md** - Build from source
- **README.md** - Project overview

## 🛠️ Technical Details

- **Binary Size**: ~17 MB (standalone, includes Python runtime)
- **Python Version**: 3.13.7 (embedded)
- **Platform**: macOS ARM64 (M1/M2/M3 Macs)
- **Dependencies**: All included (textual, click, httpx, cryptography, etc.)
- **Build Tool**: PyInstaller 6.16.0

## 🐛 Known Issues

- First run on macOS may show security warning - allow in System Preferences
- Currently only macOS ARM64 binary provided - other platforms build from source

## 🤝 Contributing

Want to contribute or build for other platforms? See:
- BUILD_INSTRUCTIONS.md for building from source
- DISTRIBUTION.md for multi-platform distribution

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built with:
- [Textual](https://github.com/Textualize/textual) - TUI framework
- [Click](https://click.palletsprojects.com/) - CLI framework
- [httpx](https://www.python-httpx.org/) - HTTP client
- [cryptography](https://cryptography.io/) - SSL/TLS handling

## 📞 Support

- **Issues**: https://github.com/dallasread/d/issues
- **Documentation**: https://github.com/dallasread/d#readme

---

**First time using d?** Check out BINARY_INSTALL.md for detailed installation instructions!
