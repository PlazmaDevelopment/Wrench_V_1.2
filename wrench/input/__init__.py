"""
Helper functions and classes for input management.
"""
from typing import Dict, List, Callable, Any, Optional
import pygame

# Event handlers
_key_handlers: Dict[int, List[Callable[[pygame.event.Event], None]]] = {}
_mouse_handlers: Dict[int, List[Callable[[pygame.event.Event], None]]] = {}
_update_handlers: List[Callable[[float], None]] = []

# Keyboard state
_key_state: Dict[int, bool] = {}
_mouse_state: Dict[int, bool] = {}
_mouse_pos: Tuple[int, int] = (0, 0)
_mouse_rel: Tuple[int, int] = (0, 0)

def on_key_press(key: int, callback: Callable[[], None]) -> None:
    """Registers a function to be called when the specified key is pressed."""
    if key not in _key_handlers:
        _key_handlers[key] = []
    _key_handlers[key].append(lambda e: callback())

def on_key_down(key: int, callback: Callable[[], None]) -> None:
    """Registers a function to be called when the specified key is pressed."""
    on_key_press(key, callback)

def on_key_up(key: int, callback: Callable[[], None]) -> None:
    """Registers a function to be called when the specified key is released."""
    if key not in _key_handlers:
        _key_handlers[key] = []
    _key_handlers[key].append(lambda e: callback() if e.type == pygame.KEYUP else None)

def on_mouse_click(button: int, callback: Callable[[int, int], None]) -> None:
    """Registers a handler for mouse clicks."""
    if button not in _mouse_handlers:
        _mouse_handlers[button] = []
    _mouse_handlers[button].append(lambda e, b=button: callback(e.pos[0], e.pos[1]) if e.type == pygame.MOUSEBUTTONDOWN and e.button == b else None)

def on_mouse_down(button: int, callback: Callable[[int, int], None]) -> None:
    """Registers a function to be called when a mouse button is pressed."""
    if button not in _mouse_handlers:
        _mouse_handlers[button] = []
    _mouse_handlers[button].append(lambda e, b=button: callback(e.pos[0], e.pos[1]) if e.type == pygame.MOUSEBUTTONDOWN and e.button == b else None)

def on_mouse_up(button: int, callback: Callable[[int, int], None]) -> None:
    """Registers a function to be called when a mouse button is released."""
    if button not in _mouse_handlers:
        _mouse_handlers[button] = []
    _mouse_handlers[button].append(lambda e, b=button: callback(e.pos[0], e.pos[1]) if e.type == pygame.MOUSEBUTTONUP and e.button == b else None)

def on_mouse_move(callback: Callable[[int, int, int, int], None]) -> None:
    """Registers a function to be called when the mouse moves."""
    if -1 not in _mouse_handlers:
        _mouse_handlers[-1] = []
    _mouse_handlers[-1].append(lambda e: callback(e.pos[0], e.pos[1], e.rel[0], e.rel[1]) if e.type == pygame.MOUSEMOTION else None)

def on_update(callback: Callable[[float], None]) -> None:
    """Registers a function to be called on each frame update."""
    _update_handlers.append(callback)

def get_key(key: int) -> bool:
    """Returns whether the specified key is currently pressed."""
    return _key_state.get(key, False)

def get_mouse_button(button: int) -> bool:
    """Returns whether the specified mouse button is currently pressed."""
    return _mouse_state.get(button, False)

def get_mouse_position() -> Tuple[int, int]:
    """Returns the current mouse position."""
    return _mouse_pos

def get_mouse_rel() -> Tuple[int, int]:
    """Returns the relative mouse movement since the last call."""
    return _mouse_rel

def _handle_event(event: pygame.event.Event) -> None:
    """Handles incoming events."""
    global _mouse_pos, _mouse_rel
    
    # Klavye olayları
    if event.type == pygame.KEYDOWN:
        _key_state[event.key] = True
        if event.key in _key_handlers:
            for handler in _key_handlers[event.key]:
                handler(event)
    
    elif event.type == pygame.KEYUP:
        _key_state[event.key] = False
        if event.key in _key_handlers:
            for handler in _key_handlers[event.key]:
                handler(event)
    
    # Fare olayları
    elif event.type == pygame.MOUSEBUTTONDOWN:
        _mouse_state[event.button] = True
        if event.button in _mouse_handlers:
            for handler in _mouse_handlers[event.button]:
                handler(event)
    
    elif event.type == pygame.MOUSEBUTTONUP:
        _mouse_state[event.button] = False
        if event.button in _mouse_handlers:
            for handler in _mouse_handlers[event.button]:
                handler(event)
    
    elif event.type == pygame.MOUSEMOTION:
        _mouse_pos = event.pos
        _mouse_rel = event.rel
        if -1 in _mouse_handlers:  # Genel fare hareket işleyicileri
            for handler in _mouse_handlers[-1]:
                handler(event)

def _update(delta_time: float) -> None:
    """Calls all update handlers."""
    for handler in _update_handlers:
        handler(delta_time)

# Convenience functions for keyboard shortcuts
KEY_ESCAPE = pygame.K_ESCAPE
KEY_SPACE = pygame.K_SPACE
KEY_RETURN = pygame.K_RETURN
KEY_UP = pygame.K_UP
KEY_DOWN = pygame.K_DOWN
KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT

# Fare düğmeleri
MOUSE_LEFT = 1
MOUSE_MIDDLE = 2
MOUSE_RIGHT = 3
MOUSE_WHEEL_UP = 4
MOUSE_WHEEL_DOWN = 5

__all__ = [
    'on_key_press', 'on_key_down', 'on_key_up',
    'on_mouse_click', 'on_mouse_down', 'on_mouse_up', 'on_mouse_move',
    'on_update', 'get_key', 'get_mouse_button', 'get_mouse_position',
    'get_mouse_rel', 'KEY_ESCAPE', 'KEY_SPACE', 'KEY_RETURN',
    'KEY_UP', 'KEY_DOWN', 'KEY_LEFT', 'KEY_RIGHT',
    'MOUSE_LEFT', 'MOUSE_MIDDLE', 'MOUSE_RIGHT',
    'MOUSE_WHEEL_UP', 'MOUSE_WHEEL_DOWN'
]
