"""
recipe_ui_keyboard.py

Description:
    * Pygame UI for AI Sous Chef with on-screen touch keyboard
    * Designed for Raspberry Pi 7" touchscreen (800x480)

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
import boto3
import json
import threading

from logic.prompting import RecipePrompter
from infra.managers.dynamodb_manager import DynamoDBItemManager
from infra.managers.s3_manager import S3ObjectManager
from infra.config import AWS_RESOURCES
from ui.home_screen import HomeScreen

# Colors - Sleek Blue theme
BLUE_DARK = (13, 27, 42)
BLUE_MID = (27, 38, 59)
BLUE_LIGHT = (41, 51, 82)
CREAM = (255, 253, 240)
GOLD = (212, 175, 55)
GOLD_DARK = (170, 140, 44)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (180, 180, 180)
RED_SOFT = (198, 86, 86)
ACCENT = (100, 149, 237)  # Cornflower blue accent

# Screen dimensions for 7" RPi display
WIDTH, HEIGHT = 800, 480

# Keyboard layout
KEYBOARD_ROWS = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
    ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', "'"],
    ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '?'],
]
KEYBOARD_HEIGHT = 200
KEY_WIDTH = 68
KEY_HEIGHT = 34
KEY_MARGIN = 4


class TouchKeyboard:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.visible = False
        self.shift = False
        self.y_offset = HEIGHT - KEYBOARD_HEIGHT
        self.pressed_key = None
        self.press_time = 0
        self.PRESS_DURATION = 100  # milliseconds
        
    def draw(self):
        if not self.visible:
            return
            
        # Keyboard background
        pygame.draw.rect(self.screen, BLUE_DARK, (0, self.y_offset, WIDTH, KEYBOARD_HEIGHT))
        pygame.draw.rect(self.screen, ACCENT, (0, self.y_offset, WIDTH, 2))
        
        y = self.y_offset + 8
        current_time = pygame.time.get_ticks()
        
        for row_idx, row in enumerate(KEYBOARD_ROWS):
            # Center each row
            row_width = len(row) * (KEY_WIDTH + KEY_MARGIN) - KEY_MARGIN
            x = (WIDTH - row_width) // 2
            
            for key in row:
                display_key = key.upper() if self.shift else key
                
                # Check if this key is pressed
                is_pressed = (self.pressed_key == key and 
                             current_time - self.press_time < self.PRESS_DURATION)
                
                # Key background
                key_rect = pygame.Rect(x, y, KEY_WIDTH, KEY_HEIGHT)
                key_color = ACCENT if is_pressed else BLUE_MID
                pygame.draw.rect(self.screen, key_color, key_rect, border_radius=4)
                pygame.draw.rect(self.screen, BLUE_LIGHT, key_rect, 1, border_radius=4)
                
                # Key label
                label = self.font.render(display_key, True, CREAM)
                label_x = x + (KEY_WIDTH - label.get_width()) // 2
                label_y = y + (KEY_HEIGHT - label.get_height()) // 2
                self.screen.blit(label, (label_x, label_y))
                
                x += KEY_WIDTH + KEY_MARGIN
            
            y += KEY_HEIGHT + KEY_MARGIN
        
        # Special keys row
        special_y = y
        special_keys = [('Shift', 70), ('SPACE', 320), ('<-', 70), ('GO', 70), ('X', 50)]
        x = (WIDTH - sum(w for _, w in special_keys) - KEY_MARGIN * 4) // 2
        
        for label, width in special_keys:
            # Check if this key is pressed
            is_pressed = (self.pressed_key == label and 
                         current_time - self.press_time < self.PRESS_DURATION)
            
            key_rect = pygame.Rect(x, special_y, width, KEY_HEIGHT)
            if is_pressed:
                color = WHITE
            elif label == 'GO':
                color = ACCENT
            elif label == 'X':
                color = RED_SOFT
            elif label == 'Shift' and self.shift:
                color = GOLD_DARK
            else:
                color = BLUE_MID
            pygame.draw.rect(self.screen, color, key_rect, border_radius=4)
            pygame.draw.rect(self.screen, ACCENT if label == 'GO' else BLUE_LIGHT, key_rect, 1, border_radius=4)
            
            text_color = BLUE_DARK if label == 'GO' else WHITE
            text = self.font.render(label, True, text_color)
            text_x = x + (width - text.get_width()) // 2
            text_y = special_y + (KEY_HEIGHT - text.get_height()) // 2
            self.screen.blit(text, (text_x, text_y))
            
            x += width + KEY_MARGIN
    
    def handle_touch(self, pos):
        if not self.visible:
            return None
            
        x, y = pos
        if y < self.y_offset:
            return None
        
        # Check regular keys
        key_y = self.y_offset + 8
        for row in KEYBOARD_ROWS:
            row_width = len(row) * (KEY_WIDTH + KEY_MARGIN) - KEY_MARGIN
            key_x = (WIDTH - row_width) // 2
            
            for key in row:
                key_rect = pygame.Rect(key_x, key_y, KEY_WIDTH, KEY_HEIGHT)
                if key_rect.collidepoint(pos):
                    result = key.upper() if self.shift else key
                    self.pressed_key = key
                    self.press_time = pygame.time.get_ticks()
                    self.shift = False
                    return result
                key_x += KEY_WIDTH + KEY_MARGIN
            
            key_y += KEY_HEIGHT + KEY_MARGIN
        
        # Check special keys
        special_y = key_y
        special_keys = [('SHIFT', 70), ('SPACE', 320), ('BACKSPACE', 70), ('GO', 70), ('HIDE', 50)]
        key_x = (WIDTH - sum(w for _, w in special_keys) - KEY_MARGIN * 4) // 2
        
        for action, width in special_keys:
            key_rect = pygame.Rect(key_x, special_y, width, KEY_HEIGHT)
            if key_rect.collidepoint(pos):
                self.pressed_key = action
                self.press_time = pygame.time.get_ticks()
                if action == 'SHIFT':
                    self.shift = not self.shift
                    return None
                elif action == 'SPACE':
                    return ' '
                elif action == 'BACKSPACE':
                    return 'BACKSPACE'
                elif action == 'GO':
                    return 'GO'
                elif action == 'HIDE':
                    return 'HIDE'
            key_x += width + KEY_MARGIN
        
        return None


class RecipeApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("AI Sous Chef")
        self.clock = pygame.time.Clock()
        
        # Fonts - larger for 7" screen readability
        self.font = pygame.font.SysFont("Georgia", 20)
        self.font_large = pygame.font.SysFont("Georgia", 36, bold=True)
        self.font_medium = pygame.font.SysFont("Georgia", 24)
        self.font_small = pygame.font.SysFont("Georgia", 16)
        self.font_italic = pygame.font.SysFont("Georgia", 18, italic=True)
        
        # Initialize clients
        self.prompter = RecipePrompter(boto3.client('bedrock-runtime', region_name='us-east-1'))
        self.dynamodb = DynamoDBItemManager(boto3.client('dynamodb', region_name='us-east-1'))
        self.s3 = S3ObjectManager()
        
        # Keyboard
        self.keyboard = TouchKeyboard(self.screen, self.font)
        
        # Home screen
        self.home_screen = HomeScreen(WIDTH, HEIGHT)
        
        # State
        self.search_text = ""
        self.modify_text = ""
        self.active_input = "search"  # "search" or "modify"
        self.results = []
        self.status = "Tap to search"
        self.loading = False
        self.scroll_offset = 0
        self.view = "home"  # "home", "search", or "recipe"
        self.modify_status = ""
        self.max_scroll = 0
        
    def _build_filter(self, params: dict) -> tuple:
        filter_parts = []
        expression_values = {}
        expression_names = {'#n': 'name'}

        keyword_parts = []
        for i, kw in enumerate(params.get('keywords', [])):
            keyword_parts.append(f'contains(keywords, :kw{i})')
            keyword_parts.append(f'contains(#n, :kw{i})')
            keyword_parts.append(f'contains(description, :kw{i})')
            expression_values[f':kw{i}'] = kw.lower()

        if keyword_parts:
            filter_parts.append(f"({' OR '.join(keyword_parts)})")

        if params.get('category'):
            filter_parts.append('category = :cat')
            expression_values[':cat'] = params['category']

        if params.get('max_calories'):
            filter_parts.append('calories <= :maxcal')
            expression_values[':maxcal'] = params['max_calories']

        filter_expression = ' AND '.join(filter_parts) if filter_parts else None
        return (filter_expression, expression_values if expression_values else None, expression_names)

    def get_active_text(self):
        return self.search_text if self.active_input == "search" else self.modify_text
    
    def set_active_text(self, text):
        if self.active_input == "search":
            self.search_text = text
        else:
            self.modify_text = text

    def search(self):
        if not self.search_text.strip() or self.loading:
            return
            
        self.loading = True
        self.status = "Searching..."
        self.results = []
        self.keyboard.visible = False
        
        def do_search():
            try:
                params = self.prompter.extract_search_params(self.search_text)
                if not params:
                    self.status = "Couldn't understand"
                    self.loading = False
                    return
                
                filter_expr, expr_vals, expr_names = self._build_filter(params)
                db_results = self.dynamodb.scan_table(
                    table_name=AWS_RESOURCES['dynamodb_recipes_table_name'],
                    filter_expression=filter_expr,
                    expression_values=expr_vals,
                    expression_names=expr_names
                )
                
                if not db_results:
                    self.status = "No recipes found"
                    self.loading = False
                    return
                
                self.results = self.prompter.rank_recipes(self.search_text, db_results, top_n=6)
                self.status = f"Found {len(db_results)}"
            except Exception as e:
                self.status = f"Error"
            finally:
                self.loading = False
        
        threading.Thread(target=do_search, daemon=True).start()

    def select_recipe(self, index):
        if index >= len(self.results) or self.loading:
            return
            
        self.loading = True
        self.status = "Loading..."
        
        def do_fetch():
            try:
                selected = self.results[index]
                raw = self.s3.get_object(AWS_RESOURCES['s3_clean_bucket_name'], selected['s3_key'])
                if raw:
                    raw_recipe = json.loads(raw.decode('utf-8'))
                    formatted = self.prompter.format_recipe(raw_recipe)
                    if formatted:
                        self.view = "recipe"
                        self.scroll_offset = 0
                        self.status = ""
            except Exception as e:
                self.status = "Error"
            finally:
                self.loading = False
        
        threading.Thread(target=do_fetch, daemon=True).start()

    def generate_recipe(self):
        if not self.search_text.strip() or self.loading:
            return
            
        self.loading = True
        self.status = "Generating..."
        self.keyboard.visible = False
        
        def do_generate():
            try:
                recipe = self.prompter.generate_recipe(self.search_text)
                if recipe:
                    self.view = "recipe"
                    self.scroll_offset = 0
                    self.status = ""
            except Exception as e:
                self.status = "Error"
            finally:
                self.loading = False
        
        threading.Thread(target=do_generate, daemon=True).start()

    def modify_recipe(self):
        if not self.modify_text.strip() or self.loading:
            return
            
        self.loading = True
        self.modify_status = "Modifying..."
        self.keyboard.visible = False
        
        def do_modify():
            try:
                response_text, modified = self.prompter.chat(self.modify_text)
                if modified:
                    self.modify_status = "Updated!"
                    self.scroll_offset = 0
                else:
                    self.modify_status = response_text[:40]
                self.modify_text = ""
            except Exception as e:
                self.modify_status = "Error"
            finally:
                self.loading = False
        
        threading.Thread(target=do_modify, daemon=True).start()

    def draw_rounded_rect(self, surface, color, rect, radius, border=0, border_color=None):
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border > 0 and border_color:
            pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)

    def draw_search_view(self):
        content_height = HEIGHT - (KEYBOARD_HEIGHT if self.keyboard.visible else 0)
        
        # Header
        pygame.draw.rect(self.screen, BLUE_DARK, (0, 0, WIDTH, 50))
        
        # Home button
        home_rect = (15, 12, 60, 28)
        self.draw_rounded_rect(self.screen, BLUE_MID, home_rect, 4, 1, ACCENT)
        home_text = self.font_small.render("Home", True, CREAM)
        self.screen.blit(home_text, (home_rect[0] + 10, home_rect[1] + 5))
        
        title = self.font_large.render("AI Sous Chef", True, CREAM)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 8))
        pygame.draw.rect(self.screen, ACCENT, (WIDTH // 2 - title.get_width() // 2, 46, title.get_width(), 2))
        
        # Search box
        search_y = 60
        search_rect = (20, search_y, WIDTH - 210, 36)
        self.draw_rounded_rect(self.screen, CREAM, search_rect, 6)
        
        if self.search_text:
            search_surface = self.font.render(self.search_text[-30:], True, BLACK)
        else:
            search_surface = self.font_italic.render("What would you like to cook?", True, GRAY)
        self.screen.blit(search_surface, (30, search_y + 9))
        
        # Cursor
        if self.active_input == "search" and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = 30 + self.font.size(self.search_text[-30:])[0] + 2
            pygame.draw.rect(self.screen, BLACK, (cursor_x, search_y + 8, 2, 20))
        
        # Search button
        btn_rect = (WIDTH - 100, search_y, 80, 36)
        self.draw_rounded_rect(self.screen, ACCENT, btn_rect, 6)
        btn_text = self.font.render("Search", True, BLUE_DARK)
        self.screen.blit(btn_text, (btn_rect[0] + 10, btn_rect[1] + 7))
        
        # Generate button (next to search)
        gen_rect = (WIDTH - 185, search_y, 80, 36)
        self.draw_rounded_rect(self.screen, BLUE_MID, gen_rect, 6, 1, ACCENT)
        gen_text = self.font_small.render("Generate", True, CREAM)
        self.screen.blit(gen_text, (gen_rect[0] + 8, gen_rect[1] + 9))
        
        # Status
        status_surface = self.font_small.render(self.status, True, GRAY)
        self.screen.blit(status_surface, (20, search_y + 42))
        
        # Results
        results_y = 105
        max_results = 4 if self.keyboard.visible else 6
        
        for i, recipe in enumerate(self.results[:max_results]):
            if results_y > content_height - 50:
                break
            
            card_rect = (20, results_y, WIDTH - 40, 56)
            self.draw_rounded_rect(self.screen, BLUE_MID, card_rect, 8, 1, BLUE_LIGHT)
            
            # Number badge
            pygame.draw.circle(self.screen, ACCENT, (card_rect[0] + 25, card_rect[1] + 28), 14)
            num_text = self.font_small.render(str(i + 1), True, BLUE_DARK)
            self.screen.blit(num_text, (card_rect[0] + 25 - num_text.get_width() // 2, card_rect[1] + 20))
            
            # Recipe name (with wrapping if needed)
            name = recipe['name']
            max_name_width = card_rect[2] - 60  # Leave room for badge
            
            if self.font_medium.size(name)[0] > max_name_width:
                # Truncate with ellipsis at word boundary
                words = name.split()
                truncated = ""
                for word in words:
                    test = truncated + " " + word if truncated else word
                    if self.font_medium.size(test + "...")[0] <= max_name_width:
                        truncated = test
                    else:
                        break
                name = truncated + "..." if truncated else name[:20] + "..."
            
            name_surface = self.font_medium.render(name, True, CREAM)
            self.screen.blit(name_surface, (card_rect[0] + 50, card_rect[1] + 6))
            
            # Details
            cal = recipe.get('calories', 'N/A')
            details = f"{recipe.get('category', '')} • {cal} cal"
            details_surface = self.font_small.render(details, True, GRAY)
            self.screen.blit(details_surface, (card_rect[0] + 50, card_rect[1] + 34))
            
            results_y += 62

    def draw_recipe_view(self):
        recipe = self.prompter.current_recipe
        if not recipe:
            return
        
        content_height = HEIGHT - (KEYBOARD_HEIGHT if self.keyboard.visible else 0)
        
        # Header
        pygame.draw.rect(self.screen, BLUE_DARK, (0, 0, WIDTH, 45))
        
        # Back button (to search)
        back_rect = (10, 8, 60, 30)
        self.draw_rounded_rect(self.screen, BLUE_MID, back_rect, 4, 1, ACCENT)
        back_text = self.font_small.render("< Back", True, CREAM)
        self.screen.blit(back_text, (back_rect[0] + 8, back_rect[1] + 6))
        
        # Done button (to home)
        done_rect = (WIDTH - 70, 8, 60, 30)
        self.draw_rounded_rect(self.screen, ACCENT, done_rect, 4)
        done_text = self.font_small.render("Done", True, BLUE_DARK)
        self.screen.blit(done_text, (done_rect[0] + 10, done_rect[1] + 6))
        
        # Title (truncate to fit between buttons)
        max_title_width = WIDTH - 160  # Leave room for Back and Done buttons
        title_text = recipe.get('name', 'Recipe')
        title = self.font_medium.render(title_text, True, CREAM)
        
        # Truncate if too wide
        while title.get_width() > max_title_width and len(title_text) > 10:
            title_text = title_text[:-4] + "..."
            title = self.font_medium.render(title_text, True, CREAM)
        
        title_x = 80 + (WIDTH - 160 - title.get_width()) // 2
        self.screen.blit(title, (title_x, 12))
        
        # Content area
        content_surface = pygame.Surface((WIDTH, 1500), pygame.SRCALPHA)
        y = 10
        
        # Info bar
        info_rect = pygame.Rect(10, y, WIDTH - 20, 35)
        self.draw_rounded_rect(content_surface, BLUE_MID, info_rect, 6)
        
        info_parts = [
            f"Time: {recipe.get('total_time', 'N/A')}",
            f"Serves: {recipe.get('servings', 'N/A')}",
        ]
        if recipe.get('nutrition'):
            info_parts.append(f"Cal: {recipe['nutrition'].get('calories', 'N/A')}")
        
        info_text = " | ".join(info_parts)
        info_surface = self.font_small.render(info_text, True, CREAM)
        content_surface.blit(info_surface, (20, y + 10))
        y += 45
        
        # Two column layout
        col_width = (WIDTH - 30) // 2
        
        # Ingredients
        ing_label = self.font_medium.render("Ingredients", True, ACCENT)
        content_surface.blit(ing_label, (10, y))
        pygame.draw.rect(content_surface, ACCENT, (10, y + 28, 100, 2))
        
        ing_y = y + 35
        for ing in recipe.get('ingredients', [])[:15]:
            if isinstance(ing, dict):
                qty = ing.get('quantity', '')
                unit = ing.get('unit', '')
                item = ing.get('item', '')
                ing_text = f"• {qty} {unit} {item}".strip()
            else:
                ing_text = f"• {ing}"
            
            # Proper word wrapping for ingredients
            ing_lines = self._wrap_text(ing_text, col_width - 20)
            for j, line in enumerate(ing_lines):
                if j > 0:
                    line = "  " + line  # Indent continuation lines
                ing_surface = self.font_small.render(line, True, CREAM)
                content_surface.blit(ing_surface, (15, ing_y))
                ing_y += 22
        
        # Instructions
        inst_label = self.font_medium.render("Instructions", True, ACCENT)
        content_surface.blit(inst_label, (col_width + 20, y))
        pygame.draw.rect(content_surface, ACCENT, (col_width + 20, y + 28, 110, 2))
        
        inst_y = y + 35
        for i, step in enumerate(recipe.get('instructions', [])[:10], 1):
            # Proper word wrapping for instructions
            step_lines = self._wrap_text(f"{i}. {step}", col_width - 30)
            for j, line in enumerate(step_lines):
                if j > 0:
                    line = "   " + line  # Indent continuation lines
                step_surface = self.font_small.render(line, True, CREAM)
                content_surface.blit(step_surface, (col_width + 20, inst_y))
                inst_y += 22
            inst_y += 4
        
        self.max_scroll = max(ing_y, inst_y) - 150
        
        # Blit scrolled content
        visible_height = content_height - 95
        self.screen.blit(content_surface, (0, 50), (0, self.scroll_offset, WIDTH, visible_height))
        
        # Modify bar at bottom
        mod_y = content_height - 50
        pygame.draw.rect(self.screen, BLUE_DARK, (0, mod_y, WIDTH, 50))
        pygame.draw.rect(self.screen, ACCENT, (0, mod_y, WIDTH, 2))
        
        # Modify input
        mod_rect = (10, mod_y + 10, WIDTH - 100, 32)
        self.draw_rounded_rect(self.screen, CREAM, mod_rect, 4)
        
        if self.modify_text:
            mod_surface = self.font_small.render(self.modify_text[-40:], True, BLACK)
        else:
            mod_surface = self.font_italic.render("Tap to modify recipe...", True, GRAY)
        self.screen.blit(mod_surface, (18, mod_y + 17))
        
        # Cursor
        if self.active_input == "modify" and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = 18 + self.font_small.size(self.modify_text[-40:])[0] + 2
            pygame.draw.rect(self.screen, BLACK, (cursor_x, mod_y + 14, 2, 20))
        
        # Modify button
        mod_btn = (WIDTH - 80, mod_y + 10, 70, 32)
        self.draw_rounded_rect(self.screen, ACCENT, mod_btn, 4)
        mod_btn_text = self.font_small.render("Modify", True, BLUE_DARK)
        self.screen.blit(mod_btn_text, (mod_btn[0] + 10, mod_btn[1] + 7))
        
        # Status
        if self.modify_status:
            status_surface = self.font_small.render(self.modify_status, True, GRAY)
            self.screen.blit(status_surface, (10, mod_y - 18))

    def _wrap_text(self, text, max_width):
        """Wrap text to fit within max_width pixels."""
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

    def handle_touch(self, pos):
        x, y = pos
        
        # Check keyboard first
        if self.keyboard.visible:
            key = self.keyboard.handle_touch(pos)
            if key:
                if key == 'BACKSPACE':
                    self.set_active_text(self.get_active_text()[:-1])
                elif key == 'GO':
                    self.keyboard.visible = False
                    if self.active_input == "search":
                        self.search()
                    else:
                        self.modify_recipe()
                elif key == 'HIDE':
                    self.keyboard.visible = False
                else:
                    self.set_active_text(self.get_active_text() + key)
                return
        
        content_height = HEIGHT - (KEYBOARD_HEIGHT if self.keyboard.visible else 0)
        
        if self.view == "home":
            # Tap anywhere on home screen goes to search
            self.view = "search"
            return
        
        if self.view == "search":
            # Home button
            if 15 <= x <= 75 and 12 <= y <= 40:
                self.view = "home"
                self.search_text = ""
                self.results = []
                self.keyboard.visible = False
                return
            
            # Search box tap
            if 20 <= x <= WIDTH - 210 and 60 <= y <= 96:
                self.active_input = "search"
                self.keyboard.visible = True
                return
            
            # Search button
            if WIDTH - 100 <= x <= WIDTH - 20 and 60 <= y <= 96:
                self.search()
                return
            
            # Generate button (next to search)
            if WIDTH - 185 <= x <= WIDTH - 105 and 60 <= y <= 96:
                self.generate_recipe()
                return
            
            # Results
            results_y = 105
            for i in range(min(len(self.results), 6)):
                if 20 <= x <= WIDTH - 20 and results_y <= y <= results_y + 50:
                    self.select_recipe(i)
                    return
                results_y += 56
                
        elif self.view == "recipe":
            # Back button (to search)
            if 10 <= x <= 70 and 8 <= y <= 38:
                self.view = "search"
                self.scroll_offset = 0
                self.modify_text = ""
                self.modify_status = ""
                self.keyboard.visible = False
                self.prompter.clear_conversation()
                return
            
            # Done button (to home)
            if WIDTH - 70 <= x <= WIDTH - 10 and 8 <= y <= 38:
                self.view = "home"
                self.scroll_offset = 0
                self.modify_text = ""
                self.modify_status = ""
                self.search_text = ""
                self.results = []
                self.keyboard.visible = False
                self.prompter.clear_conversation()
                return
            
            # Modify input tap
            mod_y = content_height - 50
            if 10 <= x <= WIDTH - 100 and mod_y + 10 <= y <= mod_y + 42:
                self.active_input = "modify"
                self.keyboard.visible = True
                return
            
            # Modify button
            if WIDTH - 80 <= x <= WIDTH - 10 and mod_y + 10 <= y <= mod_y + 42:
                self.modify_recipe()
                return

    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_touch(event.pos)
                    elif event.button == 4:  # Scroll up
                        self.scroll_offset = max(0, self.scroll_offset - 30)
                    elif event.button == 5:  # Scroll down
                        if self.view == "recipe":
                            self.scroll_offset = min(self.max_scroll, self.scroll_offset + 30)
                
                elif event.type == pygame.FINGERDOWN:
                    # Touch screen support
                    touch_x = int(event.x * WIDTH)
                    touch_y = int(event.y * HEIGHT)
                    self.handle_touch((touch_x, touch_y))
            
            # Draw
            self.screen.fill(BLUE_DARK)
            
            # Gradient
            content_height = HEIGHT - (KEYBOARD_HEIGHT if self.keyboard.visible else 0)
            for i in range(content_height):
                ratio = i / content_height
                r = int(13 + (27 - 13) * ratio)
                g = int(27 + (38 - 27) * ratio)
                b = int(42 + (59 - 42) * ratio)
                pygame.draw.line(self.screen, (r, g, b), (0, i), (WIDTH, i))
            
            if self.view == "home":
                self.home_screen.update()
                self.home_screen.draw(self.screen)
            elif self.view == "search":
                self.draw_search_view()
            else:
                self.draw_recipe_view()
            
            # Keyboard
            self.keyboard.draw()
            
            # Loading overlay
            if self.loading:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))
                
                ticks = pygame.time.get_ticks()
                for i in range(8):
                    cx = WIDTH // 2 + int(25 * pygame.math.Vector2(1, 0).rotate(i * 45 + ticks / 10).x)
                    cy = HEIGHT // 2 + int(25 * pygame.math.Vector2(1, 0).rotate(i * 45 + ticks / 10).y)
                    pygame.draw.circle(self.screen, GOLD, (cx, cy), 5)
                
                loading_text = self.font_medium.render("Loading...", True, CREAM)
                self.screen.blit(loading_text, (WIDTH // 2 - loading_text.get_width() // 2, HEIGHT // 2 + 40))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()


if __name__ == '__main__':
    app = RecipeApp()
    app.run()