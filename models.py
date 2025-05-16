import asyncio
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskValidationError(Exception):
    """Raised when task validation fails."""

    pass


class TaskNotFoundError(Exception):
    """Raised when a task is not found."""

    pass


class TaskStore:
    def __init__(self, path: str = "todos.db"):
        self.path = Path(path)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with tasks table."""
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    completed BOOLEAN NOT NULL DEFAULT 0,
                    priority TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL,
                    due_date TEXT
                )
            """)

    async def load(self) -> List[Dict]:
        """Load tasks from SQLite database."""
        try:
            return await asyncio.to_thread(self._read_db)
        except sqlite3.Error:
            return []

    def _read_db(self) -> List[Dict]:
        """Synchronous database read operation."""
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM tasks")
            return [dict(row) for row in cursor.fetchall()]

    def validate_task(
        self, title: str, description: str, due_date: Optional[str] = None
    ) -> Optional[str]:
        """Enhanced validation with specific error messages.
        Returns None if validation passes, or error message if validation fails.
        """
        if not title.strip():
            return "Title cannot be empty"
        if len(title) > 100:
            return "Title cannot exceed 100 characters"
        if len(description) > 500:
            return "Description cannot exceed 500 characters"
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                return "Due date must be in YYYY-MM-DD format"
        return None

    async def add_task(
        self,
        title: str,
        description: str = "",
        priority: Union[Priority, str] = Priority.MEDIUM,
        due_date: Optional[str] = None,
    ) -> Dict:
        """Async task addition with priority and creation date.
        Returns a dictionary with either the created task or an error message.
        """
        if isinstance(priority, str):
            try:
                priority = Priority(priority.lower())
            except ValueError:
                return {"error": f"Invalid priority value: {priority}"}

        validation_error = self.validate_task(title, description, due_date)
        if validation_error:
            return {"error": validation_error}

        now = datetime.now().isoformat()
        task = {
            "title": title.strip(),
            "description": description.strip(),
            "completed": False,
            "priority": priority.value,
            "created_at": now,
            "modified_at": now,
            "due_date": due_date if due_date and due_date.strip() else None,
        }

        try:
            task["id"] = await asyncio.to_thread(self._insert_task, task)
            return task
        except sqlite3.Error as e:
            return {"error": f"Database error: {str(e)}"}

    def _insert_task(self, task: Dict) -> int:
        """Synchronous task insertion operation."""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (
                    title, description, completed, priority,
                    created_at, modified_at, due_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task["title"],
                    task["description"],
                    task["completed"],
                    task["priority"],
                    task["created_at"],
                    task["modified_at"],
                    task["due_date"],
                ),
            )
            return cursor.lastrowid

    async def toggle_completion(self, task_id: int) -> Dict:
        """Toggle task completion status with modification tracking."""
        try:
            task = await self._get_task_by_id(task_id)
            task["completed"] = not task["completed"]
            task["modified_at"] = datetime.now().isoformat()
            await asyncio.to_thread(self._update_task, task)
            return task
        except sqlite3.Error as e:
            return {"error": f"Database error: {str(e)}"}

    async def update_task(
        self,
        task_id: int,
        title: str,
        description: str,
        priority: Optional[Union[Priority, str]] = None,
        due_date: Optional[str] = None,
    ) -> Dict:
        """Update an existing task with validation and modification tracking.
        Returns a dictionary with either the updated task or an error message.
        """
        try:
            task = await self._get_task_by_id(task_id)
        except TaskNotFoundError as e:
            return {"error": str(e)}

        validation_error = self.validate_task(title, description, due_date)
        if validation_error:
            return {"error": validation_error}

        if isinstance(priority, str):
            try:
                priority = Priority(priority.lower())
            except ValueError:
                return {"error": f"Invalid priority value: {priority}"}

        task.update(
            {
                "title": title,
                "description": description,
                "modified_at": datetime.now().isoformat(),
                "due_date": due_date,
            }
        )

        if priority is not None:
            task["priority"] = priority.value

        try:
            await asyncio.to_thread(self._update_task, task)
            return task
        except sqlite3.Error as e:
            return {"error": f"Database error: {str(e)}"}

    def _update_task(self, task: Dict) -> None:
        """Synchronous task update operation."""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                UPDATE tasks
                SET title=?, description=?, completed=?, priority=?,
                    modified_at=?, due_date=?
                WHERE id=?
                """,
                (
                    task["title"],
                    task["description"],
                    task["completed"],
                    task["priority"],
                    task["modified_at"],
                    task["due_date"],
                    task["id"],
                ),
            )

    async def delete_task(self, task_id: int) -> bool:
        """Remove a task by ID and return success status."""
        try:
            await self._get_task_by_id(task_id)  # Verify task exists
            return await asyncio.to_thread(self._delete_task, task_id)
        except (TaskNotFoundError, sqlite3.Error):
            return False

    def _delete_task(self, task_id: int) -> bool:
        """Synchronous task deletion operation."""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            return cursor.rowcount > 0

    async def _get_task_by_id(self, task_id: int) -> Dict:
        """Helper method to get task by ID or raise error."""
        try:
            task = await asyncio.to_thread(self._get_task_by_id_sync, task_id)
            if task:
                return task
            raise TaskNotFoundError(f"Task with ID {task_id} not found")
        except sqlite3.Error as e:
            raise TaskNotFoundError(f"Database error: {str(e)}")

    def _get_task_by_id_sync(self, task_id: int) -> Optional[Dict]:
        """Synchronous operation to get task by ID."""
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    async def search_tasks(
        self,
        query: str = "",
        priority: Optional[Union[Priority, str]] = None,
        completed: Optional[bool] = None,
    ) -> List[Dict]:
        """Search tasks with filtering options."""
        if isinstance(priority, str) and priority:
            try:
                priority = Priority(priority.lower())
            except ValueError:
                raise TaskValidationError(f"Invalid priority value: {priority}")

        try:
            return await asyncio.to_thread(
                self._search_tasks_sync, query, priority, completed
            )
        except sqlite3.Error:
            return []

    def _search_tasks_sync(
        self, query: str, priority: Optional[Priority], completed: Optional[bool]
    ) -> List[Dict]:
        """Synchronous task search operation."""
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            conditions = []
            params = []

            if query:
                conditions.append("(title LIKE ? OR description LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])

            if priority:
                conditions.append("priority = ?")
                params.append(priority.value)

            if completed is not None:
                conditions.append("completed = ?")
                params.append(completed)

            sql = "SELECT * FROM tasks"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
