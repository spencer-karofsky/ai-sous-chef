"""
ui_new/views/grocery_list_view.py

Description:
    * Grocery list view - view and manage shopping lists (2-column grid layout)

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
import qrcode
import io

from ui_new.constants import *

# Warm background gradient
WARM_BG_TOP = (255, 251, 245)
WARM_BG_BOTTOM = (252, 245, 235)

# Muted sage for cards
CARD_BG = (241, 244, 240)

# Checked item green
CHECK_GREEN = (80, 160, 140)
CHECK_BG = (232, 245, 242)

# Grid layout
GRID_PADDING = 30
GRID_GAP = 16
CARD_WIDTH = (WIDTH - GRID_PADDING * 2 - GRID_GAP) // 2
ITEM_HEIGHT = 44


class GroceryListView:
    """View for managing grocery lists."""
    
    def __init__(self, fonts):
        self.fonts = fonts
        self.grocery_manager = None
        self.meal_plan_manager = None
        self.scroll_offset = 0
        self.max_scroll = 0
        
        self.current_list_id = None
        self.current_list = None
        
        self.generating = False
        self.gradient_surface = None
        self.show_qr = False
        self.qr_surface = None
        self.web_url = None
        
        # Track expanded categories (all expanded by default)
        self.expanded_categories = set()
        
        # Cache for card positions (for touch handling)
        self.card_positions = []
        self.item_positions = []

    def _generate_qr_surface(self, url):
        """Generate QR code as pygame surface with brand colors."""
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=(26, 94, 120), back_color=(227, 231, 226))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return pygame.image.load(img_bytes)
    
    def set_managers(self, grocery_manager, meal_plan_manager=None):
        self.grocery_manager = grocery_manager
        self.meal_plan_manager = meal_plan_manager
    
    def _create_gradient(self, width, height):
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
        for y in range(height):
            t = y / height
            r = int(WARM_BG_TOP[0] + (WARM_BG_BOTTOM[0] - WARM_BG_TOP[0]) * t)
            g = int(WARM_BG_TOP[1] + (WARM_BG_BOTTOM[1] - WARM_BG_TOP[1]) * t)
            b = int(WARM_BG_TOP[2] + (WARM_BG_BOTTOM[2] - WARM_BG_TOP[2]) * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (surface.get_width(), y))
    
    def draw(self, screen, state, keyboard_visible=False):
        screen.blit(self._create_gradient(WIDTH, HEIGHT), (0, 0))
        content_bottom = HEIGHT - NAV_HEIGHT
        
        if self.current_list_id and self.current_list:
            self._draw_list_detail(screen, content_bottom)
        else:
            self._draw_lists_overview(screen, content_bottom)
    
    def _draw_lists_overview(self, screen, content_bottom):
        self._draw_header_overview(screen)
        y_start = 80
        
        if not self.grocery_manager:
            return
        
        lists = self.grocery_manager.get_all_lists()
        gen_y = y_start
        self._draw_generate_button(screen, gen_y)
        list_start_y = gen_y + 65
        
        if not lists:
            cy = list_start_y + 80
            cx = WIDTH // 2
            pygame.draw.circle(screen, TEAL, (cx, cy), 45)
            pygame.draw.circle(screen, SAGE_LIGHT, (cx - 10, cy + 12), 4)
            pygame.draw.circle(screen, SAGE_LIGHT, (cx + 10, cy + 12), 4)
            pygame.draw.lines(screen, SAGE_LIGHT, False, [
                (cx - 18, cy - 15), (cx - 12, cy + 5), (cx + 15, cy + 5), (cx + 20, cy - 10)
            ], 3)
            msg = self.fonts['header'].render("No Grocery Lists", True, SOFT_BLACK)
            screen.blit(msg, (cx - msg.get_width() // 2, cy + 65))
            hint = self.fonts['body'].render("Generate one from your meal plan", True, DARK_GRAY)
            screen.blit(hint, (cx - hint.get_width() // 2, cy + 105))
            return
        
        # Draw lists in 2-column grid
        card_height = 90
        y = list_start_y
        for i in range(0, len(lists), 2):
            left_list = lists[i]
            right_list = lists[i + 1] if i + 1 < len(lists) else None
            
            # Left card
            self._draw_list_card(screen, left_list, GRID_PADDING, y, CARD_WIDTH, card_height)
            
            # Right card
            if right_list:
                self._draw_list_card(screen, right_list, GRID_PADDING + CARD_WIDTH + GRID_GAP, y, CARD_WIDTH, card_height)
            
            y += card_height + GRID_GAP
    
    def _draw_header_overview(self, screen):
        back_rect = pygame.Rect(30, 20, 110, 40)
        pygame.draw.rect(screen, SAGE_LIGHT, back_rect, border_radius=20)
        pygame.draw.rect(screen, SAGE, back_rect, border_radius=20, width=1)
        ax, ay = back_rect.x + 22, back_rect.y + 20
        pygame.draw.line(screen, TEAL, (ax + 8, ay - 6), (ax, ay), 2)
        pygame.draw.line(screen, TEAL, (ax, ay), (ax + 8, ay + 6), 2)
        back_text = self.fonts['small'].render("Back", True, SOFT_BLACK)
        screen.blit(back_text, (ax + 18, ay - 14))
        
        title = self.fonts['header'].render("Grocery Lists", True, SOFT_BLACK)
        screen.blit(title, (150, 28))
        
        if self.grocery_manager:
            count = len(self.grocery_manager.get_all_lists())
            if count > 0:
                subtitle = self.fonts['small'].render(f"{count} lists", True, DARK_GRAY)
                screen.blit(subtitle, (WIDTH - 100, 32))
    
    def _draw_generate_button(self, screen, y):
        btn_rect = pygame.Rect(30, y, WIDTH - 60, 55)
        has_meals = False
        plan_name = ""
        if self.meal_plan_manager:
            meal_count = self.meal_plan_manager.get_meal_count()
            has_meals = meal_count > 0
            plan_name = self.meal_plan_manager.get_plan_name() or "Meal Plan"
        
        if has_meals:
            shadow = pygame.Surface((btn_rect.width, btn_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 20), (0, 0, btn_rect.width, btn_rect.height), border_radius=12)
            screen.blit(shadow, (btn_rect.x + 2, btn_rect.y + 3))
            pygame.draw.rect(screen, TEAL, btn_rect, border_radius=12)
            text_color = SAGE_LIGHT
        else:
            pygame.draw.rect(screen, SAGE_LIGHT, btn_rect, border_radius=12)
            pygame.draw.rect(screen, SAGE, btn_rect, border_radius=12, width=1)
            text_color = DARK_GRAY
        
        if has_meals:
            self._draw_sparkle(screen, btn_rect.x + 28, btn_rect.y + 28, 8, SAGE_LIGHT)
        
        if self.generating:
            text = "Creating a Custom Shopping List..."
        elif has_meals:
            if len(plan_name) > 40:
                plan_name = plan_name[:37] + '...'
            text = f"Generate List from {plan_name}"
        else:
            text = "Create a Meal Plan to Generate a Grocery List"
        
        btn_text = self.fonts['body'].render(text, True, text_color)
        btn_text = self.fonts['body'].render(text, True, text_color)
        
        text_y = btn_rect.y + (btn_rect.height - btn_text.get_height()) // 2
        text_x = btn_rect.x + (50 if has_meals else 20)
        
        screen.blit(btn_text, (text_x, text_y))
    
    def _draw_sparkle(self, screen, cx, cy, size, color):
        points = [(cx, cy - size), (cx + size * 0.2, cy - size * 0.2), (cx + size, cy),
                  (cx + size * 0.2, cy + size * 0.2), (cx, cy + size), (cx - size * 0.2, cy + size * 0.2),
                  (cx - size, cy), (cx - size * 0.2, cy - size * 0.2)]
        pygame.draw.polygon(screen, color, [(int(px), int(py)) for px, py in points])
        small_cx, small_cy, small_size = cx + size + 1, cy - size + 1, size * 0.4
        small_points = [(small_cx, small_cy - small_size), (small_cx + small_size * 0.2, small_cy - small_size * 0.2),
                        (small_cx + small_size, small_cy), (small_cx + small_size * 0.2, small_cy + small_size * 0.2),
                        (small_cx, small_cy + small_size), (small_cx - small_size * 0.2, small_cy + small_size * 0.2),
                        (small_cx - small_size, small_cy), (small_cx - small_size * 0.2, small_cy - small_size * 0.2)]
        pygame.draw.polygon(screen, color, [(int(px), int(py)) for px, py in small_points])
    
    def _draw_list_card(self, screen, grocery_list, x, y, width, height):
        card_rect = pygame.Rect(x, y, width, height)
        shadow = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 12), (0, 0, width, height), border_radius=12)
        screen.blit(shadow, (x + 2, y + 2))
        pygame.draw.rect(screen, SAGE_LIGHT, card_rect, border_radius=12)
        pygame.draw.rect(screen, SAGE, card_rect, border_radius=12, width=1)
        
        # Store for touch handling
        list_id = grocery_list.get('id')
        
        # Name at top
        name = grocery_list.get('name', 'Grocery List')
        if len(name) > 36:
            name = name[:33] + '...'
        screen.blit(self.fonts['body'].render(name, True, SOFT_BLACK), (x + 16, y + 12))
        
        # Stats as pills
        item_count = grocery_list.get('item_count', 0)
        recipe_count = grocery_list.get('recipe_count', 0)
        
        # --- FIX: Move pills down from y + 45 to y + 50 to give list name more room ---
        PILL_HEIGHT = 28 # Retained from previous fixes
        pill_y = y + 50 
        pill_x = x + 16
        
        items_str = f"{item_count} items"
        items_width = self.fonts['small'].size(items_str)[0] + 24
        
        # Item Count Pill
        pygame.draw.rect(screen, CARD_BG, pygame.Rect(pill_x, pill_y, items_width, PILL_HEIGHT), border_radius=14)
        text_y = pill_y + (PILL_HEIGHT - self.fonts['small'].get_height()) // 2
        screen.blit(self.fonts['small'].render(items_str, True, SOFT_BLACK), (pill_x + 12, text_y))
        pill_x += items_width + 8
        
        recipes_str = f"{recipe_count} recipes"
        recipes_width = self.fonts['small'].size(recipes_str)[0] + 24
        
        # Recipe Count Pill
        pygame.draw.rect(screen, CARD_BG, pygame.Rect(pill_x, pill_y, recipes_width, PILL_HEIGHT), border_radius=14)
        text_y = pill_y + (PILL_HEIGHT - self.fonts['small'].get_height()) // 2
        screen.blit(self.fonts['small'].render(recipes_str, True, SOFT_BLACK), (pill_x + 12, text_y))
        
        # Chevron at right (Its position is calculated relative to card height, so it remains centered)
        chevron_x = x + width - 25
        chevron_y = y + height // 2
        pygame.draw.line(screen, TEAL, (chevron_x - 4, chevron_y - 6), (chevron_x + 4, chevron_y), 2)
        pygame.draw.line(screen, TEAL, (chevron_x + 4, chevron_y), (chevron_x - 4, chevron_y + 6), 2)
    
    def _draw_list_detail(self, screen, content_bottom):
        self._draw_header_detail(screen)
        y_start = 80
        visible_height = content_bottom - y_start
        
        categories = self.current_list.get('categories', {})
        
        if not self.expanded_categories:
            self.expanded_categories = set(categories.keys())
        
        # 1. Calculate the height required for the content grid (now includes final GRID_GAP)
        content_grid_height = self._calculate_grid_height(categories)
        
        # --- FIX: Reduce the buffer slightly but keep it generous for safety ---
        BOTTOM_BUFFER = 70 
        
        # 2. Calculate the total height needed for the scrollable surface
        total_scroll_height = content_grid_height + BOTTOM_BUFFER
        
        # 3. Calculate max scroll depth
        self.max_scroll = max(0, total_scroll_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        # 4. Create the surface with the new total height
        content_surface = pygame.Surface((WIDTH, total_scroll_height), pygame.SRCALPHA)
        self._draw_gradient_surface(content_surface, total_scroll_height)
        
        self._draw_category_grid(content_surface, categories)
        
        # 5. Blit the visible portion onto the screen
        screen.blit(content_surface, (0, y_start), (0, self.scroll_offset, WIDTH, visible_height))
        
        # QR modal
        if self.show_qr and self.qr_surface:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            modal_w, modal_h = 300, 340
            modal_x, modal_y = (WIDTH - modal_w) // 2, (HEIGHT - modal_h) // 2
            pygame.draw.rect(screen, SAGE_LIGHT, pygame.Rect(modal_x, modal_y, modal_w, modal_h), border_radius=16)
            title = self.fonts['header'].render("Scan to View", True, SOFT_BLACK)
            screen.blit(title, (modal_x + (modal_w - title.get_width()) // 2, modal_y + 20))
            screen.blit(self.qr_surface, (modal_x + (modal_w - self.qr_surface.get_width()) // 2, modal_y + 60))
            close_rect = pygame.Rect(modal_x + 20, modal_y + modal_h - 55, modal_w - 40, 40)
            pygame.draw.rect(screen, CARD_BG, close_rect, border_radius=10)
            screen.blit(self.fonts['body'].render("Close", True, SOFT_BLACK), 
                       (close_rect.x + (close_rect.width - self.fonts['body'].size("Close")[0]) // 2, close_rect.y + 10))
    
    def _calculate_grid_height(self, categories):
        """Calculate total height needed for grid layout."""
        active_cats = [(name, items) for name, items in categories.items() if items]
        if not active_cats:
            return 100
        
        # Initialize with vertical padding (e.g., GRID_GAP)
        left_height = GRID_GAP 
        right_height = GRID_GAP
        
        for i, (cat_name, items) in enumerate(active_cats):
            card_height = self._get_card_height(cat_name, items)
            if i % 2 == 0:
                left_height += card_height + GRID_GAP
            else:
                right_height += card_height + GRID_GAP
        
        return max(left_height, right_height) + GRID_GAP
    
    def _get_card_height(self, cat_name, items):
        """Calculate height for a category card."""
        header_height = 38
        if cat_name not in self.expanded_categories:
            return header_height
        
        # Optional items need more height for the reason text
        if cat_name == 'Optional':
            return header_height + len(items) * (ITEM_HEIGHT + 16) + 8
        return header_height + len(items) * ITEM_HEIGHT + 8
    
    def _draw_category_grid(self, surface, categories):
        """Draw categories in a 2-column grid - each card at its own height."""
        self.card_positions = []
        self.item_positions = []
        
        active_cats = [(name, items) for name, items in categories.items() if items]
        if not active_cats:
            return
        
        # Track y position for each column independently
        left_y = 10
        right_y = 10
        
        for i, (cat_name, items) in enumerate(active_cats):
            card_height = self._get_card_height(cat_name, items)
            
            # Alternate columns, placing each card at the top of its column
            if i % 2 == 0:
                # Left column
                card_x = GRID_PADDING
                card_y = left_y
                self._draw_category_card(surface, cat_name, items, card_x, card_y, CARD_WIDTH, card_height)
                self.card_positions.append((cat_name, pygame.Rect(card_x, card_y, CARD_WIDTH, card_height)))
                left_y += card_height + GRID_GAP
            else:
                # Right column
                card_x = GRID_PADDING + CARD_WIDTH + GRID_GAP
                card_y = right_y
                self._draw_category_card(surface, cat_name, items, card_x, card_y, CARD_WIDTH, card_height)
                self.card_positions.append((cat_name, pygame.Rect(card_x, card_y, CARD_WIDTH, card_height)))
                right_y += card_height + GRID_GAP
    
    def _draw_category_card(self, surface, cat_name, items, x, y, width, height):
        """Draw a single category card."""
        card_rect = pygame.Rect(x, y, width, height)
        
        # Shadow
        shadow = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 15), (0, 0, width, height), border_radius=14)
        surface.blit(shadow, (x + 2, y + 2))
        
        # Card background - changed from WHITE to SAGE_LIGHT
        pygame.draw.rect(surface, SAGE_LIGHT, card_rect, border_radius=14)
        pygame.draw.rect(surface, SAGE, card_rect, border_radius=14, width=1)
        
        # Header
        is_expanded = cat_name in self.expanded_categories
        
        # Category colors
        icon_colors = {
            'Produce': (120, 180, 100),
            'Meat & Seafood': (200, 100, 100),
            'Dairy & Eggs': (240, 220, 150),
            'Bakery': (210, 170, 120),
            'Pantry': (160, 140, 120),
            'Frozen': (140, 180, 220),
            'Beverages': (100, 160, 200),
            'Other': (160, 160, 160),
            'Optional': TEAL
        }
        color = icon_colors.get(cat_name, SAGE)
        
        # Colored dot
        pygame.draw.circle(surface, color, (x + 16, y + 18), 6)
        
        # Category name
        cat_text = self.fonts['body'].render(cat_name, True, SOFT_BLACK)
        surface.blit(cat_text, (x + 28, y + 8))
        
        HORIZONTAL_PADDING = 30
        PILL_HEIGHT = 28 
        PILL_Y = y + 8
        
        count_str = str(len(items))
        count_width = self.fonts['small'].size(count_str)[0] + HORIZONTAL_PADDING
        
        # --- FIX: Increase the right margin from 15 to 40 pixels ---
        # This pushes the pill further left, away from the chevron.
        count_x = x + width - count_width - 40 
        
        count_rect = pygame.Rect(count_x, PILL_Y, count_width, PILL_HEIGHT)
        
        # Draw the pill background
        pygame.draw.rect(surface, CARD_BG, count_rect, border_radius=14)
        
        # Calculate text position (Centered horizontally and vertically)
        text_x = count_x + (count_width - self.fonts['small'].size(count_str)[0]) // 2
        text_y = PILL_Y + (PILL_HEIGHT - self.fonts['small'].get_height()) // 2
        
        # Draw the text
        surface.blit(self.fonts['small'].render(count_str, True, SOFT_BLACK), (text_x, text_y))
        
        # Expand/collapse chevron
        chev_x = x + width - 18
        chev_y = y + 18
        if is_expanded:
            pygame.draw.line(surface, TEAL, (chev_x - 5, chev_y - 3), (chev_x, chev_y + 3), 2)
            pygame.draw.line(surface, TEAL, (chev_x, chev_y + 3), (chev_x + 5, chev_y - 3), 2)
        else:
            pygame.draw.line(surface, TEAL, (chev_x - 3, chev_y - 5), (chev_x + 3, chev_y), 2)
            pygame.draw.line(surface, TEAL, (chev_x + 3, chev_y), (chev_x - 3, chev_y + 5), 2)
        
        # Draw items if expanded
        if is_expanded:
            # FIX: Increased padding below header (was 38, now 50)
            ITEM_START_PADDING = 50 
            item_y = y + ITEM_START_PADDING
            
            for i, item in enumerate(items):
                # Optional items need more height
                item_height = ITEM_HEIGHT + 16 if cat_name == 'Optional' else ITEM_HEIGHT
                self._draw_grid_item(surface, item, x + 8, item_y, width - 16, cat_name, i)
                self.item_positions.append((cat_name, i, pygame.Rect(x + 8, item_y, width - 16, item_height - 4)))
                item_y += item_height
    
    def _draw_grid_item(self, surface, item, x, y, width, category, index):
        """Draw a single grocery item in grid layout."""
        is_checked = self.grocery_manager.is_checked(self.current_list, category, index)
        
        # Optional items are taller
        item_height = ITEM_HEIGHT + 12 if category == 'Optional' else ITEM_HEIGHT - 4
        item_rect = pygame.Rect(x, y, width, item_height)
        
        if is_checked:
            pygame.draw.rect(surface, CHECK_BG, item_rect, border_radius=8)
        else:
            pygame.draw.rect(surface, CARD_BG, item_rect, border_radius=8)
        
        # Checkbox
        check_x = x + 10
        check_y = y + 10
        check_rect = pygame.Rect(check_x, check_y, 18, 18)
        
        if is_checked:
            pygame.draw.rect(surface, CHECK_GREEN, check_rect, border_radius=5)
            pygame.draw.line(surface, SAGE_LIGHT, (check_x + 4, check_y + 9), (check_x + 7, check_y + 13), 2)
            pygame.draw.line(surface, SAGE_LIGHT, (check_x + 7, check_y + 13), (check_x + 14, check_y + 5), 2)
        else:
            pygame.draw.rect(surface, SAGE, check_rect, 2, border_radius=5)
        
        # Item text
        item_name = item.get('item', str(item))
        quantity = item.get('quantity', '')
        reason = item.get('reason', '')
        
        display_text = f"{quantity} {item_name}".strip() if quantity else item_name
        
        # More characters - cards are wide enough
        max_chars = 35
        if len(display_text) > max_chars:
            display_text = display_text[:max_chars - 2] + '..'
        
        text_color = DARK_GRAY if is_checked else SOFT_BLACK
        surface.blit(self.fonts['small'].render(display_text, True, text_color), (check_x + 26, check_y + 1))
        
        # Reason for optional items on second line
        if reason and category == 'Optional':
            reason_text = reason[:40] + '..' if len(reason) > 40 else reason
            surface.blit(self.fonts['caption'].render(f"({reason_text})", True, DARK_GRAY), (check_x + 26, check_y + 22))
    
    def _draw_header_detail(self, screen):
        BACK_BUTTON_WIDTH = 110
        BACK_BUTTON_HEIGHT = 50  
        BACK_BUTTON_Y = 15       
        
        # Draw the main button rectangle
        back_rect = pygame.Rect(30, BACK_BUTTON_Y, BACK_BUTTON_WIDTH, BACK_BUTTON_HEIGHT)
        pygame.draw.rect(screen, SAGE_LIGHT, back_rect, border_radius=25)
        pygame.draw.rect(screen, SAGE, back_rect, border_radius=25, width=1)
        
        # Calculate center point for arrow/text alignment
        CENTER_Y = back_rect.y + BACK_BUTTON_HEIGHT // 2
        
        # Position the arrow and text closer to the left edge of the *button* for good padding
        # We start the content (arrow) at 20 pixels from the left of the button.
        ax = back_rect.x + 20 
        ay = CENTER_Y
        pygame.draw.line(screen, TEAL, (ax + 8, ay - 6), (ax, ay), 2)
        pygame.draw.line(screen, TEAL, (ax, ay), (ax + 8, ay + 6), 2)
        
        # Position the text next to the arrow
        back_text = self.fonts['small'].render("Back", True, SOFT_BLACK)
        screen.blit(back_text, (ax + 18, CENTER_Y - back_text.get_height() // 2))
        
        # --- List Name & Progress Pill Drawing (Unchanged) ---
        name = self.current_list.get('name', 'Grocery List')
        if len(name) > 50:
            name = name[:47] + '...'
        screen.blit(self.fonts['header'].render(name, True, SOFT_BLACK), (150, 20))
        
        checked, total = self.grocery_manager.get_checked_count(self.current_list)
        progress = f"{checked}/{total}"
        prog_width = self.fonts['small'].size(progress)[0] + 24
        
        PROGRESS_PILL_Y = 56 
        PILL_HEIGHT = 28
        
        pygame.draw.rect(screen, CARD_BG, pygame.Rect(150, PROGRESS_PILL_Y, prog_width, PILL_HEIGHT), border_radius=14)
        text_y = PROGRESS_PILL_Y + (PILL_HEIGHT - self.fonts['small'].get_height()) // 2
        screen.blit(self.fonts['small'].render(progress, True, SOFT_BLACK), (150 + 12, text_y))
        
        # --- SHARE AND DELETE BUTTON DRAWING (Unchanged from last fix) ---
        BUTTON_HEIGHT = 50 
        BUTTON_Y = 15 
        BUTTON_WIDTH = 100 
        RIGHT_PADDING = 25 
        BUTTON_GAP = 30 
        
        # Delete button position
        delete_x = WIDTH - BUTTON_WIDTH - RIGHT_PADDING 
        
        # Delete button
        delete_rect = pygame.Rect(delete_x, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(screen, (250, 230, 230), delete_rect, border_radius=12)
        pygame.draw.rect(screen, (220, 180, 180), delete_rect, border_radius=12, width=1)
        delete_text = self.fonts['body'].render("Delete", True, (180, 80, 80))
        text_y = delete_rect.y + (BUTTON_HEIGHT - delete_text.get_height()) // 2
        text_x = delete_rect.x + (BUTTON_WIDTH - delete_text.get_width()) // 2
        screen.blit(delete_text, (text_x, text_y))
        
        # Share button position is calculated using the gap
        share_x = delete_x - BUTTON_WIDTH - BUTTON_GAP
        
        # Share button
        share_rect = pygame.Rect(share_x, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(screen, TEAL, share_rect, border_radius=12)
        share_text = self.fonts['body'].render("Share", True, SAGE_LIGHT)
        text_y = share_rect.y + (BUTTON_HEIGHT - share_text.get_height()) // 2
        text_x = share_rect.x + (BUTTON_WIDTH - share_text.get_width()) // 2
        screen.blit(share_text, (text_x, text_y))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        if self.current_list_id and self.current_list:
            return self._handle_detail_touch(x, y)
        return self._handle_overview_touch(x, y)
    
    def _handle_overview_touch(self, x, y):
        if 30 <= x <= 125 and 20 <= y <= 60:
            return 'back'
        
        gen_y = 80
        if pygame.Rect(30, gen_y, WIDTH - 60, 55).collidepoint(x, y):
            if self.meal_plan_manager and self.meal_plan_manager.get_meal_count() > 0:
                return 'generate_list'
        
        if self.grocery_manager:
            lists = self.grocery_manager.get_all_lists()
            list_start_y = gen_y + 65
            card_height = 90
            
            for i in range(0, len(lists), 2):
                row = i // 2
                card_y = list_start_y + row * (card_height + GRID_GAP)
                
                # Left card
                left_rect = pygame.Rect(GRID_PADDING, card_y, CARD_WIDTH, card_height)
                if left_rect.collidepoint(x, y):
                    self.current_list_id = lists[i]['id']
                    self.current_list = self.grocery_manager.get_list(lists[i]['id'])
                    self.scroll_offset = 0
                    self.expanded_categories = set(self.current_list.get('categories', {}).keys())
                    return f"view_list_{lists[i]['id']}"
                
                # Right card
                if i + 1 < len(lists):
                    right_rect = pygame.Rect(GRID_PADDING + CARD_WIDTH + GRID_GAP, card_y, CARD_WIDTH, card_height)
                    if right_rect.collidepoint(x, y):
                        self.current_list_id = lists[i + 1]['id']
                        self.current_list = self.grocery_manager.get_list(lists[i + 1]['id'])
                        self.scroll_offset = 0
                        self.expanded_categories = set(self.current_list.get('categories', {}).keys())
                        return f"view_list_{lists[i + 1]['id']}"
        return None
    
    def _handle_detail_touch(self, x, y):
        # QR modal handling
        if self.show_qr:
            # Re-calculate modal bounds (must match drawing logic)
            modal_w, modal_h = 300, 340
            modal_x, modal_y = (WIDTH - modal_w) // 2, (HEIGHT - modal_h) // 2
            
            # Close button rectangle used for touch detection
            close_rect = pygame.Rect(modal_x + 20, modal_y + modal_h - 55, modal_w - 40, 40)
            
            # Touch Logic: Check if touch is on the Close button OR outside the entire modal area
            modal_bounds = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
            
            if close_rect.collidepoint(x, y) or not modal_bounds.collidepoint(x, y):
                self.show_qr = False
                return 'close_qr'
            return None
        
        # Back button FIX: Update X range (30 <= x <= 170)
        BACK_BUTTON_Y_START = 15
        BACK_BUTTON_Y_END = 65
        BACK_BUTTON_X_END = 170 # 30 + 140
        
        if 30 <= x <= BACK_BUTTON_X_END and BACK_BUTTON_Y_START <= y <= BACK_BUTTON_Y_END:
            self.current_list_id = None
            self.current_list = None
            self.scroll_offset = 0
            self.expanded_categories = set()
            return 'back_to_lists'
        
        # --- SHARE AND DELETE BUTTON TOUCH ZONES (Unchanged from last fix) ---
        BUTTON_WIDTH = 100 
        BUTTON_Y_START = 15
        BUTTON_Y_END = 65  
        RIGHT_PADDING = 25 
        BUTTON_GAP = 30
        
        delete_x_start = WIDTH - BUTTON_WIDTH - RIGHT_PADDING 
        delete_x_end = delete_x_start + BUTTON_WIDTH          
        
        share_x_start = delete_x_start - BUTTON_WIDTH - BUTTON_GAP 
        share_x_end = share_x_start + BUTTON_WIDTH
        
        # Share button touch zone... (unchanged)
        if share_x_start <= x <= share_x_end and BUTTON_Y_START <= y <= BUTTON_Y_END:
            if self.grocery_manager and self.current_list_id:
                url = self.grocery_manager.get_web_url(self.current_list_id)
                if not url:
                    url = self.grocery_manager.sync_to_web(self.current_list_id)
                if url:
                    self.web_url = url
                    self.qr_surface = self._generate_qr_surface(url)
                    self.show_qr = True
                    return 'show_qr'
            return None
        
        # Delete button touch zone... (unchanged)
        if delete_x_start <= x <= delete_x_end and BUTTON_Y_START <= y <= BUTTON_Y_END:
            if self.grocery_manager and self.current_list_id:
                self.grocery_manager.delete_list(self.current_list_id)
                self.current_list_id = None
                self.current_list = None
                self.scroll_offset = 0
                self.expanded_categories = set()
                return 'deleted_list'
        
        # Adjust for scroll... (unchanged)
        y_start = 80
        content_y = y - y_start + self.scroll_offset
        
        # Check card header clicks... (unchanged)
        for cat_name, rect in self.card_positions:
            header_rect = pygame.Rect(rect.x, rect.y, rect.width, 38)
            if header_rect.collidepoint(x, content_y):
                if cat_name in self.expanded_categories:
                    self.expanded_categories.discard(cat_name)
                else:
                    self.expanded_categories.add(cat_name)
                return f'toggle_category_{cat_name}'
        
        # Check item clicks... (unchanged)
        for cat_name, index, rect in self.item_positions:
            if rect.collidepoint(x, content_y):
                self.grocery_manager.toggle_item(self.current_list_id, cat_name, index)
                self.current_list = self.grocery_manager.get_list(self.current_list_id)
                return f'toggled_{cat_name}_{index}'
        
        return None
    
    def generate_list(self):
        if not self.grocery_manager or not self.meal_plan_manager:
            return None
        self.generating = True
        meals = self.meal_plan_manager.get_all_meals()
        plan_name = self.meal_plan_manager.get_plan_name()
        list_id = self.grocery_manager.generate_from_meals(meals, plan_name)
        self.generating = False
        if list_id:
            self.current_list_id = list_id
            self.current_list = self.grocery_manager.get_list(list_id)
            self.scroll_offset = 0
            self.expanded_categories = set(self.current_list.get('categories', {}).keys())
        return list_id
    
    def handle_scroll(self, delta):
        self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset + delta))