from typing import TypeVar, Type, Callable, Any, Optional, TypeVar
from functools import wraps
from textual.widget import Widget

from .store import Store, StoreUpdate

T = TypeVar('T', bound=Widget)

def connect(store_selector: Callable[['Store'], Any] = None):
    """Decorator to connect a widget to the store.
    
    Args:
        store_selector: Function that selects data from the store
    """
    def decorator(widget_class: Type[T]) -> Type[T]:
        # Store the original __init__ and on_mount methods
        original_init = widget_class.__init__
        original_on_mount = getattr(widget_class, 'on_mount', None)
        original_on_unmount = getattr(widget_class, 'on_unmount', None)
        
        def __init__(self, *args, **kwargs):
            # Call the original __init__
            original_init(self, *args, **kwargs)
            
            # Initialize state
            self._store = None
            self._unsubscribe = None
            self._mapped_state = None
        
        async def on_mount(self):
            # Get the store from the app
            self._store = self.app.query_one(Store)
            
            # Subscribe to store updates
            self._unsubscribe = self._store.subscribe(self._on_store_update)
            
            # Call the original on_mount if it exists
            if original_on_mount:
                if hasattr(original_on_mount, '__await__'):
                    await original_on_mount(self)
                else:
                    original_on_mount(self)
            
            # Initial state update
            await self._on_store_update(None)
        
        async def on_unmount(self):
            # Unsubscribe from store updates
            if self._unsubscribe:
                self._unsubscribe()
                self._unsubscribe = None
            
            # Call the original on_unmount if it exists
            if original_on_unmount:
                if hasattr(original_on_unmount, '__await__'):
                    await original_on_unmount(self)
                else:
                    original_on_unmount(self)
        
        async def _on_store_update(self, update: Optional[StoreUpdate]) -> None:
            """Handle store updates."""
            if not self._store:
                return
                
            # Get the selected data from the store
            selected_data = store_selector(self._store) if store_selector else None
            
            # Skip if the data hasn't changed
            if hasattr(self, '_mapped_state') and self._mapped_state == selected_data:
                return
                
            # Update the mapped state
            self._mapped_state = selected_data
            
            # Call the map_state method if it exists
            if hasattr(self, 'map_state'):
                mapped = self.map_state(selected_data) if selected_data is not None else {}
                for key, value in mapped.items():
                    setattr(self, key, value)
        
        # Replace the methods
        widget_class.__init__ = __init__
        widget_class.on_mount = on_mount
        widget_class.on_unmount = on_unmount
        
        return widget_class
    
    # If store_selector is a class, it means the decorator was used without arguments
    if callable(store_selector) and not isinstance(store_selector, type):
        return decorator(store_selector)
    
    return decorator
