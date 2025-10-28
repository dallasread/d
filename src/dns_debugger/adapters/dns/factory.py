"""Factory for creating DNS adapters with automatic fallback."""

from typing import Optional

from dns_debugger.domain.ports.dns_port import DNSPort
from dns_debugger.adapters.dns.dog_adapter import DogAdapter
from dns_debugger.adapters.dns.dig_adapter import DigAdapter


class DNSAdapterFactory:
    """Factory for creating DNS adapters.

    Automatically selects the best available DNS tool:
    1. dog (preferred - modern, JSON output)
    2. dig (fallback - traditional, always available)
    """

    @staticmethod
    def create() -> DNSPort:
        """Create a DNS adapter using the best available tool.

        Returns:
            A DNSPort implementation (DogAdapter or DigAdapter)

        Raises:
            RuntimeError: If no DNS tool is available
        """
        # Try dog first (preferred)
        dog = DogAdapter()
        if dog.is_available():
            return dog

        # Fall back to dig
        dig = DigAdapter()
        if dig.is_available():
            return dig

        # No DNS tool available
        raise RuntimeError(
            "No DNS tool available. Please install 'dog' or 'dig'.\n"
            "  - dog: https://dns.lookup.dog/\n"
            "  - dig: Usually available via bind-tools or dnsutils package"
        )

    @staticmethod
    def create_specific(tool_name: str) -> DNSPort:
        """Create a specific DNS adapter by name.

        Args:
            tool_name: Name of the tool ("dog" or "dig")

        Returns:
            The requested DNSPort implementation

        Raises:
            ValueError: If tool_name is not recognized
            RuntimeError: If the requested tool is not available
        """
        if tool_name.lower() == "dog":
            adapter = DogAdapter()
        elif tool_name.lower() == "dig":
            adapter = DigAdapter()
        else:
            raise ValueError(f"Unknown DNS tool: {tool_name}")

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

        dog = DogAdapter()
        if dog.is_available():
            tools.append("dog")

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
        tools = DNSAdapterFactory.get_available_tools()
        return tools[0] if tools else None
