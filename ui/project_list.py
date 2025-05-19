"""Project list widget implementation."""

from typing import Any, Dict, List

from textual.widgets import Label, ListItem, ListView

from database import db


class ProjectList(ListView):
    """List of projects."""

    def __init__(self):
        super().__init__()
        self.border_title = "Projects"
        self.id = "project-list"
        self.projects: List[Dict[str, Any]] = []

    async def on_mount(self) -> None:
        """Load projects when the list is mounted."""
        await self.load_projects()

    async def load_projects(self) -> None:
        """Load projects from the database."""
        try:
            rows = db.fetch_all("SELECT id, name FROM projects ORDER BY name")
            self.projects = rows
            self.refresh_projects()
        except Exception as e:
            self.notify(f"Failed to load projects: {e}", severity="error")

    def refresh_projects(self) -> None:
        """Refresh the project list view."""
        self.clear()
        for project in self.projects:
            self.append(ListItem(Label(project["name"].title(), classes="project-label")))

    async def add_project(self, name: str) -> bool:
        """Add a new project.

        Args:
            name: Name of the project to add

        Returns:
            bool: True if project was added, False otherwise
        """
        try:
            db.execute("INSERT INTO projects (name) VALUES (?)", (name,))
            await self.load_projects()
            return True
        except Exception as e:
            self.notify(f"Failed to add project: {e}", severity="error")
            return False
