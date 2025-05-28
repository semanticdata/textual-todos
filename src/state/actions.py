from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from models import TaskStore


class ActionType(Enum):
    """Type of actions that can be dispatched."""
    ADD_TASK = auto()
    UPDATE_TASK = auto()
    DELETE_TASK = auto()
    TOGGLE_TASK_COMPLETION = auto()
    SELECT_TASK = auto()
    LOAD_TASKS = auto()
    TASKS_LOADED = auto()
    SET_THEME = auto()


@dataclass(frozen=True)
class Action:
    """Action object that represents a state change request."""
    type: ActionType
    payload: Any = None


# Action Creators
def add_task(task_data: Dict) -> Action:
    """Create an action to add a new task."""
    return Action(ActionType.ADD_TASK, task_data)

def update_task(task_id: int, updates: Dict) -> Action:
    """Create an action to update an existing task."""
    return Action(ActionType.UPDATE_TASK, {"task_id": task_id, "updates": updates})

def delete_task(task_id: int) -> Action:
    """Create an action to delete a task."""
    return Action(ActionType.DELETE_TASK, task_id)

def toggle_task_completion(task_id: int) -> Action:
    """Create an action to toggle a task's completion status."""
    return Action(ActionType.TOGGLE_TASK_COMPLETION, task_id)

def select_task(task_id: Optional[int]) -> Action:
    """Create an action to select a task."""
    return Action(ActionType.SELECT_TASK, task_id)

def load_tasks() -> Action:
    """Create an action to load tasks."""
    return Action(ActionType.LOAD_TASKS)

def tasks_loaded(tasks: List[Dict]) -> Action:
    """Create an action when tasks are loaded."""
    return Action(ActionType.TASKS_LOADED, tasks)

def set_theme(theme: str) -> Action:
    """Create an action to change the theme."""
    return Action(ActionType.SET_THEME, theme)
