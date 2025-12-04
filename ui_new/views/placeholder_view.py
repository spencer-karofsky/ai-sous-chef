"""
ui_new/views/placeholder_view.py

Description:
    * Placeholder view for unimplemented screens (Favorites, Settings)

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *


class PlaceholderView:
    def __init__(self, fonts, title, icon_name):
        self.fonts = fonts
        self.title = title
        self.icon_name = icon_name
    
    def draw(self, screen, state, keyboard_visible=False):
        content_bottom = HEIGHT - NAV_HEIGHT
        
        title_text = self.fonts['header'].render(self.title, True, SOFT_BLACK)
        screen.blit(title_text, (40, 25))
        
        cy = content_bottom // 2
        
        pygame.draw.circle(screen, LIGHT_GRAY, (WIDTH // 2, cy - 30), 50, 3)
        
        soon_text = self.fonts['body'].render("Coming Soon", True, DARK_GRAY)
        screen.blit(soon_text, (WIDTH // 2 - soon_text.get_width() // 2, cy + 40))
        
        desc_text = self.fonts['small'].render(f"{self.title} feature is under development", True, MID_GRAY)
        screen.blit(desc_text, (WIDTH // 2 - desc_text.get_width() // 2, cy + 80))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        return None


class FavoritesView(PlaceholderView):
    def __init__(self, fonts):
        super().__init__(fonts, "Favorites", "heart")


class SettingsView(PlaceholderView):
    def __init__(self, fonts):
        super().__init__(fonts, "Settings", "gear")