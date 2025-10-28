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
from dns_debugger.adapters.email.factory import EmailAdapterFactory
from dns_debugger.state import StateManager


class HealthSection(Static):
    """A section within the dashboard showing health status."""

    def __init__(self, title: str, section_id: str) -> None:
        super().__init__(id=section_id)
        self.title = title
        self._content = ""

    def on_mount(self) -> None:
        """Initialize with loading state."""
        self.update(f"[bold]{self.title}[/bold]\n[dim]Loading...[/dim]")

    def set_content(self, content: str) -> None:
        """Update section content."""
        self._content = content
        self.update(f"[bold]{self.title}[/bold]\n{content}")

    def set_error(self, error: str) -> None:
        """Set error state."""
        self.update(f"[bold]{self.title}[/bold]\n[red]Error: {error}[/red]")


class DashboardPanel(Container):
    """Dashboard panel showing overall health status."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.loaded = False

    def compose(self) -> ComposeResult:
        """Compose the dashboard with health sections in columns."""
        yield Static(
            f"[bold cyan]Health Dashboard - {self.domain}[/bold cyan]  [dim]Press 0-5 to jump to tabs[/dim]",
            id="dashboard-header",
        )

        with Horizontal(id="dashboard-sections"):
            # Left side - full height Registration
            yield HealthSection("📋 Registration [dim]→ 1[/dim]", "health-registry")

            # Right side - 3 rows of sections
            with Vertical(id="dashboard-right"):
                with Horizontal(id="dashboard-row-1"):
                    yield HealthSection("📡 DNS [dim]→ 2[/dim]", "health-dns")
                    yield HealthSection("📧 Email [dim]→ 6[/dim]", "health-email")

                with Horizontal(id="dashboard-row-2"):
                    yield HealthSection("🔐 DNSSEC [dim]→ 3[/dim]", "health-dnssec")
                    yield HealthSection("🔒 Certificate [dim]→ 4[/dim]", "health-cert")

                with Horizontal(id="dashboard-row-3"):
                    yield HealthSection("🌐 HTTP/HTTPS [dim]→ 5[/dim]", "health-http")

    def on_mount(self) -> None:
        """Dashboard is ready but data not loaded."""
        pass

    def render_from_state(self, state) -> None:
        """Render dashboard from state data."""
        # Call all health check rendering methods
        self.render_http_health(state)
        self.render_cert_health(state)
        self.render_dns_health(state)
        self.render_registry_health(state)
        self.render_dnssec_health(state)
        self.render_email_health(state)

    def render_http_health(self, state) -> None:
        """Render HTTP/HTTPS health from state."""
        section = self.query_one("#health-http", HealthSection)
        try:
            https_response = state.http_response
            if not https_response:
                section.set_content("No data available")
                return

            output = []

            if https_response.error:
                output.append(f"  [red]✗ HTTPS Failed[/red]: {https_response.error}\n")
            else:
                if https_response.is_success:
                    output.append(
                        f"  [green]✓ HTTPS: {https_response.status_code}[/green]"
                    )
                elif https_response.is_redirect:
                    output.append(
                        f"  [yellow]↻ HTTPS: {https_response.status_code}[/yellow] → {https_response.final_url}"
                    )
                else:
                    output.append(f"  [red]✗ HTTPS: {https_response.status_code}[/red]")

                output.append(f" ({https_response.response_time_ms:.0f}ms)\n")

                if https_response.was_redirected:
                    output.append(f"  Redirects: {https_response.redirect_count}\n")

            section.set_content("".join(output))

        except Exception as e:
            section.set_error(str(e))

    def render_cert_health(self, state) -> None:
        """Render SSL/TLS certificate health from state."""
        section = self.query_one("#health-cert", HealthSection)
        try:
            tls_info = state.tls_info
            if not tls_info:
                section.set_content("No data available")
                return

            output = []

            if tls_info.certificate_chain.leaf_certificate:
                cert = tls_info.certificate_chain.leaf_certificate

                if cert.is_expired:
                    output.append(f"  [red]✗ Certificate EXPIRED[/red]\n")
                elif cert.days_until_expiry < 30:
                    output.append(
                        f"  [yellow]⚠ Expires in {cert.days_until_expiry} days[/yellow]\n"
                    )
                else:
                    output.append(
                        f"  [green]✓ Valid for {cert.days_until_expiry} days[/green]\n"
                    )

                output.append(f"  Issuer: {cert.issuer.common_name}\n")
                output.append(f"  Expires: {cert.not_after.strftime('%Y-%m-%d')}\n")

                if tls_info.certificate_chain.is_valid:
                    output.append(f"  Chain: [green]✓ Valid[/green]\n")
                else:
                    output.append(f"  Chain: [red]✗ Invalid[/red]\n")
            else:
                output.append(f"  [red]✗ No certificate found[/red]\n")

            section.set_content("".join(output))

        except Exception as e:
            section.set_error(str(e))

    def render_dns_health(self, state) -> None:
        """Render DNS records health from state."""
        section = self.query_one("#health-dns", HealthSection)
        try:
            if not state.dns_responses:
                section.set_content("No data available")
                return

            output = []

            # Check key record types from state
            a_response = state.dns_responses.get(RecordType.A.value)
            aaaa_response = state.dns_responses.get(RecordType.AAAA.value)
            mx_response = state.dns_responses.get(RecordType.MX.value)
            ns_response = state.dns_responses.get(RecordType.NS.value)

            # A records
            if a_response.is_success and a_response.record_count > 0:
                output.append(
                    f"  [green]✓ A[/green]: {a_response.record_count} record(s)\n"
                )
            else:
                output.append(f"  [dim]○ A: None[/dim]\n")

            # AAAA records
            if aaaa_response.is_success and aaaa_response.record_count > 0:
                output.append(
                    f"  [green]✓ AAAA[/green]: {aaaa_response.record_count} record(s)\n"
                )
            else:
                output.append(f"  [dim]○ AAAA: None[/dim]\n")

            # MX records
            if mx_response.is_success and mx_response.record_count > 0:
                output.append(
                    f"  [green]✓ MX[/green]: {mx_response.record_count} record(s)\n"
                )
            else:
                output.append(f"  [dim]○ MX: None[/dim]\n")

            # NS records
            if ns_response.is_success and ns_response.record_count > 0:
                output.append(
                    f"  [green]✓ NS[/green]: {ns_response.record_count} record(s)\n"
                )
            else:
                output.append(f"  [red]✗ NS: None[/red]\n")

            section.set_content("".join(output))

        except Exception as e:
            section.set_error(str(e))

    def render_registry_health(self, state) -> None:
        """Render domain registration health from state."""
        section = self.query_one("#health-registry", HealthSection)
        try:
            registration = state.registration
            if not registration:
                section.set_content("No data available")
                return

            output = []

            # Expiration status
            if registration.is_expired:
                output.append(f"  [red]✗ Domain EXPIRED[/red]\n")
            elif registration.is_expiring_soon():
                days_left = registration.days_until_expiry
                output.append(f"  [yellow]⚠ Expires in {days_left} days[/yellow]\n")
            else:
                days_left = registration.days_until_expiry
                output.append(f"  [green]✓ Active ({days_left} days)[/green]\n")

            if registration.expires_date:
                output.append(
                    f"  Expires: {registration.expires_date.strftime('%Y-%m-%d')}\n"
                )

            # Registrar
            if registration.registrar:
                output.append(f"  Registrar: {registration.registrar[:30]}\n")

            # DNSSEC at registry level
            if registration.dnssec:
                output.append(f"  DNSSEC: [green]✓ Enabled[/green]\n")
            else:
                output.append(f"  DNSSEC: [dim]Disabled[/dim]\n")

            # Nameservers
            if registration.nameservers:
                output.append(f"  Nameservers: {len(registration.nameservers)}\n")

            section.set_content("".join(output))

        except Exception as e:
            section.set_error(str(e))

    def render_dnssec_health(self, state) -> None:
        """Render DNSSEC health from state."""
        section = self.query_one("#health-dnssec", HealthSection)
        try:
            validation = state.dnssec_validation
            if not validation:
                section.set_content("No data available")
                return

            output = []

            # Validation status
            if validation.is_secure:
                output.append(f"  [green]✓ SECURE[/green]\n")
            elif validation.is_insecure:
                output.append(f"  [dim]○ Not signed[/dim]\n")
            elif validation.is_bogus:
                output.append(f"  [red]✗ BOGUS[/red]\n")
            else:
                output.append(f"  [yellow]? INDETERMINATE[/yellow]\n")

            if validation.chain:
                chain = validation.chain

                if chain.has_dnskey_record:
                    output.append(f"  DNSKEY: [green]✓ Present[/green]\n")
                else:
                    output.append(f"  DNSKEY: [dim]None[/dim]\n")

                if chain.has_ds_record:
                    output.append(f"  DS Record: [green]✓ Present[/green]\n")
                else:
                    output.append(f"  DS Record: [dim]None[/dim]\n")

                if chain.ksk_count > 0 or chain.zsk_count > 0:
                    output.append(
                        f"  Keys: {chain.ksk_count} KSK, {chain.zsk_count} ZSK\n"
                    )

            if validation.has_warnings:
                output.append(
                    f"  [yellow]⚠ {len(validation.warnings)} warning(s)[/yellow]\n"
                )

            section.set_content("".join(output))

        except Exception as e:
            section.set_error(str(e))

    def render_email_health(self, state) -> None:
        """Render email configuration health from state."""
        section = self.query_one("#health-email", HealthSection)
        try:
            email_config = state.email_config
            if not email_config:
                section.set_content("No data available")
                return

            output = []

            # MX Records
            if email_config.has_mx:
                output.append(
                    f"  [green]✓ MX[/green]: {len(email_config.mx_records)} record(s)\n"
                )
            else:
                output.append(f"  [red]✗ MX: None[/red]\n")

            # SPF
            if email_config.has_spf:
                if email_config.spf_record.is_strict:
                    output.append(f"  [green]✓ SPF: Strict (-all)[/green]\n")
                else:
                    output.append(
                        f"  [yellow]○ SPF: {email_config.spf_record.all_mechanism or 'present'}[/yellow]\n"
                    )
            else:
                output.append(f"  [red]✗ SPF: None[/red]\n")

            # DKIM
            if email_config.has_dkim:
                dkim_count = sum(1 for d in email_config.dkim_records if d.exists)
                output.append(f"  [green]✓ DKIM: {dkim_count} selector(s)[/green]\n")
            else:
                output.append(f"  [yellow]○ DKIM: Not found[/yellow]\n")

            # DMARC
            if email_config.has_dmarc:
                if email_config.dmarc_record.is_enforcing:
                    output.append(
                        f"  [green]✓ DMARC: {email_config.dmarc_record.policy.value}[/green]\n"
                    )
                else:
                    output.append(
                        f"  [yellow]○ DMARC: {email_config.dmarc_record.policy.value}[/yellow]\n"
                    )
            else:
                output.append(f"  [red]✗ DMARC: None[/red]\n")

            # Provider
            if email_config.email_provider:
                output.append(f"  Provider: {email_config.email_provider}\n")

            # Security score
            score = email_config.security_score
            if score >= 80:
                output.append(f"  Score: [green]{score}/100[/green]\n")
            elif score >= 50:
                output.append(f"  Score: [yellow]{score}/100[/yellow]\n")
            else:
                output.append(f"  Score: [red]{score}/100[/red]\n")

            section.set_content("".join(output))

        except Exception as e:
            section.set_error(str(e))


class DNSPanel(Static):
    """Panel for displaying DNS information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.dns_adapter = None
        self.last_responses = {}  # Store raw responses for logs

    def on_mount(self) -> None:
        """Panel mounted - will be populated from state."""
        pass

    def render_from_state(self, state) -> None:
        """Render panel from state data."""
        if not state.dns_responses:
            self.update("[dim]No DNS data available[/dim]")
            return

        self._render_dns_data(state.dns_responses)

    def _render_dns_data(self, dns_responses: dict) -> None:
        """Render DNS data from responses dict."""
        try:
            output = []
            output.append(f"[bold cyan]DNS Records for {self.domain}[/bold cyan]\n")
            output.append(f"Using: DNS queries\n\n")

            # Iterate through record types
            for record_type in [
                RecordType.A,
                RecordType.AAAA,
                RecordType.MX,
                RecordType.TXT,
                RecordType.NS,
            ]:
                response = dns_responses.get(record_type.value)

                if not response:
                    continue

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

            self.update("".join(output))

        except Exception as e:
            self.update(f"[red]Error: {str(e)}[/red]")


