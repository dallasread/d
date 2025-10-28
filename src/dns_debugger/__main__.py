"""Main entry point for the DNS Debugger application."""

import sys
import click


@click.command()
@click.argument("domain", required=True)
@click.option(
    "--theme", default="dark", help="UI theme (dark, light, monokai, solarized)"
)
@click.version_option(version="0.1.0", prog_name="d")
def main(domain: str, theme: str) -> None:
    """DNS Debugger - Interactive TUI for debugging DNS, certificates, and domain registration.

    Usage: d DOMAIN

    Example: d example.com
    """
    click.echo(f"🚀 DNS Debugger starting for domain: {domain}")
    click.echo(f"Theme: {theme}")
    click.echo()
    click.echo("⚠️  TUI interface coming soon!")
    click.echo()
    click.echo("For now, testing the DNS adapter:")

    try:
        from dns_debugger.adapters.dns.factory import DNSAdapterFactory
        from dns_debugger.domain.models.dns_record import RecordType

        # Show available DNS tools
        available_tools = DNSAdapterFactory.get_available_tools()
        preferred_tool = DNSAdapterFactory.get_preferred_tool()

        if not available_tools:
            click.echo("❌ No DNS tools available. Please install 'dog' or 'dig'.")
            sys.exit(1)

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
