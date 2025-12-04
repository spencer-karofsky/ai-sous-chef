"""
ui_new/views/recipe_view.py

Description:
    * Recipe detail view - clean minimal design

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
import math
from ui_new.constants import *


class RecipeView:
    def __init__(self, fonts):
        self.fonts = fonts
        self.favorites_manager = None  # Set by app
        self.current_s3_key = None  # Track current recipe's s3_key
        self.current_source = 'search'  # 'search' or 'generated'
    
    def set_manager(self, manager):
        self.favorites_manager = manager
    
    def draw(self, screen, state, keyboard_visible):
        recipe = state.get('recipe')
        if not recipe:
            return 0
        
        content_bottom = HEIGHT - NAV_HEIGHT
        if keyboard_visible:
            content_bottom = HEIGHT - KEYBOARD_HEIGHT
        
        self._draw_header(screen, recipe)
        max_scroll = self._draw_content(screen, recipe, state['scroll_offset'], content_bottom)
        self._draw_modify_bar(screen, state, content_bottom)
        
        return max_scroll
    
    def _draw_header(self, screen, recipe):
        # Back button
        back_rect = pygame.Rect(30, 20, 80, 40)
        pygame.draw.rect(screen, LIGHT_GRAY, back_rect, border_radius=20)
        
        ax = back_rect.x + 20
        ay = back_rect.y + 20
        pygame.draw.line(screen, CHARCOAL, (ax + 8, ay - 6), (ax, ay), 2)
        pygame.draw.line(screen, CHARCOAL, (ax, ay), (ax + 8, ay + 6), 2)
        
        back_text = self.fonts['small'].render("Back", True, CHARCOAL)
        screen.blit(back_text, (ax + 15, ay - 9))
        
        # Heart button (favorite)
        heart_rect = pygame.Rect(WIDTH - 60, 20, 40, 40)
        is_favorite = False
        if self.favorites_manager:
            is_favorite = self.favorites_manager.is_favorite(recipe.get('name', ''))
        
        self._draw_heart_button(screen, heart_rect.x + 20, heart_rect.y + 20, is_favorite)
        
        # Recipe title
        title = recipe.get('name', 'Recipe')
        max_width = WIDTH - 220  # Leave room for back and heart
        
        while self.fonts['header'].size(title)[0] > max_width and len(title) > 15:
            title = title[:-4] + "..."
        
        title_text = self.fonts['header'].render(title, True, SOFT_BLACK)
        title_x = (WIDTH - title_text.get_width()) // 2
        screen.blit(title_text, (title_x, 25))
    
    def _draw_heart_button(self, screen, cx, cy, filled):
        """Draw heart favorite button."""
        size = 12
        scale = size / 15
        points = []
        
        for i in range(50):
            t = i / 50 * 2 * math.pi
            hx = 16 * (math.sin(t) ** 3)
            hy = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
            px = cx + int(hx * scale)
            py = cy - int(hy * scale)
            points.append((px, py))
        
        if len(points) > 2:
            if filled:
                pygame.draw.polygon(screen, (220, 60, 60), points)  # Red filled
            else:
                pygame.draw.polygon(screen, CHARCOAL, points, 2)  # Outline
    
    def _draw_content(self, screen, recipe, scroll_offset, content_bottom):
        content_surface = pygame.Surface((WIDTH, 1500), pygame.SRCALPHA)
        content_surface.fill(WHITE)
        y = 10
        
        # Info pills with simple text labels
        info_items = []
        if recipe.get('total_time'):
            info_items.append(recipe['total_time'])
        if recipe.get('servings'):
            info_items.append(f"Serves {recipe['servings']}")
        if recipe.get('nutrition', {}).get('calories'):
            info_items.append(f"{recipe['nutrition']['calories']} cal")
        
        pill_x = 40
        for text in info_items:
            pill_width = self.fonts['small'].size(text)[0] + 28
            pill_rect = pygame.Rect(pill_x, y, pill_width, 36)
            pygame.draw.rect(content_surface, LIGHT_GRAY, pill_rect, border_radius=18)
            
            info_text = self.fonts['small'].render(text, True, CHARCOAL)
            content_surface.blit(info_text, (pill_x + 14, y + 8))
            pill_x += pill_width + 10
        
        y += 60
        
        col_width = (WIDTH - 100) // 2
        
        ing_label = self.fonts['body'].render("Ingredients", True, SOFT_BLACK)
        content_surface.blit(ing_label, (40, y))
        pygame.draw.rect(content_surface, SOFT_BLACK, (40, y + 35, 80, 2))
        
        ing_y = y + 55
        for ing in recipe.get('ingredients', [])[:15]:
            if isinstance(ing, dict):
                qty = ing.get('quantity', '')
                unit = ing.get('unit', '')
                item = ing.get('item', '')
                ing_text = f"{qty} {unit} {item}".strip()
            else:
                ing_text = str(ing)
            
            lines = self._wrap_text(ing_text, col_width - 20)
            for j, line in enumerate(lines):
                prefix = "• " if j == 0 else "  "
                text = self.fonts['small'].render(prefix + line, True, CHARCOAL)
                content_surface.blit(text, (40, ing_y))
                ing_y += 30
        
        inst_x = col_width + 60
        inst_label = self.fonts['body'].render("Instructions", True, SOFT_BLACK)
        content_surface.blit(inst_label, (inst_x, y))
        pygame.draw.rect(content_surface, SOFT_BLACK, (inst_x, y + 35, 90, 2))
        
        inst_y = y + 55
        for i, step in enumerate(recipe.get('instructions', [])[:12], 1):
            num_text = self.fonts['small'].render(f"{i}.", True, MID_GRAY)
            content_surface.blit(num_text, (inst_x, inst_y))
            
            lines = self._wrap_text(step, col_width - 40)
            for j, line in enumerate(lines):
                text = self.fonts['small'].render(line, True, CHARCOAL)
                content_surface.blit(text, (inst_x + 30, inst_y + j * 28))
            
            inst_y += len(lines) * 28 + 15
        
        max_scroll = max(ing_y, inst_y) - 250
        
        visible_height = content_bottom - 140
        screen.blit(content_surface, (0, 80), (0, scroll_offset, WIDTH, visible_height))
        
        return max(0, max_scroll)
    
    def _draw_modify_bar(self, screen, state, content_bottom):
        bar_y = content_bottom - 65
        
        pygame.draw.rect(screen, WHITE, (0, bar_y, WIDTH, 65))
        pygame.draw.line(screen, DIVIDER, (0, bar_y), (WIDTH, bar_y), 1)
        
        input_rect = pygame.Rect(40, bar_y + 12, WIDTH - 150, 44)
        pygame.draw.rect(screen, LIGHT_GRAY, input_rect, border_radius=22)
        
        if state.get('modify_text'):
            text = self.fonts['small'].render(state['modify_text'][-40:], True, SOFT_BLACK)
        else:
            text = self.fonts['small'].render("Ask to modify recipe...", True, MID_GRAY)
        screen.blit(text, (input_rect.x + 20, input_rect.y + 12))
        
        if state.get('active_input') == 'modify' and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = input_rect.x + 20 + self.fonts['small'].size(state.get('modify_text', '')[-40:])[0] + 2
            pygame.draw.rect(screen, SOFT_BLACK, (cursor_x, input_rect.y + 10, 2, 24))
        
        btn_rect = pygame.Rect(WIDTH - 100, bar_y + 12, 55, 44)
        pygame.draw.rect(screen, SOFT_BLACK, btn_rect, border_radius=22)
        
        ax = btn_rect.x + 22
        ay = btn_rect.y + 22
        pygame.draw.line(screen, WHITE, (ax - 8, ay), (ax + 5, ay), 2)
        pygame.draw.line(screen, WHITE, (ax, ay - 6), (ax + 5, ay), 2)
        pygame.draw.line(screen, WHITE, (ax, ay + 6), (ax + 5, ay), 2)
        
        if state.get('modify_status'):
            status = self.fonts['caption'].render(state['modify_status'], True, DARK_GRAY)
            screen.blit(status, (40, bar_y - 22))
    
    def _wrap_text(self, text, max_width):
        words = text.split()
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
        return lines if lines else [text]
    
    def handle_touch(self, pos, state, keyboard_visible):
        x, y = pos
        content_bottom = HEIGHT - NAV_HEIGHT
        if keyboard_visible:
            content_bottom = HEIGHT - KEYBOARD_HEIGHT
        
        # Back button
        if 30 <= x <= 110 and 20 <= y <= 60:
            return 'back'
        
        # Heart button (favorite)
        if WIDTH - 60 <= x <= WIDTH - 20 and 20 <= y <= 60:
            return 'toggle_favorite'
        
        # Modify input
        bar_y = content_bottom - 65
        if 40 <= x <= WIDTH - 150 and bar_y + 12 <= y <= bar_y + 56:
            return 'focus_modify'
        
        # Send button
        if WIDTH - 100 <= x <= WIDTH - 45 and bar_y + 12 <= y <= bar_y + 56:
            return 'modify'
        
        return None