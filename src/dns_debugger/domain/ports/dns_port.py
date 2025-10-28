"""Port interface for DNS query operations."""

from abc import ABC, abstractmethod
from typing import Optional

from dns_debugger.domain.models.dns_record import DNSQuery, DNSResponse, RecordType


class DNSPort(ABC):
    """Abstract interface for DNS query operations.

    This port defines the contract that DNS adapters (dog, dig, etc.) must implement.
    Following hexagonal architecture, this allows the domain logic to be independent
    of the specific DNS tool being used.
    """

    @abstractmethod
    def query(
        self, domain: str, record_type: RecordType, resolver: Optional[str] = None
    ) -> DNSResponse:
        """Execute a DNS query.

        Args:
            domain: The domain name to query
            record_type: The type of DNS record to query
            resolver: Optional DNS resolver to use (e.g., "8.8.8.8")

        Returns:
            DNSResponse containing the query results

        Raises:
            DNSQueryError: If the query fails
        """
        pass

    @abstractmethod
    def query_multiple_types(
        self,
        domain: str,
        record_types: list[RecordType],
        resolver: Optional[str] = None,
    ) -> dict[RecordType, DNSResponse]:
        """Execute multiple DNS queries for different record types.

        Args:
            domain: The domain name to query
            record_types: List of record types to query
            resolver: Optional DNS resolver to use

        Returns:
            Dictionary mapping record types to their responses
        """
        pass

    @abstractmethod
    def reverse_lookup(self, ip_address: str) -> DNSResponse:
        """Perform a reverse DNS lookup (PTR record).

        Args:
            ip_address: The IP address to look up

        Returns:
            DNSResponse containing the PTR record(s)

        Raises:
            DNSQueryError: If the lookup fails
        """
        pass

    @abstractmethod
    def trace(self, domain: str) -> list[DNSResponse]:
        """Trace the DNS resolution path from root servers.

        Args:
            domain: The domain name to trace

        Returns:
            List of DNSResponse objects representing each step in the resolution
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this DNS tool is available on the system.

        Returns:
            True if the tool is installed and available, False otherwise
        """
        pass

    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the DNS tool this adapter uses.

        Returns:
            Name of the tool (e.g., "dog", "dig")
        """
        pass

    @abstractmethod
    def get_version(self) -> Optional[str]:
        """Get the version of the DNS tool.

        Returns:
            Version string, or None if version cannot be determined
        """
        pass
