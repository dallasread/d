"""Port interface for email configuration operations."""

from abc import ABC, abstractmethod
from typing import Optional

from dns_debugger.domain.models.email_info import EmailConfiguration


class EmailPort(ABC):
    """Abstract interface for email configuration operations.

    This port defines the contract for retrieving and analyzing
    email-related DNS records (MX, SPF, DMARC, DKIM).
    """

    @abstractmethod
    def get_email_config(self, domain: str) -> EmailConfiguration:
        """Get complete email configuration for a domain.

        Args:
            domain: The domain name to query

        Returns:
            EmailConfiguration containing MX, SPF, DMARC, and DKIM info

        Raises:
            EmailConfigError: If the query fails
        """
        pass

    @abstractmethod
    def check_dkim(self, domain: str, selector: str) -> bool:
        """Check if a specific DKIM selector exists.

        Args:
            domain: The domain name
            selector: The DKIM selector to check

        Returns:
            True if DKIM record exists for this selector
        """
        pass

    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the DNS tool this adapter uses.

        Returns:
            Name of the tool (e.g., "dog", "dig")
        """
        pass
