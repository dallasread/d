# Tauri Migration Plan - DNS Debugger (d)

## Overview

This document outlines the plan to migrate the D DNS Debugger from a Python/Textual TUI application to a Tauri desktop application for macOS.

## Current Architecture

**Stack:**
- Language: Python 3.8+
- UI Framework: Textual (Terminal UI)
- Architecture: Hexagonal (Ports & Adapters)
- External Tools: dig, openssl, curl, whois
- Version: 0.1.2

**Key Features:**
- 7 panels: Dashboard + 6 detail views (Registration, DNS, DNSSEC, Certificate, HTTP/HTTPS, Email)
- Parallel data fetching (5-10 seconds total load time)
- DNSSEC chain visualization with color-coded key tags
- Email security scoring (SPF/DKIM/DMARC)
- Certificate chain inspection
- HTTP redirect analysis
- Domain expiration tracking

## Target Architecture

**Stack:**
- Backend: Rust (Tauri commands)
- Frontend: React + TypeScript
- State Management: Zustand or Redux
- Styling: TailwindCSS
- Build Target: macOS (initially)

**Architecture Pattern:**
```
┌─────────────────────────────────────┐
│   React Frontend (TypeScript)       │
│   - UI Components (7 panels)        │
│   - State Management                │
│   - Theme System                    │
├─────────────────────────────────────┤
│   Tauri IPC Layer                   │
├─────────────────────────────────────┤
│   Rust Backend (Tauri Commands)     │
│   - Adapter Layer                   │
│   - System Tool Execution           │
│   - Business Logic                  │
└─────────────────────────────────────┘
```

## Migration Tasks

### Phase 1: Project Setup
1. **Initialize Tauri project structure in app/ folder**
   - Create new Tauri app with React template
   - Configure for macOS builds
   - Set up TypeScript + TailwindCSS
   - Configure build scripts

### Phase 2: Rust Backend (Tauri Commands)

2. **Set up Rust backend with Tauri commands for system tool execution**
   - Create command execution framework
   - Add error handling patterns
   - Implement tool availability checks

3. **Implement DNS adapter in Rust (dig command execution and parsing)**
   - Execute dig commands
   - Parse dig output for A, AAAA, MX, TXT, NS, SOA records
   - Implement DNSKEY parsing with keytag extraction
   - Implement DS record parsing
   - Add authoritative nameserver caching
   - Implement cache clearing for refresh

4. **Implement Certificate adapter in Rust (openssl execution)**
   - Execute `openssl s_client` for TLS connection
   - Parse certificate chain from output
   - Extract X.509 fields (subject, issuer, dates, SANs)
   - Calculate fingerprint
   - Validate certificate chain
   - Check expiration status

5. **Implement WHOIS adapter in Rust (whois command)**
   - Execute whois command
   - Parse WHOIS output with regex
   - Extract registrar, dates, nameservers, contacts
   - Handle various WHOIS formats
   - Parse domain status codes

6. **Implement HTTP adapter in Rust (curl execution)**
   - Execute curl with redirect following
   - Parse HTTP status codes
   - Extract redirect chains
   - Get response timing
   - Parse headers
   - Test both apex and www variants

7. **Implement Email adapter logic in Rust**
   - Query MX records via DNS
   - Query SPF from TXT records
   - Check DKIM selectors (11 common ones)
   - Query DMARC from _dmarc subdomain
   - Parse SPF mechanisms
   - Parse DMARC policies
   - Calculate security score (0-100)

8. **Implement DNSSEC chain validation logic in Rust**
   - Recursive chain building (root → TLD → domain)
   - Query DNSKEY records for each zone
   - Query DS records from parent zones
   - Query RRSIG records
   - Calculate 18-color keytag palette
   - Validate chain of trust
   - Track RRSIG expiration

### Phase 3: TypeScript Domain Models

9. **Create TypeScript models matching Python domain models**
   - DNSRecord, DNSQuery, DNSResponse
   - Certificate, CertificateChain, TLSInfo
   - DNSSECValidation, DNSSECChain, ZoneData
   - DomainRegistration, Contact, Nameserver
   - HTTPResponse, HTTPRedirect
   - EmailConfiguration, SPFRecord, DKIMRecord, DMARCRecord
   - Health check models (6 health types)

### Phase 4: React Frontend

10. **Set up React frontend with routing for 7 panels**
    - Tab-based navigation
    - Keyboard shortcuts (0-6 for tabs, R for refresh, L for logs)
    - Panel container component
    - Loading states

