import asyncio
import json
from pathlib import Path
from typing import Dict, List


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

    def validate_task(self, title: str, description: str) -> bool:
        """Basic validation."""
        return bool(title.strip())

    async def add_task(self, title: str, description: str) -> Dict:
        """Async task addition."""
        task = {
            "id": self.next_id,
            "title": title,
            "description": description,
            "completed": False,
        }
        self.tasks.append(task)
        self.next_id += 1
        return task

    async def toggle_completion(self, task_id: int):
        """Toggle task completion status."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["completed"] = not task["completed"]
                break

    async def update_task(self, task_id: int, title: str, description: str) -> Dict:
        """Update an existing task."""
        for task in self.tasks:
            if task["id"] == task_id:
                task.update({"title": title, "description": description})
                return task
        raise ValueError("Task not found")

    async def delete_task(self, task_id: int) -> bool:
        """Remove a task by ID and return success status."""
        initial_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        return len(self.tasks) < initial_count  # True if deletion occurred
