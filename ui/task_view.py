"""Task view widget implementation."""

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input

from .task_types import TaskData


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

            # Task description
            desc_input = Input(id="task-view-desc", disabled=True)
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
