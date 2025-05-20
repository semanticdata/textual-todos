"""Task view widget implementation."""

from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Input

from .task_types import TaskData


class TaskView(Vertical):
    """View for displaying additional task information and making quick edits."""

    class Save(Message):
        def __init__(self, task: TaskData):
            self.task = task
            super().__init__()

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
            title_input = Input(id="task-view-title")
            title_input.border_title = "Title"
            yield title_input

            # Due date
            due_date = Input(id="task-view-due-date")
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

            # Task description
            desc_input = Input(id="task-view-desc")
            desc_input.border_title = "Description"
            yield desc_input

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
            desc_input.value = task.get("description") or ""
            due_date.value = task.get("due_date") or ""
            project_input.value = task.get("project_name", "Inbox").title()

            # Set status
            status = "✅ Completed" if task.get("completed", False) else "⏳ Pending"
            status_input.value = status

            # Style based on completion status
            status_input.styles.color = "green" if task.get("completed", False) else "yellow"
        else:
            # Clear all fields
            title_input.value = ""
            desc_input.value = ""
            due_date.value = ""
            project_input.value = ""
            status_input.value = ""
        self.refresh()

    @on(Input.Changed, "#task-view-title,#task-view-desc,#task-view-due-date")
    def on_input_changed(self, event: Input.Changed) -> None:
        title = self.query_one("#task-view-title", Input).value.strip()
        description = self.query_one("#task-view-desc", Input).value.strip()
        due_date = self.query_one("#task-view-due-date", Input).value.strip()
        if self.selected_task is None:
            # Do not auto-save for new tasks on change
            return
        orig_title = self.selected_task.get("title", "").strip()
        orig_description = (self.selected_task.get("description") or "").strip()
        orig_due_date = (self.selected_task.get("due_date") or "").strip()
        if title == orig_title and description == orig_description and due_date == orig_due_date:
            return  # No changes, do not post Save
        task_data: TaskData = {
            **self.selected_task,
            "title": title,
            "description": description if description else None,
            "due_date": due_date if due_date else None,
        }
        self.post_message(self.Save(task_data))

    @on(Input.Submitted, "#task-view-title,#task-view-desc,#task-view-due-date")
    @on(Input.Blurred, "#task-view-title,#task-view-desc,#task-view-due-date")
    def on_input_submitted_or_blurred(self, event: Input.Submitted | Input.Blurred) -> None:
        if self.selected_task is not None:
            return  # Only handle new tasks here
        title = self.query_one("#task-view-title", Input).value.strip()
        description = self.query_one("#task-view-desc", Input).value.strip()
        due_date = self.query_one("#task-view-due-date", Input).value.strip()
        if title:
            task_data: TaskData = {
                "title": title,
                "description": description if description else None,
                "due_date": due_date if due_date else None,
                "project_name": "Inbox",
            }
            self.post_message(self.Save(task_data))

    def clear_and_focus(self) -> None:
        """Clear all input fields and focus the title input for new task creation."""
        title_input = self.query_one("#task-view-title", Input)
        desc_input = self.query_one("#task-view-desc", Input)
        due_date = self.query_one("#task-view-due-date", Input)
        project_input = self.query_one("#task-view-project", Input)
        status_input = self.query_one("#task-view-status", Input)
        title_input.value = ""
        desc_input.value = ""
        due_date.value = ""
        project_input.value = ""
        status_input.value = ""
        self.selected_task = None
        self.refresh()
        title_input.focus()
