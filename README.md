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
| `L` | Show raw JSON logs for current panel |
| `H` or `?` | Show help information |
| `0` | Jump to Dashboard (overview) |
| `1` | Jump to Registration panel |
| `2` | Jump to DNS panel |
| `3` | Jump to DNSSEC panel |
| `4` | Jump to Certificate panel |
| `5` | Jump to HTTP/HTTPS panel |
| `6` | Jump to Email panel |
| `Tab` | Switch between panels |
| `Esc` | Close modals/popups |

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
- Color indicators (green: present, dim: none, red: missing NS)

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
- Status code and response time
- Success/redirect/error indicators
- Redirect count

### Registration Panel (Tab 1)

Detailed WHOIS/RDAP information:
- Registrar name
- Registration dates (created, updated, expires)
- Expiration status with countdown
- Nameserver list with IP addresses
- Domain status codes
- DNSSEC status
- Registrant organization and country

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

**Note:** Records are now properly filtered to prevent cross-contamination (e.g., CNAME records won't appear in NS section).

### DNSSEC Panel (Tab 3)

DNSSEC validation and key information:
- Validation status (SECURE/INSECURE/BOGUS)
- Validation time
- Chain of trust verification
- DNSKEY records with details:
  - Key type (KSK/ZSK)
  - Flags, algorithm, key tag
  - TTL values
- DS records (in parent zone):
  - Key tag, algorithm, digest type
  - Digest value
- RRSIG presence
- Warnings and error messages

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

HTTP connectivity and response information:
- HTTPS status code and text
- Response time in milliseconds
- Redirect chain (if applicable):
  - Each redirect step with status code
  - Final destination URL
- Server header
- Content-Type
- Content-Length

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
- Policy enforcement level (-all, ~all, +all)
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

Press `L` on any panel to view the raw JSON data structure:
- Complete domain models
- All fields and metadata
- Timestamps and query information
- Useful for debugging and API integration

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
