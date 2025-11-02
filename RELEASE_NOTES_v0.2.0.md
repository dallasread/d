# D DNS Debugger v0.2.0 - Tauri GUI Release

## 🎉 Major Release: Desktop GUI Application

This is a major release that replaces the Python terminal UI with a modern desktop application built with Tauri and Vue 3.

## ✨ What's New

### Desktop GUI Application
- **Modern Desktop Interface** - Native macOS application with beautiful dark theme UI
- **Interactive Dashboard** - At-a-glance health overview with color-coded status indicators
- **Real-time Data Loading** - Async data fetching with progress indicators
- **Keyboard Navigation** - Number keys (1-7) to jump between panels, R to refresh, L for logs

### Visual DNSSEC Chain Visualization
- **Complete chain display** - Shows root → TLD → domain with all zones
- **Hand-drawn style arrows** - Organic, flowing arrows connecting DS records to DNSKEYs
- **Color-coded key tags** - Rotating colors for easy visual matching
- **RRSIG signatures** - Cryptographic signatures displayed with matching arrows to DNSKEYs
- **Clean, modern design** - Dark background sections with clear hierarchy

### Custom App Icon
- **Distinctive branding** - Dark circle with white "D" letter
- **Orange triangle accent** - Prominent orange triangle in top-right corner
- **Universal binary icon** - Optimized for both Retina and standard displays

### Enhanced Features
- **Certificate Panel** - SSL/TLS certificate inspection with chain validation
- **HTTP/HTTPS Panel** - Status codes, redirects, response times
- **Registration Panel** - WHOIS/RDAP data with expiration tracking
- **Email Panel** - MX record display (SPF/DKIM/DMARC coming soon)
- **Command Logs** - View all backend commands (dig, openssl, curl) with full output

### Dashboard Cards
Each card shows real-time status:
- **DNS** - A, AAAA, MX, NS record counts
- **Registration** - Domain expiration countdown
- **DNSSEC** - Validation status and chain depth
- **Certificate** - Days until expiration
- **HTTP/HTTPS** - Status code and response time
- **Email** - MX record count and hostnames

## 🔧 Technical Improvements

### Architecture
- **Tauri Framework** - Rust backend with Vue 3 TypeScript frontend
- **Universal Binary** - Single app works on both Intel and Apple Silicon Macs
- **Pinia State Management** - Reactive state stores for all data
- **Vue Router** - Smooth navigation between panels
- **Tailwind CSS** - Modern, responsive styling

### Backend Fixes
- **Certificate Parsing** - Fixed PEM parsing by writing to openssl stdin instead of shell echo
- **Store Caching** - Proper clearing of all stores when domain changes
- **Error Handling** - Better error messages and fallback behavior

### Build System
- **macOS Build Script** - `build-macos.sh` creates universal binary with DMG
- **Native DMG Creation** - Uses macOS's built-in `hdiutil` for reliable DMG generation
- **ZIP Distribution** - Compressed archive for easy distribution

## 📦 Installation

### Via DMG (Recommended)
1. Download `D_0.2.0_universal.dmg`
2. Open the DMG file
3. Drag D.app to Applications folder

### Via ZIP
1. Download `D-macos-universal.zip`
2. Extract the archive
3. Copy D.app to /Applications

### Via Direct App Bundle
1. Download `D.app.zip`
2. Extract and run directly

## 🖥️ System Requirements

- **macOS 10.15 Catalina or later**
- **Intel or Apple Silicon Mac**
- **Required tools**: dig, openssl, whois, curl (install via Homebrew)

```bash
brew install bind openssl whois curl
```

## 🗂️ Legacy Python TUI

The original Python terminal UI is still available in the `legacy/` directory for users who prefer command-line interfaces. See `legacy/README.md` for documentation.

## 🔗 What's Included

- `D.app` - Universal macOS application (works on Intel and Apple Silicon)
- `D_0.2.0_universal.dmg` - DMG installer (8.0 MB)
- `D-macos-universal.zip` - ZIP archive (7.1 MB)

## 🐛 Known Issues

- DMG window positioning may not apply correctly on CI/CD platforms (cosmetic only)
- Email security features (SPF, DKIM, DMARC) are placeholder - coming in future release

## 🙏 Acknowledgments

Built with:
- [Tauri](https://tauri.app/) - Rust-based desktop framework
- [Vue 3](https://vuejs.org/) - Progressive JavaScript framework
- [TypeScript](https://www.typescriptlang.org/) - Typed JavaScript
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Heroicons](https://heroicons.com/) - Beautiful hand-crafted SVG icons

---

**Full Changelog**: https://github.com/dallasread/d/compare/v0.1.2...v0.2.0
