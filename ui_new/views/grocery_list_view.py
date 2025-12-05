"""
ui_new/views/grocery_list_view.py

Description:
    * Grocery list view - view and manage shopping lists

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *


class GroceryListView:
    """View for managing grocery lists."""
    
    def __init__(self, fonts):
        self.fonts = fonts
        self.grocery_manager = None
        self.meal_plan_manager = None
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # View state
        self.current_list_id = None  # None = show all lists, ID = show specific list
        self.current_list = None
        
        # Generating state
        self.generating = False
    
    def set_managers(self, grocery_manager, meal_plan_manager=None):
        """Set the data managers."""
        self.grocery_manager = grocery_manager
        self.meal_plan_manager = meal_plan_manager
    
    def draw(self, screen, state, keyboard_visible=False):
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
            msg = self.fonts['body'].render("No grocery lists yet", True, DARK_GRAY)
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, list_start_y + 50))
            hint = self.fonts['small'].render("Generate one from your meal plan", True, MID_GRAY)
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, list_start_y + 85))
            return
        
        # Draw lists
        item_height = 80
        y = list_start_y
        
        for grocery_list in lists:
            self._draw_list_card(screen, grocery_list, y)
            y += item_height
    
    def _draw_header_overview(self, screen):
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
        title = self.fonts['header'].render("Grocery Lists", True, SOFT_BLACK)
        screen.blit(title, (130, 20))
        
        # Subtitle
        if self.grocery_manager:
            count = len(self.grocery_manager.get_all_lists())
            subtitle = self.fonts['small'].render(f"{count} lists", True, DARK_GRAY)
            screen.blit(subtitle, (130, 52))
    
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
            pygame.draw.rect(screen, (80, 180, 100), btn_rect, border_radius=12)
            text_color = WHITE
        else:
            pygame.draw.rect(screen, LIGHT_GRAY, btn_rect, border_radius=12)
            text_color = MID_GRAY
        
        # Icon (cart with plus)
        icon_x = btn_rect.x + 30
        icon_y = btn_rect.y + 28
        pygame.draw.circle(screen, text_color, (icon_x, icon_y - 5), 3)
        pygame.draw.circle(screen, text_color, (icon_x + 12, icon_y - 5), 3)
        pygame.draw.lines(screen, text_color, False, [
            (icon_x - 8, icon_y - 15), (icon_x - 5, icon_y), (icon_x + 15, icon_y), (icon_x + 18, icon_y - 12)
        ], 2)
        
        # Text
        if self.generating:
            text = "Generating..."
        elif has_meals:
            text = f"Generate List from Meal Plan ({meal_count} meals)"
        else:
            text = "Add meals to generate a list"
        
        btn_text = self.fonts['body'].render(text, True, text_color)
        screen.blit(btn_text, (btn_rect.x + 55, btn_rect.y + 15))
    
    def _draw_list_card(self, screen, grocery_list, y):
        """Draw a grocery list card."""
        card_rect = pygame.Rect(30, y, WIDTH - 60, 70)
        pygame.draw.rect(screen, LIGHT_GRAY, card_rect, border_radius=12)
        
        # Name
        name = grocery_list.get('name', 'Grocery List')
        name_text = self.fonts['body'].render(name, True, SOFT_BLACK)
        screen.blit(name_text, (card_rect.x + 20, card_rect.y + 12))
        
        # Stats
        item_count = grocery_list.get('item_count', 0)
        recipe_count = grocery_list.get('recipe_count', 0)
        stats = f"{item_count} items • {recipe_count} recipes"
        stats_text = self.fonts['small'].render(stats, True, DARK_GRAY)
        screen.blit(stats_text, (card_rect.x + 20, card_rect.y + 40))
        
        # Chevron
        chevron_x = card_rect.x + card_rect.width - 35
        chevron_y = card_rect.y + 35
        pygame.draw.line(screen, MID_GRAY, (chevron_x, chevron_y - 8), (chevron_x + 8, chevron_y), 2)
        pygame.draw.line(screen, MID_GRAY, (chevron_x + 8, chevron_y), (chevron_x, chevron_y + 8), 2)
    
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
                content_height += 40  # Category header
                content_height += len(items) * 50  # Items
                content_height += 15  # Spacing
        
        self.max_scroll = max(0, content_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        # Create scrollable surface
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        content_surface.fill(WHITE)
        
        y = 10
        for cat_name, items in categories.items():
            if items:
                y = self._draw_category(content_surface, cat_name, items, y)
        
        screen.blit(content_surface, (0, y_start), (0, self.scroll_offset, WIDTH, visible_height))
    
    def _draw_header_detail(self, screen):
        # Back button (to list overview)
        back_rect = pygame.Rect(30, 20, 80, 40)
        pygame.draw.rect(screen, LIGHT_GRAY, back_rect, border_radius=20)
        
        ax = back_rect.x + 20
        ay = back_rect.y + 20
        pygame.draw.line(screen, CHARCOAL, (ax + 8, ay - 6), (ax, ay), 2)
        pygame.draw.line(screen, CHARCOAL, (ax, ay), (ax + 8, ay + 6), 2)
        
        back_text = self.fonts['small'].render("Back", True, CHARCOAL)
        screen.blit(back_text, (ax + 15, ay - 9))
        
        # Title
        name = self.current_list.get('name', 'Grocery List')
        if len(name) > 25:
            name = name[:22] + '...'
        title = self.fonts['header'].render(name, True, SOFT_BLACK)
        screen.blit(title, (130, 20))
        
        # Progress
        checked, total = self.grocery_manager.get_checked_count(self.current_list)
        progress = f"{checked}/{total} items checked"
        subtitle = self.fonts['small'].render(progress, True, DARK_GRAY)
        screen.blit(subtitle, (130, 52))
        
        # Delete button
        delete_rect = pygame.Rect(WIDTH - 110, 25, 80, 35)
        pygame.draw.rect(screen, (240, 200, 200), delete_rect, border_radius=8)
        delete_text = self.fonts['small'].render("Delete", True, (180, 60, 60))
        screen.blit(delete_text, (delete_rect.x + 18, delete_rect.y + 8))
    
    def _draw_category(self, surface, cat_name, items, y):
        """Draw a category section."""
        # Category header
        cat_text = self.fonts['body'].render(cat_name, True, SOFT_BLACK)
        surface.blit(cat_text, (30, y + 8))
        y += 40
        
        # Items
        for i, item in enumerate(items):
            self._draw_item(surface, item, y, cat_name, i)
            y += 50
        
        y += 15  # Spacing between categories
        return y
    
    def _draw_item(self, surface, item, y, category, index):
        """Draw a checkable grocery item."""
        item_rect = pygame.Rect(30, y, WIDTH - 60, 45)
        
        is_checked = self.grocery_manager.is_checked(self.current_list, category, index)
        
        if is_checked:
            pygame.draw.rect(surface, (240, 255, 240), item_rect, border_radius=10)
        else:
            pygame.draw.rect(surface, LIGHT_GRAY, item_rect, border_radius=10)
        
        # Checkbox
        check_x = item_rect.x + 20
        check_y = item_rect.y + 12
        check_rect = pygame.Rect(check_x, check_y, 22, 22)
        
        if is_checked:
            pygame.draw.rect(surface, (80, 180, 100), check_rect, border_radius=5)
            # Checkmark
            pygame.draw.line(surface, WHITE, (check_x + 5, check_y + 11), (check_x + 9, check_y + 16), 2)
            pygame.draw.line(surface, WHITE, (check_x + 9, check_y + 16), (check_x + 17, check_y + 6), 2)
        else:
            pygame.draw.rect(surface, MID_GRAY, check_rect, 2, border_radius=5)
        
        # Item text
        item_name = item.get('item', str(item))
        quantity = item.get('quantity', '')
        
        if quantity:
            display_text = f"{quantity} {item_name}"
        else:
            display_text = item_name
        
        if len(display_text) > 50:
            display_text = display_text[:47] + '...'
        
        text_color = DARK_GRAY if is_checked else SOFT_BLACK
        item_text = self.fonts['body'].render(display_text, True, text_color)
        surface.blit(item_text, (check_x + 35, item_rect.y + 12))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        if self.current_list_id and self.current_list:
            return self._handle_detail_touch(x, y)
        else:
            return self._handle_overview_touch(x, y)
    
    def _handle_overview_touch(self, x, y):
        # Back button
        if 30 <= x <= 110 and 20 <= y <= 60:
            return 'back'
        
        # Generate button
        gen_y = 100  # Matches: y_start (90) + 10
        gen_rect = pygame.Rect(30, gen_y, WIDTH - 60, 55)
        if gen_rect.collidepoint(x, y):
            if self.meal_plan_manager and self.meal_plan_manager.get_meal_count() > 0:
                return 'generate_list'
        
        # List cards
        if self.grocery_manager:
            lists = self.grocery_manager.get_all_lists()
            item_height = 80
            list_start_y = gen_y + 70  # Changed from 180 to match draw code
            
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
        if 30 <= x <= 110 and 20 <= y <= 60:
            self.current_list_id = None
            self.current_list = None
            self.scroll_offset = 0
            return 'back_to_lists'
        
        # Delete button
        if WIDTH - 110 <= x <= WIDTH - 30 and 25 <= y <= 60:
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
                item_y += 40  # Category header
                
                for i, item in enumerate(items):
                    if item_y <= content_y <= item_y + 45:
                        # Toggle item
                        self.grocery_manager.toggle_item(self.current_list_id, cat_name, i)
                        self.current_list = self.grocery_manager.get_list(self.current_list_id)
                        return f'toggled_{cat_name}_{i}'
                    item_y += 50
                
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