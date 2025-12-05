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
    half = size // 2
    
    points = [
        (x + half, y + 2),
        (x + size - 2, y + half),
        (x + size - 2, y + size - 2),
        (x + 2, y + size - 2),
        (x + 2, y + half),
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
    for i in range(100):
        t = i / 100 * 2 * math.pi
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


def draw_my_kitchen_icon(surface, x, y, size, color, filled=False):
    """Draw a chef's hat icon for My Kitchen - simple polygon approach."""
    # Scale everything to size
    s = size / 28.0
    
    # Define the hat shape as points (based on 28x28 grid)
    # Starting from bottom-left, going clockwise
    hat_outline = [
        # Bottom band - left side
        (6, 26),    # Bottom left
        (6, 20),    # Band top left
        # Left side going up
        (6, 16),    # Left side
        # Top cloud bumps (left bump)
        (4, 14),
        (3, 11),
        (4, 8),
        (6, 6),
        # Center bump (taller)
        (9, 4),
        (12, 2),
        (14, 2),
        (16, 2),
        (19, 4),
        # Right bump
        (22, 6),
        (24, 8),
        (25, 11),
        (24, 14),
        # Right side going down
        (22, 16),
        (22, 20),   # Band top right
        (22, 26),   # Bottom right
    ]
    
    # Scale and offset points
    points = [(x + int(px * s), y + int(py * s)) for px, py in hat_outline]
    
    thickness = 2
    
    if filled:
        pygame.draw.polygon(surface, color, points)
    else:
        pygame.draw.polygon(surface, color, points, thickness)
        
        # Draw the band separator line
        band_y = y + int(20 * s)
        pygame.draw.line(surface, color, (x + int(6 * s), band_y), (x + int(22 * s), band_y), thickness)
        
        # Draw vertical lines in band
        band_top = y + int(20 * s)
        band_bottom = y + int(26 * s)
        for i in range(1, 4):
            lx = x + int((6 + i * 4) * s)
            pygame.draw.line(surface, color, (lx, band_top + 2), (lx, band_bottom - 2), thickness)


def draw_create_icon(surface, x, y, size, color, filled=False):
    """Draw an AI sparkles icon - two sparkles."""
    _draw_sparkle(surface, x + size * 0.4, y + size * 0.55, size * 0.45, color, filled)
    _draw_sparkle(surface, x + size * 0.75, y + size * 0.22, size * 0.25, color, filled)


def _draw_sparkle(surface, cx, cy, size, color, filled=False):
    """Draw a 4-pointed star sparkle."""
    points = [
        (cx, cy - size),
        (cx + size * 0.2, cy - size * 0.2),
        (cx + size, cy),
        (cx + size * 0.2, cy + size * 0.2),
        (cx, cy + size),
        (cx - size * 0.2, cy + size * 0.2),
        (cx - size, cy),
        (cx - size * 0.2, cy - size * 0.2),
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
    'My Kitchen': draw_my_kitchen_icon,
    'Create': draw_create_icon,
    'Settings': draw_settings_icon,
}


def draw_icon(surface, name, x, y, size, color, filled=False):
    """Draw an icon by name."""
    if name in ICONS:
        ICONS[name](surface, x, y, size, color, filled)