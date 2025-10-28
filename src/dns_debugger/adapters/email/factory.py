"""Factory for creating email adapters."""

from dns_debugger.domain.ports.email_port import EmailPort
from dns_debugger.adapters.email.dns_email_adapter import DNSEmailAdapter


class EmailAdapterFactory:
    """Factory for creating email adapters."""

    @staticmethod
    def create() -> EmailPort:
        """Create an email adapter using DNS.

        Returns:
            An EmailPort implementation (DNSEmailAdapter)
        """
        return DNSEmailAdapter()
