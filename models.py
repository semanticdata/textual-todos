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
    pass


class TaskNotFoundError(Exception):
    pass


class ProjectNotFoundError(Exception):
    pass


class TaskStore:
    def __init__(self, path: str = "todos.db"):
        self.path = Path(path)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with projects and tasks tables."""
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    completed BOOLEAN NOT NULL DEFAULT 0,
                    priority TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL,
                    due_date TEXT,
                    project_id INTEGER NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                )
            """)
            # Ensure default project "Inbox" exists
            conn.execute("""
                INSERT OR IGNORE INTO projects (name) VALUES ("Inbox")
            """)

    def _get_project_id(self, project_name: str = "Inbox") -> int:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                "SELECT id FROM projects WHERE name = ?", (project_name,)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
            raise ProjectNotFoundError(f"Project '{project_name}' not found")

    async def load(self) -> List[Dict]:
        try:
            return await asyncio.to_thread(self._read_db)
        except sqlite3.Error:
            return []

    def _read_db(self) -> List[Dict]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT tasks.*, projects.name AS project_name
                FROM tasks
                JOIN projects ON tasks.project_id = projects.id
            """)
            return [dict(row) for row in cursor.fetchall()]

    def validate_task(
        self, title: str, description: str, due_date: Optional[str] = None
    ) -> Optional[str]:
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
        project: str = "Inbox",
    ) -> Dict:
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
            project_id = await asyncio.to_thread(self._get_project_id, project)
            task["id"] = await asyncio.to_thread(self._insert_task, task, project_id)
            return task
        except sqlite3.Error as e:
            return {"error": f"Database error: {str(e)}"}

    def _insert_task(self, task: Dict, project_id: int) -> int:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (
                    title, description, completed, priority,
                    created_at, modified_at, due_date, project_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task["title"],
                    task["description"],
                    task["completed"],
                    task["priority"],
                    task["created_at"],
                    task["modified_at"],
                    task["due_date"],
                    project_id,
                ),
            )
            if cursor.lastrowid is None:
                raise sqlite3.Error("Failed to insert task: no row ID returned")
            return cursor.lastrowid

    async def toggle_completion(self, task_id: int) -> Dict:
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
        try:
            await self._get_task_by_id(task_id)
            return await asyncio.to_thread(self._delete_task, task_id)
        except (TaskNotFoundError, sqlite3.Error):
            return False

    def _delete_task(self, task_id: int) -> bool:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            return cursor.rowcount > 0

    async def _get_task_by_id(self, task_id: int) -> Dict:
        try:
            task = await asyncio.to_thread(self._get_task_by_id_sync, task_id)
            if task:
                return task
            raise TaskNotFoundError(f"Task with ID {task_id} not found")
        except sqlite3.Error as e:
            raise TaskNotFoundError(f"Database error: {str(e)}")

    def _get_task_by_id_sync(self, task_id: int) -> Optional[Dict]:
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
        if isinstance(priority, str):
            if priority.strip():
                try:
                    priority = Priority(priority.lower())
                except ValueError:
                    raise TaskValidationError(f"Invalid priority value: {priority}")
            else:
                priority = None

        try:
            return await asyncio.to_thread(
                self._search_tasks_sync, query, priority, completed
            )
        except sqlite3.Error:
            return []

    def _search_tasks_sync(
        self, query: str, priority: Optional[Priority], completed: Optional[bool]
    ) -> List[Dict]:
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
