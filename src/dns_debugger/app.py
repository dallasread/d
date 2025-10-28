"""Main Textual application for DNS Debugger."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, TabbedContent, TabPane, Label

from dns_debugger.adapters.dns.factory import DNSAdapterFactory
from dns_debugger.domain.models.dns_record import RecordType


class DNSPanel(Static):
    """Panel for displaying DNS information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain
        self.dns_adapter = None

    def on_mount(self) -> None:
        """Load DNS data when the panel is mounted."""
        self.update_dns_info()

    def update_dns_info(self) -> None:
        """Query and display DNS information."""
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

        except Exception as e:
            self.update(f"[red]Error: {str(e)}[/red]")


class CertificatePanel(Static):
    """Panel for displaying certificate information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain

    def on_mount(self) -> None:
        """Load certificate data when the panel is mounted."""
        self.update(f"[bold cyan]SSL/TLS Certificate for {self.domain}[/bold cyan]\n\n")
        self.update("[yellow]Certificate checking coming soon...[/yellow]\n")
        self.update("Will show:\n")
        self.update("  • Certificate details (subject, issuer)\n")
        self.update("  • Validity dates\n")
        self.update("  • Certificate chain\n")
        self.update("  • Supported TLS versions\n")
        self.update("  • Cipher suites\n")


class RegistryPanel(Static):
    """Panel for displaying domain registration information."""

    def __init__(self, domain: str) -> None:
        super().__init__()
        self.domain = domain

    def on_mount(self) -> None:
        """Load registry data when the panel is mounted."""
        self.update(f"[bold cyan]Domain Registration for {self.domain}[/bold cyan]\n\n")
        self.update("[yellow]RDAP/WHOIS lookup coming soon...[/yellow]\n")
        self.update("Will show:\n")
        self.update("  • Registrar information\n")
        self.update("  • Registration dates\n")
        self.update("  • Expiration date\n")
        self.update("  • Nameservers\n")
        self.update("  • Contact information\n")


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
        Binding("h", "help", "Help", key_display="H/?"),
        ("question_mark", "help", "Help"),
    ]

    def __init__(self, domain: str, theme: str = "dark") -> None:
        super().__init__()
        self.domain = domain
        # Note: Textual uses CSS for theming, not a theme attribute
        self.title = f"DNS Debugger - {domain}"
        self.sub_title = "Interactive DNS, Certificate, and Registry Inspector"

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header(show_clock=True)

        with Container(id="main-container"):
            with TabbedContent(initial="dns"):
                with TabPane("DNS", id="dns"):
                    yield DNSPanel(self.domain)

                with TabPane("Certificate", id="cert"):
                    yield CertificatePanel(self.domain)

                with TabPane("Registration", id="registry"):
                    yield RegistryPanel(self.domain)

                with TabPane("About", id="about"):
                    yield Static(
                        "[bold cyan]DNS Debugger[/bold cyan]\n\n"
                        "A powerful TUI for debugging:\n"
                        "  • DNS records and resolution\n"
                        "  • SSL/TLS certificates\n"
                        "  • Domain registration (RDAP/WHOIS)\n\n"
                        "[bold]Keyboard Shortcuts:[/bold]\n"
                        "  Q - Quit\n"
                        "  R - Refresh current view\n"
                        "  H/? - Show help\n"
                        "  Tab - Switch between panels\n\n"
                        "[bold]Architecture:[/bold]\n"
                        "  Uses hexagonal architecture with adapters\n"
                        "  • DNS: dog (preferred) → dig (fallback)\n"
                        "  • Registry: RDAP (preferred) → WHOIS (fallback)\n"
                        "  • Certificates: OpenSSL / cryptography\n\n"
                        "[dim]Version 0.1.0[/dim]"
                    )

        yield Footer()

    def action_refresh(self) -> None:
        """Refresh the current view."""
        # Get the active tab
        tabbed_content = self.query_one(TabbedContent)
        active_pane = tabbed_content.active

        # Refresh the content in the active pane
        if active_pane == "dns":
            dns_panel = self.query_one(DNSPanel)
            dns_panel.update_dns_info()

        self.notify("Refreshed!", severity="information")

    def action_help(self) -> None:
        """Show help information."""
        # Switch to the About tab which has help info
        tabbed_content = self.query_one(TabbedContent)
        tabbed_content.active = "about"
        self.notify("Showing help", severity="information")

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
