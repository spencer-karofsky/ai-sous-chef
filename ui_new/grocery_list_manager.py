"""
ui_new/grocery_list_manager.py

Description:
    * Manager for grocery lists - generates and stores shopping lists

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import uuid


class GroceryListManager:
    """Manages grocery lists - generation, storage, and checking off items."""
    
    # Common categories for organizing grocery items
    CATEGORIES = [
        'Produce',
        'Meat & Seafood', 
        'Dairy & Eggs',
        'Bakery',
        'Pantry',
        'Frozen',
        'Beverages',
        'Other'
    ]
    
    def __init__(self, bedrock_manager=None):
        self.data_dir = Path.home() / '.ai-sous-chef' / 'grocery_lists'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.data_dir / 'index.json'
        self.bedrock = bedrock_manager  # This is the BedrockManager from infra/managers
        self.lists = self._load_index()
    
    def _load_index(self) -> List[Dict]:
        """Load grocery list index."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return []
    
    def _save_index(self):
        """Save grocery list index."""
        with open(self.index_file, 'w') as f:
            json.dump(self.lists, f, indent=2)
    
    def _save_list(self, list_id: str, data: Dict):
        """Save a grocery list to file."""
        list_file = self.data_dir / f'{list_id}.json'
        with open(list_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_list(self, list_id: str) -> Optional[Dict]:
        """Load a grocery list from file."""
        list_file = self.data_dir / f'{list_id}.json'
        if list_file.exists():
            try:
                with open(list_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return None
    
    def generate_from_meals(self, meals: List[Dict], week_label: str = "") -> Optional[str]:
        """
        Generate a grocery list from meal plan using AI to aggregate ingredients.
        
        Args:
            meals: List of meal dicts with 'ingredients' lists
            week_label: Optional label for the list
            
        Returns:
            List ID if successful, None otherwise
        """
        if not meals:
            return None
        
        # Collect all ingredients
        all_ingredients = []
        recipe_names = []
        for meal in meals:
            ingredients = meal.get('ingredients', [])
            all_ingredients.extend(ingredients)
            recipe_names.append(meal.get('name', 'Unknown'))
        
        if not all_ingredients:
            return None
        
        # Use AI to aggregate and categorize
        if self.bedrock:
            categorized = self._ai_aggregate_ingredients(all_ingredients)
        else:
            # Fallback: simple grouping without AI
            categorized = self._simple_aggregate(all_ingredients)
        
        # Create the grocery list
        list_id = str(uuid.uuid4())[:8]
        
        grocery_list = {
            'id': list_id,
            'name': week_label or f"Grocery List - {datetime.now().strftime('%b %d')}",
            'created_at': datetime.now().isoformat(),
            'recipes': recipe_names,
            'categories': categorized,
            'checked_items': []  # Track checked off items
        }
        
        # Save to file
        self._save_list(list_id, grocery_list)
        
        # Add to index
        self.lists.insert(0, {
            'id': list_id,
            'name': grocery_list['name'],
            'created_at': grocery_list['created_at'],
            'item_count': sum(len(items) for items in categorized.values()),
            'recipe_count': len(recipe_names)
        })
        self._save_index()
        
        return list_id
    
    def _ai_aggregate_ingredients(self, ingredients: List[str]) -> Dict[str, List[Dict]]:
        """Use AI to combine similar ingredients and categorize them."""
        
        system_prompt = """You are a grocery list organizer. Given a list of recipe ingredients:
1. Combine similar items (e.g., "1 cup flour" + "2 cups flour" = "3 cups flour")
2. Categorize into grocery store sections
3. Return ONLY valid JSON in this format:
{
    "Produce": [{"item": "onions", "quantity": "2 medium"}],
    "Meat & Seafood": [{"item": "chicken breast", "quantity": "2 lbs"}],
    "Dairy & Eggs": [{"item": "eggs", "quantity": "6 large"}],
    "Bakery": [],
    "Pantry": [{"item": "flour", "quantity": "3 cups"}],
    "Frozen": [],
    "Beverages": [],
    "Other": []
}
Be smart about combining - "2 cloves garlic" + "3 cloves garlic" = "5 cloves garlic".
Round up quantities when combining."""

        prompt = f"Organize this ingredient list for shopping:\n" + "\n".join(f"- {ing}" for ing in ingredients)
        
        try:
            response = self.bedrock.invoke_model_with_system(
                prompt=prompt,
                system_prompt=system_prompt,
                model_id=self.bedrock.models_dict['claude-haiku-3'],
                max_tokens=1024,
                temperature=0.2
            )
            
            if response:
                result = json.loads(response.strip())
                # Ensure all categories exist
                for cat in self.CATEGORIES:
                    if cat not in result:
                        result[cat] = []
                return result
        except (json.JSONDecodeError, Exception) as e:
            print(f"AI aggregation failed: {e}")
        
        return self._simple_aggregate(ingredients)
    
    def _simple_aggregate(self, ingredients: List[str]) -> Dict[str, List[Dict]]:
        """Simple fallback aggregation without AI."""
        categorized = {cat: [] for cat in self.CATEGORIES}
        
        # Simple keyword-based categorization
        produce_keywords = ['onion', 'garlic', 'tomato', 'lettuce', 'carrot', 'potato', 'pepper', 
                          'celery', 'broccoli', 'spinach', 'lemon', 'lime', 'apple', 'banana']
        meat_keywords = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'shrimp', 'turkey', 'bacon', 'sausage']
        dairy_keywords = ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'egg', 'sour cream']
        pantry_keywords = ['flour', 'sugar', 'salt', 'oil', 'vinegar', 'sauce', 'pasta', 'rice', 
                         'beans', 'spice', 'pepper', 'cinnamon', 'vanilla']
        
        seen = set()
        for ing in ingredients:
            ing_lower = ing.lower()
            if ing_lower in seen:
                continue
            seen.add(ing_lower)
            
            item = {'item': ing, 'quantity': ''}
            
            if any(kw in ing_lower for kw in produce_keywords):
                categorized['Produce'].append(item)
            elif any(kw in ing_lower for kw in meat_keywords):
                categorized['Meat & Seafood'].append(item)
            elif any(kw in ing_lower for kw in dairy_keywords):
                categorized['Dairy & Eggs'].append(item)
            elif any(kw in ing_lower for kw in pantry_keywords):
                categorized['Pantry'].append(item)
            else:
                categorized['Other'].append(item)
        
        return categorized
    
    def get_all_lists(self) -> List[Dict]:
        """Get all grocery list metadata."""
        return self.lists
    
    def get_list(self, list_id: str) -> Optional[Dict]:
        """Get full grocery list by ID."""
        return self._load_list(list_id)
    
    def toggle_item(self, list_id: str, category: str, item_index: int) -> bool:
        """Toggle an item's checked status."""
        grocery_list = self._load_list(list_id)
        if not grocery_list:
            return False
        
        # Create a unique key for the item
        item_key = f"{category}:{item_index}"
        
        checked = grocery_list.get('checked_items', [])
        if item_key in checked:
            checked.remove(item_key)
        else:
            checked.append(item_key)
        
        grocery_list['checked_items'] = checked
        self._save_list(list_id, grocery_list)
        return True
    
    def is_checked(self, grocery_list: Dict, category: str, item_index: int) -> bool:
        """Check if an item is checked off."""
        item_key = f"{category}:{item_index}"
        return item_key in grocery_list.get('checked_items', [])
    
    def delete_list(self, list_id: str):
        """Delete a grocery list."""
        # Remove from index
        self.lists = [l for l in self.lists if l['id'] != list_id]
        self._save_index()
        
        # Delete file
        list_file = self.data_dir / f'{list_id}.json'
        if list_file.exists():
            list_file.unlink()
    
    def get_checked_count(self, grocery_list: Dict) -> tuple:
        """Get (checked_count, total_count) for a grocery list."""
        total = sum(len(items) for items in grocery_list.get('categories', {}).values())
        checked = len(grocery_list.get('checked_items', []))
        return checked, total