"""
ui_new/views/meal_prep_view.py

Description:
    * AI-powered meal prep planning view

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *


class MealPrepView:
    """AI-powered weekly meal planning view."""
    
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    MEALS = ['Breakfast', 'Lunch', 'Dinner']
    
    def __init__(self, fonts):
        self.fonts = fonts
        self.meal_plan_manager = None
        self.bedrock_manager = None
        self.config = None
        
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Generation state
        self.show_generate_modal = False
        self.prompt_text = ""
        self.generating = False
        self.generation_status = ""
        
        # Recipe preview modal state
        self.show_recipe_modal = False
        self.selected_day = None
        self.selected_meal_type = None
        self.selected_meal = None
        
        # Quick prompts
        self.quick_prompts = [
            "Healthy balanced meals",
            "High protein, low carb",
            "Quick & easy (under 30 min)",
            "Budget-friendly meals",
            "Vegetarian week",
            "Comfort food classics",
        ]
    
    def set_managers(self, meal_plan_manager, bedrock_manager=None, config=None):
        """Set the data managers."""
        self.meal_plan_manager = meal_plan_manager
        self.bedrock_manager = bedrock_manager
        self.config = config
    
    def draw(self, screen, state, keyboard_visible=False):
        content_bottom = HEIGHT - NAV_HEIGHT
        if keyboard_visible:
            content_bottom = HEIGHT - KEYBOARD_HEIGHT
        
        self._draw_header(screen)
        
        if self.meal_plan_manager and self.meal_plan_manager.get_meal_count() > 0:
            self._draw_week_grid(screen, content_bottom)
        else:
            self._draw_empty_state(screen)
        
        if self.show_generate_modal:
            self._draw_generate_modal(screen, keyboard_visible)
        
        if self.show_recipe_modal:
            self._draw_recipe_modal(screen)
        
        if self.generating:
            self._draw_generating_overlay(screen)
    
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
        title = self.fonts['header'].render("Meal Prep", True, SOFT_BLACK)
        screen.blit(title, (130, 20))
        
        # Subtitle with meal count
        if self.meal_plan_manager:
            meal_count = self.meal_plan_manager.get_meal_count()
            if meal_count > 0:
                week_start = self.meal_plan_manager.get_week_start()
                subtitle = f"Week of {week_start} • {meal_count} meals"
            else:
                subtitle = "No meals planned yet"
            sub_text = self.fonts['small'].render(subtitle, True, DARK_GRAY)
            screen.blit(sub_text, (130, 52))
        
        # Generate/Regenerate button (top right)
        if self.meal_plan_manager and self.meal_plan_manager.get_meal_count() > 0:
            btn_rect = pygame.Rect(WIDTH - 180, 20, 150, 40)
            pygame.draw.rect(screen, SOFT_BLACK, btn_rect, border_radius=20)
            btn_text = self.fonts['small'].render("✦ Regenerate", True, WHITE)
            screen.blit(btn_text, (btn_rect.x + 25, btn_rect.y + 10))
    
    def _draw_empty_state(self, screen):
        """Draw empty state with generate button."""
        cx, cy = WIDTH // 2, HEIGHT // 2 - 60
        
        # Icon - meal prep container
        pygame.draw.circle(screen, (80, 160, 220), (cx, cy - 20), 60)
        
        # Container icon
        container_w = 70
        container_h = 50
        left = cx - container_w // 2
        top = cy - 20 - container_h // 2
        
        pygame.draw.rect(screen, WHITE, (left, top, container_w, container_h), border_radius=6)
        pygame.draw.rect(screen, (80, 160, 220), (left, top, container_w, 10), 
                        border_top_left_radius=6, border_top_right_radius=6)
        pygame.draw.line(screen, (80, 160, 220), (left + container_w // 3, top + 12), 
                        (left + container_w // 3, top + container_h - 4), 2)
        pygame.draw.line(screen, (80, 160, 220), (left + 2 * container_w // 3, top + 12), 
                        (left + 2 * container_w // 3, top + container_h - 4), 2)
        
        # Title
        title = self.fonts['header'].render("Plan Your Week", True, SOFT_BLACK)
        screen.blit(title, (cx - title.get_width() // 2, cy + 60))
        
        # Description
        desc = self.fonts['body'].render("Let AI generate a personalized meal plan", True, DARK_GRAY)
        screen.blit(desc, (cx - desc.get_width() // 2, cy + 100))
        
        # Generate button
        btn_width = 320
        btn_rect = pygame.Rect(cx - btn_width // 2, cy + 150, btn_width, 55)
        pygame.draw.rect(screen, SOFT_BLACK, btn_rect, border_radius=12)
        
        # Sparkle icon
        spark_x = btn_rect.x + 30
        spark_y = btn_rect.y + 28
        self._draw_sparkle(screen, spark_x, spark_y, 8, WHITE)
        
        btn_text = self.fonts['body'].render("Generate Meal Plan", True, WHITE)
        text_x = btn_rect.x + (btn_width - btn_text.get_width()) // 2 + 10
        screen.blit(btn_text, (text_x, btn_rect.y + 15))
    
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
    
    def _draw_week_grid(self, screen, content_bottom):
        """Draw the weekly meal plan grid."""
        if not self.meal_plan_manager:
            return
        
        y_start = 85
        visible_height = content_bottom - y_start
        
        # Calculate content height
        day_height = 75
        content_height = len(self.DAYS) * day_height + 80  # Extra for clear button
        
        self.max_scroll = max(0, content_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        # Create scrollable surface
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        content_surface.fill(WHITE)
        
        y = 10
        days_data = self.meal_plan_manager.get_all_days()
        
        for day_name in self.DAYS:
            day_data = days_data.get(day_name, {})
            self._draw_day_row(content_surface, day_name, day_data, y)
            y += day_height
        
        # Clear week button at bottom
        clear_rect = pygame.Rect(30, y + 10, WIDTH - 60, 45)
        pygame.draw.rect(content_surface, LIGHT_GRAY, clear_rect, border_radius=10)
        clear_text = self.fonts['body'].render("Clear Week", True, DARK_GRAY)
        content_surface.blit(clear_text, (clear_rect.x + (clear_rect.width - clear_text.get_width()) // 2, 
                                          clear_rect.y + 12))
        
        screen.blit(content_surface, (0, y_start), (0, self.scroll_offset, WIDTH, visible_height))
    
    def _draw_day_row(self, surface, day_name, day_data, y):
        # Day label
        day_label = self.fonts['body'].render(day_name[:3], True, SOFT_BLACK)
        surface.blit(day_label, (30, y + 22))
        
        # Date
        date_str = day_data.get('date', '')[-5:] if day_data.get('date') else ''
        if date_str:
            date_label = self.fonts['caption'].render(date_str, True, DARK_GRAY)
            surface.blit(date_label, (30, y + 45))
        
        # Meal slots
        meals = day_data.get('meals', {})
        slot_width = (WIDTH - 140) // 3
        slot_x = 90
        
        for meal_type in self.MEALS:
            meal = meals.get(meal_type)
            self._draw_meal_slot(surface, slot_x, y + 5, slot_width - 10, 55, meal_type, meal)
            slot_x += slot_width
    
    def _draw_meal_slot(self, surface, x, y, width, height, meal_type, meal):
        slot_rect = pygame.Rect(x, y, width, height)
        
        if meal:
            # Check if hydrated
            is_hydrated = meal.get('hydrated', False)
            
            if is_hydrated:
                # Hydrated - solid dark
                pygame.draw.rect(surface, SOFT_BLACK, slot_rect, border_radius=10)
            else:
                # Not hydrated - outlined with subtle fill
                pygame.draw.rect(surface, (240, 245, 250), slot_rect, border_radius=10)
                pygame.draw.rect(surface, SOFT_BLACK, slot_rect, 2, border_radius=10)
            
            # Recipe name
            name = meal.get('name', 'Recipe')
            max_width = width - 20
            if self.fonts['small'].size(name)[0] > max_width:
                while self.fonts['small'].size(name + '...')[0] > max_width and len(name) > 5:
                    name = name[:-1]
                name += '...'
            
            text_color = WHITE if is_hydrated else SOFT_BLACK
            name_text = self.fonts['small'].render(name, True, text_color)
            surface.blit(name_text, (x + 10, y + 10))
            
            # Meal type label
            type_color = MID_GRAY if is_hydrated else DARK_GRAY
            type_text = self.fonts['caption'].render(meal_type, True, type_color)
            surface.blit(type_text, (x + 10, y + 32))
        else:
            # Empty slot
            pygame.draw.rect(surface, LIGHT_GRAY, slot_rect, border_radius=10)
            
            type_text = self.fonts['caption'].render(meal_type, True, DARK_GRAY)
            type_x = x + (width - type_text.get_width()) // 2
            surface.blit(type_text, (type_x, y + height // 2 - 8))
    
    def _draw_recipe_modal(self, screen):
        """Draw modal to preview/generate recipe."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        modal_width = 500
        modal_height = 280
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        pygame.draw.rect(screen, WHITE, (modal_x, modal_y, modal_width, modal_height), border_radius=16)
        
        # Close button (top right)
        close_x = modal_x + modal_width - 35
        close_y = modal_y + 35
        pygame.draw.circle(screen, LIGHT_GRAY, (close_x, close_y), 18)
        pygame.draw.line(screen, CHARCOAL, (close_x - 6, close_y - 6), (close_x + 6, close_y + 6), 2)
        pygame.draw.line(screen, CHARCOAL, (close_x + 6, close_y - 6), (close_x - 6, close_y + 6), 2)
        
        if not self.selected_meal:
            return
        
        is_hydrated = self.selected_meal.get('hydrated', False)
        recipe_name = self.selected_meal.get('name', 'Recipe')
        
        # Title - meal type and day
        title = f"{self.selected_meal_type} - {self.selected_day}"
        title_text = self.fonts['body'].render(title, True, DARK_GRAY)
        screen.blit(title_text, (modal_x + 25, modal_y + 20))
        
        # Recipe name - truncate to fit
        max_name_width = modal_width - 100  # Leave room for close button
        if self.fonts['header'].size(recipe_name)[0] > max_name_width:
            while self.fonts['header'].size(recipe_name + '...')[0] > max_name_width and len(recipe_name) > 5:
                recipe_name = recipe_name[:-1]
            recipe_name += '...'
        
        name_text = self.fonts['header'].render(recipe_name, True, SOFT_BLACK)
        screen.blit(name_text, (modal_x + 25, modal_y + 50))
        
        if is_hydrated:
            # Show recipe preview info
            recipe_data = self.selected_meal.get('recipe_data', {})
            
            # Time and servings
            info_y = modal_y + 95
            if recipe_data.get('total_time'):
                time_text = self.fonts['small'].render(f"⏱ {recipe_data['total_time']}", True, CHARCOAL)
                screen.blit(time_text, (modal_x + 25, info_y))
            
            if recipe_data.get('servings'):
                servings_text = self.fonts['small'].render(f"🍽 {recipe_data['servings']}", True, CHARCOAL)
                screen.blit(servings_text, (modal_x + 180, info_y))
            
            # Ingredient count
            ing_count = len(recipe_data.get('ingredients', []))
            if ing_count:
                ing_text = self.fonts['small'].render(f"{ing_count} ingredients", True, DARK_GRAY)
                screen.blit(ing_text, (modal_x + 25, info_y + 35))
            
            # View Recipe button
            btn_rect = pygame.Rect(modal_x + 25, modal_y + modal_height - 70, modal_width - 50, 50)
            pygame.draw.rect(screen, SOFT_BLACK, btn_rect, border_radius=12)
            btn_text = self.fonts['body'].render("View Full Recipe", True, WHITE)
            screen.blit(btn_text, (btn_rect.x + (btn_rect.width - btn_text.get_width()) // 2, btn_rect.y + 13))
        else:
            # Show generate prompt
            prompt_text = self.fonts['body'].render("Recipe not yet generated", True, DARK_GRAY)
            screen.blit(prompt_text, (modal_x + 25, modal_y + 100))
            
            hint_text = self.fonts['small'].render("Tap below to generate the full recipe with", True, MID_GRAY)
            screen.blit(hint_text, (modal_x + 25, modal_y + 135))
            hint_text2 = self.fonts['small'].render("ingredients, instructions, and nutrition info.", True, MID_GRAY)
            screen.blit(hint_text2, (modal_x + 25, modal_y + 158))
            
            # Generate Recipe button
            btn_rect = pygame.Rect(modal_x + 25, modal_y + modal_height - 70, modal_width - 50, 50)
            pygame.draw.rect(screen, (80, 160, 220), btn_rect, border_radius=12)
            
            # Sparkle icon
            spark_x = btn_rect.x + 30
            spark_y = btn_rect.y + 25
            self._draw_sparkle(screen, spark_x, spark_y, 8, WHITE)
            
            btn_text = self.fonts['body'].render("Generate Recipe", True, WHITE)
            screen.blit(btn_text, (btn_rect.x + 50, btn_rect.y + 13))
    
    def _draw_generate_modal(self, screen, keyboard_visible):
        """Draw the meal plan generation modal."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        modal_width = 600
        modal_height = 420 if not keyboard_visible else 320
        modal_x = (WIDTH - modal_width) // 2
        modal_y = 50 if keyboard_visible else (HEIGHT - modal_height) // 2
        
        pygame.draw.rect(screen, WHITE, (modal_x, modal_y, modal_width, modal_height), border_radius=16)
        
        # Title
        title = self.fonts['header'].render("Generate Meal Plan", True, SOFT_BLACK)
        screen.blit(title, (modal_x + 25, modal_y + 20))
        
        # Close button
        close_x = modal_x + modal_width - 45
        close_y = modal_y + 25
        pygame.draw.circle(screen, LIGHT_GRAY, (close_x, close_y), 15)
        pygame.draw.line(screen, CHARCOAL, (close_x - 5, close_y - 5), (close_x + 5, close_y + 5), 2)
        pygame.draw.line(screen, CHARCOAL, (close_x + 5, close_y - 5), (close_x - 5, close_y + 5), 2)
        
        # Subtitle
        sub = self.fonts['small'].render("Describe what kind of meals you want this week", True, DARK_GRAY)
        screen.blit(sub, (modal_x + 25, modal_y + 55))
        
        # Input field
        field_rect = pygame.Rect(modal_x + 25, modal_y + 90, modal_width - 50, 50)
        pygame.draw.rect(screen, LIGHT_GRAY, field_rect, border_radius=10)
        
        if self.prompt_text:
            input_text = self.fonts['body'].render(self.prompt_text, True, SOFT_BLACK)
        else:
            input_text = self.fonts['body'].render("e.g., Healthy meals with lots of protein...", True, MID_GRAY)
        screen.blit(input_text, (field_rect.x + 15, field_rect.y + 12))
        
        # Cursor
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = field_rect.x + 15 + self.fonts['body'].size(self.prompt_text)[0] + 2
            pygame.draw.rect(screen, SOFT_BLACK, (cursor_x, field_rect.y + 12, 2, 26))
        
        # Quick prompts (only if keyboard not visible)
        if not keyboard_visible:
            quick_y = modal_y + 155
            quick_label = self.fonts['small'].render("Quick options:", True, DARK_GRAY)
            screen.blit(quick_label, (modal_x + 25, quick_y))
            
            chip_y = quick_y + 30
            chip_x = modal_x + 25
            chip_height = 35
            
            for i, prompt in enumerate(self.quick_prompts):
                chip_width = self.fonts['small'].size(prompt)[0] + 24
                
                if chip_x + chip_width > modal_x + modal_width - 25:
                    chip_x = modal_x + 25
                    chip_y += chip_height + 10
                
                chip_rect = pygame.Rect(chip_x, chip_y, chip_width, chip_height)
                pygame.draw.rect(screen, LIGHT_GRAY, chip_rect, border_radius=17)
                
                chip_text = self.fonts['small'].render(prompt, True, SOFT_BLACK)
                screen.blit(chip_text, (chip_x + 12, chip_y + 8))
                
                chip_x += chip_width + 10
        
        # Generate button
        btn_y = modal_y + modal_height - 65
        btn_rect = pygame.Rect(modal_x + modal_width - 175, btn_y, 150, 45)
        btn_color = SOFT_BLACK if self.prompt_text.strip() else MID_GRAY
        pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)
        
        btn_text = self.fonts['body'].render("Generate", True, WHITE)
        screen.blit(btn_text, (btn_rect.x + 35, btn_rect.y + 11))
        
        # Cancel button
        cancel_rect = pygame.Rect(modal_x + 25, btn_y, 100, 45)
        pygame.draw.rect(screen, LIGHT_GRAY, cancel_rect, border_radius=10)
        cancel_text = self.fonts['body'].render("Cancel", True, SOFT_BLACK)
        screen.blit(cancel_text, (cancel_rect.x + 18, cancel_rect.y + 11))
    
    def _draw_generating_overlay(self, screen):
        """Draw generating animation overlay."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 230))
        screen.blit(overlay, (0, 0))
        
        cx, cy = WIDTH // 2, HEIGHT // 2
        
        # Spinning animation
        ticks = pygame.time.get_ticks()
        for i in range(8):
            angle = i * 45 + ticks / 5
            alpha = 255 - i * 25
            px = cx + int(30 * pygame.math.Vector2(1, 0).rotate(angle).x)
            py = cy + int(30 * pygame.math.Vector2(1, 0).rotate(angle).y)
            pygame.draw.circle(screen, SOFT_BLACK, (px, py), 6 - i * 0.5)
        
        # Status text
        status = self.generation_status or "Generating your meal plan..."
        status_text = self.fonts['body'].render(status, True, CHARCOAL)
        screen.blit(status_text, (cx - status_text.get_width() // 2, cy + 50))
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos
        
        if self.generating:
            return None
        
        if self.show_recipe_modal:
            return self._handle_recipe_modal_touch(x, y)
        
        if self.show_generate_modal:
            return self._handle_modal_touch(x, y, keyboard_visible)
        
        # Back button
        if 30 <= x <= 110 and 20 <= y <= 60:
            return 'back'
        
        # Regenerate button (when meals exist)
        if self.meal_plan_manager and self.meal_plan_manager.get_meal_count() > 0:
            if WIDTH - 180 <= x <= WIDTH - 30 and 20 <= y <= 60:
                self.show_generate_modal = True
                self.prompt_text = ""
                return 'show_generate'
        
        # Empty state generate button
        if self.meal_plan_manager and self.meal_plan_manager.get_meal_count() == 0:
            cx = WIDTH // 2
            cy = HEIGHT // 2 - 60
            btn_width = 320
            btn_rect = pygame.Rect(cx - btn_width // 2, cy + 150, btn_width, 55)
            if btn_rect.collidepoint(x, y):
                self.show_generate_modal = True
                self.prompt_text = ""
                return 'show_generate'
        
        # Clear week button (at bottom of grid)
        if self.meal_plan_manager and self.meal_plan_manager.get_meal_count() > 0:
            y_start = 85
            content_y = y - y_start + self.scroll_offset
            clear_y = len(self.DAYS) * 75 + 10
            
            if 30 <= x <= WIDTH - 30 and clear_y <= content_y <= clear_y + 45:
                self.meal_plan_manager.clear_week()
                return 'cleared_week'
            
        # Meal slot taps
        if self.meal_plan_manager and self.meal_plan_manager.get_meal_count() > 0:
            y_start = 85
            content_y = y - y_start + self.scroll_offset
            day_height = 75
            
            for i, day_name in enumerate(self.DAYS):
                row_y = 10 + i * day_height
                if row_y <= content_y <= row_y + 65:
                    # Check which meal slot was tapped
                    slot_width = (WIDTH - 140) // 3
                    slot_x_start = 90
                    
                    for j, meal_type in enumerate(self.MEALS):
                        slot_x = slot_x_start + j * slot_width
                        if slot_x <= x <= slot_x + slot_width - 10:
                            meal = self.meal_plan_manager.get_meal(day_name, meal_type)
                            if meal:
                                # Show recipe modal
                                self.selected_day = day_name
                                self.selected_meal_type = meal_type
                                self.selected_meal = meal
                                self.show_recipe_modal = True
                                return 'show_recipe_modal'
                    break
        
        return None
    
    def _handle_recipe_modal_touch(self, x, y):
        """Handle touches on the recipe preview modal."""
        modal_width = 500
        modal_height = 280
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        # Close button - match the draw position
        close_x = modal_x + modal_width - 35
        close_y = modal_y + 35
        if (x - close_x) ** 2 + (y - close_y) ** 2 <= 324:  # 18^2
            self.show_recipe_modal = False
            self.selected_meal = None
            self.selected_day = None
            self.selected_meal_type = None
            return 'close_recipe_modal'
        
        # Action button (View or Generate)
        btn_rect = pygame.Rect(modal_x + 25, modal_y + modal_height - 70, modal_width - 50, 50)
        if btn_rect.collidepoint(x, y):
            is_hydrated = self.selected_meal.get('hydrated', False) if self.selected_meal else False
            
            day = self.selected_day
            meal_type = self.selected_meal_type
            
            self.show_recipe_modal = False
            self.selected_meal = None
            self.selected_day = None
            self.selected_meal_type = None
            
            if is_hydrated:
                return f'view_meal_{day}_{meal_type}'
            else:
                return f'hydrate_meal_{day}_{meal_type}'
        
        # Click outside modal to close
        if not (modal_x <= x <= modal_x + modal_width and modal_y <= y <= modal_y + modal_height):
            self.show_recipe_modal = False
            self.selected_meal = None
            self.selected_day = None
            self.selected_meal_type = None
            return 'close_recipe_modal'
        
        return None
    
    def _handle_modal_touch(self, x, y, keyboard_visible):
        modal_width = 600
        modal_height = 420 if not keyboard_visible else 320
        modal_x = (WIDTH - modal_width) // 2
        modal_y = 50 if keyboard_visible else (HEIGHT - modal_height) // 2
        
        # Close button
        close_x = modal_x + modal_width - 45
        close_y = modal_y + 25
        if (x - close_x) ** 2 + (y - close_y) ** 2 <= 225:  # 15^2
            self.show_generate_modal = False
            return 'close_modal'
        
        # Input field tap
        field_rect = pygame.Rect(modal_x + 25, modal_y + 90, modal_width - 50, 50)
        if field_rect.collidepoint(x, y):
            return 'focus_meal_prompt'
        
        # Quick prompts (only if keyboard not visible)
        if not keyboard_visible:
            quick_y = modal_y + 155 + 30
            chip_x = modal_x + 25
            chip_height = 35
            
            for i, prompt in enumerate(self.quick_prompts):
                chip_width = self.fonts['small'].size(prompt)[0] + 24
                
                if chip_x + chip_width > modal_x + modal_width - 25:
                    chip_x = modal_x + 25
                    quick_y += chip_height + 10
                
                chip_rect = pygame.Rect(chip_x, quick_y, chip_width, chip_height)
                if chip_rect.collidepoint(x, y):
                    self.prompt_text = prompt
                    return f'quick_prompt_{i}'
                
                chip_x += chip_width + 10
        
        # Generate button
        btn_y = modal_y + modal_height - 65
        btn_rect = pygame.Rect(modal_x + modal_width - 175, btn_y, 150, 45)
        if btn_rect.collidepoint(x, y) and self.prompt_text.strip():
            return 'generate_meal_plan'
        
        # Cancel button
        cancel_rect = pygame.Rect(modal_x + 25, btn_y, 100, 45)
        if cancel_rect.collidepoint(x, y):
            self.show_generate_modal = False
            return 'cancel'
        
        # Click outside modal
        if not (modal_x <= x <= modal_x + modal_width and modal_y <= y <= modal_y + modal_height):
            self.show_generate_modal = False
            return 'close_modal'
        
        return None
    
    def handle_keyboard_input(self, key):
        """Handle keyboard input for prompt."""
        if not self.show_generate_modal:
            return
        
        if key == 'BACKSPACE':
            self.prompt_text = self.prompt_text[:-1]
        elif key == 'GO':
            if self.prompt_text.strip():
                return 'generate_meal_plan'
        elif key not in ('HIDE', 'SHIFT'):
            self.prompt_text += key
    
    def handle_scroll(self, delta):
        if not self.show_generate_modal and not self.show_recipe_modal:
            self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset + delta))