"""
Classes and functions for AI and behavior management.
"""
from typing import Dict, List, Optional, Tuple, Any, Callable
import random
import math
from ..core.game_object import GameObject

class AI:
    """Base AI class that provides different behavior templates."""
    
    def __init__(self, behavior_type: str = "idle", **kwargs):
        """Creates a new AI instance.
        
        Args:
            behavior_type: AI behavior type (idle, patrol, chase, wander, flee)
            **kwargs: Behavior-specific parameters
        """
        self.behavior_type = behavior_type
        self.target = None
        self.speed = kwargs.get('speed', 100.0)
        self.range = kwargs.get('range', 300.0)
        self.detection_range = kwargs.get('detection_range', 200.0)
        self.patrol_points = kwargs.get('patrol_points', [])
        self.current_patrol_index = 0
        self.wander_radius = kwargs.get('wander_radius', 50.0)
        self.wander_distance = kwargs.get('wander_distance', 100.0)
        self.wander_jitter = kwargs.get('wander_jitter', 10.0)
        self.wander_target = (0, 0)
        self.flee_threshold = kwargs.get('flee_threshold', 100.0)
        self.obstacles = kwargs.get('obstacles', [])
        self.avoid_radius = kwargs.get('avoid_radius', 50.0)
    
    def update(self, delta_time: float, owner: GameObject) -> None:
        """Updates the AI behavior."""
        if not hasattr(owner, 'position'):
            return
            
        if self.behavior_type == "idle":
            self._update_idle(delta_time, owner)
        elif self.behavior_type == "patrol":
            self._update_patrol(delta_time, owner)
        elif self.behavior_type == "chase":
            self._update_chase(delta_time, owner)
        elif self.behavior_type == "wander":
            self._update_wander(delta_time, owner)
        elif self.behavior_type == "flee":
            self._update_flee(delta_time, owner)
    
    def _update_idle(self, delta_time: float, owner: GameObject) -> None:
        """Idle behavior - does nothing."""
        pass  # Hiçbir şey yapma, olduğu yerde kalsın
    
    def _update_patrol(self, delta_time: float, owner: GameObject) -> None:
        """Patrol behavior - moves between specified points."""
        if not self.patrol_points:
            return
            
        target_pos = self.patrol_points[self.current_patrol_index]
        direction = pygame.Vector2(target_pos) - pygame.Vector2(owner.position)
        
        if direction.length() < 10.0:  # Hedefe ulaşıldı
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)
            target_pos = self.patrol_points[self.current_patrol_index]
            direction = pygame.Vector2(target_pos) - pygame.Vector2(owner.position)
        
        if direction.length() > 0:
            direction = direction.normalize()
            new_pos = pygame.Vector2(owner.position) + direction * self.speed * delta_time
            owner.position = (new_pos.x, new_pos.y)
    
    def _update_chase(self, delta_time: float, owner: GameObject) -> None:
        """Chase behavior - follows a target."""
        if not self.target or not hasattr(self.target, 'position'):
            return
            
        direction = pygame.Vector2(self.target.position) - pygame.Vector2(owner.position)
        distance = direction.length()
        
        if distance > self.range or distance > self.detection_range:
            return  # Hedef menzil dışında
            
        if distance > 0:
            direction = direction.normalize()
            new_pos = pygame.Vector2(owner.position) + direction * self.speed * delta_time
            owner.position = (new_pos.x, new_pos.y)
    
    def _update_wander(self, delta_time: float, owner: GameObject) -> None:
        """Wander behavior - moves randomly."""
        # Change direction randomly
        self.wander_target = (
            self.wander_target[0] + random.uniform(-1, 1) * self.wander_jitter,
            self.wander_target[1] + random.uniform(-1, 1) * self.wander_jitter
        )
        # Normalize the target
        if self.wander_target != (0, 0):
            wander_force = pygame.Vector2(self.wander_target).normalize() * self.wander_radius
        else:
            wander_force = pygame.Vector2(0, 0)
        # Add a forward force
        forward = pygame.Vector2(1, 0)  # Default forward direction
        if hasattr(owner, 'rotation'):
            rad = math.radians(owner.rotation)
            forward = pygame.Vector2(math.cos(rad), math.sin(rad))
        
        target = pygame.Vector2(owner.position) + forward * self.wander_distance + wander_force
        direction = target - pygame.Vector2(owner.position)
        
        if direction.length() > 0:
            direction = direction.normalize()
            new_pos = pygame.Vector2(owner.position) + direction * self.speed * delta_time
            owner.position = (new_pos.x, new_pos.y)
            
            # Rotate toward target
            if hasattr(owner, 'rotation'):
                target_angle = math.degrees(math.atan2(direction.y, direction.x))
                owner.rotation = target_angle
    
    def _update_flee(self, delta_time: float, owner: GameObject) -> None:
        """Flee behavior - runs away from target."""
        if not self.target or not hasattr(self.target, 'position'):
            return
            
        direction = pygame.Vector2(owner.position) - pygame.Vector2(self.target.position)
        distance = direction.length()
        
        if distance < self.flee_threshold and distance > 0:
            direction = direction.normalize()
            new_pos = pygame.Vector2(owner.position) + direction * self.speed * delta_time
            owner.position = (new_pos.x, new_pos.y)
    
    def avoid_obstacles(self, owner: GameObject) -> pygame.Vector2:
        """Avoidance behavior - steers away from obstacles."""
        avoidance = pygame.Vector2(0, 0)
        
        for obstacle in self.obstacles:
            if not hasattr(obstacle, 'position'):
                continue
                
            to_obstacle = pygame.Vector2(obstacle.position) - pygame.Vector2(owner.position)
            distance = to_obstacle.length()
            
            if distance < self.avoid_radius and distance > 0:
                # Increase avoidance force as distance decreases
                strength = 1.0 - (distance / self.avoid_radius)
                avoidance -= to_obstacle.normalize() * strength
        
        return avoidance

def create_ai(behavior_type: str = "idle", **kwargs) -> AI:
    """Creates a new AI instance."""
    return AI(behavior_type, **kwargs)

# Predefined AI types
AI_TYPES = {
    "idle": "Does nothing",
    "patrol": "Moves between points",
    "chase": "Chases a target",
    "wander": "Wanders randomly",
    "flee": "Runs away from target"
}

__all__ = ['AI', 'create_ai', 'AI_TYPES']
