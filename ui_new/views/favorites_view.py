"""
ui_new/views/favorites_view.py

Description:
    * Favorites view - displays saved recipes

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
import math
from ui_new.constants import *

# Warm background gradient
WARM_BG_TOP = (255, 251, 245)
WARM_BG_BOTTOM = (252, 245, 235)

# Muted sage for cards (20-30% sage over warm white)
CARD_BG = (241, 244, 240)


class FavoritesView:
    def __init__(self, fonts):
        self.fonts = fonts
        self.scroll_offset = 0
        self.max_scroll = 0
        self.favorites_manager = None
        
        self.delete_confirm_id = None
        self.gradient_surface = None
    
    def set_manager(self, manager):
        self.favorites_manager = manager
    
    def _create_gradient(self, width, height):
        """Create warm gradient background."""
        if self.gradient_surface and self.gradient_surface.get_size() == (width, height):
            return self.gradient_surface
        
        self.gradient_surface = pygame.Surface((width, height))
        for y in range(height):
            t = y / height
            r = int(WARM_BG_TOP[0] + (WARM_BG_BOTTOM[0] - WARM_BG_TOP[0]) * t)
            g = int(WARM_BG_TOP[1] + (WARM_BG_BOTTOM[1] - WARM_BG_TOP[1]) * t)
            b = int(WARM_BG_TOP[2] + (WARM_BG_BOTTOM[2] - WARM_BG_TOP[2]) * t)
            pygame.draw.line(self.gradient_surface, (r, g, b), (0, y), (width, y))
        
        return self.gradient_surface
    
    def _draw_gradient_surface(self, surface, height):
        """Draw gradient on a surface."""
        for y in range(height):
            t = y / height
            r = int(WARM_BG_TOP[0] + (WARM_BG_BOTTOM[0] - WARM_BG_TOP[0]) * t)
            g = int(WARM_BG_TOP[1] + (WARM_BG_BOTTOM[1] - WARM_BG_TOP[1]) * t)
            b = int(WARM_BG_TOP[2] + (WARM_BG_BOTTOM[2] - WARM_BG_TOP[2]) * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (surface.get_width(), y))
    
    def draw(self, screen, state, keyboard_visible=False):
        screen.blit(self._create_gradient(WIDTH, HEIGHT), (0, 0))
        content_bottom = HEIGHT - NAV_HEIGHT
        
        self._draw_header(screen)
        
        if not self.favorites_manager or self.favorites_manager.count() == 0:
            self._draw_empty_state(screen)
        else:
            self._draw_favorites_list(screen, content_bottom)
        
        if self.delete_confirm_id:
            self._draw_delete_modal(screen)
    
    def _draw_header(self, screen):
        # Back button - sage light with sage border (matching meal prep)
        back_rect = pygame.Rect(30, 20, 95, 40)
        pygame.draw.rect(screen, SAGE_LIGHT, back_rect, border_radius=20)
        pygame.draw.rect(screen, SAGE, back_rect, border_radius=20, width=1)
        
        # Chevron arrow in teal
        ax = back_rect.x + 22
        ay = back_rect.y + 20
        pygame.draw.line(screen, TEAL, (ax + 8, ay - 6), (ax, ay), 2)
        pygame.draw.line(screen, TEAL, (ax, ay), (ax + 8, ay + 6), 2)
        
        back_text = self.fonts['small'].render("Back", True, SOFT_BLACK)
        screen.blit(back_text, (ax + 18, ay - 9))
        
        # Title - positioned like meal prep
        title = self.fonts['header'].render("Favorites", True, SOFT_BLACK)
        screen.blit(title, (150, 28))
        
        # Count badge
        if self.favorites_manager:
            count = self.favorites_manager.count()
            if count > 0:
                count_text = self.fonts['small'].render(f"{count} saved", True, DARK_GRAY)
                screen.blit(count_text, (WIDTH - 100, 32))
    
    def _draw_empty_state(self, screen):
        cy = HEIGHT // 2 - 40
        cx = WIDTH // 2
        
        # Heart icon circle background (teal like meal prep)
        pygame.draw.circle(screen, TEAL, (cx, cy - 20), 60)
        self._draw_heart_outline(screen, cx, cy - 20, 40, WHITE)
        
        text = self.fonts['header'].render("No Favorites Yet", True, SOFT_BLACK)
        screen.blit(text, (cx - text.get_width() // 2, cy + 60))
        
        hint = self.fonts['body'].render("Tap the heart on any recipe to save it", True, DARK_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, cy + 100))
    
    def _draw_heart_outline(self, screen, cx, cy, size, color):
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
        
        content_height = len(favorites) * 100 + 20
        visible_height = content_bottom - 80
        self.max_scroll = max(0, content_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        # Create scrollable surface with gradient
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        self._draw_gradient_surface(content_surface, content_height)
        
        y = 10
        for i, fav in enumerate(favorites):
            self._draw_favorite_card(content_surface, fav, y, i)
            y += 100
        
        screen.blit(content_surface, (0, 80), (0, self.scroll_offset, WIDTH, visible_height))
    
    def _draw_favorite_card(self, surface, favorite, y, index):
        card_rect = pygame.Rect(30, y, WIDTH - 60, 90)
        
        # Soft shadow
        shadow_surface = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 15), (0, 0, card_rect.width, card_rect.height), border_radius=12)
        surface.blit(shadow_surface, (card_rect.x + 2, card_rect.y + 2))
        
        # Card background - soft sage tint
        pygame.draw.rect(surface, CARD_BG, card_rect, border_radius=12)
        pygame.draw.rect(surface, SAGE, card_rect, border_radius=12, width=1)
        
        # Heart icon (filled, teal)
        heart_x = card_rect.x + 30
        heart_y = card_rect.y + 45
        self._draw_heart_filled(surface, heart_x, heart_y, 12, TEAL)
        
        # Recipe name
        name = favorite.get('name', 'Untitled')
        max_width = card_rect.width - 140
        
        if self.fonts['body'].size(name)[0] > max_width:
            while self.fonts['body'].size(name + "...")[0] > max_width and len(name) > 10:
                name = name[:-1]
            name = name + "..."
        
        name_text = self.fonts['body'].render(name, True, SOFT_BLACK)
        surface.blit(name_text, (card_rect.x + 60, card_rect.y + 18))
        
        # Details as pills
        details_y = card_rect.y + 50
        pill_x = card_rect.x + 60
        
        if favorite.get('category'):
            cat_str = favorite['category']
            cat_width = self.fonts['small'].size(cat_str)[0] + 16
            cat_rect = pygame.Rect(pill_x, details_y, cat_width, 24)
            pygame.draw.rect(surface, SAGE_LIGHT, cat_rect, border_radius=12)
            cat_text = self.fonts['small'].render(cat_str, True, SOFT_BLACK)
            surface.blit(cat_text, (pill_x + 8, details_y + 4))
            pill_x += cat_width + 8
        
        if favorite.get('total_time'):
            time_str = favorite['total_time']
            time_width = self.fonts['small'].size(time_str)[0] + 16
            time_rect = pygame.Rect(pill_x, details_y, time_width, 24)
            pygame.draw.rect(surface, SAGE_LIGHT, time_rect, border_radius=12)
            time_text = self.fonts['small'].render(time_str, True, SOFT_BLACK)
            surface.blit(time_text, (pill_x + 8, details_y + 4))
            pill_x += time_width + 8
        
        if favorite.get('calories'):
            cal_str = f"{favorite['calories']} cal"
            cal_width = self.fonts['small'].size(cal_str)[0] + 16
            cal_rect = pygame.Rect(pill_x, details_y, cal_width, 24)
            pygame.draw.rect(surface, SAGE_LIGHT, cal_rect, border_radius=12)
            cal_text = self.fonts['small'].render(cal_str, True, SOFT_BLACK)
            surface.blit(cal_text, (pill_x + 8, details_y + 4))
        
        # Delete button (X in circle)
        delete_x = card_rect.x + card_rect.width - 35
        delete_y = card_rect.y + 45
        pygame.draw.circle(surface, SAGE_LIGHT, (delete_x, delete_y), 14)
        pygame.draw.line(surface, DARK_GRAY, (delete_x - 5, delete_y - 5), (delete_x + 5, delete_y + 5), 2)
        pygame.draw.line(surface, DARK_GRAY, (delete_x + 5, delete_y - 5), (delete_x - 5, delete_y + 5), 2)
        
        # Chevron arrow (teal)
        arrow_x = card_rect.x + card_rect.width - 70
        arrow_y = card_rect.y + 45
        pygame.draw.line(surface, TEAL, (arrow_x, arrow_y - 6), (arrow_x + 6, arrow_y), 2)
        pygame.draw.line(surface, TEAL, (arrow_x + 6, arrow_y), (arrow_x, arrow_y + 6), 2)
    
    def _draw_heart_filled(self, surface, cx, cy, size, color):
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
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        modal_width = 420
        modal_height = 200
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        pygame.draw.rect(screen, WHITE, (modal_x, modal_y, modal_width, modal_height), border_radius=16)
        
        # Title
        title = self.fonts['header'].render("Remove Favorite?", True, SOFT_BLACK)
        screen.blit(title, (modal_x + 30, modal_y + 25))
        
        # Message
        msg = self.fonts['body'].render("This recipe will be removed from favorites", True, DARK_GRAY)
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
        
        # Remove - red/coral
        remove_rect = pygame.Rect(modal_x + modal_width - 140, btn_y, 110, 45)
        pygame.draw.rect(screen, (200, 80, 80), remove_rect, border_radius=10)
        remove_text = self.fonts['body'].render("Remove", True, WHITE)
        screen.blit(remove_text, (remove_rect.x + (remove_rect.width - remove_text.get_width()) // 2, 
                                  remove_rect.y + 11))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        # Handle delete modal first
        if self.delete_confirm_id:
            return self._handle_modal_touch(x, y)
        
        # Back button
        if 30 <= x <= 125 and 20 <= y <= 60:
            return 'back'
        
        if not self.favorites_manager or self.favorites_manager.count() == 0:
            return None
        
        # Adjust for scroll
        content_y = y - 80 + self.scroll_offset
        
        favorites = self.favorites_manager.get_all()
        card_y = 10
        
        for i, fav in enumerate(favorites):
            card_rect = pygame.Rect(30, card_y, WIDTH - 60, 90)
            
            if card_y <= content_y <= card_y + 90:
                # Check delete button (right side)
                delete_x = card_rect.x + card_rect.width - 35
                if delete_x - 20 <= x <= delete_x + 20:
                    self.delete_confirm_id = fav['id']
                    return 'delete_prompt'
                
                # Tap on card = view recipe
                if 30 <= x <= WIDTH - 60:
                    return f"view_{fav['id']}"
            
            card_y += 100
        
        return None
    
    def _handle_modal_touch(self, x, y):
        modal_width = 420
        modal_height = 200
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        btn_y = modal_y + modal_height - 65
        
        # Cancel button
        if modal_x + 30 <= x <= modal_x + 140 and btn_y <= y <= btn_y + 45:
            self.delete_confirm_id = None
            return 'delete_cancelled'
        
        # Remove button
        if modal_x + modal_width - 140 <= x <= modal_x + modal_width - 30 and btn_y <= y <= btn_y + 45:
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