"""
Basic drawing functions.
"""
import pygame
import math
from typing import Tuple, List, Optional, Union

def draw_rectangle(surface: pygame.Surface, color: Tuple[int, int, int], 
                  rect: Tuple[float, float, float, float], 
                  width: int = 0, border_radius: int = 0) -> None:
    """Draws a rectangle.
    
    Args:
        surface: Surface to draw on
        color: Color (R, G, B)
        rect: (x, y, width, height)
        width: Line thickness (0 for filled rectangle)
        border_radius: Corner rounding radius
    """
    pygame.draw.rect(surface, color, rect, width, border_radius)

def draw_circle(surface: pygame.Surface, color: Tuple[int, int, int], 
               center: Tuple[float, float], radius: float, 
               width: int = 0) -> None:
    """Draws a circle."""
    pygame.draw.circle(surface, color, (int(center[0]), int(center[1])), 
                      int(radius), width)

def draw_text(surface: pygame.Surface, text: str, 
             position: Tuple[float, float], 
             font_name: str = "Arial", font_size: int = 24, 
             color: Tuple[int, int, int] = (255, 255, 255),
             antialias: bool = True) -> None:
    """Draws text."""
    font = pygame.font.SysFont(font_name, font_size)
    text_surface = font.render(text, antialias, color)
    surface.blit(text_surface, position)

def draw_image(surface: pygame.Surface, image_path: str, 
              position: Tuple[float, float], 
              size: Optional[Tuple[float, float]] = None) -> None:
    """Draws an image."""
    try:
        image = pygame.image.load(image_path)
        if size:
            image = pygame.transform.scale(image, (int(size[0]), int(size[1])))
        surface.blit(image, position)
    except pygame.error as e:
        print(f"Failed to load image: {e}")

def draw_line(surface: pygame.Surface, color: Tuple[int, int, int], 
             start_pos: Tuple[float, float], end_pos: Tuple[float, float], 
             width: int = 1) -> None:
    """Draws a line."""
    pygame.draw.line(surface, color, start_pos, end_pos, width)

def draw_polygon(surface: pygame.Surface, color: Tuple[int, int, int], 
                points: List[Tuple[float, float]], width: int = 0) -> None:
    """Draws a polygon."""
    pygame.draw.polygon(surface, color, points, width)

def draw_ellipse(surface: pygame.Surface, color: Tuple[int, int, int], 
                rect: Tuple[float, float, float, float], 
                width: int = 0) -> None:
    """Draws an ellipse."""
    pygame.draw.ellipse(surface, color, rect, width)

def draw_arc(surface: pygame.Surface, color: Tuple[int, int, int], 
            rect: Tuple[float, float, float, float], 
            start_angle: float, stop_angle: float, 
            width: int = 1) -> None:
    """Draws an arc."""
    pygame.draw.arc(surface, color, rect, start_angle, stop_angle, width)

def draw_star(surface: pygame.Surface, color: Tuple[int, int, int], 
             center: Tuple[float, float], 
             outer_radius: float, inner_radius: float, 
             points: int = 5, width: int = 0) -> None:
    """Draws a star."""
    point_list = []
    for i in range(points * 2):
        radius = inner_radius if i % 2 else outer_radius
        angle = math.pi / points * i - math.pi / 2
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius
        point_list.append((x, y))
    
    if width == 0:
        pygame.draw.polygon(surface, color, point_list)
    else:
        pygame.draw.polygon(surface, color, point_list, width)

def draw_triangle(surface: pygame.Surface, color: Tuple[int, int, int], 
                 points: List[Tuple[float, float]], 
                 width: int = 0) -> None:
    """Draws a triangle."""
    if len(points) != 3:
        raise ValueError("Exactly 3 points are required to draw a triangle.")
    draw_polygon(surface, color, points, width)

def draw_regular_polygon(surface: pygame.Surface, 
                       color: Tuple[int, int, int], 
                       center: Tuple[float, float], 
                       radius: float, point_count: int, 
                       width: int = 0) -> None:
    """Draws a regular polygon."""
    points = []
    for i in range(point_count):
        angle = 2 * math.pi * i / point_count - math.pi / 2
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius
        points.append((x, y))
    
    if width == 0:
        pygame.draw.polygon(surface, color, points)
    else:
        pygame.draw.polygon(surface, color, points, width)
