from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.message import Message
from textual.widgets import Footer, Header

from models import TaskStore
from ui import (
    DeleteConfirmDialog,
    ProjectList,
    SettingsDialog,
    TaskList,
    TaskView,
    ThemeChanged,
)


class TodoApp(App):
    """Todo application with working dialog and strikethrough."""

    CSS_PATH = "style.tcss"

    BINDINGS = [
        ("a", "add_task", "Add Task"),
        ("d", "delete_task", "Delete Task"),
        ("c", "complete_task", "Complete Task"),
        ("s", "settings", "Settings"),
        ("q", "quit", "Quit"),
    ]

    class ThemeChangedMessage(Message):
        """Message sent when the theme changes."""

        def __init__(self, theme: str):
            self.theme = theme
            super().__init__()

    def __init__(self):
        super().__init__()
        self.task_store = TaskStore()
        self.tasks = []

    async def on_mount(self) -> None:
        """Initialize the app and load tasks."""
        self.title = "Textual Todos"
        self.sub_title = "A simple Todo app in your terminal"
        """Load tasks when the app starts."""
        self.tasks = await self.task_store.load()
        self.update_list()

    def update_list(self, focus_task_id: Optional[int] = None):
        """Refresh the task list with current tasks.

        Args:
            focus_task_id: Optional task ID to focus after update
        """
        task_list = self.query_one(TaskList)
        task_view = self.query_one(TaskView)

        # Update the task list
        task_list.update_table(self.tasks, focus_task_id)

        # If we have tasks but none is selected, select the first one
        if self.tasks and focus_task_id is None:
            task_view.update_task(self.tasks[0])
        # If we have a specific task to focus
        elif focus_task_id is not None:
            task = next((t for t in self.tasks if t["id"] == focus_task_id), None)
            if task:
                task_view.update_task(task)
        # No tasks
        elif not self.tasks:
            task_view.update_task(None)

        # Ensure the task list has focus by default if not editing
        if not task_view._is_editing:
            task_list.focus()

    @on(TaskList.Selected)
    def handle_task_selected(self, event: TaskList.Selected) -> None:
        """Handle task selection in the task list."""
        task_view = self.query_one(TaskView)
        task_view.update_task(event.task)
        # Keep focus on the task list unless we're in edit mode
        if not task_view._is_editing:
            self.query_one(TaskList).focus()

    @on("data_table.row_highlighted")
    def handle_row_highlighted(self, event) -> None:
        """Update TaskView when the row highlight (cursor) changes in the DataTable."""
        task_view = self.query_one(TaskView)
        # Only update if we're not currently editing
        if not task_view._is_editing:
            # Find the TaskList and DataTable
            task_list = self.query_one(TaskList)
            table = task_list.query_one("#task-table")
            row_idx = table.cursor_row
            if row_idx is not None and 0 <= row_idx < len(self.tasks):
                task_view.update_task(self.tasks[row_idx])

    def action_add_task(self):
        """Focus TaskView for adding a new task."""
        task_view = self.query_one(TaskView)
        task_list = self.query_one(TaskList)

        # Clear and focus the task view for new task
        task_view.clear_and_focus()

        # If there are no tasks, ensure the task list is in a good state
        if not self.tasks:
            task_list.update_table([])

        # The task view will take focus in clear_and_focus()

    async def action_complete_task(self):
        """Toggle completion for selected task."""
        task_list = self.query_one(TaskList)
        selected_task = task_list.get_selected_task()
        if selected_task:
            task_id = selected_task["id"]
            await self.task_store.toggle_completion(task_id)
            self.tasks = await self.task_store.load()
            self.update_list()
            self.notify("Task updated!", timeout=3)

    def compose(self) -> ComposeResult:
        """Layout of the app."""
        yield Header()
        yield ProjectList()
        yield TaskList()
        yield TaskView()
        yield Footer()

    @on(TaskView.Save)
    async def handle_taskview_save(self, event: TaskView.Save):
        # If there is no id, this is a new task
        if not event.task.get("id"):
            # Create new task
            result = await self.task_store.add_task(
                event.task["title"],
                event.task.get("description") or "",
                priority=event.task.get("priority", "medium"),
                due_date=event.task.get("due_date"),
                project=event.task.get("project_name", "Inbox"),
            )
            if "error" in result:
                self.notify(result["error"], severity="error", timeout=3)
                return

            # Reload tasks and update the list, focusing on the new task
            self.tasks = await self.task_store.load()
            self.update_list(focus_task_id=result["id"])

            # Notify user
            self.notify("Task created!", timeout=2)

            # Focus the task list after a short delay
            def focus_task_list():
                task_list = self.query_one(TaskList)
                task_list.focus()

            self.set_timer(0.1, focus_task_list)
        else:
            # Update existing task
            task_id = event.task["id"]
            result = await self.task_store.update_task(
                task_id,
                event.task["title"],
                event.task["description"],
                due_date=event.task.get("due_date"),
            )
            if "error" in result:
                self.notify(result["error"], severity="error", timeout=3)
                return

            # Reload tasks and update the list, maintaining focus on the updated task
            self.tasks = await self.task_store.load()
            self.update_list(focus_task_id=task_id)

            # Notify user
            self.notify("Task updated!", timeout=2)

            # Focus the task list after a short delay
            def focus_task_list():
                task_list = self.query_one(TaskList)
                task_list.focus()

            self.set_timer(0.1, focus_task_list)

    async def action_delete_task(self):
        """Handle task deletion flow."""
        task_list = self.query_one(TaskList)
        selected_task = task_list.get_selected_task()

        if not selected_task:
            self.notify("No task selected!", timeout=3)
            return

        if not self.tasks:
            self.notify("Task list is empty!", timeout=3)
            return

        # Show confirmation dialog
        dialog = DeleteConfirmDialog(selected_task["title"], selected_task["id"])
        await self.push_screen(dialog)

    @on(DeleteConfirmDialog.Delete)
    async def handle_delete(self, message: DeleteConfirmDialog.Delete):
        """Handle the deletion of a task."""
        success = await self.task_store.delete_task(message.task_id)
        if success:
            self.tasks = await self.task_store.load()
            self.update_list()
            self.notify("Task deleted!", timeout=3)
        else:
            self.notify("Failed to delete task!", severity="error", timeout=3)

    def action_settings(self):
        """Open settings dialog."""
        self.push_screen(SettingsDialog())

    @on(ThemeChanged)
    def handle_theme_changed(self, event: ThemeChanged) -> None:
        """Handle theme change event from settings dialog."""
        theme = event.theme
        # Apply the selected theme
        self.theme = theme
        # Post a message about the theme change
        self.post_message(self.ThemeChangedMessage(theme))
        self.notify(f"Theme changed to {theme}", timeout=3)


if __name__ == "__main__":
    app = TodoApp()
    app.run()
