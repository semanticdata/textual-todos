"""Delete confirmation dialog implementation."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class DeleteConfirmDialog(ModalScreen):
    """Confirmation dialog for task deletion."""

    class Delete(Message):
        """Message sent when the user confirms deletion."""

        def __init__(self, task_id: int):
            """Initialize the Delete message.

            Args:
                task_id: ID of the task to be deleted
            """
            self.task_id = task_id
            super().__init__()

    def __init__(self, task_title: str, task_id: int):
        """Initialize the dialog.

        Args:
            task_title: Title of the task to be deleted
            task_id: ID of the task to be deleted
        """
        super().__init__()
        self.task_title = task_title
        self.task_id = task_id

    def compose(self) -> ComposeResult:
        """Compose the dialog UI."""
        with Vertical(id="delete-dialog"):
            yield Label(
                f"Are you sure you want to delete task: {self.task_title}?",
                id="delete-message",
            )
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel-button", variant="primary")
                yield Button("Delete", id="delete-button", variant="error")

    @on(Button.Pressed, "#delete-button")
    def on_delete(self) -> None:
        """Handle delete button click."""
        self.post_message(self.Delete(self.task_id))
        self.dismiss()

    @on(Button.Pressed, "#cancel-button")
    def on_cancel(self) -> None:
        """Handle cancel button click."""
        self.dismiss()
