# Tauri Rewrite Plan: Cross-Platform DNS Debugger

## Executive Summary

Rewrite the `d` DNS debugger from Python/Textual to Rust/Tauri to achieve:
- ✅ Cross-platform support: macOS, iOS, Linux, Windows, Web
- ✅ No external dependencies (dog, dig, whois)
- ✅ Single codebase for desktop and mobile
- ✅ Pure Rust implementations for DNS, WHOIS, SSL
- ✅ Modern UI with native performance

## Development Branch

**IMPORTANT:** All work for this rewrite must be done in the `with-rust` branch.

```bash
# Create and switch to the development branch
git checkout -b with-rust

# All commits and work happen here
git add .
git commit -m "Your changes"

# Push to remote
git push origin with-rust

# When ready, create PR to merge into main
```

**Branch Strategy:**
- `main` - Continues to maintain the Python/Textual version
- `with-rust` - All Rust/Tauri development happens here
- Once the Rust version reaches feature parity and stability, merge to `main`
- Keep both versions available during transition period if needed

## Current Architecture (Python/Textual)

```
d/
├── src/dns_debugger/
│   ├── __main__.py           # Entry point
│   ├── app.py                # Textual TUI
│   ├── adapters/             # External tool integrations
│   │   ├── dns/              # dog/dig wrappers
│   │   ├── whois/            # whois command wrapper
│   │   └── ssl/              # openssl wrapper
│   ├── domain/               # Business logic
│   └── widgets/              # Textual UI components
```

**Limitations:**
- macOS ARM64 only
- Requires external binaries (dog/dig/whois)
- PyInstaller complexity
- No mobile support
- No web deployment option

## Target Architecture (Rust/Tauri)

```
d-tauri/
├── src-tauri/                # Rust backend
│   ├── src/
│   │   ├── main.rs           # Tauri entry point
│   │   ├── commands/         # Tauri commands (API for frontend)
│   │   ├── dns/              # Pure Rust DNS implementation
│   │   ├── whois/            # Pure Rust WHOIS implementation
│   │   ├── ssl/              # Pure Rust SSL/TLS implementation
│   │   ├── rdap/             # RDAP client (modern WHOIS)
│   │   └── domain/           # Core business logic
│   ├── Cargo.toml            # Rust dependencies
│   └── tauri.conf.json       # Tauri configuration
├── src/                      # Frontend (TypeScript/React or Svelte)
│   ├── components/           # UI components
│   ├── stores/               # State management
│   └── main.ts               # Frontend entry point
└── package.json              # Node dependencies
```

## Phase 1: Research & Prototyping (1-2 weeks)

### 1.1 Rust DNS Library Evaluation

**Primary candidate: `hickory-dns` (formerly trust-dns)**

```toml
[dependencies]
hickory-resolver = "0.24"
hickory-client = "0.24"
```

**Evaluate features:**
- [ ] A, AAAA, MX, NS, SOA, TXT, CNAME records
- [ ] DNSSEC validation
- [ ] Custom nameserver selection
- [ ] Async/await support (tokio)
- [ ] Error handling and timeouts
- [ ] Platform compatibility (macOS, iOS, Linux, Windows)

**Prototype tasks:**
- [ ] Create simple DNS query CLI in Rust
- [ ] Test all record types from current tool
- [ ] Compare output format with `dog`
- [ ] Benchmark performance
- [ ] Test on macOS, Linux (VM), iOS simulator

### 1.2 WHOIS Implementation Strategy

**Two approaches:**

#### Approach A: Direct TCP WHOIS
```toml
[dependencies]
tokio = { version = "1.0", features = ["net", "io-util", "rt-multi-thread"] }
```

**Pros:**
- Traditional WHOIS protocol
- Works with all TLDs
- No external dependencies

**Cons:**
- Need WHOIS server database for each TLD
- Rate limiting issues
- Parsing complexity

#### Approach B: RDAP (Recommended)
```toml
[dependencies]
reqwest = { version = "0.11", features = ["json"] }
serde = { version = "1.0", features = ["derive"] }
```

**Pros:**
- Modern, RESTful API
- JSON responses (easier parsing)
- Standardized across registries
- Better for mobile (HTTPS vs raw TCP)

**Cons:**
- Not all registries support it (yet)
- Fallback to WHOIS still needed

**Prototype tasks:**
- [ ] Implement RDAP client for .com/.net
- [ ] Implement fallback WHOIS for other TLDs
- [ ] Create TLD → WHOIS server mapping
- [ ] Test with current domain examples
- [ ] Compare output with current tool

