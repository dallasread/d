# DNS Debugger (d) - Terminal UI for Domain Analysis

A powerful Terminal User Interface (TUI) application for debugging DNS, domain registration, SSL/TLS certificates, email configuration, and DNSSEC validation. Built with Python's Textual framework and following hexagonal architecture principles.

## Overview

DNS Debugger (`d`) is an interactive terminal application that provides a comprehensive dashboard for domain analysis. Launch it with a single command (`d example.com`) to instantly see:

- **Domain Registration** - WHOIS/RDAP data, expiration dates, registrar info
- **DNS Records** - A, AAAA, MX, TXT, NS records with proper type filtering
- **DNSSEC** - Validation status, DNSKEY/DS records, chain of trust
- **SSL/TLS Certificates** - Validity, chain, expiration, security features
- **HTTP/HTTPS** - Status codes, redirects, response times
- **Email Security** - SPF, DKIM, DMARC configuration and scoring

All data loads asynchronously with detailed progress indicators and is cached in a global state for instant panel switching. Press `R` to refresh all data.

## Recent Updates

**Latest improvements:**
- ✅ **Enhanced DNSSEC visualization** - Complete root-to-leaf DNSSEC chain with table-aligned record display
- ✅ **18-color keytag palette** - Hash-based color selection for consistent visual tracking across DNSKEY and DS records
- ✅ **Compact record format** - Single-line key=value format with truncated public keys and full digest hashes
- ✅ **Table alignment** - Fixed-width columns for KEYTAG, ALGO, TYPE, and DIGEST fields for easy vertical scanning
- ✅ **SOA-based RRSIG detection** - Queries SOA records instead of A records to properly detect signatures for all domains
- ✅ **Full record details** - Shows complete DNSKEY public keys (truncated for display) and full DS digest hashes
- ✅ **HTTP redirect status fix** - Dashboard correctly shows green/pass for successful responses (200 OK) even after following redirects (301/302)
- ✅ **Improved curl parsing** - Fixed status code extraction to use curl's JSON stats output for accurate final status
- ✅ **WWW subdomain checking** - HTTP/HTTPS panel now tests both apex domain and www subdomain automatically
- ✅ **SPF policy explanations** - Human-readable descriptions for SPF mechanisms (-all, ~all, +all, ?all)
- ✅ **Enhanced registration display** - Registration panel shows created/updated dates and all domain status codes
- ✅ **Improved nameserver parsing** - Fixed WHOIS parser to exclude TLD registry servers (gtld-servers.net)
- ✅ **Tab key navigation** - Use Tab/Shift+Tab to cycle through panels (same as arrow keys)
- ✅ **Raw tool output toggle** - Press T in raw logs view to switch between JSON and actual tool output (dig, openssl, curl, whois)
- ✅ **Smart NS record warnings** - Missing NS records only show as errors for apex domains; subdomains show informational message
- ✅ **HTTP/HTTPS dual testing** - Both protocols tested with full redirect chain analysis
- ✅ **Email panel fixes** - Complete email security configuration display with SPF/DKIM/DMARC
- ✅ **Parallel data fetching** - 5-10x performance improvement with concurrent queries
- ✅ **DNS record filtering** - Proper type-based filtering prevents record cross-contamination

## Installation

### Quick Install

```bash
# Using the install script
bash install.sh

# Or manually with pip
pip install -e .
```

### Dependencies

The application uses system tools as adapters (with automatic fallback):

**DNS Tools:**
- `dog` (preferred) or `dig` (fallback) for DNS queries

**SSL/TLS:**
- `openssl` command-line tool for certificate inspection

**Domain Registration:**
- `whois` command (brew install whois / apt-get install whois)
- Python `whodap` library for RDAP (fallback to python-whois)

**HTTP:**
- `curl` (preferred) or `wget` (fallback) for HTTP requests

The application will automatically detect and use available tools.

## Usage

### Launch the TUI

