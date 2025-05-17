from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class EditDialog(ModalScreen):
    """Dialog for both adding and editing tasks."""

    class Save(Message):
        def __init__(self, task: dict, is_edit: bool = False):
            self.task = task
            self.is_edit = is_edit
            super().__init__()

    def __init__(self, task: dict | None = None):
        super().__init__()
        self.editing_task = task or {}
        self.is_edit = task is not None

    def compose(self) -> ComposeResult:
        editDialog = Vertical(id="edit-dialog")
        editDialog.border_title = "Edit Task" if self.is_edit else "Add Task"
        with editDialog:
            with Vertical(id="fields"):
                inputTitle = Input(
                    placeholder="Do the laundry",
                    id="title-input",
                    value=self.editing_task.get("title", ""),
                )
                inputTitle.border_title = "Task Title"
                yield inputTitle

                inputDesc = Input(
                    placeholder="Remember the upstairs baskets",
                    id="desc-input",
                    value=self.editing_task.get("description", ""),
                )
                inputDesc.border_title = "Description"
                yield inputDesc

                inputDate = Input(
                    placeholder="YYYY-MM-DD",
                    id="due-date-input",
                    value=self.editing_task.get("due_date", ""),
                )
                inputDate.border_title = "Due Date"
                yield inputDate

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
            "title": self.query_one("#title-input", Input).value,
            "description": self.query_one("#desc-input", Input).value,
            "due_date": self.query_one("#due-date-input", Input).value or None,
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
        deleteDialog = Vertical(id="delete-dialog")
        deleteDialog.border_title = "Delete Task"
        with deleteDialog:
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


class SettingsDialog(ModalScreen):
    """Dialog for application settings."""

    def compose(self) -> ComposeResult:
        settingsDialog = Vertical(id="settings-dialog")
        settingsDialog.border_title = "Settings"
        with settingsDialog:
            yield Label("Settings go here")
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel-button")
                yield Button("Save", id="save-button", variant="primary")

    @on(Button.Pressed, "#save-button")
    def on_save(self):
        # Save settings logic goes here
        self.dismiss()

    @on(Button.Pressed, "#cancel-button")
    def on_cancel(self):
        self.dismiss()
