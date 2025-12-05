"""
ui_new/views/saved_recipes_view.py

Description:
    * View for browsing and managing saved AI-generated recipes

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *


class SavedRecipesView:
    """View for saved AI-generated recipes."""
    
    def __init__(self, fonts):
        self.fonts = fonts
        self.recipes_manager = None
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Delete confirmation
        self.confirm_delete_id = None
    
    def set_manager(self, recipes_manager):
        self.recipes_manager = recipes_manager
    
    def draw(self, screen, state, keyboard_visible=False):
        content_bottom = HEIGHT - NAV_HEIGHT
        
        self._draw_header(screen)
        self._draw_recipes_list(screen, content_bottom)
        
        if self.confirm_delete_id:
            self._draw_delete_modal(screen)
    
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
        title = self.fonts['header'].render("Saved Creations", True, SOFT_BLACK)
        screen.blit(title, (130, 25))
        
        # Count
        if self.recipes_manager:
            count = len(self.recipes_manager.get_all())
            subtitle = self.fonts['small'].render(f"{count} recipes", True, DARK_GRAY)
            screen.blit(subtitle, (130, 55))
    
    def _draw_recipes_list(self, screen, content_bottom):
        y_start = 90
        visible_height = content_bottom - y_start
        
        if not self.recipes_manager:
            return
        
        recipes = self.recipes_manager.get_all()
        
        if not recipes:
            # Empty state
            self._draw_empty_state(screen)
            return
        
        # Calculate scroll
        content_height = len(recipes) * 90 + 20
        self.max_scroll = max(0, content_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        # Create scrollable surface
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        content_surface.fill(WHITE)
        
        y = 10
        for recipe in recipes:
            self._draw_recipe_card(content_surface, recipe, y)
            y += 90
        
        screen.blit(content_surface, (0, y_start), (0, self.scroll_offset, WIDTH, visible_height))
    
    def _draw_empty_state(self, screen):
        # Sparkle icon
        cx, cy = WIDTH // 2, 220
        pygame.draw.circle(screen, LIGHT_GRAY, (cx, cy), 50)
        self._draw_sparkle(screen, cx, cy - 5, 25, MID_GRAY)
        self._draw_sparkle(screen, cx + 18, cy - 22, 12, MID_GRAY)
        
        # Text
        msg = self.fonts['body'].render("No saved creations yet", True, DARK_GRAY)
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, cy + 70))
        
        hint = self.fonts['small'].render("AI-generated recipes will appear here", True, MID_GRAY)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, cy + 105))
    
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
        card_rect = pygame.Rect(30, y, WIDTH - 60, 80)
        pygame.draw.rect(surface, LIGHT_GRAY, card_rect, border_radius=12)
        
        # Sparkle icon
        icon_x = card_rect.x + 35
        icon_y = card_rect.y + 40
        pygame.draw.circle(surface, (160, 100, 220), (icon_x, icon_y), 22)
        self._draw_sparkle(surface, icon_x, icon_y - 2, 10, WHITE)
        
        # Recipe name
        name = recipe.get('name', 'Untitled')
        if len(name) > 35:
            name = name[:32] + "..."
        name_text = self.fonts['body'].render(name, True, SOFT_BLACK)
        surface.blit(name_text, (card_rect.x + 70, card_rect.y + 15))
        
        # Date
        created = recipe.get('created_at', '')[:10]  # Just the date part
        date_text = self.fonts['caption'].render(f"Created {created}", True, DARK_GRAY)
        surface.blit(date_text, (card_rect.x + 70, card_rect.y + 45))
        
        # Delete button
        delete_x = card_rect.x + card_rect.width - 50
        delete_y = card_rect.y + 25
        delete_rect = pygame.Rect(delete_x, delete_y, 30, 30)
        pygame.draw.rect(surface, (240, 200, 200), delete_rect, border_radius=8)
        
        # X icon
        pygame.draw.line(surface, (200, 80, 80), (delete_x + 9, delete_y + 9), (delete_x + 21, delete_y + 21), 2)
        pygame.draw.line(surface, (200, 80, 80), (delete_x + 21, delete_y + 9), (delete_x + 9, delete_y + 21), 2)
    
    def _draw_delete_modal(self, screen):
        # Overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Modal
        modal_width = 400
        modal_height = 180
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        pygame.draw.rect(screen, WHITE, (modal_x, modal_y, modal_width, modal_height), border_radius=16)
        
        # Title
        title = self.fonts['header'].render("Delete Recipe?", True, SOFT_BLACK)
        screen.blit(title, (modal_x + 30, modal_y + 25))
        
        # Message
        msg = self.fonts['body'].render("This cannot be undone.", True, DARK_GRAY)
        screen.blit(msg, (modal_x + 30, modal_y + 70))
        
        # Buttons
        btn_y = modal_y + modal_height - 55
        
        # Cancel
        cancel_rect = pygame.Rect(modal_x + 30, btn_y, 100, 40)
        pygame.draw.rect(screen, LIGHT_GRAY, cancel_rect, border_radius=8)
        cancel_text = self.fonts['small'].render("Cancel", True, SOFT_BLACK)
        screen.blit(cancel_text, (cancel_rect.x + 22, cancel_rect.y + 10))
        
        # Delete
        delete_rect = pygame.Rect(modal_x + modal_width - 130, btn_y, 100, 40)
        pygame.draw.rect(screen, (200, 60, 60), delete_rect, border_radius=8)
        delete_text = self.fonts['small'].render("Delete", True, WHITE)
        screen.blit(delete_text, (delete_rect.x + 24, delete_rect.y + 10))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        # Handle delete modal
        if self.confirm_delete_id:
            return self._handle_modal_touch(x, y)
        
        # Back button
        if 30 <= x <= 110 and 20 <= y <= 60:
            return 'back'
        
        if not self.recipes_manager:
            return None
        
        recipes = self.recipes_manager.get_all()
        if not recipes:
            return None
        
        # Recipe list - check if tap is in the list area
        y_start = 90
        if y < y_start:
            return None
        
        content_y = y - y_start + self.scroll_offset
        
        item_y = 10
        for recipe in recipes:
            card_rect_x = 30
            card_width = WIDTH - 60
            card_height = 80
            
            # Check if tap is in this card's Y range
            if item_y <= content_y <= item_y + card_height:
                # Check delete button first (right side of card)
                delete_x = card_rect_x + card_width - 50
                
                if delete_x <= x <= delete_x + 30:
                    self.confirm_delete_id = recipe['id']
                    return 'show_delete_confirm'
                
                # Check card tap (view recipe) - rest of card
                if card_rect_x <= x <= delete_x:
                    return f"view_saved_{recipe['id']}"
            
            item_y += 90
        
        return None
    
    def _handle_modal_touch(self, x, y):
        modal_width = 400
        modal_height = 180
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        btn_y = modal_y + modal_height - 55
        
        # Cancel
        if modal_x + 30 <= x <= modal_x + 130 and btn_y <= y <= btn_y + 40:
            self.confirm_delete_id = None
            return 'cancel_delete'
        
        # Delete
        if modal_x + modal_width - 130 <= x <= modal_x + modal_width - 30 and btn_y <= y <= btn_y + 40:
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