"""
Core scene management class.
"""
from typing import List, Dict, Optional, Type, Any
import pygame
from .game_object import GameObject

class Scene:
    """Base class representing game scenes."""
    
    _current_scene = None
    
    def __init__(self, name: str):
        self.name = name
        self.game_objects: List[GameObject] = []
        self._game_objects_to_add = []
        self._game_objects_to_remove = []
        self.initialized = False
    
    @classmethod
    def create(cls, name: str) -> 'Scene':
        """Creates a new scene."""
        return cls(name)
    
    @classmethod
    def get_current(cls) -> Optional['Scene']:
        """Returns the current active scene."""
        return cls._current_scene
    
    def add_game_object(self, game_object: GameObject) -> None:
        """Adds a new game object to the scene."""
        self._game_objects_to_add.append(game_object)
    
    def remove_game_object(self, game_object: GameObject) -> None:
        """Removes a game object from the scene."""
        self._game_objects_to_remove.append(game_object)
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handles incoming events."""
        for game_object in self.game_objects:
            if hasattr(game_object, 'handle_event'):
                game_object.handle_event(event)
    
    def update(self, delta_time: float) -> None:
        """Updates the scene."""
        # Add new objects
        for game_object in self._game_objects_to_add:
            if game_object not in self.game_objects:
                self.game_objects.append(game_object)
                if not game_object.initialized:
                    game_object.start()
                    game_object.initialized = True
        self._game_objects_to_add.clear()
        
        # Remove objects marked for deletion
        for game_object in self._game_objects_to_remove:
            if game_object in self.game_objects:
                if hasattr(game_object, 'on_destroy'):
                    game_object.on_destroy()
                self.game_objects.remove(game_object)
        self._game_objects_to_remove.clear()
        
        # Update all objects
        for game_object in self.game_objects:
            if hasattr(game_object, 'update'):
                game_object.update(delta_time)
    
    def draw(self, screen: pygame.Surface) -> None:
        """Renders the scene."""
        screen.fill((0, 0, 0))  # Black background
        screen.fill((0, 0, 0))  # Siyah arka plan
        
        # Tüm nesneleri çiz
        for game_object in sorted(self.game_objects, key=lambda x: x.z_index):
            if hasattr(game_object, 'draw'):
                game_object.draw(screen)
    
    def on_enter(self) -> None:
        """Called when the scene becomes active."""
        Scene._current_scene = self
        if not self.initialized:
            self.initialized = True
            self.start()
    
    def on_exit(self) -> None:
        """Called when the scene is being replaced."""
        pass
    
    def start(self) -> None:
        """Called when the scene is first initialized."""
        pass