class CertificatePanel(Static):
    """Panel for displaying certificate information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.cert_adapter = None
        self.last_tls_info = None  # Store raw TLS info for logs

    def on_mount(self) -> None:
        """Panel mounted - data already loaded via dashboard."""
        pass

    def render_from_state(self, state) -> None:
        """Render panel from state data."""
        if not state.tls_info:
            self.update("[dim]No certificate data available[/dim]")
            return
        self._render_cert_data(state.tls_info)

    def _render_cert_data(self, tls_info) -> None:
        """Render certificate data from TLS info."""
        # TODO: Implement rendering from state
        self.update(
            "[yellow]Certificate panel - rendering from state not yet implemented[/yellow]"
        )

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

        except Exception as e:
            self.update(
                f"[red]Error: {str(e)}[/red]\n\n[dim]Make sure OpenSSL is installed and the domain is accessible[/dim]"
            )


class RegistryPanel(Static):
    """Panel for displaying domain registration information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.registry_adapter = None
        self.last_registration = None  # Store raw registration for logs

    def on_mount(self) -> None:
        """Panel mounted - data already loaded via dashboard."""
        pass

    def render_from_state(self, state) -> None:
        """Render panel from state data."""
        self.update(
            "[yellow]Registry panel - rendering from state not yet implemented[/yellow]"
        )

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

        except Exception as e:
            self.update(
                f"[red]Error: {str(e)}[/red]\n\n[dim]Make sure 'whois' command is installed (brew install whois / apt-get install whois)[/dim]"
            )


