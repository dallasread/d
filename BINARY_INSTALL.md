# Installing d-dns-debugger (Binary Distribution)

This guide is for users who want to install the pre-built binary of `d` - the DNS debugger tool.

## Quick Install

### macOS / Linux

1. **Download the binary** for your platform from the releases page

2. **Extract the archive:**
   ```bash
   tar -xzf d-v0.1.0-*.tar.gz
   ```

3. **Make it executable:**
   ```bash
   chmod +x d
   ```

4. **Test it:**
   ```bash
   ./d example.com --help
   ```

5. **Optional: Install system-wide:**
   ```bash
   sudo mv d /usr/local/bin/
   ```

   Now you can run it from anywhere:
   ```bash
   d example.com
   ```

## Requirements

### For DNS Queries
The tool requires one of these DNS query tools to be installed:
- **dog** (recommended): https://dns.lookup.dog/
- **dig** (alternative): Usually in `bind-tools` or `dnsutils` package

Install dog:
```bash
# macOS
brew install dog

# Linux (various methods available at dns.lookup.dog)
```

Or install dig:
```bash
# macOS (usually pre-installed)
# dig should already be available

# Ubuntu/Debian
sudo apt-get install dnsutils

# Fedora/RHEL
sudo dnf install bind-utils
```

### Built-in Features
These features work without additional tools:
- ✓ SSL/TLS certificate validation
- ✓ WHOIS queries
- ✓ RDAP queries
- ✓ Interactive TUI

## Usage

### Interactive TUI Mode (default)
```bash
d example.com
```

### CLI Mode
```bash
d example.com --no-tui
```

### Custom Theme
```bash
d example.com --theme monokai
```

Available themes: dark, light, monokai, solarized

### Get Version
```bash
d --version
```

## Verification

To verify the download integrity:

```bash
# Check the SHA256 hash
shasum -a 256 d-v0.1.0-*.tar.gz
# Compare with the .sha256 file
```

## Troubleshooting

### "Permission denied" error
```bash
chmod +x d
```

### "Cannot be opened because the developer cannot be verified" (macOS)
```bash
xattr -d com.apple.quarantine d
# Or: System Preferences > Security & Privacy > Allow
```

### "No DNS tools available" error
Install `dog` or `dig` (see Requirements section above)

### Other Issues
- Make sure you're running a compatible version of macOS/Linux
- Try running with `--no-tui` flag for CLI mode
- Check that you have internet connectivity for DNS queries

## Uninstall

```bash
# If installed system-wide
sudo rm /usr/local/bin/d

# If using locally
rm d
```

## Support

- GitHub Issues: https://github.com/yourusername/d/issues
- Documentation: https://github.com/yourusername/d#readme

## License

MIT License - See LICENSE file for details