### 1.3 SSL/TLS Certificate Inspection

```toml
[dependencies]
rustls = "0.23"
tokio-rustls = "0.26"
webpki = "0.22"
x509-parser = "0.16"
```

**Prototype tasks:**
- [ ] Connect to HTTPS servers
- [ ] Extract certificate chain
- [ ] Parse certificate details (issuer, validity, SAN)
- [ ] Validate certificate trust chain
- [ ] Display certificate transparency logs
- [ ] Test on various domains

### 1.4 Tauri Setup & Frontend Choice

**Frontend options:**

| Framework | Pros | Cons |
|-----------|------|------|
| **React** | Popular, rich ecosystem, TypeScript | Larger bundle |
| **Svelte** | Smaller bundle, simpler syntax | Smaller ecosystem |
| **Solid.js** | Reactive, fast | Newer, less mature |
| **Vanilla** | No framework overhead | More boilerplate |

**Recommendation: Svelte**
- Smaller binary size (important for mobile)
- Reactive by default (good for real-time DNS updates)
- TypeScript support
- Good Tauri integration

**Prototype tasks:**
- [ ] Set up basic Tauri app with Svelte
- [ ] Create simple DNS query UI
- [ ] Test Rust ↔ Frontend communication
- [ ] Test on macOS desktop
- [ ] Test on iOS simulator
- [ ] Test on Linux (VM)

## Phase 2: Core Backend Implementation (3-4 weeks)

### 2.1 DNS Module

**File: `src-tauri/src/dns/mod.rs`**

```rust
pub mod resolver;
pub mod types;
pub mod cache;

use hickory_resolver::TokioAsyncResolver;

pub struct DnsClient {
    resolver: TokioAsyncResolver,
    cache: Cache,
}

impl DnsClient {
    pub async fn query(&self, domain: &str, record_type: RecordType) -> Result<DnsResponse>;
    pub async fn query_nameserver(&self, domain: &str, ns: &str, record_type: RecordType) -> Result<DnsResponse>;
    pub async fn trace_delegation(&self, domain: &str) -> Result<Vec<DelegationStep>>;
}
```

**Features to implement:**
- [ ] Basic record queries (A, AAAA, MX, NS, SOA, TXT, CNAME)
- [ ] DNSSEC validation
- [ ] Custom nameserver queries
- [ ] NS record caching (like current tool)
- [ ] Cache busting option
- [ ] Query timing/performance metrics
- [ ] Parallel queries for multiple record types
- [ ] Error handling with detailed messages

### 2.2 WHOIS/RDAP Module

**File: `src-tauri/src/whois/mod.rs`**

```rust
pub mod rdap;
pub mod whois_tcp;
pub mod parser;

pub struct WhoisClient {
    http_client: reqwest::Client,
    server_map: HashMap<String, String>,
}

impl WhoisClient {
    pub async fn query(&self, domain: &str) -> Result<WhoisRecord>;
    pub async fn query_ip(&self, ip: &str) -> Result<IpWhoisRecord>;
}
```

**Features to implement:**
- [ ] RDAP client for supported TLDs
- [ ] Fallback TCP WHOIS for unsupported TLDs
- [ ] TLD → server mapping (bootstrap from IANA)
- [ ] Referral following (thick vs thin WHOIS)
- [ ] Response parsing (registrar, dates, nameservers)
- [ ] IP WHOIS (RIR lookups)
- [ ] Rate limiting / retry logic
- [ ] Caching

### 2.3 SSL/TLS Module

**File: `src-tauri/src/ssl/mod.rs`**

```rust
pub mod certificate;
pub mod chain;
pub mod validation;

pub struct SslClient;

impl SslClient {
    pub async fn get_certificate(&self, domain: &str, port: u16) -> Result<Certificate>;
    pub async fn validate_chain(&self, cert: &Certificate) -> Result<ValidationResult>;
    pub async fn check_transparency_logs(&self, cert: &Certificate) -> Result<Vec<CtLog>>;
}
```

**Features to implement:**
- [ ] TLS connection and cert retrieval
- [ ] Certificate parsing (X.509)
- [ ] Chain validation
- [ ] Expiry checking
- [ ] SAN extraction
- [ ] Certificate transparency lookup
- [ ] OCSP stapling check
- [ ] Protocol/cipher suite info

### 2.4 Tauri Commands (API Layer)

**File: `src-tauri/src/commands/mod.rs`**

