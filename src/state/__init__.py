"""State management for the Textual Todo application.

This package implements a Redux-like state management system for the Textual UI framework.
"""

from .actions import (
    Action,
    ActionType,
    add_task,
    update_task,
    delete_task,
    toggle_task_completion,
    select_task,
    load_tasks,
    tasks_loaded,
    set_theme,
)
from .state import AppState
from .store import Store, StoreUpdate
from .reducer import reducer
from .connect import connect

__all__ = [
    'Action',
    'ActionType',
    'add_task',
    'update_task',
    'delete_task',
    'toggle_task_completion',
    'select_task',
    'load_tasks',
    'tasks_loaded',
    'set_theme',
    'AppState',
    'Store',
    'StoreUpdate',
    'reducer',
    'connect',
]
