import sqlite3

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Label,
    ListItem,
    ListView,
    Select,
)


class ProjectList(ListView):
    """List of projects."""

    def __init__(self):
        super().__init__()
        self.border_title = "Projects"
        self.id = "project-list"
        self.projects = []

    async def on_mount(self) -> None:
        """Load projects when the list is mounted."""
        with sqlite3.connect("todos.db") as conn:
            cursor = conn.execute("SELECT name FROM projects ORDER BY name")
            self.projects = [row[0] for row in cursor.fetchall()]
        self.refresh_projects()

    def refresh_projects(self) -> None:
        """Refresh the project list view."""
        self.clear()
        for project in self.projects:
            self.append(ListItem(Label(project.title(), classes="project-label")))


class TaskView(Vertical):
    """View for displaying additional task information and making quick edits."""

    def __init__(self):
        super().__init__()
        self.id = "task-view"
        self.border_title = "Task Details"
        self.selected_task = None

    def compose(self) -> ComposeResult:
        """Layout of the task view."""
        title_input = Input(id="task-view-title", disabled=True)
        title_input.border_title = "Title"
        yield title_input

        desc_input = Input(id="task-view-desc", disabled=True)
        desc_input.border_title = "Description"
        yield desc_input

        due_date = Input(id="task-view-due-date", disabled=True)
        due_date.border_title = "Due Date"
        yield due_date

    def update_task(self, task: dict | None) -> None:
        """Update the task view with the selected task's details."""
        self.selected_task = task
        title_input = self.query_one("#task-view-title", Input)
        desc_input = self.query_one("#task-view-desc", Input)
        due_date = self.query_one("#task-view-due-date", Input)

        if task:
            title_input.value = task["title"]
            desc_input.value = (
                task["description"] if task["description"] is not None else ""
            )
            due_date.value = task["due_date"] if task["due_date"] is not None else ""
        else:
            title_input.value = ""
            desc_input.value = ""
            due_date.value = ""


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
        self.project_list = [("Inbox", "Inbox")]

    async def on_mount(self) -> None:
        """Load projects when dialog is mounted."""
        with sqlite3.connect("todos.db") as conn:
            cursor = conn.execute("SELECT name FROM projects WHERE name != 'Inbox'")
            projects = cursor.fetchall()
            self.project_list.extend((p[0], p[0]) for p in projects)
            self.query_one("#project-select", Select).options = self.project_list

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

                selectProject = Select(
                    id="project-select",
                    options=self.project_list,
                    value=self.editing_task.get("project_name", "Inbox"),
                )
                selectProject.border_title = "Project"
                yield selectProject

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
            "due_date": self.query_one("#due-date-input", Input).value,
            "project_name": self.query_one("#project-select", Select).value,
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
            # yield Label("Settings go here")
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