```rust
use tauri::command;

#[command]
pub async fn query_dns(
    domain: String,
    record_type: String,
    nameserver: Option<String>
) -> Result<DnsResponse, String> {
    // Implementation
}

#[command]
pub async fn query_whois(domain: String) -> Result<WhoisRecord, String> {
    // Implementation
}

#[command]
pub async fn query_ssl(domain: String, port: u16) -> Result<Certificate, String> {
    // Implementation
}

#[command]
pub async fn analyze_domain(domain: String) -> Result<DomainAnalysis, String> {
    // Parallel queries for DNS, WHOIS, SSL
    // Aggregate results
}
```

**Error handling:**
- [ ] Convert Rust errors to JSON-serializable errors
- [ ] Include helpful error messages
- [ ] Handle timeouts gracefully
- [ ] Provide retry mechanisms

## Phase 3: Frontend Implementation (2-3 weeks)

### 3.1 Component Architecture (Svelte)

```
src/
├── lib/
│   ├── components/
│   │   ├── DnsTab.svelte           # DNS records view
│   │   ├── WhoisTab.svelte         # WHOIS data view
│   │   ├── SslTab.svelte           # SSL/TLS cert view
│   │   ├── EmailTab.svelte         # MX, SPF, DKIM, DMARC
│   │   ├── DnssecTab.svelte        # DNSSEC validation
│   │   ├── RecordCard.svelte       # Individual record display
│   │   └── LoadingSpinner.svelte   # Loading states
│   ├── stores/
│   │   ├── domain.ts               # Domain state
│   │   ├── dns.ts                  # DNS results
│   │   ├── whois.ts                # WHOIS results
│   │   └── ssl.ts                  # SSL results
│   ├── services/
│   │   └── tauri.ts                # Tauri command wrappers
│   └── types/
│       └── index.ts                # TypeScript types
├── App.svelte                      # Main app component
└── main.ts                         # Entry point
```

### 3.2 State Management

```typescript
// stores/domain.ts
import { writable } from 'svelte/store';

export const currentDomain = writable<string>('');
export const isLoading = writable<boolean>(false);
export const activeTab = writable<string>('dns');
```

### 3.3 Tauri Integration

```typescript
// services/tauri.ts
import { invoke } from '@tauri-apps/api/tauri';

export async function queryDns(
  domain: string,
  recordType: string,
  nameserver?: string
): Promise<DnsResponse> {
  return await invoke('query_dns', { domain, recordType, nameserver });
}

export async function queryWhois(domain: string): Promise<WhoisRecord> {
  return await invoke('query_whois', { domain });
}

export async function querySsl(domain: string, port: number): Promise<Certificate> {
  return await invoke('query_ssl', { domain, port });
}
```

### 3.4 UI Features

**Implement features from current tool:**
- [ ] Domain input with validation
- [ ] Tabbed interface (DNS, WHOIS, SSL, Email, DNSSEC)
- [ ] Copy to clipboard functionality
- [ ] Theme support (dark, light, monokai, solarized)
- [ ] Loading states and spinners
- [ ] Error display with helpful messages
- [ ] Record type filtering
- [ ] Nameserver selection
- [ ] Cache control toggle
- [ ] Export results (JSON, text)

**New features enabled by Tauri:**
- [ ] Multiple domain tabs (compare domains)
- [ ] History/favorites
- [ ] Scheduled monitoring
- [ ] Notifications for cert expiry
- [ ] Diff view for record changes

## Phase 4: Mobile Implementation (iOS) (2 weeks)

### 4.1 Tauri Mobile Setup

```bash
# Install Tauri mobile tools
cargo install tauri-cli --version "^2.0.0-beta"

# Initialize mobile
cargo tauri ios init
```

### 4.2 iOS-Specific Considerations

**Configuration: `src-tauri/tauri.conf.json`**

```json
{
  "tauri": {
    "bundle": {
      "iOS": {
        "minimumSystemVersion": "13.0"
      }
    }
  }
}
```

**Tasks:**
- [ ] Test DNS queries on iOS simulator
- [ ] Test on physical iPhone
- [ ] Optimize UI for mobile (touch targets, scrolling)
- [ ] Handle iOS permissions (network access)
- [ ] Test battery impact
- [ ] Handle background/foreground transitions
- [ ] Add iOS-specific UI (native navigation)

### 4.3 Mobile UI Adaptations

**Responsive design:**
- [ ] Mobile-first layout
- [ ] Hamburger menu for navigation
- [ ] Bottom sheet for details
- [ ] Pull-to-refresh
- [ ] Swipe gestures
- [ ] Native share sheet integration

## Phase 5: Linux & Windows Support (1 week)

### 5.1 Linux

