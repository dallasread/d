"""Factory for creating registry adapters with automatic fallback."""

from typing import Optional

from dns_debugger.domain.ports.registry_port import RegistryPort
from dns_debugger.adapters.registry.rdap_adapter import RDAPAdapter
from dns_debugger.adapters.registry.whois_adapter import WHOISAdapter


class RegistryAdapterFactory:
    """Factory for creating registry adapters.

    Automatically selects the best available registry lookup method:
    1. RDAP (preferred - structured JSON data)
    2. WHOIS (fallback - text-based data)
    """

    @staticmethod
    def create() -> RegistryPort:
        """Create a registry adapter using the best available method.

        Returns:
            A RegistryPort implementation (RDAPAdapter or WHOISAdapter)

        Raises:
            RuntimeError: If no registry lookup method is available
        """
        # Try RDAP first (preferred)
        rdap = RDAPAdapter()
        if rdap.is_available():
            return rdap

        # Fall back to WHOIS
        whois_adapter = WHOISAdapter()
        if whois_adapter.is_available():
            return whois_adapter

        # No registry lookup method available
        raise RuntimeError(
            "No registry lookup method available. Please install 'whodap' or 'python-whois'.\n"
            "  - RDAP (preferred): pip install whodap\n"
            "  - WHOIS (fallback): pip install python-whois"
        )

    @staticmethod
    def create_specific(method_name: str) -> RegistryPort:
        """Create a specific registry adapter by name.

        Args:
            method_name: Name of the method ("rdap" or "whois")

        Returns:
            The requested RegistryPort implementation

        Raises:
            ValueError: If method_name is not recognized
            RuntimeError: If the requested method is not available
        """
        if method_name.lower() == "rdap":
            adapter = RDAPAdapter()
        elif method_name.lower() == "whois":
            adapter = WHOISAdapter()
        else:
            raise ValueError(f"Unknown registry method: {method_name}")

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

        rdap = RDAPAdapter()
        if rdap.is_available():
            methods.append("rdap")

        whois_adapter = WHOISAdapter()
        if whois_adapter.is_available():
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
