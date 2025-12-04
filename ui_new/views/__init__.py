"""
ui_new/views/__init__.py
"""
from ui_new.views.home_view import HomeView
from ui_new.views.search_view import SearchView
from ui_new.views.create_view import CreateView
from ui_new.views.recipe_view import RecipeView
from ui_new.views.favorites_view import FavoritesView
from ui_new.views.settings_view import SettingsView
from ui_new.views.wifi_view import WiFiView

__all__ = [
    'HomeView',
    'SearchView', 
    'CreateView',
    'RecipeView',
    'FavoritesView',
    'SettingsView',
    'WiFiView',
]