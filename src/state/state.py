from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AppState:
    """Application state container.
    
    This class holds the entire application state and provides methods to create
    new immutable copies of the state with updates applied.
    """
    tasks: List[Dict] = field(default_factory=list)
    current_task_id: Optional[int] = None
    theme: str = "dark"
    loading: bool = False
    error: Optional[str] = None

    @property
    def current_task(self) -> Optional[Dict]:
        """Get the currently selected task."""
        if self.current_task_id is None:
            return None
        return next((t for t in self.tasks if t["id"] == self.current_task_id), None)

    def copy(self, **changes) -> 'AppState':
        """Create a new state with the given changes applied."""
        return AppState(
            tasks=changes.get('tasks', self.tasks.copy()),
            current_task_id=changes.get('current_task_id', self.current_task_id),
            theme=changes.get('theme', self.theme),
            loading=changes.get('loading', self.loading),
            error=changes.get('error', self.error),
        )
