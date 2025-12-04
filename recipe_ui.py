"""
recipe_ui.py

Description:
    * Pygame UI for AI Sous Chef recipe search

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

# Colors - British Racing Green theme
BRG_DARK = (0, 66, 37)
BRG_MID = (0, 82, 46)
BRG_LIGHT = (0, 102, 58)
CREAM = (255, 253, 240)
GOLD = (212, 175, 55)
GOLD_DARK = (170, 140, 44)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (180, 180, 180)
RED_SOFT = (198, 86, 86)

# Screen dimensions
WIDTH, HEIGHT = 1280, 720


class RecipeApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("AI Sous Chef")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font = pygame.font.SysFont("Georgia", 18)
        self.font_large = pygame.font.SysFont("Georgia", 36, bold=True)
        self.font_medium = pygame.font.SysFont("Georgia", 22)
        self.font_small = pygame.font.SysFont("Georgia", 14)
        self.font_italic = pygame.font.SysFont("Georgia", 16, italic=True)
        
        # Initialize clients
        self.prompter = RecipePrompter(boto3.client('bedrock-runtime', region_name='us-east-1'))
        self.dynamodb = DynamoDBItemManager(boto3.client('dynamodb', region_name='us-east-1'))
        self.s3 = S3ObjectManager()
        
        # State
        self.search_text = ""
        self.modify_text = ""
        self.results = []
        self.status = "Enter a search query"
        self.loading = False
        self.scroll_offset = 0
        self.view = "search"  # "search", "recipe", or "modify"
        self.hover_index = -1
        self.modify_status = ""
        
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

    def search(self):
        if not self.search_text.strip() or self.loading:
            return
            
        self.loading = True
        self.status = "Searching..."
        self.results = []
        
        def do_search():
            try:
                params = self.prompter.extract_search_params(self.search_text)
                if not params:
                    self.status = "Couldn't understand query"
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
                    self.status = "No recipes found. Press G to generate one."
                    self.loading = False
                    return
                
                self.results = self.prompter.rank_recipes(self.search_text, db_results, top_n=10)
                self.status = f"Found {len(db_results)} recipes"
            except Exception as e:
                self.status = f"Error: {str(e)[:50]}"
            finally:
                self.loading = False
        
        threading.Thread(target=do_search, daemon=True).start()

    def select_recipe(self, index):
        if index >= len(self.results) or self.loading:
            return
            
        self.loading = True
        self.status = "Loading recipe..."
        
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
                    else:
                        self.status = "Failed to format recipe"
            except Exception as e:
                self.status = f"Error: {str(e)[:50]}"
            finally:
                self.loading = False
        
        threading.Thread(target=do_fetch, daemon=True).start()

    def generate_recipe(self):
        if not self.search_text.strip() or self.loading:
            return
            
        self.loading = True
        self.status = "Generating recipe..."
        
        def do_generate():
            try:
                recipe = self.prompter.generate_recipe(self.search_text)
                if recipe:
                    self.view = "recipe"
                    self.scroll_offset = 0
                    self.status = ""
                else:
                    self.status = "Failed to generate recipe"
            except Exception as e:
                self.status = f"Error: {str(e)[:50]}"
            finally:
                self.loading = False
        
        threading.Thread(target=do_generate, daemon=True).start()

    def modify_recipe(self):
        if not self.modify_text.strip() or self.loading:
            return
            
        self.loading = True
        self.modify_status = "Modifying..."
        
        def do_modify():
            try:
                response_text, modified = self.prompter.chat(self.modify_text)
                if modified:
                    self.modify_status = "Recipe updated!"
                    self.scroll_offset = 0
                else:
                    self.modify_status = response_text[:80]
                self.modify_text = ""
            except Exception as e:
                self.modify_status = f"Error: {str(e)[:50]}"
            finally:
                self.loading = False
        
        threading.Thread(target=do_modify, daemon=True).start()

    def draw_rounded_rect(self, surface, color, rect, radius, border=0, border_color=None):
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border > 0 and border_color:
            pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)

    def draw_search_view(self):
        # Header bar
        pygame.draw.rect(self.screen, BRG_DARK, (0, 0, WIDTH, 80))
        
        # Title with gold accent
        title = self.font_large.render("AI Sous Chef", True, CREAM)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 22))
        
        # Gold underline
        title_width = title.get_width()
        pygame.draw.rect(self.screen, GOLD, (WIDTH // 2 - title_width // 2, 65, title_width, 3))
        
        # Search container
        search_y = 110
        self.draw_rounded_rect(self.screen, CREAM, (60, search_y, WIDTH - 230, 50), 8)
        
        # Search text or placeholder
        if self.search_text:
            search_surface = self.font.render(self.search_text, True, BLACK)
        else:
            search_surface = self.font_italic.render("What would you like to cook?", True, GRAY)
        self.screen.blit(search_surface, (80, search_y + 15))
        
        # Cursor blink effect
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = 80 + self.font.size(self.search_text)[0] + 2
            pygame.draw.rect(self.screen, BLACK, (cursor_x, search_y + 12, 2, 26))
        
        # Search button
        btn_rect = (WIDTH - 150, search_y, 80, 50)
        btn_color = GOLD_DARK if self.loading else GOLD
        self.draw_rounded_rect(self.screen, btn_color, btn_rect, 8)
        btn_text = self.font.render("Search", True, BRG_DARK)
        self.screen.blit(btn_text, (btn_rect[0] + 12, btn_rect[1] + 14))
        
        # Status message (right-aligned next to search box)
        status_color = RED_SOFT if "Error" in self.status else GRAY
        status_surface = self.font_small.render(self.status, True, status_color)
        self.screen.blit(status_surface, (WIDTH - 150 - status_surface.get_width() - 20, search_y + 18))
        
        # Results section
        results_y = 200
        
        if self.results:
            results_header = self.font_medium.render("Recipes", True, CREAM)
            self.screen.blit(results_header, (60, results_y - 35))
            pygame.draw.rect(self.screen, GOLD, (60, results_y - 8, 80, 2))
        
        mouse_pos = pygame.mouse.get_pos()
        self.hover_index = -1
        
        for i, recipe in enumerate(self.results):
            if results_y > HEIGHT - 100:
                break
            
            card_rect = (60, results_y, WIDTH - 120, 70)
            
            if card_rect[0] <= mouse_pos[0] <= card_rect[0] + card_rect[2] and \
               card_rect[1] <= mouse_pos[1] <= card_rect[1] + card_rect[3]:
                self.hover_index = i
                card_color = BRG_LIGHT
                border_color = GOLD
            else:
                card_color = BRG_MID
                border_color = BRG_LIGHT
            
            self.draw_rounded_rect(self.screen, card_color, card_rect, 10, 2, border_color)
            
            badge_rect = (card_rect[0] + 15, card_rect[1] + 20, 30, 30)
            pygame.draw.circle(self.screen, GOLD, (badge_rect[0] + 15, badge_rect[1] + 15), 15)
            num_text = self.font.render(str(i + 1), True, BRG_DARK)
            self.screen.blit(num_text, (badge_rect[0] + 15 - num_text.get_width() // 2, badge_rect[1] + 6))
            
            name = self.font_medium.render(recipe['name'], True, CREAM)
            self.screen.blit(name, (card_rect[0] + 60, card_rect[1] + 12))
            
            cal = recipe.get('calories', 'N/A')
            category = recipe.get('category', 'N/A')
            details = f"{category}  •  {cal} cal"
            details_surface = self.font_small.render(details, True, GRAY)
            self.screen.blit(details_surface, (card_rect[0] + 60, card_rect[1] + 42))
            
            results_y += 80
        
        # Footer
        footer_rect = (0, HEIGHT - 50, WIDTH, 50)
        pygame.draw.rect(self.screen, BRG_DARK, footer_rect)
        
        help_parts = [("ENTER", "Search"), ("G", "Generate"), ("Click", "Select")]
        help_x = WIDTH // 2 - 180
        for key, action in help_parts:
            key_surface = self.font_small.render(key, True, GOLD)
            action_surface = self.font_small.render(f" {action}", True, CREAM)
            self.screen.blit(key_surface, (help_x, HEIGHT - 32))
            self.screen.blit(action_surface, (help_x + key_surface.get_width(), HEIGHT - 32))
            help_x += key_surface.get_width() + action_surface.get_width() + 30

    def draw_recipe_view(self):
        recipe = self.prompter.current_recipe
        if not recipe:
            return
        
        # Header bar
        pygame.draw.rect(self.screen, BRG_DARK, (0, 0, WIDTH, 80))
        
        # Back button
        back_rect = (30, 22, 100, 36)
        mouse_pos = pygame.mouse.get_pos()
        back_hover = back_rect[0] <= mouse_pos[0] <= back_rect[0] + back_rect[2] and \
                     back_rect[1] <= mouse_pos[1] <= back_rect[1] + back_rect[3]
        
        self.draw_rounded_rect(self.screen, GOLD if back_hover else BRG_MID, back_rect, 6, 2, GOLD)
        back_text = self.font.render("← Back", True, CREAM)
        self.screen.blit(back_text, (back_rect[0] + 20, back_rect[1] + 8))
        
        # Recipe title
        title = self.font_large.render(recipe.get('name', 'Recipe')[:40], True, CREAM)
        title_x = max(150, WIDTH // 2 - title.get_width() // 2)
        self.screen.blit(title, (title_x, 22))
        
        # Content area
        content_surface = pygame.Surface((WIDTH, 2000), pygame.SRCALPHA)
        y = 20
        
        # Description
        if recipe.get('description'):
            desc_card = pygame.Rect(60, y, WIDTH - 120, 70)
            self.draw_rounded_rect(content_surface, BRG_MID, desc_card, 10)
            desc_lines = self._wrap_text(recipe['description'], WIDTH - 160)
            desc_y = y + 15
            for line in desc_lines[:2]:
                desc_surface = self.font_italic.render(line, True, CREAM)
                content_surface.blit(desc_surface, (80, desc_y))
                desc_y += 22
            y += 90
        
        # Info bar
        info_card = pygame.Rect(60, y, WIDTH - 120, 50)
        self.draw_rounded_rect(content_surface, BRG_MID, info_card, 10)
        
        # Time
        time_label = self.font_small.render("TIME", True, GOLD)
        content_surface.blit(time_label, (80, y + 8))
        time_val = self.font.render(recipe.get('total_time', 'N/A'), True, CREAM)
        content_surface.blit(time_val, (80, y + 24))
        
        # Servings
        serv_label = self.font_small.render("SERVINGS", True, GOLD)
        content_surface.blit(serv_label, (220, y + 8))
        serv_val = self.font.render(str(recipe.get('servings', 'N/A')), True, CREAM)
        content_surface.blit(serv_val, (220, y + 24))
        
        # Nutrition
        if recipe.get('nutrition'):
            n = recipe['nutrition']
            cal_label = self.font_small.render("CALORIES", True, GOLD)
            content_surface.blit(cal_label, (360, y + 8))
            cal_val = self.font.render(str(n.get('calories', 'N/A')), True, CREAM)
            content_surface.blit(cal_val, (360, y + 24))
            
            prot_label = self.font_small.render("PROTEIN", True, GOLD)
            content_surface.blit(prot_label, (500, y + 8))
            prot_val = self.font.render(str(n.get('protein', 'N/A')), True, CREAM)
            content_surface.blit(prot_val, (500, y + 24))
        
        y += 70
        
        # Two column layout
        col_width = (WIDTH - 140) // 2
        
        # Ingredients
        ing_header = self.font_medium.render("Ingredients", True, GOLD)
        content_surface.blit(ing_header, (60, y))
        pygame.draw.rect(content_surface, GOLD, (60, y + 30, 100, 2))
        
        ing_y = y + 45
        for ing in recipe.get('ingredients', []):
            if isinstance(ing, dict):
                qty = ing.get('quantity', '')
                unit = ing.get('unit', '')
                item = ing.get('item', '')
                notes = ing.get('notes')
                ing_text = f"• {qty} {unit} {item}".strip()
                if notes:
                    ing_text += f" ({notes})"
            else:
                ing_text = f"• {ing}"
            
            ing_lines = self._wrap_text(ing_text, col_width - 20)
            for line in ing_lines:
                ing_surface = self.font.render(line, True, CREAM)
                content_surface.blit(ing_surface, (70, ing_y))
                ing_y += 26
        
        # Instructions
        inst_header = self.font_medium.render("Instructions", True, GOLD)
        content_surface.blit(inst_header, (60 + col_width + 20, y))
        pygame.draw.rect(content_surface, GOLD, (60 + col_width + 20, y + 30, 110, 2))
        
        inst_y = y + 45
        for i, step in enumerate(recipe.get('instructions', []), 1):
            step_num = self.font.render(f"{i}.", True, GOLD)
            content_surface.blit(step_num, (60 + col_width + 20, inst_y))
            
            step_lines = self._wrap_text(step, col_width - 50)
            for line in step_lines:
                step_surface = self.font.render(line, True, CREAM)
                content_surface.blit(step_surface, (60 + col_width + 50, inst_y))
                inst_y += 26
            inst_y += 8
        
        # Tags
        if recipe.get('tags'):
            max_y = max(ing_y, inst_y) + 20
            tags_label = self.font_small.render("TAGS", True, GOLD)
            content_surface.blit(tags_label, (60, max_y))
            tags_text = ", ".join(recipe['tags'][:8])
            tags_surface = self.font.render(tags_text, True, CREAM)
            content_surface.blit(tags_surface, (60, max_y + 18))
        
        # Calculate max content height for scroll limiting
        self.max_scroll = max(ing_y, inst_y) + 100
        
        # Blit scrolled content
        self.screen.blit(content_surface, (0, 80), (0, self.scroll_offset, WIDTH, HEIGHT - 180))
        
        # Modification bar at bottom
        mod_bar_y = HEIGHT - 100
        pygame.draw.rect(self.screen, BRG_DARK, (0, mod_bar_y, WIDTH, 100))
        pygame.draw.rect(self.screen, GOLD, (0, mod_bar_y, WIDTH, 2))
        
        # Modify input
        self.draw_rounded_rect(self.screen, CREAM, (60, mod_bar_y + 15, WIDTH - 230, 40), 6)
        if self.modify_text:
            mod_surface = self.font.render(self.modify_text, True, BLACK)
        else:
            mod_surface = self.font_italic.render("Modify: 'make it vegetarian', 'double servings'...", True, GRAY)
        self.screen.blit(mod_surface, (75, mod_bar_y + 25))
        
        # Cursor
        if self.view == "recipe" and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = 75 + self.font.size(self.modify_text)[0] + 2
            pygame.draw.rect(self.screen, BLACK, (cursor_x, mod_bar_y + 22, 2, 20))
        
        # Modify button
        mod_btn_rect = (WIDTH - 150, mod_bar_y + 15, 80, 40)
        self.draw_rounded_rect(self.screen, GOLD_DARK if self.loading else GOLD, mod_btn_rect, 6)
        mod_btn_text = self.font.render("Modify", True, BRG_DARK)
        self.screen.blit(mod_btn_text, (mod_btn_rect[0] + 12, mod_btn_rect[1] + 10))
        
        # Modify status
        if self.modify_status:
            status_color = RED_SOFT if "Error" in self.modify_status or "only" in self.modify_status else CREAM
            status_surface = self.font_small.render(self.modify_status[:100], True, status_color)
            self.screen.blit(status_surface, (60, mod_bar_y + 65))
        
        # Help text
        help_surface = self.font_small.render("Scroll • ESC to go back • ENTER to modify", True, GRAY)
        self.screen.blit(help_surface, (WIDTH - 300, mod_bar_y + 65))

    def _wrap_text(self, text, max_width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = current + " " + word if current else word
            if self.font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def handle_click(self, pos):
        x, y = pos
        
        if self.view == "recipe":
            # Back button
            if 30 <= x <= 130 and 22 <= y <= 58:
                self.view = "search"
                self.scroll_offset = 0
                self.modify_text = ""
                self.modify_status = ""
                self.prompter.clear_conversation()
                return
            
            # Modify button
            mod_bar_y = HEIGHT - 100
            if WIDTH - 150 <= x <= WIDTH - 70 and mod_bar_y + 15 <= y <= mod_bar_y + 55:
                self.modify_recipe()
                return
            return
        
        # Search view
        # Search button
        if WIDTH - 150 <= x <= WIDTH - 70 and 110 <= y <= 160:
            self.search()
            return
        
        # Results
        if self.hover_index >= 0:
            self.select_recipe(self.hover_index)

    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if self.view == "recipe":
                        if event.key == pygame.K_ESCAPE:
                            self.view = "search"
                            self.scroll_offset = 0
                            self.modify_text = ""
                            self.modify_status = ""
                            self.prompter.clear_conversation()
                        elif event.key == pygame.K_RETURN:
                            self.modify_recipe()
                        elif event.key == pygame.K_BACKSPACE:
                            self.modify_text = self.modify_text[:-1]
                        elif event.unicode.isprintable():
                            self.modify_text += event.unicode
                    else:
                        if event.key == pygame.K_RETURN:
                            self.search()
                        elif event.key == pygame.K_g and not self.search_text.endswith('g'):
                            self.generate_recipe()
                        elif event.key == pygame.K_BACKSPACE:
                            self.search_text = self.search_text[:-1]
                        elif event.unicode.isprintable():
                            self.search_text += event.unicode
                            
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(event.pos)
                    elif event.button == 4:
                        self.scroll_offset = max(0, self.scroll_offset - 40)
                    elif event.button == 5:
                        self.scroll_offset += 40
            
            # Draw
            self.screen.fill(BRG_DARK)
            
            # Gradient
            for i in range(HEIGHT):
                alpha = int(20 * (i / HEIGHT))
                pygame.draw.line(self.screen, (0, 66 + alpha // 2, 37 + alpha // 3), (0, i), (WIDTH, i))
            
            if self.view == "search":
                self.draw_search_view()
            else:
                self.draw_recipe_view()
            
            # Loading overlay
            if self.loading:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))
                
                ticks = pygame.time.get_ticks()
                for i in range(8):
                    x = WIDTH // 2 + int(30 * pygame.math.Vector2(1, 0).rotate(i * 45 + ticks / 10).x)
                    y = HEIGHT // 2 + int(30 * pygame.math.Vector2(1, 0).rotate(i * 45 + ticks / 10).y)
                    alpha = 255 - i * 25
                    pygame.draw.circle(self.screen, GOLD, (x, y), 6)
                
                loading_text = self.font_medium.render("Loading...", True, CREAM)
                self.screen.blit(loading_text, (WIDTH // 2 - loading_text.get_width() // 2, HEIGHT // 2 + 50))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()


if __name__ == '__main__':
    app = RecipeApp()
    app.run()