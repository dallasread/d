"""Main Textual application for DNS Debugger."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Static,
    TabbedContent,
    TabPane,
    Label,
    LoadingIndicator,
)
from textual.worker import Worker, WorkerState

from dns_debugger.adapters.dns.factory import DNSAdapterFactory
from dns_debugger.domain.models.dns_record import RecordType
from dns_debugger.screens.raw_data_screen import RawDataScreen
from dns_debugger.adapters.http.factory import HTTPAdapterFactory
from dns_debugger.domain.models.http_info import HTTPMethod


class DNSPanel(Static):
    """Panel for displaying DNS information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.dns_adapter = None
        self.last_responses = {}  # Store raw responses for logs
        self.loaded = False

    def compose(self) -> ComposeResult:
        """Compose the panel with a loading indicator."""
        yield LoadingIndicator()

    def on_mount(self) -> None:
        """Show initial loading state without fetching data."""
        loading = self.query_one(LoadingIndicator)
        loading.display = False
        self.update("[dim]Switch to this tab to load DNS records[/dim]")

    def load_data(self) -> None:
        """Load DNS data when the panel is first viewed."""
        if not self.loaded:
            loading = self.query_one(LoadingIndicator)
            loading.display = True
            self.update("")
            self.run_worker(self.fetch_dns_data(), exclusive=True)

    def update_dns_info(self) -> None:
        """Refresh DNS data (called by refresh action)."""
        self.update("[dim]Refreshing DNS records...[/dim]")
        self.run_worker(self.fetch_dns_data(), exclusive=True)

    async def fetch_dns_data(self) -> None:
        """Async worker to fetch DNS information."""
        try:
            self.dns_adapter = DNSAdapterFactory.create()
            tool_name = self.dns_adapter.get_tool_name()

            # Build the entire output as a string first
            output = []
            output.append(f"[bold cyan]DNS Records for {self.domain}[/bold cyan]\n")
            output.append(f"Using: {tool_name}\n\n")

            # Query multiple record types
            record_types = [
                RecordType.A,
                RecordType.AAAA,
                RecordType.MX,
                RecordType.TXT,
                RecordType.NS,
            ]

            for record_type in record_types:
                response = self.dns_adapter.query(self.domain, record_type)

                # Store raw response for logs
                self.last_responses[record_type.value] = {
                    "query": {
                        "domain": response.query.domain,
                        "type": response.query.record_type.value,
                        "resolver": response.query.resolver,
                    },
                    "records": [
                        {
                            "name": r.name,
                            "type": r.record_type.value,
                            "value": r.value,
                            "ttl": r.ttl,
                            "class": r.record_class,
                        }
                        for r in response.records
                    ],
                    "query_time_ms": response.query_time_ms,
                    "resolver_used": response.resolver_used,
                    "timestamp": response.timestamp.isoformat(),
                    "error": response.error,
                }

                output.append(
                    f"[bold yellow]{record_type.value} Records:[/bold yellow]\n"
                )

                if response.is_success and response.record_count > 0:
                    for record in response.records:
                        output.append(
                            f"  {record.value} [dim](TTL: {record.ttl})[/dim]\n"
                        )
                else:
                    output.append(f"  [dim]No records found[/dim]\n")

                output.append("\n")

            # Update once with all content
            self.update("".join(output))
            self.loaded = True
            loading = self.query_one(LoadingIndicator)
            loading.display = False

        except Exception as e:
            self.update(f"[red]Error: {str(e)}[/red]")
            self.loaded = True
            loading = self.query_one(LoadingIndicator)
            loading.display = False