11. **Implement Dashboard panel UI**
    - 3x2 grid layout + registration card
    - 6 health check cards
    - Overall health summary
    - Color-coded status indicators

12. **Implement Registration panel UI**
    - Registrar information
    - Dates (created, updated, expires)
    - Expiration countdown
    - Nameserver list with IPs
    - Contact information display
    - Status codes
    - DNSSEC indicator

13. **Implement DNS panel UI**
    - A records table
    - AAAA records table
    - MX records with priority
    - TXT records display
    - NS records table

14. **Implement DNSSEC panel UI with chain visualization**
    - Zone-by-zone chain display
    - DNSKEY table (keytag, algo, type, pubkey)
    - DS table (keytag, algo, digest type, hash)
    - RRSIG display with expiration
    - Color-coded keytag matching
    - Chain of trust validation status

15. **Implement Certificate panel UI**
    - Certificate subject display
    - Issuer information
    - Validity dates
    - Days until expiry (color-coded)
    - SANs list
    - Public key info
    - Fingerprint
    - Chain status

16. **Implement HTTP/HTTPS panel UI**
    - Status for apex domain
    - Status for www subdomain
    - Color-coded status codes
    - Response time display
    - Redirect chain visualization
    - Headers display

17. **Implement Email panel UI with security scoring**
    - MX records table
    - Email provider detection
    - SPF status and policy
    - DKIM status and selectors
    - DMARC policy display
    - Security score (0-100) visualization

### Phase 5: Application Features

18. **Implement state management using Zustand or Redux**
    - Global AppState
    - Domain-specific state slices
    - State update actions
    - Cache management
    - Loading state tracking

19. **Implement parallel data fetching with loading indicators**
    - Concurrent Tauri command invocations
    - Progress tracking per data source
    - Error handling per source
    - Retry logic
    - Refresh functionality

20. **Implement raw data modal for JSON/tool output**
    - Modal overlay component
    - JSON view (pretty-printed)
    - Raw tool output view
    - Toggle between views
    - Syntax highlighting
    - Copy to clipboard

21. **Implement keyboard shortcuts and navigation**
    - Tab switching (0-6, Tab, Shift+Tab)
    - Refresh (R key)
    - Logs modal (L key)
    - Toggle raw/JSON (T key)
    - Help (H key)
    - Quit (Q key or Cmd+Q)
    - ESC to close modals

22. **Implement theme system (dark, light, monokai, solarized)**
    - Theme definitions
    - Theme switcher UI
    - CSS variable system
    - Persistent theme preference
    - Command-line theme option

### Phase 6: Build & Distribution

23. **Add build scripts and configuration for macOS**
    - Tauri build configuration
    - App icon and metadata
    - Code signing (optional)
    - DMG creation
    - Version management (sync with pyproject.toml)

24. **Test complete application workflow**
    - Test all 7 panels
    - Test data fetching and refresh
    - Test keyboard shortcuts
    - Test themes
    - Test error handling
    - Performance benchmarking
    - Memory usage testing

## Key Implementation Details

### Rust Backend Pattern

```rust
#[tauri::command]
async fn query_dns(domain: String, record_type: String) -> Result<DNSResponse, String> {
    // Execute dig command
    // Parse output
    // Return structured data
}

#[tauri::command]
async fn fetch_all_data(domain: String) -> Result<AppState, String> {
    // Execute all queries in parallel using tokio
    // Aggregate results
    // Return complete state
}
```

### Frontend Data Fetching Pattern

```typescript
// Invoke Tauri command
const fetchData = async (domain: string) => {
  try {
    const data = await invoke<AppState>('fetch_all_data', { domain });
    updateState(data);
  } catch (error) {
    handleError(error);
  }
};
```

### DNSSEC Chain Algorithm

The DNSSEC chain building is a critical feature requiring careful translation:

1. Start from root (.)
2. Query DNSKEY records for current zone
3. Query DS records for child zone from current zone
4. Move to child zone and repeat
5. Continue until reaching target domain
6. Calculate keytag colors using 18-color palette
7. Match DNSKEY keytags to DS keytags visually

### Email Security Scoring

```
Base points:
- MX records exist: +20
- SPF exists: +15
- SPF has -all: +10
- DKIM found: +25
- DMARC exists: +15
- DMARC has quarantine/reject: +10
- DMARC has reporting: +5

Total: 0-100 points
```

