"""
logic/prompting.py

Description:
    * Recipe prompting logic for AI Sous Chef
    * Handles search param extraction, recipe formatting, generation, and conversation

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
from infra.managers.bedrock_manager import BedrockManager
from infra.config import AWS_RESOURCES
from botocore.client import BaseClient
from typing import Optional, List, Dict
import json


# Standard recipe schema all recipes must conform to
RECIPE_SCHEMA = {
    "name": "string (max 40 characters, concise and descriptive)",
    "description": "string (1-2 sentences)",
    "prep_time": "string (e.g., '15 minutes')",
    "cook_time": "string (e.g., '30 minutes')", 
    "total_time": "string (e.g., '45 minutes')",
    "servings": "integer",
    "ingredients": [
        {
            "quantity": "string (e.g., '2', '1/2', '1 1/4')",
            "unit": "string (e.g., 'cup', 'tablespoon', 'pound', 'piece')",
            "item": "string (e.g., 'all-purpose flour')",
            "notes": "string or null (e.g., 'diced', 'at room temperature')"
        }
    ],
    "instructions": ["string (complete sentence for each step)"],
    "nutrition": {
        "calories": "integer",
        "protein": "string (e.g., '25g')",
        "carbs": "string (e.g., '30g')",
        "fat": "string (e.g., '12g')"
    },
    "tags": ["string (e.g., 'vegetarian', 'quick', 'gluten-free')"]
}

UNIT_STANDARDIZATION = """
Standardize all units as follows:
- Volume: teaspoon, tablespoon, cup, fluid ounce, pint, quart, gallon, milliliter, liter
- Weight: ounce, pound, gram, kilogram
- Count: piece, slice, clove, sprig, bunch, head
- Size descriptors: small, medium, large (for items like "1 large onion")

Convert ambiguous quantities:
- "4 salts" -> "4 teaspoons salt" or "to taste" depending on context
- "a pinch" -> "1/8 teaspoon"
- "a dash" -> "1/8 teaspoon"
- "a handful" -> estimate in cups or pieces
- Numeric only (e.g., "2 eggs") -> quantity: "2", unit: "large", item: "eggs"

If a quantity is truly unclear, use your best judgment to make it cookable.
"""


class RecipePrompter:
    def __init__(self, client: BaseClient) -> None:
        """
        Initialize the RecipePrompter with a Bedrock client.
        
        Args:
            client: boto3 Bedrock Runtime client
        """
        self.bedrock = BedrockManager(client)
        self.current_recipe: Optional[Dict] = None
        self.conversation_history: List[Dict] = []
    
    def extract_search_params(self, user_query: str) -> Optional[Dict]:
        """
        Extract structured search parameters from natural language query.
        """
        system_prompt = """You extract structured search parameters from food requests.
Return ONLY valid JSON with these optional fields:
- keywords: list of ingredient/dish/cuisine keywords (lowercase)
- category: one of Breakfast, Lunch, Dinner, Dessert, Snack, Appetizer
- max_calories: integer if user mentions diet/light/healthy
- max_total_time: ISO 8601 duration if user mentions quick/fast (e.g. PT30M)

Example input: "quick healthy chicken dinner"
Example output: {"keywords": ["chicken"], "category": "Dinner", "max_calories": 500, "max_total_time": "PT30M"}"""

        response = self.bedrock.invoke_model_with_system(
            prompt=user_query,
            system_prompt=system_prompt,
            model_id=AWS_RESOURCES['bedrock_model_id_extract_search_params'],
            max_tokens=256,
            temperature=0.2
        )
        
        if not response:
            return None
            
        try:
            return json.loads(self._clean_json(response))
        except json.JSONDecodeError:
            return None
    
    def format_recipe(self, raw_recipe: Dict) -> Optional[Dict]:
        """
        Standardize a raw recipe into the canonical format.
        """
        system_prompt = f"""You are a recipe formatter for a cooking app. Your job is to take raw recipe data and output a clean, standardized JSON recipe.