class CertificatePanel(Static):
    """Panel for displaying certificate information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.cert_adapter = None
        self.last_tls_info = None  # Store raw TLS info for logs
        self.loaded = False

    def compose(self) -> ComposeResult:
        """Compose the panel with a loading indicator."""
        yield LoadingIndicator()

    def on_mount(self) -> None:
        """Show initial loading state without fetching data."""
        loading = self.query_one(LoadingIndicator)
        loading.display = False
        self.update("[dim]Switch to this tab to load certificate info[/dim]")

    def load_data(self) -> None:
        """Load certificate data when the panel is first viewed."""
        if not self.loaded:
            loading = self.query_one(LoadingIndicator)
            loading.display = True
            self.update("")
            self.run_worker(self.fetch_cert_data(), exclusive=True)

    def update_cert_info(self) -> None:
        """Refresh certificate data (called by refresh action)."""
        self.update("[dim]Refreshing SSL/TLS certificate...[/dim]")
        self.run_worker(self.fetch_cert_data(), exclusive=True)

    async def fetch_cert_data(self) -> None:
        """Async worker to fetch certificate information."""
        try:
            from dns_debugger.adapters.cert.factory import CertificateAdapterFactory

            self.cert_adapter = CertificateAdapterFactory.create()
            tool_name = self.cert_adapter.get_tool_name()

            output = []
            output.append(
                f"[bold cyan]SSL/TLS Certificate for {self.domain}[/bold cyan]\n"
            )
            output.append(f"Using: {tool_name}\n\n")

            # Get certificate info
            tls_info = self.cert_adapter.get_certificate_info(self.domain)
            self.last_tls_info = tls_info  # Store for raw logs

            if tls_info.certificate_chain.leaf_certificate:
                cert = tls_info.certificate_chain.leaf_certificate

                output.append("[bold yellow]Certificate Details:[/bold yellow]\n")
                output.append(f"  Subject: {cert.subject.common_name}\n")
                output.append(f"  Issuer: {cert.issuer.common_name}\n")
                output.append(f"  Valid From: {cert.not_before.strftime('%Y-%m-%d')}\n")
                output.append(f"  Valid Until: {cert.not_after.strftime('%Y-%m-%d')}\n")

                if cert.is_expired:
                    output.append(f"  Status: [red]EXPIRED[/red]\n")
                elif cert.days_until_expiry < 30:
                    output.append(
                        f"  Status: [yellow]Expires in {cert.days_until_expiry} days[/yellow]\n"
                    )
                else:
                    output.append(
                        f"  Status: [green]Valid ({cert.days_until_expiry} days remaining)[/green]\n"
                    )

                output.append(f"\n[bold yellow]Public Key:[/bold yellow]\n")
                output.append(f"  Algorithm: {cert.public_key_algorithm}\n")
                output.append(f"  Size: {cert.public_key_size} bits\n")

                if cert.subject_alternative_names:
                    output.append(
                        f"\n[bold yellow]Subject Alternative Names:[/bold yellow]\n"
                    )
                    for san in cert.subject_alternative_names[:5]:  # Limit to first 5
                        output.append(f"  • {san}\n")
                    if len(cert.subject_alternative_names) > 5:
                        output.append(
                            f"  [dim]... and {len(cert.subject_alternative_names) - 5} more[/dim]\n"
                        )

                output.append(f"\n[bold yellow]Certificate Chain:[/bold yellow]\n")
                output.append(
                    f"  Chain Length: {tls_info.certificate_chain.chain_length}\n"
                )
                output.append(
                    f"  Valid: {'[green]Yes[/green]' if tls_info.certificate_chain.is_valid else '[red]No[/red]'}\n"
                )

                if tls_info.supported_versions:
                    output.append(f"\n[bold yellow]TLS Versions:[/bold yellow]\n")
                    for version in tls_info.supported_versions:
                        output.append(f"  • {version.value}\n")

                output.append(f"\n[bold yellow]Security Features:[/bold yellow]\n")
                output.append(
                    f"  OCSP Stapling: {'[green]Yes[/green]' if tls_info.has_ocsp_stapling else '[dim]No[/dim]'}\n"
                )
                output.append(
                    f"  Self-Signed: {'[yellow]Yes[/yellow]' if cert.is_self_signed else '[green]No[/green]'}\n"
                )
            else:
                output.append("[red]Failed to retrieve certificate[/red]\n")

            self.update("".join(output))
            self.loaded = True
            loading = self.query_one(LoadingIndicator)
            loading.display = False

        except Exception as e:
            self.update(f"[red]Error: {str(e)}[/red]\n\n")
            self.update(
                "[dim]Make sure OpenSSL is installed and the domain is accessible[/dim]"
            )
            self.loaded = True
            loading = self.query_one(LoadingIndicator)
            loading.display = False


class RegistryPanel(Static):
    """Panel for displaying domain registration information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.registry_adapter = None
        self.last_registration = None  # Store raw registration for logs
        self.loaded = False

    def compose(self) -> ComposeResult:
        """Compose the panel with a loading indicator."""
        yield LoadingIndicator()

    def on_mount(self) -> None:
        """Show initial loading state without fetching data."""
        loading = self.query_one(LoadingIndicator)
        loading.display = False
        self.update("[dim]Switch to this tab to load registration info[/dim]")

    def load_data(self) -> None:
        """Load registry data when the panel is first viewed."""
        if not self.loaded:
            loading = self.query_one(LoadingIndicator)
            loading.display = True
            self.update("")
            self.run_worker(self.fetch_registry_data(), exclusive=True)

    def update_registry_info(self) -> None:
        """Refresh registry data (called by refresh action)."""
        self.update("[dim]Refreshing domain registration info...[/dim]")
        self.run_worker(self.fetch_registry_data(), exclusive=True)

    async def fetch_registry_data(self) -> None:
        """Async worker to fetch domain registration information."""
        try:
            from dns_debugger.adapters.registry.factory import RegistryAdapterFactory

            self.registry_adapter = RegistryAdapterFactory.create()
            source_name = self.registry_adapter.get_source_name()

            output = []
            output.append(
                f"[bold cyan]Domain Registration for {self.domain}[/bold cyan]\n"
            )
            output.append(f"Using: {source_name}\n\n")

            # Get registration info
            registration = self.registry_adapter.lookup(self.domain)
            self.last_registration = registration  # Store for raw logs

            output.append("[bold yellow]Registrar:[/bold yellow]\n")
            output.append(
                f"  {registration.registrar or '[dim]Not available[/dim]'}\n\n"
            )

            output.append("[bold yellow]Registration Dates:[/bold yellow]\n")
            if registration.created_date:
                output.append(
                    f"  Created: {registration.created_date.strftime('%Y-%m-%d')}\n"
                )
            if registration.updated_date:
                output.append(
                    f"  Updated: {registration.updated_date.strftime('%Y-%m-%d')}\n"
                )
            if registration.expires_date:
                output.append(
                    f"  Expires: {registration.expires_date.strftime('%Y-%m-%d')}\n"
                )

                if registration.is_expired:
                    output.append(f"  Status: [red]EXPIRED[/red]\n")
                elif registration.is_expiring_soon():
                    days_left = registration.days_until_expiry
                    output.append(
                        f"  Status: [yellow]Expires in {days_left} days[/yellow]\n"
                    )
                else:
                    days_left = registration.days_until_expiry
                    output.append(
                        f"  Status: [green]Active ({days_left} days remaining)[/green]\n"
                    )

            if registration.nameservers:
                output.append(f"\n[bold yellow]Nameservers:[/bold yellow]\n")
                for ns in registration.nameservers[:5]:  # Limit to first 5
                    output.append(f"  • {ns.hostname}\n")
                    if ns.ip_addresses:
                        for ip in ns.ip_addresses[:2]:
                            output.append(f"    [dim]{ip}[/dim]\n")
                if len(registration.nameservers) > 5:
                    output.append(
                        f"  [dim]... and {len(registration.nameservers) - 5} more[/dim]\n"
                    )

            if registration.status:
                output.append(f"\n[bold yellow]Domain Status:[/bold yellow]\n")
                for status in registration.status[:5]:
                    output.append(f"  • {status}\n")

            output.append(f"\n[bold yellow]Security:[/bold yellow]\n")
            output.append(
                f"  DNSSEC: {'[green]Enabled[/green]' if registration.dnssec else '[dim]Disabled[/dim]'}\n"
            )

            if registration.registrant and registration.registrant.organization:
                output.append(f"\n[bold yellow]Registrant:[/bold yellow]\n")
                output.append(f"  {registration.registrant.organization}\n")
                if registration.registrant.country:
                    output.append(f"  {registration.registrant.country}\n")

            self.update("".join(output))
            self.loaded = True
            loading = self.query_one(LoadingIndicator)
            loading.display = False

        except Exception as e:
            self.update(f"[red]Error: {str(e)}[/red]\n\n")
            self.update(
                "[dim]Make sure 'whois' command is installed (brew install whois / apt-get install whois)[/dim]"
            )
            self.loaded = True
            loading = self.query_one(LoadingIndicator)
            loading.display = False


