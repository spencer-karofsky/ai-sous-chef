"""
ui_new/views/recipe_view.py

Description:
    * Recipe detail view - elegant cookbook-quality design

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
import math
from ui_new.constants import *

# Warm background matching app palette
WARM_BG = (255, 251, 245)
WARM_BG_BOTTOM = (252, 245, 235)


class RecipeView:
    def __init__(self, fonts):
        self.fonts = fonts
        self.favorites_manager = None
        self.current_s3_key = None
        self.current_source = 'search'
        self.gradient_surface = None
    
    def set_manager(self, manager):
        self.favorites_manager = manager
    
    def _create_gradient(self, width, height):
        """Create warm gradient background."""
        if self.gradient_surface and self.gradient_surface.get_size() == (width, height):
            return self.gradient_surface
        
        self.gradient_surface = pygame.Surface((width, height))
        for y in range(height):
            t = y / height
            r = int(WARM_BG[0] + (WARM_BG_BOTTOM[0] - WARM_BG[0]) * t)
            g = int(WARM_BG[1] + (WARM_BG_BOTTOM[1] - WARM_BG[1]) * t)
            b = int(WARM_BG[2] + (WARM_BG_BOTTOM[2] - WARM_BG[2]) * t)
            pygame.draw.line(self.gradient_surface, (r, g, b), (0, y), (width, y))
        
        return self.gradient_surface
    
    def draw(self, screen, state, keyboard_visible):
        recipe = state.get('recipe')
        if not recipe:
            return 0
        
        # Draw warm gradient background
        screen.blit(self._create_gradient(WIDTH, HEIGHT), (0, 0))
        
        content_bottom = HEIGHT - NAV_HEIGHT
        if keyboard_visible:
            content_bottom = HEIGHT - KEYBOARD_HEIGHT
        
        self._draw_header(screen, recipe)
        max_scroll = self._draw_content(screen, recipe, state['scroll_offset'], content_bottom)
        self._draw_assistant_bar(screen, state, content_bottom)
        
        return max_scroll
    
    def _draw_header(self, screen, recipe):
        """Minimal header with back, title, and favorite."""
        # Back button - sage light with teal chevron
        back_rect = pygame.Rect(30, 22, 85, 36)
        pygame.draw.rect(screen, SAGE_LIGHT, back_rect, border_radius=18)
        pygame.draw.rect(screen, SAGE, back_rect, border_radius=18, width=1)
        
        # Teal chevron
        ax = back_rect.x + 20
        ay = back_rect.y + 18
        pygame.draw.line(screen, TEAL, (ax + 6, ay - 5), (ax, ay), 2)
        pygame.draw.line(screen, TEAL, (ax, ay), (ax + 6, ay + 5), 2)
        
        back_text = self.fonts['small'].render("Back", True, SOFT_BLACK)
        screen.blit(back_text, (ax + 14, ay - 8))
        
        # Heart button
        heart_rect = pygame.Rect(WIDTH - 58, 22, 36, 36)
        pygame.draw.rect(screen, SAGE_LIGHT, heart_rect, border_radius=18)
        pygame.draw.rect(screen, SAGE, heart_rect, border_radius=18, width=1)
        
        is_favorite = False
        if self.favorites_manager:
            is_favorite = self.favorites_manager.is_favorite(recipe.get('name', ''))
        self._draw_heart(screen, heart_rect.x + 18, heart_rect.y + 18, is_favorite)
        
        # Recipe title - centered
        title = recipe.get('name', 'Recipe')
        max_width = WIDTH - 240
        while self.fonts['header'].size(title)[0] > max_width and len(title) > 15:
            title = title[:-4] + "..."
        
        title_text = self.fonts['header'].render(title, True, SOFT_BLACK)
        title_x = (WIDTH - title_text.get_width()) // 2
        screen.blit(title_text, (title_x, 24))
    
    def _draw_heart(self, screen, cx, cy, filled):
        """Draw heart icon."""
        size = 10
        scale = size / 15
        points = []
        for i in range(50):
            t = i / 50 * 2 * math.pi
            hx = 16 * (math.sin(t) ** 3)
            hy = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
            points.append((cx + int(hx * scale), cy - int(hy * scale)))
        
        if len(points) > 2:
            if filled:
                pygame.draw.polygon(screen, (220, 80, 80), points)
            else:
                pygame.draw.polygon(screen, SAGE, points, 2)
    
    def _draw_content(self, screen, recipe, scroll_offset, content_bottom):
        """Draw recipe content with elegant cookbook styling."""
        content_height = 1800
        content_surface = pygame.Surface((WIDTH, content_height), pygame.SRCALPHA)
        
        # Draw gradient on content surface
        for y in range(content_height):
            t = min(y / content_height, 1.0)
            r = int(WARM_BG[0] + (WARM_BG_BOTTOM[0] - WARM_BG[0]) * t)
            g = int(WARM_BG[1] + (WARM_BG_BOTTOM[1] - WARM_BG[1]) * t)
            b = int(WARM_BG[2] + (WARM_BG_BOTTOM[2] - WARM_BG[2]) * t)
            pygame.draw.line(content_surface, (r, g, b), (0, y), (WIDTH, y))
        
        y = 15
        
        # Metadata pill banner - centered, elegant
        y = self._draw_metadata_banner(content_surface, recipe, y)
        
        y += 30
        
        # Two-column layout with vertical divider
        left_margin = 50
        right_margin = 50
        divider_x = WIDTH // 2
        col_width = (WIDTH - left_margin - right_margin - 40) // 2
        
        # Draw soft vertical divider
        divider_top = y
        divider_bottom = y + 800  # Will extend as needed
        pygame.draw.line(content_surface, SAGE, (divider_x, divider_top), (divider_x, divider_bottom), 1)
        
        # Ingredients column (left)
        ing_y = self._draw_ingredients(content_surface, recipe, left_margin, y, col_width)
        
        # Instructions column (right)
        inst_x = divider_x + 25
        inst_y = self._draw_instructions(content_surface, recipe, inst_x, y, col_width)
        
        # Calculate scroll
        max_content = max(ing_y, inst_y) + 100
        visible_height = content_bottom - 80
        max_scroll = max(0, max_content - visible_height)
        
        screen.blit(content_surface, (0, 70), (0, scroll_offset, WIDTH, visible_height))
        
        return max_scroll
    
    def _draw_metadata_banner(self, surface, recipe, y):
        """Draw centered metadata in elegant pill banner."""
        # Collect metadata items
        items = []
        if recipe.get('total_time'):
            items.append(('time', recipe['total_time']))
        if recipe.get('servings'):
            items.append(('servings', f"Serves {recipe['servings']}"))
        if recipe.get('nutrition', {}).get('calories'):
            items.append(('cal', f"{recipe['nutrition']['calories']} cal"))
        
        if not items:
            return y
        
        # Calculate total width for centering
        item_widths = []
        padding = 24
        spacing = 20
        
        for _, text in items:
            w = self.fonts['small'].size(text)[0] + padding * 2
            item_widths.append(w)
        
        total_width = sum(item_widths) + spacing * (len(items) - 1)
        start_x = (WIDTH - total_width) // 2
        
        # Draw each pill
        pill_x = start_x
        pill_height = 38
        
        for i, (icon_type, text) in enumerate(items):
            pill_width = item_widths[i]
            pill_rect = pygame.Rect(pill_x, y, pill_width, pill_height)
            
            # Sage light fill with sage border
            pygame.draw.rect(surface, SAGE_LIGHT, pill_rect, border_radius=19)
            pygame.draw.rect(surface, SAGE, pill_rect, border_radius=19, width=1)
            
            # Text centered in pill
            text_surf = self.fonts['small'].render(text, True, SOFT_BLACK)
            text_x = pill_x + (pill_width - text_surf.get_width()) // 2
            text_y = y + (pill_height - text_surf.get_height()) // 2
            surface.blit(text_surf, (text_x, text_y))
            
            pill_x += pill_width + spacing
        
        return y + pill_height + 10
    
    def _draw_ingredients(self, surface, recipe, x, y, width):
        """Draw ingredients with sage bullets and clean hierarchy."""
        # Section header
        header = self.fonts['body'].render("Ingredients", True, SOFT_BLACK)
        surface.blit(header, (x, y))
        
        # Subtle underline accent in sage
        line_width = header.get_width()
        pygame.draw.rect(surface, SAGE, (x, y + 32, line_width, 2), border_radius=1)
        
        y += 55
        
        ingredients = recipe.get('ingredients', [])
        
        for ing in ingredients[:18]:
            if isinstance(ing, dict):
                qty = ing.get('quantity', '')
                unit = ing.get('unit', '')
                item = ing.get('item', '')
                ing_text = f"{qty} {unit} {item}".strip()
            else:
                ing_text = str(ing)
            
            # Wrap text
            lines = self._wrap_text(ing_text, width - 30, 'small')
            
            for j, line in enumerate(lines):
                if j == 0:
                    # Sage bullet for first line
                    bullet_y = y + 8
                    pygame.draw.circle(surface, SAGE, (x + 6, bullet_y), 4)
                    text = self.fonts['small'].render(line, True, SOFT_BLACK)
                    surface.blit(text, (x + 22, y))
                else:
                    # Continuation indented
                    text = self.fonts['small'].render(line, True, SOFT_BLACK)
                    surface.blit(text, (x + 22, y))
                y += 28
            
            y += 8  # Extra spacing between items
        
        return y
    
    def _draw_instructions(self, surface, recipe, x, y, width):
        """Draw instructions with numbered circles and clear hierarchy."""
        # Section header
        header = self.fonts['body'].render("Instructions", True, SOFT_BLACK)
        surface.blit(header, (x, y))
        
        # Subtle underline accent in sage
        line_width = header.get_width()
        pygame.draw.rect(surface, SAGE, (x, y + 32, line_width, 2), border_radius=1)
        
        y += 55
        
        instructions = recipe.get('instructions', [])
        
        for i, step in enumerate(instructions[:15], 1):
            # Strip leading number if present (e.g., "1.", "1)", "1 -", "1:")
            step_text = step.strip()
            if step_text and step_text[0].isdigit():
                # Remove leading digits and common separators
                j = 0
                while j < len(step_text) and step_text[j].isdigit():
                    j += 1
                # Skip past separator (., ), :, -)
                while j < len(step_text) and step_text[j] in '.):- ':
                    j += 1
                step_text = step_text[j:].strip()
            
            # Numbered circle
            circle_x = x + 14
            circle_y = y + 12
            
            # Teal circle with white number
            pygame.draw.circle(surface, TEAL, (circle_x, circle_y), 14)
            num_text = self.fonts['small'].render(str(i), True, WHITE)
            num_x = circle_x - num_text.get_width() // 2
            num_y = circle_y - num_text.get_height() // 2
            surface.blit(num_text, (num_x, num_y))
            
            # Step text with wrapping
            text_x = x + 40
            lines = self._wrap_text(step_text, width - 50, 'small')
            
            step_y = y
            for line in lines:
                text = self.fonts['small'].render(line, True, SOFT_BLACK)
                surface.blit(text, (text_x, step_y))
                step_y += 28
            
            y = step_y + 18  # Generous spacing between steps
        
        return y
    
    def _draw_assistant_bar(self, screen, state, content_bottom):
        """Draw friendly assistant bubble for recipe modifications."""
        bar_height = 75
        bar_y = content_bottom - bar_height
        
        # Subtle top border
        pygame.draw.line(screen, SAGE, (0, bar_y), (WIDTH, bar_y), 1)
        
        # Assistant bubble container
        bubble_margin = 30
        bubble_rect = pygame.Rect(bubble_margin, bar_y + 12, WIDTH - bubble_margin * 2, 52)
        
        # White fill with sage border - friendly rounded shape
        pygame.draw.rect(screen, WHITE, bubble_rect, border_radius=26)
        pygame.draw.rect(screen, SAGE, bubble_rect, border_radius=26, width=1)
        
        # Sparkle/AI icon on left
        icon_x = bubble_rect.x + 22
        icon_y = bubble_rect.y + 26
        self._draw_sparkle_icon(screen, icon_x, icon_y, TEAL)
        
        # Input text or placeholder
        text_x = bubble_rect.x + 50
        text_y = bubble_rect.y + 16
        
        if state.get('modify_text'):
            display_text = state['modify_text']
            if len(display_text) > 35:
                display_text = display_text[-35:]
            text = self.fonts['body'].render(display_text, True, SOFT_BLACK)
        else:
            text = self.fonts['body'].render("Ask me to modify this recipe...", True, DARK_GRAY)
        
        screen.blit(text, (text_x, text_y))
        
        # Blinking cursor when focused
        if state.get('active_input') == 'modify' and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = text_x + self.fonts['body'].size(state.get('modify_text', '')[-35:])[0] + 2
            pygame.draw.rect(screen, SOFT_BLACK, (cursor_x, text_y - 2, 2, 24))
        
        # Send button - teal circle
        send_size = 40
        send_x = bubble_rect.x + bubble_rect.width - send_size - 8
        send_y = bubble_rect.y + (bubble_rect.height - send_size) // 2
        
        has_text = bool(state.get('modify_text'))
        btn_color = TEAL if has_text else SAGE_LIGHT
        
        pygame.draw.circle(screen, btn_color, (send_x + send_size // 2, send_y + send_size // 2), send_size // 2)
        
        # Arrow icon
        arrow_color = WHITE if has_text else DARK_GRAY
        ax = send_x + send_size // 2
        ay = send_y + send_size // 2
        pygame.draw.line(screen, arrow_color, (ax - 6, ay), (ax + 4, ay), 2)
        pygame.draw.line(screen, arrow_color, (ax, ay - 5), (ax + 4, ay), 2)
        pygame.draw.line(screen, arrow_color, (ax, ay + 5), (ax + 4, ay), 2)
        
        # Status text if any
        if state.get('modify_status'):
            status = self.fonts['caption'].render(state['modify_status'], True, DARK_GRAY)
            screen.blit(status, (bubble_margin, bar_y - 20))
    
    def _draw_sparkle_icon(self, screen, cx, cy, color):
        """Draw AI sparkle icon with small companion sparkle."""
        # Main sparkle
        size = 8
        points = [
            (cx, cy - size),
            (cx + size * 0.25, cy - size * 0.25),
            (cx + size, cy),
            (cx + size * 0.25, cy + size * 0.25),
            (cx, cy + size),
            (cx - size * 0.25, cy + size * 0.25),
            (cx - size, cy),
            (cx - size * 0.25, cy - size * 0.25),
        ]
        points = [(int(px), int(py)) for px, py in points]
        pygame.draw.polygon(screen, color, points)
        
        # Small companion sparkle (top right)
        small_cx = cx + 10
        small_cy = cy - 8
        small_size = 4
        small_points = [
            (small_cx, small_cy - small_size),
            (small_cx + small_size * 0.25, small_cy - small_size * 0.25),
            (small_cx + small_size, small_cy),
            (small_cx + small_size * 0.25, small_cy + small_size * 0.25),
            (small_cx, small_cy + small_size),
            (small_cx - small_size * 0.25, small_cy + small_size * 0.25),
            (small_cx - small_size, small_cy),
            (small_cx - small_size * 0.25, small_cy - small_size * 0.25),
        ]
        small_points = [(int(px), int(py)) for px, py in small_points]
        pygame.draw.polygon(screen, color, small_points)
    
    def _wrap_text(self, text, max_width, font_key='small'):
        """Wrap text to fit within max_width."""
        font = self.fonts[font_key]
        words = text.split()
        lines = []
        current = ""
        
        for word in words:
            test = current + " " + word if current else word
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        
        if current:
            lines.append(current)
        
        return lines if lines else [text]
    
    def handle_touch(self, pos, state, keyboard_visible):
        x, y = pos
        
        content_bottom = HEIGHT - NAV_HEIGHT
        if keyboard_visible:
            content_bottom = HEIGHT - KEYBOARD_HEIGHT
        
        # Back button
        if 30 <= x <= 115 and 22 <= y <= 58:
            return 'back'
        
        # Heart button
        if WIDTH - 58 <= x <= WIDTH - 22 and 22 <= y <= 58:
            return 'toggle_favorite'
        
        # Assistant bar
        bar_y = content_bottom - 75
        bubble_margin = 30
        bubble_rect = pygame.Rect(bubble_margin, bar_y + 12, WIDTH - bubble_margin * 2, 52)
        
        # Send button (circle on right side of bubble)
        send_size = 40
        send_x = bubble_rect.x + bubble_rect.width - send_size - 8
        send_y = bubble_rect.y + (bubble_rect.height - send_size) // 2
        send_center = (send_x + send_size // 2, send_y + send_size // 2)
        
        if (x - send_center[0]) ** 2 + (y - send_center[1]) ** 2 <= (send_size // 2) ** 2:
            return 'modify'
        
        # Input area (rest of bubble)
        if bubble_rect.collidepoint(x, y):
            return 'focus_modify'
        
        return None