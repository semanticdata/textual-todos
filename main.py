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

    def update_list(self):
        """Refresh the task list with current tasks."""
        task_list = self.query_one(TaskList)
        task_list.update_table(self.tasks)
        # Focus the first task if there is one
        if self.tasks:
            table = task_list.query_one("#task-table")
            table.focused_cell = (0, 0)
            table.focus()
            self.query_one(TaskView).update_task(self.tasks[0])
        else:
            # Update task view with no selection
            self.query_one(TaskView).update_task(None)

    @on(TaskList.Selected)
    def handle_task_selected(self, event: TaskList.Selected) -> None:
        """Handle task selection in the task list."""
        self.query_one(TaskView).update_task(event.task)

    @on("data_table.row_highlighted")
    def handle_row_highlighted(self, event) -> None:
        """Update TaskView when the row highlight (cursor) changes in the DataTable."""
        # Find the TaskList and DataTable
        task_list = self.query_one(TaskList)
        table = task_list.query_one("#task-table")
        row_idx = table.cursor_row
        if row_idx is not None and 0 <= row_idx < len(self.tasks):
            self.query_one(TaskView).update_task(self.tasks[row_idx])

    def action_add_task(self):
        """Focus TaskView for adding a new task."""
        task_view = self.query_one(TaskView)
        task_view.clear_and_focus()
        # Optionally, you could set a flag here if needed for new task mode

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
            self.tasks = await self.task_store.load()
            self.update_list()
            # Focus the new task in the list
            task_list = self.query_one(TaskList)
            for idx, t in enumerate(self.tasks):
                if t["id"] == result["id"]:
                    table = task_list.query_one("#task-table")
                    table.focused_cell = (idx, 0)
                    break
            self.query_one(TaskView).update_task(result)
        else:
            # Update existing task
            result = await self.task_store.update_task(
                event.task["id"],
                event.task["title"],
                event.task["description"],
                due_date=event.task["due_date"],
            )
            if "error" in result:
                self.notify(result["error"], severity="error", timeout=3)
                return
            self.tasks = await self.task_store.load()
            # Find the updated task in the new list
            updated_task = next((t for t in self.tasks if t["id"] == event.task["id"]), None)
            # Update the list and re-select the task
            task_list = self.query_one(TaskList)
            task_list.update_table(self.tasks)
            if updated_task:
                # Find the row index for the updated task
                for idx, t in enumerate(self.tasks):
                    if t["id"] == updated_task["id"]:
                        table = task_list.query_one("#task-table")
                        table.focused_cell = (idx, 0)
                        break
                self.query_one(TaskView).update_task(updated_task)

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
