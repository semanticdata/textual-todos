from typing import Any, Dict, List, Optional, TypedDict

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Select

from database import db


class TaskData(TypedDict, total=False):
    """Type definition for task data dictionary."""

    id: int
    title: str
    description: str
    due_date: Optional[str]
    project_name: str
    completed: bool
    priority: str
    created_at: str
    modified_at: str
    project_id: int


class ProjectList(ListView):
    """List of projects."""

    def __init__(self):
        super().__init__()
        self.border_title = "Projects"
        self.id = "project-list"
        self.projects: List[Dict[str, Any]] = []

    async def on_mount(self) -> None:
        """Load projects when the list is mounted."""
        await self.load_projects()

    async def load_projects(self) -> None:
        """Load projects from the database."""
        try:
            rows = db.fetch_all("SELECT id, name FROM projects ORDER BY name")
            self.projects = rows
            self.refresh_projects()
        except Exception as e:
            self.notify(f"Failed to load projects: {e}", severity="error")

    def refresh_projects(self) -> None:
        """Refresh the project list view."""
        self.clear()
        for project in self.projects:
            self.append(
                ListItem(Label(project["name"].title(), classes="project-label"))
            )

    async def add_project(self, name: str) -> bool:
        """Add a new project.

        Args:
            name: Name of the project to add

        Returns:
            bool: True if project was added, False otherwise
        """
        try:
            db.execute("INSERT INTO projects (name) VALUES (?)", (name,))
            await self.load_projects()
            return True
        except Exception as e:
            self.notify(f"Failed to add project: {e}", severity="error")
            return False


class TaskView(Vertical):
    """View for displaying additional task information and making quick edits."""

    def __init__(self):
        """Initialize the task view."""
        super().__init__()
        self.id = "task-view"
        self.border_title = "Task Details"
        self.selected_task: Optional[TaskData] = None

    def compose(self) -> ComposeResult:
        """Compose the task view UI."""
        with Vertical(id="task-details"):
            # Task title
            title_input = Input(id="task-view-title", disabled=True)
            title_input.border_title = "Title"
            yield title_input

            # Task description
            desc_input = Input(id="task-view-desc", disabled=True)
            desc_input.border_title = "Description"
            yield desc_input

            # Due date
            due_date = Input(id="task-view-due-date", disabled=True)
            due_date.border_title = "Due Date"
            yield due_date

            # Project
            project_input = Input(id="task-view-project", disabled=True)
            project_input.border_title = "Project"
            yield project_input

            # Status
            status_input = Input(id="task-view-status", disabled=True)
            status_input.border_title = "Status"
            yield status_input

    def update_task(self, task: Optional[TaskData]) -> None:
        """Update the task view with the selected task's details.

        Args:
            task: The task data to display, or None to clear the view
        """
        self.selected_task = task

        # Get all input fields
        title_input = self.query_one("#task-view-title", Input)
        desc_input = self.query_one("#task-view-desc", Input)
        due_date = self.query_one("#task-view-due-date", Input)
        project_input = self.query_one("#task-view-project", Input)
        status_input = self.query_one("#task-view-status", Input)

        if task:
            # Update fields with task data
            title_input.value = task.get("title", "")
            desc_input.value = task.get("description", "") or "No description"
            due_date.value = task.get("due_date", "") or "No due date"
            project_input.value = task.get("project_name", "Inbox").title()

            # Set status
            status = "✅ Completed" if task.get("completed", False) else "⏳ Pending"
            status_input.value = status

            # Style based on completion status
            status_input.styles.color = (
                "green" if task.get("completed", False) else "yellow"
            )
        else:
            # Clear all fields
            title_input.value = ""
            desc_input.value = ""
            due_date.value = ""
            project_input.value = ""
            status_input.value = ""


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
        self.project_list: List[tuple[str, str]] = [("Inbox", "Inbox")]

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
            with Vertical(id="fields"):
                # Task Title
                input_title = Input(
                    placeholder="Do the laundry",
                    id="title-input",
                    value=self.editing_task.get("title", ""),
                )
                input_title.border_title = "Task Title"
                yield input_title

                # Description
                input_desc = Input(
                    placeholder="Remember the upstairs baskets",
                    id="desc-input",
                    value=self.editing_task.get("description", ""),
                )
                input_desc.border_title = "Description"
                yield input_desc

                # Due Date
                input_date = Input(
                    placeholder="YYYY-MM-DD",
                    id="due-date-input",
                    value=self.editing_task.get("due_date", ""),
                )
                input_date.border_title = "Due Date (YYYY-MM-DD)"
                yield input_date

                # Project Selection
                current_project = self.editing_task.get("project_name", "Inbox")
                select_project = Select(
                    id="project-select",
                    options=self.project_list,
                    value=current_project,
                    allow_blank=False,
                )
                select_project.border_title = "Project"
                yield select_project

            # Action Buttons
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel-button")
                yield Button(
                    "Update" if self.is_edit else "Save",
                    id="save-button",
                    variant="primary",
                )

    @on(Button.Pressed, "#save-button")
    def on_save(self) -> None:
        """Handle save button click."""
        task: TaskData = {
            "title": self.query_one("#title-input", Input).value.strip(),
            "description": self.query_one("#desc-input", Input).value.strip(),
            "due_date": self.query_one("#due-date-input", Input).value.strip() or None,
            "project_name": self.query_one("#project-select", Select).value,
        }

        # Include task ID if this is an edit
        if self.is_edit and "id" in self.editing_task:
            task["id"] = self.editing_task["id"]

        self.post_message(self.Save(task, self.is_edit))
        self.dismiss()

    @on(Button.Pressed, "#cancel-button")
    def on_cancel(self) -> None:
        """Handle cancel button click."""
        self.dismiss()


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
        dialog = Vertical(id="delete-dialog")
        dialog.border_title = "Delete Task"

        with dialog:
            # Confirmation message
            yield Label(
                f"Are you sure you want to delete task: '{self.task_title}'?",
                id="question",
            )

            # Action buttons
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel-button")
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


class SettingsDialog(ModalScreen):
    """Dialog for application settings."""

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
        settingsDialog = Vertical(id="settings-dialog")
        settingsDialog.border_title = "Settings"
        with settingsDialog:
            selectTheme = Select(options=self.selectThemeList, id="theme-select")
            selectTheme.border_title = "Select Theme"
            yield selectTheme
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel-button", variant="error")
                yield Button("Save", id="save-button", variant="primary")

    @on(Button.Pressed, "#save-button")
    def on_save(self):
        # Save settings logic goes here
        self.dismiss()

    @on(Button.Pressed, "#cancel-button")
    def on_cancel(self):
        self.dismiss()
