"""
ui_new/views/grocery_list_view.py

Description:
    * Grocery list view - view and manage shopping lists

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *

# Warm background
WARM_BG = (255, 251, 245)

# Muted sage for cards (20-30% sage over warm white)
CARD_BG = (241, 244, 240)

# Checked item green (matches teal family)
CHECK_GREEN = (80, 160, 140)
CHECK_BG = (232, 245, 242)


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
    
    def set_managers(self, grocery_manager, meal_plan_manager=None):
        """Set the data managers."""
        self.grocery_manager = grocery_manager
        self.meal_plan_manager = meal_plan_manager
    
    def draw(self, screen, state, keyboard_visible=False):
        screen.fill(WARM_BG)
        content_bottom = HEIGHT - NAV_HEIGHT
        
        if self.current_list_id and self.current_list:
            self._draw_list_detail(screen, content_bottom)
        else:
            self._draw_lists_overview(screen, content_bottom)
    
    def _draw_lists_overview(self, screen, content_bottom):
        """Draw the list of all grocery lists."""
        self._draw_header_overview(screen)
        
        y_start = 90
        visible_height = content_bottom - y_start
        
        if not self.grocery_manager:
            return
        
        lists = self.grocery_manager.get_all_lists()
        
        # Generate button
        gen_y = y_start + 10
        self._draw_generate_button(screen, gen_y)
        
        list_start_y = gen_y + 70
        
        if not lists:
            # Empty state
            cy = list_start_y + 80
            cx = WIDTH // 2
            
            # Cart icon in teal circle
            pygame.draw.circle(screen, TEAL, (cx, cy), 45)
            
            # Simple cart icon
            pygame.draw.circle(screen, WHITE, (cx - 10, cy + 12), 4)
            pygame.draw.circle(screen, WHITE, (cx + 10, cy + 12), 4)
            pygame.draw.lines(screen, WHITE, False, [
                (cx - 18, cy - 15), (cx - 12, cy + 5), (cx + 15, cy + 5), (cx + 20, cy - 10)
            ], 3)
            
            msg = self.fonts['header'].render("No Grocery Lists", True, SOFT_BLACK)
            screen.blit(msg, (cx - msg.get_width() // 2, cy + 65))
            
            hint = self.fonts['body'].render("Generate one from your meal plan", True, DARK_GRAY)
            screen.blit(hint, (cx - hint.get_width() // 2, cy + 105))
            return
        
        # Draw lists
        item_height = 80
        y = list_start_y
        for grocery_list in lists:
            self._draw_list_card(screen, grocery_list, y)
            y += item_height
    
    def _draw_header_overview(self, screen):
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
        title = self.fonts['header'].render("Grocery Lists", True, SOFT_BLACK)
        screen.blit(title, (150, 28))
        
        # Subtitle - count on right side
        if self.grocery_manager:
            count = len(self.grocery_manager.get_all_lists())
            if count > 0:
                subtitle = self.fonts['small'].render(f"{count} lists", True, DARK_GRAY)
                screen.blit(subtitle, (WIDTH - 100, 32))
    
    def _draw_generate_button(self, screen, y):
        """Draw the generate from meal plan button."""
        btn_rect = pygame.Rect(30, y, WIDTH - 60, 55)
        
        # Check if meal plan has meals
        has_meals = False
        meal_count = 0
        if self.meal_plan_manager:
            meal_count = self.meal_plan_manager.get_meal_count()
            has_meals = meal_count > 0
        
        if has_meals:
            # Soft shadow
            shadow_surface = pygame.Surface((btn_rect.width, btn_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, 20), (0, 0, btn_rect.width, btn_rect.height), border_radius=12)
            screen.blit(shadow_surface, (btn_rect.x + 2, btn_rect.y + 3))
            
            pygame.draw.rect(screen, TEAL, btn_rect, border_radius=12)
            text_color = WHITE
        else:
            pygame.draw.rect(screen, SAGE_LIGHT, btn_rect, border_radius=12)
            pygame.draw.rect(screen, SAGE, btn_rect, border_radius=12, width=1)
            text_color = DARK_GRAY
        
        # Sparkle icon for active state
        if has_meals:
            spark_x = btn_rect.x + 28
            spark_y = btn_rect.y + 28
            self._draw_sparkle(screen, spark_x, spark_y, 8, WHITE)
        
        # Text
        if self.generating:
            text = "Generating..."
        elif has_meals:
            text = f"Generate List from Meal Plan ({meal_count} meals)"
        else:
            text = "Add meals to generate a list"
        
        btn_text = self.fonts['body'].render(text, True, text_color)
        text_x = btn_rect.x + (50 if has_meals else 20)
        screen.blit(btn_text, (text_x, btn_rect.y + 16))
    
    def _draw_sparkle(self, screen, cx, cy, size, color):
        points = [
            (cx, cy - size),
            (cx + size * 0.2, cy - size * 0.2),
            (cx + size, cy),
            (cx + size * 0.2, cy + size * 0.2),
            (cx, cy + size),
            (cx - size * 0.2, cy + size * 0.2),
            (cx - size, cy),
            (cx - size * 0.2, cy - size * 0.2),
        ]
        points = [(int(px), int(py)) for px, py in points]
        pygame.draw.polygon(screen, color, points)
    
    def _draw_list_card(self, screen, grocery_list, y):
        """Draw a grocery list card."""
        card_rect = pygame.Rect(30, y, WIDTH - 60, 70)
        
        # Soft shadow
        shadow_surface = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 12), (0, 0, card_rect.width, card_rect.height), border_radius=12)
        screen.blit(shadow_surface, (card_rect.x + 2, card_rect.y + 2))
        
        # Card background
        pygame.draw.rect(screen, CARD_BG, card_rect, border_radius=12)
        pygame.draw.rect(screen, SAGE, card_rect, border_radius=12, width=1)
        
        # Name
        name = grocery_list.get('name', 'Grocery List')
        name_text = self.fonts['body'].render(name, True, SOFT_BLACK)
        screen.blit(name_text, (card_rect.x + 20, card_rect.y + 12))
        
        # Stats as pills
        item_count = grocery_list.get('item_count', 0)
        recipe_count = grocery_list.get('recipe_count', 0)
        
        pill_y = card_rect.y + 42
        pill_x = card_rect.x + 20
        
        items_str = f"{item_count} items"
        items_width = self.fonts['small'].size(items_str)[0] + 16
        items_rect = pygame.Rect(pill_x, pill_y, items_width, 22)
        pygame.draw.rect(screen, SAGE_LIGHT, items_rect, border_radius=11)
        items_text = self.fonts['small'].render(items_str, True, SOFT_BLACK)
        screen.blit(items_text, (pill_x + 8, pill_y + 3))
        pill_x += items_width + 8
        
        recipes_str = f"{recipe_count} recipes"
        recipes_width = self.fonts['small'].size(recipes_str)[0] + 16
        recipes_rect = pygame.Rect(pill_x, pill_y, recipes_width, 22)
        pygame.draw.rect(screen, SAGE_LIGHT, recipes_rect, border_radius=11)
        recipes_text = self.fonts['small'].render(recipes_str, True, SOFT_BLACK)
        screen.blit(recipes_text, (pill_x + 8, pill_y + 3))
        
        # Chevron in teal
        chevron_x = card_rect.x + card_rect.width - 35
        chevron_y = card_rect.y + 35
        pygame.draw.line(screen, TEAL, (chevron_x, chevron_y - 8), (chevron_x + 8, chevron_y), 2)
        pygame.draw.line(screen, TEAL, (chevron_x + 8, chevron_y), (chevron_x, chevron_y + 8), 2)
    
    def _draw_list_detail(self, screen, content_bottom):
        """Draw a specific grocery list with checkable items."""
        self._draw_header_detail(screen)
        
        y_start = 90
        visible_height = content_bottom - y_start
        
        categories = self.current_list.get('categories', {})
        
        # Calculate content height
        content_height = 20
        for cat_name, items in categories.items():
            if items:
                content_height += 45  # Category header
                content_height += len(items) * 55  # Items
                content_height += 15  # Spacing
        
        self.max_scroll = max(0, content_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        # Create scrollable surface
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        content_surface.fill(WARM_BG)
        
        y = 10
        for cat_name, items in categories.items():
            if items:
                y = self._draw_category(content_surface, cat_name, items, y)
        
        screen.blit(content_surface, (0, y_start), (0, self.scroll_offset, WIDTH, visible_height))
    
    def _draw_header_detail(self, screen):
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
        name = self.current_list.get('name', 'Grocery List')
        if len(name) > 20:
            name = name[:17] + '...'
        title = self.fonts['header'].render(name, True, SOFT_BLACK)
        screen.blit(title, (150, 20))
        
        # Progress pill
        checked, total = self.grocery_manager.get_checked_count(self.current_list)
        progress = f"{checked}/{total} checked"
        prog_width = self.fonts['small'].size(progress)[0] + 16
        prog_rect = pygame.Rect(150, 52, prog_width, 24)
        pygame.draw.rect(screen, SAGE_LIGHT, prog_rect, border_radius=12)
        subtitle = self.fonts['small'].render(progress, True, SOFT_BLACK)
        screen.blit(subtitle, (158, 56))
        
        # Delete button - subtle coral
        delete_rect = pygame.Rect(WIDTH - 100, 25, 70, 35)
        pygame.draw.rect(screen, (250, 230, 230), delete_rect, border_radius=10)
        pygame.draw.rect(screen, (220, 180, 180), delete_rect, border_radius=10, width=1)
        delete_text = self.fonts['small'].render("Delete", True, (180, 80, 80))
        screen.blit(delete_text, (delete_rect.x + (delete_rect.width - delete_text.get_width()) // 2, 
                                  delete_rect.y + 8))
    
    def _draw_category(self, surface, cat_name, items, y):
        """Draw a category section."""
        # Category header - subtle background
        header_rect = pygame.Rect(30, y, WIDTH - 60, 35)
        pygame.draw.rect(surface, SAGE_LIGHT, header_rect, border_radius=8)
        
        cat_text = self.fonts['body'].render(cat_name, True, SOFT_BLACK)
        surface.blit(cat_text, (45, y + 8))
        
        # Item count
        count_text = self.fonts['small'].render(f"{len(items)}", True, DARK_GRAY)
        surface.blit(count_text, (WIDTH - 60, y + 10))
        
        y += 45
        
        # Items
        for i, item in enumerate(items):
            self._draw_item(surface, item, y, cat_name, i)
            y += 55
        
        y += 15  # Spacing between categories
        return y
    
    def _draw_item(self, surface, item, y, category, index):
        """Draw a checkable grocery item."""
        item_rect = pygame.Rect(30, y, WIDTH - 60, 48)
        
        is_checked = self.grocery_manager.is_checked(self.current_list, category, index)
        
        # Card background
        if is_checked:
            pygame.draw.rect(surface, CHECK_BG, item_rect, border_radius=10)
        else:
            # Soft shadow for unchecked
            shadow_surface = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, 8), (0, 0, item_rect.width, item_rect.height), border_radius=10)
            surface.blit(shadow_surface, (item_rect.x + 1, item_rect.y + 1))
            pygame.draw.rect(surface, CARD_BG, item_rect, border_radius=10)
            pygame.draw.rect(surface, SAGE, item_rect, border_radius=10, width=1)
        
        # Checkbox
        check_x = item_rect.x + 18
        check_y = item_rect.y + 13
        check_rect = pygame.Rect(check_x, check_y, 22, 22)
        
        if is_checked:
            pygame.draw.rect(surface, CHECK_GREEN, check_rect, border_radius=6)
            # Checkmark
            pygame.draw.line(surface, WHITE, (check_x + 5, check_y + 11), (check_x + 9, check_y + 16), 2)
            pygame.draw.line(surface, WHITE, (check_x + 9, check_y + 16), (check_x + 17, check_y + 6), 2)
        else:
            pygame.draw.rect(surface, SAGE, check_rect, 2, border_radius=6)
        
        # Item text
        item_name = item.get('item', str(item))
        quantity = item.get('quantity', '')
        
        if quantity:
            display_text = f"{quantity} {item_name}"
        else:
            display_text = item_name
        
        if len(display_text) > 45:
            display_text = display_text[:42] + '...'
        
        text_color = DARK_GRAY if is_checked else SOFT_BLACK
        item_text = self.fonts['body'].render(display_text, True, text_color)
        surface.blit(item_text, (check_x + 35, item_rect.y + 13))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        if self.current_list_id and self.current_list:
            return self._handle_detail_touch(x, y)
        else:
            return self._handle_overview_touch(x, y)
    
    def _handle_overview_touch(self, x, y):
        # Back button
        if 30 <= x <= 125 and 20 <= y <= 60:
            return 'back'
        
        # Generate button
        gen_y = 100
        gen_rect = pygame.Rect(30, gen_y, WIDTH - 60, 55)
        if gen_rect.collidepoint(x, y):
            if self.meal_plan_manager and self.meal_plan_manager.get_meal_count() > 0:
                return 'generate_list'
        
        # List cards
        if self.grocery_manager:
            lists = self.grocery_manager.get_all_lists()
            item_height = 80
            list_start_y = gen_y + 70
            
            for i, grocery_list in enumerate(lists):
                card_y = list_start_y + i * item_height
                if 30 <= x <= WIDTH - 30 and card_y <= y <= card_y + 70:
                    self.current_list_id = grocery_list['id']
                    self.current_list = self.grocery_manager.get_list(grocery_list['id'])
                    self.scroll_offset = 0
                    return f"view_list_{grocery_list['id']}"
        
        return None
    
    def _handle_detail_touch(self, x, y):
        # Back button
        if 30 <= x <= 125 and 20 <= y <= 60:
            self.current_list_id = None
            self.current_list = None
            self.scroll_offset = 0
            return 'back_to_lists'
        
        # Delete button
        if WIDTH - 100 <= x <= WIDTH - 30 and 25 <= y <= 60:
            if self.grocery_manager and self.current_list_id:
                self.grocery_manager.delete_list(self.current_list_id)
                self.current_list_id = None
                self.current_list = None
                self.scroll_offset = 0
                return 'deleted_list'
        
        # Item checkboxes
        y_start = 90
        content_y = y - y_start + self.scroll_offset
        
        categories = self.current_list.get('categories', {})
        item_y = 10
        
        for cat_name, items in categories.items():
            if items:
                item_y += 45  # Category header
                
                for i, item in enumerate(items):
                    if item_y <= content_y <= item_y + 48:
                        self.grocery_manager.toggle_item(self.current_list_id, cat_name, i)
                        self.current_list = self.grocery_manager.get_list(self.current_list_id)
                        return f'toggled_{cat_name}_{i}'
                    item_y += 55
                
                item_y += 15
        
        return None
    
    def generate_list(self):
        """Generate a grocery list from the current meal plan."""
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
        
        return list_id
    
    def handle_scroll(self, delta):
        self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset + delta))