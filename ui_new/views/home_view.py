"""
ui_new/views/home_view.py

Description:
    * Home screen view - clean minimal design with meal plan preview and timer

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from datetime import datetime
from ui_new.constants import *


class HomeView:
    def __init__(self, fonts):
        self.fonts = fonts
        self.meal_plan_manager = None
        self.favorites_manager = None
        self.saved_recipes_manager = None
        
        # Timer state
        self.timer_active = False
        self.timer_start_ticks = 0
        self.timer_duration = 0
        self.timer_done = False
        self.show_timer_modal = False
        self.timer_input = ""
        
        # Flash state
        self.flash_on = False
        self.last_flash_ticks = 0
        
        # Sleep state
        self.is_sleeping = False
        self.last_activity_ticks = pygame.time.get_ticks()
        self.sleep_timeout = 60000
        
        # Pre-render gradient background
        self.gradient_surface = None

    def _create_gradient(self, width, height):
        """Create a subtle warm gradient background."""
        if self.gradient_surface and self.gradient_surface.get_size() == (width, height):
            return self.gradient_surface
        
        self.gradient_surface = pygame.Surface((width, height))
        
        # Soft warm white gradient - 10% warmer
        top_color = (255, 251, 245)      # Warm ivory white
        bottom_color = (252, 245, 235)   # Soft cream
        
        for y in range(height):
            t = y / height
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
            pygame.draw.line(self.gradient_surface, (r, g, b), (0, y), (width, y))
        
        return self.gradient_surface

    def wake(self):
        """Wake from sleep."""
        self.is_sleeping = False
        self.last_activity_ticks = pygame.time.get_ticks()

    def reset_activity(self):
        """Reset the inactivity timer."""
        self.last_activity_ticks = pygame.time.get_ticks()

    def draw(self, screen, state):
        elapsed = pygame.time.get_ticks() - self.last_activity_ticks
        
        # Check for sleep
        if not self.is_sleeping and not self.timer_active and not self.timer_done and not self.show_timer_modal:
            if elapsed > self.sleep_timeout:
                self.is_sleeping = True
        
        # Draw sleep screen
        if self.is_sleeping:
            self._draw_sleep_screen(screen)
            return
        
        # Flash red if timer done
        if self.timer_done:
            ticks = pygame.time.get_ticks()
            if ticks - self.last_flash_ticks > 500:
                self.flash_on = not self.flash_on
                self.last_flash_ticks = ticks
            if self.flash_on:
                screen.fill((255, 60, 60))
            else:
                screen.blit(self._create_gradient(WIDTH, HEIGHT), (0, 0))
        else:
            # Draw gradient background
            screen.blit(self._create_gradient(WIDTH, HEIGHT), (0, 0))
        
        self._draw_header(screen)
        self._draw_quick_actions(screen)
        self._draw_todays_meals(screen)
        
        if self.timer_active:
            self._draw_timer_pill(screen)
        
        if self.timer_done:
            self._draw_timer_done(screen)
        
        if self.show_timer_modal:
            self._draw_timer_modal(screen)

    def _draw_sleep_screen(self, screen):
        """Draw minimal sleep screen with analog clock only."""
        screen.fill((15, 15, 20))
        
        now = datetime.now()
        cx, cy = WIDTH // 2, HEIGHT // 2
        radius = 150
        
        pygame.draw.circle(screen, (30, 30, 35), (cx, cy), radius)
        pygame.draw.circle(screen, (50, 50, 55), (cx, cy), radius, 3)
        
        for i in range(12):
            angle = i * 30 - 90
            outer_x = cx + int((radius - 15) * pygame.math.Vector2(1, 0).rotate(angle).x)
            outer_y = cy + int((radius - 15) * pygame.math.Vector2(1, 0).rotate(angle).y)
            inner_len = 25 if i % 3 == 0 else 12
            inner_x = cx + int((radius - 15 - inner_len) * pygame.math.Vector2(1, 0).rotate(angle).x)
            inner_y = cy + int((radius - 15 - inner_len) * pygame.math.Vector2(1, 0).rotate(angle).y)
            thickness = 3 if i % 3 == 0 else 2
            pygame.draw.line(screen, (80, 80, 90), (inner_x, inner_y), (outer_x, outer_y), thickness)
        
        hour = now.hour % 12
        minute = now.minute
        
        hour_angle = (hour + minute / 60) * 30 - 90
        hour_length = radius * 0.5
        hour_x = cx + int(hour_length * pygame.math.Vector2(1, 0).rotate(hour_angle).x)
        hour_y = cy + int(hour_length * pygame.math.Vector2(1, 0).rotate(hour_angle).y)
        pygame.draw.line(screen, (180, 180, 190), (cx, cy), (hour_x, hour_y), 6)
        
        min_angle = minute * 6 - 90
        min_length = radius * 0.75
        min_x = cx + int(min_length * pygame.math.Vector2(1, 0).rotate(min_angle).x)
        min_y = cy + int(min_length * pygame.math.Vector2(1, 0).rotate(min_angle).y)
        pygame.draw.line(screen, (150, 150, 160), (cx, cy), (min_x, min_y), 4)
        
        pygame.draw.circle(screen, (100, 100, 110), (cx, cy), 8)
    
    def set_managers(self, meal_plan_manager=None, favorites_manager=None, saved_recipes_manager=None):
        self.meal_plan_manager = meal_plan_manager
        self.favorites_manager = favorites_manager
        self.saved_recipes_manager = saved_recipes_manager
    
    def _draw_header(self, screen):
        """Header row - title left, clock right, vertically aligned."""
        header_y = 25
        
        # Title and subtitle on left
        title = self.fonts['title'].render("AI Sous Chef", True, SOFT_BLACK)
        screen.blit(title, (40, header_y))
        
        subtitle = self.fonts['small'].render("Find a recipe or create something new", True, DARK_GRAY)
        screen.blit(subtitle, (40, header_y + 50))
        
        # Clock box on right - aligned with title
        now = datetime.now()
        time_str = now.strftime("%I:%M").lstrip("0")
        ampm = now.strftime("%p")
        
        clock_rect = pygame.Rect(WIDTH - 180, header_y, 140, 65)
        pygame.draw.rect(screen, LIGHT_GRAY, clock_rect, border_radius=12)
        
        time_text = self.fonts['header'].render(time_str, True, SOFT_BLACK)
        screen.blit(time_text, (clock_rect.x + 18, clock_rect.y + 10))
        
        ampm_text = self.fonts['small'].render(ampm, True, DARK_GRAY)
        screen.blit(ampm_text, (clock_rect.x + 18 + time_text.get_width() + 5, clock_rect.y + 18))
        
        date_str = now.strftime("%a, %b %d")
        date_text = self.fonts['small'].render(date_str, True, DARK_GRAY)
        screen.blit(date_text, (clock_rect.x + 18, clock_rect.y + 40))
    
    def _draw_quick_actions(self, screen):
        """Search and Create cards."""
        y = 110
        card_width = (WIDTH - 100) // 2
        card_height = 160
        
        # Search card - warm sage green, inviting but not loud
        search_rect = pygame.Rect(40, y, card_width, card_height)
        search_bg = (142, 157, 139)  # Muted sage
        pygame.draw.rect(screen, search_bg, search_rect, border_radius=16)
        
        search_title = self.fonts['header'].render("Search", True, WHITE)
        screen.blit(search_title, (search_rect.x + 25, search_rect.y + 22))
        
        search_desc = self.fonts['small'].render("Find recipes from", True, (230, 235, 228))
        screen.blit(search_desc, (search_rect.x + 25, search_rect.y + 62))
        search_desc2 = self.fonts['small'].render("our collection", True, (230, 235, 228))
        screen.blit(search_desc2, (search_rect.x + 25, search_rect.y + 86))
        
        self._draw_search_icon(screen, search_rect.x + card_width - 75, search_rect.y + card_height - 65, WHITE)
        
        # Create card - teal blue
        create_rect = pygame.Rect(60 + card_width, y, card_width, card_height)
        create_bg = (26, 94, 120)  # #1a5e78
        pygame.draw.rect(screen, create_bg, create_rect, border_radius=16)
        
        create_title = self.fonts['header'].render("Create", True, WHITE)
        screen.blit(create_title, (create_rect.x + 25, create_rect.y + 22))
        
        create_desc = self.fonts['small'].render("Generate a custom", True, MID_GRAY)
        screen.blit(create_desc, (create_rect.x + 25, create_rect.y + 62))
        create_desc2 = self.fonts['small'].render("recipe with AI", True, MID_GRAY)
        screen.blit(create_desc2, (create_rect.x + 25, create_rect.y + 86))
        
        self._draw_sparkles_icon(screen, create_rect.x + card_width - 85, create_rect.y + card_height - 75, WHITE)
    
    def _draw_todays_meals(self, screen):
        """Today's meals section - more spacious layout."""
        y = 290
        box_height = 170
        
        box_rect = pygame.Rect(40, y, WIDTH - 80, box_height)
        # Light sage at ~25% opacity blended with white
        sage_light = (227, 231, 226)  # Sage (142,157,139) at ~25% over white
        pygame.draw.rect(screen, sage_light, box_rect, border_radius=16)
        
        # Title row
        today = datetime.now().strftime("%A")
        title = self.fonts['body'].render("Today's Meals", True, SOFT_BLACK)
        screen.blit(title, (box_rect.x + 25, box_rect.y + 20))
        
        day_text = self.fonts['caption'].render(today, True, DARK_GRAY)
        screen.blit(day_text, (box_rect.x + 25 + title.get_width() + 12, box_rect.y + 24))
        
        # Check if we have meals
        has_meals = False
        day_data = None
        
        if self.meal_plan_manager and self.meal_plan_manager.get_meal_count() > 0:
            day_data = self.meal_plan_manager.get_day(today)
            if day_data:
                meals = day_data.get('meals', {})
                for meal_type in ['Breakfast', 'Lunch', 'Dinner']:
                    if meals.get(meal_type):
                        has_meals = True
                        break
        
        if has_meals and day_data:
            meals = day_data.get('meals', {})
            
            # Three meal slots with more padding
            slot_width = (box_rect.width - 80) // 3
            slot_height = 85
            slot_x = box_rect.x + 25
            slot_y = box_rect.y + 60
            
            for meal_type in ['Breakfast', 'Lunch', 'Dinner']:
                meal = meals.get(meal_type)
                self._draw_meal_slot(screen, slot_x, slot_y, slot_width, slot_height, meal_type, meal)
                slot_x += slot_width + 15
        else:
            self._draw_no_meals(screen, box_rect)
    
    def _draw_meal_slot(self, screen, x, y, width, height, meal_type, meal):
        """Individual meal slot with better spacing."""
        slot_rect = pygame.Rect(x, y, width, height)
        
        if meal:
            is_hydrated = meal.get('hydrated', False)
            
            if is_hydrated:
                pygame.draw.rect(screen, SOFT_BLACK, slot_rect, border_radius=12)
                text_color = WHITE
                sub_color = MID_GRAY
            else:
                pygame.draw.rect(screen, WHITE, slot_rect, border_radius=12)
                text_color = SOFT_BLACK
                sub_color = DARK_GRAY
            
            # Meal type label
            type_text = self.fonts['caption'].render(meal_type, True, sub_color)
            screen.blit(type_text, (x + 15, y + 12))
            
            # Recipe name (with truncation)
            name = meal.get('name', 'Recipe')
            max_width = width - 30
            if self.fonts['body'].size(name)[0] > max_width:
                while self.fonts['body'].size(name + '...')[0] > max_width and len(name) > 3:
                    name = name[:-1]
                name += '...'
            
            name_text = self.fonts['body'].render(name, True, text_color)
            screen.blit(name_text, (x + 15, y + 38))
        else:
            pygame.draw.rect(screen, WHITE, slot_rect, border_radius=12)
            
            type_text = self.fonts['caption'].render(meal_type, True, DARK_GRAY)
            screen.blit(type_text, (x + 15, y + 12))
            
            empty_text = self.fonts['body'].render("—", True, MID_GRAY)
            screen.blit(empty_text, (x + 15, y + 38))
    
    def _draw_no_meals(self, screen, box_rect):
        """Empty state with button."""
        center_y = box_rect.y + box_rect.height // 2
        
        msg = self.fonts['body'].render("No meals planned for today", True, DARK_GRAY)
        screen.blit(msg, (box_rect.x + 25, center_y - 25))
        
        btn_rect = pygame.Rect(box_rect.x + 25, center_y + 10, 180, 40)
        pygame.draw.rect(screen, SOFT_BLACK, btn_rect, border_radius=10)
        btn_text = self.fonts['small'].render("Plan Your Week", True, WHITE)
        screen.blit(btn_text, (btn_rect.x + 20, btn_rect.y + 10))
    
    def _draw_timer_pill(self, screen):
        """Active timer display."""
        elapsed = (pygame.time.get_ticks() - self.timer_start_ticks) // 1000
        remaining = max(0, self.timer_duration - elapsed)
        
        if remaining == 0:
            self.timer_active = False
            self.timer_done = True
            self.last_flash_ticks = pygame.time.get_ticks()
            return
        
        mins = remaining // 60
        secs = remaining % 60
        time_str = f"{mins}:{secs:02d}"
        
        pill_rect = pygame.Rect(WIDTH // 2 - 90, 20, 180, 50)
        pygame.draw.rect(screen, (80, 180, 100), pill_rect, border_radius=25)
        
        timer_text = self.fonts['header'].render(time_str, True, WHITE)
        screen.blit(timer_text, (pill_rect.x + 25, pill_rect.y + 10))
        
        cancel_x = pill_rect.x + pill_rect.width - 30
        cancel_y = pill_rect.y + 25
        pygame.draw.circle(screen, (60, 150, 80), (cancel_x, cancel_y), 15)
        pygame.draw.line(screen, WHITE, (cancel_x - 5, cancel_y - 5), (cancel_x + 5, cancel_y + 5), 2)
        pygame.draw.line(screen, WHITE, (cancel_x + 5, cancel_y - 5), (cancel_x - 5, cancel_y + 5), 2)
    
    def _draw_timer_done(self, screen):
        """Timer finished overlay."""
        modal_rect = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 - 70, 280, 140)
        pygame.draw.rect(screen, WHITE, modal_rect, border_radius=16)
        pygame.draw.rect(screen, (255, 60, 60), modal_rect, 3, border_radius=16)
        
        done_text = self.fonts['header'].render("TIME'S UP!", True, (255, 60, 60))
        screen.blit(done_text, (modal_rect.x + (280 - done_text.get_width()) // 2, modal_rect.y + 25))
        
        dismiss_rect = pygame.Rect(modal_rect.x + 40, modal_rect.y + 85, 200, 40)
        pygame.draw.rect(screen, SOFT_BLACK, dismiss_rect, border_radius=10)
        dismiss_text = self.fonts['body'].render("Dismiss", True, WHITE)
        screen.blit(dismiss_text, (dismiss_rect.x + (200 - dismiss_text.get_width()) // 2, dismiss_rect.y + 10))
    
    def _draw_timer_modal(self, screen):
        """Timer input modal."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        modal_width = 350
        modal_height = 260
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        pygame.draw.rect(screen, WHITE, (modal_x, modal_y, modal_width, modal_height), border_radius=16)
        
        title = self.fonts['header'].render("Kitchen Timer", True, SOFT_BLACK)
        screen.blit(title, (modal_x + 25, modal_y + 20))
        
        # Close button - sage light fill with soft black X
        close_x = modal_x + modal_width - 35
        close_y = modal_y + 35
        pygame.draw.circle(screen, SAGE_LIGHT, (close_x, close_y), 16)
        pygame.draw.line(screen, SOFT_BLACK, (close_x - 5, close_y - 5), (close_x + 5, close_y + 5), 2)
        pygame.draw.line(screen, SOFT_BLACK, (close_x + 5, close_y - 5), (close_x - 5, close_y + 5), 2)
        
        # Input field - white fill with sage border
        input_rect = pygame.Rect(modal_x + 25, modal_y + 65, modal_width - 50, 50)
        pygame.draw.rect(screen, WHITE, input_rect, border_radius=10)
        pygame.draw.rect(screen, SAGE, input_rect, border_radius=10, width=1)
        
        display = self.timer_input if self.timer_input else "0"
        input_text = self.fonts['header'].render(f"{display} min", True, SOFT_BLACK if self.timer_input else MID_GRAY)
        screen.blit(input_text, (input_rect.x + 20, input_rect.y + 10))
        
        # Quick time buttons - sage light fill with sage border
        quick_y = modal_y + 130
        quick_times = [1, 5, 10, 15, 30]
        btn_width = (modal_width - 70) // 5
        btn_x = modal_x + 25
        
        for mins in quick_times:
            btn_rect = pygame.Rect(btn_x, quick_y, btn_width - 5, 38)
            pygame.draw.rect(screen, SAGE_LIGHT, btn_rect, border_radius=8)
            pygame.draw.rect(screen, SAGE, btn_rect, border_radius=8, width=1)
            btn_text = self.fonts['body'].render(str(mins), True, SOFT_BLACK)
            screen.blit(btn_text, (btn_rect.x + (btn_width - 5 - btn_text.get_width()) // 2, btn_rect.y + 8))
            btn_x += btn_width
        
        # Start button - teal when active, sage light when disabled
        start_rect = pygame.Rect(modal_x + 25, modal_y + modal_height - 55, modal_width - 50, 42)
        if self.timer_input:
            pygame.draw.rect(screen, TEAL, start_rect, border_radius=10)
            start_text = self.fonts['body'].render("Start Timer", True, WHITE)
        else:
            pygame.draw.rect(screen, SAGE_LIGHT, start_rect, border_radius=10)
            start_text = self.fonts['body'].render("Start Timer", True, DARK_GRAY)
        screen.blit(start_text, (start_rect.x + (modal_width - 50 - start_text.get_width()) // 2, start_rect.y + 10))
    
    def _draw_search_icon(self, screen, x, y, color=CHARCOAL):
        pygame.draw.circle(screen, color, (x + 20, y + 20), 18, 3)
        pygame.draw.line(screen, color, (x + 33, y + 33), (x + 48, y + 48), 4)
    
    def _draw_sparkles_icon(self, screen, x, y, color):
        size = 50
        self._draw_sparkle(screen, x + size * 0.4, y + size * 0.55, size * 0.45, color)
        self._draw_sparkle(screen, x + size * 0.75, y + size * 0.22, size * 0.25, color)
    
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
    
    def handle_touch(self, pos, state, keyboard_visible=False):
        x, y = pos

        if self.is_sleeping:
            self.wake()
            return 'woke_up'
        
        self.reset_activity()
        
        if self.timer_done:
            dismiss_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 15, 200, 40)
            if dismiss_rect.collidepoint(x, y):
                self.timer_done = False
                self.flash_on = False
                return 'timer_dismissed'
            return None
        
        if self.show_timer_modal:
            return self._handle_timer_modal_touch(x, y)
        
        if self.timer_active:
            pill_rect = pygame.Rect(WIDTH // 2 - 90, 20, 180, 50)
            cancel_x = pill_rect.x + pill_rect.width - 30
            cancel_y = pill_rect.y + 25
            if (x - cancel_x) ** 2 + (y - cancel_y) ** 2 <= 225:
                self.timer_active = False
                return 'timer_cancelled'
        
        # Clock box - same position as header
        clock_rect = pygame.Rect(WIDTH - 180, 25, 140, 65)
        if clock_rect.collidepoint(x, y):
            self.show_timer_modal = True
            self.timer_input = ""
            return 'show_timer'
        
        # Quick action cards (updated positions)
        card_width = (WIDTH - 100) // 2
        card_height = 160
        card_y = 110
        
        if 40 <= x <= 40 + card_width and card_y <= y <= card_y + card_height:
            return 'navigate_search'
        
        if 60 + card_width <= x <= 60 + card_width * 2 and card_y <= y <= card_y + card_height:
            return 'navigate_create'
        
        # Today's meals box (updated position)
        box_rect = pygame.Rect(40, 290, WIDTH - 80, 170)
        if box_rect.collidepoint(x, y):
            today = datetime.now().strftime("%A")
            
            has_meals = False
            if self.meal_plan_manager and self.meal_plan_manager.get_meal_count() > 0:
                day_data = self.meal_plan_manager.get_day(today)
                if day_data:
                    meals = day_data.get('meals', {})
                    for meal_type in ['Breakfast', 'Lunch', 'Dinner']:
                        if meals.get(meal_type):
                            has_meals = True
                            break
            
            if has_meals:
                slot_width = (box_rect.width - 80) // 3
                slot_height = 85
                slot_x = box_rect.x + 25
                slot_y = box_rect.y + 60
                
                for meal_type in ['Breakfast', 'Lunch', 'Dinner']:
                    slot_rect = pygame.Rect(slot_x, slot_y, slot_width, slot_height)
                    if slot_rect.collidepoint(x, y):
                        meal = self.meal_plan_manager.get_meal(today, meal_type)
                        if meal:
                            return f'home_meal_{today}_{meal_type}'
                    slot_x += slot_width + 15
            else:
                center_y = box_rect.y + box_rect.height // 2
                btn_rect = pygame.Rect(box_rect.x + 25, center_y + 10, 180, 40)
                if btn_rect.collidepoint(x, y):
                    return 'navigate_meal_prep'
        
        return None
    
    def _handle_timer_modal_touch(self, x, y):
        modal_width = 350
        modal_height = 260
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        close_x = modal_x + modal_width - 35
        close_y = modal_y + 35
        if (x - close_x) ** 2 + (y - close_y) ** 2 <= 256:
            self.show_timer_modal = False
            return 'close_timer_modal'
        
        quick_y = modal_y + 130
        quick_times = [1, 5, 10, 15, 30]
        btn_width = (modal_width - 70) // 5
        btn_x = modal_x + 25
        
        for mins in quick_times:
            btn_rect = pygame.Rect(btn_x, quick_y, btn_width - 5, 38)
            if btn_rect.collidepoint(x, y):
                self.timer_input = str(mins)
                return f'timer_quick_{mins}'
            btn_x += btn_width
        
        start_rect = pygame.Rect(modal_x + 25, modal_y + modal_height - 55, modal_width - 50, 42)
        if start_rect.collidepoint(x, y) and self.timer_input:
            try:
                mins = int(self.timer_input)
                if mins > 0:
                    self.timer_duration = mins * 60
                    self.timer_start_ticks = pygame.time.get_ticks()
                    self.timer_active = True
                    self.show_timer_modal = False
                    return 'timer_started'
            except ValueError:
                pass
        
        if not (modal_x <= x <= modal_x + modal_width and modal_y <= y <= modal_y + modal_height):
            self.show_timer_modal = False
            return 'close_timer_modal'
        
        return None
    
    def handle_keyboard_input(self, key):
        if not self.show_timer_modal:
            return None
        
        if key == 'BACKSPACE':
            self.timer_input = self.timer_input[:-1]
        elif key == 'GO':
            if self.timer_input:
                try:
                    mins = int(self.timer_input)
                    if mins > 0:
                        self.timer_duration = mins * 60
                        self.timer_start_ticks = pygame.time.get_ticks()
                        self.timer_active = True
                        self.show_timer_modal = False
                        return 'timer_started'
                except ValueError:
                    pass
        elif key.isdigit() and len(self.timer_input) < 3:
            self.timer_input += key
        
        return None