"""Port interface for export operations."""

from abc import ABC, abstractmethod
from typing import Any


class ExportPort(ABC):
    """Abstract interface for data export operations.

    This port defines the contract that export adapters (JSON, CSV, text) must implement.
    """

    @abstractmethod
    def export(self, data: Any, output_path: str) -> None:
        """Export data to a file.

        Args:
            data: The data to export (can be any domain model)
            output_path: Path to the output file

        Raises:
            ExportError: If export fails
        """
        pass

    @abstractmethod
    def export_to_string(self, data: Any) -> str:
        """Export data to a string.

        Args:
            data: The data to export

        Returns:
            Formatted string representation of the data
        """
        pass

    @abstractmethod
    def get_format_name(self) -> str:
        """Get the name of the export format.

        Returns:
            Name of the format (e.g., "JSON", "CSV", "Text")
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this format.

        Returns:
            File extension without the dot (e.g., "json", "csv", "txt")
        """
        pass

    @abstractmethod
    def supports_type(self, data_type: type) -> bool:
        """Check if this exporter supports the given data type.

        Args:
            data_type: The type to check

        Returns:
            True if this exporter can handle the type, False otherwise
        """
        pass
