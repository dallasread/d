"""Screen for displaying raw data/logs."""

import json
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, Button


class RawDataScreen(ModalScreen):
    """Modal screen for displaying raw data in JSON or raw tool output format."""

    CSS = """
    RawDataScreen {
        align: center middle;
    }

    #raw-dialog {
        width: 90%;
        height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    #raw-header {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        content-align: center middle;
        text-style: bold;
    }

    #raw-content {
        height: 1fr;
        border: solid $primary;
        background: $surface-darken-1;
        padding: 1;
        overflow-y: scroll;
    }

    #raw-footer {
        dock: bottom;
        height: 3;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, title: str, data: dict | str, raw_output: str = None) -> None:
        """Initialize raw data screen.

        Args:
            title: Title for the modal
            data: JSON data (dict) or text data (str)
            raw_output: Optional raw tool output (e.g., whois output, dig output)
        """
        super().__init__()
        self.title_text = title
        self.json_data = data
        self.raw_output = raw_output
        self.show_json = True  # Start with JSON view

    def compose(self) -> ComposeResult:
        """Create the modal dialog."""
        with Container(id="raw-dialog"):
            yield Static(f"Raw Data: {self.title_text}", id="raw-header")

            with VerticalScroll(id="raw-content"):
                yield Static(self._get_formatted_content(), id="raw-text")

            with Container(id="raw-footer"):
                with Horizontal():
                    if self.raw_output:
                        yield Button(
                            "Toggle JSON/Raw (T)", variant="default", id="toggle-button"
                        )
                    yield Button("Close (Esc)", variant="primary", id="close-button")

    def _get_formatted_content(self) -> str:
        """Get formatted content based on current view mode."""
        if self.show_json:
            # Show JSON view
            if isinstance(self.json_data, dict):
                return json.dumps(self.json_data, indent=2, default=str)
            else:
                return str(self.json_data)
        else:
            # Show raw tool output
            if self.raw_output:
                return self.raw_output
            else:
                return "[dim]No raw tool output available[/dim]"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "toggle-button":
            self.show_json = not self.show_json
            # Update the content
            raw_text = self.query_one("#raw-text", Static)
            raw_text.update(self._get_formatted_content())
            # Update header to show current mode
            header = self.query_one("#raw-header", Static)
            mode = "JSON" if self.show_json else "Raw Tool Output"
            header.update(f"Raw Data: {self.title_text} [{mode}]")
        elif event.button.id == "close-button":
            self.dismiss()

    def on_key(self, event) -> None:
        """Handle key press."""
        if event.key == "escape":
            self.dismiss()
        elif event.key == "t" and self.raw_output:
            # Toggle with T key
            self.show_json = not self.show_json
            raw_text = self.query_one("#raw-text", Static)
            raw_text.update(self._get_formatted_content())
            header = self.query_one("#raw-header", Static)
            mode = "JSON" if self.show_json else "Raw Tool Output"
            header.update(f"Raw Data: {self.title_text} [{mode}]")
