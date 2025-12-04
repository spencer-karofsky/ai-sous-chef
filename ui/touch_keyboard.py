"""
ui/touch_keyboard.py

Description:
    * On-screen touch keyboard for AI Sous Chef

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui.constants import (
    WIDTH, HEIGHT, KEYBOARD_HEIGHT, KEYBOARD_ROWS,
    KEY_WIDTH, KEY_HEIGHT, KEY_MARGIN,
    BLUE_DARK, BLUE_MID, BLUE_LIGHT, CREAM, ACCENT, RED_SOFT, GOLD_DARK, WHITE
)


class TouchKeyboard:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.visible = False
        self.shift = False
        self.y_offset = HEIGHT - KEYBOARD_HEIGHT
        self.pressed_key = None
        self.press_time = 0
        self.PRESS_DURATION = 100  # milliseconds

    def draw(self):
        if not self.visible:
            return

        # Keyboard background (with bottom margin)
        pygame.draw.rect(self.screen, BLUE_DARK, (0, self.y_offset, WIDTH, KEYBOARD_HEIGHT + 10))
        pygame.draw.rect(self.screen, ACCENT, (0, self.y_offset, WIDTH, 3))

        y = self.y_offset + 12
        current_time = pygame.time.get_ticks()

        for row in KEYBOARD_ROWS:
            # Center each row
            row_width = len(row) * (KEY_WIDTH + KEY_MARGIN) - KEY_MARGIN
            x = (WIDTH - row_width) // 2

            for key in row:
                display_key = key.upper() if self.shift else key

                # Check if this key is pressed
                is_pressed = (self.pressed_key == key and
                              current_time - self.press_time < self.PRESS_DURATION)

                # Key background
                key_rect = pygame.Rect(x, y, KEY_WIDTH, KEY_HEIGHT)
                key_color = ACCENT if is_pressed else BLUE_MID
                pygame.draw.rect(self.screen, key_color, key_rect, border_radius=6)
                pygame.draw.rect(self.screen, BLUE_LIGHT, key_rect, 2, border_radius=6)

                # Key label
                label = self.font.render(display_key, True, CREAM)
                label_x = x + (KEY_WIDTH - label.get_width()) // 2
                label_y = y + (KEY_HEIGHT - label.get_height()) // 2
                self.screen.blit(label, (label_x, label_y))

                x += KEY_WIDTH + KEY_MARGIN

            y += KEY_HEIGHT + KEY_MARGIN

        # Special keys row
        self._draw_special_keys(y, current_time)

    def _draw_special_keys(self, y, current_time):
        special_keys = [('Shift', 100), ('SPACE', 450), ('<-', 100), ('GO', 100), ('X', 70)]
        x = (WIDTH - sum(w for _, w in special_keys) - KEY_MARGIN * 4) // 2

        for label, width in special_keys:
            is_pressed = (self.pressed_key == label and
                          current_time - self.press_time < self.PRESS_DURATION)

            key_rect = pygame.Rect(x, y, width, KEY_HEIGHT)
            if is_pressed:
                color = WHITE
            elif label == 'GO':
                color = ACCENT
            elif label == 'X':
                color = RED_SOFT
            elif label == 'Shift' and self.shift:
                color = GOLD_DARK
            else:
                color = BLUE_MID
            pygame.draw.rect(self.screen, color, key_rect, border_radius=6)
            pygame.draw.rect(self.screen, ACCENT if label == 'GO' else BLUE_LIGHT, key_rect, 2, border_radius=6)

            text_color = BLUE_DARK if label == 'GO' else WHITE
            text = self.font.render(label, True, text_color)
            text_x = x + (width - text.get_width()) // 2
            text_y = y + (KEY_HEIGHT - text.get_height()) // 2
            self.screen.blit(text, (text_x, text_y))

            x += width + KEY_MARGIN

    def handle_touch(self, pos):
        if not self.visible:
            return None

        x, y = pos
        if y < self.y_offset:
            return None

        # Check regular keys
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

        # Check special keys
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
                elif action == 'BACKSPACE':
                    return 'BACKSPACE'
                elif action == 'GO':
                    return 'GO'
                elif action == 'HIDE':
                    return 'HIDE'
            key_x += width + KEY_MARGIN

        return None