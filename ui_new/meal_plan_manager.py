"""
ui_new/meal_plan_manager.py

Description:
    * Manager for meal planning - AI generation and storage
    * Two-phase approach: generate plan outline, then hydrate recipes on-demand

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class MealPlanManager:
    """Manages weekly meal plans with AI generation."""
    
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    MEAL_TYPES = ['Breakfast', 'Lunch', 'Dinner']
    
    def __init__(self, bedrock_manager=None):
        self.data_dir = Path.home() / '.ai-sous-chef' / 'meal_plans'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.current_week_file = self.data_dir / 'current_week.json'
        self.bedrock = bedrock_manager
        self.plan = self._load()
    
    def set_bedrock(self, bedrock_manager):
        """Set bedrock manager after init."""
        self.bedrock = bedrock_manager
    
    def _load(self) -> Dict:
        """Load current meal plan."""
        if self.current_week_file.exists():
            try:
                with open(self.current_week_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._create_empty_week()
    
    def _save(self):
        """Save current meal plan."""
        with open(self.current_week_file, 'w') as f:
            json.dump(self.plan, f, indent=2)
    
    def _create_empty_week(self) -> Dict:
        """Create empty week structure starting from Monday."""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        
        week = {
            'week_start': monday.strftime('%Y-%m-%d'),
            'days': {}
        }
        
        for i, day_name in enumerate(self.DAYS):
            date = monday + timedelta(days=i)
            week['days'][day_name] = {
                'date': date.strftime('%Y-%m-%d'),
                'meals': {
                    'Breakfast': None,
                    'Lunch': None,
                    'Dinner': None
                }
            }
        
        return week
    
    def generate_meal_plan(self, user_prompt: str, dietary_prefs: List[str] = None, 
                          exclusions: List[str] = None, skill_level: str = "Beginner") -> bool:
        """
        Generate a weekly meal plan outline (names only, no full recipes).
        
        Args:
            user_prompt: User's description of what they want
            dietary_prefs: List of dietary preferences
            exclusions: List of ingredients to exclude
            skill_level: Cooking skill level
            
        Returns:
            True if successful, False otherwise
        """
        print(f"[MealPlan] Starting generation with prompt: {user_prompt}")
        
        if not self.bedrock:
            print("[MealPlan] ERROR: No bedrock manager available")
            return False
        
        # Build context
        context_parts = []
        if dietary_prefs:
            context_parts.append(f"Dietary preferences: {', '.join(dietary_prefs)}")
        if exclusions:
            context_parts.append(f"Exclude these ingredients: {', '.join(exclusions)}")
        context_parts.append(f"Cooking skill level: {skill_level}")
        context = "\n".join(context_parts)
        
        system_prompt = """You are a professional meal planner. Generate a weekly meal plan with descriptive recipe names.

Return ONLY valid JSON in this exact format:
{
    "Monday": {
        "Breakfast": "Descriptive Recipe Name",
        "Lunch": "Descriptive Recipe Name", 
        "Dinner": "Descriptive Recipe Name"
    },
    "Tuesday": {...},
    ...for all 7 days
}

