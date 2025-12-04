"""
ui_new/views/skill_level_view.py

Description:
    * Cooking skill level selection view

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *


class SkillLevelView:
    """View for selecting cooking skill level."""
    
    SKILL_LEVELS = [
        {
            'id': 'Beginner',
            'title': 'Beginner',
            'description': 'New to cooking. Prefer simple recipes with basic techniques and common ingredients.',
            'icon': 'egg'
        },
        {
            'id': 'Intermediate',
            'title': 'Intermediate',
            'description': 'Comfortable in the kitchen. Can handle moderate complexity and some unfamiliar techniques.',
            'icon': 'pan'
        },
        {
            'id': 'Advanced',
            'title': 'Advanced',
            'description': 'Experienced cook. Enjoy challenging recipes with complex techniques and specialty ingredients.',
            'icon': 'chef'
        },
    ]
    
    def __init__(self, fonts, config):
        self.fonts = fonts
        self.config = config
        self.scroll_offset = 0
        self.max_scroll = 0
    
    def _get_selected(self):
        return self.config.get('skill_level', 'Beginner')
    
    def _save_selected(self, level):
        self.config.set('skill_level', level)
    
    def draw(self, screen, state, keyboard_visible=False):
        content_bottom = HEIGHT - NAV_HEIGHT
        
        self._draw_header(screen)
        self._draw_skill_options(screen, content_bottom)
    
    def _draw_header(self, screen):
        # Back button
        back_rect = pygame.Rect(30, 20, 80, 40)
        pygame.draw.rect(screen, LIGHT_GRAY, back_rect, border_radius=20)
        
        ax = back_rect.x + 20
        ay = back_rect.y + 20
        pygame.draw.line(screen, CHARCOAL, (ax + 8, ay - 6), (ax, ay), 2)
        pygame.draw.line(screen, CHARCOAL, (ax, ay), (ax + 8, ay + 6), 2)
        
        back_text = self.fonts['small'].render("Back", True, CHARCOAL)
        screen.blit(back_text, (ax + 15, ay - 9))
        
        # Title
        title = self.fonts['header'].render("Cooking Skill Level", True, SOFT_BLACK)
        screen.blit(title, (130, 25))
        
        # Subtitle
        subtitle = self.fonts['small'].render("Recipes will be tailored to your experience", True, DARK_GRAY)
        screen.blit(subtitle, (130, 58))
    
    def _draw_skill_options(self, screen, content_bottom):
        y_start = 110
        selected = self._get_selected()
        
        card_height = 120
        card_margin = 20
        y = y_start
        
        for level in self.SKILL_LEVELS:
            is_selected = level['id'] == selected
            self._draw_skill_card(screen, level, y, is_selected)
            y += card_height + card_margin
    
    def _draw_skill_card(self, screen, level, y, is_selected):
        card_rect = pygame.Rect(30, y, WIDTH - 60, 120)
        
        if is_selected:
            pygame.draw.rect(screen, SOFT_BLACK, card_rect, border_radius=16)
            title_color = WHITE
            desc_color = LIGHT_GRAY
            icon_color = WHITE
            check_bg = WHITE
            check_fg = SOFT_BLACK
        else:
            pygame.draw.rect(screen, LIGHT_GRAY, card_rect, border_radius=16)
            title_color = SOFT_BLACK
            desc_color = DARK_GRAY
            icon_color = CHARCOAL
            check_bg = None
            check_fg = MID_GRAY
        
        # Icon
        icon_x = card_rect.x + 30
        icon_y = card_rect.y + 35
        self._draw_skill_icon(screen, level['icon'], icon_x, icon_y, icon_color)
        
        # Title
        title = self.fonts['header'].render(level['title'], True, title_color)
        screen.blit(title, (card_rect.x + 90, card_rect.y + 25))
        
        # Description - word wrap
        desc_text = level['description']
        max_width = card_rect.width - 160
        words = desc_text.split()
        lines = []
        current = ""
        
        for word in words:
            test = current + " " + word if current else word
            if self.fonts['small'].size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        
        desc_y = card_rect.y + 55
        for line in lines[:2]:  # Max 2 lines
            desc_surface = self.fonts['small'].render(line, True, desc_color)
            screen.blit(desc_surface, (card_rect.x + 90, desc_y))
            desc_y += 22
        
        # Selection indicator (radio button style)
        radio_x = card_rect.x + card_rect.width - 50
        radio_y = card_rect.y + card_rect.height // 2
        
        if is_selected:
            pygame.draw.circle(screen, check_bg, (radio_x, radio_y), 12)
            pygame.draw.circle(screen, check_fg, (radio_x, radio_y), 6)
        else:
            pygame.draw.circle(screen, check_fg, (radio_x, radio_y), 12, 2)
    
    def _draw_skill_icon(self, screen, icon_type, x, y, color):
        """Draw skill level icons."""
        if icon_type == 'egg':
            # Simple egg shape
            pygame.draw.ellipse(screen, color, (x, y, 28, 36), 3)
        
        elif icon_type == 'pan':
            # Frying pan
            pygame.draw.circle(screen, color, (x + 18, y + 18), 14, 3)
            pygame.draw.line(screen, color, (x + 30, y + 18), (x + 45, y + 18), 3)
        
        elif icon_type == 'chef':
            # Chef hat
            pygame.draw.ellipse(screen, color, (x + 2, y + 18, 32, 18), 3)
            pygame.draw.arc(screen, color, (x + 5, y, 26, 24), 0, 3.14, 3)
            pygame.draw.circle(screen, color, (x + 8, y + 8), 6, 2)
            pygame.draw.circle(screen, color, (x + 18, y + 4), 7, 2)
            pygame.draw.circle(screen, color, (x + 28, y + 8), 6, 2)
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        # Back button
        if 30 <= x <= 110 and 20 <= y <= 60:
            return 'back'
        
        # Skill cards
        y_start = 110
        card_height = 120
        card_margin = 20
        
        for i, level in enumerate(self.SKILL_LEVELS):
            card_y = y_start + i * (card_height + card_margin)
            
            if 30 <= x <= WIDTH - 30 and card_y <= y <= card_y + card_height:
                self._save_selected(level['id'])
                return f"skill_{level['id']}"
        
        return None
    
    def handle_scroll(self, delta):
        # No scrolling needed for 3 options, but keep for consistency
        pass