"""
ui_new/views/search_view.py

Description:
    * Search view - clean minimal design

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *


class SearchView:
    def __init__(self, fonts):
        self.fonts = fonts
        self.gradient_surface = None
    
    def _create_gradient(self, width, height):
        """Create a subtle warm gradient background."""
        if self.gradient_surface and self.gradient_surface.get_size() == (width, height):
            return self.gradient_surface
        
        self.gradient_surface = pygame.Surface((width, height))
        
        # Soft warm white gradient - matches Home
        top_color = (255, 251, 245)
        bottom_color = (252, 245, 235)
        
        for y in range(height):
            t = y / height
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
            pygame.draw.line(self.gradient_surface, (r, g, b), (0, y), (width, y))
        
        return self.gradient_surface
    
    def draw(self, screen, state, keyboard_visible):
        # Draw gradient background
        screen.blit(self._create_gradient(WIDTH, HEIGHT), (0, 0))
        
        content_bottom = HEIGHT - NAV_HEIGHT
        if keyboard_visible:
            content_bottom = HEIGHT - KEYBOARD_HEIGHT
        
        self._draw_header(screen)
        self._draw_search_bar(screen, state)
        self._draw_results(screen, state, content_bottom)
    
    def _draw_header(self, screen):
        y = 25
        title = self.fonts['header'].render("Search", True, SOFT_BLACK)
        screen.blit(title, (40, y))
    
    def _draw_search_bar(self, screen, state):
        y = 80
        
        search_rect = pygame.Rect(40, y, WIDTH - 80, 56)
        pygame.draw.rect(screen, WHITE, search_rect, border_radius=12)
        pygame.draw.rect(screen, SAGE, search_rect, 1, border_radius=12)
        
        icon_x = search_rect.x + 20
        icon_y = search_rect.y + 16
        pygame.draw.circle(screen, DARK_GRAY, (icon_x + 10, icon_y + 10), 9, 2)
        pygame.draw.line(screen, DARK_GRAY, (icon_x + 17, icon_y + 17), (icon_x + 23, icon_y + 23), 2)
        
        text_x = search_rect.x + 55
        if state['search_text']:
            text = self.fonts['body'].render(state['search_text'][-35:], True, SOFT_BLACK)
        else:
            text = self.fonts['body'].render("Search recipes...", True, DARK_GRAY)
        screen.blit(text, (text_x, y + 14))
        
        if state['active_input'] == 'search' and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = text_x + self.fonts['body'].size(state['search_text'][-35:])[0] + 2
            pygame.draw.rect(screen, SOFT_BLACK, (cursor_x, y + 14, 2, 28))
        
        if state['search_text']:
            btn_rect = pygame.Rect(WIDTH - 140, y, 90, 56)
            pygame.draw.rect(screen, TEAL, btn_rect, border_radius=12)
            btn_text = self.fonts['small'].render("Search", True, WHITE)
            screen.blit(btn_text, (btn_rect.x + 15, btn_rect.y + 17))
        
        if state['status'] and state['status'] != "Tap to search":
            status = self.fonts['caption'].render(state['status'], True, DARK_GRAY)
            screen.blit(status, (40, y + 65))
    
    def _draw_results(self, screen, state, content_bottom):
        if not state['results']:
            self._draw_empty_state(screen)
            return
        
        y = 170
        
        for i, recipe in enumerate(state['results'][:5]):
            if y + 90 > content_bottom:
                break
            
            self._draw_recipe_card(screen, recipe, i, y)
            y += 100
    
    def _draw_empty_state(self, screen):
        y = HEIGHT // 2 - 60
        
        cx = WIDTH // 2
        pygame.draw.circle(screen, SAGE, (cx, y), 40, 3)
        pygame.draw.circle(screen, SAGE, (cx - 8, y - 5), 15, 2)
        pygame.draw.line(screen, SAGE, (cx + 3, y + 7), (cx + 18, y + 22), 3)
        
        text = self.fonts['body'].render("Search for recipes", True, SOFT_BLACK)
        screen.blit(text, (cx - text.get_width() // 2, y + 60))
        
        hint = self.fonts['small'].render("Try 'pasta' or 'quick dinner'", True, DARK_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, y + 95))
    
    def _draw_recipe_card(self, screen, recipe, index, y):
        card_rect = pygame.Rect(40, y, WIDTH - 80, 90)
        
        pygame.draw.rect(screen, WHITE, card_rect, border_radius=12)
        pygame.draw.rect(screen, SAGE, card_rect, 1, border_radius=12)
        
        num_x = card_rect.x + 25
        num_text = self.fonts['header'].render(f"{index + 1}", True, SAGE)
        screen.blit(num_text, (num_x, card_rect.y + 28))
        
        name = recipe.get('name', 'Untitled')
        max_width = card_rect.width - 120
        
        if self.fonts['body'].size(name)[0] > max_width:
            while self.fonts['body'].size(name + "...")[0] > max_width and len(name) > 10:
                name = name[:-1]
            name = name + "..."
        
        name_text = self.fonts['body'].render(name, True, SOFT_BLACK)
        screen.blit(name_text, (card_rect.x + 70, card_rect.y + 18))
        
        cal = recipe.get('calories', 'N/A')
        category = recipe.get('category', '')
        details = f"{category} • {cal} cal" if category else f"{cal} cal"
        details_text = self.fonts['small'].render(details, True, DARK_GRAY)
        screen.blit(details_text, (card_rect.x + 70, card_rect.y + 52))
        
        arrow_x = card_rect.x + card_rect.width - 35
        arrow_y = card_rect.y + 40
        pygame.draw.line(screen, TEAL, (arrow_x, arrow_y - 8), (arrow_x + 8, arrow_y), 2)
        pygame.draw.line(screen, TEAL, (arrow_x + 8, arrow_y), (arrow_x, arrow_y + 8), 2)
    
    def handle_touch(self, pos, state, keyboard_visible):
        x, y = pos
        
        # Search button FIRST (check before search bar since it overlaps)
        if state['search_text'] and WIDTH - 140 <= x <= WIDTH - 40 and 80 <= y <= 136:
            return 'search'
        
        # Search bar tap (exclude the button area)
        if 40 <= x <= WIDTH - 150 and 80 <= y <= 136:
            return 'focus_search'
        
        # Results
        result_y = 170
        for i in range(min(len(state['results']), 5)):
            if 40 <= x <= WIDTH - 40 and result_y <= y <= result_y + 90:
                return f'select_{i}'
            result_y += 100
        
        return None