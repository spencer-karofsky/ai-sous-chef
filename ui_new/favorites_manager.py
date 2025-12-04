"""
ui_new/favorites_manager.py

Description:
    * Manages favorite recipes - save, load, delete

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import json
import uuid
from pathlib import Path
from datetime import datetime


class FavoritesManager:
    """Manages favorite recipes persistence."""
    
    def __init__(self):
        self.config_dir = Path.home() / '.ai-sous-chef'
        self.favorites_file = self.config_dir / 'favorites.json'
        
        self.config_dir.mkdir(exist_ok=True)
        self.favorites = self._load()
    
    def _load(self):
        if self.favorites_file.exists():
            try:
                with open(self.favorites_file, 'r') as f:
                    data = json.load(f)
                    return data.get('favorites', [])
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save(self):
        with open(self.favorites_file, 'w') as f:
            json.dump({'favorites': self.favorites}, f, indent=2)
    
    def add(self, recipe, source='search', s3_key=None):
        """Add a recipe to favorites."""
        # Check if already exists
        if self.is_favorite(recipe.get('name')):
            return None
        
        favorite = {
            'id': str(uuid.uuid4()),
            'name': recipe.get('name', 'Untitled'),
            'category': recipe.get('category', ''),
            'calories': recipe.get('nutrition', {}).get('calories') or recipe.get('calories'),
            'total_time': recipe.get('total_time', ''),
            'servings': recipe.get('servings', ''),
            'saved_at': datetime.now().isoformat(),
            'source': source,
        }
        
        if source == 'search' and s3_key:
            favorite['s3_key'] = s3_key
        else:
            # Store full recipe for generated recipes
            favorite['recipe_data'] = recipe
        
        self.favorites.insert(0, favorite)  # Add to beginning
        self._save()
        return favorite['id']
    
    def remove(self, favorite_id):
        """Remove a recipe from favorites by ID."""
        self.favorites = [f for f in self.favorites if f['id'] != favorite_id]
        self._save()
    
    def remove_by_name(self, name):
        """Remove a recipe from favorites by name."""
        self.favorites = [f for f in self.favorites if f['name'] != name]
        self._save()
    
    def get_all(self):
        """Get all favorites."""
        return self.favorites
    
    def get_by_id(self, favorite_id):
        """Get a specific favorite by ID."""
        for fav in self.favorites:
            if fav['id'] == favorite_id:
                return fav
        return None
    
    def is_favorite(self, recipe_name):
        """Check if a recipe is in favorites."""
        return any(f['name'] == recipe_name for f in self.favorites)
    
    def get_favorite_id(self, recipe_name):
        """Get the favorite ID for a recipe name."""
        for fav in self.favorites:
            if fav['name'] == recipe_name:
                return fav['id']
        return None
    
    def count(self):
        """Get number of favorites."""
        return len(self.favorites)