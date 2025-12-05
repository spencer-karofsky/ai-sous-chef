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
        content_bottom = HEIGHT - NAV_HEIGHT
        if keyboard_visible:
            content_bottom = HEIGHT - KEYBOARD_HEIGHT
        
        self._draw_header(screen)
        self._draw_network_list(screen, content_bottom)
        
        if self.show_password_modal:
            self._draw_password_modal(screen, keyboard_visible)
    
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
        title = self.fonts['header'].render("Wi-Fi", True, SOFT_BLACK)
        screen.blit(title, (130, 25))
        
        # Refresh button
        refresh_rect = pygame.Rect(WIDTH - 120, 20, 90, 40)
        pygame.draw.rect(screen, LIGHT_GRAY if not self.scanning else DIVIDER, refresh_rect, border_radius=20)
        
        refresh_text = self.fonts['small'].render("Refresh", True, CHARCOAL if not self.scanning else MID_GRAY)
        screen.blit(refresh_text, (refresh_rect.x + 15, refresh_rect.y + 10))
        
        # Current connection
        current = self.wifi.get_current_network()
        if current:
            status = self.fonts['small'].render(f"Connected to: {current}", True, (60, 160, 60))
            screen.blit(status, (130, 55))
        
        # Status message
        if self.connection_status:
            status = self.fonts['small'].render(self.connection_status, True, DARK_GRAY)
            screen.blit(status, (WIDTH - 300, 55))
    
    def _draw_network_list(self, screen, content_bottom):
        y_start = 100
        visible_height = content_bottom - y_start
        
        if not self.networks and not self.scanning:
            # Empty state
            msg = self.fonts['body'].render("No networks found", True, DARK_GRAY)
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 250))
            hint = self.fonts['small'].render("Tap Refresh to scan again", True, MID_GRAY)
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 290))
            return
        
        if self.scanning and not self.networks:
            msg = self.fonts['body'].render("Scanning for networks...", True, DARK_GRAY)
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 250))
            return
        
        # Calculate scroll
        content_height = len(self.networks) * 70 + 20
        self.max_scroll = max(0, content_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        # Create scrollable surface
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        content_surface.fill(WHITE)
        
        y = 10
        current_ssid = self.wifi.get_current_network()
        
        for network in self.networks:
            self._draw_network_item(content_surface, network, y, network['ssid'] == current_ssid)
            y += 70
        
        screen.blit(content_surface, (0, y_start), (0, self.scroll_offset, WIDTH, visible_height))
    
    def _draw_network_item(self, surface, network, y, is_connected):
        card_rect = pygame.Rect(40, y, WIDTH - 80, 60)
        
        # Background
        bg_color = (240, 255, 240) if is_connected else LIGHT_GRAY
        pygame.draw.rect(surface, bg_color, card_rect, border_radius=12)
        
        # WiFi signal icon
        self._draw_wifi_icon(surface, card_rect.x + 25, card_rect.y + 18, network['signal'])
        
        # Network name
        name = network['ssid']
        if len(name) > 30:
            name = name[:27] + "..."
        name_text = self.fonts['body'].render(name, True, SOFT_BLACK)
        surface.blit(name_text, (card_rect.x + 60, card_rect.y + 10))
        
        # Status / security
        if is_connected:
            status = self.fonts['small'].render("Connected", True, (60, 160, 60))
        elif network['secured']:
            status = self.fonts['small'].render("Secured", True, DARK_GRAY)
        else:
            status = self.fonts['small'].render("Open", True, DARK_GRAY)
        surface.blit(status, (card_rect.x + 60, card_rect.y + 35))
        
        # Lock icon if secured
        if network['secured'] and not is_connected:
            lock_x = card_rect.x + card_rect.width - 40
            lock_y = card_rect.y + 25
            # Simple lock shape
            pygame.draw.rect(surface, DARK_GRAY, (lock_x, lock_y, 12, 10), border_radius=2)
            pygame.draw.arc(surface, DARK_GRAY, (lock_x + 1, lock_y - 8, 10, 12), 0, 3.14, 2)
    
    def _draw_wifi_icon(self, surface, x, y, signal):
        """Draw WiFi signal strength icon."""
        color = SOFT_BLACK
        
        # Three arcs representing signal strength
        for i in range(3):
            threshold = (i + 1) * 33
            arc_color = color if signal >= threshold else DIVIDER
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
        modal_width = 500
        modal_height = 220
        modal_x = (WIDTH - modal_width) // 2
        modal_y = 80 if keyboard_visible else (HEIGHT - modal_height) // 2
        
        pygame.draw.rect(screen, WHITE, (modal_x, modal_y, modal_width, modal_height), border_radius=16)
        
        # Title
        title = self.fonts['header'].render("Enter Password", True, SOFT_BLACK)
        screen.blit(title, (modal_x + 30, modal_y + 20))
        
        # Network name
        if self.selected_network:
            ssid = self.fonts['small'].render(f"Network: {self.selected_network['ssid']}", True, DARK_GRAY)
            screen.blit(ssid, (modal_x + 30, modal_y + 55))
        
        # Password field
        field_rect = pygame.Rect(modal_x + 30, modal_y + 90, modal_width - 60, 50)
        pygame.draw.rect(screen, LIGHT_GRAY, field_rect, border_radius=10)
        
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
        btn_y = modal_y + modal_height - 55
        
        # Cancel
        cancel_rect = pygame.Rect(modal_x + 30, btn_y, 100, 40)
        pygame.draw.rect(screen, LIGHT_GRAY, cancel_rect, border_radius=8)
        cancel_text = self.fonts['small'].render("Cancel", True, SOFT_BLACK)
        screen.blit(cancel_text, (cancel_rect.x + 20, cancel_rect.y + 10))
        
        # Connect
        connect_rect = pygame.Rect(modal_x + modal_width - 130, btn_y, 100, 40)
        btn_color = SOFT_BLACK if self.password else MID_GRAY
        pygame.draw.rect(screen, btn_color, connect_rect, border_radius=8)
        connect_text = self.fonts['small'].render("Connect", True, WHITE)
        screen.blit(connect_text, (connect_rect.x + 15, connect_rect.y + 10))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        # Handle password modal
        if self.show_password_modal:
            return self._handle_modal_touch(x, y, keyboard_visible)
        
        # Back button
        if 30 <= x <= 110 and 20 <= y <= 60:
            return 'back'
        
        # Refresh button
        if WIDTH - 120 <= x <= WIDTH - 30 and 20 <= y <= 60:
            if not self.scanning:
                self.start_scan()
            return 'refresh'
        
        # Network list
        y_start = 100
        content_y = y - y_start + self.scroll_offset
        
        item_y = 10
        for network in self.networks:
            if item_y <= content_y <= item_y + 60:
                current = self.wifi.get_current_network()
                if network['ssid'] == current:
                    # Already connected - maybe show disconnect option?
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
            
            item_y += 70
        
        return None
    
    def _handle_modal_touch(self, x, y, keyboard_visible):
        modal_width = 500
        modal_height = 220
        modal_x = (WIDTH - modal_width) // 2
        modal_y = 80 if keyboard_visible else (HEIGHT - modal_height) // 2
        
        btn_y = modal_y + modal_height - 55
        
        # Cancel button
        if modal_x + 30 <= x <= modal_x + 130 and btn_y <= y <= btn_y + 40:
            self.show_password_modal = False
            self.selected_network = None
            self.password = ""
            return 'cancel'
        
        # Connect button
        if modal_x + modal_width - 130 <= x <= modal_x + modal_width - 30 and btn_y <= y <= btn_y + 40:
            if self.password and self.selected_network:
                self._connect_to_network(self.selected_network, self.password)
                return 'connecting'
        
        # Password field tap - show keyboard
        field_rect = pygame.Rect(modal_x + 30, modal_y + 90, modal_width - 60, 50)
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