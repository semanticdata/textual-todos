"""Settings dialog implementation."""

from dataclasses import dataclass

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Select


@dataclass
class ThemeChanged(events.Event):
    """Event emitted when the theme is changed."""

    theme: str  # The name of the selected theme


class SettingsDialog(ModalScreen):
    """Dialog for application settings."""

    # Available themes
    selectThemeList = [
        ("textual-dark", "textual-dark"),
        ("textual-light", "textual-light"),
        ("nord", "nord"),
        ("gruvbox", "gruvbox"),
        ("dracula", "dracula"),
        ("tokyo-night", "tokyo-night"),
        ("monokai", "monokai"),
        ("flexoki", "flexoki"),
        ("catppuccin-mocha", "catppuccin-mocha"),
        ("catppuccin-latte", "catppuccin-latte"),
        ("solarized-light", "solarized-light"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the dialog UI."""
        with Vertical(id="settings-dialog"):
            yield Label("Settings", id="settings-title")

            # Theme selection
            theme_select = Select(
                self.selectThemeList,
                id="theme-select",
                value=self.app.dark_theme
                if hasattr(self.app, "dark_theme")
                else "textual-dark",
            )
            theme_select.border_title = "Theme"
            yield theme_select

            # Buttons
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel-button", variant="error")
                yield Button("Save", id="save-button", variant="primary")

    @on(Button.Pressed, "#save-button")
    def on_save(self) -> None:
        """Handle save button click."""
        theme = self.query_one("#theme-select", Select).value
        # Emit the ThemeChanged event with the selected theme
        self.post_message(ThemeChanged(theme))
        self.dismiss()

    @on(Button.Pressed, "#cancel-button")
    def on_cancel(self) -> None:
        """Handle cancel button click."""
        self.dismiss()
