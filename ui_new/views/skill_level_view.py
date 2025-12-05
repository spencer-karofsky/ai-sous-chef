"""
ui_new/views/skill_level_view.py

Description:
    * Cooking skill level selection view

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *

# Warm background
WARM_BG = (255, 251, 245)

# Muted sage for cards
CARD_BG = (241, 244, 240)


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
        screen.fill(WARM_BG)
        content_bottom = HEIGHT - NAV_HEIGHT
        
        self._draw_header(screen)
        self._draw_skill_options(screen, content_bottom)
    
    def _draw_header(self, screen):
        # Back button - sage light with sage border
        back_rect = pygame.Rect(30, 20, 95, 40)
        pygame.draw.rect(screen, SAGE_LIGHT, back_rect, border_radius=20)
        pygame.draw.rect(screen, SAGE, back_rect, border_radius=20, width=1)
        
        # Chevron in teal
        ax = back_rect.x + 22
        ay = back_rect.y + 20
        pygame.draw.line(screen, TEAL, (ax + 8, ay - 6), (ax, ay), 2)
        pygame.draw.line(screen, TEAL, (ax, ay), (ax + 8, ay + 6), 2)
        
        back_text = self.fonts['small'].render("Back", True, SOFT_BLACK)
        screen.blit(back_text, (ax + 18, ay - 9))
        
        # Title
        title = self.fonts['header'].render("Cooking Skill Level", True, SOFT_BLACK)
        screen.blit(title, (150, 28))
        
        # Subtitle as pill on right
        current = self._get_selected()
        pill_width = self.fonts['small'].size(current)[0] + 16
        pill_rect = pygame.Rect(WIDTH - pill_width - 30, 30, pill_width, 26)
        pygame.draw.rect(screen, SAGE_LIGHT, pill_rect, border_radius=13)
        subtitle = self.fonts['small'].render(current, True, SOFT_BLACK)
        screen.blit(subtitle, (pill_rect.x + 8, pill_rect.y + 4))
    
    def _draw_skill_options(self, screen, content_bottom):
        y_start = 90
        selected = self._get_selected()
        
        card_height = 130
        card_margin = 16
        y = y_start
        
        for level in self.SKILL_LEVELS:
            is_selected = level['id'] == selected
            self._draw_skill_card(screen, level, y, is_selected)
            y += card_height + card_margin
    
    def _draw_skill_card(self, screen, level, y, is_selected):
        card_rect = pygame.Rect(30, y, WIDTH - 60, 130)
        
        # Shadow
        shadow_surface = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 12), (0, 0, card_rect.width, card_rect.height), border_radius=16)
        screen.blit(shadow_surface, (card_rect.x + 2, card_rect.y + 2))
        
        if is_selected:
            # Selected: teal background
            pygame.draw.rect(screen, TEAL, card_rect, border_radius=16)
            title_color = WHITE
            desc_color = (200, 225, 220)
            icon_color = WHITE
            radio_outer = WHITE
            radio_inner = TEAL
        else:
            # Unselected: muted sage background with border
            pygame.draw.rect(screen, CARD_BG, card_rect, border_radius=16)
            pygame.draw.rect(screen, SAGE, card_rect, border_radius=16, width=1)
            title_color = SOFT_BLACK
            desc_color = DARK_GRAY
            icon_color = TEAL
            radio_outer = SAGE
            radio_inner = None
        
        # Icon in circle
        icon_cx = card_rect.x + 50
        icon_cy = card_rect.y + 50
        
        if is_selected:
            pygame.draw.circle(screen, (255, 255, 255, 50), (icon_cx, icon_cy), 28)
        else:
            pygame.draw.circle(screen, SAGE_LIGHT, (icon_cx, icon_cy), 28)
        
        self._draw_skill_icon(screen, level['icon'], icon_cx - 18, icon_cy - 18, icon_color)
        
        # Title
        title = self.fonts['header'].render(level['title'], True, title_color)
        screen.blit(title, (card_rect.x + 95, card_rect.y + 25))
        
        # Description - word wrap
        desc_text = level['description']
        max_width = card_rect.width - 170
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
        
        desc_y = card_rect.y + 58
        for line in lines[:3]:  # Max 3 lines
            desc_surface = self.fonts['small'].render(line, True, desc_color)
            screen.blit(desc_surface, (card_rect.x + 95, desc_y))
            desc_y += 22
        
        # Selection indicator (radio button style)
        radio_x = card_rect.x + card_rect.width - 45
        radio_y = card_rect.y + card_rect.height // 2
        
        if is_selected:
            pygame.draw.circle(screen, radio_outer, (radio_x, radio_y), 14)
            pygame.draw.circle(screen, radio_inner, (radio_x, radio_y), 7)
        else:
            pygame.draw.circle(screen, radio_outer, (radio_x, radio_y), 14, 2)
    
    def _draw_skill_icon(self, screen, icon_type, x, y, color):
        """Draw skill level icons."""
        if icon_type == 'egg':
            # Simple egg shape
            pygame.draw.ellipse(screen, color, (x + 4, y, 28, 36), 3)
        
        elif icon_type == 'pan':
            # Frying pan
            pygame.draw.circle(screen, color, (x + 16, y + 18), 14, 3)
            pygame.draw.line(screen, color, (x + 28, y + 18), (x + 40, y + 18), 3)
        
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
        if 30 <= x <= 125 and 20 <= y <= 60:
            return 'back'
        
        # Skill cards
        y_start = 90
        card_height = 130
        card_margin = 16
        
        for i, level in enumerate(self.SKILL_LEVELS):
            card_y = y_start + i * (card_height + card_margin)
            
            if 30 <= x <= WIDTH - 30 and card_y <= y <= card_y + card_height:
                self._save_selected(level['id'])
                return f"skill_{level['id']}"
        
        return None
    
    def handle_scroll(self, delta):
        # No scrolling needed for 3 options, but keep for consistency
        pass