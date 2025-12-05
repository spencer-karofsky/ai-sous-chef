"""
ui_new/components.py

Description:
    * Reusable UI components (navbar, keyboard, cards)

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *
from ui_new.icons import draw_icon


class NavBar:
    """Bottom navigation bar with 5 items."""
    
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.active = 'Home'
        self.y = HEIGHT - NAV_HEIGHT
    
    def draw(self):
        # Light sage background
        pygame.draw.rect(self.screen, SAGE_LIGHT, (0, self.y, WIDTH, NAV_HEIGHT))
        
        # Subtle top border
        pygame.draw.line(self.screen, SAGE, (0, self.y), (WIDTH, self.y), 1)
        
        item_width = WIDTH // len(NAV_ITEMS)
        
        for i, name in enumerate(NAV_ITEMS):
            x = i * item_width
            cx = x + item_width // 2
            is_active = (name == self.active)
            
            # Active = teal, inactive = muted sage
            color = TEAL if is_active else (120, 130, 118)
            
            # Icon
            icon_x = cx - NAV_ICON_SIZE // 2
            icon_y = self.y + 15
            draw_icon(self.screen, name, icon_x, icon_y, NAV_ICON_SIZE, color, filled=is_active)
            
            # Label
            label = self.font.render(name, True, color)
            label_x = cx - label.get_width() // 2
            label_y = self.y + 50
            self.screen.blit(label, (label_x, label_y))
    
    def handle_touch(self, pos):
        x, y = pos
        if y < self.y:
            return None
        
        item_width = WIDTH // len(NAV_ITEMS)
        index = x // item_width
        if 0 <= index < len(NAV_ITEMS):
            return NAV_ITEMS[index]
        return None