"""
Base class for game objects.
"""
from typing import Dict, Any, Optional, List, Tuple, Type, TypeVar, Generic
import pygame

T = TypeVar('T')

class Component:
    """Base class for components."""
    def __init__(self, game_object: 'GameObject'):
        self.game_object = game_object
        self.enabled = True
    
    def start(self) -> None:
        """Called when the component is first initialized."""
        pass
    
    def update(self, delta_time: float) -> None:
        """Her karede güncelleme için çağrılır."""
        pass
    
    def on_destroy(self) -> None:
        """Called when the component is being destroyed."""
        pass

class GameObject:
    """Base class for all objects in the game world."""
    
    def __init__(self, name: str = "GameObject", position: Tuple[float, float] = (0, 0)):
        self.name = name
        self.position = list(position)
        self.rotation = 0.0
        self.scale = [1.0, 1.0]
        self.z_index = 0
        self.components: List[Component] = []
        self.tags: List[str] = []
        self.initialized = False
    
    def add_component(self, component_type: Type[T], *args, **kwargs) -> T:
        """Adds a new component to this object."""
        component = component_type(self, *args, **kwargs)
        self.components.append(component)
        
        if self.initialized:
            component.start()
            
        return component
    
    def get_component(self, component_type: Type[T]) -> Optional[T]:
        """Returns the first component of the specified type."""
        for component in self.components:
            if isinstance(component, component_type):
                return component
        return None
    
    def get_components(self, component_type: Type[T]) -> List[T]:
        """Returns all components of the specified type."""
        return [c for c in self.components if isinstance(c, component_type)]
    
    def start(self) -> None:
        """Called when the object is first initialized."""
        for component in self.components:
            component.start()
    
    def update(self, delta_time: float) -> None:
        """Her karede güncelleme için çağrılır."""
        for component in self.components:
            if hasattr(component, 'update') and component.enabled:
                component.update(delta_time)
    
    def draw(self, screen: pygame.Surface) -> None:
        """Renders the object to the screen."""
        for component in self.components:
            if hasattr(component, 'draw') and component.enabled:
                component.draw(screen)
    
    def on_destroy(self) -> None:
        """Called when the object is being destroyed."""
        for component in self.components:
            if hasattr(component, 'on_destroy'):
                component.on_destroy()
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handles incoming events."""
        for component in self.components:
            if hasattr(component, 'handle_event') and component.enabled:
                component.handle_event(event)
    
    def has_tag(self, tag: str) -> bool:
        """Checks if the object has the specified tag."""
        return tag in self.tags
    
    def add_tag(self, tag: str) -> None:
        """Adds a new tag to the object."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Removes a tag from the object."""
        if tag in self.tags:
            self.tags.remove(tag)
