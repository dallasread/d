# v0.1.2 - Documentation & Developer Experience

**Release Title:** `v0.1.2 - Documentation & Developer Experience Improvements`

---

## 📚 What's New

This release focuses on improving the developer experience and ensuring consistent version management across the codebase.

## 🔧 Improvements

### Version Management
- **Added Version Bump Checklist**: New `VERSION_BUMP_CHECKLIST.md` document that clearly outlines all files that need updating when releasing a new version
- **Documented Dual-Version Requirement**: Clarified why both `pyproject.toml` and `src/dns_debugger/__main__.py` must be updated (Click doesn't auto-read from pyproject.toml)
- **Added Quick Reference Commands**: Included grep/ripgrep commands to find all version references in the codebase

### Project Documentation
- **Added `.claude/CLAUDE.md`**: Project-specific context file for AI assistants with comprehensive project information including:
  - Architecture patterns (Clean/Hexagonal Architecture)
  - Build system details
  - Common pitfalls and tips
  - Version management reminders
  - Project structure overview
  - Key documentation references

## 🐛 Bug Fixes
- Fixed version display in binary - now correctly shows 0.1.2 instead of 0.1.0

## 📦 Download

The `d` binary is included in this release (17MB, macOS ARM64).

## Installation

```bash
# Download the binary
curl -L https://github.com/dallasread/d/releases/download/v0.1.2/d-v0.1.2-darwin-arm64.tar.gz -o d.tar.gz

# Extract
tar -xzf d.tar.gz

# Make executable
chmod +x d

# Optional: Install system-wide
sudo mv d /usr/local/bin/
```

## Usage

```bash
d example.com
d --version  # Should now show: d, version 0.1.2
```

## Requirements

- macOS ARM64 (Apple Silicon)
- `dig` command (usually pre-installed)
- `openssl` command (usually pre-installed)

## For Developers

If you're contributing to this project:

1. **Before bumping versions**, read `VERSION_BUMP_CHECKLIST.md`
2. **For project context**, check `.claude/CLAUDE.md`
3. **For build instructions**, see `BUILD_INSTRUCTIONS.md`

## What's Changed

- Bump version to 0.1.2 by @dallasread
- Add .claude/CLAUDE.md for project-specific AI context by @dallasread
- Add VERSION_BUMP_CHECKLIST.md documentation by @dallasread
- Fix version display in pyproject.toml and __main__.py by @dallasread

**Full Changelog**: https://github.com/dallasread/d/compare/v0.1.1...v0.1.2

---

## Previous Releases

For v0.1.1 changes (DNSSEC improvements, NS caching, performance optimizations), see [v0.1.1 release notes](https://github.com/dallasread/d/releases/tag/v0.1.1).
