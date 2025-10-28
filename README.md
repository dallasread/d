# DNS Debugger - TUI Application

A powerful Terminal User Interface (TUI) application for debugging domain registration, DNS issues, and SSL/TLS certificates, built with Python's Textual framework.

## Overview

DNS Debugger is an interactive terminal application designed to help developers, system administrators, and DevOps engineers quickly diagnose and troubleshoot DNS, domain registration, and certificate problems. With a beautiful, modern interface that rivals GUI applications, it provides real-time insights into DNS records, domain configuration, registration status, and SSL/TLS certificate details.

## Features

### Core Functionality

#### DNS Features

- **DNS Record Lookup**: Query A, AAAA, CNAME, MX, TXT, NS, SOA, and other DNS records
- **Multi-Resolver Support**: Test against multiple DNS resolvers (Google, Cloudflare, custom)
- **DNS Propagation Checker**: Check DNS propagation across different geographic locations
- **DNSSEC Validation**: Verify DNSSEC signatures and chain of trust
- **Domain Registration Lookup**: Query domain registration information via RDAP (with WHOIS fallback)
- **Reverse DNS Lookup**: Perform PTR record lookups
- **DNS Trace**: Trace DNS resolution path from root servers
- **Zone Transfer Testing**: Attempt AXFR/IXFR zone transfers (for authorized domains)

#### SSL/TLS Certificate Features

- **Certificate Information**: View certificate details (subject, issuer, validity dates)
- **Certificate Chain Validation**: Verify complete certificate chain up to root CA
- **Expiration Monitoring**: Check certificate expiration and get warnings for soon-to-expire certs
- **Protocol Support Detection**: Check supported TLS/SSL versions (TLS 1.0, 1.1, 1.2, 1.3)
- **Cipher Suite Analysis**: List available cipher suites and identify weak ciphers
- **Certificate Transparency**: Check CT log inclusion
- **OCSP Stapling**: Verify OCSP stapling support
- **Multi-Host Testing**: Test certificates for multiple hosts/SNI
- **PEM Export**: Export certificates in PEM format for analysis

### Interface Features

- **Real-time Updates**: Live DNS query results with loading indicators
- **Syntax Highlighting**: Color-coded DNS records for easy reading
- **Tabbed Interface**: Multiple queries in separate tabs
- **History Panel**: Track your recent DNS queries
- **Export Results**: Save query results to JSON, CSV, or plain text
- **Dark/Light Themes**: Multiple color schemes for different preferences
- **Responsive Layout**: Adapts to different terminal sizes
- **Keyboard Shortcuts**: Fast navigation without touching the mouse

## Installation

### One-Line Install

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/d/main/install.sh | bash
```

This will:
- Detect your platform (macOS, Linux, Windows)
- Install required dependencies (dog, openssl if needed)
- Install the `d` command globally
- Verify the installation

### Manual Installation

If you prefer to install manually:

```bash
pipx install d-dns-debugger
```

### From Source

```bash
git clone https://github.com/yourusername/d.git
cd d
make install
```

## Usage

### Basic Usage
```bash
# Launch the interactive dashboard for a domain
d example.com

# That's it! The TUI opens with a full dashboard where you can:
# - View DNS records (navigate to different record types)
# - Check SSL/TLS certificates
# - View WHOIS information
# - Test DNS propagation
# - And more - all from the interactive interface
```

### Command Line Options
```
d DOMAIN [OPTIONS]

Options:
  --theme TEXT          UI theme (dark, light, monokai, solarized)
  -h, --help            Show help and exit
  --version             Show version and exit
