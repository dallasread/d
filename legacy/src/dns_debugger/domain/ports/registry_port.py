"""Port interface for domain registry lookup operations."""

from abc import ABC, abstractmethod
from typing import Optional

from dns_debugger.domain.models.domain_info import DomainRegistration


class RegistryPort(ABC):
    """Abstract interface for domain registration lookup operations.

    This port defines the contract that registry adapters (RDAP, WHOIS) must implement.
    Following hexagonal architecture, this allows the domain logic to be independent
    of the specific registry lookup tool being used.
    """

    @abstractmethod
    def lookup(self, domain: str) -> DomainRegistration:
        """Look up domain registration information.

        Args:
            domain: The domain name to look up

        Returns:
            DomainRegistration containing the registration details

        Raises:
            RegistryLookupError: If the lookup fails
        """
        pass

    @abstractmethod
    def lookup_ip(self, ip_address: str) -> DomainRegistration:
        """Look up IP address registration information.

        Args:
            ip_address: The IP address to look up

        Returns:
            DomainRegistration containing the IP registration details

        Raises:
            RegistryLookupError: If the lookup fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this registry lookup method is available.

        Returns:
            True if the method is available, False otherwise
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of the registry source.

        Returns:
            Name of the source (e.g., "RDAP", "WHOIS")
        """
        pass

    @abstractmethod
    def supports_domain(self, domain: str) -> bool:
        """Check if this adapter supports looking up the given domain.

        Some adapters may only support certain TLDs or domain formats.

        Args:
            domain: The domain name to check

        Returns:
            True if this adapter can look up the domain, False otherwise
        """
        pass
