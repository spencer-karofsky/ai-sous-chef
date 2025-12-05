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
        
        # Subtle sage top border
        pygame.draw.line(self.screen, SAGE, (0, self.y), (WIDTH, self.y), 1)
        
        item_width = WIDTH // len(NAV_ITEMS)
        
        for i, name in enumerate(NAV_ITEMS):
            x = i * item_width
            cx = x + item_width // 2
            is_active = (name == self.active)
            
            # Active = teal, inactive = muted sage
            color = TEAL if is_active else (120, 130, 118)
            
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
    """On-screen touch keyboard - half screen height."""
    
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.visible = False
        self.shift = False
        self.pressed_key = None
        self.press_time = 0
        self.PRESS_DURATION = 100
        
        # Target half screen height
        self.actual_height = HEIGHT // 2
        self.y_offset = HEIGHT - self.actual_height
        
        # Calculate key dimensions to fill the space
        num_rows = len(KEYBOARD_ROWS) + 1  # +1 for special keys row
        self.vertical_padding = 10
        self.horizontal_padding = 10
        self.row_spacing = 6
        self.key_margin = 5
        
        # Calculate key height to fill available vertical space
        available_height = self.actual_height - (self.vertical_padding * 2) - (self.row_spacing * (num_rows - 1))
        self.key_height = available_height // num_rows
        
        # Calculate key width to fill available horizontal space
        # Use the longest row (usually first row with 10 keys) to determine width
        max_keys_in_row = max(len(row) for row in KEYBOARD_ROWS)
        available_width = WIDTH - (self.horizontal_padding * 2) - (self.key_margin * (max_keys_in_row - 1))
        self.key_width = available_width // max_keys_in_row

    def draw(self):
        if not self.visible:
            return

        # Warm cream background matching app palette
        pygame.draw.rect(self.screen, (252, 245, 235), (0, self.y_offset, WIDTH, self.actual_height))
        # Sage top border
        pygame.draw.line(self.screen, SAGE, (0, self.y_offset), (WIDTH, self.y_offset), 1)

        y = self.y_offset + self.vertical_padding
        current_time = pygame.time.get_ticks()

        for row in KEYBOARD_ROWS:
            # Calculate width for this row to center it
            row_width = len(row) * (self.key_width + self.key_margin) - self.key_margin
            x = (WIDTH - row_width) // 2

            for key in row:
                display_key = key.upper() if self.shift else key
                is_pressed = (self.pressed_key == key and
                              current_time - self.press_time < self.PRESS_DURATION)

                key_rect = pygame.Rect(x, y, self.key_width, self.key_height)
                
                if is_pressed:
                    # Pressed state: teal background
                    pygame.draw.rect(self.screen, TEAL, key_rect, border_radius=10)
                    label = self.font.render(display_key, True, WHITE)
                else:
                    # Normal state: white with sage border
                    pygame.draw.rect(self.screen, WHITE, key_rect, border_radius=10)
                    pygame.draw.rect(self.screen, SAGE, key_rect, border_radius=10, width=1)
                    label = self.font.render(display_key, True, SOFT_BLACK)

                label_x = x + (self.key_width - label.get_width()) // 2
                label_y = y + (self.key_height - label.get_height()) // 2
                self.screen.blit(label, (label_x, label_y))

                x += self.key_width + self.key_margin
            y += self.key_height + self.row_spacing

        self._draw_special_keys(y, current_time)

    def _draw_special_keys(self, y, current_time):
        # Special keys fill the full width
        available_width = WIDTH - (self.horizontal_padding * 2)
        
        # Proportions for special keys
        proportions = [0.12, 0.46, 0.14, 0.16, 0.08]  # Shift, Space, Delete, Go, Hide
        labels = ['Shift', 'SPACE', 'DELETE', 'Go', 'HIDE']
        
        # Calculate widths and account for margins
        num_keys = len(labels)
        total_margin = self.key_margin * (num_keys - 1)
        keys_width = available_width - total_margin
        widths = [int(keys_width * p) for p in proportions]
        
        # Adjust last key to fill any rounding gap
        widths[-1] = available_width - sum(widths[:-1]) - total_margin
        
        x = self.horizontal_padding

        for i, (label, width) in enumerate(zip(labels, widths)):
            is_pressed = (self.pressed_key == label and
                        current_time - self.press_time < self.PRESS_DURATION)

            key_rect = pygame.Rect(x, y, width, self.key_height)
            
            if label == 'Go':
                # Go button: teal (primary action)
                bg_color = TEAL
                text_color = WHITE
            elif is_pressed:
                # Pressed state: teal
                bg_color = TEAL
                text_color = WHITE
            elif label == 'Shift' and self.shift:
                # Shift active: sage (darker)
                bg_color = SAGE
                text_color = WHITE
            else:
                # Normal special keys: sage light with sage border
                bg_color = SAGE_LIGHT
                text_color = SOFT_BLACK
            
            pygame.draw.rect(self.screen, bg_color, key_rect, border_radius=10)
            
            # Add border for non-filled buttons
            if bg_color == SAGE_LIGHT:
                pygame.draw.rect(self.screen, SAGE, key_rect, border_radius=10, width=1)
            
            if label == 'DELETE':
                self._draw_backspace_icon(x, y, width, text_color)
            elif label == 'HIDE':
                self._draw_hide_icon(x, y, width, text_color)
            else:
                text = self.font.render(label, True, text_color)
                text_x = x + (width - text.get_width()) // 2
                text_y = y + (self.key_height - text.get_height()) // 2
                self.screen.blit(text, (text_x, text_y))

            x += width + self.key_margin

    def _draw_backspace_icon(self, x, y, width, color):
        """Draw a backspace arrow icon."""
        cx = x + width // 2
        cy = y + self.key_height // 2
        
        # Scale icon with key height
        scale = self.key_height / 50
        arrow_width = int(28 * scale)
        arrow_height = int(18 * scale)
        
        points = [
            (cx - arrow_width // 2, cy),
            (cx - arrow_width // 4, cy - arrow_height // 2),
            (cx + arrow_width // 2, cy - arrow_height // 2),
            (cx + arrow_width // 2, cy + arrow_height // 2),
            (cx - arrow_width // 4, cy + arrow_height // 2),
        ]
        pygame.draw.polygon(self.screen, color, points, 2)
        
        x_size = int(5 * scale)
        x_cx = cx + int(5 * scale)
        pygame.draw.line(self.screen, color, (x_cx - x_size, cy - x_size), 
                        (x_cx + x_size, cy + x_size), 2)
        pygame.draw.line(self.screen, color, (x_cx + x_size, cy - x_size), 
                        (x_cx - x_size, cy + x_size), 2)

    def _draw_hide_icon(self, x, y, width, color):
        """Draw a keyboard hide icon (chevron down)."""
        cx = x + width // 2
        cy = y + self.key_height // 2
        
        # Scale icon with key height
        scale = self.key_height / 50
        chevron_width = int(18 * scale)
        chevron_height = int(10 * scale)
        
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

        key_y = self.y_offset + self.vertical_padding
        for row in KEYBOARD_ROWS:
            row_width = len(row) * (self.key_width + self.key_margin) - self.key_margin
            key_x = (WIDTH - row_width) // 2

            for key in row:
                key_rect = pygame.Rect(key_x, key_y, self.key_width, self.key_height)
                if key_rect.collidepoint(pos):
                    result = key.upper() if self.shift else key
                    self.pressed_key = key
                    self.press_time = pygame.time.get_ticks()
                    self.shift = False
                    return result
                key_x += self.key_width + self.key_margin
            key_y += self.key_height + self.row_spacing

        return self._handle_special_keys(pos, key_y)

    def _handle_special_keys(self, pos, y):
        available_width = WIDTH - (self.horizontal_padding * 2)
        proportions = [0.12, 0.46, 0.14, 0.16, 0.08]
        actions = ['SHIFT', 'SPACE', 'BACKSPACE', 'GO', 'HIDE']
        
        num_keys = len(actions)
        total_margin = self.key_margin * (num_keys - 1)
        keys_width = available_width - total_margin
        widths = [int(keys_width * p) for p in proportions]
        widths[-1] = available_width - sum(widths[:-1]) - total_margin
        
        key_x = self.horizontal_padding

        for action, width in zip(actions, widths):
            key_rect = pygame.Rect(key_x, y, width, self.key_height)
            if key_rect.collidepoint(pos):
                self.pressed_key = action
                self.press_time = pygame.time.get_ticks()
                if action == 'SHIFT':
                    self.shift = not self.shift
                    return None
                elif action == 'SPACE':
                    return ' '
                return action
            key_x += width + self.key_margin
        return None