class DNSSECPanel(Static):
    """Panel for displaying DNSSEC information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.dns_adapter = None
        self.last_validation = None  # Store validation for logs
        self.loaded = False

    def compose(self) -> ComposeResult:
        """Compose the panel with a loading indicator."""
        yield LoadingIndicator()

    def on_mount(self) -> None:
        """Show initial loading state without fetching data."""
        loading = self.query_one(LoadingIndicator)
        loading.display = False
        self.update("[dim]Switch to this tab to load DNSSEC info[/dim]")

    def load_data(self) -> None:
        """Load DNSSEC data when the panel is first viewed."""
        if not self.loaded:
            loading = self.query_one(LoadingIndicator)
            loading.display = True
            self.update("")
            self.run_worker(self.fetch_dnssec_data(), exclusive=True)

    def update_dnssec_info(self) -> None:
        """Refresh DNSSEC data (called by refresh action)."""
        self.update("[dim]Validating DNSSEC...[/dim]")
        self.run_worker(self.fetch_dnssec_data(), exclusive=True)

    async def fetch_dnssec_data(self) -> None:
        """Async worker to fetch DNSSEC information."""
        try:
            self.dns_adapter = DNSAdapterFactory.create()
            tool_name = self.dns_adapter.get_tool_name()

            output = []
            output.append(
                f"[bold cyan]DNSSEC Validation for {self.domain}[/bold cyan]\n"
            )
            output.append(f"Using: {tool_name}\n\n")

            # Validate DNSSEC
            validation = self.dns_adapter.validate_dnssec(self.domain)
            self.last_validation = validation

            # Status
            output.append("[bold yellow]Validation Status:[/bold yellow]\n")
            if validation.is_secure:
                output.append(f"  [green]✓ SECURE[/green]\n")
            elif validation.is_insecure:
                output.append(f"  [dim]INSECURE (not signed)[/dim]\n")
            elif validation.is_bogus:
                output.append(f"  [red]✗ BOGUS (validation failed)[/red]\n")
            else:
                output.append(f"  [yellow]? INDETERMINATE[/yellow]\n")

            output.append(
                f"  Validation Time: {validation.validation_time_ms:.2f}ms\n\n"
            )

            # Error message if any
            if validation.error_message:
                output.append(f"[red]Error: {validation.error_message}[/red]\n\n")

            # Chain of trust
            if validation.chain:
                chain = validation.chain
                output.append("[bold yellow]Chain of Trust:[/bold yellow]\n")
                output.append(
                    f"  Domain Signed: {'[green]Yes[/green]' if chain.is_signed else '[dim]No[/dim]'}\n"
                )
                output.append(
                    f"  DS in Parent: {'[green]Yes[/green]' if chain.has_ds_record else '[dim]No[/dim]'}\n"
                )
                output.append(
                    f"  Complete Chain: {'[green]Yes[/green]' if chain.has_chain_of_trust else '[dim]No[/dim]'}\n\n"
                )

                # DNSKEY records
                if chain.dnskey_records:
                    output.append("[bold yellow]DNSKEY Records:[/bold yellow]\n")
                    output.append(f"  Total Keys: {len(chain.dnskey_records)}\n")
                    output.append(f"  Key Signing Keys (KSK): {chain.ksk_count}\n")
                    output.append(f"  Zone Signing Keys (ZSK): {chain.zsk_count}\n\n")

                    for i, key in enumerate(chain.dnskey_records[:3], 1):
                        key_type = "KSK" if key.is_key_signing_key else "ZSK"
                        output.append(f"  Key {i} ({key_type}):\n")
                        output.append(f"    Flags: {key.flags}\n")
                        output.append(f"    Algorithm: {key.algorithm.value}\n")
                        output.append(f"    Key Tag: {key.key_tag}\n")
                        output.append(f"    TTL: {key.ttl}s\n")

                    if len(chain.dnskey_records) > 3:
                        output.append(
                            f"  [dim]... and {len(chain.dnskey_records) - 3} more keys[/dim]\n"
                        )
                    output.append("\n")

                # DS records
                if chain.ds_records:
                    output.append(
                        "[bold yellow]DS Records (in parent zone):[/bold yellow]\n"
                    )
                    for i, ds in enumerate(chain.ds_records[:3], 1):
                        output.append(f"  DS {i}:\n")
                        output.append(f"    Key Tag: {ds.key_tag}\n")
                        output.append(f"    Algorithm: {ds.algorithm.value}\n")
                        output.append(f"    Digest Type: {ds.digest_type.value}\n")
                        output.append(f"    Digest: {ds.digest[:32]}...\n")
                        output.append(f"    TTL: {ds.ttl}s\n")

                    if len(chain.ds_records) > 3:
                        output.append(
                            f"  [dim]... and {len(chain.ds_records) - 3} more DS records[/dim]\n"
                        )
                    output.append("\n")

                # Signatures
                if chain.has_rrsig_record:
                    output.append("[bold yellow]Signatures:[/bold yellow]\n")
                    output.append(f"  [green]✓ RRSIG records present[/green]\n\n")

            # Warnings
            if validation.has_warnings:
                output.append("[bold yellow]Warnings:[/bold yellow]\n")
                for warning in validation.warnings:
                    output.append(f"  [yellow]⚠[/yellow] {warning}\n")
                output.append("\n")

            self.update("".join(output))
            self.loaded = True
            loading = self.query_one(LoadingIndicator)
            loading.display = False

        except Exception as e:
            self.update(f"[red]Error: {str(e)}[/red]\n\n")
            self.update("[dim]Make sure 'dog' or 'dig' is installed[/dim]")
            self.loaded = True
            loading = self.query_one(LoadingIndicator)
            loading.display = False


class HTTPPanel(Static):
    """Panel for displaying HTTP/HTTPS information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.http_adapter = None
        self.last_response = None  # Store raw response for logs
        self.loaded = False

    def compose(self) -> ComposeResult:
        """Compose the panel with a loading indicator."""
        yield LoadingIndicator()

    def on_mount(self) -> None:
        """Show initial loading state without fetching data."""
        loading = self.query_one(LoadingIndicator)
        loading.display = False
        self.update("[dim]Switch to this tab to load HTTP info[/dim]")

    def load_data(self) -> None:
        """Load HTTP data when the panel is first viewed."""
        if not self.loaded:
            loading = self.query_one(LoadingIndicator)
            loading.display = True
            self.update("")
            self.run_worker(self.fetch_http_data(), exclusive=True)

    def update_http_info(self) -> None:
        """Refresh HTTP data (called by refresh action)."""
        self.update("[dim]Refreshing HTTP/HTTPS status...[/dim]")
        self.run_worker(self.fetch_http_data(), exclusive=True)

    async def fetch_http_data(self) -> None:
        """Async worker to fetch HTTP information."""
        try:
            self.http_adapter = HTTPAdapterFactory.create()
            tool_name = self.http_adapter.get_tool_name()

            output = []
            output.append(f"[bold cyan]HTTP/HTTPS for {self.domain}[/bold cyan]\n")
            output.append(f"Using: {tool_name}\n\n")

            # Test both HTTP and HTTPS
            for protocol in ["https", "http"]:
                url = f"{protocol}://{self.domain}"
                output.append(
                    f"[bold yellow]{protocol.upper()}://{self.domain}[/bold yellow]\n"
                )

                response = self.http_adapter.check_url(url)
                self.last_response = response  # Store for logs

                if response.error:
                    output.append(f"  [red]Error: {response.error}[/red]\n")
                else:
                    # Status
                    if response.is_success:
                        status_color = "green"
                    elif response.is_redirect:
                        status_color = "yellow"
                    elif response.is_client_error or response.is_server_error:
                        status_color = "red"
                    else:
                        status_color = "white"

                    output.append(
                        f"  Status: [{status_color}]{response.status_code} {response.status_text}[/{status_color}]\n"
                    )
                    output.append(
                        f"  Response Time: {response.response_time_ms:.2f}ms\n"
                    )

                    # Redirect chain
                    if response.was_redirected:
                        output.append(
                            f"\n  [bold]Redirect Chain ({response.redirect_count} redirect(s)):[/bold]\n"
                        )
                        for i, redirect in enumerate(response.redirect_chain, 1):
                            output.append(
                                f"    {i}. {redirect.status_code} → {redirect.to_url}\n"
                            )
                        output.append(f"    Final: {response.final_url}\n")

                    # Headers
                    if response.server:
                        output.append(f"  Server: {response.server}\n")
                    if response.content_type:
                        output.append(f"  Content-Type: {response.content_type}\n")
                    if response.content_length is not None:
                        output.append(
                            f"  Content-Length: {response.content_length} bytes\n"
                        )

                output.append("\n")

            self.update("".join(output))
            self.loaded = True
            loading = self.query_one(LoadingIndicator)
            loading.display = False

        except Exception as e:
            self.update(f"[red]Error: {str(e)}[/red]\n\n")
            self.update("[dim]Make sure 'curl' or 'wget' is installed[/dim]")
            self.loaded = True
            loading = self.query_one(LoadingIndicator)
            loading.display = False


