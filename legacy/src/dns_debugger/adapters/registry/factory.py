"""Factory for creating registry adapters with automatic fallback."""

from typing import Optional

from dns_debugger.domain.ports.registry_port import RegistryPort
from dns_debugger.adapters.registry.whois_bash_adapter import WHOISBashAdapter


class RegistryAdapterFactory:
    """Factory for creating registry adapters.

    Uses bash whois command exclusively - no Python packages required.
    """

    @staticmethod
    def create() -> RegistryPort:
        """Create a registry adapter using the bash whois command.

        Returns:
            WHOISBashAdapter using the system whois command

        Raises:
            RuntimeError: If whois command is not available
        """
        # Use bash whois command
        whois_bash = WHOISBashAdapter()
        if whois_bash.is_available():
            return whois_bash

        # No registry lookup method available
        raise RuntimeError(
            "whois command not found. Please install whois.\n"
            "  - macOS: brew install whois\n"
            "  - Ubuntu/Debian: apt-get install whois\n"
            "  - RHEL/Fedora: dnf install whois"
        )

    @staticmethod
    def create_specific(method_name: str) -> RegistryPort:
        """Create a specific registry adapter by name.

        Args:
            method_name: Name of the method ("whois")

        Returns:
            The requested RegistryPort implementation

        Raises:
            ValueError: If method_name is not recognized
            RuntimeError: If the requested method is not available
        """
        if method_name.lower() == "whois":
            adapter = WHOISBashAdapter()
        else:
            raise ValueError(
                f"Unknown registry method: {method_name}. Only 'whois' is supported."
            )

        if not adapter.is_available():
            raise RuntimeError(f"Registry method '{method_name}' is not available")

        return adapter

    @staticmethod
    def get_available_methods() -> list[str]:
        """Get a list of available registry lookup methods.

        Returns:
            List of method names that are available
        """
        methods = []

        whois_bash = WHOISBashAdapter()
        if whois_bash.is_available():
            methods.append("whois")

        return methods

    @staticmethod
    def get_preferred_method() -> Optional[str]:
        """Get the name of the preferred method that will be used.

        Returns:
            Name of the preferred method, or None if no method is available
        """
        methods = RegistryAdapterFactory.get_available_methods()
        return methods[0] if methods else None
