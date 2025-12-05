"""
ui_new/views/__init__.py
"""
from .home_view import HomeView
from .search_view import SearchView
from .create_view import CreateView
from .recipe_view import RecipeView
from .favorites_view import FavoritesView
from .settings_view import SettingsView
from .wifi_view import WiFiView
from .preferences_view import PreferencesView
from .skill_level_view import SkillLevelView
from .my_kitchen_view import MyKitchenView
from .saved_recipes_view import SavedRecipesView
from .meal_prep_view import MealPrepView
from .grocery_list_view import GroceryListView

__all__ = [
    'HomeView',
    'SearchView', 
    'CreateView',
    'RecipeView',
    'FavoritesView',
    'SettingsView',
    'WiFiView',
    'PreferencesView',
    'SkillLevelView',
    'MyKitchenView',
    'SavedRecipesView',
    'MealPrepView',
    'GroceryListView',
]