# DNS Debugger (d) - GUI Application for Domain Analysis

A powerful desktop GUI application for debugging DNS, domain registration, SSL/TLS certificates, email configuration, and DNSSEC validation. Built with Tauri (Rust backend) and Vue 3 (TypeScript frontend).

## Overview

DNS Debugger (`d`) is an interactive desktop application that provides a comprehensive dashboard for domain analysis. Launch it and enter a domain to instantly see:

- **Dashboard** - At-a-glance health overview with color-coded status indicators
- **Domain Registration** - WHOIS/RDAP data, expiration dates, registrar info
- **DNS Records** - A, AAAA, MX, TXT, NS records with proper type filtering
- **DNSSEC** - Complete chain visualization from root to target with arrows showing trust relationships
- **SSL/TLS Certificates** - Validity, chain, expiration, security features
- **HTTP/HTTPS** - Status codes, redirects, response times
- **Email Security** - SPF, DKIM, DMARC configuration (coming soon)

All data loads asynchronously with detailed progress indicators. Press the Refresh button or use keyboard shortcut `R` to refresh all data.

## Recent Updates

**Latest improvements:**
- ✅ **Complete DNSSEC chain visualization** - Shows root → TLD → domain with hand-drawn arrows connecting DS records to DNSKEYs
- ✅ **RRSIG signature display** - Shows cryptographic signatures in target zone with matching arrows to DNSKEYs
- ✅ **Hand-drawn arrow style** - Organic, flowing arrows with curved arrowheads for visual appeal
- ✅ **Color-coded key tags** - Rotating colors for key tags make it easy to track relationships
- ✅ **Dark theme UI** - Modern, clean interface with monospace font for technical data
- ✅ **Keyboard navigation** - Number keys (1-7) to jump between tabs
- ✅ **Real-time command logging** - View all backend commands (dig, openssl, curl) with timestamps
- ✅ **Parallel data fetching** - Fast loading with concurrent queries to multiple data sources

## Installation

### Prerequisites

The application uses system tools via the Rust backend:

**Required:**
- `dig` (BIND DNS tools) - for DNS and DNSSEC queries
- `openssl` - for SSL/TLS certificate inspection
- `whois` - for domain registration data
- `curl` - for HTTP/HTTPS requests

**Installation on macOS:**
```bash
brew install bind openssl whois curl
```

**Installation on Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install dnsutils openssl whois curl

