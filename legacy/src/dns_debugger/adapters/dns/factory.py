"""Factory for creating DNS adapters."""

from typing import Optional

from dns_debugger.domain.ports.dns_port import DNSPort
from dns_debugger.adapters.dns.dig_adapter import DigAdapter


class DNSAdapterFactory:
    """Factory for creating DNS adapters.

    Uses dig (BIND DNS tools) for all DNS queries.
    """

    @staticmethod
    def create() -> DNSPort:
        """Create a DNS adapter using dig.

        Returns:
            A DNSPort implementation (DigAdapter)

        Raises:
            RuntimeError: If dig is not available
        """
        dig = DigAdapter()
        if dig.is_available():
            return dig

        # No DNS tool available
        raise RuntimeError(
            "dig is not available. Please install BIND DNS tools.\n"
            "  - macOS: brew install bind\n"
            "  - Ubuntu/Debian: apt-get install dnsutils\n"
            "  - RHEL/Fedora: dnf install bind-utils"
        )

    @staticmethod
    def create_specific(tool_name: str) -> DNSPort:
        """Create a specific DNS adapter by name.

        Args:
            tool_name: Name of the tool ("dig")

        Returns:
            The requested DNSPort implementation

        Raises:
            ValueError: If tool_name is not recognized
            RuntimeError: If the requested tool is not available
        """
        if tool_name.lower() == "dig":
            adapter = DigAdapter()
        else:
            raise ValueError(f"Unknown DNS tool: {tool_name}. Only 'dig' is supported.")

        if not adapter.is_available():
            raise RuntimeError(
                f"DNS tool '{tool_name}' is not available on this system"
            )

        return adapter

    @staticmethod
    def get_available_tools() -> list[str]:
        """Get a list of available DNS tools on the system.

        Returns:
            List of tool names that are available
        """
        tools = []

        dig = DigAdapter()
        if dig.is_available():
            tools.append("dig")

        return tools

    @staticmethod
    def get_preferred_tool() -> Optional[str]:
        """Get the name of the preferred tool that will be used.

        Returns:
            Name of the preferred tool, or None if no tool is available
        """
        dig = DigAdapter()
        return "dig" if dig.is_available() else None
