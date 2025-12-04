"""
ui_new/icons.py

Description:
    * Simple icon drawing for navigation bar

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
import math


def draw_home_icon(surface, x, y, size, color, filled=False):
    """Draw a simple home icon - house outline."""
    # Single unified house shape
    half = size // 2
    
    # All points for the house outline
    points = [
        (x + half, y + 2),            # Roof peak
        (x + size - 2, y + half),     # Roof right
        (x + size - 2, y + size - 2), # Bottom right
        (x + 2, y + size - 2),        # Bottom left
        (x + 2, y + half),            # Roof left
    ]
    
    if filled:
        pygame.draw.polygon(surface, color, points)
    else:
        pygame.draw.polygon(surface, color, points, 2)


def draw_search_icon(surface, x, y, size, color, filled=False):
    """Draw a magnifying glass icon."""
    circle_r = size // 3
    circle_cx = x + circle_r + 2
    circle_cy = y + circle_r + 2
    
    pygame.draw.circle(surface, color, (circle_cx, circle_cy), circle_r, 0 if filled else 2)
    
    # Handle
    handle_start_x = circle_cx + int(circle_r * 0.7)
    handle_start_y = circle_cy + int(circle_r * 0.7)
    handle_end_x = x + size - 2
    handle_end_y = y + size - 2
    pygame.draw.line(surface, color, (handle_start_x, handle_start_y), 
                     (handle_end_x, handle_end_y), 3)


def draw_heart_icon(surface, x, y, size, color, filled=False):
    """Draw a smooth heart icon using parametric equation."""
    cx = x + size // 2
    cy = y + size // 2 + 2
    scale = size / 30
    
    points = []
    # Parametric heart curve
    for i in range(100):
        t = i / 100 * 2 * math.pi
        # Heart parametric equations
        hx = 16 * (math.sin(t) ** 3)
        hy = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
        px = cx + int(hx * scale)
        py = cy - int(hy * scale)
        points.append((px, py))
    
    if len(points) > 2:
        if filled:
            pygame.draw.polygon(surface, color, points)
        else:
            pygame.draw.polygon(surface, color, points, 2)


def draw_create_icon(surface, x, y, size, color, filled=False):
    """Draw an AI sparkles icon - two sparkles."""
    # Large sparkle - center/bottom-left
    _draw_sparkle(surface, x + size * 0.4, y + size * 0.55, size * 0.45, color, filled)
    
    # Smaller sparkle - top-right
    _draw_sparkle(surface, x + size * 0.75, y + size * 0.22, size * 0.25, color, filled)


def _draw_sparkle(surface, cx, cy, size, color, filled=False):
    """Draw a 4-pointed star sparkle."""
    points = [
        (cx, cy - size),                        # Top
        (cx + size * 0.2, cy - size * 0.2),     # Top-right inner
        (cx + size, cy),                        # Right
        (cx + size * 0.2, cy + size * 0.2),     # Bottom-right inner
        (cx, cy + size),                        # Bottom
        (cx - size * 0.2, cy + size * 0.2),     # Bottom-left inner
        (cx - size, cy),                        # Left
        (cx - size * 0.2, cy - size * 0.2),     # Top-left inner
    ]
    
    points = [(int(px), int(py)) for px, py in points]
    
    if filled:
        pygame.draw.polygon(surface, color, points)
    else:
        pygame.draw.polygon(surface, color, points, 2)

def draw_settings_icon(surface, x, y, size, color, filled=False):
    """Draw a gear icon with subtle teeth."""
    cx = x + size // 2
    cy = y + size // 2
    outer_r = size // 2 - 1
    hole_r = size // 5
    num_teeth = 8
    tooth_depth = 3
    
    # Build gear shape with teeth
    points = []
    for i in range(num_teeth * 2):
        angle = i * math.pi / num_teeth - math.pi / 2
        if i % 2 == 0:
            r = outer_r
        else:
            r = outer_r - tooth_depth
        
        px = cx + int(r * math.cos(angle))
        py = cy + int(r * math.sin(angle))
        points.append((px, py))
    
    if filled:
        pygame.draw.polygon(surface, color, points)
        try:
            bg = surface.get_at((x - 1, y - 1))[:3]
        except:
            bg = (255, 255, 255)
        pygame.draw.circle(surface, bg, (cx, cy), hole_r)
    else:
        pygame.draw.polygon(surface, color, points, 2)
        pygame.draw.circle(surface, color, (cx, cy), hole_r, 2)


ICONS = {
    'Home': draw_home_icon,
    'Search': draw_search_icon,
    'Favorites': draw_heart_icon,
    'Create': draw_create_icon,
    'Settings': draw_settings_icon,
}


def draw_icon(surface, name, x, y, size, color, filled=False):
    """Draw an icon by name."""
    if name in ICONS:
        ICONS[name](surface, x, y, size, color, filled)