CRITICAL: Output ONLY valid JSON. No markdown, no explanation, no extra text.

{UNIT_STANDARDIZATION}

Recipe Schema:
{json.dumps(RECIPE_SCHEMA, indent=2)}

Rules:
1. All fields are required. If data is missing, infer reasonable values.
2. Ingredients must have quantity, unit, item, and notes (null if none).
3. Instructions must be clear, numbered steps as complete sentences.
4. Times should be human-readable strings like "15 minutes" or "1 hour 30 minutes".
5. Nutrition values should be realistic estimates if not provided.
6. Description should be appetizing and 1-2 sentences max.
7. Tags should include relevant categories (cuisine, diet, meal type, difficulty).

INGREDIENT VALIDATION (CRITICAL):
- Cross-reference ingredients with the recipe name and instructions
- If the recipe name mentions a main ingredient (e.g., "Rib Eye Steak") but it's missing from ingredients, ADD IT with a reasonable quantity
- If nutrition seems impossibly low for the dish (e.g., 13 cal for a steak dinner), RECALCULATE based on actual ingredients
- Fix nonsensical quantities like "4 salts" or "1 medium fresh mushrooms"
- Ensure ingredient quantities make sense for the serving size"""

        response = self.bedrock.invoke_model_with_system(
            prompt=f"Format this recipe:\n{json.dumps(raw_recipe)}",
            system_prompt=system_prompt,
            model_id=AWS_RESOURCES['bedrock_model_id_format_recipe'],
            max_tokens=2048,
            temperature=0.3
        )
        
        if not response:
            return None
            
        try:
            recipe = json.loads(self._clean_json(response))
            self.current_recipe = recipe
            self.conversation_history = []
            return recipe
        except json.JSONDecodeError:
            return None
    
    def generate_recipe(self, user_request: str) -> Optional[Dict]:
        """
        Generate a new recipe based on user request.
        """
        system_prompt = f"""You are an expert chef creating recipes for a cooking app. Generate creative, delicious, and practical recipes.

CRITICAL: Output ONLY valid JSON. No markdown, no explanation, no extra text.

{UNIT_STANDARDIZATION}

Recipe Schema:
{json.dumps(RECIPE_SCHEMA, indent=2)}

Rules:
1. Create recipes that are practical for home cooks.
2. Use common ingredients when possible, noting substitutions in instruction notes.
3. Be precise with measurements - no vague quantities.
4. Instructions should be detailed enough for beginners.
5. Include realistic nutrition estimates.
6. Make the description appetizing and engaging."""

        response = self.bedrock.invoke_model_with_system(
            prompt=f"Create a recipe for: {user_request}",
            system_prompt=system_prompt,
            model_id=AWS_RESOURCES['bedrock_model_id_generate_recipe'],
            max_tokens=2048,
            temperature=0.7
        )
        
        if not response:
            return None
            
        try:
            recipe = json.loads(self._clean_json(response))
            self.current_recipe = recipe
            self.conversation_history = []
            return recipe
        except json.JSONDecodeError:
            return None
    
    def rank_recipes(self, user_query: str, recipes: List[Dict], top_n: int = 5) -> List[Dict]:
        """
        Rank recipes by relevance to user query.
        """
        if not recipes:
            return []
        
        if len(recipes) <= top_n:
            return recipes

        system_prompt = """You rank recipes by relevance to a user's request.
