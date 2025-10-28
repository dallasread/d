"""Port interface for SSL/TLS certificate operations."""

from abc import ABC, abstractmethod
from typing import Optional

from dns_debugger.domain.models.certificate import (
    TLSInfo,
    Certificate,
    CertificateChain,
)


class CertificatePort(ABC):
    """Abstract interface for SSL/TLS certificate operations.

    This port defines the contract that certificate adapters must implement.
    Following hexagonal architecture, this allows the domain logic to be independent
    of the specific certificate inspection tool being used.
    """

    @abstractmethod
    def get_certificate_info(
        self, host: str, port: int = 443, servername: Optional[str] = None
    ) -> TLSInfo:
        """Get SSL/TLS certificate information for a host.

        Args:
            host: The hostname to connect to
            port: The port to connect on (default: 443)
            servername: Optional SNI servername (defaults to host)

        Returns:
            TLSInfo containing certificate and connection details

        Raises:
            CertificateError: If certificate retrieval fails
        """
        pass

    @abstractmethod
    def get_certificate_chain(
        self, host: str, port: int = 443, servername: Optional[str] = None
    ) -> tuple[CertificateChain, str]:
        """Get the full certificate chain for a host.

        Args:
            host: The hostname to connect to
            port: The port to connect on (default: 443)
            servername: Optional SNI servername

        Returns:
            CertificateChain with all certificates in the chain

        Raises:
            CertificateError: If chain retrieval fails
        """
        pass

    @abstractmethod
    def verify_certificate(
        self, host: str, port: int = 443, servername: Optional[str] = None
    ) -> tuple[bool, list[str]]:
        """Verify the certificate and chain for a host.

        Args:
            host: The hostname to connect to
            port: The port to connect on (default: 443)
            servername: Optional SNI servername

        Returns:
            Tuple of (is_valid, list of validation errors/warnings)
        """
        pass

    @abstractmethod
    def check_ocsp_stapling(self, host: str, port: int = 443) -> bool:
        """Check if OCSP stapling is enabled.

        Args:
            host: The hostname to connect to
            port: The port to connect on (default: 443)

        Returns:
            True if OCSP stapling is enabled, False otherwise
        """
        pass

    @abstractmethod
    def get_supported_cipher_suites(self, host: str, port: int = 443) -> list[str]:
        """Get the list of supported cipher suites.

        Args:
            host: The hostname to connect to
            port: The port to connect on (default: 443)

        Returns:
            List of supported cipher suite names
        """
        pass

    @abstractmethod
    def export_certificate_pem(self, certificate: Certificate) -> str:
        """Export a certificate in PEM format.

        Args:
            certificate: The certificate to export

        Returns:
            PEM-encoded certificate string
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this certificate tool is available.

        Returns:
            True if the tool is available, False otherwise
        """
        pass

    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the certificate tool.

        Returns:
            Name of the tool (e.g., "openssl", "cryptography")
        """
        pass
