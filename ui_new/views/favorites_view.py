"""
ui_new/views/favorites_view.py

Description:
    * Favorites view - displays saved recipes

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *


class FavoritesView:
    def __init__(self, fonts):
        self.fonts = fonts
        self.scroll_offset = 0
        self.max_scroll = 0
        self.favorites_manager = None  # Set by app
        
        # Delete confirmation
        self.delete_confirm_id = None
    
    def set_manager(self, manager):
        self.favorites_manager = manager
    
    def draw(self, screen, state, keyboard_visible=False):
        content_bottom = HEIGHT - NAV_HEIGHT
        
        self._draw_header(screen)
        
        if not self.favorites_manager or self.favorites_manager.count() == 0:
            self._draw_empty_state(screen)
        else:
            self._draw_favorites_list(screen, content_bottom)
        
        # Delete confirmation modal
        if self.delete_confirm_id:
            self._draw_delete_modal(screen)
    
    def _draw_header(self, screen):
        y = 25
        title = self.fonts['header'].render("Favorites", True, SOFT_BLACK)
        screen.blit(title, (40, y))
        
        # Count badge
        if self.favorites_manager:
            count = self.favorites_manager.count()
            if count > 0:
                count_text = self.fonts['small'].render(f"{count} saved", True, DARK_GRAY)
                screen.blit(count_text, (40, y + 40))
    
    def _draw_empty_state(self, screen):
        cy = HEIGHT // 2 - 40
        cx = WIDTH // 2
        
        # Empty heart icon
        self._draw_heart_outline(screen, cx, cy - 20, 50, MID_GRAY)
        
        text = self.fonts['body'].render("No favorites yet", True, DARK_GRAY)
        screen.blit(text, (cx - text.get_width() // 2, cy + 50))
        
        hint = self.fonts['small'].render("Tap the heart on any recipe to save it", True, MID_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, cy + 90))
    
    def _draw_heart_outline(self, screen, cx, cy, size, color):
        """Draw a heart outline."""
        import math
        scale = size / 30
        points = []
        for i in range(100):
            t = i / 100 * 2 * math.pi
            hx = 16 * (math.sin(t) ** 3)
            hy = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
            px = cx + int(hx * scale)
            py = cy - int(hy * scale)
            points.append((px, py))
        if len(points) > 2:
            pygame.draw.polygon(screen, color, points, 3)
    
    def _draw_favorites_list(self, screen, content_bottom):
        favorites = self.favorites_manager.get_all()
        
        # Calculate content height
        content_height = len(favorites) * 100 + 20
        visible_height = content_bottom - 90
        self.max_scroll = max(0, content_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        # Create scrollable surface
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        content_surface.fill(WHITE)
        
        y = 10
        for i, fav in enumerate(favorites):
            self._draw_favorite_card(content_surface, fav, y, i)
            y += 100
        
        # Blit scrolled content
        screen.blit(content_surface, (0, 90), (0, self.scroll_offset, WIDTH, visible_height))
    
    def _draw_favorite_card(self, surface, favorite, y, index):
        card_rect = pygame.Rect(40, y, WIDTH - 80, 90)
        
        # Card background
        pygame.draw.rect(surface, LIGHT_GRAY, card_rect, border_radius=12)
        
        # Heart icon (filled)
        heart_x = card_rect.x + 30
        heart_y = card_rect.y + 45
        self._draw_heart_filled(surface, heart_x, heart_y, 12, SOFT_BLACK)
        
        # Recipe name
        name = favorite.get('name', 'Untitled')
        max_width = card_rect.width - 140
        
        if self.fonts['body'].size(name)[0] > max_width:
            while self.fonts['body'].size(name + "...")[0] > max_width and len(name) > 10:
                name = name[:-1]
            name = name + "..."
        
        name_text = self.fonts['body'].render(name, True, SOFT_BLACK)
        surface.blit(name_text, (card_rect.x + 60, card_rect.y + 18))
        
        # Details
        details_parts = []
        if favorite.get('category'):
            details_parts.append(favorite['category'])
        if favorite.get('total_time'):
            details_parts.append(favorite['total_time'])
        if favorite.get('calories'):
            details_parts.append(f"{favorite['calories']} cal")
        
        details = " • ".join(details_parts) if details_parts else "No details"
        details_text = self.fonts['small'].render(details, True, DARK_GRAY)
        surface.blit(details_text, (card_rect.x + 60, card_rect.y + 52))
        
        # Source badge
        source = favorite.get('source', 'search')
        if source == 'generated':
            badge_text = self.fonts['caption'].render("AI Generated", True, DARK_GRAY)
            badge_x = card_rect.x + card_rect.width - badge_text.get_width() - 45
            surface.blit(badge_text, (badge_x, card_rect.y + 20))
        
        # Delete button (trash icon / X)
        delete_x = card_rect.x + card_rect.width - 35
        delete_y = card_rect.y + 45
        pygame.draw.circle(surface, MID_GRAY, (delete_x, delete_y), 12, 2)
        # X inside
        pygame.draw.line(surface, MID_GRAY, (delete_x - 5, delete_y - 5), (delete_x + 5, delete_y + 5), 2)
        pygame.draw.line(surface, MID_GRAY, (delete_x + 5, delete_y - 5), (delete_x - 5, delete_y + 5), 2)
        
        # Arrow for tap to view
        arrow_x = card_rect.x + card_rect.width - 70
        arrow_y = card_rect.y + 45
        pygame.draw.line(surface, MID_GRAY, (arrow_x, arrow_y - 6), (arrow_x + 6, arrow_y), 2)
        pygame.draw.line(surface, MID_GRAY, (arrow_x + 6, arrow_y), (arrow_x, arrow_y + 6), 2)
    
    def _draw_heart_filled(self, surface, cx, cy, size, color):
        """Draw a filled heart."""
        import math
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
            pygame.draw.polygon(surface, color, points)
    
    def _draw_delete_modal(self, screen):
        # Overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Modal
        modal_width = 400
        modal_height = 200
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        pygame.draw.rect(screen, WHITE, (modal_x, modal_y, modal_width, modal_height), border_radius=16)
        
        # Title
        title = self.fonts['header'].render("Remove Favorite?", True, SOFT_BLACK)
        screen.blit(title, (modal_x + 30, modal_y + 25))
        
        # Message
        msg = self.fonts['body'].render("This recipe will be removed", True, DARK_GRAY)
        screen.blit(msg, (modal_x + 30, modal_y + 80))
        
        # Buttons
        btn_y = modal_y + modal_height - 60
        
        # Cancel
        cancel_rect = pygame.Rect(modal_x + 30, btn_y, 100, 40)
        pygame.draw.rect(screen, LIGHT_GRAY, cancel_rect, border_radius=8)
        cancel_text = self.fonts['small'].render("Cancel", True, SOFT_BLACK)
        screen.blit(cancel_text, (cancel_rect.x + 20, cancel_rect.y + 10))
        
        # Remove
        remove_rect = pygame.Rect(modal_x + modal_width - 130, btn_y, 100, 40)
        pygame.draw.rect(screen, (200, 60, 60), remove_rect, border_radius=8)
        remove_text = self.fonts['small'].render("Remove", True, WHITE)
        screen.blit(remove_text, (remove_rect.x + 15, remove_rect.y + 10))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        # Handle delete modal
        if self.delete_confirm_id:
            return self._handle_modal_touch(x, y)
        
        if not self.favorites_manager or self.favorites_manager.count() == 0:
            return None
        
        # Adjust for scroll
        content_y = y - 90 + self.scroll_offset
        
        favorites = self.favorites_manager.get_all()
        card_y = 10
        
        for i, fav in enumerate(favorites):
            card_rect = pygame.Rect(40, card_y, WIDTH - 80, 90)
            
            if card_y <= content_y <= card_y + 90:
                # Check delete button (right side)
                delete_x = card_rect.x + card_rect.width - 35
                if delete_x - 20 <= x <= delete_x + 20:
                    self.delete_confirm_id = fav['id']
                    return 'delete_prompt'
                
                # Tap on card = view recipe
                if 40 <= x <= WIDTH - 80:
                    return f"view_{fav['id']}"
            
            card_y += 100
        
        return None
    
    def _handle_modal_touch(self, x, y):
        modal_width = 400
        modal_height = 200
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        btn_y = modal_y + modal_height - 60
        
        # Cancel button
        if modal_x + 30 <= x <= modal_x + 130 and btn_y <= y <= btn_y + 40:
            self.delete_confirm_id = None
            return 'delete_cancelled'
        
        # Remove button
        if modal_x + modal_width - 130 <= x <= modal_x + modal_width - 30 and btn_y <= y <= btn_y + 40:
            if self.favorites_manager and self.delete_confirm_id:
                self.favorites_manager.remove(self.delete_confirm_id)
            self.delete_confirm_id = None
            return 'deleted'
        
        # Click outside to cancel
        if not (modal_x <= x <= modal_x + modal_width and modal_y <= y <= modal_y + modal_height):
            self.delete_confirm_id = None
            return 'delete_cancelled'
        
        return None
    
    def handle_scroll(self, delta):
        if not self.delete_confirm_id:
            self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset + delta))