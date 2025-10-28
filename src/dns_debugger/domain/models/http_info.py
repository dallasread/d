"""Domain models for HTTP/HTTPS information."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class HTTPMethod(Enum):
    """HTTP request methods."""

    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"


@dataclass
class HTTPRedirect:
    """Represents a single redirect in a chain."""

    from_url: str
    to_url: str
    status_code: int
    location_header: str


@dataclass
class HTTPResponse:
    """Represents an HTTP/HTTPS response."""

    url: str
    final_url: str
    status_code: int
    status_text: str
    response_time_ms: float
    redirect_chain: list[HTTPRedirect]
    headers: dict[str, str]
    content_length: Optional[int]
    content_type: Optional[str]
    server: Optional[str]
    timestamp: datetime
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if request was successful."""
        return self.error is None and 200 <= self.status_code < 300

    @property
    def is_redirect(self) -> bool:
        """Check if response is a redirect."""
        return 300 <= self.status_code < 400

    @property
    def is_client_error(self) -> bool:
        """Check if response is a client error."""
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        """Check if response is a server error."""
        return 500 <= self.status_code < 600

    @property
    def redirect_count(self) -> int:
        """Get the number of redirects."""
        return len(self.redirect_chain)

    @property
    def was_redirected(self) -> bool:
        """Check if the request was redirected."""
        return len(self.redirect_chain) > 0
