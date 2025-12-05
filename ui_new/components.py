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
        pygame.draw.rect(self.screen, WHITE, (0, self.y, WIDTH, NAV_HEIGHT))
        pygame.draw.line(self.screen, DIVIDER, (0, self.y), (WIDTH, self.y), 1)
        
        item_width = WIDTH // len(NAV_ITEMS)
        
        for i, name in enumerate(NAV_ITEMS):
            x = i * item_width
            cx = x + item_width // 2
            is_active = (name == self.active)
            
            color = SOFT_BLACK if is_active else MID_GRAY
            
            icon_x = cx - NAV_ICON_SIZE // 2
            icon_y = self.y + 15
            draw_icon(self.screen, name, icon_x, icon_y, NAV_ICON_SIZE, color, filled=is_active)
            
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


class TouchKeyboard:
    """On-screen touch keyboard."""
    
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.visible = False
        self.shift = False
        self.y_offset = HEIGHT - KEYBOARD_HEIGHT
        self.pressed_key = None
        self.press_time = 0
        self.PRESS_DURATION = 100

    def draw(self):
        if not self.visible:
            return

        pygame.draw.rect(self.screen, WHITE, (0, self.y_offset, WIDTH, KEYBOARD_HEIGHT + 10))
        pygame.draw.line(self.screen, DIVIDER, (0, self.y_offset), (WIDTH, self.y_offset), 1)

        y = self.y_offset + 12
        current_time = pygame.time.get_ticks()

        for row in KEYBOARD_ROWS:
            row_width = len(row) * (KEY_WIDTH + KEY_MARGIN) - KEY_MARGIN
            x = (WIDTH - row_width) // 2

            for key in row:
                display_key = key.upper() if self.shift else key
                is_pressed = (self.pressed_key == key and
                              current_time - self.press_time < self.PRESS_DURATION)

                key_rect = pygame.Rect(x, y, KEY_WIDTH, KEY_HEIGHT)
                
                if is_pressed:
                    pygame.draw.rect(self.screen, SOFT_BLACK, key_rect, border_radius=8)
                    label = self.font.render(display_key, True, WHITE)
                else:
                    pygame.draw.rect(self.screen, LIGHT_GRAY, key_rect, border_radius=8)
                    label = self.font.render(display_key, True, SOFT_BLACK)

                label_x = x + (KEY_WIDTH - label.get_width()) // 2
                label_y = y + (KEY_HEIGHT - label.get_height()) // 2
                self.screen.blit(label, (label_x, label_y))

                x += KEY_WIDTH + KEY_MARGIN
            y += KEY_HEIGHT + KEY_MARGIN

        self._draw_special_keys(y, current_time)

    def _draw_special_keys(self, y, current_time):
        # Changed labels: ⌫ -> backspace arrow, × -> down arrow for hide
        special_keys = [('Shift', 100), ('SPACE', 450), ('DELETE', 100), ('Go', 100), ('HIDE', 70)]
        x = (WIDTH - sum(w for _, w in special_keys) - KEY_MARGIN * 4) // 2

        for label, width in special_keys:
            is_pressed = (self.pressed_key == label and
                        current_time - self.press_time < self.PRESS_DURATION)

            key_rect = pygame.Rect(x, y, width, KEY_HEIGHT)
            
            if label == 'Go':
                bg_color = SOFT_BLACK
                text_color = WHITE
            elif is_pressed:
                bg_color = SOFT_BLACK
                text_color = WHITE
            elif label == 'Shift' and self.shift:
                bg_color = CHARCOAL
                text_color = WHITE
            else:
                bg_color = LIGHT_GRAY
                text_color = SOFT_BLACK
            
            pygame.draw.rect(self.screen, bg_color, key_rect, border_radius=8)
            
            # Draw icons for special keys
            if label == 'DELETE':
                # Backspace arrow icon
                self._draw_backspace_icon(x, y, width, text_color)
            elif label == 'HIDE':
                # Keyboard hide icon (down chevron)
                self._draw_hide_icon(x, y, width, text_color)
            else:
                # Regular text
                text = self.font.render(label, True, text_color)
                text_x = x + (width - text.get_width()) // 2
                text_y = y + (KEY_HEIGHT - text.get_height()) // 2
                self.screen.blit(text, (text_x, text_y))

            x += width + KEY_MARGIN

    def _draw_backspace_icon(self, x, y, width, color):
        """Draw a backspace arrow icon."""
        cx = x + width // 2
        cy = y + KEY_HEIGHT // 2
        
        # Arrow pointing left with x inside
        arrow_width = 24
        arrow_height = 16
        
        # Arrow shape points
        points = [
            (cx - arrow_width // 2, cy),                    # Left point
            (cx - arrow_width // 4, cy - arrow_height // 2), # Top left
            (cx + arrow_width // 2, cy - arrow_height // 2), # Top right
            (cx + arrow_width // 2, cy + arrow_height // 2), # Bottom right
            (cx - arrow_width // 4, cy + arrow_height // 2), # Bottom left
        ]
        pygame.draw.polygon(self.screen, color, points, 2)
        
        # Small X inside
        x_size = 4
        x_cx = cx + 4
        pygame.draw.line(self.screen, color, (x_cx - x_size, cy - x_size), 
                        (x_cx + x_size, cy + x_size), 2)
        pygame.draw.line(self.screen, color, (x_cx + x_size, cy - x_size), 
                        (x_cx - x_size, cy + x_size), 2)

    def _draw_hide_icon(self, x, y, width, color):
        """Draw a keyboard hide icon (chevron down)."""
        cx = x + width // 2
        cy = y + KEY_HEIGHT // 2
        
        # Down chevron
        chevron_width = 16
        chevron_height = 8
        
        pygame.draw.line(self.screen, color, 
                        (cx - chevron_width // 2, cy - chevron_height // 2),
                        (cx, cy + chevron_height // 2), 2)
        pygame.draw.line(self.screen, color,
                        (cx, cy + chevron_height // 2),
                        (cx + chevron_width // 2, cy - chevron_height // 2), 2)

    def handle_touch(self, pos):
        if not self.visible:
            return None

        x, y = pos
        if y < self.y_offset:
            return None

        key_y = self.y_offset + 12
        for row in KEYBOARD_ROWS:
            row_width = len(row) * (KEY_WIDTH + KEY_MARGIN) - KEY_MARGIN
            key_x = (WIDTH - row_width) // 2

            for key in row:
                key_rect = pygame.Rect(key_x, key_y, KEY_WIDTH, KEY_HEIGHT)
                if key_rect.collidepoint(pos):
                    result = key.upper() if self.shift else key
                    self.pressed_key = key
                    self.press_time = pygame.time.get_ticks()
                    self.shift = False
                    return result
                key_x += KEY_WIDTH + KEY_MARGIN
            key_y += KEY_HEIGHT + KEY_MARGIN

        return self._handle_special_keys(pos, key_y)

    def _handle_special_keys(self, pos, y):
        special_keys = [('SHIFT', 100), ('SPACE', 450), ('BACKSPACE', 100), ('GO', 100), ('HIDE', 70)]
        key_x = (WIDTH - sum(w for _, w in special_keys) - KEY_MARGIN * 4) // 2

        for action, width in special_keys:
            key_rect = pygame.Rect(key_x, y, width, KEY_HEIGHT)
            if key_rect.collidepoint(pos):
                self.pressed_key = action
                self.press_time = pygame.time.get_ticks()
                if action == 'SHIFT':
                    self.shift = not self.shift
                    return None
                elif action == 'SPACE':
                    return ' '
                return action
            key_x += width + KEY_MARGIN
        return None