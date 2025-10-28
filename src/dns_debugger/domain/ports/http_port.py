"""Port interface for HTTP/HTTPS operations."""

from abc import ABC, abstractmethod
from typing import Optional

from dns_debugger.domain.models.http_info import HTTPResponse, HTTPMethod


class HTTPPort(ABC):
    """Abstract interface for HTTP/HTTPS request operations.

    This port defines the contract that HTTP adapters (curl, wget) must implement.
    Following hexagonal architecture, this allows the domain logic to be independent
    of the specific HTTP tool being used.
    """

    @abstractmethod
    def request(
        self,
        url: str,
        method: HTTPMethod = HTTPMethod.HEAD,
        follow_redirects: bool = True,
        timeout: int = 10,
    ) -> HTTPResponse:
        """Execute an HTTP/HTTPS request.

        Args:
            url: The URL to request
            method: HTTP method (default: HEAD to minimize data transfer)
            follow_redirects: Whether to follow redirects
            timeout: Request timeout in seconds

        Returns:
            HTTPResponse containing status, headers, and redirect chain

        Raises:
            HTTPError: If the request fails
        """
        pass

    @abstractmethod
    def check_url(self, url: str) -> HTTPResponse:
        """Quick check if a URL is accessible.

        Uses HEAD request by default for efficiency.

        Args:
            url: The URL to check

        Returns:
            HTTPResponse with status and timing information
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this HTTP tool is available on the system.

        Returns:
            True if the tool is installed and available, False otherwise
        """
        pass

    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the HTTP tool this adapter uses.

        Returns:
            Name of the tool (e.g., "curl", "wget")
        """
        pass

    @abstractmethod
    def get_version(self) -> Optional[str]:
        """Get the version of the HTTP tool.

        Returns:
            Version string, or None if version cannot be determined
        """
        pass