```

All features are accessible through the interactive dashboard once launched. Simply run `d example.com` and use the TUI to explore DNS records, certificates, WHOIS data, and more.

### Keyboard Shortcuts
- `q` or `Ctrl+C`: Quit application
- `Tab`: Navigate between panels (DNS, Certificates, WHOIS, etc.)
- `Enter`: Drill into selected item for more details
- `Esc`: Go back to previous view
- `r`: Refresh current data
- `e`: Export current view
- `h` or `?`: Show help screen
- `1-9`: Quick switch to specific panels
- `Arrow keys`: Navigate within panels

## Architecture

### Project Structure

The project follows **Hexagonal Architecture** (Ports and Adapters pattern) to maintain clean separation between business logic and external tools:

```
dns-debugger-tui/
├── src/
│   └── dns_debugger/
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── app.py                # Main Textual application
│       ├── domain/              # Core business logic (hexagon center)
│       │   ├── __init__.py
│       │   ├── models/          # Domain models
│       │   │   ├── __init__.py
│       │   │   ├── dns_record.py
│       │   │   ├── certificate.py
│       │   │   └── domain_info.py
│       │   ├── ports/           # Port interfaces (contracts)
│       │   │   ├── __init__.py
│       │   │   ├── dns_port.py      # DNS query interface
│       │   │   ├── registry_port.py # RDAP/WHOIS interface
│       │   │   ├── cert_port.py     # Certificate interface
│       │   │   └── export_port.py   # Export interface
│       │   └── services/        # Core business logic
│       │       ├── __init__.py
│       │       ├── domain_analyzer.py
│       │       └── validation.py
│       ├── adapters/            # Adapters (implementations)
│       │   ├── __init__.py
│       │   ├── dns/             # DNS adapters
│       │   │   ├── __init__.py
│       │   │   ├── dog_adapter.py   # Primary: dog command
│       │   │   ├── dig_adapter.py   # Fallback: dig command
│       │   │   └── factory.py       # Auto-detect and return available adapter
│       │   ├── registry/        # Domain registration adapters
│       │   │   ├── __init__.py
│       │   │   ├── rdap_adapter.py  # Primary: RDAP
│       │   │   ├── whois_adapter.py # Fallback: WHOIS
│       │   │   └── factory.py
│       │   ├── cert/            # Certificate adapters
│       │   │   ├── __init__.py
│       │   │   ├── openssl_adapter.py
│       │   │   └── cryptography_adapter.py
│       │   └── export/          # Export adapters
│       │       ├── __init__.py
│       │       ├── json_adapter.py
│       │       ├── csv_adapter.py
│       │       └── text_adapter.py
│       ├── screens/             # UI layer
│       │   ├── __init__.py
│       │   ├── main_screen.py
│       │   ├── history_screen.py
│       │   └── help_screen.py
│       └── widgets/             # UI components
│           ├── __init__.py
│           ├── dns_panel.py
│           ├── cert_panel.py
│           └── registry_panel.py
├── tests/
│   ├── __init__.py
│   ├── test_dns_resolver.py
│   ├── test_widgets.py
│   └── test_app.py
├── docs/
│   ├── user_guide.md
│   ├── development.md
│   └── screenshots/
├── pyproject.toml
├── setup.py
├── requirements.txt
├── requirements-dev.txt
├── LICENSE
└── README.md
```

### Technology Stack

- **Framework**: [Textual](https://textual.textualize.io/) - Modern TUI framework
- **Architecture**: Hexagonal Architecture (Ports and Adapters) - Clean separation of concerns
- **DNS Tools** (adapters with automatic fallback):
  - Primary: [dog](https://dns.lookup.dog/) - Modern DNS client
  - Fallback: dig - Standard DNS tool
- **SSL/TLS**: [cryptography](https://cryptography.io/) - Certificate parsing and validation
- **SSL/TLS**: OpenSSL command-line tool - Certificate inspection
- **RDAP**: [whodap](https://pypi.org/project/whodap/) - RDAP client library (primary registration lookup)
- **WHOIS**: [python-whois](https://github.com/richardpenman/whois) - WHOIS lookups (fallback)
- **HTTP Client**: [httpx](https://www.python-httpx.org/) - For API-based propagation checks
- **CLI**: [Click](https://click.palletsprojects.com/) - Command-line interface
- **Testing**: [pytest](https://pytest.org/) - Test framework

## Development

### Setup Development Environment
```bash
# Clone the repository
git clone https://github.com/yourusername/dns-debugger-tui.git
cd dns-debugger-tui

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests

The project uses pytest for testing. To run the test suite:

```bash
# Run all tests
pytest

# Run all tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=dns_debugger --cov-report=html

# Run specific test file
pytest tests/test_dns_resolver.py

# Run tests matching a pattern
pytest -k "test_dns"

# Run tests and stop at first failure
pytest -x

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

### Code Style
This project follows:
- PEP 8 style guide
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

```bash
# Format code
black src/
isort src/

# Run linters
flake8 src/
mypy src/
```

## Configuration

### Config File Location
- Linux/macOS: `~/.config/dns-debugger/config.toml`
- Windows: `%APPDATA%\dns-debugger\config.toml`

### Example Configuration
```toml
[general]
theme = "dark"
auto_refresh = false
history_limit = 100

[resolvers]
default = "8.8.8.8"
favorites = [
    "8.8.8.8",      # Google
    "1.1.1.1",      # Cloudflare
    "9.9.9.9",      # Quad9
    "208.67.222.222" # OpenDNS
]

[display]
show_ttl = true
show_timestamp = true
syntax_highlighting = true

[export]
default_format = "json"
output_directory = "~/dns-queries"
```

## Roadmap

### Version 1.0
- [ ] Basic DNS record lookups
- [ ] Multiple resolver support
- [ ] TUI interface with Textual
- [ ] SSL/TLS certificate inspection
- [ ] WHOIS lookups
- [ ] Export functionality

### Version 1.1
- [ ] DNS propagation checker
- [ ] DNSSEC validation
- [ ] Certificate chain validation
- [ ] Cipher suite analysis
- [ ] Reverse DNS lookups
- [ ] Query history persistence

### Version 1.2
- [ ] DNS trace from root
- [ ] Zone transfer testing
- [ ] Certificate expiration monitoring
- [ ] OCSP stapling validation
- [ ] Custom resolver profiles
- [ ] Bulk domain checking

### Version 2.0
- [ ] Plugin system
- [ ] Network diagnostics (ping, traceroute)
- [ ] Certificate transparency logs
- [ ] Protocol version detection (TLS 1.0-1.3)
- [ ] API mode for automation

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Ways to Contribute
- Report bugs and issues
- Suggest new features or enhancements
- Improve documentation
- Submit pull requests with bug fixes or features
- Write tutorials or blog posts

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Textual](https://textual.textualize.io/) by Textualize.io
- DNS queries powered by [dnspython](https://www.dnspython.org/)
- Inspired by tools like `dig`, `nslookup`, and `doggo`

## Support

- **Documentation**: [https://dns-debugger.readthedocs.io](https://dns-debugger.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/yourusername/dns-debugger-tui/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/dns-debugger-tui/discussions)
- **Twitter**: [@dnsdebugger](https://twitter.com/dnsdebugger)

## Screenshots

![Main Interface](docs/screenshots/main-screen.png)
*Main query interface with results panel*

![Propagation Check](docs/screenshots/propagation.png)
*DNS propagation checker across multiple locations*

![History Panel](docs/screenshots/history.png)
*Query history with filtering*

---

**Note**: This project is under active development. Features and API may change before v1.0 release.
