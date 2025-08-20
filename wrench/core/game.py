"""
Wrench Game Engine - Main Game Class
"""
import pygame
import sys
from typing import Dict, Optional
from ..scene import Scene

class Game:
    """Main game class. Manages the game loop and core functionality."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, title: str = "Wrench Game", width: int = 800, height: int = 600):
        if hasattr(self, '_initialized'):
            return
            
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        
        self.clock = pygame.time.Clock()
        self.running = False
        self.scenes: Dict[str, Scene] = {}
        self.current_scene: Optional[Scene] = None
        self.fps = 60
        self._initialized = True
    
    def add_scene(self, name: str, scene: 'Scene') -> None:
        """Adds a new scene to the game."""
        self.scenes[name] = scene
        if self.current_scene is None:
            self.current_scene = scene
    
    def set_scene(self, name: str) -> None:
        """Changes the active scene."""
        if name in self.scenes:
            self.current_scene = self.scenes[name]
    
    def run(self) -> None:
        """Starts the game loop."""
        if not self.current_scene:
            raise RuntimeError("No scenes added to the game!")
            
        self.running = True
        
        while self.running:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Aktif sahneye olayı ilet
                if self.current_scene:
                    self.current_scene.handle_event(event)
            
            # Update
            delta_time = self.clock.tick(self.fps) / 1000.0  # Saniye cinsinden delta time
            
            if self.current_scene:
                self.current_scene.update(delta_time)
                self.current_scene.draw(self.screen)
            
            # Update the display
            pygame.display.flip()
        
        self.quit()
    
    def quit(self) -> None:
        """Quits the game and cleans up resources."""
        pygame.quit()
        sys.exit()
