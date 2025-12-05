"""
ui_new/views/wifi_view.py

Description:
    * WiFi connection view

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
import threading
from ui_new.constants import *
from ui_new.wifi_manager import WiFiManager

# Warm background
WARM_BG = (255, 251, 245)

# Muted sage for cards
CARD_BG = (241, 244, 240)

# Connected green (teal family)
CONNECTED_GREEN = (60, 160, 120)
CONNECTED_BG = (232, 245, 240)


class WiFiView:
    def __init__(self, fonts):
        self.fonts = fonts
        self.wifi = WiFiManager()
        
        self.networks = []
        self.scanning = False
        self.connecting = False
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Password entry
        self.selected_network = None
        self.password = ""
        self.show_password_modal = False
        self.connection_status = ""
        
        # Start initial scan
        self.start_scan()
    
    def start_scan(self):
        """Start scanning for networks in background."""
        if self.scanning:
            return
        
        self.scanning = True
        self.connection_status = "Scanning..."
        
        def do_scan():
            self.networks = self.wifi.scan_networks()
            self.scanning = False
            self.connection_status = ""
        
        threading.Thread(target=do_scan, daemon=True).start()
    
    def draw(self, screen, state, keyboard_visible=False):
        screen.fill(WARM_BG)
        content_bottom = HEIGHT - NAV_HEIGHT
        if keyboard_visible:
            content_bottom = HEIGHT - KEYBOARD_HEIGHT
        
        self._draw_header(screen)
        self._draw_network_list(screen, content_bottom)
        
        if self.show_password_modal:
            self._draw_password_modal(screen, keyboard_visible)
    
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
        title = self.fonts['header'].render("Wi-Fi", True, SOFT_BLACK)
        screen.blit(title, (150, 28))
        
        # Refresh button - teal when active
        refresh_rect = pygame.Rect(WIDTH - 130, 20, 100, 40)
        if self.scanning:
            pygame.draw.rect(screen, SAGE_LIGHT, refresh_rect, border_radius=20)
            pygame.draw.rect(screen, SAGE, refresh_rect, border_radius=20, width=1)
            refresh_text = self.fonts['small'].render("Scanning", True, DARK_GRAY)
        else:
            pygame.draw.rect(screen, TEAL, refresh_rect, border_radius=20)
            refresh_text = self.fonts['small'].render("Refresh", True, WHITE)
        
        screen.blit(refresh_text, (refresh_rect.x + (refresh_rect.width - refresh_text.get_width()) // 2, 
                                   refresh_rect.y + 10))
        
        # Current connection status
        current = self.wifi.get_current_network()
        if current:
            # Connected pill
            connected_str = f"Connected: {current}"
            if len(connected_str) > 30:
                connected_str = connected_str[:27] + "..."
            pill_width = self.fonts['small'].size(connected_str)[0] + 20
            pill_rect = pygame.Rect(150, 55, pill_width, 26)
            pygame.draw.rect(screen, CONNECTED_BG, pill_rect, border_radius=13)
            status = self.fonts['small'].render(connected_str, True, CONNECTED_GREEN)
            screen.blit(status, (160, 59))
        
        # Status message (scanning, connecting, etc.)
        if self.connection_status and not current:
            status = self.fonts['small'].render(self.connection_status, True, DARK_GRAY)
            screen.blit(status, (150, 58))
    
    def _draw_network_list(self, screen, content_bottom):
        y_start = 95
        visible_height = content_bottom - y_start
        
        if not self.networks and not self.scanning:
            # Empty state
            cx, cy = WIDTH // 2, HEIGHT // 2 - 40
            
            # WiFi icon in teal circle
            pygame.draw.circle(screen, TEAL, (cx, cy - 20), 50)
            self._draw_wifi_icon(screen, cx - 5, cy - 35, 100, WHITE)
            
            msg = self.fonts['header'].render("No Networks Found", True, SOFT_BLACK)
            screen.blit(msg, (cx - msg.get_width() // 2, cy + 50))
            hint = self.fonts['body'].render("Tap Refresh to scan again", True, DARK_GRAY)
            screen.blit(hint, (cx - hint.get_width() // 2, cy + 90))
            return
        
        if self.scanning and not self.networks:
            cx, cy = WIDTH // 2, HEIGHT // 2 - 20
            msg = self.fonts['body'].render("Scanning for networks...", True, DARK_GRAY)
            screen.blit(msg, (cx - msg.get_width() // 2, cy))
            return
        
        # Calculate scroll
        content_height = len(self.networks) * 75 + 20
        self.max_scroll = max(0, content_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        # Create scrollable surface
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        content_surface.fill(WARM_BG)
        
        y = 10
        current_ssid = self.wifi.get_current_network()
        
        for network in self.networks:
            self._draw_network_item(content_surface, network, y, network['ssid'] == current_ssid)
            y += 75
        
        screen.blit(content_surface, (0, y_start), (0, self.scroll_offset, WIDTH, visible_height))
    
    def _draw_network_item(self, surface, network, y, is_connected):
        card_rect = pygame.Rect(30, y, WIDTH - 60, 65)
        
        # Shadow
        shadow_surface = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 10), (0, 0, card_rect.width, card_rect.height), border_radius=12)
        surface.blit(shadow_surface, (card_rect.x + 2, card_rect.y + 2))
        
        # Background
        bg_color = CONNECTED_BG if is_connected else CARD_BG
        pygame.draw.rect(surface, bg_color, card_rect, border_radius=12)
        if not is_connected:
            pygame.draw.rect(surface, SAGE, card_rect, border_radius=12, width=1)
        
        # WiFi signal icon
        icon_color = CONNECTED_GREEN if is_connected else TEAL
        self._draw_wifi_icon(surface, card_rect.x + 30, card_rect.y + 18, network['signal'], icon_color)
        
        # Network name
        name = network['ssid']
        if len(name) > 28:
            name = name[:25] + "..."
        name_text = self.fonts['body'].render(name, True, SOFT_BLACK)
        surface.blit(name_text, (card_rect.x + 70, card_rect.y + 12))
        
        # Status / security as pill
        if is_connected:
            status_str = "Connected"
            pill_bg = CONNECTED_GREEN
            pill_text_color = WHITE
        elif network['secured']:
            status_str = "Secured"
            pill_bg = SAGE_LIGHT
            pill_text_color = SOFT_BLACK
        else:
            status_str = "Open"
            pill_bg = SAGE_LIGHT
            pill_text_color = SOFT_BLACK
        
        pill_width = self.fonts['small'].size(status_str)[0] + 14
        pill_rect = pygame.Rect(card_rect.x + 70, card_rect.y + 40, pill_width, 20)
        pygame.draw.rect(surface, pill_bg, pill_rect, border_radius=10)
        status = self.fonts['small'].render(status_str, True, pill_text_color)
        surface.blit(status, (pill_rect.x + 7, pill_rect.y + 2))
        
        # Lock icon if secured (and not connected)
        if network['secured'] and not is_connected:
            lock_x = card_rect.x + card_rect.width - 40
            lock_y = card_rect.y + 28
            # Simple lock shape
            pygame.draw.rect(surface, DARK_GRAY, (lock_x, lock_y, 12, 10), border_radius=2)
            pygame.draw.arc(surface, DARK_GRAY, (lock_x + 1, lock_y - 8, 10, 12), 0, 3.14, 2)
        
        # Chevron for tap indication
        if not is_connected:
            chevron_x = card_rect.x + card_rect.width - 25
            chevron_y = card_rect.y + 32
            pygame.draw.line(surface, TEAL, (chevron_x, chevron_y - 6), (chevron_x + 6, chevron_y), 2)
            pygame.draw.line(surface, TEAL, (chevron_x + 6, chevron_y), (chevron_x, chevron_y + 6), 2)
    
    def _draw_wifi_icon(self, surface, x, y, signal, color=None):
        """Draw WiFi signal strength icon."""
        if color is None:
            color = SOFT_BLACK
        
        # Three arcs representing signal strength
        for i in range(3):
            threshold = (i + 1) * 33
            arc_color = color if signal >= threshold else SAGE
            rect = pygame.Rect(x - 5 - i * 6, y - i * 6, 20 + i * 12, 20 + i * 12)
            pygame.draw.arc(surface, arc_color, rect, 0.5, 2.6, 2)
        
        # Base dot
        pygame.draw.circle(surface, color, (x + 5, y + 15), 3)
    
    def _draw_password_modal(self, screen, keyboard_visible):
        # Overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Modal position (higher if keyboard visible)
        modal_width = 520
        modal_height = 240
        modal_x = (WIDTH - modal_width) // 2
        modal_y = 80 if keyboard_visible else (HEIGHT - modal_height) // 2
        
        pygame.draw.rect(screen, WHITE, (modal_x, modal_y, modal_width, modal_height), border_radius=16)
        
        # Title
        title = self.fonts['header'].render("Enter Password", True, SOFT_BLACK)
        screen.blit(title, (modal_x + 30, modal_y + 25))
        
        # Network name as pill
        if self.selected_network:
            ssid = self.selected_network['ssid']
            if len(ssid) > 25:
                ssid = ssid[:22] + "..."
            ssid_width = self.fonts['small'].size(ssid)[0] + 16
            ssid_rect = pygame.Rect(modal_x + 30, modal_y + 60, ssid_width, 26)
            pygame.draw.rect(screen, SAGE_LIGHT, ssid_rect, border_radius=13)
            ssid_text = self.fonts['small'].render(ssid, True, SOFT_BLACK)
            screen.blit(ssid_text, (modal_x + 38, modal_y + 64))
        
        # Password field - white with sage border
        field_rect = pygame.Rect(modal_x + 30, modal_y + 100, modal_width - 60, 50)
        pygame.draw.rect(screen, WHITE, field_rect, border_radius=10)
        pygame.draw.rect(screen, SAGE, field_rect, border_radius=10, width=1)
        
        # Password text (masked)
        if self.password:
            masked = "•" * len(self.password)
            pwd_text = self.fonts['body'].render(masked, True, SOFT_BLACK)
        else:
            pwd_text = self.fonts['body'].render("Enter password...", True, MID_GRAY)
        screen.blit(pwd_text, (field_rect.x + 15, field_rect.y + 12))
        
        # Cursor
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = field_rect.x + 15 + self.fonts['body'].size("•" * len(self.password))[0] + 2
            pygame.draw.rect(screen, SOFT_BLACK, (cursor_x, field_rect.y + 12, 2, 26))
        
        # Buttons
        btn_y = modal_y + modal_height - 65
        
        # Cancel - sage light with border
        cancel_rect = pygame.Rect(modal_x + 30, btn_y, 110, 45)
        pygame.draw.rect(screen, SAGE_LIGHT, cancel_rect, border_radius=10)
        pygame.draw.rect(screen, SAGE, cancel_rect, border_radius=10, width=1)
        cancel_text = self.fonts['body'].render("Cancel", True, SOFT_BLACK)
        screen.blit(cancel_text, (cancel_rect.x + (cancel_rect.width - cancel_text.get_width()) // 2, 
                                  cancel_rect.y + 11))
        
        # Connect - teal when active
        connect_rect = pygame.Rect(modal_x + modal_width - 140, btn_y, 110, 45)
        btn_color = TEAL if self.password else MID_GRAY
        pygame.draw.rect(screen, btn_color, connect_rect, border_radius=10)
        connect_text = self.fonts['body'].render("Connect", True, WHITE)
        screen.blit(connect_text, (connect_rect.x + (connect_rect.width - connect_text.get_width()) // 2, 
                                   connect_rect.y + 11))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        # Handle password modal
        if self.show_password_modal:
            return self._handle_modal_touch(x, y, keyboard_visible)
        
        # Back button
        if 30 <= x <= 125 and 20 <= y <= 60:
            return 'back'
        
        # Refresh button
        if WIDTH - 130 <= x <= WIDTH - 30 and 20 <= y <= 60:
            if not self.scanning:
                self.start_scan()
            return 'refresh'
        
        # Network list
        y_start = 95
        content_y = y - y_start + self.scroll_offset
        
        item_y = 10
        for network in self.networks:
            if item_y <= content_y <= item_y + 65:
                current = self.wifi.get_current_network()
                if network['ssid'] == current:
                    # Already connected
                    return None
                
                if network['secured']:
                    # Show password modal
                    self.selected_network = network
                    self.password = ""
                    self.show_password_modal = True
                    return 'show_password'
                else:
                    # Connect directly to open network
                    self._connect_to_network(network, None)
                    return 'connecting'
            
            item_y += 75
        
        return None
    
    def _handle_modal_touch(self, x, y, keyboard_visible):
        modal_width = 520
        modal_height = 240
        modal_x = (WIDTH - modal_width) // 2
        modal_y = 80 if keyboard_visible else (HEIGHT - modal_height) // 2
        
        btn_y = modal_y + modal_height - 65
        
        # Cancel button
        if modal_x + 30 <= x <= modal_x + 140 and btn_y <= y <= btn_y + 45:
            self.show_password_modal = False
            self.selected_network = None
            self.password = ""
            return 'cancel'
        
        # Connect button
        if modal_x + modal_width - 140 <= x <= modal_x + modal_width - 30 and btn_y <= y <= btn_y + 45:
            if self.password and self.selected_network:
                self._connect_to_network(self.selected_network, self.password)
                return 'connecting'
        
        # Password field tap - show keyboard
        field_rect = pygame.Rect(modal_x + 30, modal_y + 100, modal_width - 60, 50)
        if field_rect.collidepoint(x, y):
            return 'focus_password'
        
        # Click outside modal
        if not (modal_x <= x <= modal_x + modal_width and modal_y <= y <= modal_y + modal_height):
            self.show_password_modal = False
            self.selected_network = None
            self.password = ""
            return 'cancel'
        
        return None
    
    def _connect_to_network(self, network, password):
        """Connect to network in background."""
        self.connecting = True
        self.connection_status = f"Connecting to {network['ssid']}..."
        self.show_password_modal = False
        
        def do_connect():
            success, message = self.wifi.connect(
                network['ssid'], 
                password, 
                network.get('security')
            )
            self.connecting = False
            if success:
                self.connection_status = "Connected!"
            else:
                self.connection_status = f"Failed: {message}"
            self.selected_network = None
            self.password = ""
        
        threading.Thread(target=do_connect, daemon=True).start()
    
    def handle_keyboard_input(self, key):
        """Handle keyboard input for password."""
        if not self.show_password_modal:
            return
        
        if key == 'BACKSPACE':
            self.password = self.password[:-1]
        elif key == 'GO':
            if self.password and self.selected_network:
                self._connect_to_network(self.selected_network, self.password)
        elif key not in ('HIDE', 'SHIFT'):
            self.password += key
    
    def handle_scroll(self, delta):
        if not self.show_password_modal:
            self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset + delta))