Guidelines:
- Recipe names should be descriptive enough to recreate (e.g., "Garlic Herb Grilled Chicken with Roasted Vegetables" not just "Chicken")
- Include key ingredients or cooking method in the name
- Breakfast should be quick options
- Vary meals throughout the week - no repeats
- Consider ingredient reuse across days (e.g., if using chicken Monday, use it again Wednesday)
- Match the user's dietary requirements exactly"""

        prompt = f"""Create a weekly meal plan based on this request:

User request: {user_prompt}

{context}

Generate descriptive recipe names for Breakfast, Lunch, and Dinner for all 7 days (Monday through Sunday)."""

        try:
            print("[MealPlan] Calling Bedrock API for plan outline...")
            response = self.bedrock.invoke_model_with_system(
                prompt=prompt,
                system_prompt=system_prompt,
                model_id=self.bedrock.models_dict['claude-haiku-3'],
                max_tokens=1500,  # Plenty for just names
                temperature=0.7
            )
            
            if not response:
                print("[MealPlan] ERROR: Empty response from Bedrock")
                return False
            
            print(f"[MealPlan] Got response: {response[:300]}...")
            
            # Parse the response
            meal_plan_data = json.loads(response.strip())
            
            # Update plan with recipe names (no full recipe data yet)
            for day_name in self.DAYS:
                if day_name in meal_plan_data:
                    day_meals = meal_plan_data[day_name]
                    for meal_type in self.MEAL_TYPES:
                        if meal_type in day_meals and day_meals[meal_type]:
                            recipe_name = day_meals[meal_type]
                            self.plan['days'][day_name]['meals'][meal_type] = {
                                'name': recipe_name,
                                'hydrated': False  # Flag: full recipe not yet generated
                            }
            
            self._save()
            print(f"[MealPlan] SUCCESS: Planned {self.get_meal_count()} meals")
            return True
            
        except json.JSONDecodeError as e:
            print(f"[MealPlan] ERROR: Failed to parse JSON: {e}")
            print(f"[MealPlan] Response was: {response[:500] if response else 'None'}...")
            return False
        except Exception as e:
            print(f"[MealPlan] ERROR: {type(e).__name__}: {e}")
            return False
    
    def hydrate_recipe(self, day_name: str, meal_type: str) -> Optional[Dict]:
        """
        Generate full recipe details for a specific meal slot.
        Call this when user taps on a meal to view it.
        
        Args:
            day_name: Day of the week
            meal_type: Breakfast, Lunch, or Dinner
            
        Returns:
            Full recipe dict, or None if failed
        """
        if not self.bedrock:
            return None
        
        meal = self.plan.get('days', {}).get(day_name, {}).get('meals', {}).get(meal_type)
        if not meal:
            return None
        
        # Already hydrated? Return cached recipe
        if meal.get('hydrated') and meal.get('recipe_data'):
            return meal['recipe_data']
        
        recipe_name = meal.get('name', '')
        if not recipe_name:
            return None
        
        print(f"[MealPlan] Hydrating recipe: {recipe_name}")
        
        system_prompt = """You are a professional chef. Create a complete recipe based on the given name.

Return ONLY valid JSON:
{
    "name": "Recipe Name",
    "description": "Brief 1-2 sentence description",
    "prep_time": "X minutes",
    "cook_time": "X minutes",
    "total_time": "X minutes",
    "servings": "X servings",
    "ingredients": ["1 cup ingredient", "2 tbsp ingredient", ...],
    "instructions": ["Step 1...", "Step 2...", ...],
    "nutrition": {"calories": "XXX", "protein": "XXg", "carbs": "XXg", "fat": "XXg"}
}

Create a practical, delicious recipe with 4-8 ingredients and clear instructions."""

        prompt = f"Create a complete recipe for: {recipe_name}"
        
        try:
            response = self.bedrock.invoke_model_with_system(
                prompt=prompt,
                system_prompt=system_prompt,
                model_id=self.bedrock.models_dict['claude-haiku-3'],
                max_tokens=1500,
                temperature=0.4
            )
            
            if not response:
                return None
            
            recipe_data = json.loads(response.strip())
            
            # Update the meal slot with full recipe
            self.plan['days'][day_name]['meals'][meal_type] = {
                'name': recipe_data.get('name', recipe_name),
                'description': recipe_data.get('description', ''),
                'prep_time': recipe_data.get('prep_time', ''),
                'cook_time': recipe_data.get('cook_time', ''),
                'total_time': recipe_data.get('total_time', ''),
                'servings': recipe_data.get('servings', ''),
                'ingredients': recipe_data.get('ingredients', []),
                'instructions': recipe_data.get('instructions', []),
                'nutrition': recipe_data.get('nutrition', {}),
                'recipe_data': recipe_data,
                'hydrated': True
            }
            
            self._save()
            print(f"[MealPlan] Hydrated: {recipe_name}")
            return recipe_data
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"[MealPlan] ERROR hydrating recipe: {e}")
            return None
    
    def get_week_start(self) -> str:
        """Get the start date of current week."""
        return self.plan.get('week_start', '')
    
    def get_day(self, day_name: str) -> Optional[Dict]:
        """Get meals for a specific day."""
        return self.plan.get('days', {}).get(day_name)
    
    def get_all_days(self) -> Dict:
        """Get all days in the plan."""
        return self.plan.get('days', {})
    
    def get_meal(self, day_name: str, meal_type: str) -> Optional[Dict]:
        """Get a specific meal."""
        return self.plan.get('days', {}).get(day_name, {}).get('meals', {}).get(meal_type)
    
    def is_hydrated(self, day_name: str, meal_type: str) -> bool:
        """Check if a meal has full recipe data."""
        meal = self.get_meal(day_name, meal_type)
        return meal.get('hydrated', False) if meal else False
    
    def set_meal(self, day_name: str, meal_type: str, recipe: Optional[Dict]):
        """Manually assign a recipe to a meal slot."""
        if day_name not in self.plan['days']:
            return
        if meal_type not in self.MEAL_TYPES:
            return
        
        if recipe:
            self.plan['days'][day_name]['meals'][meal_type] = {
                'name': recipe.get('name', 'Unknown'),
                'description': recipe.get('description', ''),
                'servings': recipe.get('servings', ''),
                'ingredients': recipe.get('ingredients', []),
                'total_time': recipe.get('total_time', ''),
                'recipe_data': recipe,
                'hydrated': True
            }
        else:
            self.plan['days'][day_name]['meals'][meal_type] = None
        
        self._save()
    
    def clear_meal(self, day_name: str, meal_type: str):
        """Remove a meal from a slot."""
        self.set_meal(day_name, meal_type, None)
    
    def clear_day(self, day_name: str):
        """Clear all meals for a day."""
        for meal_type in self.MEAL_TYPES:
            self.clear_meal(day_name, meal_type)
    
    def clear_week(self):
        """Clear all meals and reset to empty week."""
        self.plan = self._create_empty_week()
        self._save()
    
    def get_all_meals(self) -> List[Dict]:
        """Get all assigned meals for the week (for grocery list generation)."""
        meals = []
        for day_name, day_data in self.plan.get('days', {}).items():
            for meal_type, meal in day_data.get('meals', {}).items():
                if meal:
                    meals.append({
                        'day': day_name,
                        'meal_type': meal_type,
                        'name': meal.get('name'),
                        'ingredients': meal.get('ingredients', []),
                        'servings': meal.get('servings', ''),
                        'hydrated': meal.get('hydrated', False)
                    })
        return meals
    
    def get_all_ingredients(self) -> List[str]:
        """Get all ingredients from hydrated meals (for grocery list)."""
        ingredients = []
        for meal in self.get_all_meals():
            if meal.get('hydrated'):
                ingredients.extend(meal.get('ingredients', []))
        return ingredients
    
    def get_meal_count(self) -> int:
        """Count how many meals are planned."""
        count = 0
        for day_data in self.plan.get('days', {}).values():
            for meal in day_data.get('meals', {}).values():
                if meal:
                    count += 1
        return count
    
    def get_hydrated_count(self) -> int:
        """Count how many meals have full recipes."""
        count = 0
        for day_data in self.plan.get('days', {}).values():
            for meal in day_data.get('meals', {}).values():
                if meal and meal.get('hydrated'):
                    count += 1
        return count
    
    def hydrate_all(self) -> int:
        """Hydrate all meals (useful before generating grocery list)."""
        hydrated = 0
        for day_name in self.DAYS:
            for meal_type in self.MEAL_TYPES:
                meal = self.get_meal(day_name, meal_type)
                if meal and not meal.get('hydrated'):
                    if self.hydrate_recipe(day_name, meal_type):
                        hydrated += 1
        return hydrated
    
    def new_week(self):
        """Start a fresh week."""
        self.plan = self._create_empty_week()
        self._save()