"""Factory for creating HTTP adapters with automatic fallback."""

from typing import Optional

from dns_debugger.domain.ports.http_port import HTTPPort
from dns_debugger.adapters.http.curl_adapter import CurlAdapter
from dns_debugger.adapters.http.wget_adapter import WgetAdapter


class HTTPAdapterFactory:
    """Factory for creating HTTP adapters.

    Automatically selects the best available HTTP tool:
    1. curl (preferred - more features, better output parsing)
    2. wget (fallback - universally available)
    """

    @staticmethod
    def create() -> HTTPPort:
        """Create an HTTP adapter using the best available tool.

        Returns:
            An HTTPPort implementation (CurlAdapter or WgetAdapter)

        Raises:
            RuntimeError: If no HTTP tool is available
        """
        # Try curl first (preferred)
        curl = CurlAdapter()
        if curl.is_available():
            return curl

        # Fall back to wget
        wget = WgetAdapter()
        if wget.is_available():
            return wget

        # No HTTP tool available
        raise RuntimeError(
            "No HTTP tool available. Please install 'curl' or 'wget'.\n"
            "  - curl (preferred): Usually pre-installed on macOS/Linux\n"
            "  - wget (fallback): brew install wget / apt-get install wget"
        )

    @staticmethod
    def create_specific(tool_name: str) -> HTTPPort:
        """Create a specific HTTP adapter by name.

        Args:
            tool_name: Name of the tool ("curl" or "wget")

        Returns:
            The requested HTTPPort implementation

        Raises:
            ValueError: If tool_name is not recognized
            RuntimeError: If the requested tool is not available
        """
        if tool_name.lower() == "curl":
            adapter = CurlAdapter()
        elif tool_name.lower() == "wget":
            adapter = WgetAdapter()
        else:
            raise ValueError(f"Unknown HTTP tool: {tool_name}")

        if not adapter.is_available():
            raise RuntimeError(
                f"HTTP tool '{tool_name}' is not available on this system"
            )

        return adapter

    @staticmethod
    def get_available_tools() -> list[str]:
        """Get a list of available HTTP tools on the system.

        Returns:
            List of tool names that are available
        """
        tools = []

        curl = CurlAdapter()
        if curl.is_available():
            tools.append("curl")

        wget = WgetAdapter()
        if wget.is_available():
            tools.append("wget")

        return tools

    @staticmethod
    def get_preferred_tool() -> Optional[str]:
        """Get the name of the preferred tool that will be used.

        Returns:
            Name of the preferred tool, or None if no tool is available
        """
        tools = HTTPAdapterFactory.get_available_tools()
        return tools[0] if tools else None
