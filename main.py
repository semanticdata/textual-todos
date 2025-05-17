from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, ListItem, ListView

from models import TaskStore
from widgets import (
    DeleteConfirmDialog,
    EditDialog,
    ProjectList,
    SettingsDialog,
    TaskView,
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
        """Refresh the ListView with current tasks."""
        list_view = self.query_one(ListView)
        list_view.border_title = "Tasks"
        list_view.clear()

        title_header = Label("[b]Title[/b]", classes="header")
        desc_header = Label("[b]Description[/b]", classes="header")
        due_header = Label("[b]Due Date[/b]", classes="header")
        list_view.append(ListItem(title_header, desc_header, due_header))

        for task in self.tasks:
            title_text = task["title"]
            title_label = Label(title_text)
            desc_label = Label(task["description"])
            due_date_label = Label(task["due_date"])
            if task["completed"]:
                title_label.add_class("completed")
                desc_label.add_class("completed")
                due_date_label.add_class("completed")
            list_view.append(ListItem(title_label, desc_label, due_date_label))

        # Update task view with no selection
        self.query_one(TaskView).update_task(None)

    @on(ListView.Highlighted)
    def handle_selection(self, event: ListView.Highlighted) -> None:
        """Handle task selection in the list view."""
        list_view = self.query_one(ListView)
        # Check if index is valid (greater than 0 because 0 is the header)
        if (
            event.item is not None
            and list_view.index is not None
            and list_view.index > 0
        ):
            # Subtract 1 from index to account for header row
            task = self.tasks[list_view.index - 1]
            self.query_one(TaskView).update_task(task)
        else:
            self.query_one(TaskView).update_task(None)

    def action_add_task(self):
        """Open the add-task dialog."""
        self.push_screen(EditDialog())

    async def action_complete_task(self):
        """Toggle completion for selected task."""
        if self.query_one(ListView).highlighted_child:
            index = self.query_one(ListView).index
            if index is not None:
                task_id = self.tasks[index]["id"]
                await self.task_store.toggle_completion(task_id)
                self.tasks = await self.task_store.load()
                self.update_list()
                self.notify("Task updated!", timeout=3)

    def compose(self) -> ComposeResult:
        """Layout of the app."""
        yield Header()
        yield ListView(id="task-list")
        yield ProjectList()
        yield TaskView()
        yield Footer()

    def action_edit_task(self):
        """Open edit dialog for selected task."""
        if self.query_one(ListView).highlighted_child:
            index = self.query_one(ListView).index
            if index is not None:
                task = self.tasks[index]
                self.push_screen(EditDialog(task))

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
                project=event.task["project_name"]
                if "project_name" in event.task
                else "inbox",
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
        list_view = self.query_one(ListView)

        # Guard clauses for all edge cases
        if not list_view.highlighted_child:
            self.notify("No task selected!", timeout=3)
            return

        if not self.tasks:
            self.notify("Task list is empty!", timeout=3)
            return

        index = list_view.index
        if index is None or index >= len(self.tasks):
            self.notify("Invalid selection!", timeout=3)
            return

        task = self.tasks[index]

        # Show confirmation dialog
        dialog = DeleteConfirmDialog(task["title"], task["id"])
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


if __name__ == "__main__":
    app = TodoApp()
    app.run()