Given a user request and list of recipes, return the indices of the most relevant recipes in order of best match.
Return ONLY valid JSON: {"ranked_indices": [0, 3, 1, ...]}"""
        
        # Build condensed recipe list for ranking
        recipe_summaries = [
            f"{i}: {r.get('name', 'Unknown')} - {r.get('category', '')} - {r.get('calories', 'N/A')} cal"
            for i, r in enumerate(recipes[:50])
        ]
        
        prompt = f"User request: {user_query}\n\nRecipes:\n" + "\n".join(recipe_summaries) + f"\n\nReturn the indices of the top {top_n} most relevant recipes."
        
        response = self.bedrock.invoke_model_with_system(
            prompt=prompt,
            system_prompt=system_prompt,
            model_id=AWS_RESOURCES['bedrock_model_id_rank_recipes'],
            max_tokens=128,
            temperature=0.3
        )
        
        if not response:
            return recipes[:top_n]
            
        try:
            result = json.loads(self._clean_json(response))
            indices = result.get('ranked_indices', [])[:top_n]
            ranked = [recipes[i] for i in indices if i < len(recipes)]
            return ranked if ranked else recipes[:top_n]
        except (json.JSONDecodeError, IndexError, TypeError):
            return recipes[:top_n]
    
    def chat(self, user_message: str) -> tuple:
        """
        Handle follow-up requests to modify the current recipe.
        
        Only accepts modification requests. Rejects off-topic or question-only inputs.
        
        Returns:
            Tuple of (response_text, modified_recipe or None)
        """
        if not self.current_recipe:
            return "No recipe loaded. Search for a recipe first.", None
        
        system_prompt = f"""You are an AI sous chef that ONLY modifies recipes. You do not answer general questions.

TASK: Determine if the user is requesting a recipe modification. 

VALID modification requests (output modified recipe as JSON):
- Adjust servings/portions (e.g., "make it for 4 people", "double the recipe")
- Swap ingredients (e.g., "make it vegetarian", "substitute chicken for beef")
- Dietary adjustments (e.g., "make it gluten-free", "lower the sodium")
- Add/remove ingredients (e.g., "add garlic", "remove the onions")
- Change cooking method (e.g., "make it in an air fryer", "grill instead of bake")
- Adjust flavor profile (e.g., "make it spicier", "less sweet")

INVALID requests (output exactly "OFF_TOPIC"):
- General questions about cooking techniques
- Questions about the recipe without requesting changes
- Unrelated conversation
- Asking for nutrition advice without recipe changes
- Anything not directly modifying THIS recipe

CRITICAL RULES FOR MODIFICATIONS:
1. When scaling servings (double, triple, halve, etc.), you MUST scale ALL of these proportionally:
   - All ingredient quantities
   - Nutrition values (calories, protein, carbs, fat)
   - Update the servings count
2. When swapping ingredients, recalculate nutrition based on the new ingredients
3. Always output the COMPLETE recipe with ALL fields

If VALID: Output ONLY the complete modified recipe as JSON using this schema:
{json.dumps(RECIPE_SCHEMA, indent=2)}

If INVALID: Output exactly the string: OFF_TOPIC

Current recipe:
{json.dumps(self.current_recipe, indent=2)}
"""
        
        response = self.bedrock.invoke_model_with_system(
            prompt=user_message,
            system_prompt=system_prompt,
            model_id=AWS_RESOURCES['bedrock_model_id_generate_recipe'],
            max_tokens=2048,
            temperature=0.5
        )
        
        if not response:
            return "Sorry, I couldn't process that request.", None
        
        cleaned = self._clean_json(response)
        
        # Check if off-topic
        if cleaned.strip().upper() == "OFF_TOPIC":
            return "I can only modify recipes. Try something like 'make it vegetarian', 'double the servings', or 'make it spicier'. Type 'done' to search for a new recipe.", None
        
        # Try to parse as modified recipe
        try:
            modified_recipe = json.loads(cleaned)
            if isinstance(modified_recipe, dict) and 'name' in modified_recipe:
                self.current_recipe = modified_recipe
                return "Here's the modified recipe:", modified_recipe
        except json.JSONDecodeError:
            pass
        
        return "I couldn't understand that modification. Try something like 'make it for 6 servings' or 'substitute tofu for chicken'. Type 'done' to search for a new recipe.", None
    
    def clear_conversation(self) -> None:
        """Reset conversation state for a new recipe search."""
        self.current_recipe = None
        self.conversation_history = []
    
    def _clean_json(self, text: str) -> str:
        """Remove markdown code fences and extra whitespace from JSON response."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()