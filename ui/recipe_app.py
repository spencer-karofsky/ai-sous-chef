"""
ui/recipe_app.py

Description:
    * Main application class for AI Sous Chef

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

from ui.constants import WIDTH, HEIGHT, KEYBOARD_HEIGHT, BLUE_DARK, CREAM, GOLD
from ui.touch_keyboard import TouchKeyboard
from ui.home_screen import HomeScreen
from ui.views import SearchView, RecipeView


class RecipeApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("AI Sous Chef")
        self.clock = pygame.time.Clock()

        # Fonts
        self.fonts = {
            'regular': pygame.font.SysFont("Georgia", 32),
            'large': pygame.font.SysFont("Georgia", 56, bold=True),
            'medium': pygame.font.SysFont("Georgia", 38),
            'small': pygame.font.SysFont("Georgia", 26),
            'italic': pygame.font.SysFont("Georgia", 28, italic=True),
        }

        # Initialize clients
        self.prompter = RecipePrompter(boto3.client('bedrock-runtime', region_name='us-east-1'))
        self.dynamodb = DynamoDBItemManager(boto3.client('dynamodb', region_name='us-east-1'))
        self.s3 = S3ObjectManager()

        # UI components
        self.keyboard = TouchKeyboard(self.screen, self.fonts['regular'])
        self.home_screen = HomeScreen(WIDTH, HEIGHT)
        self.search_view = SearchView(self.fonts)
        self.recipe_view = RecipeView(self.fonts)

        # State
        self.search_text = ""
        self.modify_text = ""
        self.active_input = "search"
        self.results = []
        self.status = "Tap to search"
        self.loading = False
        self.scroll_offset = 0
        self.view = "home"
        self.modify_status = ""
        self.max_scroll = 0

        # Touch scrolling
        self.touch_start_y = None
        self.touch_start_scroll = 0
        self.is_dragging = False
        self.drag_threshold = 10

    def _get_state(self):
        """Get current state dict for views."""
        return {
            'search_text': self.search_text,
            'modify_text': self.modify_text,
            'active_input': self.active_input,
            'results': self.results,
            'status': self.status,
            'scroll_offset': self.scroll_offset,
            'modify_status': self.modify_status,
            'recipe': self.prompter.current_recipe,
        }

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
            except Exception:
                self.status = "Error"
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
            except Exception:
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
            except Exception:
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
            except Exception:
                self.modify_status = "Error"
            finally:
                self.loading = False

        threading.Thread(target=do_modify, daemon=True).start()

    def handle_touch(self, pos):
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

        if self.view == "home":
            self.view = "search"
            return

        state = self._get_state()

        if self.view == "search":
            action = self.search_view.handle_touch(pos, state, self.keyboard.visible)
            if action == 'home':
                self.view = "home"
                self.search_text = ""
                self.results = []
                self.keyboard.visible = False
            elif action == 'focus_search':
                self.active_input = "search"
                self.keyboard.visible = True
            elif action == 'generate':
                self.generate_recipe()
            elif action == 'search':
                self.search()
            elif action and action.startswith('select_'):
                idx = int(action.split('_')[1])
                self.select_recipe(idx)

        elif self.view == "recipe":
            action = self.recipe_view.handle_touch(pos, state, self.keyboard.visible)
            if action == 'back':
                self.view = "search"
                self.scroll_offset = 0
                self.modify_text = ""
                self.modify_status = ""
                self.keyboard.visible = False
                self.prompter.clear_conversation()
            elif action == 'done':
                self.view = "home"
                self.scroll_offset = 0
                self.modify_text = ""
                self.modify_status = ""
                self.search_text = ""
                self.results = []
                self.keyboard.visible = False
                self.prompter.clear_conversation()
            elif action == 'focus_modify':
                self.active_input = "modify"
                self.keyboard.visible = True
            elif action == 'modify':
                self.modify_recipe()

    def _draw_background(self):
        content_height = HEIGHT - (KEYBOARD_HEIGHT if self.keyboard.visible else 0)
        for i in range(content_height):
            ratio = i / content_height
            r = int(13 + (27 - 13) * ratio)
            g = int(27 + (38 - 27) * ratio)
            b = int(42 + (59 - 42) * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, i), (WIDTH, i))

    def _draw_loading(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        ticks = pygame.time.get_ticks()
        for i in range(8):
            cx = WIDTH // 2 + int(40 * pygame.math.Vector2(1, 0).rotate(i * 45 + ticks / 10).x)
            cy = HEIGHT // 2 + int(40 * pygame.math.Vector2(1, 0).rotate(i * 45 + ticks / 10).y)
            pygame.draw.circle(self.screen, GOLD, (cx, cy), 8)

        loading_text = self.fonts['medium'].render("Loading...", True, CREAM)
        self.screen.blit(loading_text, (WIDTH // 2 - loading_text.get_width() // 2, HEIGHT // 2 + 60))

    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.touch_start_y = event.pos[1]
                        self.touch_start_scroll = self.scroll_offset
                        self.is_dragging = False
                    elif event.button == 4:
                        self.scroll_offset = max(0, self.scroll_offset - 40)
                    elif event.button == 5:
                        if self.view == "recipe":
                            self.scroll_offset = min(self.max_scroll, self.scroll_offset + 40)

                elif event.type == pygame.MOUSEMOTION:
                    if self.touch_start_y is not None and self.view == "recipe":
                        delta = self.touch_start_y - event.pos[1]
                        if abs(delta) > self.drag_threshold:
                            self.is_dragging = True
                            new_scroll = self.touch_start_scroll + delta
                            self.scroll_offset = max(0, min(self.max_scroll, new_scroll))

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        if not self.is_dragging:
                            self.handle_touch(event.pos)
                        self.touch_start_y = None
                        self.is_dragging = False

                elif event.type == pygame.FINGERDOWN:
                    touch_x = int(event.x * WIDTH)
                    touch_y = int(event.y * HEIGHT)
                    self.touch_start_y = touch_y
                    self.touch_start_scroll = self.scroll_offset
                    self.is_dragging = False

                elif event.type == pygame.FINGERMOTION:
                    if self.touch_start_y is not None and self.view == "recipe":
                        touch_y = int(event.y * HEIGHT)
                        delta = self.touch_start_y - touch_y
                        if abs(delta) > self.drag_threshold:
                            self.is_dragging = True
                            new_scroll = self.touch_start_scroll + delta
                            self.scroll_offset = max(0, min(self.max_scroll, new_scroll))

                elif event.type == pygame.FINGERUP:
                    touch_x = int(event.x * WIDTH)
                    touch_y = int(event.y * HEIGHT)
                    if not self.is_dragging:
                        self.handle_touch((touch_x, touch_y))
                    self.touch_start_y = None
                    self.is_dragging = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            # Draw
            self.screen.fill(BLUE_DARK)
            self._draw_background()

            state = self._get_state()
            if self.view == "home":
                self.home_screen.update()
                self.home_screen.draw(self.screen)
            elif self.view == "search":
                self.search_view.draw(self.screen, state, self.keyboard.visible)
            else:
                new_max = self.recipe_view.draw(self.screen, state, self.keyboard.visible)
                if new_max is not None:
                    self.max_scroll = new_max

            self.keyboard.draw()

            if self.loading:
                self._draw_loading()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


if __name__ == '__main__':
    app = RecipeApp()
    app.run()