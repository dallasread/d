# Version Bump Checklist

This document lists all the files that need to be updated when bumping the version number.

## 📝 Required Version Updates

When releasing a new version (e.g., from 0.1.0 to 0.1.1), update the version in these files:

### 1. `pyproject.toml`
**Location:** `/pyproject.toml`  
**Line:** ~6

```toml
[project]
name = "d-dns-debugger"
version = "0.1.1"  # ← Update this
```

### 2. `src/dns_debugger/__main__.py`
**Location:** `/src/dns_debugger/__main__.py`  
**Line:** ~13

```python
@click.version_option(version="0.1.1", prog_name="d")  # ← Update this
```

## 🔨 Build Steps After Version Update

After updating both files above:

1. **Rebuild the binary:**
   ```bash
   ./build_binary.sh
   ```

2. **Verify the version:**
   ```bash
   ./dist/d --version
   # Should output: d, version 0.1.1
   ```

3. **Package for distribution (optional):**
   ```bash
   ./package.sh
   ```

## 📦 Additional Files to Update (For Release)

If you're creating a GitHub release, you may also need to update:

### Optional Release Documentation
- `RELEASE_NOTES_vX.X.X.md` - Create new release notes for the version
- `RELEASE_vX.X.X.md` - Create release announcement document
- `GITHUB_RELEASE_STEPS.md` - Update to reference new version/tag

## ⚠️ Common Mistakes

1. **Forgetting `__main__.py`**: The version in `pyproject.toml` is NOT automatically used by Click's `@click.version_option`. You MUST update both files.

2. **Not rebuilding**: After updating the version, you must rebuild the binary for the changes to take effect.

3. **Cached builds**: If the version doesn't update after rebuilding, try cleaning first:
   ```bash
   make clean
   ./build_binary.sh
   ```

## ✅ Quick Checklist

Before releasing a new version:

- [ ] Update `pyproject.toml` version
- [ ] Update `src/dns_debugger/__main__.py` version
- [ ] Run `./build_binary.sh`
- [ ] Verify with `./dist/d --version`
- [ ] Create release notes (if needed)
- [ ] Commit version changes
- [ ] Create git tag: `git tag vX.X.X`
- [ ] Push with tags: `git push origin main --tags`

## 🔍 Finding All Version References

To search for hardcoded version strings in the codebase:

```bash
# Search for version patterns
grep -r "0\.1\.[0-9]" --include="*.py" --include="*.toml" src/ pyproject.toml

# Or use ripgrep (rg) if available
rg "0\.1\.[0-9]" -t py -t toml
```

## 📚 Related Documentation

- `BUILD_INSTRUCTIONS.md` - How to build the binary
- `DISTRIBUTION.md` - Distribution and packaging process
- `GITHUB_RELEASE_STEPS.md` - Creating GitHub releases
