"""Main entry point for the DNS Debugger application."""

import sys
import click


@click.command()
@click.argument("domain", required=True)
@click.option(
    "--theme", default="dark", help="UI theme (dark, light, monokai, solarized)"
)
@click.option("--no-tui", is_flag=True, help="Disable TUI and use CLI mode")
@click.version_option(version="0.1.0", prog_name="d")
def main(domain: str, theme: str, no_tui: bool) -> None:
    """DNS Debugger - Interactive TUI for debugging DNS, certificates, and domain registration.

    Usage: d DOMAIN

    Example: d example.com
    """
    # Validate domain
    if not domain:
        click.echo("❌ Domain is required")
        sys.exit(1)

    # Check if DNS tools are available
    try:
        from dns_debugger.adapters.dns.factory import DNSAdapterFactory

        available_tools = DNSAdapterFactory.get_available_tools()
        if not available_tools:
            click.echo("❌ No DNS tools available. Please install 'dog' or 'dig'.")
            click.echo("   • dog: https://dns.lookup.dog/")
            click.echo("   • dig: Usually available via bind-tools or dnsutils package")
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error checking DNS tools: {str(e)}")
        sys.exit(1)

    # Launch TUI or CLI mode
    if no_tui:
        # CLI mode (for testing or scripting)
        run_cli_mode(domain)
    else:
        # TUI mode (default)
        try:
            from dns_debugger.app import run_tui

            run_tui(domain, theme)
        except Exception as e:
            click.echo(f"❌ Error launching TUI: {str(e)}")
            click.echo("   Try using --no-tui flag for CLI mode")
            sys.exit(1)


def run_cli_mode(domain: str) -> None:
    """Run in CLI mode (non-interactive)."""
    from dns_debugger.adapters.dns.factory import DNSAdapterFactory
    from dns_debugger.domain.models.dns_record import RecordType

    click.echo(f"🚀 DNS Debugger (CLI mode) - {domain}")
    click.echo()

    try:
        # Show available DNS tools
        available_tools = DNSAdapterFactory.get_available_tools()
        preferred_tool = DNSAdapterFactory.get_preferred_tool()

        click.echo(f"✓ Available DNS tools: {', '.join(available_tools)}")
        click.echo(f"✓ Using: {preferred_tool}")
        click.echo()

        # Create DNS adapter
        dns_adapter = DNSAdapterFactory.create()

        # Query A record
        click.echo(f"Querying A records for {domain}...")
        response = dns_adapter.query(domain, RecordType.A)

        if response.is_success:
            click.echo(f"✓ Query completed in {response.query_time_ms:.2f}ms")
            click.echo(f"✓ Found {response.record_count} record(s)")
            click.echo()
            for record in response.records:
                click.echo(f"  {record}")
        else:
            click.echo(f"❌ Query failed: {response.error}")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
