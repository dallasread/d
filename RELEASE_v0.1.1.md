# v0.1.1 - Performance & DNSSEC Improvements

## 🚀 Performance Improvements
- **NS Caching**: Added smart caching for authoritative nameserver lookups - eliminates redundant DNS queries and prevents loading indicator flashing
- **Cache Busting**: Press `r` to refresh and clear all caches for fresh data
- **Faster Loading**: Reduced HTTP/HTTPS timeouts from 10s to 5s
- **Faster Certificate Checks**: Optimized OpenSSL certificate validation (~17s → ~8s per domain)
  - Removed slow TLS version probing, cipher suite detection, and OCSP checks
  - Improved timeout handling for unresponsive hosts

## 🔒 DNSSEC Fixes
- **Accurate Validation**: Now correctly detects mismatched DS/DNSKEY records (broken DNSSEC chains show as BOGUS instead of SECURE)
- **Parent Zone Queries**: DS records are now queried from the correct parent zone's authoritative nameservers
- **Better Visualization**: Fixed dangling connection lines in DNSSEC chain visualization
- **Neutral RRSIG Indicator**: Changed RRSIG presence from positive indicator to neutral observation

## 🧹 Codebase Improvements
- **Simplified DNS Stack**: Removed dog adapter - now uses dig exclusively for better compatibility
- **Cleaner Code**: Removed unnecessary progress callbacks that caused UI flashing

## 📦 Download
The `d` binary is included in this release (17MB, macOS ARM64).

## Installation
```bash
# Download and make executable
curl -L https://github.com/dallasread/d/releases/download/v0.1.1/d -o d
chmod +x d

# Optional: Install system-wide
sudo mv d /usr/local/bin/
```

## Usage
```bash
d example.com
```

## Requirements
- macOS ARM64 (Apple Silicon)
- `dig` command (usually pre-installed)
- `openssl` command (usually pre-installed)
- `curl` or `wget` command

## What's Changed
- Build v0.1.1 binary with NS caching improvements by @dallasread
- Add cache busting when pressing 'r' to refresh by @dallasread
- Add caching for authoritative nameserver lookups to prevent flashing by @dallasread
- Fix DS record queries to use parent zone's authoritative nameservers by @dallasread
- Change RRSIG message to neutral indicator by @dallasread
- Remove dog adapter and use dig exclusively by @dallasread
- Fix DNSSEC validation to detect mismatched DS/DNSKEY records by @dallasread
- Reduce HTTP and certificate check timeouts for faster loading by @dallasread
- Fix dangling lines in DNSSEC visualization and improve cert check performance by @dallasread

**Full Changelog**: https://github.com/dallasread/d/compare/v0.1.0...v0.1.1
