"""
ui_new/views/saved_recipes_view.py

Description:
    * View for browsing and managing saved AI-generated recipes

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *

# Warm background
WARM_BG = (255, 251, 245)


class SavedRecipesView:
    """View for saved AI-generated recipes."""
    
    def __init__(self, fonts):
        self.fonts = fonts
        self.recipes_manager = None
        self.scroll_offset = 0
        self.max_scroll = 0
        
        self.confirm_delete_id = None
    
    def set_manager(self, recipes_manager):
        self.recipes_manager = recipes_manager
    
    def draw(self, screen, state, keyboard_visible=False):
        screen.fill(WARM_BG)
        content_bottom = HEIGHT - NAV_HEIGHT
        
        self._draw_header(screen)
        self._draw_recipes_list(screen, content_bottom)
        
        if self.confirm_delete_id:
            self._draw_delete_modal(screen)
    
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
        title = self.fonts['header'].render("Saved Creations", True, SOFT_BLACK)
        screen.blit(title, (150, 28))
        
        # Count on right side
        if self.recipes_manager:
            count = len(self.recipes_manager.get_all())
            if count > 0:
                subtitle = self.fonts['small'].render(f"{count} recipes", True, DARK_GRAY)
                screen.blit(subtitle, (WIDTH - 110, 32))
    
    def _draw_recipes_list(self, screen, content_bottom):
        y_start = 80
        visible_height = content_bottom - y_start
        
        if not self.recipes_manager:
            return
        
        recipes = self.recipes_manager.get_all()
        
        if not recipes:
            self._draw_empty_state(screen)
            return
        
        # Calculate scroll
        content_height = len(recipes) * 95 + 20
        self.max_scroll = max(0, content_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        # Create scrollable surface
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        content_surface.fill(WARM_BG)
        
        y = 10
        for recipe in recipes:
            self._draw_recipe_card(content_surface, recipe, y)
            y += 95
        
        screen.blit(content_surface, (0, y_start), (0, self.scroll_offset, WIDTH, visible_height))
    
    def _draw_empty_state(self, screen):
        cx, cy = WIDTH // 2, HEIGHT // 2 - 60
        
        # Teal circle with sparkle icon
        pygame.draw.circle(screen, TEAL, (cx, cy - 20), 60)
        self._draw_sparkle(screen, cx, cy - 25, 28, WHITE)
        self._draw_sparkle(screen, cx + 22, cy - 45, 12, WHITE)
        
        # Text
        title = self.fonts['header'].render("No Saved Creations", True, SOFT_BLACK)
        screen.blit(title, (cx - title.get_width() // 2, cy + 60))
        
        hint = self.fonts['body'].render("AI-generated recipes will appear here", True, DARK_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, cy + 100))
    
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
    
    def _draw_recipe_card(self, surface, recipe, y):
        card_rect = pygame.Rect(30, y, WIDTH - 60, 85)
        
        # Soft shadow
        shadow_surface = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 12), (0, 0, card_rect.width, card_rect.height), border_radius=12)
        surface.blit(shadow_surface, (card_rect.x + 2, card_rect.y + 2))
        
        # Card background
        pygame.draw.rect(surface, WHITE, card_rect, border_radius=12)
        pygame.draw.rect(surface, SAGE, card_rect, border_radius=12, width=1)
        
        # Sparkle icon in teal circle
        icon_x = card_rect.x + 38
        icon_y = card_rect.y + 42
        pygame.draw.circle(surface, TEAL, (icon_x, icon_y), 22)
        self._draw_sparkle(surface, icon_x, icon_y - 2, 12, WHITE)
        self._draw_sparkle(surface, icon_x + 8, icon_y - 10, 5, WHITE)
        
        # Recipe name
        name = recipe.get('name', 'Untitled')
        max_width = card_rect.width - 150
        if self.fonts['body'].size(name)[0] > max_width:
            while self.fonts['body'].size(name + "...")[0] > max_width and len(name) > 10:
                name = name[:-1]
            name = name + "..."
        
        name_text = self.fonts['body'].render(name, True, SOFT_BLACK)
        surface.blit(name_text, (card_rect.x + 75, card_rect.y + 18))
        
        # Date as pill
        created = recipe.get('created_at', '')[:10]
        if created:
            date_str = f"Created {created}"
            date_width = self.fonts['caption'].size(date_str)[0] + 14
            date_rect = pygame.Rect(card_rect.x + 75, card_rect.y + 50, date_width, 22)
            pygame.draw.rect(surface, SAGE_LIGHT, date_rect, border_radius=11)
            date_text = self.fonts['caption'].render(date_str, True, SOFT_BLACK)
            surface.blit(date_text, (card_rect.x + 82, card_rect.y + 54))
        
        # Delete button - subtle
        delete_x = card_rect.x + card_rect.width - 45
        delete_y = card_rect.y + 42
        pygame.draw.circle(surface, SAGE_LIGHT, (delete_x, delete_y), 16)
        # X icon
        pygame.draw.line(surface, DARK_GRAY, (delete_x - 5, delete_y - 5), (delete_x + 5, delete_y + 5), 2)
        pygame.draw.line(surface, DARK_GRAY, (delete_x + 5, delete_y - 5), (delete_x - 5, delete_y + 5), 2)
        
        # Chevron in teal
        chevron_x = card_rect.x + card_rect.width - 80
        chevron_y = card_rect.y + 42
        pygame.draw.line(surface, TEAL, (chevron_x, chevron_y - 8), (chevron_x + 8, chevron_y), 2)
        pygame.draw.line(surface, TEAL, (chevron_x + 8, chevron_y), (chevron_x, chevron_y + 8), 2)
    
    def _draw_delete_modal(self, screen):
        # Overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Modal
        modal_width = 420
        modal_height = 200
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        pygame.draw.rect(screen, WHITE, (modal_x, modal_y, modal_width, modal_height), border_radius=16)
        
        # Title
        title = self.fonts['header'].render("Delete Recipe?", True, SOFT_BLACK)
        screen.blit(title, (modal_x + 30, modal_y + 25))
        
        # Message
        msg = self.fonts['body'].render("This cannot be undone.", True, DARK_GRAY)
        screen.blit(msg, (modal_x + 30, modal_y + 75))
        
        # Buttons
        btn_y = modal_y + modal_height - 65
        
        # Cancel - sage light with border
        cancel_rect = pygame.Rect(modal_x + 30, btn_y, 110, 45)
        pygame.draw.rect(screen, SAGE_LIGHT, cancel_rect, border_radius=10)
        pygame.draw.rect(screen, SAGE, cancel_rect, border_radius=10, width=1)
        cancel_text = self.fonts['body'].render("Cancel", True, SOFT_BLACK)
        screen.blit(cancel_text, (cancel_rect.x + (cancel_rect.width - cancel_text.get_width()) // 2, 
                                  cancel_rect.y + 11))
        
        # Delete - coral red
        delete_rect = pygame.Rect(modal_x + modal_width - 140, btn_y, 110, 45)
        pygame.draw.rect(screen, (200, 80, 80), delete_rect, border_radius=10)
        delete_text = self.fonts['body'].render("Delete", True, WHITE)
        screen.blit(delete_text, (delete_rect.x + (delete_rect.width - delete_text.get_width()) // 2, 
                                  delete_rect.y + 11))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        # Handle delete modal
        if self.confirm_delete_id:
            return self._handle_modal_touch(x, y)
        
        # Back button
        if 30 <= x <= 125 and 20 <= y <= 60:
            return 'back'
        
        if not self.recipes_manager:
            return None
        
        recipes = self.recipes_manager.get_all()
        if not recipes:
            return None
        
        # Recipe list
        y_start = 80
        if y < y_start:
            return None
        
        content_y = y - y_start + self.scroll_offset
        item_y = 10
        
        for recipe in recipes:
            card_rect_x = 30
            card_width = WIDTH - 60
            card_height = 85
            
            if item_y <= content_y <= item_y + card_height:
                # Check delete button (circle on right)
                delete_x = card_rect_x + card_width - 45
                if delete_x - 20 <= x <= delete_x + 20:
                    self.confirm_delete_id = recipe['id']
                    return 'show_delete_confirm'
                
                # Card tap = view recipe
                if card_rect_x <= x <= card_rect_x + card_width - 60:
                    return f"view_saved_{recipe['id']}"
            
            item_y += 95
        
        return None
    
    def _handle_modal_touch(self, x, y):
        modal_width = 420
        modal_height = 200
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        btn_y = modal_y + modal_height - 65
        
        # Cancel
        if modal_x + 30 <= x <= modal_x + 140 and btn_y <= y <= btn_y + 45:
            self.confirm_delete_id = None
            return 'cancel_delete'
        
        # Delete
        if modal_x + modal_width - 140 <= x <= modal_x + modal_width - 30 and btn_y <= y <= btn_y + 45:
            if self.confirm_delete_id and self.recipes_manager:
                self.recipes_manager.remove(self.confirm_delete_id)
            self.confirm_delete_id = None
            return 'deleted'
        
        # Outside modal
        if not (modal_x <= x <= modal_x + modal_width and modal_y <= y <= modal_y + modal_height):
            self.confirm_delete_id = None
            return 'cancel_delete'
        
        return None
    
    def handle_scroll(self, delta):
        if not self.confirm_delete_id:
            self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset + delta))