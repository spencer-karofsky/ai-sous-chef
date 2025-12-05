"""
ui_new/saved_recipes_manager.py

Description:
    * Manager for locally saved AI-generated recipes

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import json
import uuid
from pathlib import Path
from datetime import datetime


class SavedRecipesManager:
    """Manages locally saved AI-generated recipes."""
    
    def __init__(self):
        self.data_dir = Path.home() / '.ai-sous-chef' / 'saved_recipes'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.data_dir / 'index.json'
        self.recipes = self._load_index()
    
    def _load_index(self):
        """Load the recipe index."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save_index(self):
        """Save the recipe index."""
        with open(self.index_file, 'w') as f:
            json.dump(self.recipes, f, indent=2)
    
    def _save_recipe_file(self, recipe_id, recipe_data):
        """Save individual recipe to file."""
        recipe_file = self.data_dir / f'{recipe_id}.json'
        with open(recipe_file, 'w') as f:
            json.dump(recipe_data, f, indent=2)
    
    def _load_recipe_file(self, recipe_id):
        """Load individual recipe from file."""
        recipe_file = self.data_dir / f'{recipe_id}.json'
        if recipe_file.exists():
            try:
                with open(recipe_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None
    
    def _delete_recipe_file(self, recipe_id):
        """Delete individual recipe file."""
        recipe_file = self.data_dir / f'{recipe_id}.json'
        if recipe_file.exists():
            recipe_file.unlink()
    
    def add(self, recipe_data):
        """Add a new saved recipe."""
        recipe_id = str(uuid.uuid4())[:8]
        
        entry = {
            'id': recipe_id,
            'name': recipe_data.get('name', 'Untitled Recipe'),
            'created_at': datetime.now().isoformat(),
            'description': recipe_data.get('description', '')[:100],
        }
        
        # Save full recipe data to separate file
        self._save_recipe_file(recipe_id, recipe_data)
        
        # Add to index
        self.recipes.insert(0, entry)
        self._save_index()
        
        return recipe_id
    
    def get_all(self):
        """Get all saved recipe entries (index only, not full data)."""
        return self.recipes
    
    def get_by_id(self, recipe_id):
        """Get full recipe data by ID."""
        return self._load_recipe_file(recipe_id)
    
    def get_entry_by_id(self, recipe_id):
        """Get index entry by ID."""
        for entry in self.recipes:
            if entry['id'] == recipe_id:
                return entry
        return None
    
    def remove(self, recipe_id):
        """Remove a saved recipe."""
        self.recipes = [r for r in self.recipes if r['id'] != recipe_id]
        self._delete_recipe_file(recipe_id)
        self._save_index()
    
    def exists(self, recipe_name):
        """Check if a recipe with this name exists."""
        for entry in self.recipes:
            if entry['name'] == recipe_name:
                return True
        return False
    
    def clear_all(self):
        """Remove all saved recipes."""
        for entry in self.recipes:
            self._delete_recipe_file(entry['id'])
        self.recipes = []
        self._save_index()