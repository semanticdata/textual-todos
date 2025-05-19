from datetime import datetime
from typing import Dict, List, Optional, Union

from config import DATE_FORMAT, MAX_DESCRIPTION_LENGTH, MAX_TITLE_LENGTH, Priority
from database import db


class TaskValidationError(Exception):
    """Raised when task validation fails."""

    pass


class TaskNotFoundError(Exception):
    """Raised when a task is not found in the database."""

    pass


class ProjectNotFoundError(Exception):
    """Raised when a project is not found in the database."""

    pass


class TaskStore:
    """Handles task-related database operations."""

    @staticmethod
    def _format_task(row: Dict) -> Dict:
        """Format task data from database row to dict."""
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"] or "",
            "completed": bool(row["completed"]),
            "priority": row["priority"],
            "created_at": row["created_at"],
            "modified_at": row["modified_at"],
            "due_date": row["due_date"],
            "project_id": row["project_id"],
            "project_name": row.get("project_name", ""),
        }

    @staticmethod
    def validate_task(title: str, description: str = "", due_date: Optional[str] = None) -> Optional[str]:
        """Validate task data.

        Args:
            title: Task title
            description: Task description
            due_date: Due date in YYYY-MM-DD format

        Returns:
            Optional error message if validation fails, None otherwise
        """
        if not title.strip():
            return "Title cannot be empty"
        if len(title) > MAX_TITLE_LENGTH:
            return f"Title cannot exceed {MAX_TITLE_LENGTH} characters"
        if len(description) > MAX_DESCRIPTION_LENGTH:
            return f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters"
        if due_date:
            try:
                datetime.strptime(due_date, DATE_FORMAT)
            except ValueError:
                return f"Due date must be in {DATE_FORMAT} format"
        return None

    async def load(self) -> List[Dict]:
        """Load all tasks from the database.

        Returns:
            List of tasks as dictionaries
        """
        query = """
            SELECT tasks.*, projects.name AS project_name
            FROM tasks
            JOIN projects ON tasks.project_id = projects.id
            ORDER BY tasks.completed, tasks.due_date, tasks.created_at
        """
        rows = db.fetch_all(query)
        return [self._format_task(row) for row in rows]

    async def _get_project_id(self, project_name: str) -> int:
        """Get project ID by name.

        Args:
            project_name: Name of the project

        Returns:
            Project ID

        Raises:
            ProjectNotFoundError: If project is not found
        """
        query = "SELECT id FROM projects WHERE name = ?"
        project = db.fetch_one(query, (project_name,))
        if not project:
            raise ProjectNotFoundError(f"Project '{project_name}' not found")
        return project["id"]

    async def add_task(
        self,
        title: str,
        description: str = "",
        priority: Union[Priority, str] = Priority.MEDIUM,
        due_date: Optional[str] = None,
        project: str = "Inbox",
    ) -> Dict:
        """Add a new task.

        Args:
            title: Task title
            description: Task description
            priority: Task priority (low/medium/high or Priority enum)
            due_date: Due date in YYYY-MM-DD format
            project: Project name

        Returns:
            Dictionary with task data or error message
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
            project_id = await self._get_project_id(project)
            task_id = db.execute(
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
            ).lastrowid

            if task_id is None:
                return {"error": "Failed to insert task: no row ID returned"}

            task["id"] = task_id
            task["project_id"] = project_id
            task["project_name"] = project
            return task

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    async def toggle_completion(self, task_id: int) -> Dict:
        """Toggle task completion status.

        Args:
            task_id: ID of the task to toggle

        Returns:
            Updated task data or error message
        """
        try:
            task = await self.get_task_by_id(task_id)
            completed = not task["completed"]
            modified_at = datetime.now().isoformat()

            db.execute(
                "UPDATE tasks SET completed = ?, modified_at = ? WHERE id = ?",
                (completed, modified_at, task_id),
            )

            task["completed"] = completed
            task["modified_at"] = modified_at
            return task

        except TaskNotFoundError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    async def update_task(
        self,
        task_id: int,
        title: str,
        description: str,
        due_date: Optional[str] = None,
        priority: Optional[Union[Priority, str]] = None,
        project: Optional[str] = None,
    ) -> Dict:
        """Update an existing task.

        Args:
            task_id: ID of the task to update
            title: New title
            description: New description
            due_date: New due date in YYYY-MM-DD format
            priority: New priority (low/medium/high or Priority enum)
            project: New project name

        Returns:
            Updated task data or error message
        """
        try:
            task = await self.get_task_by_id(task_id)

            validation_error = self.validate_task(title, description, due_date)
            if validation_error:
                return {"error": validation_error}

            if priority is not None:
                if isinstance(priority, str):
                    try:
                        priority = Priority(priority.lower())
                    except ValueError:
                        return {"error": f"Invalid priority value: {priority}"}
                task["priority"] = priority.value

            task.update(
                {
                    "title": title.strip(),
                    "description": description.strip(),
                    "due_date": due_date if due_date and due_date.strip() else None,
                    "modified_at": datetime.now().isoformat(),
                }
            )

            project_id = None
            if project is not None and project != task.get("project_name"):
                project_id = await self._get_project_id(project)
                task["project_id"] = project_id
                task["project_name"] = project

            db.execute(
                """
                UPDATE tasks 
                SET title=?, description=?, due_date=?, modified_at=?, 
                    priority=?, project_id=COALESCE(?, project_id)
                WHERE id=?
                """,
                (
                    task["title"],
                    task["description"],
                    task["due_date"],
                    task["modified_at"],
                    task["priority"],
                    project_id,
                    task_id,
                ),
            )

            return task

        except (TaskNotFoundError, ProjectNotFoundError) as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    async def delete_task(self, task_id: int) -> bool:
        """Delete a task.

        Args:
            task_id: ID of the task to delete

        Returns:
            True if task was deleted, False otherwise
        """
        try:
            await self.get_task_by_id(task_id)  # Verify task exists
            db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            return True
        except (TaskNotFoundError, Exception):
            return False

    async def get_task_by_id(self, task_id: int) -> Dict:
        """Get a task by ID.

        Args:
            task_id: ID of the task to retrieve

        Returns:
            Task data as a dictionary

        Raises:
            TaskNotFoundError: If task is not found
        """
        query = """
            SELECT tasks.*, projects.name AS project_name
            FROM tasks
            JOIN projects ON tasks.project_id = projects.id
            WHERE tasks.id = ?
        """
        task = db.fetch_one(query, (task_id,))
        if not task:
            raise TaskNotFoundError(f"Task with ID {task_id} not found")
        return self._format_task(task)

    async def search_tasks(
        self,
        query: str = "",
        priority: Optional[Union[Priority, str]] = None,
        completed: Optional[bool] = None,
    ) -> List[Dict]:
        """Search for tasks with optional filters.

        Args:
            query: Search term to match in title or description
            priority: Filter by priority (low/medium/high or Priority enum)
            completed: Filter by completion status

        Returns:
            List of matching tasks
        """
        conditions = []
        params = []

        if query:
            conditions.append("(title LIKE ? OR description LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        if priority is not None:
            if isinstance(priority, str):
                try:
                    priority = Priority(priority.lower())
                except ValueError:
                    raise TaskValidationError(f"Invalid priority value: {priority}")
            conditions.append("priority = ?")
            params.append(priority.value)

        if completed is not None:
            conditions.append("completed = ?")
            params.append(completed)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT tasks.*, projects.name AS project_name
            FROM tasks
            JOIN projects ON tasks.project_id = projects.id
            {where_clause}
            ORDER BY tasks.completed, tasks.due_date, tasks.created_at
        """

        try:
            rows = db.fetch_all(query, tuple(params))
            return [self._format_task(row) for row in rows]
        except Exception as e:
            print(f"Error searching tasks: {e}")
            return []
