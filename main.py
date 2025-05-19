from textual import on
from textual.app import App, ComposeResult
from textual.message import Message
from textual.widgets import Footer, Header

from models import TaskStore
from ui import (
    DeleteConfirmDialog,
    EditDialog,
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
        ("e", "edit_task", "Edit Task"),
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
        # Update task view with no selection
        self.query_one(TaskView).update_task(None)

    @on(TaskList.Selected)
    def handle_task_selected(self, event: TaskList.Selected) -> None:
        """Handle task selection in the task list."""
        self.query_one(TaskView).update_task(event.task)

    def action_add_task(self):
        """Open the add-task dialog."""
        self.push_screen(EditDialog())

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

    def action_edit_task(self):
        """Open edit dialog for selected task."""
        task_list = self.query_one(TaskList)
        selected_task = task_list.get_selected_task()
        if selected_task:
            self.push_screen(EditDialog(selected_task))

    @on(EditDialog.Save)
    async def handle_save(self, event: EditDialog.Save):
        """Handle both new tasks and updates."""
        if event.is_edit:
            result = await self.task_store.update_task(
                event.task["id"],
                event.task["title"],
                event.task["description"],
                due_date=event.task["due_date"],
            )
        else:
            result = await self.task_store.add_task(
                event.task["title"],
                event.task["description"],
                due_date=event.task["due_date"],
                project=event.task["project_name"] if "project_name" in event.task else "inbox",
            )

        if "error" in result:
            self.notify(result["error"], severity="error", timeout=3)
            return

        # Reload tasks from database to ensure UI is in sync
        self.tasks = await self.task_store.load()
        self.update_list()

        message = "Task updated!" if event.is_edit else "Task saved!"
        self.notify(message, timeout=3)

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
