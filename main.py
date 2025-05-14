from textual.app import App, ComposeResult
from textual.widgets import ListView, Footer, ListItem, Label
from textual import on
from models import TaskStore
from widgets import EditDialog, DeleteConfirmDialog


class TodoApp(App):
    """Todo application with working dialog and strikethrough."""

    CSS = """
    ListView {
        border: solid $primary;
        height: 1fr;
        scrollbar-gutter: stable;
    }
    ListItem {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 3fr;
    }
    ListItem:hover {
        background: $boost;
    }
    ListItem .completed {
        text-style: strike;
        color: $text-muted;
    }
    ListItem > Label {
        width: 100%;
        height: 100%;
    }
    Button.error {
        background: $error;
        color: auto;
    }
    #dialog {
        width: 40;
    }
    #question {
        padding: 1;
        text-align: center;
    }
    """

    BINDINGS = [
        ("a", "add_task", "Add"),
        ("e", "edit_task", "Edit"),
        ("d", "delete_task", "Delete"),
        ("c", "complete_task", "Complete"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.task_store = TaskStore()

    async def on_mount(self) -> None:
        """Load tasks when the app starts."""
        await self.task_store.load()
        self.update_list()

    def update_list(self):
        """Refresh the ListView with current tasks."""
        list_view = self.query_one(ListView)
        list_view.clear()
        for task in self.task_store.tasks:
            title_label = Label(task["title"])
            desc_label = Label(task["description"])
            if task["completed"]:
                title_label.add_class("completed")
                desc_label.add_class("completed")
            list_view.append(ListItem(title_label, desc_label))

    def action_add_task(self):
        """Open the add-task dialog."""
        self.push_screen(EditDialog())

    async def action_complete_task(self):
        """Toggle completion for selected task."""
        if selected := self.query_one(ListView).highlighted_child:
            index = self.query_one(ListView).index
            task_id = self.task_store.tasks[index]["id"]
            await self.task_store.toggle_completion(task_id)
            await self.task_store.save()
            self.update_list()
            self.notify("Task updated!", timeout=3)

    @on(EditDialog.Save)
    async def handle_save(self, event: EditDialog.Save):
        """Handle saving a new task."""
        if self.task_store.validate_task(
            event.task["title"], event.task["description"]
        ):
            await self.task_store.add_task(
                event.task["title"], event.task["description"]
            )
            await self.task_store.save()
            self.update_list()
            self.notify("Task saved!", timeout=3)

    def compose(self) -> ComposeResult:
        """Layout of the app."""
        yield ListView()
        yield Footer()

    def action_edit_task(self):
        """Open edit dialog for selected task."""
        if selected := self.query_one(ListView).highlighted_child:
            index = self.query_one(ListView).index
            task = self.task_store.tasks[index]
            self.push_screen(EditDialog(task))

    @on(EditDialog.Save)
    async def handle_save(self, event: EditDialog.Save):
        """Handle both new tasks and updates."""
        if event.is_edit:
            await self.task_store.update_task(
                event.task["id"], event.task["title"], event.task["description"]
            )
            message = "Task updated!"
        else:
            await self.task_store.add_task(
                event.task["title"], event.task["description"]
            )
            message = "Task saved!"

        await self.task_store.save()
        self.update_list()
        self.notify(message, timeout=3)

    async def action_delete_task(self):
        """Handle task deletion flow."""
        list_view = self.query_one(ListView)

        # Guard clauses for all edge cases
        if not list_view.highlighted_child:
            self.notify("No task selected!", timeout=3)
            return

        if not self.task_store.tasks:
            self.notify("Task list is empty!", timeout=3)
            return

        index = list_view.index
        if index is None or index >= len(self.task_store.tasks):
            self.notify("Invalid selection!", timeout=3)
            return

        task = self.task_store.tasks[index]

        # Show confirmation dialog
        dialog = DeleteConfirmDialog(task["title"], task["id"])
        await self.push_screen(dialog)

    @on(DeleteConfirmDialog.Delete)
    async def handle_delete(self, message: DeleteConfirmDialog.Delete):
        """Handle the deletion of a task."""
        success = await self.task_store.delete_task(message.task_id)
        if success:
            await self.task_store.save()
            self.update_list()
            self.notify("Task deleted!", timeout=3)
        else:
            self.notify("Failed to delete task!", severity="error", timeout=3)


if __name__ == "__main__":
    app = TodoApp()
    app.run()