**Test on distributions:**
- [ ] Ubuntu 22.04 LTS (Debian-based)
- [ ] Fedora 39 (RPM-based)
- [ ] Arch Linux (rolling)
- [ ] Alpine Linux (musl)

**Packaging:**
- [ ] AppImage (universal)
- [ ] .deb package (Debian/Ubuntu)
- [ ] .rpm package (Fedora/RHEL)
- [ ] AUR package (Arch)
- [ ] Flatpak (optional)

### 5.2 Windows

**Test on:**
- [ ] Windows 11
- [ ] Windows 10

**Packaging:**
- [ ] .msi installer
- [ ] Portable .exe
- [ ] winget package (optional)
- [ ] Chocolatey package (optional)

## Phase 6: Testing & Quality Assurance (2 weeks)

### 6.1 Unit Tests

```rust
// src-tauri/src/dns/resolver.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_query_a_record() {
        let client = DnsClient::new().unwrap();
        let result = client.query("example.com", RecordType::A).await;
        assert!(result.is_ok());
    }
}
```

**Coverage targets:**
- [ ] DNS module: 80%+
- [ ] WHOIS module: 70%+
- [ ] SSL module: 70%+
- [ ] Commands: 60%+

### 6.2 Integration Tests

```typescript
// src/__tests__/integration.test.ts
import { test, expect } from 'vitest';
import { queryDns } from '../services/tauri';

test('DNS query returns valid results', async () => {
  const result = await queryDns('example.com', 'A');
  expect(result.records).toBeDefined();
  expect(result.records.length).toBeGreaterThan(0);
});
```

### 6.3 E2E Tests

**Use Tauri WebDriver:**

```typescript
import { expect } from '@wdio/globals';

describe('DNS Debugger App', () => {
  it('should query a domain', async () => {
    await browser.url('/');
    const input = await $('input[name="domain"]');
    await input.setValue('example.com');
    await browser.keys('Enter');
    
    const results = await $('.dns-results');
    await expect(results).toBeDisplayed();
  });
});
```

### 6.4 Performance Testing

**Benchmarks:**
- [ ] DNS query latency (< 100ms for cached)
- [ ] WHOIS query latency (< 2s)
- [ ] SSL query latency (< 1s)
- [ ] UI render time (< 16ms for 60fps)
- [ ] Binary size (< 20MB for desktop, < 50MB for mobile)
- [ ] Memory usage (< 100MB idle)

### 6.5 Manual Testing Matrix

| Feature | macOS | iOS | Linux | Windows |
|---------|-------|-----|-------|---------|
| DNS queries | ⬜ | ⬜ | ⬜ | ⬜ |
| WHOIS queries | ⬜ | ⬜ | ⬜ | ⬜ |
| SSL cert inspection | ⬜ | ⬜ | ⬜ | ⬜ |
| DNSSEC validation | ⬜ | ⬜ | ⬜ | ⬜ |
| Theme switching | ⬜ | ⬜ | ⬜ | ⬜ |
| Copy to clipboard | ⬜ | ⬜ | ⬜ | ⬜ |
| Export results | ⬜ | ⬜ | ⬜ | ⬜ |

## Phase 7: Documentation & Release (1 week)

### 7.1 Documentation

**Create/update:**
- [ ] README.md (project overview, features, installation)
- [ ] BUILDING.md (build instructions for all platforms)
- [ ] CONTRIBUTING.md (contribution guidelines)
- [ ] API.md (Tauri command reference)
- [ ] ARCHITECTURE.md (system design documentation)
- [ ] MIGRATION.md (migrating from Python version)
- [ ] User guide (screenshots, examples)

### 7.2 GitHub Release Preparation

**Assets to build:**
- [ ] macOS Intel: `d-vX.X.X-darwin-x64.dmg`
- [ ] macOS ARM: `d-vX.X.X-darwin-arm64.dmg`
- [ ] Linux AppImage: `d-vX.X.X-x86_64.AppImage`
- [ ] Linux .deb: `d-vX.X.X-amd64.deb`
- [ ] Linux .rpm: `d-vX.X.X-x86_64.rpm`
- [ ] Windows: `d-vX.X.X-x64.msi`
- [ ] iOS: Submit to TestFlight / App Store

### 7.3 Release Notes

