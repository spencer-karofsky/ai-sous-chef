"""
ui_new/views/preferences_view.py

Description:
    * Dietary preferences and ingredient exclusions view

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *


class PreferencesView:
    """View for selecting dietary preferences or ingredient exclusions."""
    
    DIETARY_OPTIONS = [
        'Vegetarian',
        'Vegan',
        'Gluten-Free',
        'Dairy-Free',
        'Keto',
        'Paleo',
        'Low-Carb',
        'Low-Sodium',
        'Nut-Free',
        'Halal',
        'Kosher',
        'Pescatarian',
    ]
    
    EXCLUSION_OPTIONS = [
        'Peanuts',
        'Tree Nuts',
        'Milk',
        'Eggs',
        'Wheat',
        'Soy',
        'Fish',
        'Shellfish',
        'Sesame',
        'Gluten',
        'Lactose',
        'Red Meat',
        'Pork',
        'Alcohol',
        'Caffeine',
        'Sugar',
        'Mushrooms',
        'Onions',
        'Garlic',
        'Cilantro',
    ]
    
    def __init__(self, fonts, config):
        self.fonts = fonts
        self.config = config
        self.mode = 'dietary'
        self.scroll_offset = 0
        self.max_scroll = 0
        self.custom_text = ""
        self.show_custom_input = False
    
    def set_mode(self, mode):
        self.mode = mode
        self.scroll_offset = 0
        self.custom_text = ""
        self.show_custom_input = False
    
    def _get_options(self):
        if self.mode == 'dietary':
            return self.DIETARY_OPTIONS
        else:
            return self.EXCLUSION_OPTIONS
    
    def _get_selected(self):
        if self.mode == 'dietary':
            return self.config.get('dietary', [])
        else:
            return self.config.get('exclusions', [])
    
    def _save_selected(self, selected):
        if self.mode == 'dietary':
            self.config.set('dietary', selected)
        else:
            self.config.set('exclusions', selected)
    
    def draw(self, screen, state, keyboard_visible=False):
        content_bottom = HEIGHT - NAV_HEIGHT
        if keyboard_visible:
            content_bottom = HEIGHT - KEYBOARD_HEIGHT
        
        self._draw_header(screen)
        self._draw_options_list(screen, content_bottom)
        
        if self.show_custom_input:
            self._draw_custom_modal(screen, keyboard_visible)
    
    def _draw_header(self, screen):
        back_rect = pygame.Rect(30, 20, 80, 40)
        pygame.draw.rect(screen, LIGHT_GRAY, back_rect, border_radius=20)
        
        ax = back_rect.x + 20
        ay = back_rect.y + 20
        pygame.draw.line(screen, CHARCOAL, (ax + 8, ay - 6), (ax, ay), 2)
        pygame.draw.line(screen, CHARCOAL, (ax, ay), (ax + 8, ay + 6), 2)
        
        back_text = self.fonts['small'].render("Back", True, CHARCOAL)
        screen.blit(back_text, (ax + 15, ay - 9))
        
        if self.mode == 'dietary':
            title_text = "Dietary Preferences"
        else:
            title_text = "Ingredient Exclusions"
        
        title = self.fonts['header'].render(title_text, True, SOFT_BLACK)
        screen.blit(title, (130, 25))
        
        selected = self._get_selected()
        count_text = f"{len(selected)} selected"
        subtitle = self.fonts['small'].render(count_text, True, DARK_GRAY)
        screen.blit(subtitle, (130, 58))
    
    def _draw_options_list(self, screen, content_bottom):
        y_start = 100
        visible_height = content_bottom - y_start
        
        options = self._get_options()
        selected = self._get_selected()
        
        all_options = list(options)
        for item in selected:
            if item not in all_options:
                all_options.append(item)
        
        # +1 row for the "Other" card
        rows = (len(all_options) + 1) // 2 + 1
        content_height = rows * 70 + 20
        
        self.max_scroll = max(0, content_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        content_surface.fill(WHITE)
        
        col_width = (WIDTH - 100) // 2
        
        for i, option in enumerate(all_options):
            col = i % 2
            row = i // 2
            x = 40 + col * (col_width + 20)
            y = 10 + row * 70
            is_selected = option in selected
            is_custom = option not in options
            self._draw_option_chip(content_surface, option, x, y, col_width, is_selected, is_custom)
        
        # Draw "Other" card at the end
        other_index = len(all_options)
        other_col = other_index % 2
        other_row = other_index // 2
        other_x = 40 + other_col * (col_width + 20)
        other_y = 10 + other_row * 70
        self._draw_other_chip(content_surface, other_x, other_y, col_width)
        
        screen.blit(content_surface, (0, y_start), (0, self.scroll_offset, WIDTH, visible_height))
    
    def _draw_option_chip(self, surface, text, x, y, width, is_selected, is_custom):
        chip_rect = pygame.Rect(x, y, width, 55)
        
        if is_selected:
            pygame.draw.rect(surface, SOFT_BLACK, chip_rect, border_radius=12)
            text_color = WHITE
        else:
            pygame.draw.rect(surface, LIGHT_GRAY, chip_rect, border_radius=12)
            text_color = SOFT_BLACK
        
        check_x = chip_rect.x + 20
        check_y = chip_rect.y + 18
        check_rect = pygame.Rect(check_x, check_y, 20, 20)
        
        if is_selected:
            pygame.draw.rect(surface, WHITE, check_rect, border_radius=4)
            pygame.draw.line(surface, SOFT_BLACK, (check_x + 4, check_y + 10), (check_x + 8, check_y + 14), 2)
            pygame.draw.line(surface, SOFT_BLACK, (check_x + 8, check_y + 14), (check_x + 16, check_y + 6), 2)
        else:
            pygame.draw.rect(surface, MID_GRAY, check_rect, 2, border_radius=4)
        
        display_text = text
        max_text_width = width - 70
        if self.fonts['body'].size(display_text)[0] > max_text_width:
            while self.fonts['body'].size(display_text + "...")[0] > max_text_width and len(display_text) > 5:
                display_text = display_text[:-1]
            display_text += "..."
        
        label = self.fonts['body'].render(display_text, True, text_color)
        surface.blit(label, (chip_rect.x + 50, chip_rect.y + 15))
        
        if is_custom:
            custom_label = self.fonts['caption'].render("custom", True, MID_GRAY if not is_selected else LIGHT_GRAY)
            surface.blit(custom_label, (chip_rect.x + width - 60, chip_rect.y + 35))
    
    def _draw_other_chip(self, surface, x, y, width):
        """Draw the 'Other' chip that opens custom input."""
        chip_rect = pygame.Rect(x, y, width, 55)
        
        # Dashed border effect using outline
        pygame.draw.rect(surface, MID_GRAY, chip_rect, 2, border_radius=12)
        
        # Plus icon
        plus_x = chip_rect.x + 28
        plus_y = chip_rect.y + 27
        pygame.draw.line(surface, DARK_GRAY, (plus_x - 8, plus_y), (plus_x + 8, plus_y), 2)
        pygame.draw.line(surface, DARK_GRAY, (plus_x, plus_y - 8), (plus_x, plus_y + 8), 2)
        
        # Text
        label = self.fonts['body'].render("Other...", True, DARK_GRAY)
        surface.blit(label, (chip_rect.x + 50, chip_rect.y + 15))
    
    def _draw_custom_modal(self, screen, keyboard_visible):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        modal_width = 500
        modal_height = 200
        modal_x = (WIDTH - modal_width) // 2
        modal_y = 80 if keyboard_visible else (HEIGHT - modal_height) // 2
        
        pygame.draw.rect(screen, WHITE, (modal_x, modal_y, modal_width, modal_height), border_radius=16)
        
        if self.mode == 'dietary':
            title_text = "Add Custom Diet"
        else:
            title_text = "Add Custom Exclusion"
        
        title = self.fonts['header'].render(title_text, True, SOFT_BLACK)
        screen.blit(title, (modal_x + 30, modal_y + 20))
        
        field_rect = pygame.Rect(modal_x + 30, modal_y + 75, modal_width - 60, 50)
        pygame.draw.rect(screen, LIGHT_GRAY, field_rect, border_radius=10)
        
        if self.custom_text:
            input_text = self.fonts['body'].render(self.custom_text, True, SOFT_BLACK)
        else:
            input_text = self.fonts['body'].render("Enter name...", True, MID_GRAY)
        screen.blit(input_text, (field_rect.x + 15, field_rect.y + 12))
        
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = field_rect.x + 15 + self.fonts['body'].size(self.custom_text)[0] + 2
            pygame.draw.rect(screen, SOFT_BLACK, (cursor_x, field_rect.y + 12, 2, 26))
        
        btn_y = modal_y + modal_height - 55
        
        cancel_rect = pygame.Rect(modal_x + 30, btn_y, 100, 40)
        pygame.draw.rect(screen, LIGHT_GRAY, cancel_rect, border_radius=8)
        cancel_text = self.fonts['small'].render("Cancel", True, SOFT_BLACK)
        screen.blit(cancel_text, (cancel_rect.x + 20, cancel_rect.y + 10))
        
        add_rect = pygame.Rect(modal_x + modal_width - 130, btn_y, 100, 40)
        btn_color = SOFT_BLACK if self.custom_text.strip() else MID_GRAY
        pygame.draw.rect(screen, btn_color, add_rect, border_radius=8)
        add_text = self.fonts['small'].render("Add", True, WHITE)
        screen.blit(add_text, (add_rect.x + 35, add_rect.y + 10))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        if self.show_custom_input:
            return self._handle_modal_touch(x, y, keyboard_visible)
        
        if 30 <= x <= 110 and 20 <= y <= 60:
            return 'back'
        
        y_start = 100
        content_y = y - y_start + self.scroll_offset
        
        options = self._get_options()
        selected = self._get_selected()
        
        all_options = list(options)
        for item in selected:
            if item not in all_options:
                all_options.append(item)
        
        col_width = (WIDTH - 100) // 2
        
        # Check predefined options
        for i, option in enumerate(all_options):
            col = i % 2
            row = i // 2
            chip_x = 40 + col * (col_width + 20)
            chip_y = 10 + row * 70
            
            if chip_x <= x <= chip_x + col_width and chip_y <= content_y <= chip_y + 55:
                selected = list(self._get_selected())
                if option in selected:
                    selected.remove(option)
                else:
                    selected.append(option)
                self._save_selected(selected)
                return f'toggle_{option}'
        
        # Check "Other" chip
        other_index = len(all_options)
        other_col = other_index % 2
        other_row = other_index // 2
        other_x = 40 + other_col * (col_width + 20)
        other_y = 10 + other_row * 70
        
        if other_x <= x <= other_x + col_width and other_y <= content_y <= other_y + 55:
            self.show_custom_input = True
            self.custom_text = ""
            return 'show_custom'
        
        return None
    
    def _handle_modal_touch(self, x, y, keyboard_visible):
        modal_width = 500
        modal_height = 200
        modal_x = (WIDTH - modal_width) // 2
        modal_y = 80 if keyboard_visible else (HEIGHT - modal_height) // 2
        
        btn_y = modal_y + modal_height - 55
        
        if modal_x + 30 <= x <= modal_x + 130 and btn_y <= y <= btn_y + 40:
            self.show_custom_input = False
            self.custom_text = ""
            return 'cancel'
        
        if modal_x + modal_width - 130 <= x <= modal_x + modal_width - 30 and btn_y <= y <= btn_y + 40:
            if self.custom_text.strip():
                selected = list(self._get_selected())
                if self.custom_text.strip() not in selected:
                    selected.append(self.custom_text.strip())
                    self._save_selected(selected)
                self.show_custom_input = False
                self.custom_text = ""
                return 'added_custom'
        
        field_rect = pygame.Rect(modal_x + 30, modal_y + 75, modal_width - 60, 50)
        if field_rect.collidepoint(x, y):
            return 'focus_custom'
        
        if not (modal_x <= x <= modal_x + modal_width and modal_y <= y <= modal_y + modal_height):
            self.show_custom_input = False
            self.custom_text = ""
            return 'cancel'
        
        return None
    
    def handle_keyboard_input(self, key):
        if not self.show_custom_input:
            return
        
        if key == 'BACKSPACE':
            self.custom_text = self.custom_text[:-1]
        elif key == 'GO':
            if self.custom_text.strip():
                selected = list(self._get_selected())
                if self.custom_text.strip() not in selected:
                    selected.append(self.custom_text.strip())
                    self._save_selected(selected)
                self.show_custom_input = False
                self.custom_text = ""
        elif key not in ('HIDE', 'SHIFT'):
            self.custom_text += key
    
    def handle_scroll(self, delta):
        if not self.show_custom_input:
            self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset + delta))