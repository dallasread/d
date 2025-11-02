# Version Bump Checklist

This document lists all the files that need to be updated when bumping the version number.

## 📝 Required Version Updates

When releasing a new version (e.g., from 0.2.0 to 0.2.1), update the version in these files:

### 1. `package.json`
**Location:** `/package.json`  
**Line:** ~4

```json
{
  "name": "d-dns-debugger",
  "version": "0.2.1",  // ← Update this
  "type": "module",
  ...
}
```

### 2. `src-tauri/tauri.conf.json`
**Location:** `/src-tauri/tauri.conf.json`  
**Line:** ~3

```json
{
  "$schema": "...",
  "productName": "D",
  "version": "0.2.1",  // ← Update this
  ...
}
```

### 3. `src-tauri/Cargo.toml`
**Location:** `/src-tauri/Cargo.toml`  
**Line:** ~3

```toml
[package]
name = "d-dns-debugger"
version = "0.2.1"  # ← Update this
```

## 🔨 Build Steps After Version Update

After updating all three files above:

1. **Build the application:**
   ```bash
   npm run tauri build
   ```

2. **Verify the build output:**
   The DMG and app bundle will include the new version number:
   - `src-tauri/target/release/bundle/dmg/D_0.2.1_aarch64.dmg`
   - `src-tauri/target/release/bundle/macos/D.app`

## 📦 Additional Files to Update (For Release)

When creating a GitHub release:

### Release Documentation
- `RELEASE_NOTES_vX.X.X.md` - Create new release notes for the version
- Update DMG creation commands in `GITHUB_RELEASE_STEPS.md` to reference new version

## ⚠️ Common Mistakes

1. **Forgetting one of the three files**: All three files must be updated - `package.json`, `tauri.conf.json`, AND `Cargo.toml`.

2. **Version mismatch**: All three files must have the exact same version number.

3. **Not rebuilding**: After updating the version, you must rebuild for changes to take effect.

## ✅ Quick Checklist

Before releasing a new version:

- [ ] Update `package.json` version
- [ ] Update `src-tauri/tauri.conf.json` version
- [ ] Update `src-tauri/Cargo.toml` version
- [ ] Verify all three versions match
- [ ] Run `npm run tauri build`
- [ ] Create release notes
- [ ] Commit version changes
- [ ] Create git tag: `git tag vX.X.X`
- [ ] Push with tags: `git push origin main --tags`
- [ ] Build binaries from the tag (see `GITHUB_RELEASE_STEPS.md`)

## 🔍 Finding All Version References

To search for hardcoded version strings in the codebase:

```bash
# Search for version patterns in config files
grep -r "0\.2\.[0-9]" package.json src-tauri/tauri.conf.json src-tauri/Cargo.toml

# Or use ripgrep (rg) if available
rg "0\.2\.[0-9]" package.json src-tauri/
```

## 📚 Related Documentation

- `BUILD_INSTRUCTIONS.md` - How to build the application
- `GITHUB_RELEASE_STEPS.md` - Creating GitHub releases
