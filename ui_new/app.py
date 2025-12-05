"""
ui_new/app.py

Description:
    * Main application class for AI Sous Chef (Clean minimal design)

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

from ui_new.constants import *
from ui_new.components import NavBar, TouchKeyboard
from ui_new.saved_recipes_manager import SavedRecipesManager
from ui_new.meal_plan_manager import MealPlanManager
from ui_new.grocery_list_manager import GroceryListManager
from ui_new.views import (
    HomeView, SearchView, CreateView, 
    RecipeView, FavoritesView, SettingsView, WiFiView, PreferencesView,
    SkillLevelView, MyKitchenView, SavedRecipesView, MealPrepView, GroceryListView
)
from infra.managers.bedrock_manager import BedrockManager
from ui_new.config import Config
from ui_new.favorites_manager import FavoritesManager


class RecipeApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("AI Sous Chef")
        self.clock = pygame.time.Clock()

        self.bedrock = BedrockManager(boto3.client('bedrock-runtime', region_name='us-east-1'))
        self.prompter = RecipePrompter(boto3.client('bedrock-runtime', region_name='us-east-1'))

        # Fonts - find a good sans-serif font
        font_name = None
        for name in FONT_SANS:
            if name is None:
                break
            if name.lower() in [f.lower() for f in pygame.font.get_fonts()]:
                font_name = name
                break
        
        self.fonts = {
            'title': pygame.font.SysFont(font_name, FONT_TITLE, bold=True),
            'header': pygame.font.SysFont(font_name, FONT_HEADER, bold=True),
            'body': pygame.font.SysFont(font_name, FONT_BODY),
            'small': pygame.font.SysFont(font_name, FONT_SMALL),
            'caption': pygame.font.SysFont(font_name, FONT_CAPTION),
        }

        # Config - initialize early since views depend on it
        self.config = Config()

        # AWS clients
        self.prompter = RecipePrompter(boto3.client('bedrock-runtime', region_name='us-east-1'))
        self.dynamodb = DynamoDBItemManager(boto3.client('dynamodb', region_name='us-east-1'))
        self.s3 = S3ObjectManager()

        # UI components
        self.navbar = NavBar(self.screen, self.fonts['caption'])
        self.keyboard = TouchKeyboard(self.screen, self.fonts['body'])

        # Favorites manager
        self.favorites_manager = FavoritesManager()
        self.saved_recipes_manager = SavedRecipesManager()
        self.meal_plan_manager = MealPlanManager(self.bedrock)
        self.grocery_list_manager = GroceryListManager(self.bedrock)

        # Views
        self.views = {
            'Home': HomeView(self.fonts),
            'Search': SearchView(self.fonts),
            'Create': CreateView(self.fonts),
            'My Kitchen': MyKitchenView(self.fonts),
            'Favorites': FavoritesView(self.fonts),
            'SavedRecipes': SavedRecipesView(self.fonts),
            'MealPrep': MealPrepView(self.fonts),
            'GroceryList': GroceryListView(self.fonts),
            'Settings': SettingsView(self.fonts, self.config),
            'Recipe': RecipeView(self.fonts),
            'WiFi': WiFiView(self.fonts),
            'Preferences': PreferencesView(self.fonts, self.config),
            'SkillLevel': SkillLevelView(self.fonts, self.config),
        }

        # Pass manager to views that need it
        self.views['Recipe'].set_manager(self.favorites_manager)
        self.views['Favorites'].set_manager(self.favorites_manager)
        self.views['My Kitchen'].set_managers(self.favorites_manager, self.saved_recipes_manager)
        self.views['SavedRecipes'].set_manager(self.saved_recipes_manager)
        self.views['MealPrep'].set_managers(
            self.meal_plan_manager, 
            self.bedrock,
            self.config
        )
        self.views['GroceryList'].set_managers(
            self.grocery_list_manager,
            self.meal_plan_manager
        )

        # State
        self.current_view = 'Home'
        self.previous_view = None
        self.search_text = ""
        self.create_text = ""
        self.modify_text = ""
        self.active_input = None
        self.results = []
        self.status = ""
        self.create_status = ""
        self.modify_status = ""
        self.loading = False
        self.scroll_offset = 0
        self.max_scroll = 0

        # Touch scrolling
        self.touch_start_y = None
        self.touch_start_scroll = 0
        self.is_dragging = False
        self.drag_threshold = 10
        self.touch_start_x = None

        # Track current recipe source for favorites
        self.current_recipe_source = 'search'
        self.current_recipe_s3_key = None

    def _get_state(self):
        return {
            'search_text': self.search_text,
            'create_text': self.create_text,
            'modify_text': self.modify_text,
            'active_input': self.active_input,
            'results': self.results,
            'status': self.status,
            'create_status': self.create_status,
            'modify_status': self.modify_status,
            'scroll_offset': self.scroll_offset,
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

    def _get_active_text(self):
        if self.active_input == 'search':
            return self.search_text
        elif self.active_input == 'create':
            return self.create_text
        elif self.active_input == 'modify':
            return self.modify_text
        return ""

    def _set_active_text(self, text):
        if self.active_input == 'search':
            self.search_text = text
        elif self.active_input == 'create':
            self.create_text = text
        elif self.active_input == 'modify':
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
                self.status = f"Found {len(db_results)} recipes"
            except Exception:
                self.status = "Error searching"
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
                        self.previous_view = self.current_view
                        self.current_view = 'Recipe'
                        self.scroll_offset = 0
                        self.status = ""
                        self.current_recipe_source = 'search'
                        self.current_recipe_s3_key = selected['s3_key']
            except Exception:
                self.status = "Error loading"
            finally:
                self.loading = False

        threading.Thread(target=do_fetch, daemon=True).start()

    def generate_recipe(self):
        if not self.create_text.strip() or self.loading:
            return

        self.loading = True
        self.create_status = "Generating..."
        self.keyboard.visible = False

        def do_generate():
            try:
                recipe = self.prompter.generate_recipe(self.create_text)
                if recipe:
                    # Auto-save the generated recipe
                    self.saved_recipes_manager.add(recipe)
                    
                    self.previous_view = self.current_view
                    self.current_view = 'Recipe'
                    self.scroll_offset = 0
                    self.create_status = ""
                    self.create_text = ""
                    self.current_recipe_source = 'generated'
                    self.current_recipe_s3_key = None
            except Exception:
                self.create_status = "Error generating"
            finally:
                self.loading = False

        threading.Thread(target=do_generate, daemon=True).start()

    def modify_recipe(self):
        if not self.modify_text.strip() or self.loading:
            return

        self.loading = True
        self.modify_status = "Updating..."
        self.keyboard.visible = False

        def do_modify():
            try:
                response_text, modified = self.prompter.chat(self.modify_text)
                if modified:
                    self.modify_status = "Recipe updated!"
                    self.scroll_offset = 0
                else:
                    self.modify_status = response_text[:40]
                self.modify_text = ""
            except Exception:
                self.modify_status = "Error"
            finally:
                self.loading = False

        threading.Thread(target=do_modify, daemon=True).start()

    def handle_keyboard_input(self, key):
        if key == 'BACKSPACE':
            if self.active_input == 'wifi_password':
                self.views['WiFi'].handle_keyboard_input(key)
            elif self.active_input == 'custom_preference':
                self.views['Preferences'].handle_keyboard_input(key)
            elif self.active_input == 'meal_prompt':
                self.views['MealPrep'].handle_keyboard_input(key)
            else:
                self._set_active_text(self._get_active_text()[:-1])
        elif key == 'GO':
            self.keyboard.visible = False
            if self.active_input == 'search':
                self.search()
            elif self.active_input == 'create':
                self.generate_recipe()
            elif self.active_input == 'modify':
                self.modify_recipe()
            elif self.active_input == 'wifi_password':
                self.views['WiFi'].handle_keyboard_input(key)
            elif self.active_input == 'custom_preference':
                self.views['Preferences'].handle_keyboard_input(key)
            elif self.active_input == 'meal_prompt':
                result = self.views['MealPrep'].handle_keyboard_input(key)
                if result == 'generate_meal_plan':
                    self._generate_meal_plan()
        elif key == 'HIDE':
            self.keyboard.visible = False
        else:
            if self.active_input == 'wifi_password':
                self.views['WiFi'].handle_keyboard_input(key)
            elif self.active_input == 'custom_preference':
                self.views['Preferences'].handle_keyboard_input(key)
            elif self.active_input == 'meal_prompt':
                self.views['MealPrep'].handle_keyboard_input(key)
            else:
                self._set_active_text(self._get_active_text() + key)

    def handle_view_action(self, action):
        if not action:
            return

        # Navigation actions
        if action.startswith('navigate_'):
            view_name = action.replace('navigate_', '')
            
            if view_name == 'wifi':
                self.previous_view = self.current_view
                self.current_view = 'WiFi'
                return
            elif view_name == 'dietary':
                self.views['Preferences'].set_mode('dietary')
                self.previous_view = self.current_view
                self.current_view = 'Preferences'
                return
            elif view_name == 'exclusions':
                self.views['Preferences'].set_mode('exclusions')
                self.previous_view = self.current_view
                self.current_view = 'Preferences'
                return
            elif view_name == 'skill':
                self.previous_view = self.current_view
                self.current_view = 'SkillLevel'
                return
            elif view_name == 'favorites':
                self.previous_view = self.current_view
                self.current_view = 'Favorites'
                return
            elif view_name == 'saved_recipes':
                self.previous_view = self.current_view
                self.current_view = 'SavedRecipes'
                return
            elif view_name == 'meal_prep':
                self.previous_view = self.current_view
                self.current_view = 'MealPrep'
                return
            elif view_name == 'grocery_list':
                self.previous_view = self.current_view
                self.current_view = 'GroceryList'
                return
            
            # Standard navigation
            view_name = view_name.replace('_', ' ').title()
            if view_name in self.views:
                self.current_view = view_name
                self.navbar.active = view_name
                self.keyboard.visible = False
            return

        # Focus actions
        if action == 'focus_search':
            self.active_input = 'search'
            self.keyboard.visible = True
        elif action == 'focus_create':
            self.active_input = 'create'
            self.keyboard.visible = True
        elif action == 'focus_modify':
            self.active_input = 'modify'
            self.keyboard.visible = True
        elif action == 'focus_password':
            self.active_input = 'wifi_password'
            self.keyboard.visible = True
        elif action == 'focus_custom':
            self.active_input = 'custom_preference'
            self.keyboard.visible = True
        
        # Search actions
        elif action == 'search':
            self.search()
        elif action.startswith('select_'):
            idx = int(action.split('_')[1])
            self.select_recipe(idx)
        
        # Create actions
        elif action == 'generate':
            self.generate_recipe()
        elif action.startswith('suggestion_'):
            self.create_text = action.replace('suggestion_', '')
            self.active_input = 'create'
            self.keyboard.visible = True
        
        # Recipe actions
        elif action == 'back':
            if self.current_view in ('Favorites', 'SavedRecipes', 'MealPrep', 'GroceryList'):
                self.current_view = 'My Kitchen'
                self.navbar.active = 'My Kitchen'
                self.keyboard.visible = False
                self.scroll_offset = 0
            elif self.current_view == 'WiFi':
                self.current_view = 'Settings'
                self.navbar.active = 'Settings'
                self.keyboard.visible = False
            elif self.current_view == 'Preferences':
                self.current_view = 'Settings'
                self.navbar.active = 'Settings'
                self.keyboard.visible = False
                self.views['Settings']._build_sections()
            elif self.current_view == 'SkillLevel':
                self.current_view = 'Settings'
                self.navbar.active = 'Settings'
                self.keyboard.visible = False
                self.views['Settings']._build_sections()
            else:
                self.current_view = self.previous_view or 'Search'
                self.navbar.active = self.current_view
                self.scroll_offset = 0
                self.modify_text = ""
                self.modify_status = ""
                self.keyboard.visible = False
                self.prompter.clear_conversation()

        elif action == 'modify':
            self.modify_recipe()
        
        # Favorite actions
        elif action == 'toggle_favorite':
            self._toggle_favorite()
        elif action.startswith('view_'):
            fav_id = action.replace('view_', '')
            self._view_favorite(fav_id)

        elif action.startswith('view_saved_'):
            recipe_id = action.replace('view_saved_', '')
            self._view_saved_recipe(recipe_id)

        elif action == 'generate_list':
            self._generate_grocery_list()

        elif action == 'generate_meal_plan':
            self._generate_meal_plan()

        elif action == 'focus_meal_prompt':
            self.active_input = 'meal_prompt'
            self.keyboard.visible = True

    def _view_saved_recipe(self, recipe_id):
        """Load and view a saved recipe."""
        recipe_data = self.saved_recipes_manager.get_by_id(recipe_id)
        if not recipe_data:
            return
        
        self.prompter.current_recipe = recipe_data
        self.current_recipe_source = 'saved'
        self.current_recipe_s3_key = None
        self.previous_view = 'SavedRecipes'
        self.current_view = 'Recipe'
        self.scroll_offset = 0

    def _generate_grocery_list(self):
        """Generate grocery list from meal plan."""
        self.loading = True
        
        def do_generate():
            try:
                list_id = self.views['GroceryList'].generate_list()
                if list_id:
                    print(f"Generated grocery list: {list_id}")
            except Exception as e:
                print(f"Error generating grocery list: {e}")
            finally:
                self.loading = False
        
        import threading
        threading.Thread(target=do_generate, daemon=True).start()
    
    def _generate_meal_plan(self):
        """Generate AI meal plan based on user prompt."""
        meal_view = self.views['MealPrep']
        prompt = meal_view.prompt_text
        
        if not prompt.strip():
            return
        
        meal_view.generating = True
        meal_view.generation_status = "Creating your personalized meal plan..."
        meal_view.show_generate_modal = False
        self.keyboard.visible = False
        
        def do_generate():
            try:
                # Get user preferences from config
                dietary = self.config.get('dietary', []) if self.config else []
                exclusions = self.config.get('exclusions', []) if self.config else []
                skill = self.config.get('skill_level', 'Beginner') if self.config else 'Beginner'
                
                meal_view.generation_status = "Generating 21 recipes for your week..."
                
                success = self.meal_plan_manager.generate_meal_plan(
                    user_prompt=prompt,
                    dietary_prefs=dietary,
                    exclusions=exclusions,
                    skill_level=skill
                )
                
                if success:
                    meal_view.generation_status = "Meal plan created!"
                    # Auto-generate grocery list
                    meal_view.generation_status = "Generating grocery list..."
                    self.grocery_list_manager.generate_from_meals(
                        self.meal_plan_manager.get_all_meals(),
                        f"Week of {self.meal_plan_manager.get_week_start()}"
                    )
                else:
                    meal_view.generation_status = "Failed to generate. Try again."
                    
            except Exception as e:
                print(f"Error generating meal plan: {e}")
                meal_view.generation_status = "Error occurred. Please try again."
            finally:
                meal_view.generating = False
                meal_view.prompt_text = ""
        
        import threading
        threading.Thread(target=do_generate, daemon=True).start()
    
    def _toggle_favorite(self):
        recipe = self.prompter.current_recipe
        if not recipe:
            return
        
        recipe_name = recipe.get('name', '')
        
        if self.favorites_manager.is_favorite(recipe_name):
            self.favorites_manager.remove_by_name(recipe_name)
        else:
            self.favorites_manager.add(
                recipe,
                source=self.current_recipe_source,
                s3_key=self.current_recipe_s3_key
            )

    def _view_favorite(self, favorite_id):
        favorite = self.favorites_manager.get_by_id(favorite_id)
        if not favorite:
            return
        
        self.loading = True
        
        def do_load():
            try:
                if favorite.get('recipe_data'):
                    self.prompter.current_recipe = favorite['recipe_data']
                    self.current_recipe_source = 'generated'
                    self.current_recipe_s3_key = None
                elif favorite.get('s3_key'):
                    raw = self.s3.get_object(AWS_RESOURCES['s3_clean_bucket_name'], favorite['s3_key'])
                    if raw:
                        raw_recipe = json.loads(raw.decode('utf-8'))
                        self.prompter.format_recipe(raw_recipe)
                        self.current_recipe_source = 'search'
                        self.current_recipe_s3_key = favorite['s3_key']
                
                self.previous_view = 'Favorites'
                self.current_view = 'Recipe'
                self.scroll_offset = 0
            except Exception as e:
                print(f"Error loading favorite: {e}")
            finally:
                self.loading = False
        
        threading.Thread(target=do_load, daemon=True).start()

    def handle_touch(self, pos):
        if self.keyboard.visible:
            key = self.keyboard.handle_touch(pos)
            if key:
                self.handle_keyboard_input(key)
                return

        nav_action = self.navbar.handle_touch(pos)
        if nav_action:
            if nav_action != self.current_view and self.current_view != 'Recipe':
                self.current_view = nav_action
                self.navbar.active = nav_action
                self.keyboard.visible = False
                self.scroll_offset = 0
            elif self.current_view == 'Recipe':
                self.current_view = nav_action
                self.navbar.active = nav_action
                self.keyboard.visible = False
                self.scroll_offset = 0
                self.prompter.clear_conversation()
            return

        state = self._get_state()
        view = self.views.get(self.current_view)
        if view:
            action = view.handle_touch(pos, state, self.keyboard.visible)
            self.handle_view_action(action)

    def _draw_loading(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 220))
        self.screen.blit(overlay, (0, 0))

        ticks = pygame.time.get_ticks()
        cx, cy = WIDTH // 2, HEIGHT // 2
        
        for i in range(8):
            angle = i * 45 + ticks / 5
            x = cx + int(30 * pygame.math.Vector2(1, 0).rotate(angle).x)
            y = cy + int(30 * pygame.math.Vector2(1, 0).rotate(angle).y)
            color = (SOFT_BLACK[0], SOFT_BLACK[1], SOFT_BLACK[2])
            pygame.draw.circle(self.screen, color, (x, y), 6 - i * 0.5)

        loading_text = self.fonts['body'].render("Loading...", True, CHARCOAL)
        self.screen.blit(loading_text, (cx - loading_text.get_width() // 2, cy + 50))
    
    def _view_saved_recipe(self, recipe_id):
        """Load and view a saved recipe."""
        recipe_data = self.saved_recipes_manager.get_by_id(recipe_id)
        if not recipe_data:
            return
        
        self.prompter.current_recipe = recipe_data
        self.current_recipe_source = 'saved'
        self.current_recipe_s3_key = None
        self.previous_view = 'SavedRecipes'
        self.current_view = 'Recipe'
        self.scroll_offset = 0

    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.touch_start_y = event.pos[1]
                        self.touch_start_x = event.pos[0]
                        self.is_dragging = False
                        
                        if self.current_view == 'Settings':
                            self.touch_start_scroll = self.views['Settings'].scroll_offset
                            self._check_slider_start(event.pos)
                        elif self.current_view == 'Recipe':
                            self.touch_start_scroll = self.scroll_offset
                        elif self.current_view == 'Favorites':
                            self.touch_start_scroll = self.views['Favorites'].scroll_offset
                        elif self.current_view == 'WiFi':
                            self.touch_start_scroll = self.views['WiFi'].scroll_offset
                        elif self.current_view == 'Preferences':
                            self.touch_start_scroll = self.views['Preferences'].scroll_offset
                        else:
                            self.touch_start_scroll = 0
                            
                    elif event.button == 4:
                        self._handle_scroll(-40)
                    elif event.button == 5:
                        self._handle_scroll(40)

                elif event.type == pygame.MOUSEMOTION:
                    if self.touch_start_y is not None:
                        if self.current_view == 'Settings' and self.views['Settings'].dragging_slider:
                            self.views['Settings'].handle_drag(event.pos[0], event.pos[1])
                            self.is_dragging = True
                        else:
                            delta = self.touch_start_y - event.pos[1]
                            if abs(delta) > self.drag_threshold:
                                self.is_dragging = True
                                if self.current_view == 'Recipe':
                                    new_scroll = self.touch_start_scroll + delta
                                    self.scroll_offset = max(0, min(self.max_scroll, new_scroll))
                                elif self.current_view == 'Settings':
                                    settings = self.views['Settings']
                                    new_scroll = self.touch_start_scroll + delta
                                    settings.scroll_offset = max(0, min(settings.max_scroll, new_scroll))
                                elif self.current_view == 'Favorites':
                                    favorites = self.views['Favorites']
                                    new_scroll = self.touch_start_scroll + delta
                                    favorites.scroll_offset = max(0, min(favorites.max_scroll, new_scroll))
                                elif self.current_view == 'WiFi':
                                    wifi = self.views['WiFi']
                                    new_scroll = self.touch_start_scroll + delta
                                    wifi.scroll_offset = max(0, min(wifi.max_scroll, new_scroll))
                                elif self.current_view == 'Preferences':
                                    prefs = self.views['Preferences']
                                    new_scroll = self.touch_start_scroll + delta
                                    prefs.scroll_offset = max(0, min(prefs.max_scroll, new_scroll))

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        if self.current_view == 'Settings':
                            self.views['Settings'].handle_drag_end()
                        
                        if not self.is_dragging:
                            self.handle_touch(event.pos)
                        
                        self.touch_start_y = None
                        self.touch_start_x = None
                        self.is_dragging = False

                elif event.type == pygame.FINGERDOWN:
                    touch_x = int(event.x * WIDTH)
                    touch_y = int(event.y * HEIGHT)
                    self.touch_start_y = touch_y
                    self.touch_start_x = touch_x
                    self.is_dragging = False
                    
                    if self.current_view == 'Settings':
                        self.touch_start_scroll = self.views['Settings'].scroll_offset
                        self._check_slider_start((touch_x, touch_y))
                    elif self.current_view == 'Recipe':
                        self.touch_start_scroll = self.scroll_offset
                    elif self.current_view == 'Favorites':
                        self.touch_start_scroll = self.views['Favorites'].scroll_offset
                    elif self.current_view == 'WiFi':
                        self.touch_start_scroll = self.views['WiFi'].scroll_offset
                    elif self.current_view == 'Preferences':
                        self.touch_start_scroll = self.views['Preferences'].scroll_offset
                    else:
                        self.touch_start_scroll = 0

                elif event.type == pygame.FINGERMOTION:
                    touch_x = int(event.x * WIDTH)
                    touch_y = int(event.y * HEIGHT)
                    
                    if self.touch_start_y is not None:
                        if self.current_view == 'Settings' and self.views['Settings'].dragging_slider:
                            self.views['Settings'].handle_drag(touch_x, touch_y)
                            self.is_dragging = True
                        else:
                            delta = self.touch_start_y - touch_y
                            if abs(delta) > self.drag_threshold:
                                self.is_dragging = True
                                if self.current_view == 'Recipe':
                                    new_scroll = self.touch_start_scroll + delta
                                    self.scroll_offset = max(0, min(self.max_scroll, new_scroll))
                                elif self.current_view == 'Settings':
                                    settings = self.views['Settings']
                                    new_scroll = self.touch_start_scroll + delta
                                    settings.scroll_offset = max(0, min(settings.max_scroll, new_scroll))
                                elif self.current_view == 'Favorites':
                                    favorites = self.views['Favorites']
                                    new_scroll = self.touch_start_scroll + delta
                                    favorites.scroll_offset = max(0, min(favorites.max_scroll, new_scroll))
                                elif self.current_view == 'WiFi':
                                    wifi = self.views['WiFi']
                                    new_scroll = self.touch_start_scroll + delta
                                    wifi.scroll_offset = max(0, min(wifi.max_scroll, new_scroll))
                                elif self.current_view == 'Preferences':
                                    prefs = self.views['Preferences']
                                    new_scroll = self.touch_start_scroll + delta
                                    prefs.scroll_offset = max(0, min(prefs.max_scroll, new_scroll))

                elif event.type == pygame.FINGERUP:
                    touch_x = int(event.x * WIDTH)
                    touch_y = int(event.y * HEIGHT)
                    
                    if self.current_view == 'Settings':
                        self.views['Settings'].handle_drag_end()
                    
                    if not self.is_dragging:
                        self.handle_touch((touch_x, touch_y))
                    
                    self.touch_start_y = None
                    self.touch_start_x = None
                    self.is_dragging = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            # Draw
            self.screen.fill(WHITE)

            state = self._get_state()
            view = self.views.get(self.current_view)
            
            if view:
                if self.current_view == 'Recipe':
                    new_max = view.draw(self.screen, state, self.keyboard.visible)
                    if new_max is not None:
                        self.max_scroll = new_max
                elif self.current_view in ('Search', 'Create', 'Settings', 'WiFi', 'Preferences', 
                                        'SkillLevel', 'Favorites', 'SavedRecipes', 'MealPrep', 'GroceryList'):
                    view.draw(self.screen, state, self.keyboard.visible)
                else:
                    view.draw(self.screen, state)

            self.keyboard.draw()

            if not self.keyboard.visible:
                self.navbar.draw()

            if self.loading:
                self._draw_loading()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def _handle_scroll(self, delta):
        if self.current_view == 'Settings':
            self.views['Settings'].handle_scroll(delta)
        elif self.current_view == 'Favorites':
            self.views['Favorites'].handle_scroll(delta)
        elif self.current_view == 'WiFi':
            self.views['WiFi'].handle_scroll(delta)
        elif self.current_view == 'Preferences':
            self.views['Preferences'].handle_scroll(delta)
        elif self.current_view == 'SavedRecipes':
            self.views['SavedRecipes'].handle_scroll(delta)
        elif self.current_view == 'MealPrep':
            self.views['MealPrep'].handle_scroll(delta)
        elif self.current_view == 'GroceryList':
            self.views['GroceryList'].handle_scroll(delta)
        elif self.current_view == 'Recipe':
            self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset + delta))

    def _check_slider_start(self, pos):
        settings = self.views['Settings']
        x, y = pos
        content_y = y - 80 + settings.scroll_offset
        
        item_y = 10
        for section in settings.sections:
            item_y += 35 + 5
            
            for item in section['items']:
                if item['type'] == 'slider':
                    slider_x = WIDTH - 80 - 150 + 20
                    slider_y = item_y + 8
                    
                    if (slider_x - 20 <= x <= slider_x + 170 and 
                        item_y <= content_y <= item_y + 60):
                        settings.dragging_slider = item
                        settings.handle_drag(x, y)
                        return
                item_y += 70
            
            item_y += 20