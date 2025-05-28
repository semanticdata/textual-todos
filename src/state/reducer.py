from typing import Tuple, Optional, List, Dict

from .state import AppState
from .actions import Action, ActionType


def reducer(state: AppState, action: Action) -> Tuple[AppState, Optional[Dict]]:
    """Pure function that takes the current state and an action, and returns a new state.
    
    Args:
        state: The current application state
        action: The action to process
        
    Returns:
        A tuple containing:
        - The new state
        - An optional effect to be processed
    """
    if action.type == ActionType.ADD_TASK:
        # Add the new task to the list
        new_task = action.payload
        new_tasks = [*state.tasks, new_task]
        return state.copy(tasks=new_tasks), {"type": "save_tasks"}
        
    elif action.type == ActionType.UPDATE_TASK:
        # Update an existing task
        task_id = action.payload["task_id"]
        updates = action.payload["updates"]
        new_tasks = [
            {**task, **updates, "modified_at": updates.get("modified_at")}
            if task["id"] == task_id
            else task
            for task in state.tasks
        ]
        return state.copy(tasks=new_tasks), {"type": "save_tasks"}
        
    elif action.type == ActionType.DELETE_TASK:
        # Remove a task
        task_id = action.payload
        new_tasks = [t for t in state.tasks if t["id"] != task_id]
        # Clear current task if it was deleted
        new_current_id = (
            None if state.current_task_id == task_id 
            else state.current_task_id
        )
        return (
            state.copy(tasks=new_tasks, current_task_id=new_current_id),
            {"type": "save_tasks"}
        )
        
    elif action.type == ActionType.TOGGLE_TASK_COMPLETION:
        # Toggle completion status of a task
        task_id = action.payload
        new_tasks = [
            {
                **task,
                "completed": not task["completed"],
                "modified_at": None,  # This should be set by the effect
            }
            if task["id"] == task_id
            else task
            for task in state.tasks
        ]
        return state.copy(tasks=new_tasks), {
            "type": "toggle_task_completion",
            "task_id": task_id,
        }
        
    elif action.type == ActionType.SELECT_TASK:
        # Update the currently selected task
        return state.copy(current_task_id=action.payload), None
        
    elif action.type == ActionType.LOAD_TASKS:
        # Set loading state
        return state.copy(loading=True, error=None), {"type": "load_tasks"}
        
    elif action.type == ActionType.TASKS_LOADED:
        # Update tasks from the server
        tasks = action.payload
        # Preserve the current task selection if possible
        current_task_id = next(
            (t["id"] for t in tasks if state.current_task_id == t["id"]),
            tasks[0]["id"] if tasks else None
        )
        return state.copy(
            tasks=tasks,
            current_task_id=current_task_id,
            loading=False,
            error=None
        ), None
        
    elif action.type == ActionType.SET_THEME:
        # Update the theme
        return state.copy(theme=action.payload), None
        
    # If the action is not recognized, return the current state
    return state, None
