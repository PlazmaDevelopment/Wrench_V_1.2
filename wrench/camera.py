"""
Camera class used to control the viewable area in the game world.
"""
import pygame
from typing import Tuple, Optional, List

class Camera:
    """2D game camera class."""
    
    def __init__(self, width: int, height: int):
        """Creates a new camera.
        
        Args:
            width: Viewport width
            height: Viewport height
        """
        self.position = pygame.Vector2(0, 0)
        self.width = width
        self.height = height
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 4.0
        self.zoom_speed = 0.1
        self.target = None
        self.smooth_speed = 10.0
        self.bounds = None  # (min_x, min_y, max_x, max_y)
        self.shake_intensity = 0
        self.shake_duration = 0
        self.shake_timer = 0
    
    def update(self, delta_time: float) -> None:
        """Updates the camera."""
        # Target following
        if self.target:
            target_pos = pygame.Vector2(
                self.target.position[0] - self.width // 2,
                self.target.position[1] - self.height // 2
            )
            # Smooth following
            self.position += (target_pos - self.position) * (self.smooth_speed * delta_time)
        
        # Screen shake effect
        if self.shake_timer > 0:
            self.shake_timer -= delta_time
            self.position.x += (pygame.math.clamp(self.shake_intensity * (self.shake_timer / self.shake_duration), 0, self.shake_intensity) * 
                              (pygame.math.noise(pygame.time.get_ticks() * 0.01) * 2 - 1))
            self.position.y += (pygame.math.clamp(self.shake_intensity * (self.shake_timer / self.shake_duration), 0, self.shake_intensity) * 
                              (pygame.math.noise(pygame.time.get_ticks() * 0.01 + 1000) * 2 - 1))
        
        # Boundary check
        if self.bounds:
            min_x, min_y, max_x, max_y = self.bounds
            self.position.x = max(min_x, min(self.position.x, max_x - self.width))
            self.position.y = max(min_y, min(self.position.y, max_y - self.height))
    
    def apply(self, position: Tuple[float, float]) -> Tuple[float, float]:
        """Applies camera transformation to a position."""
        x = (position[0] - self.position.x) * self.zoom
        y = (position[1] - self.position.y) * self.zoom
        return x, y
    
    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """Applies camera transformation to a rectangle."""
        x, y = self.apply((rect.x, rect.y))
        return pygame.Rect(x, y, rect.width * self.zoom, rect.height * self.zoom)
    
    def zoom_in(self, amount: Optional[float] = None) -> None:
        """Zooms in."""
        if amount is None:
            amount = self.zoom_speed
        self.zoom = min(self.zoom + amount, self.max_zoom)
    
    def zoom_out(self, amount: Optional[float] = None) -> None:
        """Zooms out."""
        if amount is None:
            amount = self.zoom_speed
        self.zoom = max(self.zoom - amount, self.min_zoom)
    
    def set_zoom(self, value: float) -> None:
        """Sets the zoom level."""
        self.zoom = pygame.math.clamp(value, self.min_zoom, self.max_zoom)
    
    def follow(self, target) -> None:
        """Sets the target for the camera to follow."""
        self.target = target
    
    def set_bounds(self, min_x: float, min_y: float, max_x: float, max_y: float) -> None:
        """Sets the camera's movement boundaries."""
        self.bounds = (min_x, min_y, max_x, max_y)
    
    def shake(self, intensity: float, duration: float) -> None:
        """Applies a screen shake effect to the camera.
        
        Args:
            intensity: Shake intensity
            duration: Shake duration (in seconds)
        """
        self.shake_intensity = intensity
        self.shake_duration = duration
        self.shake_timer = duration
    
    def get_viewport(self) -> pygame.Rect:
        """Returns the camera's viewport."""
        return pygame.Rect(
            self.position.x,
            self.position.y,
            self.width / self.zoom,
            self.height / self.zoom
        )
    
    def is_visible(self, rect: pygame.Rect) -> bool:
        """Checks if the specified rectangle is within the camera's viewport."""
        viewport = self.get_viewport()
        return (rect.right > viewport.left and 
                rect.left < viewport.right and
                rect.bottom > viewport.top and 
                rect.top < viewport.bottom)