```markdown
# v1.0.0 - Tauri Rewrite

## 🚀 Major Changes

- Complete rewrite in Rust + Tauri
- Cross-platform: macOS, iOS, Linux, Windows
- No external dependencies (dog, dig, whois no longer needed)
- 10x faster DNS queries
- Native mobile app (iOS)

## ✨ New Features

- Multi-tab domain comparison
- History and favorites
- Export to JSON/CSV
- RDAP support (modern WHOIS)
- Real-time certificate monitoring

## 🔧 Technical Improvements

- Pure Rust DNS resolver (hickory-dns)
- Async/await throughout
- Better error handling
- Smaller binary size
- Lower memory usage

## 📦 Installation

See BUILDING.md for platform-specific instructions.

## 🔄 Migration from Python Version

The Tauri version is a drop-in replacement. See MIGRATION.md for details.
```

## Phase 8: Post-Release (Ongoing)

### 8.1 Monitoring

**Set up:**
- [ ] GitHub issues for bug reports
- [ ] GitHub Discussions for feature requests
- [ ] Crash reporting (Sentry or similar)
- [ ] Analytics (privacy-respecting)

### 8.2 Maintenance Plan

**Regular tasks:**
- [ ] Dependency updates (Dependabot)
- [ ] Security audits (`cargo audit`)
- [ ] Performance monitoring
- [ ] User feedback triage
- [ ] Bug fixes
- [ ] Feature additions

### 8.3 Future Enhancements

**Potential features:**
- [ ] Web version (via Tauri's web target)
- [ ] Android support
- [ ] Collaborative features (share results)
- [ ] API for automation
- [ ] Plugins/extensions system
- [ ] DNS server monitoring
- [ ] Zone file editor
- [ ] Bulk domain analysis

## Technology Stack Summary

### Backend (Rust)
```toml
[dependencies]
tauri = { version = "2.0", features = ["mobile"] }
tokio = { version = "1.0", features = ["full"] }
hickory-resolver = "0.24"      # DNS queries
hickory-client = "0.24"        # Advanced DNS features
reqwest = { version = "0.11", features = ["json"] }  # RDAP/HTTP
rustls = "0.23"                # SSL/TLS
tokio-rustls = "0.26"          # Async TLS
x509-parser = "0.16"           # Certificate parsing
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
```

### Frontend (TypeScript/Svelte)
```json
{
  "dependencies": {
    "svelte": "^4.0.0",
    "@tauri-apps/api": "^2.0.0",
    "@tauri-apps/plugin-shell": "^2.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "@sveltejs/vite-plugin-svelte": "^3.0.0",
    "vitest": "^1.0.0"
  }
}
```

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Research & Prototyping | 1-2 weeks | None |
| Phase 2: Core Backend | 3-4 weeks | Phase 1 |
| Phase 3: Frontend | 2-3 weeks | Phase 2 |
| Phase 4: Mobile (iOS) | 2 weeks | Phase 3 |
| Phase 5: Linux & Windows | 1 week | Phase 3 |
| Phase 6: Testing & QA | 2 weeks | Phase 5 |
| Phase 7: Documentation & Release | 1 week | Phase 6 |

**Total: 12-17 weeks (~3-4 months)**

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| iOS limitations (socket access) | Low | High | Prototype early (Phase 1) |
| DNSSEC complexity | Medium | Medium | Use battle-tested library (hickory-dns) |
| WHOIS server inconsistencies | High | Low | Robust parsing, RDAP fallback |
| Tauri Mobile maturity | Medium | High | Join Tauri Discord, contribute fixes |
| Performance on mobile | Low | Medium | Profile early, optimize critical paths |
| Binary size bloat | Low | Medium | Strip symbols, optimize release builds |

## Success Metrics

- [ ] Feature parity with Python version (100%)
- [ ] Works on macOS, iOS, Linux, Windows
- [ ] No external dependencies required
- [ ] Binary size < 20MB (desktop), < 50MB (mobile)
- [ ] DNS queries < 100ms (cached)
- [ ] Test coverage > 70%
- [ ] User satisfaction (GitHub stars, positive feedback)
- [ ] App Store approval (iOS)

## Questions to Answer During Research

1. Does `hickory-dns` support all DNS record types we need?
2. Does DNSSEC validation work on iOS?
3. Can we implement RDAP for all major TLDs?
4. What's the binary size with all dependencies?
5. How's the performance compared to native tools?
6. Can we use the same UI code for desktop and mobile?
7. What's the learning curve for team members?
8. Are there any iOS App Store restrictions on DNS tools?

## Next Steps

1. ✅ Review this plan
2. ⬜ Create `with-rust` branch
3. ⬜ Start Phase 1: Create Rust prototypes
4. ⬜ Test DNS queries with `hickory-dns`
5. ⬜ Test WHOIS/RDAP client
6. ⬜ Set up basic Tauri + Svelte project
7. ⬜ Make go/no-go decision based on prototype results

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-02  
**Author:** Claude  
**Status:** Planning
