"""
ui_new/views/my_kitchen_view.py

Description:
    * My Kitchen hub - access favorites, meal prep, grocery lists, and saved recipes

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *


class MyKitchenView:
    """Hub view for all personal recipe management."""
    
    def __init__(self, fonts):
        self.fonts = fonts
        self.favorites_manager = None
        self.recipes_manager = None
    
    def set_managers(self, favorites_manager, recipes_manager):
        """Set the data managers."""
        self.favorites_manager = favorites_manager
        self.recipes_manager = recipes_manager
    
    def draw(self, screen, state):
        self._draw_header(screen)
        self._draw_sections(screen)
    
    def _draw_header(self, screen):
        y = 25
        title = self.fonts['header'].render("My Kitchen", True, SOFT_BLACK)
        screen.blit(title, (40, y))
        
        subtitle = self.fonts['small'].render("Your recipes and meal planning", True, DARK_GRAY)
        screen.blit(subtitle, (40, y + 35))
    
    def _draw_sections(self, screen):
        sections = [
            {
                'id': 'favorites',
                'title': 'Favorites',
                'subtitle': self._get_favorites_subtitle(),
                'icon': 'heart',
                'color': (220, 80, 80),
            },
            {
                'id': 'meal_prep',
                'title': 'Meal Prep',
                'subtitle': 'Plan your weekly meals',
                'icon': 'calendar',
                'color': (80, 160, 220),
            },
            {
                'id': 'grocery_list',
                'title': 'Grocery Lists',
                'subtitle': 'Shopping lists from meal plans',
                'icon': 'cart',
                'color': (80, 180, 100),
            },
            {
                'id': 'saved_recipes',
                'title': 'Saved Creations',
                'subtitle': self._get_saved_subtitle(),
                'icon': 'sparkle',
                'color': (160, 100, 220),
            },
        ]
        
        y = 100
        card_height = 90
        card_margin = 15
        
        for section in sections:
            self._draw_section_card(screen, section, y)
            y += card_height + card_margin
    
    def _get_favorites_subtitle(self):
        if self.favorites_manager:
            count = len(self.favorites_manager.get_all())
            if count == 0:
                return "No favorites yet"
            elif count == 1:
                return "1 favorite recipe"
            else:
                return f"{count} favorite recipes"
        return "Your favorite recipes"
    
    def _get_saved_subtitle(self):
        if self.recipes_manager:
            count = len(self.recipes_manager.get_all())
            if count == 0:
                return "No saved creations yet"
            elif count == 1:
                return "1 saved creation"
            else:
                return f"{count} saved creations"
        return "AI-generated recipes"
    
    def _draw_section_card(self, screen, section, y):
        card_rect = pygame.Rect(30, y, WIDTH - 60, 90)
        
        # Card background
        pygame.draw.rect(screen, LIGHT_GRAY, card_rect, border_radius=16)
        
        # Icon circle
        icon_x = card_rect.x + 50
        icon_y = card_rect.y + 45
        pygame.draw.circle(screen, section['color'], (icon_x, icon_y), 28)
        
        # Draw icon
        self._draw_icon(screen, section['icon'], icon_x, icon_y)
        
        # Title
        title = self.fonts['header'].render(section['title'], True, SOFT_BLACK)
        screen.blit(title, (card_rect.x + 95, card_rect.y + 20))
        
        # Subtitle
        subtitle = self.fonts['small'].render(section['subtitle'], True, DARK_GRAY)
        screen.blit(subtitle, (card_rect.x + 95, card_rect.y + 52))
        
        # Chevron
        chevron_x = card_rect.x + card_rect.width - 40
        chevron_y = card_rect.y + 45
        pygame.draw.line(screen, MID_GRAY, (chevron_x, chevron_y - 8), (chevron_x + 8, chevron_y), 2)
        pygame.draw.line(screen, MID_GRAY, (chevron_x + 8, chevron_y), (chevron_x, chevron_y + 8), 2)
    
    def _draw_icon(self, screen, icon_type, cx, cy):
        color = WHITE
        
        if icon_type == 'heart':
            # Simple heart shape using parametric points
            import math
            scale = 0.8
            points = []
            for i in range(50):
                t = i / 50 * 2 * math.pi
                hx = 16 * (math.sin(t) ** 3)
                hy = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
                px = cx + int(hx * scale)
                py = cy - int(hy * scale) + 2
                points.append((px, py))
            if len(points) > 2:
                pygame.draw.polygon(screen, color, points)
        
        elif icon_type == 'calendar':
            # Meal prep container icon
            container_w = 28
            container_h = 20
            left = cx - container_w // 2
            top = cy - container_h // 2
            
            # Main container
            pygame.draw.rect(screen, color, (left, top, container_w, container_h), border_radius=3)
            
            # Divider lines (3 compartments)
            pygame.draw.line(screen, (80, 160, 220), (left + container_w // 3, top + 2), 
                           (left + container_w // 3, top + container_h - 2), 2)
            pygame.draw.line(screen, (80, 160, 220), (left + 2 * container_w // 3, top + 2), 
                           (left + 2 * container_w // 3, top + container_h - 2), 2)
            
            # Lid line at top
            pygame.draw.line(screen, (80, 160, 220), (left + 2, top + 4), (left + container_w - 2, top + 4), 2)
        
        elif icon_type == 'cart':
            # Shopping cart
            pygame.draw.line(screen, color, (cx - 12, cy - 10), (cx - 8, cy - 10), 2)
            pygame.draw.line(screen, color, (cx - 8, cy - 10), (cx - 5, cy + 6), 2)
            pygame.draw.line(screen, color, (cx - 5, cy + 6), (cx + 12, cy + 6), 2)
            pygame.draw.line(screen, color, (cx + 12, cy + 6), (cx + 14, cy - 8), 2)
            pygame.draw.line(screen, color, (cx + 14, cy - 8), (cx - 3, cy - 8), 2)
            pygame.draw.circle(screen, color, (cx - 2, cy + 12), 4)
            pygame.draw.circle(screen, color, (cx + 9, cy + 12), 4)
        
        elif icon_type == 'sparkle':
            # AI sparkle icon
            self._draw_sparkle(screen, cx, cy - 2, 12, color)
            self._draw_sparkle(screen, cx + 8, cy - 10, 6, color)
    
    def _draw_sparkle(self, screen, cx, cy, size, color):
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
        pygame.draw.polygon(screen, color, points)
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        # Check section cards
        sections = ['favorites', 'meal_prep', 'grocery_list', 'saved_recipes']
        
        card_y = 100
        card_height = 90
        card_margin = 15
        
        for section_id in sections:
            if 30 <= x <= WIDTH - 30 and card_y <= y <= card_y + card_height:
                return f'navigate_{section_id}'
            card_y += card_height + card_margin
        
        return None