class DNSSECPanel(Static):
    """Panel for displaying DNSSEC information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.dns_adapter = None
        self.last_validation = None  # Store validation for logs

    def on_mount(self) -> None:
        """Panel mounted - data already loaded via dashboard."""
        pass

    def render_from_state(self, state) -> None:
        """Render panel from state data."""
        self.update(
            "[yellow]DNSSEC panel - rendering from state not yet implemented[/yellow]"
        )

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

        except Exception as e:
            self.update(
                f"[red]Error: {str(e)}[/red]\n\n[dim]Make sure 'dog' or 'dig' is installed[/dim]"
            )


class HTTPPanel(Static):
    """Panel for displaying HTTP/HTTPS information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.http_adapter = None
        self.last_response = None  # Store raw response for logs

    def on_mount(self) -> None:
        """Panel mounted - data already loaded via dashboard."""
        pass

    def render_from_state(self, state) -> None:
        """Render panel from state data."""
        self.update(
            "[yellow]HTTP panel - rendering from state not yet implemented[/yellow]"
        )

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

        except Exception as e:
            self.update(
                f"[red]Error: {str(e)}[/red]\n\n[dim]Make sure 'curl' or 'wget' is installed[/dim]"
            )


class EmailPanel(Static):
    """Panel for displaying email configuration information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.email_adapter = None
        self.last_email_config = None  # Store raw config for logs

    def on_mount(self) -> None:
        """Panel mounted - data already loaded via dashboard."""
        pass

    def render_from_state(self, state) -> None:
        """Render panel from state data."""
        self.update(
            "[yellow]Email panel - rendering from state not yet implemented[/yellow]"
        )

    def update_email_info(self) -> None:
        """Refresh email data (called by refresh action)."""
        self.update("[dim]Refreshing email configuration...[/dim]")
        self.run_worker(self.fetch_email_data(), exclusive=True)

    async def fetch_email_data(self) -> None:
        """Async worker to fetch email configuration."""
        try:
            self.email_adapter = EmailAdapterFactory.create()

            output = []
            output.append(
                f"[bold cyan]Email Configuration for {self.domain}[/bold cyan]\n"
            )
            output.append(f"Using: DNS queries\n\n")

            # Get email configuration
            email_config = self.email_adapter.get_email_config(self.domain)
            self.last_email_config = email_config  # Store for logs

            # Overall security score
            score = email_config.security_score
            if score >= 80:
                score_color = "green"
            elif score >= 50:
                score_color = "yellow"
            else:
                score_color = "red"
            output.append(
                f"[bold]Security Score: [{score_color}]{score}/100[/{score_color}][/bold]\n\n"
            )

            # Email Provider
            if email_config.email_provider:
                output.append(f"[bold yellow]Email Provider:[/bold yellow]\n")
                output.append(f"  {email_config.email_provider}\n\n")

            # MX Records
            output.append("[bold yellow]MX Records:[/bold yellow]\n")
            if email_config.has_mx:
                for mx in email_config.mx_records:
                    output.append(f"  Priority {mx.priority}: {mx.hostname}\n")
                    if mx.ip_addresses:
                        for ip in mx.ip_addresses[:2]:
                            output.append(f"    [dim]{ip}[/dim]\n")
            else:
                output.append(f"  [red]✗ No MX records found[/red]\n")
            output.append("\n")

            # SPF Record
            output.append("[bold yellow]SPF (Sender Policy Framework):[/bold yellow]\n")
            if email_config.has_spf:
                spf = email_config.spf_record
                output.append(
                    f"  Record: [dim]{spf.record[:80]}{'...' if len(spf.record) > 80 else ''}[/dim]\n"
                )

                if spf.is_strict:
                    output.append(f"  Policy: [green]✓ Strict (-all)[/green]\n")
                elif spf.all_mechanism == "~all":
                    output.append(f"  Policy: [yellow]○ Soft Fail (~all)[/yellow]\n")
                elif spf.all_mechanism == "+all":
                    output.append(f"  Policy: [red]✗ Allow All (+all)[/red]\n")
                elif spf.all_mechanism:
                    output.append(f"  Policy: {spf.all_mechanism}\n")
                else:
                    output.append(f"  Policy: [dim]No 'all' mechanism[/dim]\n")

                if spf.mechanisms:
                    output.append(f"  Mechanisms: {len(spf.mechanisms)}\n")
            else:
                output.append(f"  [red]✗ No SPF record found[/red]\n")
                output.append(
                    f"  [dim]Recommendation: Add TXT record with SPF policy[/dim]\n"
                )
            output.append("\n")

            # DKIM Records
            output.append(
                "[bold yellow]DKIM (DomainKeys Identified Mail):[/bold yellow]\n"
            )
            if email_config.has_dkim:
                found_count = sum(1 for d in email_config.dkim_records if d.exists)
                output.append(f"  Found {found_count} selector(s):\n")
                for dkim in email_config.dkim_records:
                    if dkim.exists:
                        output.append(f"    [green]✓[/green] {dkim.selector}\n")
                        if dkim.public_key:
                            key_preview = (
                                dkim.public_key[:40] + "..."
                                if len(dkim.public_key) > 40
                                else dkim.public_key
                            )
                            output.append(f"      [dim]{key_preview}[/dim]\n")
            else:
                output.append(f"  [yellow]○ No DKIM records found[/yellow]\n")
                output.append(
                    f"  [dim]Checked selectors: default, google, k1, s1, s2, selector1, selector2[/dim]\n"
                )
                output.append(
                    f"  [dim]Note: DKIM selector names are provider-specific[/dim]\n"
                )
            output.append("\n")

            # DMARC Record
            output.append(
                "[bold yellow]DMARC (Domain-based Message Authentication):[/bold yellow]\n"
            )
            if email_config.has_dmarc:
                dmarc = email_config.dmarc_record
                output.append(
                    f"  Record: [dim]{dmarc.record[:80]}{'...' if len(dmarc.record) > 80 else ''}[/dim]\n"
                )

                # Policy
                if dmarc.is_enforcing:
                    policy_color = "green"
                elif dmarc.policy.value == "none":
                    policy_color = "yellow"
                else:
                    policy_color = "white"
                output.append(
                    f"  Policy: [{policy_color}]{dmarc.policy.value}[/{policy_color}]\n"
                )

                if dmarc.subdomain_policy:
                    output.append(
                        f"  Subdomain Policy: {dmarc.subdomain_policy.value}\n"
                    )

                # Alignment
                if dmarc.dkim_alignment:
                    align_text = "strict" if dmarc.dkim_alignment == "s" else "relaxed"
                    output.append(f"  DKIM Alignment: {align_text}\n")
                if dmarc.spf_alignment:
                    align_text = "strict" if dmarc.spf_alignment == "s" else "relaxed"
                    output.append(f"  SPF Alignment: {align_text}\n")

                # Reporting
                if dmarc.aggregate_report_uri:
                    output.append(
                        f"  Aggregate Reports: {dmarc.aggregate_report_uri[:50]}\n"
                    )
                if dmarc.forensic_report_uri:
                    output.append(
                        f"  Forensic Reports: {dmarc.forensic_report_uri[:50]}\n"
                    )

                if dmarc.percentage and dmarc.percentage < 100:
                    output.append(
                        f"  [yellow]Coverage: {dmarc.percentage}% of messages[/yellow]\n"
                    )
            else:
                output.append(f"  [red]✗ No DMARC record found[/red]\n")
                output.append(
                    f"  [dim]Recommendation: Add TXT record at _dmarc.{self.domain}[/dim]\n"
                )
            output.append("\n")

            # Recommendations
            output.append("[bold yellow]Configuration Status:[/bold yellow]\n")
            if not email_config.has_mx:
                output.append(
                    f"  [red]✗ Missing MX records - email delivery not configured[/red]\n"
                )
            if not email_config.has_spf:
                output.append(f"  [red]✗ Missing SPF - risk of email spoofing[/red]\n")
            if not email_config.has_dmarc:
                output.append(f"  [red]✗ Missing DMARC - no policy enforcement[/red]\n")
            if not email_config.has_dkim:
                output.append(
                    f"  [yellow]○ DKIM not found - message signing not verified[/yellow]\n"
                )

            if email_config.has_mx and email_config.has_spf and email_config.has_dmarc:
                if email_config.has_dkim:
                    output.append(
                        f"  [green]✓ All essential email authentication configured[/green]\n"
                    )
                else:
                    output.append(
                        f"  [green]✓ Core authentication configured[/green]\n"
                    )
                    output.append(
                        f"  [yellow]○ Consider adding DKIM for enhanced security[/yellow]\n"
                    )

            self.update("".join(output))

        except Exception as e:
            self.update(
                f"[red]Error: {str(e)}[/red]\n\n[dim]Make sure DNS tools are available[/dim]"
            )


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

    #app-loading {
        dock: top;
        height: auto;
        padding: 1;
        background: $surface;
    }

    #dashboard-header {
        padding: 0 0 1 0;
    }

    #dashboard-sections {
        height: 1fr;
        width: 100%;
    }

    #dashboard-sections > #health-registry {
        width: 40%;
        height: 100%;
        border: solid $primary;
        margin: 0 1 0 0;
        padding: 1 2;
    }

    #dashboard-right {
        width: 60%;
        height: 100%;
    }

    #dashboard-row-1,
    #dashboard-row-2 {
        height: 1fr;
        width: 100%;
    }

    #dashboard-row-1 HealthSection,
    #dashboard-row-2 HealthSection {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        margin: 0 0 0 1;
        padding: 1 2;
    }

    #dashboard-row-1 {
        margin: 0 0 1 0;
    }

    #dashboard-row-2 {
        margin: 0 0 1 0;
    }

    #dashboard-row-3 {
        height: 1fr;
        width: 100%;
    }

    #dashboard-row-3 HealthSection {
        width: 100%;
        height: 100%;
        border: solid $primary;
        margin: 0 0 0 1;
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", key_display="Q"),
        Binding("r", "refresh", "Refresh", key_display="R"),
        Binding("l", "show_raw", "Raw Logs", key_display="L"),
        Binding("h", "help", "Help", key_display="H/?"),
        ("question_mark", "help", "Help"),
        Binding("0", "switch_tab('dashboard')", "Dashboard", show=False),
        Binding("1", "switch_tab('registry')", "Registration", show=False),
        Binding("2", "switch_tab('dns')", "DNS", show=False),
        Binding("3", "switch_tab('dnssec')", "DNSSEC", show=False),
        Binding("4", "switch_tab('cert')", "Certificate", show=False),
        Binding("5", "switch_tab('http')", "HTTP", show=False),
        Binding("6", "switch_tab('email')", "Email", show=False),
    ]

    def __init__(self, domain: str, theme: str = "dark") -> None:
        super().__init__()
        self.domain = domain
        # Note: Textual uses CSS for theming, not a theme attribute
        self.title = domain
        self.sub_title = ""

        # Initialize state manager
        self.state_manager = StateManager()
        self.state_manager.initialize(domain)

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header(show_clock=False)
        yield LoadingIndicator(id="app-loading")

        with Container(id="main-container"):
            with TabbedContent(initial="dashboard"):
                with TabPane("Dashboard", id="dashboard"):
                    yield DashboardPanel(self.domain)

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

                with TabPane("Email", id="email"):
                    yield EmailPanel(self.domain)

        yield Footer()

    def on_mount(self) -> None:
        """App mounted - load all data into state."""
        # Show loading indicator
        loading = self.query_one("#app-loading", LoadingIndicator)
        loading.display = True

        # Hide main container while loading
        main_container = self.query_one("#main-container")
        main_container.display = False

        # Fetch all data
        self.run_worker(self.fetch_all_data(), exclusive=True)

    async def fetch_all_data(self) -> None:
        """Fetch all data from all ports and populate state."""
        try:
            # Fetch DNS data
            dns_adapter = DNSAdapterFactory.create()
            dns_responses = {}
            for record_type in [
                RecordType.A,
                RecordType.AAAA,
                RecordType.MX,
                RecordType.TXT,
                RecordType.NS,
            ]:
                response = dns_adapter.query(self.domain, record_type)
                dns_responses[record_type.value] = response
            self.state_manager.update_dns(dns_responses)

            # Fetch DNSSEC data
            validation = dns_adapter.validate_dnssec(self.domain)
            self.state_manager.update_dnssec(validation)

            # Fetch Certificate data
            from dns_debugger.adapters.cert.factory import CertificateAdapterFactory

            cert_adapter = CertificateAdapterFactory.create()
            tls_info = cert_adapter.get_certificate_info(self.domain)
            self.state_manager.update_tls(tls_info)

            # Fetch HTTP data
            http_adapter = HTTPAdapterFactory.create()
            https_response = http_adapter.check_url(f"https://{self.domain}")
            self.state_manager.update_http(https_response)

            # Fetch Registration data
            from dns_debugger.adapters.registry.factory import RegistryAdapterFactory

            registry_adapter = RegistryAdapterFactory.create()
            registration = registry_adapter.lookup(self.domain)
            self.state_manager.update_registration(registration)

            # Fetch Email data
            email_adapter = EmailAdapterFactory.create()
            email_config = email_adapter.get_email_config(self.domain)
            self.state_manager.update_email(email_config)

            # All data loaded - now render all panels
            self.call_later(self.render_all_panels)

        except Exception as e:
            self.notify(f"Error loading data: {str(e)}", severity="error")
        finally:
            # Hide loading indicator and show content
            loading = self.query_one("#app-loading", LoadingIndicator)
            loading.display = False
            main_container = self.query_one("#main-container")
            main_container.display = True

    def render_all_panels(self) -> None:
        """Render all panels from state data."""
        state = self.state_manager.state

        # Render dashboard
        dashboard_panel = self.query_one(DashboardPanel)
        dashboard_panel.render_from_state(state)

        # Render all detail panels
        dns_panel = self.query_one(DNSPanel)
        dns_panel.render_from_state(state)

        dnssec_panel = self.query_one(DNSSECPanel)
        dnssec_panel.render_from_state(state)

        cert_panel = self.query_one(CertificatePanel)
        cert_panel.render_from_state(state)

        http_panel = self.query_one(HTTPPanel)
        http_panel.render_from_state(state)

        registry_panel = self.query_one(RegistryPanel)
        registry_panel.render_from_state(state)

        email_panel = self.query_one(EmailPanel)
        email_panel.render_from_state(state)

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab by ID."""
        tabbed_content = self.query_one(TabbedContent)
        tabbed_content.active = tab_id

    def action_refresh(self) -> None:
        """Refresh all data by refetching from ports."""
        self.notify("Refreshing all data...", severity="information")
        # Refetch all data and re-render all panels
        self.run_worker(self.fetch_all_data(), exclusive=True)

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
        elif active_pane == "email":
            email_panel = self.query_one(EmailPanel)
            if email_panel.last_email_config:
                email_config = email_panel.last_email_config
                raw_data = {
                    "domain": email_config.domain,
                    "email_provider": email_config.email_provider,
                    "security_score": email_config.security_score,
                    "mx_records": [
                        {
                            "hostname": mx.hostname,
                            "priority": mx.priority,
                            "ip_addresses": mx.ip_addresses,
                        }
                        for mx in email_config.mx_records
                    ],
                    "spf_record": {
                        "domain": email_config.spf_record.domain,
                        "record": email_config.spf_record.record,
                        "mechanisms": email_config.spf_record.mechanisms,
                        "all_mechanism": email_config.spf_record.all_mechanism,
                        "is_strict": email_config.spf_record.is_strict,
                    }
                    if email_config.spf_record
                    else None,
                    "dkim_records": [
                        {
                            "selector": dkim.selector,
                            "domain": dkim.domain,
                            "exists": dkim.exists,
                            "public_key": dkim.public_key[:100] + "..."
                            if dkim.public_key and len(dkim.public_key) > 100
                            else dkim.public_key,
                        }
                        for dkim in email_config.dkim_records
                    ],
                    "dmarc_record": {
                        "domain": email_config.dmarc_record.domain,
                        "record": email_config.dmarc_record.record,
                        "policy": email_config.dmarc_record.policy.value,
                        "subdomain_policy": email_config.dmarc_record.subdomain_policy.value
                        if email_config.dmarc_record.subdomain_policy
                        else None,
                        "percentage": email_config.dmarc_record.percentage,
                        "dkim_alignment": email_config.dmarc_record.dkim_alignment,
                        "spf_alignment": email_config.dmarc_record.spf_alignment,
                        "aggregate_report_uri": email_config.dmarc_record.aggregate_report_uri,
                        "forensic_report_uri": email_config.dmarc_record.forensic_report_uri,
                        "is_enforcing": email_config.dmarc_record.is_enforcing,
                    }
                    if email_config.dmarc_record
                    else None,
                    "has_mx": email_config.has_mx,
                    "has_spf": email_config.has_spf,
                    "has_dkim": email_config.has_dkim,
                    "has_dmarc": email_config.has_dmarc,
                }
                title = f"Email Raw Data - {email_panel.domain}"

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
