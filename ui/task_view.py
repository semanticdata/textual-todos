"""Task view widget implementation."""

from typing import Optional

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input, Label

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
        self.has_focus = reactive(False)
        self._is_editing = False

    def compose(self) -> ComposeResult:
        """Compose the task view UI."""
        with Vertical(id="task-details"):
            # Task title
            title_input = Input(id="task-view-title", placeholder="Task title")
            title_input.border_title = "Title"
            title_input.tooltip = "Press Enter to save changes"
            yield title_input

            # Due date
            due_date = Input(id="task-view-due-date", placeholder="YYYY-MM-DD")
            due_date.border_title = "Due Date"
            due_date.tooltip = "Format: YYYY-MM-DD"
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
            desc_input = Input(id="task-view-desc", placeholder="Task description")
            desc_input.border_title = "Description"
            desc_input.tooltip = "Press Enter or click outside to save"
            yield desc_input

            # Help text
            help_text = Label("[dim]Tip: Press 'Esc' to return to task list[/]", id="task-view-help")
            yield help_text

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

            # Update border title to show task title
            self.border_title = f"[bold]Task: {task.get('title', 'Untitled')}[/]"
        else:
            # Clear all fields
            title_input.value = ""
            desc_input.value = ""
            due_date.value = ""
            project_input.value = ""
            status_input.value = ""
            self.border_title = "[dim]No task selected[/]"

        # If we're not currently editing, focus the title input
        if not self._is_editing and task:
            title_input.focus()

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
        self.selected_task = None
        self._is_editing = True
        self.add_class("editing")

        # Clear all fields
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

        # Update UI
        self.border_title = "[bold]New Task[/]"
        self.refresh()

        # Focus the title input
        title_input.focus()

    def on_focus(self, event: events.Focus) -> None:
        """Handle focus events on the task view."""
        self.has_focus = True
        if not self._is_editing and self.selected_task:
            self.border_title = f"[bold]Task: {self.selected_task.get('title', 'Untitled')}[/]"
        elif self._is_editing:
            self.border_title = "[bold]New Task[/]"
        else:
            self.border_title = "[dim]No task selected[/]"

    def on_blur(self, event: events.Blur) -> None:
        """Handle blur events on the task view."""
        self.has_focus = False
        if self.selected_task:
            self.border_title = f"Task: {self.selected_task.get('title', 'Untitled')}"
        else:
            self.border_title = "Task Details"

    def on_input_focus(self, event: events.Focus) -> None:
        """Handle focus events on input fields."""
        self._is_editing = True
        self.add_class("editing")

    def on_key(self, event: events.Key) -> None:
        """Handle key events in the task view."""
        if event.key == "escape":
            # Return focus to the task list
            self._is_editing = False
            self.remove_class("editing")
            task_list = self.app.query_one("#task-list")
            task_list.focus()
            event.stop()
        elif event.key == "enter" and event.control.id in ("task-view-title", "task-view-desc", "task-view-due-date"):
            # Save on Enter in any input field
            self._is_editing = False
            self.remove_class("editing")
            event.control.blur()
            event.stop()

    def on_input_blur(self, event: events.Blur) -> None:
        """Handle blur events on input fields."""
        # Check if focus is moving to another input in the same view
        if event.control.id in ("task-view-title", "task-view-desc", "task-view-due-date"):
            self._is_editing = True
            self.add_class("editing")
        else:
            self._is_editing = False
            self.remove_class("editing")
