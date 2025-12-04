"""
ui_new/views/home_view.py

Description:
    * Home screen view - clean minimal design

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *


class HomeView:
    def __init__(self, fonts):
        self.fonts = fonts
        self.recent_recipes = []
    
    def draw(self, screen, state):
        content_bottom = HEIGHT - NAV_HEIGHT
        
        self._draw_header(screen)
        self._draw_welcome(screen)
        self._draw_quick_actions(screen)
        
        if self.recent_recipes:
            self._draw_recent(screen, content_bottom)
    
    def _draw_header(self, screen):
        y = 20
        time_text = self.fonts['caption'].render("AI Sous Chef", True, MID_GRAY)
        screen.blit(time_text, (40, y))
    
    def _draw_welcome(self, screen):
        y = 80
        
        greeting = self.fonts['title'].render("AI Sous Chef", True, SOFT_BLACK)
        screen.blit(greeting, (40, y))
        
        subtitle = self.fonts['body'].render("Find a recipe or create something new", True, DARK_GRAY)
        screen.blit(subtitle, (40, y + 60))
    
    def _draw_quick_actions(self, screen):
        y = 200
        
        card_width = (WIDTH - 100) // 2
        card_height = 180
        
        # Search card
        search_rect = pygame.Rect(40, y, card_width, card_height)
        pygame.draw.rect(screen, LIGHT_GRAY, search_rect, border_radius=16)
        
        search_title = self.fonts['header'].render("Search", True, SOFT_BLACK)
        screen.blit(search_title, (search_rect.x + 30, search_rect.y + 30))
        
        search_desc = self.fonts['small'].render("Find recipes from", True, DARK_GRAY)
        screen.blit(search_desc, (search_rect.x + 30, search_rect.y + 75))
        search_desc2 = self.fonts['small'].render("our collection", True, DARK_GRAY)
        screen.blit(search_desc2, (search_rect.x + 30, search_rect.y + 100))
        
        self._draw_search_icon_large(screen, search_rect.x + card_width - 80, search_rect.y + card_height - 70)
        
        # Create card
        create_rect = pygame.Rect(60 + card_width, y, card_width, card_height)
        pygame.draw.rect(screen, SOFT_BLACK, create_rect, border_radius=16)
        
        create_title = self.fonts['header'].render("Create", True, WHITE)
        screen.blit(create_title, (create_rect.x + 30, create_rect.y + 30))
        
        create_desc = self.fonts['small'].render("Generate a custom", True, MID_GRAY)
        screen.blit(create_desc, (create_rect.x + 30, create_rect.y + 75))
        create_desc2 = self.fonts['small'].render("recipe with AI", True, MID_GRAY)
        screen.blit(create_desc2, (create_rect.x + 30, create_rect.y + 100))
        
        # Sparkles icon instead of plus
        self._draw_sparkles_icon_large(screen, create_rect.x + card_width - 90, create_rect.y + card_height - 80, WHITE)

    def _draw_search_icon_large(self, screen, x, y):
        color = CHARCOAL
        pygame.draw.circle(screen, color, (x + 20, y + 20), 18, 3)
        pygame.draw.line(screen, color, (x + 33, y + 33), (x + 48, y + 48), 4)

    def _draw_sparkles_icon_large(self, screen, x, y, color):
        """Draw AI sparkles icon - matches nav bar icon."""
        import math
        size = 50
        
        # Large sparkle - center/bottom-left
        self._draw_sparkle(screen, x + size * 0.4, y + size * 0.55, size * 0.45, color)
        
        # Smaller sparkle - top-right
        self._draw_sparkle(screen, x + size * 0.75, y + size * 0.22, size * 0.25, color)

    def _draw_sparkle(self, screen, cx, cy, size, color):
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
        pygame.draw.polygon(screen, color, points)
    
    def _draw_search_icon_large(self, screen, x, y):
        color = CHARCOAL
        pygame.draw.circle(screen, color, (x + 20, y + 20), 18, 3)
        pygame.draw.line(screen, color, (x + 33, y + 33), (x + 48, y + 48), 4)
    
    def _draw_plus_icon_large(self, screen, x, y, color):
        cx, cy = x + 25, y + 25
        pygame.draw.line(screen, color, (cx, cy - 20), (cx, cy + 20), 4)
        pygame.draw.line(screen, color, (cx - 20, cy), (cx + 20, cy), 4)
    
    def _draw_recent(self, screen, content_bottom):
        y = 420
        section_title = self.fonts['body'].render("Recent", True, SOFT_BLACK)
        screen.blit(section_title, (40, y))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        card_width = (WIDTH - 100) // 2
        card_height = 180
        card_y = 200
        
        if 40 <= x <= 40 + card_width and card_y <= y <= card_y + card_height:
            return 'navigate_search'
        
        if 60 + card_width <= x <= 60 + card_width * 2 and card_y <= y <= card_y + card_height:
            return 'navigate_create'
        
        return None