"""Edit task dialog implementation."""

from typing import List, Optional, Tuple

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select

from database import db

from .task_types import TaskData


class EditDialog(ModalScreen):
    """Dialog for both adding and editing tasks."""

    class Save(Message):
        """Message sent when the user saves the task."""

        def __init__(self, task: TaskData, is_edit: bool = False):
            """Initialize the Save message.

            Args:
                task: The task data
                is_edit: Whether this is an edit operation
            """
            self.task = task
            self.is_edit = is_edit
            super().__init__()

    def __init__(self, task: Optional[TaskData] = None):
        """Initialize the dialog.

        Args:
            task: Optional task data to edit
        """
        super().__init__()
        self.editing_task: TaskData = task or {}
        self.is_edit = task is not None
        self.project_list: List[Tuple[str, str]] = [("Inbox", "Inbox")]

    async def on_mount(self) -> None:
        """Load projects when dialog is mounted."""
        try:
            # Load all projects except 'Inbox' (already added in __init__)
            projects = db.fetch_all(
                "SELECT name FROM projects WHERE name != 'Inbox' ORDER BY name"
            )
            self.project_list.extend((p["name"], p["name"]) for p in projects)

            # Update the select widget if it exists
            select = self.query_one("#project-select", Select)
            if select:
                select.options = self.project_list
        except Exception as e:
            self.notify(f"Failed to load projects: {e}", severity="error")

    def compose(self) -> ComposeResult:
        """Compose the dialog UI."""
        edit_dialog = Vertical(id="edit-dialog")
        edit_dialog.border_title = "Edit Task" if self.is_edit else "Add Task"

        with edit_dialog:
            # Task title
            title_input = Input(
                id="edit-title",
                placeholder="Task title",
                value=self.editing_task.get("title", ""),
            )
            title_input.border_title = "Title"
            yield title_input

            # Task description
            desc_input = Input(
                id="edit-desc",
                placeholder="Task description (optional)",
                value=self.editing_task.get("description", ""),
            )
            desc_input.border_title = "Description"
            yield desc_input

            # Due date
            due_date = Input(
                id="edit-due-date",
                placeholder="YYYY-MM-DD (optional)",
                value=self.editing_task.get("due_date", ""),
            )
            due_date.border_title = "Due Date"
            yield due_date

            # Project selection
            project_select = Select(
                self.project_list,
                id="project-select",
                value=self.editing_task.get("project_name", "Inbox"),
            )
            project_select.border_title = "Project"
            yield project_select

            # Priority selection
            priority_select = Select(
                [
                    ("High", "high"),
                    ("Medium", "medium"),
                    ("Low", "low"),
                ],
                id="priority-select",
                value=self.editing_task.get("priority", "medium"),
            )
            priority_select.border_title = "Priority"
            yield priority_select

            # Buttons
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel-button", variant="error")
                yield Button("Save", id="save-button", variant="primary")

    @on(Button.Pressed, "#save-button")
    def on_save(self) -> None:
        """Handle save button click."""
        title = self.query_one("#edit-title", Input).value.strip()
        if not title:
            self.notify("Title cannot be empty", severity="error")
            return

        # Get values from form
        description = self.query_one("#edit-desc", Input).value.strip()
        due_date = self.query_one("#edit-due-date", Input).value.strip()
        project = self.query_one("#project-select", Select).value
        priority = self.query_one("#priority-select", Select).value

        # Update task data
        task_data: TaskData = {
            **self.editing_task,
            "title": title,
            "description": description if description else None,
            "due_date": due_date if due_date else None,
            "project_name": project,
            "priority": priority,
        }

        # Post message to parent with task data
        self.post_message(self.Save(task_data, self.is_edit))
        self.dismiss()

    @on(Button.Pressed, "#cancel-button")
    def on_cancel(self) -> None:
        """Handle cancel button click."""
        self.dismiss()
