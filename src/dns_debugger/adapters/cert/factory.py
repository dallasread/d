"""Factory for creating certificate adapters."""

from typing import Optional

from dns_debugger.domain.ports.cert_port import CertificatePort
from dns_debugger.adapters.cert.openssl_adapter import OpenSSLAdapter


class CertificateAdapterFactory:
    """Factory for creating certificate adapters.

    Currently only supports OpenSSL adapter.
    Future: Add cryptography library fallback.
    """

    @staticmethod
    def create() -> CertificatePort:
        """Create a certificate adapter using the best available tool.

        Returns:
            A CertificatePort implementation (OpenSSLAdapter)

        Raises:
            RuntimeError: If no certificate tool is available
        """
        # Try OpenSSL
        openssl = OpenSSLAdapter()
        if openssl.is_available():
            return openssl

        # No certificate tool available
        raise RuntimeError(
            "No certificate inspection tool available. Please install OpenSSL.\n"
            "  - macOS: brew install openssl\n"
            "  - Ubuntu/Debian: apt-get install openssl\n"
            "  - RHEL/Fedora: dnf install openssl"
        )

    @staticmethod
    def create_specific(tool_name: str) -> CertificatePort:
        """Create a specific certificate adapter by name.

        Args:
            tool_name: Name of the tool ("openssl")

        Returns:
            The requested CertificatePort implementation

        Raises:
            ValueError: If tool_name is not recognized
            RuntimeError: If the requested tool is not available
        """
        if tool_name.lower() == "openssl":
            adapter = OpenSSLAdapter()
        else:
            raise ValueError(f"Unknown certificate tool: {tool_name}")

        if not adapter.is_available():
            raise RuntimeError(f"Certificate tool '{tool_name}' is not available")

        return adapter

    @staticmethod
    def get_available_tools() -> list[str]:
        """Get a list of available certificate tools.

        Returns:
            List of tool names that are available
        """
        tools = []

        openssl = OpenSSLAdapter()
        if openssl.is_available():
            tools.append("openssl")

        return tools

    @staticmethod
    def get_preferred_tool() -> Optional[str]:
        """Get the name of the preferred tool that will be used.

        Returns:
            Name of the preferred tool, or None if no tool is available
        """
        tools = CertificateAdapterFactory.get_available_tools()
        return tools[0] if tools else None
