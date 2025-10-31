# D DNS Debugger - Claude Project Guide

This document contains important project-specific information for Claude to remember.

## 🔢 Version Management

**CRITICAL:** Version numbers are stored in TWO places and BOTH must be updated:

1. **`pyproject.toml:6`** - Project metadata version
   ```toml
   version = "0.1.1"
   ```

2. **`src/dns_debugger/__main__.py:13`** - Click CLI version option
   ```python
   @click.version_option(version="0.1.1", prog_name="d")
   ```

**Why both?** Click's `@click.version_option` decorator does NOT automatically read from `pyproject.toml`. It must be manually set.

**After updating:** Always rebuild the binary with `./build_binary.sh` and verify with `./dist/d --version`

**Full checklist:** See `VERSION_BUMP_CHECKLIST.md`

## 🏗️ Project Structure

```
d/
├── src/dns_debugger/          # Main application code
│   ├── __main__.py            # Entry point (contains version!)
│   ├── app.py                 # TUI application
│   ├── adapters/              # External integrations (DNS, WHOIS, SSL)
│   ├── domain/                # Business logic
│   └── widgets/               # Textual UI components
├── dist/                      # Built binary output
├── build/                     # PyInstaller build artifacts
├── packages/                  # Distribution packages (.tar.gz)
├── pyproject.toml             # Python project config (contains version!)
├── d.spec                     # PyInstaller specification
├── build_binary.sh            # Build script for macOS binary
├── package.sh                 # Package script for distribution
└── Makefile                   # Python development commands
```

## 🔨 Build System

- **Language:** Python 3.8+ (TUI built with Textual)
- **Binary Builder:** PyInstaller
- **Build Script:** `./build_binary.sh` (macOS ARM64)
- **Packaging:** `./package.sh` creates versioned `.tar.gz` archives

### Build Commands

```bash
# Development (Python)
make dev          # Install with dev dependencies
make test         # Run tests
make run DOMAIN=example.com

# Binary builds
./build_binary.sh              # Build binary to dist/d
./dist/d --version             # Verify version
./package.sh                   # Create tarball in packages/
```

## 📦 Distribution

- **Binary location:** `dist/d` (after build)
- **Packaged releases:** `packages/d-vX.X.X-darwin-arm64.tar.gz`
- **GitHub Releases:** Manual upload via GitHub UI or `gh` CLI
- **Installation docs:** `BINARY_INSTALL.md`

## 🧪 Testing

- Framework: pytest
- Location: `tests/` directory
- Run: `make test` or `pytest`
- Coverage: Configured in `pyproject.toml`

## 🎨 UI Framework

- **Framework:** Textual (Python TUI framework)
- **Widgets:** Custom widgets in `src/dns_debugger/widgets/`
- **Themes:** dark, light, monokai, solarized (via `--theme` flag)
- **Launch:** TUI mode by default, `--no-tui` for CLI mode

## 🔧 Development Notes

### DNS Adapters
The app supports multiple DNS query tools with fallback:
1. `dog` (preferred) - Modern DNS client
2. `dig` (fallback) - Traditional BIND tool

Adapter selection in `src/dns_debugger/adapters/dns/factory.py`

### Architecture Pattern
Clean/Hexagonal Architecture:
- **Domain:** Core business logic (domain-independent)
- **Adapters:** External integrations (DNS, WHOIS, RDAP, SSL)
- **Ports:** Interfaces between domain and adapters
- **Widgets:** UI layer (Textual components)

### Recent Changes
- v0.1.1: Added NS caching, DNSSEC validation indicators, cache busting
- v0.1.0: Initial binary release

## 🚨 Common Pitfalls

1. **Version mismatch**: Forgetting to update both version locations
2. **Stale builds**: Not rebuilding after code changes
3. **Cache issues**: PyInstaller caching old modules (run `make clean` first)
4. **Platform-specific**: Current build is macOS ARM64 only

## 📝 Release Process

See `GITHUB_RELEASE_STEPS.md` for full process:

1. Update versions (both files!)
2. Create release notes: `RELEASE_NOTES_vX.X.X.md`
3. Build: `./build_binary.sh`
4. Package: `./package.sh`
5. Commit and tag: `git tag vX.X.X`
6. Push: `git push origin main --tags`
7. Create GitHub release with binary assets

## 🔗 Key Documentation

- `VERSION_BUMP_CHECKLIST.md` - Version update process
- `BUILD_INSTRUCTIONS.md` - Detailed build instructions
- `DISTRIBUTION.md` - Distribution setup
- `GITHUB_RELEASE_STEPS.md` - Release process
- `README.md` - User-facing documentation

## 💡 Tips for Claude

- Always check both version locations when bumping versions
- Use `./dist/d --version` to verify builds
- The binary is PyInstaller-compiled Python, not Rust/Go
- Project uses modern Python practices (type hints, async where needed)
- Textual uses reactive programming model for UI updates