# Fedora/RHEL
sudo dnf install bind-utils openssl whois curl
```

### Running the Application

**Development mode:**
```bash
npm install
npm run tauri dev
```

**Build for production:**
```bash
npm run tauri build
```

The built application will be in `src-tauri/target/release/bundle/`.

## Usage

### Navigation

**Keyboard Shortcuts:**
- `1` - Dashboard (overview)
- `2` - Registration panel
- `3` - DNS panel
- `4` - DNSSEC panel
- `5` - Certificate panel
- `6` - HTTP/HTTPS panel
- `7` - Email panel
- `R` - Refresh all data
- `L` - Toggle command logs slideout

**Mouse Navigation:**
- Click on any dashboard card to jump to detailed view
- Click on tab names to switch panels
- Use refresh button in navigation bar

### Features Overview

#### Dashboard (Tab 1)

The dashboard provides an at-a-glance health overview with color-coded status indicators:

**Layout:**
- Top row: DNS, Registration, DNSSEC cards
- Bottom row: Certificate, HTTP/HTTPS, Email cards

**DNS Card:**
- A, AAAA, MX, NS record counts
- Color indicators (green: present, dim: none)

**Registration Card:**
- Domain expiration status
- Registrar information
- DNSSEC status

**DNSSEC Card:**
- Validation status (SECURE/INSECURE/BOGUS)
- Chain depth (number of zones)
- Warning count

**Certificate Card:**
- Days until expiration
- Issuer information
- Validity status

**HTTP/HTTPS Card:**
- HTTPS status code
- Response time
- Redirect count

**Email Card:**
- MX record count
- First 2 MX hostnames
- Additional record indicator

#### Registration Panel (Tab 2)

Detailed WHOIS/RDAP information:
- Registrar name
- Registration dates (created, updated, expires)
- Expiration status with countdown
- Nameserver list
- Domain status codes
- DNSSEC status

#### DNS Panel (Tab 3)

Complete DNS record display:
- A records (IPv4 addresses)
- AAAA records (IPv6 addresses)
- MX records (mail servers with priority)
- TXT records (text data, SPF, verification)
- NS records (authoritative nameservers)

Each record shows value, TTL, and type-specific data.

#### DNSSEC Panel (Tab 4)

**Complete DNSSEC chain visualization** - Similar to DNSViz.net but with a cleaner interface:

**What's shown for each zone:**
- Zone name with FQDN notation (e.g., `io.`, `meat.io.`)
- **DNSKEY Records:**
  - Format: `DNSKEY KEYTAG=5116 ALGO=8 TYPE=KSK PUBKEY=AwEA...`
  - Color-coded key tags for visual matching
  - Algorithm number and key type (KSK/ZSK)
  - Truncated public key

- **DS Records (in dark section):**
  - Format: `DS KEYTAG=5116 ALGO=8 HASH=97BAA...`
  - Points to child zone's DNSKEY
  - Color-coded key tags match DNSKEYs
  - Full digest hash

- **RRSIG Records (target zone only, in dark section):**
  - Format: `RRSIG KEYTAG=5116 ALGO=8 TYPE=DNSKEY SIGNER=... EXPIRES=...`
  - Cryptographic signatures
  - Color-coded key tags match DNSKEYs
  - Expiration dates

**Visual Arrows:**
- Hand-drawn style arrows on the left side
- Connect parent DS records → child DNSKEY records (by matching key_tag)
- Connect DNSKEY records → RRSIG records in target zone
- Organic, flowing appearance with curved arrowheads

**Chain Support:**
- Shows every zone from root (`.`) down to target
- Example: `. → io. → meat.io.`
- Works for deeply nested domains

#### Certificate Panel (Tab 5)

SSL/TLS certificate details:
- Subject and issuer common names
- Validity period (NotBefore/NotAfter dates)
- Expiration status with day countdown
- Public key algorithm and size
- Subject Alternative Names (SANs)
- Certificate chain validation
- Supported TLS versions

#### HTTP/HTTPS Panel (Tab 6)

HTTP connectivity and response information:
- Status code and response time
- Color-coded status:
  - Green: 200-299 (success)
  - Yellow: 300-399 (redirects)
  - Red: 400-599 (errors)
- Redirect chain visualization
- Server and Content-Type headers
- Content-Length

#### Email Panel (Tab 7)

Email configuration (coming soon):
- MX record display
- SPF, DKIM, DMARC analysis
- Security score
- Configuration recommendations

### Command Logs

The logs slideout (press `L`) shows all backend commands executed:
- Command name and arguments
- Execution time
- Exit code
- Full output
- Timestamp

Useful for debugging and understanding what queries are being made.

## Architecture

### Technology Stack

**Frontend (Vue 3 + TypeScript):**
- Vue 3 with Composition API
- TypeScript for type safety
- Tailwind CSS for styling
- Pinia for state management
- Vue Router for navigation

**Backend (Rust + Tauri):**
- Tauri framework for desktop app
- Rust for performance and safety
- Command execution for system tools
- Structured JSON responses

**System Tools:**
- `dig` - DNS and DNSSEC queries with +multi and +dnssec flags
- `openssl s_client` - TLS certificate inspection
- `whois` - Domain registration data
- `curl` - HTTP/HTTPS requests with redirect following

### Project Structure

```
d/                           # Repository root
├── src/                      # Vue 3 frontend
│   ├── components/           # Vue components
│   │   ├── Dashboard.vue     # Overview cards
│   │   ├── Registration.vue  # WHOIS data
│   │   ├── DNS.vue          # DNS records
│   │   ├── DNSSEC.vue       # DNSSEC chain visualization
│   │   ├── Certificate.vue  # TLS certificates
│   │   ├── HTTP.vue         # HTTP/HTTPS status
│   │   ├── Email.vue        # Email config (coming soon)
│   │   ├── Navigation.vue   # Top nav with tabs
│   │   └── LogsSlideout.vue # Command logs
│   ├── stores/              # Pinia state stores
│   │   ├── app.ts           # App-wide state
│   │   ├── dns.ts           # DNS data
│   │   ├── dnssec.ts        # DNSSEC validation
│   │   ├── certificate.ts   # Certificate data
│   │   ├── http.ts          # HTTP responses
│   │   ├── whois.ts         # Registration data
│   │   └── logs.ts          # Command logs
│   └── router/              # Vue Router config
│
├── src-tauri/               # Rust backend
│   ├── src/
│   │   ├── main.rs          # Tauri setup
│   │   ├── commands/        # Tauri commands (API)
│   │   │   ├── dns.rs       # DNS query commands
│   │   │   ├── dnssec.rs    # DNSSEC validation
│   │   │   ├── certificate.rs # TLS cert commands
│   │   │   ├── http.rs      # HTTP request commands
│   │   │   └── whois.rs     # WHOIS commands
│   │   ├── adapters/        # System tool wrappers
│   │   │   ├── dns.rs       # dig adapter
│   │   │   ├── certificate.rs # openssl adapter
│   │   │   ├── http.rs      # curl adapter
│   │   │   └── whois.rs     # whois adapter
│   │   └── models/          # Data structures
│   │       ├── dns.rs
│   │       ├── dnssec.rs
│   │       ├── certificate.rs
│   │       ├── http.rs
│   │       └── whois.rs
│   └── Cargo.toml           # Rust dependencies
│
├── legacy/                  # Legacy Python TUI (deprecated)
│   ├── src/                 # Python source
│   ├── tests/               # Python tests
│   └── README.md            # Python TUI docs
│
└── package.json             # Node dependencies
```

### Data Flow

1. User enters domain in search bar
2. Frontend calls Tauri commands (Rust backend)
3. Rust adapters execute system tools (dig, openssl, etc.)
4. Output parsed into structured models
5. JSON returned to frontend
6. Pinia stores update with new data
7. Vue components reactively update UI
8. Command logs stored for debugging

## Development

### Setup

```bash
# Install Node.js dependencies
npm install

