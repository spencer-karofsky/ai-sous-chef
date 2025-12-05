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
        self.sleep_timeout = 30000 # 30 seconds

    def wake(self):
        """Wake from sleep."""
        self.is_sleeping = False
        self.last_activity_ticks = pygame.time.get_ticks()

    def reset_activity(self):
        """Reset the inactivity timer."""
        self.last_activity_ticks = pygame.time.get_ticks()

    def draw(self, screen, state):
        # Debug - remove after fixing
        elapsed = pygame.time.get_ticks() - self.last_activity_ticks
        if elapsed % 5000 < 50:  # Print every ~5 seconds
            print(f"[Home] Elapsed: {elapsed // 1000}s, Sleeping: {self.is_sleeping}, Timeout: {self.sleep_timeout // 1000}s")
        
        # Check for sleep
        if not self.is_sleeping and not self.timer_active and not self.timer_done and not self.show_timer_modal:
            if elapsed > self.sleep_timeout:
                print("[Home] Going to sleep!")
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
        
        self._draw_header(screen)
        self._draw_clock_box(screen)
        self._draw_quick_actions(screen)
        self._draw_todays_meals(screen)
        
        if self.timer_active:
            self._draw_timer_pill(screen)
        
        if self.timer_done:
            self._draw_timer_done(screen)
        
        if self.show_timer_modal:
            self._draw_timer_modal(screen)

    def _draw_sleep_screen(self, screen):
        """Draw minimal sleep screen with clock."""
        screen.fill((15, 15, 20))  # Very dark background
        
        now = datetime.now()
        time_str = now.strftime("%I:%M").lstrip("0")
        date_str = now.strftime("%A, %B %d")
        
        # Large centered clock
        time_text = self.fonts['title'].render(time_str, True, (80, 80, 90))
        time_x = (WIDTH - time_text.get_width()) // 2
        time_y = HEIGHT // 2 - 40
        screen.blit(time_text, (time_x, time_y))
        
        # Date below
        date_text = self.fonts['body'].render(date_str, True, (60, 60, 70))
        date_x = (WIDTH - date_text.get_width()) // 2
        screen.blit(date_text, (time_x + time_text.get_width() + 15, time_y + 20))
        
        # Subtle hint
        hint_text = self.fonts['caption'].render("Tap anywhere to wake", True, (40, 40, 50))
        hint_x = (WIDTH - hint_text.get_width()) // 2
        screen.blit(hint_text, (hint_x, HEIGHT - 60))
    
    def set_managers(self, meal_plan_manager=None, favorites_manager=None, saved_recipes_manager=None):
        self.meal_plan_manager = meal_plan_manager
        self.favorites_manager = favorites_manager
        self.saved_recipes_manager = saved_recipes_manager
    
    def draw(self, screen, state):
        # Flash red if timer done
        if self.timer_done:
            ticks = pygame.time.get_ticks()
            if ticks - self.last_flash_ticks > 500:
                self.flash_on = not self.flash_on
                self.last_flash_ticks = ticks
            if self.flash_on:
                screen.fill((255, 60, 60))
        
        self._draw_header(screen)
        self._draw_clock_box(screen)
        self._draw_quick_actions(screen)
        self._draw_todays_meals(screen)
        
        if self.timer_active:
            self._draw_timer_pill(screen)
        
        if self.timer_done:
            self._draw_timer_done(screen)
        
        if self.show_timer_modal:
            self._draw_timer_modal(screen)
    
    def _draw_header(self, screen):
        title = self.fonts['title'].render("AI Sous Chef", True, SOFT_BLACK)
        screen.blit(title, (40, 25))
        
        subtitle = self.fonts['body'].render("Find a recipe or create something new", True, DARK_GRAY)
        screen.blit(subtitle, (40, 75))
    
    def _draw_clock_box(self, screen):
        """Clock box in top right - tap for timer."""
        now = datetime.now()
        time_str = now.strftime("%I:%M").lstrip("0")
        ampm = now.strftime("%p")
        
        # Bigger box
        clock_rect = pygame.Rect(WIDTH - 180, 20, 140, 65)
        pygame.draw.rect(screen, LIGHT_GRAY, clock_rect, border_radius=12)
        
        # Time
        time_text = self.fonts['header'].render(time_str, True, SOFT_BLACK)
        screen.blit(time_text, (clock_rect.x + 18, clock_rect.y + 10))
        
        # AM/PM
        ampm_text = self.fonts['small'].render(ampm, True, DARK_GRAY)
        screen.blit(ampm_text, (clock_rect.x + 18 + time_text.get_width() + 5, clock_rect.y + 18))
        
        # Date below
        date_str = now.strftime("%a, %b %d")
        date_text = self.fonts['small'].render(date_str, True, DARK_GRAY)
        screen.blit(date_text, (clock_rect.x + 18, clock_rect.y + 40))
    
    def _draw_quick_actions(self, screen):
        y = 130
        card_width = (WIDTH - 100) // 2
        card_height = 180
        
        # Search card
        search_rect = pygame.Rect(40, y, card_width, card_height)
        pygame.draw.rect(screen, LIGHT_GRAY, search_rect, border_radius=16)
        
        search_title = self.fonts['header'].render("Search", True, SOFT_BLACK)
        screen.blit(search_title, (search_rect.x + 30, search_rect.y + 30))
        
        search_desc = self.fonts['small'].render("Find recipes from", True, DARK_GRAY)
        screen.blit(search_desc, (search_rect.x + 30, search_rect.y + 75))
        search_desc2 = self.fonts['small'].render("our collection", True, DARK_GRAY)
        screen.blit(search_desc2, (search_rect.x + 30, search_rect.y + 100))
        
        self._draw_search_icon(screen, search_rect.x + card_width - 80, search_rect.y + card_height - 70)
        
        # Create card
        create_rect = pygame.Rect(60 + card_width, y, card_width, card_height)
        pygame.draw.rect(screen, SOFT_BLACK, create_rect, border_radius=16)
        
        create_title = self.fonts['header'].render("Create", True, WHITE)
        screen.blit(create_title, (create_rect.x + 30, create_rect.y + 30))
        
        create_desc = self.fonts['small'].render("Generate a custom", True, MID_GRAY)
        screen.blit(create_desc, (create_rect.x + 30, create_rect.y + 75))
        create_desc2 = self.fonts['small'].render("recipe with AI", True, MID_GRAY)
        screen.blit(create_desc2, (create_rect.x + 30, create_rect.y + 100))
        
        self._draw_sparkles_icon(screen, create_rect.x + card_width - 90, create_rect.y + card_height - 80, WHITE)
    
    def _draw_todays_meals(self, screen):
        """Today's meals as a single box."""
        y = 330
        
        # Section box
        box_rect = pygame.Rect(40, y, WIDTH - 80, 130)
        pygame.draw.rect(screen, LIGHT_GRAY, box_rect, border_radius=16)
        
        # Title
        today = datetime.now().strftime("%A")
        title = self.fonts['body'].render("Today's Meals", True, SOFT_BLACK)
        screen.blit(title, (box_rect.x + 25, box_rect.y + 18))
        
        day_text = self.fonts['caption'].render(today, True, DARK_GRAY)
        screen.blit(day_text, (box_rect.x + 25 + title.get_width() + 10, box_rect.y + 22))
        
        # Debug - remove after fixing
        if self.meal_plan_manager:
            print(f"[Home] Today: {today}")
            print(f"[Home] Meal count: {self.meal_plan_manager.get_meal_count()}")
            day_data = self.meal_plan_manager.get_day(today)
            print(f"[Home] Day data keys: {day_data.keys() if day_data else None}")
            if day_data:
                meals = day_data.get('meals', {})
                print(f"[Home] Meals: {list(meals.keys())} -> {[bool(m) for m in meals.values()]}")
        
        # Check if we have meals for today
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
            slot_width = (box_rect.width - 70) // 3
            slot_x = box_rect.x + 25
            slot_y = box_rect.y + 55
            
            for meal_type in ['Breakfast', 'Lunch', 'Dinner']:
                meal = meals.get(meal_type)
                self._draw_meal_slot(screen, slot_x, slot_y, slot_width - 10, 55, meal_type, meal)
                slot_x += slot_width
        else:
            self._draw_no_meals(screen, box_rect)
    
    def _draw_meal_slot(self, screen, x, y, width, height, meal_type, meal):
        slot_rect = pygame.Rect(x, y, width, height)
        
        if meal:
            is_hydrated = meal.get('hydrated', False)
            
            if is_hydrated:
                pygame.draw.rect(screen, SOFT_BLACK, slot_rect, border_radius=10)
                text_color = WHITE
                sub_color = MID_GRAY
            else:
                pygame.draw.rect(screen, WHITE, slot_rect, border_radius=10)
                text_color = SOFT_BLACK
                sub_color = DARK_GRAY
            
            # Meal type
            type_text = self.fonts['caption'].render(meal_type, True, sub_color)
            screen.blit(type_text, (x + 10, y + 8))
            
            # Recipe name
            name = meal.get('name', 'Recipe')
            max_width = width - 20
            if self.fonts['small'].size(name)[0] > max_width:
                while self.fonts['small'].size(name + '...')[0] > max_width and len(name) > 3:
                    name = name[:-1]
                name += '...'
            
            name_text = self.fonts['small'].render(name, True, text_color)
            screen.blit(name_text, (x + 10, y + 28))
        else:
            pygame.draw.rect(screen, WHITE, slot_rect, border_radius=10)
            
            type_text = self.fonts['caption'].render(meal_type, True, DARK_GRAY)
            screen.blit(type_text, (x + 10, y + 8))
            
            empty_text = self.fonts['small'].render("—", True, MID_GRAY)
            screen.blit(empty_text, (x + 10, y + 28))
    
    def _draw_no_meals(self, screen, box_rect):
        """Draw prompt to plan meals - tappable."""
        msg = self.fonts['body'].render("No meals planned", True, DARK_GRAY)
        screen.blit(msg, (box_rect.x + 25, box_rect.y + 55))
        
        # Tappable button
        btn_rect = pygame.Rect(box_rect.x + 25, box_rect.y + 85, 180, 35)
        pygame.draw.rect(screen, SOFT_BLACK, btn_rect, border_radius=8)
        btn_text = self.fonts['small'].render("Plan Your Week", True, WHITE)
        screen.blit(btn_text, (btn_rect.x + 15, btn_rect.y + 8))
    
    def _draw_timer_pill(self, screen):
        """Active timer display with cancel button."""
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
        
        # Pill at top center
        pill_rect = pygame.Rect(WIDTH // 2 - 90, 20, 180, 50)
        pygame.draw.rect(screen, (80, 180, 100), pill_rect, border_radius=25)
        
        # Timer text - no emoji
        timer_text = self.fonts['header'].render(time_str, True, WHITE)
        screen.blit(timer_text, (pill_rect.x + 25, pill_rect.y + 10))
        
        # Cancel X button
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
        
        # Title
        title = self.fonts['header'].render("Kitchen Timer", True, SOFT_BLACK)
        screen.blit(title, (modal_x + 25, modal_y + 20))
        
        # Close button
        close_x = modal_x + modal_width - 35
        close_y = modal_y + 35
        pygame.draw.circle(screen, LIGHT_GRAY, (close_x, close_y), 16)
        pygame.draw.line(screen, CHARCOAL, (close_x - 5, close_y - 5), (close_x + 5, close_y + 5), 2)
        pygame.draw.line(screen, CHARCOAL, (close_x + 5, close_y - 5), (close_x - 5, close_y + 5), 2)
        
        # Input display
        input_rect = pygame.Rect(modal_x + 25, modal_y + 65, modal_width - 50, 50)
        pygame.draw.rect(screen, LIGHT_GRAY, input_rect, border_radius=10)
        
        display = self.timer_input if self.timer_input else "0"
        input_text = self.fonts['header'].render(f"{display} min", True, SOFT_BLACK if self.timer_input else MID_GRAY)
        screen.blit(input_text, (input_rect.x + 20, input_rect.y + 10))
        
        # Quick buttons
        quick_y = modal_y + 130
        quick_times = [1, 5, 10, 15, 30]
        btn_width = (modal_width - 70) // 5
        btn_x = modal_x + 25
        
        for mins in quick_times:
            btn_rect = pygame.Rect(btn_x, quick_y, btn_width - 5, 38)
            pygame.draw.rect(screen, LIGHT_GRAY, btn_rect, border_radius=8)
            btn_text = self.fonts['body'].render(str(mins), True, SOFT_BLACK)
            screen.blit(btn_text, (btn_rect.x + (btn_width - 5 - btn_text.get_width()) // 2, btn_rect.y + 8))
            btn_x += btn_width
        
        # Start button
        start_rect = pygame.Rect(modal_x + 25, modal_y + modal_height - 55, modal_width - 50, 42)
        btn_color = (80, 180, 100) if self.timer_input else MID_GRAY
        pygame.draw.rect(screen, btn_color, start_rect, border_radius=10)
        start_text = self.fonts['body'].render("Start Timer", True, WHITE)
        screen.blit(start_text, (start_rect.x + (modal_width - 50 - start_text.get_width()) // 2, start_rect.y + 10))
    
    def _draw_search_icon(self, screen, x, y):
        pygame.draw.circle(screen, CHARCOAL, (x + 20, y + 20), 18, 3)
        pygame.draw.line(screen, CHARCOAL, (x + 33, y + 33), (x + 48, y + 48), 4)
    
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
        
        # Reset activity timer on any touch
        self.reset_activity()
        
        # Timer done dismiss
        if self.timer_done:
            dismiss_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 15, 200, 40)
            if dismiss_rect.collidepoint(x, y):
                self.timer_done = False
                self.flash_on = False
                return 'timer_dismissed'
            return None
        
        # Timer modal
        if self.show_timer_modal:
            return self._handle_timer_modal_touch(x, y)
        
        # Active timer cancel button
        if self.timer_active:
            pill_rect = pygame.Rect(WIDTH // 2 - 90, 20, 180, 50)
            cancel_x = pill_rect.x + pill_rect.width - 30
            cancel_y = pill_rect.y + 25
            if (x - cancel_x) ** 2 + (y - cancel_y) ** 2 <= 225:
                self.timer_active = False
                return 'timer_cancelled'
        
        # Clock box tap - easter egg
        clock_rect = pygame.Rect(WIDTH - 180, 20, 140, 65)
        if clock_rect.collidepoint(x, y):
            self.show_timer_modal = True
            self.timer_input = ""
            return 'show_timer'
        
        # Quick action cards
        card_width = (WIDTH - 100) // 2
        card_height = 180
        card_y = 130
        
        if 40 <= x <= 40 + card_width and card_y <= y <= card_y + card_height:
            return 'navigate_search'
        
        if 60 + card_width <= x <= 60 + card_width * 2 and card_y <= y <= card_y + card_height:
            return 'navigate_create'
        
        # Today's meals box
        box_rect = pygame.Rect(40, 330, WIDTH - 80, 130)
        if box_rect.collidepoint(x, y):
            today = datetime.now().strftime("%A")
            
            # Check if we have meals
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
                # Check which meal slot was tapped
                slot_width = (box_rect.width - 70) // 3
                slot_x = box_rect.x + 25
                slot_y = box_rect.y + 55
                
                for meal_type in ['Breakfast', 'Lunch', 'Dinner']:
                    slot_rect = pygame.Rect(slot_x, slot_y, slot_width - 10, 55)
                    if slot_rect.collidepoint(x, y):
                        meal = self.meal_plan_manager.get_meal(today, meal_type)
                        if meal:
                            return f'home_meal_{today}_{meal_type}'
                    slot_x += slot_width
            else:
                # "Plan Your Week" button
                btn_rect = pygame.Rect(box_rect.x + 25, box_rect.y + 85, 180, 35)
                if btn_rect.collidepoint(x, y):
                    return 'navigate_meal_prep'
        
        return None
    
    def _handle_timer_modal_touch(self, x, y):
        modal_width = 350
        modal_height = 260
        modal_x = (WIDTH - modal_width) // 2
        modal_y = (HEIGHT - modal_height) // 2
        
        # Close button
        close_x = modal_x + modal_width - 35
        close_y = modal_y + 35
        if (x - close_x) ** 2 + (y - close_y) ** 2 <= 256:
            self.show_timer_modal = False
            return 'close_timer_modal'
        
        # Quick buttons
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
        
        # Start button
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
        
        # Outside modal
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