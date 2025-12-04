"""
ui/views/search_view.py

Description:
    * Search view rendering for AI Sous Chef

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui.constants import (
    WIDTH, HEIGHT, KEYBOARD_HEIGHT,
    BLUE_DARK, BLUE_MID, BLUE_LIGHT, CREAM, ACCENT, BLACK, GRAY
)


class SearchView:
    def __init__(self, fonts):
        self.font = fonts['regular']
        self.font_large = fonts['large']
        self.font_medium = fonts['medium']
        self.font_small = fonts['small']
        self.font_italic = fonts['italic']

    def draw(self, screen, state, keyboard_visible):
        content_height = HEIGHT - (KEYBOARD_HEIGHT if keyboard_visible else 0)

        self._draw_header(screen)
        self._draw_search_box(screen, state, keyboard_visible)
        self._draw_results(screen, state, content_height, keyboard_visible)

    def _draw_header(self, screen):
        pygame.draw.rect(screen, BLUE_DARK, (0, 0, WIDTH, 75))

        # Home button
        home_rect = pygame.Rect(20, 18, 90, 42)
        self._draw_rounded_rect(screen, BLUE_MID, home_rect, 6, 2, ACCENT)
        home_text = self.font_small.render("Home", True, CREAM)
        screen.blit(home_text, (home_rect.x + 15, home_rect.y + 8))

        # Title
        title = self.font_large.render("AI Sous Chef", True, CREAM)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 12))
        pygame.draw.rect(screen, ACCENT, (WIDTH // 2 - title.get_width() // 2, 70, title.get_width(), 3))

    def _draw_search_box(self, screen, state, keyboard_visible):
        search_y = 95
        search_rect = pygame.Rect(30, search_y, WIDTH - 330, 54)
        self._draw_rounded_rect(screen, CREAM, search_rect, 8)

        if state['search_text']:
            search_surface = self.font.render(state['search_text'][-40:], True, BLACK)
        else:
            search_surface = self.font_italic.render("What would you like to cook?", True, GRAY)
        screen.blit(search_surface, (45, search_y + 12))

        # Cursor
        if state['active_input'] == "search" and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = 45 + self.font.size(state['search_text'][-40:])[0] + 2
            pygame.draw.rect(screen, BLACK, (cursor_x, search_y + 12, 2, 30))

        # Generate button
        gen_rect = pygame.Rect(WIDTH - 290, search_y, 120, 54)
        self._draw_rounded_rect(screen, BLUE_MID, gen_rect, 8, 2, ACCENT)
        gen_text = self.font_small.render("Generate", True, CREAM)
        screen.blit(gen_text, (gen_rect.x + 15, gen_rect.y + 14))

        # Search button
        btn_rect = pygame.Rect(WIDTH - 155, search_y, 120, 54)
        self._draw_rounded_rect(screen, ACCENT, btn_rect, 8)
        btn_text = self.font.render("Search", True, BLUE_DARK)
        screen.blit(btn_text, (btn_rect.x + 18, btn_rect.y + 10))

        # Status
        status_surface = self.font_small.render(state['status'], True, GRAY)
        screen.blit(status_surface, (30, search_y + 58))

    def _draw_results(self, screen, state, content_height, keyboard_visible):
        results_y = 180
        max_results = 4 if keyboard_visible else 6

        for i, recipe in enumerate(state['results'][:max_results]):
            if results_y > content_height - 80:
                break

            card_rect = pygame.Rect(30, results_y, WIDTH - 60, 85)
            self._draw_rounded_rect(screen, BLUE_MID, card_rect, 10, 2, BLUE_LIGHT)

            # Number badge
            pygame.draw.circle(screen, ACCENT, (card_rect.x + 40, card_rect.y + 42), 22)
            num_text = self.font_small.render(str(i + 1), True, BLUE_DARK)
            screen.blit(num_text, (card_rect.x + 40 - num_text.get_width() // 2, card_rect.y + 30))

            # Recipe name
            name = recipe['name']
            max_name_width = card_rect.width - 100

            if self.font_medium.size(name)[0] > max_name_width:
                words = name.split()
                truncated = ""
                for word in words:
                    test = truncated + " " + word if truncated else word
                    if self.font_medium.size(test + "...")[0] <= max_name_width:
                        truncated = test
                    else:
                        break
                name = truncated + "..." if truncated else name[:25] + "..."

            name_surface = self.font_medium.render(name, True, CREAM)
            screen.blit(name_surface, (card_rect.x + 80, card_rect.y + 12))

            # Details
            cal = recipe.get('calories', 'N/A')
            details = f"{recipe.get('category', '')} • {cal} cal"
            details_surface = self.font_small.render(details, True, GRAY)
            screen.blit(details_surface, (card_rect.x + 80, card_rect.y + 52))

            results_y += 95

    def _draw_rounded_rect(self, surface, color, rect, radius, border=0, border_color=None):
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border > 0 and border_color:
            pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)

    def handle_touch(self, pos, state, keyboard_visible):
        """Returns action string or None."""
        x, y = pos

        # Home button
        if 20 <= x <= 110 and 18 <= y <= 60:
            return 'home'

        # Search box tap
        if 30 <= x <= WIDTH - 330 and 95 <= y <= 149:
            return 'focus_search'

        # Generate button
        if WIDTH - 290 <= x <= WIDTH - 170 and 95 <= y <= 149:
            return 'generate'

        # Search button
        if WIDTH - 155 <= x <= WIDTH - 35 and 95 <= y <= 149:
            return 'search'

        # Results
        results_y = 175
        for i in range(min(len(state['results']), 6)):
            if 30 <= x <= WIDTH - 30 and results_y <= y <= results_y + 85:
                return f'select_{i}'
            results_y += 95

        return None