# Install Rust toolchain (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Tauri CLI
npm install -g @tauri-apps/cli
```

### Running in Development

```bash
npm run tauri dev
```

This starts:
- Vite dev server for hot-reload frontend
- Tauri in development mode with Rust backend
- Opens application window automatically

### Building for Production

#### macOS Universal Binary (Recommended)

Use the included build script for macOS to create a universal binary (Intel + Apple Silicon):

```bash
./build-macos.sh
```

This script leverages Tauri's native bundling to:
1. Check and install required Rust targets (aarch64-apple-darwin, x86_64-apple-darwin)
2. Clean previous builds
3. Build a universal binary (x86_64 + arm64)
4. Create a DMG installer using macOS's built-in `hdiutil`
5. Copy outputs to `dist/` directory
6. Create a ZIP archive for distribution

**Outputs:**
- `dist/D.app` - Universal macOS application bundle
- `dist/D_0.2.0_universal.dmg` - DMG installer (created with hdiutil)
- `dist/D-macos-universal.zip` - ZIP archive for distribution

**No additional tools required** - uses macOS's built-in `hdiutil` for DMG creation!

#### Manual Build

For platform-specific builds or other operating systems:

```bash
npm run tauri build
```

**Outputs:**
- macOS: `.app` bundle and `.dmg` installer in `src-tauri/target/release/bundle/macos/`
- Linux: `.deb`, `.AppImage` in `src-tauri/target/release/bundle/`
- Windows: `.exe`, `.msi` in `src-tauri/target/release/bundle/`

**Build for specific architecture:**
```bash
# macOS Apple Silicon only
npm run tauri build -- --target aarch64-apple-darwin

# macOS Intel only
npm run tauri build -- --target x86_64-apple-darwin

# Universal (both architectures)
npm run tauri build -- --target universal-apple-darwin
```

### Code Style

**Frontend:**
```bash
npm run lint      # ESLint
npm run format    # Prettier
```

**Backend:**
```bash
cd src-tauri
cargo fmt         # Format Rust code
cargo clippy      # Rust linter
```

## Legacy Python TUI

The original Python terminal UI application is still available in the `legacy/` directory for those who prefer command-line interfaces. See `legacy/README.md` for documentation.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Follow existing code style
4. Write clear commit messages
5. Test your changes thoroughly
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [Tauri](https://tauri.app/) - Rust-based desktop framework
- Frontend with [Vue 3](https://vuejs.org/) and [TypeScript](https://www.typescriptlang.org/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Icons from [Heroicons](https://heroicons.com/)
- Inspired by DNSViz, dig, and other DNS debugging tools

---

**Quick Start:**
```bash
# Development
npm install
npm run tauri dev

# Build
npm run tauri build

# Navigate
- Press 1-7 to jump between panels
- Press R to refresh
- Press L to toggle logs
```
