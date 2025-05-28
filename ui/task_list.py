"""Task list widget implementation using DataTable."""

from typing import Optional

from rich.text import Text
from textual import events, on
from textual.app import ComposeResult
from textual.containers import Container
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import DataTable


class TaskList(Container):
    """A widget that displays a list of tasks in a DataTable."""

    def __init__(self):
        """Initialize the task list."""
        super().__init__()
        self.id = "task-list"
        self.border_title = "Tasks"
        self.tasks = []
        self.has_focus = reactive(False)

    def compose(self) -> ComposeResult:
        """Compose the task list UI."""
        table = DataTable(
            id="task-table",
            cursor_type="row",
            zebra_stripes=True,
            header_height=1,
        )
        table.add_columns("Title", "Description", "Due Date", "Status")
        table.cursor_type = "row"
        yield table

    def on_mount(self) -> None:
        """Configure the table after it's mounted."""
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_class("task-table")

        # Focus the table by default if it has tasks
        if self.tasks:
            table.focus()

    def update_table(self, tasks: list[dict], focus_task_id: Optional[int] = None) -> None:
        """Update the table with the given tasks.

        Args:
            tasks: List of task dictionaries
            focus_task_id: Optional task ID to focus after update
        """
        self.tasks = tasks
        table = self.query_one(DataTable)

        # Store current scroll position
        scroll_x, scroll_y = table.scroll_x, table.scroll_y

        # Clear and repopulate the table
        table.clear()

        # Add tasks to the table
        for task in tasks:
            # Determine status text and style
            status = "✅" if task.get("completed", False) else "⏳"

            # Create styled text for title with strikethrough if completed
            title_text = Text(task.get("title", ""))
            if task.get("completed", False):
                title_text.stylize("strike")

            # Add row to table
            row_key = str(task["id"])
            table.add_row(
                title_text,
                task.get("description", ""),
                task.get("due_date", ""),
                status,
                key=row_key,
            )

            # Focus the specified task if it exists
            if focus_task_id is not None and task["id"] == focus_task_id:
                try:
                    table.cursor_coordinate = (table.get_row_index(row_key), 0)
                    table.focus()
                except NoMatches:
                    pass

        # Restore scroll position
        table.scroll_to(scroll_x, scroll_y)

    def get_selected_task_id(self) -> Optional[int]:
        """Get the ID of the currently selected task.

        Returns:
            Optional[int]: The task ID or None if no task is selected
        """
        table = self.query_one(DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.tasks):
            return self.tasks[table.cursor_row].get("id")
        return None

    def get_selected_task(self) -> Optional[dict]:
        """Get the currently selected task.

        Returns:
            Optional[dict]: The selected task or None if no task is selected
        """
        table = self.query_one(DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.tasks):
            return self.tasks[table.cursor_row]
        return None

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the table."""
        if event.row_key is not None and event.row_key.value is not None:
            try:
                task_id = int(str(event.row_key.value))
                task = next((t for t in self.tasks if t["id"] == task_id), None)
                if task:
                    self.post_message(self.Selected(task))
                    # Update focus state
                    self.has_focus = True
            except (ValueError, AttributeError):
                # Skip if the row_key value can't be converted to an int
                pass

    def on_focus(self, event: events.Focus) -> None:
        """Handle focus events on the task list."""
        self.has_focus = True
        self.border_title = "[bold]Tasks[/]"

    def on_blur(self, event: events.Blur) -> None:
        """Handle blur events on the task list."""
        self.has_focus = False
        self.border_title = "Tasks"

    def focus(self, scroll_visible: bool = True) -> None:
        """Focus the task list."""
        try:
            table = self.query_one(DataTable)
            table.focus(scroll_visible)
            self.has_focus = True
            self.border_title = "[bold]Tasks[/]"
        except NoMatches:
            pass

    class Selected(Message):
        """Message sent when a task is selected in the table."""

        def __init__(self, task: dict):
            super().__init__()
            self.task = task