## Directory Structure (app/)

```
app/
├── src-tauri/              # Rust backend
│   ├── src/
│   │   ├── main.rs         # Tauri app setup
│   │   ├── commands/       # Tauri commands
│   │   ├── adapters/       # System tool adapters
│   │   ├── models/         # Rust data structures
│   │   └── utils/          # Helper functions
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/                    # React frontend
│   ├── components/         # React components
│   │   ├── Dashboard.tsx
│   │   ├── Registration.tsx
│   │   ├── DNS.tsx
│   │   ├── DNSSEC.tsx
│   │   ├── Certificate.tsx
│   │   ├── HTTP.tsx
│   │   ├── Email.tsx
│   │   └── RawDataModal.tsx
│   ├── models/             # TypeScript types
│   ├── store/              # State management
│   ├── themes/             # Theme definitions
│   ├── utils/              # Helper functions
│   ├── App.tsx
│   └── main.tsx
├── public/                 # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

## Dependencies

### Rust (Cargo.toml)
```toml
[dependencies]
tauri = "1.5"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1.0", features = ["full"] }
regex = "1.0"
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tauri-apps/api": "^1.5.0",
    "zustand": "^4.4.0",
    "tailwindcss": "^3.3.0"
  }
}
```

## Migration Benefits

1. **Native macOS app** - Better performance than TUI
2. **Rich UI** - More visual design possibilities
3. **Easier distribution** - Single .app bundle or DMG
4. **Better accessibility** - Mouse + keyboard support
5. **Maintainability** - Separation of concerns with Rust/React
6. **Extensibility** - Easier to add features like export, sharing, etc.

## Challenges & Solutions

### Challenge 1: System Tool Dependencies
**Solution:** Check tool availability on startup, provide installation instructions

### Challenge 2: Parsing Complex Output
**Solution:** Port regex patterns from Python, add robust error handling

### Challenge 3: Parallel Execution
**Solution:** Use tokio for async Rust, Promise.all() for frontend

### Challenge 4: DNSSEC Visualization
**Solution:** Carefully port 18-color palette and keytag matching logic

### Challenge 5: State Synchronization
**Solution:** Use single source of truth in frontend state store

## Testing Strategy

1. **Unit tests** - Rust adapters and parsers
2. **Integration tests** - Tauri commands with real tools
3. **E2E tests** - Frontend interaction flows
4. **Manual testing** - Real domains (example.com, google.com, etc.)
5. **Performance testing** - Compare to Python version

## Version Management

**Critical:** Maintain version in multiple locations:
1. `app/src-tauri/Cargo.toml` - Rust package version
2. `app/package.json` - Frontend package version
3. `app/src-tauri/tauri.conf.json` - App bundle version
4. Keep in sync with Python version (currently 0.1.2)

## Timeline Estimate

- Phase 1 (Setup): 1 day
- Phase 2 (Rust Backend): 5-7 days
- Phase 3 (TypeScript Models): 1 day
- Phase 4 (React Frontend): 7-10 days
- Phase 5 (Features): 3-5 days
- Phase 6 (Build/Test): 2-3 days

**Total: 3-4 weeks**

## Success Criteria

- [ ] All 7 panels render correctly
- [ ] Data fetching completes in <10 seconds
- [ ] All keyboard shortcuts work
- [ ] All 4 themes functional
- [ ] DNSSEC chain visualization matches Python version
- [ ] Email security scoring matches Python version
- [ ] Raw data modal shows both JSON and tool output
- [ ] App builds successfully for macOS
- [ ] App bundle <50MB
- [ ] Memory usage <200MB

## Future Enhancements (Post-Migration)

1. **Export functionality** - PDF, CSV, JSON export
2. **History tracking** - Compare domain changes over time
3. **Batch analysis** - Multiple domains
4. **Notifications** - Alert on cert expiration, domain expiration
5. **Custom DNS resolvers** - Test against different resolvers
6. **Cross-platform** - Windows and Linux builds
7. **Cloud sync** - Save analysis results
8. **API integration** - Webhook notifications

## References

- Tauri Documentation: https://tauri.app/
- Python source code: `/Users/dread/apps/dns/d/src/dns_debugger/`
- Original TUI: Textual framework
- Version: 0.1.2

---

**Next Steps:** Begin Phase 1 - Initialize Tauri project structure in `app/` folder
