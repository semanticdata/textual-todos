from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass
from textual.reactive import reactive
from textual.message import Message, MessageTarget
from textual.widget import Widget

from .state import AppState
from .actions import Action, ActionType
from .reducer import reducer
from models import TaskStore


class StoreUpdate(Message):
    """Message sent when the store's state changes."""
    def __init__(self, store: 'Store', previous_state: AppState) -> None:
        self.store = store
        self.previous_state = previous_state
        self.new_state = store.state
        super().__init__()


class Store(Widget):
    """Centralized store for application state management.
    
    This widget manages the application state and dispatches actions
    to update it. Other widgets can subscribe to state changes.
    """
    
    def __init__(self) -> None:
        super().__init__()
        self._state = AppState()
        self.task_store = TaskStore()
        self._listeners = []
    
    @property
    def state(self) -> AppState:
        """Get the current state."""
        return self._state
    
    async def dispatch(self, action: Action) -> None:
        """Dispatch an action to update the state.
        
        Args:
            action: The action to dispatch
        """
        # Get the current state
        current_state = self._state
        
        # Reduce the state
        new_state, effect = reducer(current_state, action)
        
        # Update the state
        self._state = new_state
        
        # Notify listeners of the state change
        await self.emit(StoreUpdate(self, current_state))
        
        # Handle any side effects
        if effect:
            await self._handle_effect(effect)
    
    async def _handle_effect(self, effect: Dict[str, Any]) -> None:
        """Handle side effects from the reducer."""
        effect_type = effect["type"]
        
        if effect_type == "load_tasks":
            # Load tasks from the database
            tasks = await self.task_store.load()
            await self.dispatch(Action(ActionType.TASKS_LOADED, tasks))
            
        elif effect_type == "save_tasks":
            # Save tasks to the database
            # Note: In a real app, you would implement this
            pass
            
        elif effect_type == "toggle_task_completion":
            # Toggle task completion in the database
            task_id = effect["task_id"]
            await self.task_store.toggle_completion(task_id)
            
    def subscribe(self, callback: Callable[[StoreUpdate], None]) -> Callable[[], None]:
        """Subscribe to state changes.
        
        Args:
            callback: Function to call when the state changes
            
        Returns:
            A function to unsubscribe
        """
        # Store the callback
        self._listeners.append(callback)
        
        # Return an unsubscribe function
        def unsubscribe():
            if callback in self._listeners:
                self._listeners.remove(callback)
                
        return unsubscribe
    
    async def emit(self, message: StoreUpdate) -> None:
        """Eit a message to all listeners."""
        # Call all listeners
        for callback in self._listeners:
            # Check if the callback is a coroutine
            if hasattr(callback, "__await__"):
                await callback(message)
            else:
                callback(message)
