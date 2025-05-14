from textual.app import ComposeResult
from textual.widgets import Input, Button, Label
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual import on
from textual.message import Message


class EditDialog(ModalScreen):
    """Dialog for both adding and editing tasks."""

    class Save(Message):
        def __init__(self, task: dict, is_edit: bool = False):
            self.task = task
            self.is_edit = is_edit
            super().__init__()

    CSS = """
    EditDialog {
        align: center middle;
    }
    #dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
    }
    #fields {
        height: auto;
        padding: 1;
    }
    #buttons {
        height: auto;
        padding: 1;
        layout: horizontal;
        align: right middle;
    }
    #save-button {
        margin-left: 1;
    }
    """

    def __init__(self, task: dict = None):
        super().__init__()
        self.editing_task = task or {}
        self.is_edit = task is not None

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            with Vertical(id="fields"):
                yield Label("Title:")
                yield Input(
                    placeholder="Task title",
                    id="title-input",
                    value=self.editing_task.get("title", ""),
                )
                yield Label("Description:")
                yield Input(
                    placeholder="Optional description",
                    id="desc-input",
                    value=self.editing_task.get("description", ""),
                )
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel-button")
                yield Button(
                    "Update" if self.is_edit else "Save",
                    id="save-button",
                    variant="primary",
                )

    @on(Button.Pressed, "#save-button")
    def on_save(self):
        task = {
            "title": self.query_one("#title-input").value,
            "description": self.query_one("#desc-input").value,
        }
        if self.is_edit:
            task["id"] = self.editing_task["id"]
        self.post_message(self.Save(task, self.is_edit))
        self.dismiss()

    @on(Button.Pressed, "#cancel-button")
    def on_cancel(self):
        self.dismiss()


class DeleteConfirmDialog(ModalScreen):
    """Confirmation dialog for deletion."""

    class Delete(Message):
        def __init__(self, task_id: int):
            self.task_id = task_id
            super().__init__()

    def __init__(self, task_title: str, task_id: int):
        super().__init__()
        self.task_title = task_title
        self.task_id = task_id

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Delete '{self.task_title}'?", id="question")
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel-button")
                yield Button("Delete", id="delete-button", variant="error")

    @on(Button.Pressed, "#delete-button")
    def on_delete(self):
        self.post_message(self.Delete(self.task_id))
        self.dismiss()

    @on(Button.Pressed, "#cancel-button")
    def on_cancel(self):
        self.dismiss()
