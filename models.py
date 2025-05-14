import asyncio
import json
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
    def __init__(self, path: str = "todos.json"):
        self.path = Path(path)
        self.tasks: List[Dict] = []
        self.next_id = 1

    async def load(self) -> List[Dict]:
        """Load tasks from JSON file."""
        try:
            data = await asyncio.to_thread(self._read_file)
            if data.strip():
                loaded = json.loads(data)
                if isinstance(loaded, dict) and "version" in loaded:  # New schema
                    self.tasks = loaded["tasks"]
                else:  # Legacy schema
                    self.tasks = loaded
                self.next_id = max((t["id"] for t in self.tasks), default=0) + 1
        except (FileNotFoundError, json.JSONDecodeError):
            self.tasks = []
        return self.tasks

    def _read_file(self) -> str:
        """Synchronous file read operation."""
        with open(self.path, "r") as f:
            return f.read()

    async def save(self):
        """Save tasks with versioned schema."""
        data = {"version": "1.0", "tasks": self.tasks}
        await asyncio.to_thread(self._write_file, json.dumps(data, indent=2))

    def _write_file(self, content: str) -> None:
        """Synchronous file write operation."""
        with open(self.path, "w") as f:
            f.write(content)

    def validate_task(self, title: str, description: str) -> Optional[str]:
        """Enhanced validation with specific error messages.
        Returns None if validation passes, or error message if validation fails.
        """
        if not title.strip():
            return "Title cannot be empty"
        if len(title) > 100:
            return "Title cannot exceed 100 characters"
        if len(description) > 500:
            return "Description cannot exceed 500 characters"
        return None

    async def add_task(
        self,
        title: str,
        description: str,
        priority: Union[Priority, str] = Priority.MEDIUM,
    ) -> Dict:
        """Async task addition with priority and creation date.
        Returns a dictionary with either the created task or an error message.
        """
        if isinstance(priority, str):
            try:
                priority = Priority(priority.lower())
            except ValueError:
                return {"error": f"Invalid priority value: {priority}"}

        validation_error = self.validate_task(title, description)
        if validation_error:
            return {"error": validation_error}

        # Only create and save task if validation passes
        task = {
            "id": self.next_id,
            "title": title,
            "description": description,
            "completed": False,
            "priority": priority.value,
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
        }
        self.tasks.append(task)
        self.next_id += 1
        await self.save()
        return task

    async def toggle_completion(self, task_id: int) -> Dict:
        """Toggle task completion status with modification tracking."""
        task = await self._get_task_by_id(task_id)
        task["completed"] = not task["completed"]
        task["modified_at"] = datetime.now().isoformat()
        await self.save()
        return task

    async def update_task(
        self,
        task_id: int,
        title: str,
        description: str,
        priority: Optional[Union[Priority, str]] = None,
    ) -> Dict:
        """Update an existing task with validation and modification tracking.
        Returns a dictionary with either the updated task or an error message.
        """
        try:
            task = await self._get_task_by_id(task_id)
        except TaskNotFoundError as e:
            return {"error": str(e)}

        validation_error = self.validate_task(title, description)
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
            }
        )

        if priority is not None:
            task["priority"] = priority.value

        await self.save()
        return task

    async def delete_task(self, task_id: int) -> bool:
        """Remove a task by ID and return success status."""
        await self._get_task_by_id(task_id)  # Verify task exists
        initial_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        await self.save()
        return len(self.tasks) < initial_count

    async def _get_task_by_id(self, task_id: int) -> Dict:
        """Helper method to get task by ID or raise error."""
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        raise TaskNotFoundError(f"Task with ID {task_id} not found")

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

        results = self.tasks

        if query:
            query = query.lower()
            results = [
                task
                for task in results
                if query in task["title"].lower()
                or query in task["description"].lower()
            ]

        if priority:
            results = [task for task in results if task["priority"] == priority.value]

        if completed is not None:
            results = [task for task in results if task["completed"] == completed]

        return results
