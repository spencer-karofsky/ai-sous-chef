"""
ui/views/recipe_view.py

Description:
    * Recipe view rendering for AI Sous Chef

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui.constants import (
    WIDTH, HEIGHT, KEYBOARD_HEIGHT,
    BLUE_DARK, BLUE_MID, CREAM, ACCENT, BLACK, GRAY
)


class RecipeView:
    def __init__(self, fonts):
        self.font = fonts['regular']
        self.font_medium = fonts['medium']
        self.font_small = fonts['small']
        self.font_italic = fonts['italic']

    def draw(self, screen, state, keyboard_visible):
        recipe = state['recipe']
        if not recipe:
            return

        content_height = HEIGHT - (KEYBOARD_HEIGHT if keyboard_visible else 0)

        self._draw_header(screen, recipe)
        max_scroll = self._draw_content(screen, recipe, state['scroll_offset'], content_height)
        self._draw_modify_bar(screen, state, content_height, keyboard_visible)

        return max_scroll

    def _draw_header(self, screen, recipe):
        pygame.draw.rect(screen, BLUE_DARK, (0, 0, WIDTH, 70))

        # Back button
        back_rect = pygame.Rect(15, 15, 90, 45)
        self._draw_rounded_rect(screen, BLUE_MID, back_rect, 6, 2, ACCENT)
        back_text = self.font_small.render("< Back", True, CREAM)
        screen.blit(back_text, (back_rect.x + 12, back_rect.y + 10))

        # Done button
        done_rect = pygame.Rect(WIDTH - 105, 15, 90, 45)
        self._draw_rounded_rect(screen, ACCENT, done_rect, 6)
        done_text = self.font_small.render("Done", True, BLUE_DARK)
        screen.blit(done_text, (done_rect.x + 18, done_rect.y + 10))

        # Title
        max_title_width = WIDTH - 240
        title_text = recipe.get('name', 'Recipe')
        title = self.font_medium.render(title_text, True, CREAM)

        while title.get_width() > max_title_width and len(title_text) > 10:
            title_text = title_text[:-4] + "..."
            title = self.font_medium.render(title_text, True, CREAM)

        title_x = 120 + (WIDTH - 240 - title.get_width()) // 2
        screen.blit(title, (title_x, 18))

    def _draw_content(self, screen, recipe, scroll_offset, content_height):
        content_surface = pygame.Surface((WIDTH, 2000), pygame.SRCALPHA)
        y = 10

        # Info bar
        info_rect = pygame.Rect(20, y, WIDTH - 40, 45)
        self._draw_rounded_rect(content_surface, BLUE_MID, info_rect, 8)

        info_parts = [
            f"Time: {recipe.get('total_time', 'N/A')}",
            f"Serves: {recipe.get('servings', 'N/A')}",
        ]
        if recipe.get('nutrition'):
            info_parts.append(f"Cal: {recipe['nutrition'].get('calories', 'N/A')}")

        info_text = " | ".join(info_parts)
        info_surface = self.font_small.render(info_text, True, CREAM)
        content_surface.blit(info_surface, (35, y + 12))
        y += 60

        # Two column layout
        col_width = (WIDTH - 60) // 2

        # Ingredients
        ing_label = self.font_medium.render("Ingredients", True, ACCENT)
        content_surface.blit(ing_label, (25, y))
        pygame.draw.rect(content_surface, ACCENT, (25, y + 42, 150, 3))

        ing_y = y + 55
        for ing in recipe.get('ingredients', [])[:15]:
            if isinstance(ing, dict):
                qty = ing.get('quantity', '')
                unit = ing.get('unit', '')
                item = ing.get('item', '')
                ing_text = f"• {qty} {unit} {item}".strip()
            else:
                ing_text = f"• {ing}"

            ing_lines = self._wrap_text(ing_text, col_width - 40)
            for j, line in enumerate(ing_lines):
                if j > 0:
                    line = "  " + line
                ing_surface = self.font_small.render(line, True, CREAM)
                content_surface.blit(ing_surface, (30, ing_y))
                ing_y += 32

        # Instructions
        inst_label = self.font_medium.render("Instructions", True, ACCENT)
        content_surface.blit(inst_label, (col_width + 45, y))
        pygame.draw.rect(content_surface, ACCENT, (col_width + 45, y + 42, 165, 3))

        inst_y = y + 55
        for i, step in enumerate(recipe.get('instructions', [])[:10], 1):
            step_lines = self._wrap_text(f"{i}. {step}", col_width - 50)
            for j, line in enumerate(step_lines):
                if j > 0:
                    line = "   " + line
                step_surface = self.font_small.render(line, True, CREAM)
                content_surface.blit(step_surface, (col_width + 45, inst_y))
                inst_y += 32
            inst_y += 5

        max_scroll = max(ing_y, inst_y) - 200

        # Blit scrolled content
        visible_height = content_height - 145
        screen.blit(content_surface, (0, 75), (0, scroll_offset, WIDTH, visible_height))

        return max_scroll

    def _draw_modify_bar(self, screen, state, content_height, keyboard_visible):
        mod_y = content_height - 70
        pygame.draw.rect(screen, BLUE_DARK, (0, mod_y, WIDTH, 70))
        pygame.draw.rect(screen, ACCENT, (0, mod_y, WIDTH, 3))

        # Modify input
        mod_rect = pygame.Rect(20, mod_y + 12, WIDTH - 160, 46)
        self._draw_rounded_rect(screen, CREAM, mod_rect, 6)

        if state['modify_text']:
            mod_surface = self.font_small.render(state['modify_text'][-50:], True, BLACK)
        else:
            mod_surface = self.font_italic.render("Tap to modify recipe...", True, GRAY)
        screen.blit(mod_surface, (32, mod_y + 22))

        # Cursor
        if state['active_input'] == "modify" and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = 32 + self.font_small.size(state['modify_text'][-50:])[0] + 2
            pygame.draw.rect(screen, BLACK, (cursor_x, mod_y + 18, 2, 28))

        # Modify button
        mod_btn = pygame.Rect(WIDTH - 130, mod_y + 12, 110, 46)
        self._draw_rounded_rect(screen, ACCENT, mod_btn, 6)
        mod_btn_text = self.font_small.render("Modify", True, BLUE_DARK)
        screen.blit(mod_btn_text, (mod_btn.x + 20, mod_btn.y + 11))

        # Status
        if state['modify_status']:
            status_surface = self.font_small.render(state['modify_status'], True, GRAY)
            screen.blit(status_surface, (15, mod_y - 28))

    def _wrap_text(self, text, max_width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = current + " " + word if current else word
            if self.font_small.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines if lines else [text]

    def _draw_rounded_rect(self, surface, color, rect, radius, border=0, border_color=None):
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border > 0 and border_color:
            pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)

    def handle_touch(self, pos, state, keyboard_visible):
        """Returns action string or None."""
        x, y = pos
        content_height = HEIGHT - (KEYBOARD_HEIGHT if keyboard_visible else 0)

        # Back button
        if 15 <= x <= 105 and 15 <= y <= 60:
            return 'back'

        # Done button
        if WIDTH - 105 <= x <= WIDTH - 15 and 15 <= y <= 60:
            return 'done'

        # Modify input tap
        mod_y = content_height - 70
        if 20 <= x <= WIDTH - 160 and mod_y + 12 <= y <= mod_y + 58:
            return 'focus_modify'

        # Modify button
        if WIDTH - 130 <= x <= WIDTH - 20 and mod_y + 12 <= y <= mod_y + 58:
            return 'modify'

        return None