```bash
# Basic usage - opens interactive dashboard
d example.com
dns-debugger example.com
python -m dns_debugger example.com
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Q` | Quit application |
| `R` | Refresh all data (shows loading progress) |
| `L` | Show raw logs for current panel (toggle JSON/raw tool output with T) |
| `H` or `?` | Show help information |
| `0` | Jump to Dashboard (overview) |
| `1` | Jump to Registration panel |
| `2` | Jump to DNS panel |
| `3` | Jump to DNSSEC panel |
| `4` | Jump to Certificate panel |
| `5` | Jump to HTTP/HTTPS panel |
| `6` | Jump to Email panel |
| `Tab` / `Shift+Tab` | Cycle forward/backward through panels |
| `←` / `→` | Navigate between panels |
| `Esc` | Close modals/popups |
| `T` | Toggle between JSON and raw tool output (in raw logs view) |

## Performance

DNS Debugger is optimized for fast data loading:

- **Parallel Data Fetching**: All data sources (DNS, WHOIS, certificates, HTTP, etc.) are queried simultaneously using `asyncio.gather()` with ThreadPoolExecutor
- **Typical load time**: 5-10 seconds for complete domain analysis
- **State Caching**: Once loaded, all data is cached in memory for instant panel switching
- **No Re-fetching**: Switching between panels uses cached data - only explicit refresh (R key) fetches new data

**Performance improvements:**
- 5-10x faster than sequential fetching
- 10 concurrent workers for parallel operations
- Graceful handling of slow/timeout responses
- Independent fetching prevents one slow query from blocking others

## Features

### Dashboard (Tab 0)

The dashboard provides an at-a-glance health overview with color-coded status indicators:

**Layout:**
- Left side: Full-height Registration card
- Right side: 2x3 grid of health cards (DNS, Email, DNSSEC, Certificate, HTTP/HTTPS)

**Registration Card:**
- Domain expiration status (green: >30 days, yellow: <30 days, red: expired)
- Registrar information
- DNSSEC enabled/disabled status
- Nameserver count

**DNS Card:**
- A, AAAA, MX, NS record counts
- Color indicators (green: present, dim: none, red: missing NS for apex domains only)
- Subdomains show dimmed NS status as they inherit from parent zone

**Email Card:**
- MX record status
- SPF, DKIM, DMARC configuration
- Overall security score (0-100)
- Email provider detection

**DNSSEC Card:**
- Validation status (SECURE, INSECURE, BOGUS, INDETERMINATE)
- DNSKEY and DS record presence
- Key counts (KSK/ZSK)
- Warning count

**Certificate Card:**
- Validity status
- Days until expiration (with warnings at <30 days)
- Issuer information
- Certificate chain validity

**HTTP/HTTPS Card:**
- Status code and response time for HTTPS requests
- Success/redirect/error indicators
- Redirect count
- Correctly shows green/pass for 200 OK responses, even after following redirects (301→200, 302→200)
- Yellow/warn for final redirect status (3xx with no further redirect)
- Red/fail for errors (4xx, 5xx) or connection failures

### Registration Panel (Tab 1)

Detailed WHOIS/RDAP information:
- Registrar name
- Registration dates (created, updated, expires) displayed prominently
- Expiration status with countdown
- Full nameserver list with IP addresses (filtered to exclude TLD registry servers)
- Complete domain status codes (clientTransferProhibited, serverDeleteProhibited, etc.)
- DNSSEC status
- Registrant organization and country

**Note:** The WHOIS parser correctly filters out IANA TLD registry servers (gtld-servers.net) to show only your domain's actual authoritative nameservers.

### DNS Panel (Tab 2)

Complete DNS record display with proper type filtering:
- A records (IPv4 addresses)
- AAAA records (IPv6 addresses)
- MX records (mail servers with priority)
- TXT records (text data, SPF, verification records)
- NS records (authoritative nameservers)

Each record shows:
- Value
- TTL (Time To Live)
- Type-specific data

