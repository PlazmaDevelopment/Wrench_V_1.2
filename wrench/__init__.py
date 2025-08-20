"""
Wrench - Python Game Development Library

A comprehensive library for easy and fast 2D game development in Python.
"""

__version__ = "0.1.0"

# Import core modules
from .core.game import Game
from .core.scene import Scene
from .core.game_object import GameObject

# User-friendly aliases
create_scene = Scene.create
get_current_scene = Scene.get_current

# Basic drawing functions
from .graphics.draw import draw_rectangle, draw_circle, draw_text, draw_image

# Input management
from .input import on_key_press, on_mouse_click, on_update

# Camera control
from .camera import Camera

# AI module
from .ai import AI, create_ai

__all__ = [
    'Game', 'Scene', 'GameObject',
    'create_scene', 'get_current_scene',
    'draw_rectangle', 'draw_circle', 'draw_text', 'draw_image',
    'on_key_press', 'on_mouse_click', 'on_update',
    'Camera', 'AI', 'create_ai'
]
