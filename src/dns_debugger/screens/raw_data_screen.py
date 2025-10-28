"""Screen for displaying raw data/logs."""

import json
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Button


class RawDataScreen(ModalScreen):
    """Modal screen for displaying raw data in JSON or text format."""

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

    def __init__(self, title: str, data: dict | str) -> None:
        super().__init__()
        self.title_text = title
        self.raw_data = data

    def compose(self) -> ComposeResult:
        """Create the modal dialog."""
        with Container(id="raw-dialog"):
            yield Static(f"Raw Data: {self.title_text}", id="raw-header")

            with VerticalScroll(id="raw-content"):
                # Format the data
                if isinstance(self.raw_data, dict):
                    formatted = json.dumps(self.raw_data, indent=2, default=str)
                else:
                    formatted = str(self.raw_data)

                yield Static(formatted, id="raw-text")

            with Container(id="raw-footer"):
                yield Button("Close (Esc)", variant="primary", id="close-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        self.dismiss()

    def on_key(self, event) -> None:
        """Handle key press."""
        if event.key == "escape":
            self.dismiss()