**Note:** Records are properly filtered by type to prevent cross-contamination (e.g., CNAME records won't appear in NS section). Each record type is queried and displayed independently.

### DNSSEC Panel (Tab 3)

**Complete DNSSEC chain visualization from root to leaf** - similar to DNSViz.net

The DNSSEC panel now provides a **recursive, full-chain visualization** that shows every zone in the delegation path from the root zone down to your target domain. For example, querying `example.com` shows:

1. **Root Zone (`.`)**
   - All DNSKEY records (KSK and ZSK) with full details
   - DS records delegating to `.com` TLD

2. **TLD Zone (`.com`)**
   - All DNSKEY records for the `.com` zone
   - DS records delegating to `example.com`

3. **Target Zone (`example.com`)**
   - All DNSKEY records (your domain's keys)
   - RRSIG signatures covering zone records
   - Full chain validation summary

**What's shown for each zone:**
- **DNSKEY Records** (table-aligned format):
  - Format: `DNSKEY KEYTAG=5116  ALGO=8 TYPE=KSK PUBKEY=AwEAAZpR...KsU=`
  - Key tag (color-coded for easy visual matching)
  - Algorithm number (8 = RSASHA256)
  - Key type: KSK (Key Signing Key) or ZSK (Zone Signing Key)
  - Public key (truncated middle: first 16 + last 16 chars for display)

- **DS Records** (table-aligned format):
  - Format: `DS KEYTAG=5116  ALGO=8 DIGEST=2 HASH=97BAA418B759...C70D90BE`
  - Key tag (color-coded to match corresponding DNSKEY above)
  - Algorithm number
  - Digest type (1=SHA-1, 2=SHA-256, 3=GOST, 4=SHA-384)
  - Complete digest hash (spaces stripped)

- **RRSIG Records** (for target zone):
  - Which key (KSK/ZSK) signed which record types
  - Signature inception and expiration dates
  - Days until expiry (color-coded: green >30d, yellow <30d, red expired)
  - Signer name and algorithm

**Recursive chain support:**
- Works for deeply nested domains: `a.b.c.d.example.com`
- Shows every zone in the path: `. → com → example.com → d.example.com → c.d.example.com → ...`
- Each zone displays complete DNSKEY and DS data
- Color-coded key tags make it easy to trace DS → DNSKEY relationships

**Key Features:**
- **18-color keytag palette**: Hash-based color selection ensures consistent visual tracking across the entire chain
  - Uses hash function instead of modulus for better color distribution
  - Same key tag always gets the same color, even across different zones
  - Highly distinct colors (coral red, turquoise, gold, lavender, etc.) maximally separated in color space
- **Table-aligned display**: Fixed-width columns make it easy to scan vertically and match KEYTAGs
- **Compact format**: Single-line records with essential information (KEYTAG, ALGO, TYPE/DIGEST, key material)
- **Full details**: Shows ALL DNSKEY and DS records (not limited to 2 per zone)
- **Validation summary**: Clear indication of chain status (SECURE, SIGNED BUT NOT SECURE, INSECURE)
- **Expiration warnings**: RRSIG signatures color-coded by expiration status

**Implementation Notes:**
- Both `dig` and `dog` adapters support recursive chain building
- Queries are made zone-by-zone from root down to target
- Each zone's DNSKEY and DS records are queried and parsed independently
- Handles errors gracefully - continues building chain even if individual queries fail

### Certificate Panel (Tab 4)

SSL/TLS certificate details:
- Subject and issuer common names
- Validity period (from/to dates)
- Expiration status with day countdown
- Public key information (algorithm, size)
- Subject Alternative Names (SANs)
- Certificate chain:
  - Chain length
  - Validation status
- Supported TLS versions
- Security features:
  - OCSP stapling
  - Self-signed detection

### HTTP/HTTPS Panel (Tab 5)

HTTP connectivity and response information for both apex domain and www subdomain:

**Apex Domain Tests:**
- `http://example.com` and `https://example.com` checked
- Status code and text for both protocols
- Response time in milliseconds
- Success indicators:
  - **Green**: 200-299 final status (including after redirects)
  - **Yellow**: Redirect status (3xx) with no further redirect
  - **Red**: Client/server errors (4xx, 5xx) or connection failures
- Redirect chain display (if applicable):
  - Each redirect step with status code
  - From URL → To URL for each hop
  - Color-coded status (yellow for redirects, green for final success)
- Server header
- Content-Type
- Content-Length

**WWW Subdomain Tests:**
- `http://www.example.com` and `https://www.example.com` checked automatically
- Same comprehensive checks as apex domain
- Helps verify proper www redirect configuration

**Status Code Handling:**
The HTTP adapter now correctly uses curl's JSON stats output (`-w` flag) to capture the final status code after following all redirects. This ensures that domains with redirect chains (e.g., `https://example.com` → 301 → `https://www.example.com` → 200) are correctly identified as successful rather than failed.

Both the naked domain and www subdomain are tested for both HTTP and HTTPS protocols to ensure complete coverage of common domain access patterns.

### Email Panel (Tab 6)

Comprehensive email security configuration:

**Overview:**
- Security score (0-100) with color coding
- Email provider detection (Google, Microsoft, etc.)

**MX Records:**
- Priority and hostname for each mail server
- IP addresses

**SPF (Sender Policy Framework):**
- Full SPF record
- Policy enforcement level with human-readable explanations:
  - `-all` (Strict): Rejects unauthorized senders (recommended)
  - `~all` (Soft Fail): Marks unauthorized as suspicious (transitional)
  - `+all` (Allow All): Allows anyone to send (not recommended)
  - `?all` (Neutral): No policy enforcement
- Mechanism count
- Recommendations if missing

**DKIM (DomainKeys Identified Mail):**
- Selector discovery (checks common selectors)
- Public key display
- Per-selector validation status

**DMARC (Domain-based Message Authentication):**
- Policy (none, quarantine, reject)
- Subdomain policy
- Alignment modes (strict/relaxed)
- Reporting URIs (aggregate/forensic)
- Message coverage percentage

**Configuration Status:**
- Missing component warnings
- Overall security recommendations

### Raw Logs (Press L)

Press `L` on any panel to view both structured data and raw tool output:

**JSON View (default):**
- Complete domain models
- All fields and metadata
- Timestamps and query information
- Useful for debugging and API integration

**Raw Tool Output (press T to toggle):**
- Original output from command-line tools
- `dig` output for DNS/DNSSEC queries
- `openssl s_client` output for certificates
- `curl`/`wget` output for HTTP requests
- `whois` output for registration data
- Useful for debugging tool-specific issues

The raw data is preserved from the cached state, ensuring consistency with displayed information.

## Architecture

### Hexagonal Architecture (Ports & Adapters)

The application follows a clean hexagonal architecture pattern:

```
┌─────────────────────────────────────────┐
│          UI Layer (Textual TUI)         │
│  ┌─────────────────────────────────┐   │
│  │  Dashboard, Panels, Screens     │   │
│  └─────────────────────────────────┘   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Facade Layer                    │
│  ┌─────────────────────────────────┐   │
│  │  DashboardFacade                │   │
│  │  - Simplified data structures   │   │
│  │  - Display-optimized models     │   │
│  └─────────────────────────────────┘   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Domain Layer (Hexagon Core)     │
│  ┌─────────────────────────────────┐   │
│  │  Domain Models:                 │   │
│  │  - DNSResponse                  │   │
│  │  - DNSSECValidation             │   │
│  │  - TLSInfo, Certificate         │   │
│  │  - HTTPResponse                 │   │
│  │  - DomainRegistration           │   │
│  │  - EmailConfiguration           │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Ports (Interfaces):            │   │
│  │  - DNSPort                      │   │
│  │  - CertificatePort              │   │
│  │  - HTTPPort                     │   │
│  │  - RegistryPort                 │   │
│  │  - EmailPort                    │   │
│  └─────────────────────────────────┘   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Adapter Layer                   │
│  ┌─────────────────────────────────┐   │
│  │  DNS Adapters:                  │   │
│  │  - DogAdapter (primary)         │   │
│  │  - DigAdapter (fallback)        │   │
│  │                                 │   │
│  │  Certificate Adapters:          │   │
│  │  - OpenSSLAdapter               │   │
│  │                                 │   │
│  │  HTTP Adapters:                 │   │
│  │  - CurlAdapter (primary)        │   │
│  │  - WgetAdapter (fallback)       │   │
│  │                                 │   │
│  │  Registry Adapters:             │   │
│  │  - RDAPAdapter (primary)        │   │
│  │  - WhoisAdapter (fallback)      │   │
│  │                                 │   │
│  │  Email Adapters:                │   │
│  │  - DNSEmailAdapter              │   │
│  └─────────────────────────────────┘   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    External Tools & Libraries           │
│  dog/dig, openssl, curl/wget,           │
│  whois, whodap, httpx                   │
└─────────────────────────────────────────┘
```

### Key Architectural Patterns

**1. Global State Management**
- `StateManager` singleton stores all fetched data
- Data fetched once on load, stored in `AppState`
- Panels render from cached state via `render_from_state()`
- Refresh (R key) refetches ALL data and updates state

**2. Facade Pattern for Display**
- `DashboardFacade` provides simplified health data structures:
  - `HTTPHealthData`, `CertHealthData`, `DNSHealthData`, etc.
- Separates complex domain models from display concerns
- Dashboard uses simple, flat data structures
- Detail panels use full domain models

**3. Factory Pattern for Adapters**
- Each adapter type has a factory (e.g., `DNSAdapterFactory`)
- Factories auto-detect available tools at runtime
- Graceful fallback to alternative implementations
- Example: `dog` → `dig` → error message

**4. Port/Adapter Pattern**
- Domain layer defines port interfaces (contracts)
- Adapters implement ports using external tools
- Business logic never directly depends on tools
- Easy to add new adapters without changing core logic

### Project Structure

```
src/dns_debugger/
├── __init__.py
├── __main__.py              # Entry point
├── app.py                   # Main Textual app, all panels, dashboard
├── state.py                 # Global StateManager and AppState
│
├── domain/                  # Core business logic (hexagon center)
│   ├── models/              # Rich domain models
│   │   ├── dns_record.py    # DNSRecord, DNSResponse, RecordType
│   │   ├── dnssec.py        # DNSSECValidation, DNSKEYRecord, DSRecord
│   │   ├── certificate.py   # Certificate, TLSInfo, CertificateChain
│   │   ├── http_info.py     # HTTPResponse, HTTPRedirect
│   │   ├── domain_info.py   # DomainRegistration, Nameserver, Contact
│   │   └── email_config.py  # EmailConfiguration, SPF, DKIM, DMARC
│   │
│   └── ports/               # Port interfaces (contracts)
│       ├── dns_port.py      # DNSPort interface
│       ├── cert_port.py     # CertificatePort interface
│       ├── http_port.py     # HTTPPort interface
│       ├── registry_port.py # RegistryPort interface
│       └── email_port.py    # EmailPort interface
│
├── adapters/                # Adapter implementations
│   ├── dns/
│   │   ├── dog_adapter.py   # Primary DNS adapter using 'dog'
│   │   ├── dig_adapter.py   # Fallback using 'dig'
│   │   └── factory.py       # Auto-detect available tool
│   │
│   ├── cert/
│   │   ├── openssl_adapter.py  # Certificate adapter using OpenSSL
│   │   └── factory.py
│   │
│   ├── http/
│   │   ├── curl_adapter.py     # Primary HTTP adapter using 'curl'
│   │   ├── wget_adapter.py     # Fallback using 'wget'
│   │   └── factory.py
│   │
│   ├── registry/
│   │   ├── rdap_adapter.py     # Primary using RDAP protocol
│   │   ├── whois_adapter.py    # Fallback using WHOIS
│   │   └── factory.py
│   │
│   └── email/
│       ├── dns_email_adapter.py  # Email config via DNS queries
│       └── factory.py
│
├── facades/
│   ├── __init__.py
│   └── dashboard_facade.py  # Simplified health data structures
│
└── screens/
    ├── __init__.py
    └── raw_data_screen.py   # Modal for displaying raw JSON logs
```

### Data Flow

**On Application Start:**
1. User runs `d example.com`
2. `DNSDebuggerApp` initializes `StateManager` with domain
3. `on_mount()` triggers `fetch_all_data()` worker
4. Loading status shows progress: "Loading: HTTP/HTTPS...", "Loading: Certificate...", etc.
5. `DashboardFacade` fetches health data via adapters
6. Full detail data fetched and stored in `AppState`
7. `render_all_panels()` called to populate all panels from state
8. Loading indicator hidden, main content displayed

**On Refresh (R key):**
1. Loading status shown: "Refreshing data..."
2. `fetch_all_data()` worker re-runs
3. All adapters queried again
4. State updated with fresh data
5. All panels re-rendered from new state
6. Loading indicator hidden

**On Tab Switch:**
1. User presses 1-6 or Tab
2. Textual switches active tab pane
3. Panel already populated from state (instant display)
4. No new data fetching required

**On Raw Logs (L key):**
1. User presses L on any panel
2. `action_show_raw()` determines active panel
3. Panel's stored `last_*` object converted to JSON
4. `RawDataScreen` modal displays formatted JSON
5. User presses Esc to close

### State Management

**AppState Structure:**
```python
@dataclass
class AppState:
    domain: str
    
    # Full detail data (for panels)
    dns_responses: dict              # {record_type: DNSResponse}
    dnssec_validation: DNSSECValidation
    tls_info: TLSInfo
    http_response: HTTPResponse
    registration: DomainRegistration
    email_config: EmailConfiguration
    
    # Dashboard health data (simplified)
    http_health: HTTPHealthData
    cert_health: CertHealthData
    dns_health: DNSHealthData
    registry_health: RegistryHealthData
    dnssec_health: DNSSECHealthData
    email_health: EmailHealthData
```

**StateManager Singleton:**
- Single source of truth for all data
- Thread-safe access
- Update methods for each data type
- Accessed globally via `StateManager()`

## Development

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd d

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running the Application

```bash
# From project root
python -m dns_debugger example.com

# Or if installed
dns-debugger example.com
d example.com
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dns_debugger --cov-report=html

# Run specific test
pytest tests/test_adapters/test_dns_adapter.py -v
```

### Code Style

```bash
# Format code
black src/
isort src/

# Lint
flake8 src/
mypy src/
```

### Adding a New Adapter

1. **Create adapter class** implementing the port interface:
```python
# src/dns_debugger/adapters/my_category/my_adapter.py
from dns_debugger.domain.ports.my_port import MyPort

class MyAdapter(MyPort):
    def my_method(self, domain: str) -> MyResult:
        # Implementation using external tool
        pass
```

2. **Update factory** to include new adapter:
```python
# src/dns_debugger/adapters/my_category/factory.py
class MyAdapterFactory:
    @staticmethod
    def create() -> MyPort:
        if shutil.which("my_tool"):
            return MyAdapter()
        else:
            raise RuntimeError("No adapter available")
```

3. **Test the adapter**:
```bash
pytest tests/test_adapters/test_my_adapter.py
```

### Adding a New Panel

1. **Create panel class** in `app.py`:
```python
class MyPanel(Static):
    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.last_data = None
    
    def render_from_state(self, state) -> None:
        # Render from state.my_data
        pass
```

2. **Add to TabPane** in `compose()`:
```python
with TabPane("My Feature", id="my-feature"):
    yield MyPanel(self.domain)
```

3. **Add keyboard binding**:
```python
Binding("7", "switch_tab('my-feature')", "My Feature", show=False)
```

4. **Update state** to include your data:
```python
# In state.py
@dataclass
class AppState:
    # ... existing fields
    my_data: Optional[MyData] = None
```

5. **Fetch data** in `fetch_all_data()`:
```python
self.update_loading_status("My feature...")
my_adapter = MyAdapterFactory.create()
my_data = my_adapter.get_data(self.domain)
self.state_manager.update_my_data(my_data)
```

## Configuration

Currently, the application uses sensible defaults. Future versions will support configuration files.

## Known Issues

- Large TXT records may be truncated in display
- DNSSEC validation requires recursive resolver support
- Some WHOIS servers have rate limiting
- Certificate transparency log checking not yet implemented

## Roadmap

**Current Version: 0.1.0**

**Planned Features:**
- [ ] Configuration file support (~/.config/dns-debugger/config.toml)
- [ ] Query history persistence
- [ ] Export to JSON/CSV/Markdown
- [ ] Multiple domain comparison mode
- [ ] DNS propagation checker (query multiple geographic resolvers)
- [ ] Certificate expiration monitoring/alerts
- [ ] Plugin system for custom adapters
- [ ] API mode for automation/scripting
- [ ] Network diagnostics (ping, traceroute integration)
- [ ] Certificate transparency log verification

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the hexagonal architecture pattern
4. Write tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Format code (`black`, `isort`)
7. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [Textual](https://textual.textualize.io/) by Textualize
- Uses `dog`, `dig`, `openssl`, `curl`, `wget`, `whois` command-line tools
- Inspired by CLI DNS debugging tools and the need for a unified interface

## Support

- **Issues**: Create an issue on GitHub
- **Questions**: Start a discussion on GitHub Discussions

---

**Quick Start Reminder:**
```bash
# Install
pip install -e .

# Run
d example.com

# Navigate
- Press 0-6 to jump between panels
- Press R to refresh
- Press L to see raw JSON
- Press H for help
- Press Q to quit
```