class DNSDebuggerApp(App):
    """Main DNS Debugger TUI application."""

    CSS = """
    Screen {
        background: $background;
    }

    Header {
        background: $primary;
    }

    Footer {
        background: $primary;
    }

    TabbedContent {
        height: 100%;
    }

    TabPane {
        padding: 1 2;
    }

    Static {
        height: auto;
    }

    #main-container {
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", key_display="Q"),
        Binding("r", "refresh", "Refresh", key_display="R"),
        Binding("l", "show_raw", "Raw Logs", key_display="L"),
        Binding("h", "help", "Help", key_display="H/?"),
        ("question_mark", "help", "Help"),
    ]

    def __init__(self, domain: str, theme: str = "dark") -> None:
        super().__init__()
        self.domain = domain
        # Note: Textual uses CSS for theming, not a theme attribute
        self.title = domain
        self.sub_title = ""

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header(show_clock=True)

        with Container(id="main-container"):
            with TabbedContent(initial="registry"):
                with TabPane("Registration", id="registry"):
                    yield RegistryPanel(self.domain)

                with TabPane("DNS", id="dns"):
                    yield DNSPanel(self.domain)

                with TabPane("DNSSEC", id="dnssec"):
                    yield DNSSECPanel(self.domain)

                with TabPane("Certificate", id="cert"):
                    yield CertificatePanel(self.domain)

                with TabPane("HTTP", id="http"):
                    yield HTTPPanel(self.domain)

        yield Footer()

    def on_mount(self) -> None:
        """Load the initial DNS panel when app starts."""
        # Defer loading to next tick to not block UI rendering
        self.call_later(self._load_initial_panel)

    def _load_initial_panel(self) -> None:
        """Load the Registration panel data on next tick."""
        registry_panel = self.query_one(RegistryPanel)
        registry_panel.load_data()

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        """Load data when a tab is activated."""
        # Defer loading to next tick to not block UI thread
        self.call_later(self._load_active_panel)

    def _load_active_panel(self) -> None:
        """Load data for the currently active panel on next tick."""
        # Get the active pane ID from the TabbedContent widget
        tabbed_content = self.query_one(TabbedContent)
        active_pane = tabbed_content.active

        # Load data for the active panel if not already loaded
        if active_pane == "dns":
            dns_panel = self.query_one(DNSPanel)
            dns_panel.load_data()
        elif active_pane == "dnssec":
            dnssec_panel = self.query_one(DNSSECPanel)
            dnssec_panel.load_data()
        elif active_pane == "registry":
            registry_panel = self.query_one(RegistryPanel)
            registry_panel.load_data()
        elif active_pane == "cert":
            cert_panel = self.query_one(CertificatePanel)
            cert_panel.load_data()
        elif active_pane == "http":
            http_panel = self.query_one(HTTPPanel)
            http_panel.load_data()

    def action_refresh(self) -> None:
        """Refresh the current view."""
        # Get the active tab
        tabbed_content = self.query_one(TabbedContent)
        active_pane = tabbed_content.active

        # Refresh the content in the active pane
        if active_pane == "dns":
            dns_panel = self.query_one(DNSPanel)
            dns_panel.update_dns_info()
        elif active_pane == "dnssec":
            dnssec_panel = self.query_one(DNSSECPanel)
            dnssec_panel.update_dnssec_info()
        elif active_pane == "http":
            http_panel = self.query_one(HTTPPanel)
            http_panel.update_http_info()
        elif active_pane == "cert":
            cert_panel = self.query_one(CertificatePanel)
            cert_panel.update_cert_info()
        elif active_pane == "registry":
            registry_panel = self.query_one(RegistryPanel)
            registry_panel.update_registry_info()

        self.notify("Refreshed!", severity="information")

    def action_show_raw(self) -> None:
        """Show raw logs for the current panel."""
        tabbed_content = self.query_one(TabbedContent)
        active_pane = tabbed_content.active

        raw_data = None
        title = ""

        if active_pane == "dns":
            dns_panel = self.query_one(DNSPanel)
            if dns_panel.last_responses:
                raw_data = dns_panel.last_responses
                title = f"DNS Raw Data - {dns_panel.domain}"
        elif active_pane == "dnssec":
            dnssec_panel = self.query_one(DNSSECPanel)
            if dnssec_panel.last_validation:
                val = dnssec_panel.last_validation
                raw_data = {
                    "domain": val.domain,
                    "status": val.status.value,
                    "validation_time_ms": val.validation_time_ms,
                    "timestamp": val.timestamp.isoformat(),
                    "error_message": val.error_message,
                    "warnings": val.warnings,
                }
                if val.chain:
                    chain = val.chain
                    raw_data["chain"] = {
                        "domain": chain.domain,
                        "has_ds_record": chain.has_ds_record,
                        "has_dnskey_record": chain.has_dnskey_record,
                        "has_rrsig_record": chain.has_rrsig_record,
                        "is_signed": chain.is_signed,
                        "has_chain_of_trust": chain.has_chain_of_trust,
                        "ksk_count": chain.ksk_count,
                        "zsk_count": chain.zsk_count,
                        "ds_records": [
                            {
                                "key_tag": ds.key_tag,
                                "algorithm": ds.algorithm.value,
                                "digest_type": ds.digest_type.value,
                                "digest": ds.digest,
                                "ttl": ds.ttl,
                            }
                            for ds in chain.ds_records
                        ],
                        "dnskey_records": [
                            {
                                "flags": key.flags,
                                "protocol": key.protocol,
                                "algorithm": key.algorithm.value,
                                "key_tag": key.key_tag,
                                "public_key": key.public_key[:64] + "...",
                                "ttl": key.ttl,
                                "is_ksk": key.is_key_signing_key,
                                "is_zsk": key.is_zone_signing_key,
                            }
                            for key in chain.dnskey_records
                        ],
                    }
                title = f"DNSSEC Raw Data - {dnssec_panel.domain}"
        elif active_pane == "http":
            http_panel = self.query_one(HTTPPanel)
            if http_panel.last_response:
                resp = http_panel.last_response
                raw_data = {
                    "url": resp.url,
                    "final_url": resp.final_url,
                    "status_code": resp.status_code,
                    "status_text": resp.status_text,
                    "response_time_ms": resp.response_time_ms,
                    "was_redirected": resp.was_redirected,
                    "redirect_count": resp.redirect_count,
                    "redirect_chain": [
                        {
                            "from_url": r.from_url,
                            "to_url": r.to_url,
                            "status_code": r.status_code,
                            "location_header": r.location_header,
                        }
                        for r in resp.redirect_chain
                    ],
                    "headers": resp.headers,
                    "content_length": resp.content_length,
                    "content_type": resp.content_type,
                    "server": resp.server,
                    "timestamp": resp.timestamp.isoformat(),
                    "error": resp.error,
                }
                title = f"HTTP Raw Data - {http_panel.domain}"
        elif active_pane == "cert":
            cert_panel = self.query_one(CertificatePanel)
            if cert_panel.last_tls_info:
                # Convert TLSInfo to dict for display
                tls = cert_panel.last_tls_info
                raw_data = {
                    "host": tls.host,
                    "port": tls.port,
                    "connection_time_ms": tls.connection_time_ms,
                    "timestamp": tls.timestamp.isoformat(),
                    "has_ocsp_stapling": tls.has_ocsp_stapling,
                    "supports_sni": tls.supports_sni,
                    "supported_versions": [v.value for v in tls.supported_versions],
                    "cipher_suites": tls.cipher_suites,
                    "certificate_chain": {
                        "chain_length": tls.certificate_chain.chain_length,
                        "is_valid": tls.certificate_chain.is_valid,
                        "validation_errors": tls.certificate_chain.validation_errors,
                        "certificates": [
                            {
                                "subject": str(cert.subject),
                                "issuer": str(cert.issuer),
                                "serial_number": cert.serial_number,
                                "not_before": cert.not_before.isoformat(),
                                "not_after": cert.not_after.isoformat(),
                                "is_expired": cert.is_expired,
                                "days_until_expiry": cert.days_until_expiry,
                                "public_key_algorithm": cert.public_key_algorithm,
                                "public_key_size": cert.public_key_size,
                                "signature_algorithm": cert.signature_algorithm,
                                "subject_alternative_names": cert.subject_alternative_names,
                                "fingerprint_sha256": cert.fingerprint_sha256,
                            }
                            for cert in tls.certificate_chain.certificates
                        ],
                    },
                }
                title = f"Certificate Raw Data - {cert_panel.domain}"
        elif active_pane == "registry":
            registry_panel = self.query_one(RegistryPanel)
            if registry_panel.last_registration:
                # Use the raw_data from registration if available
                raw_data = registry_panel.last_registration.raw_data
                title = f"Registration Raw Data - {registry_panel.domain}"

        if raw_data:
            self.push_screen(RawDataScreen(title, raw_data))
        else:
            self.notify(
                "No raw data available yet. Try refreshing first.", severity="warning"
            )

    def action_help(self) -> None:
        """Show help information."""
        help_text = (
            "[bold cyan]DNS Debugger - Keyboard Shortcuts[/bold cyan]\n\n"
            "[bold]Q[/bold] - Quit application\n"
            "[bold]R[/bold] - Refresh current view\n"
            "[bold]L[/bold] - Show raw logs/data (JSON)\n"
            "[bold]H/?[/bold] - Show this help\n"
            "[bold]Tab[/bold] - Switch between panels\n\n"
            "[dim]Press Esc to close[/dim]"
        )
        self.push_screen(RawDataScreen("Help", help_text))

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_tui(domain: str, theme: str = "dark") -> None:
    """Run the Textual TUI application.

    Args:
        domain: The domain to debug
        theme: The UI theme to use
    """
    app = DNSDebuggerApp(domain, theme)
    app.run()
