"""
ui_new/views/settings_view.py

Description:
    * Settings view with organized sections

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
import os
import sys
from ui_new.constants import *


class SettingsView:
    def __init__(self, fonts, config):
        self.fonts = fonts
        self.config = config  # Use passed-in config instead of creating new one
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Active slider dragging
        self.dragging_slider = None
        
        # Modal state
        self.modal = None
        self.modal_data = None
        
        self._build_sections()
    
    def _build_sections(self):
        """Build settings sections from config."""
        units_value = 0 if self.config.get('units') == 'US' else 1
        
        self.sections = [
            {
                'title': 'Network',
                'items': [
                    {'id': 'wifi', 'label': 'Connect to Wi-Fi', 'type': 'action'},
                    {'id': 'network_status', 'label': 'View network status', 'type': 'action'},
                ]
            },
            {
                'title': 'Display',
                'items': [
                    {'id': 'brightness', 'label': 'Brightness', 'type': 'slider', 'value': self.config.get('brightness', 80)},
                ]
            },
            {
                'title': 'Cooking Preferences',
                'items': [
                    {'id': 'dietary', 'label': 'Dietary preferences', 'type': 'action', 'subtitle': ', '.join(self.config.get('dietary', [])) or 'None set'},
                    {'id': 'exclusions', 'label': 'Ingredient exclusions', 'type': 'action', 'subtitle': ', '.join(self.config.get('exclusions', [])) or 'None set'},
                    {'id': 'units', 'label': 'Units', 'type': 'toggle', 'options': ['US', 'Metric'], 'value': units_value},
                    {'id': 'skill', 'label': 'Cooking skill level', 'type': 'action', 'subtitle': self.config.get('skill_level', 'Beginner')},
                ]
            },
            {
                'title': 'Device',
                'items': [
                    {'id': 'system_info', 'label': 'View system info', 'type': 'action'},
                    {'id': 'restart', 'label': 'Restart app', 'type': 'action'},
                    {'id': 'clear_cache', 'label': 'Clear cache', 'type': 'action'},
                    {'id': 'factory_reset', 'label': 'Factory reset', 'type': 'danger', 'subtitle': 'Delete all config files'},
                    {'id': 'shutdown', 'label': 'Shut down', 'type': 'danger', 'subtitle': 'Power off the device'},
                ]
            },
        ]
    
    def draw(self, screen, state, keyboard_visible=False):
        content_bottom = HEIGHT - NAV_HEIGHT
        
        self._draw_header(screen)
        self.max_scroll = self._draw_content(screen, content_bottom)
        
        if self.modal:
            self._draw_modal(screen)
    
    def _draw_header(self, screen):
        y = 25
        title = self.fonts['header'].render("Settings", True, SOFT_BLACK)
        screen.blit(title, (40, y))
    
    def _draw_content(self, screen, content_bottom):
        content_height = self._calculate_content_height()
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        content_surface.fill(WHITE)
        
        y = 10
        
        for section in self.sections:
            y = self._draw_section(content_surface, section, y)
        
        visible_height = content_bottom - 80
        max_scroll = max(0, content_height - visible_height)
        
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
        
        screen.blit(content_surface, (0, 80), (0, self.scroll_offset, WIDTH, visible_height))
        
        return max_scroll
    
    def _calculate_content_height(self):
        height = 20
        for section in self.sections:
            height += 50
            height += len(section['items']) * 70
            height += 20
        return height + 40
    
    def _draw_section(self, surface, section, y):
        title = self.fonts['small'].render(section['title'].upper(), True, DARK_GRAY)
        surface.blit(title, (40, y))
        y += 35
        
        card_height = len(section['items']) * 70 - 10
        card_rect = pygame.Rect(30, y, WIDTH - 60, card_height)
        pygame.draw.rect(surface, LIGHT_GRAY, card_rect, border_radius=12)
        
        item_y = y + 5
        for i, item in enumerate(section['items']):
            self._draw_item(surface, item, item_y, i == len(section['items']) - 1)
            item_y += 70
        
        return y + card_height + 25
    
    def _draw_item(self, surface, item, y, is_last):
        x = 50
        
        if item.get('type') == 'danger':
            label_color = (200, 60, 60)
        else:
            label_color = SOFT_BLACK
        
        label = self.fonts['body'].render(item['label'], True, label_color)
        surface.blit(label, (x, y + 12))
        
        if item.get('subtitle'):
            subtitle = self.fonts['caption'].render(item['subtitle'], True, DARK_GRAY)
            surface.blit(subtitle, (x, y + 38))
        
        right_x = WIDTH - 80
        
        if item['type'] == 'action':
            chevron_x = right_x
            chevron_y = y + 25
            pygame.draw.line(surface, MID_GRAY, (chevron_x, chevron_y - 6), (chevron_x + 6, chevron_y), 2)
            pygame.draw.line(surface, MID_GRAY, (chevron_x + 6, chevron_y), (chevron_x, chevron_y + 6), 2)
        
        elif item['type'] == 'danger':
            chevron_x = right_x
            chevron_y = y + 25
            pygame.draw.line(surface, (200, 60, 60), (chevron_x, chevron_y - 6), (chevron_x + 6, chevron_y), 2)
            pygame.draw.line(surface, (200, 60, 60), (chevron_x + 6, chevron_y), (chevron_x, chevron_y + 6), 2)
        
        elif item['type'] == 'toggle':
            options = item.get('options', ['Off', 'On'])
            current = item.get('value', 0)
            
            toggle_width = 100
            toggle_x = right_x - toggle_width + 20
            toggle_y = y + 15
            
            pygame.draw.rect(surface, DIVIDER, (toggle_x, toggle_y, toggle_width, 32), border_radius=16)
            
            option_width = toggle_width // 2
            selected_x = toggle_x + (current * option_width)
            pygame.draw.rect(surface, SOFT_BLACK, (selected_x + 2, toggle_y + 2, option_width - 4, 28), border_radius=14)
            
            for i, opt in enumerate(options):
                opt_x = toggle_x + (i * option_width) + option_width // 2
                opt_color = WHITE if i == current else DARK_GRAY
                opt_text = self.fonts['caption'].render(opt, True, opt_color)
                surface.blit(opt_text, (opt_x - opt_text.get_width() // 2, toggle_y + 8))
        
        elif item['type'] == 'slider':
            slider_width = 150
            slider_x = right_x - slider_width + 20
            slider_y = y + 23
            value = item.get('value', 50)
            
            item['_slider_rect'] = (slider_x, slider_y - 15, slider_width, 30)
            
            pygame.draw.rect(surface, DIVIDER, (slider_x, slider_y, slider_width, 6), border_radius=3)
            
            fill_width = int(slider_width * value / 100)
            if fill_width > 0:
                pygame.draw.rect(surface, SOFT_BLACK, (slider_x, slider_y, fill_width, 6), border_radius=3)
            
            knob_x = slider_x + fill_width
            pygame.draw.circle(surface, SOFT_BLACK, (knob_x, slider_y + 3), 10)
            pygame.draw.circle(surface, WHITE, (knob_x, slider_y + 3), 6)
        
        if not is_last:
            pygame.draw.line(surface, DIVIDER, (x, y + 60), (WIDTH - 50, y + 60), 1)
        
        return y + 70
    
    def _draw_modal(self, screen):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        modal_width = 500
        modal_height = 350
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        pygame.draw.rect(screen, WHITE, (modal_x, modal_y, modal_width, modal_height), border_radius=16)
        
        if self.modal == 'system_info':
            self._draw_system_info_modal(screen, modal_x, modal_y, modal_width, modal_height)
        elif self.modal == 'network_status':
            self._draw_network_modal(screen, modal_x, modal_y, modal_width, modal_height)
        elif self.modal == 'confirm_reset':
            self._draw_confirm_modal(screen, modal_x, modal_y, modal_width, modal_height,
                                     "Factory Reset", "This will delete all settings and preferences. Are you sure?")
        elif self.modal == 'confirm_clear':
            self._draw_confirm_modal(screen, modal_x, modal_y, modal_width, modal_height,
                                     "Clear Cache", "This will delete all cached data. Continue?")
        elif self.modal == 'confirm_shutdown':
            self._draw_confirm_modal(screen, modal_x, modal_y, modal_width, modal_height,
                                     "Shut Down", "Are you sure you want to power off the device?")
    
    def _draw_system_info_modal(self, screen, x, y, w, h):
        title = self.fonts['header'].render("System Info", True, SOFT_BLACK)
        screen.blit(title, (x + 30, y + 25))
        
        info = self.config.get_system_info()
        info_y = y + 80
        for key, value in info.items():
            key_text = self.fonts['body'].render(f"{key}:", True, DARK_GRAY)
            val_text = self.fonts['body'].render(str(value), True, SOFT_BLACK)
            screen.blit(key_text, (x + 30, info_y))
            screen.blit(val_text, (x + 180, info_y))
            info_y += 40
        
        self._draw_modal_button(screen, x + w - 130, y + h - 60, 100, 40, "Close", SOFT_BLACK)
    
    def _draw_network_modal(self, screen, x, y, w, h):
        title = self.fonts['header'].render("Network Status", True, SOFT_BLACK)
        screen.blit(title, (x + 30, y + 25))
        
        status = self.config.get_network_status()
        info_y = y + 80
        
        status_text = "Connected" if status['connected'] else "Disconnected"
        status_color = (60, 160, 60) if status['connected'] else (200, 60, 60)
        
        label = self.fonts['body'].render("Status:", True, DARK_GRAY)
        value = self.fonts['body'].render(status_text, True, status_color)
        screen.blit(label, (x + 30, info_y))
        screen.blit(value, (x + 180, info_y))
        info_y += 40
        
        if status['connected']:
            label = self.fonts['body'].render("Wi-Fi:", True, DARK_GRAY)
            value = self.fonts['body'].render(status['ssid'], True, SOFT_BLACK)
            screen.blit(label, (x + 30, info_y))
            screen.blit(value, (x + 180, info_y))
            info_y += 40
            
            label = self.fonts['body'].render("IP Address:", True, DARK_GRAY)
            value = self.fonts['body'].render(status['ip'], True, SOFT_BLACK)
            screen.blit(label, (x + 30, info_y))
            screen.blit(value, (x + 180, info_y))
        
        self._draw_modal_button(screen, x + w - 130, y + h - 60, 100, 40, "Close", SOFT_BLACK)
    
    def _draw_confirm_modal(self, screen, x, y, w, h, title_text, message):
        title = self.fonts['header'].render(title_text, True, SOFT_BLACK)
        screen.blit(title, (x + 30, y + 25))
        
        words = message.split()
        lines = []
        current = ""
        for word in words:
            test = current + " " + word if current else word
            if self.fonts['body'].size(test)[0] <= w - 60:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        
        msg_y = y + 90
        for line in lines:
            text = self.fonts['body'].render(line, True, DARK_GRAY)
            screen.blit(text, (x + 30, msg_y))
            msg_y += 35
        
        self._draw_modal_button(screen, x + 30, y + h - 60, 100, 40, "Cancel", LIGHT_GRAY, SOFT_BLACK)
        self._draw_modal_button(screen, x + w - 130, y + h - 60, 100, 40, "Confirm", (200, 60, 60), WHITE)
    
    def _draw_modal_button(self, screen, x, y, w, h, text, bg_color, text_color=None):
        if text_color is None:
            text_color = WHITE
        pygame.draw.rect(screen, bg_color, (x, y, w, h), border_radius=8)
        btn_text = self.fonts['small'].render(text, True, text_color)
        screen.blit(btn_text, (x + (w - btn_text.get_width()) // 2, y + (h - btn_text.get_height()) // 2))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        if self.modal:
            return self._handle_modal_touch(x, y)
        
        content_y = y - 80 + self.scroll_offset
        
        item_y = 10
        for section in self.sections:
            item_y += 35
            item_y += 5
            
            for item in section['items']:
                if 30 <= x <= WIDTH - 30 and item_y <= content_y <= item_y + 60:
                    return self._handle_item_tap(item, x, content_y - item_y)
                item_y += 70
            
            item_y += 20
        
        return None
    
    def _handle_modal_touch(self, x, y):
        modal_width = 500
        modal_height = 350
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        btn_y = modal_y + modal_height - 60
        
        if self.modal in ('system_info', 'network_status'):
            if modal_x + modal_width - 130 <= x <= modal_x + modal_width - 30 and btn_y <= y <= btn_y + 40:
                self.modal = None
                return 'modal_closed'
        
        elif self.modal in ('confirm_reset', 'confirm_clear', 'confirm_shutdown'):
            if modal_x + 30 <= x <= modal_x + 130 and btn_y <= y <= btn_y + 40:
                self.modal = None
                return 'modal_cancelled'
            
            if modal_x + modal_width - 130 <= x <= modal_x + modal_width - 30 and btn_y <= y <= btn_y + 40:
                if self.modal == 'confirm_reset':
                    self.config.factory_reset()
                    self._build_sections()
                elif self.modal == 'confirm_clear':
                    self.config.clear_cache()
                elif self.modal == 'confirm_shutdown':
                    self._do_shutdown()
                self.modal = None
                return 'modal_confirmed'
        
        if not (modal_x <= x <= modal_x + modal_width and modal_y <= y <= modal_y + modal_height):
            self.modal = None
            return 'modal_closed'
        
        return None
    
    def _handle_item_tap(self, item, x, relative_y):
        if item['type'] == 'toggle':
            current = item.get('value', 0)
            options = item.get('options', ['Off', 'On'])
            item['value'] = (current + 1) % len(options)
            
            if item['id'] == 'units':
                self.config.set('units', options[item['value']])
            
            return f"toggle_{item['id']}"
        
        elif item['type'] == 'slider':
            self.dragging_slider = item
            return f"slider_{item['id']}"
        
        elif item['type'] == 'danger':
            if item['id'] == 'factory_reset':
                self.modal = 'confirm_reset'
            elif item['id'] == 'shutdown':
                self.modal = 'confirm_shutdown'
            return f"danger_{item['id']}"
        
        elif item['type'] == 'action':
            if item['id'] == 'wifi':
                return 'navigate_wifi'
            elif item['id'] == 'dietary':
                return 'navigate_dietary'
            elif item['id'] == 'exclusions':
                return 'navigate_exclusions'
            elif item['id'] == 'skill':
                return 'navigate_skill'
            elif item['id'] == 'system_info':
                self.modal = 'system_info'
            elif item['id'] == 'network_status':
                self.modal = 'network_status'
            elif item['id'] == 'clear_cache':
                self.modal = 'confirm_clear'
            elif item['id'] == 'restart':
                os.execv(sys.executable, ['python'] + sys.argv)
            return f"action_{item['id']}"
        
        return None
    
    def handle_drag(self, x, y):
        if not self.dragging_slider:
            return
        
        item = self.dragging_slider
        
        slider_width = 150
        slider_x = WIDTH - 80 - slider_width + 20
        
        relative_x = x - slider_x
        new_value = max(0, min(100, int(relative_x / slider_width * 100)))
        
        item['value'] = new_value
        
        if item['id'] == 'brightness':
            self.config.set_brightness(new_value)
    
    def handle_drag_end(self):
        self.dragging_slider = None
    
    def handle_scroll(self, delta):
        if not self.modal:
            self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset + delta))
    
    def _do_shutdown(self):
        """Shut down the device."""
        import platform
        import subprocess
        
        if platform.system() == 'Linux':
            try:
                subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
            except Exception as e:
                print(f"Shutdown error: {e}")
        else:
            print("Shutdown requested (mock - not on Pi)")
            # On non-Linux, just quit the app
            import pygame
            pygame.quit()
            sys.exit(0)