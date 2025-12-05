"""
ui_new/meal_plan_manager.py

Description:
    * Manager for meal planning - AI generation and storage

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
        Generate a complete weekly meal plan using AI.
        
        Args:
            user_prompt: User's description of what they want
            dietary_prefs: List of dietary preferences (e.g., ['vegetarian', 'low-carb'])
            exclusions: List of ingredients to exclude
            skill_level: Cooking skill level
            
        Returns:
            True if successful, False otherwise
        """
        print(f"[MealPlan] Starting generation with prompt: {user_prompt}")
        print(f"[MealPlan] Dietary: {dietary_prefs}, Exclusions: {exclusions}, Skill: {skill_level}")
        print(f"[MealPlan] Bedrock manager: {self.bedrock}")
        
        if not self.bedrock:
            print("[MealPlan] ERROR: No bedrock manager available")
            return False
        
        # Build context from preferences
        context_parts = []
        if dietary_prefs:
            context_parts.append(f"Dietary preferences: {', '.join(dietary_prefs)}")
        if exclusions:
            context_parts.append(f"Exclude these ingredients: {', '.join(exclusions)}")
        context_parts.append(f"Cooking skill level: {skill_level}")
        
        context = "\n".join(context_parts)
        
        system_prompt = """You are a professional meal planner and chef. Generate a complete weekly meal plan.

Return ONLY valid JSON in this exact format:
{
    "Monday": {
        "Breakfast": {"name": "...", "description": "...", "prep_time": "...", "cook_time": "...", "total_time": "...", "servings": "...", "ingredients": ["..."], "instructions": ["..."], "nutrition": {"calories": "...", "protein": "...", "carbs": "...", "fat": "..."}},
        "Lunch": {...},
        "Dinner": {...}
    },
    "Tuesday": {...},
    ...for all 7 days
}

Guidelines:
- Create practical, delicious recipes that match the user's request
- Vary the meals throughout the week (don't repeat the same dish)
- Consider ingredient reuse to minimize waste (e.g., if buying chicken, use it in multiple meals)
- Breakfast should be quick and easy
- Include prep_time, cook_time as human readable (e.g., "15 minutes")
- Include realistic nutrition estimates
- Each recipe should have 4-8 ingredients and clear instructions"""

        prompt = f"""Create a weekly meal plan based on this request:

User request: {user_prompt}

{context}

Generate complete recipes for Breakfast, Lunch, and Dinner for all 7 days (Monday through Sunday)."""

        try:
            print("[MealPlan] Calling Bedrock API...")
            response = self.bedrock.invoke_model_with_system(
                prompt=prompt,
                system_prompt=system_prompt,
                model_id=self.bedrock.models_dict['claude-haiku-3'],
                max_tokens=8000,
                temperature=0.7
            )
            
            print(f"[MealPlan] Got response: {response[:200] if response else 'None'}...")
            
            if not response:
                print("[MealPlan] ERROR: Empty response from Bedrock")
                return False
            
            # Parse the response
            meal_plan_data = json.loads(response.strip())
            
            # Update our plan with the generated meals
            for day_name in self.DAYS:
                if day_name in meal_plan_data:
                    day_meals = meal_plan_data[day_name]
                    for meal_type in self.MEAL_TYPES:
                        if meal_type in day_meals and day_meals[meal_type]:
                            recipe = day_meals[meal_type]
                            self.plan['days'][day_name]['meals'][meal_type] = {
                                'name': recipe.get('name', 'Untitled'),
                                'description': recipe.get('description', ''),
                                'prep_time': recipe.get('prep_time', ''),
                                'cook_time': recipe.get('cook_time', ''),
                                'total_time': recipe.get('total_time', ''),
                                'servings': recipe.get('servings', ''),
                                'ingredients': recipe.get('ingredients', []),
                                'instructions': recipe.get('instructions', []),
                                'nutrition': recipe.get('nutrition', {}),
                                'recipe_data': recipe  # Store full recipe
                            }
            
            self._save()
            print(f"[MealPlan] SUCCESS: Saved {self.get_meal_count()} meals")
            return True
            
        except json.JSONDecodeError as e:
            print(f"[MealPlan] ERROR: Failed to parse JSON: {e}")
            print(f"[MealPlan] Response was: {response[:500] if response else 'None'}...")
            return False
        except Exception as e:
            print(f"[MealPlan] ERROR: {type(e).__name__}: {e}")
            return False
    
    def get_week_start(self) -> str:
        """Get the start date of current week."""
        return self.plan.get('week_start', '')
    
    def get_day(self, day_name: str) -> Optional[Dict]:
        """Get meals for a specific day."""
        return self.plan.get('days', {}).get(day_name)
    
    def get_all_days(self) -> Dict:
        """Get all days in the plan."""
        return self.plan.get('days', {})
    
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
                'recipe_data': recipe
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
                    })
        return meals
    
    def get_all_ingredients(self) -> List[str]:
        """Get all ingredients from all meals (for grocery list)."""
        ingredients = []
        for meal in self.get_all_meals():
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
    
    def new_week(self):
        """Start a fresh week."""
        self.plan = self._create_empty_week()
        self._save()