"""
recipe_search.py

Description:
    * Interactive recipe search using AI

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import boto3
import json

from logic.prompting import RecipePrompter
from infra.managers.dynamodb_manager import DynamoDBItemManager
from infra.managers.s3_manager import S3ObjectManager
from infra.config import AWS_RESOURCES


def _print_recipe(recipe: dict) -> None:
    """Pretty print a recipe"""
    print(f"\n{'='*50}")
    print(f"{recipe.get('name', 'Recipe')}")
    print(f"{'='*50}")
    
    if recipe.get('description'):
        print(f"\n{recipe['description']}")
    
    # Times
    times = []
    if recipe.get('prep_time'):
        times.append(f"Prep: {recipe['prep_time']}")
    if recipe.get('cook_time'):
        times.append(f"Cook: {recipe['cook_time']}")
    if recipe.get('total_time'):
        times.append(f"Total: {recipe['total_time']}")
    if times:
        print(f"\n{' | '.join(times)}")
    
    if recipe.get('servings'):
        print(f"Servings: {recipe['servings']}")
    
    # Nutrition
    if recipe.get('nutrition'):
        n = recipe['nutrition']
        nutrition_parts = []
        if n.get('calories'):
            nutrition_parts.append(f"{n['calories']} cal")
        if n.get('protein'):
            nutrition_parts.append(f"{n['protein']} protein")
        if n.get('carbs'):
            nutrition_parts.append(f"{n['carbs']} carbs")
        if n.get('fat'):
            nutrition_parts.append(f"{n['fat']} fat")
        if nutrition_parts:
            print(f"Nutrition: {' | '.join(nutrition_parts)}")

    # Ingredients
    print("\nIngredients:")
    for ing in recipe.get('ingredients', []):
        if isinstance(ing, dict):
            qty = ing.get('quantity', '')
            unit = ing.get('unit', '')
            item = ing.get('item', '')
            notes = ing.get('notes', '')
            
            ing_str = f"  - {qty} {unit} {item}".strip()
            if notes:
                ing_str += f" ({notes})"
            print(ing_str)
        else:
            print(f"  - {ing}")

    # Instructions
    print("\nInstructions:")
    for i, step in enumerate(recipe.get('instructions', []), 1):
        print(f"  {i}. {step}")
    
    # Tags
    if recipe.get('tags'):
        print(f"\nTags: {', '.join(recipe['tags'])}")
    
    print()


def _build_filter(params: dict) -> tuple:
    """
    Build DynamoDB filter expression from search params
    
    Returns:
        (filter_expression, expression_values, expression_names)
    """
    filter_parts = []
    expression_values = {}
    expression_names = {'#n': 'name'}

    # Keywords search name, description, and keywords list
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
    
    return (
        filter_expression,
        expression_values if expression_values else None,
        expression_names
    )


def _recipe_conversation(prompter: RecipePrompter) -> None:
    """Handle recipe modification requests"""
    print("\n" + "-"*50)
    print("Modify this recipe (e.g., 'make it vegetarian', 'double the servings')")
    print("Type 'done' to search again")
    print("-"*50)
    
    while True:
        user_input = input("\n> ").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() in ['done', 'back', 'new', 'search']:
            prompter.clear_conversation()
            print()
            break
        
        response_text, modified_recipe = prompter.chat(user_input)
        print(f"\n{response_text}")
        
        if modified_recipe:
            _print_recipe(modified_recipe)


def recipe_search() -> None:
    """Interactive recipe search"""
    
    # Initialize clients
    prompter = RecipePrompter(boto3.client('bedrock-runtime', region_name='us-east-1'))
    dynamodb = DynamoDBItemManager(boto3.client('dynamodb', region_name='us-east-1'))
    s3 = S3ObjectManager()

    print("\n" + "="*50)
    print("  AI Sous Chef - Recipe Search")
    print("="*50)
    print("Type 'quit' to exit\n")

    while True:
        user_input = input("What would you like to cook? > ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        if not user_input:
            continue

        # Extract search params
        print("\nSearching...")
        params = prompter.extract_search_params(user_input)
        
        if not params:
            print("Sorry, I couldn't understand that. Try again.\n")
            continue

        print(f"Looking for: {params}")

        # Build filter and scan DynamoDB
        filter_expression, expression_values, expression_names = _build_filter(params)

        results = dynamodb.scan_table(
            table_name=AWS_RESOURCES['dynamodb_recipes_table_name'],
            filter_expression=filter_expression,
            expression_values=expression_values,
            expression_names=expression_names
        )

        # No Results; Offer to Generate
        if not results:
            print("\nNo recipes found matching your request.")
            generate = input("Want me to create a recipe for you? (y/n) > ").strip().lower()
            
            if generate == 'y':
                print("\nGenerating recipe...")
                recipe = prompter.generate_recipe(user_input)
                if recipe:
                    _print_recipe(recipe)
                    _recipe_conversation(prompter)
            continue

        # Rank results
        top_recipes = prompter.rank_recipes(user_input, results, top_n=5)

        # Present options
        print(f"\nFound {len(results)} recipes. Top matches:\n")
        for i, r in enumerate(top_recipes, 1):
            cal = r.get('calories', 'N/A')
            cal_str = f"{cal} cal" if cal != 'N/A' else 'N/A'
            print(f"  {i}. {r['name']} - {r.get('category', '')} - {cal_str}")

        print("\n  0. None of these - generate a new recipe")
        
        # Get user choice
        choice = input("\nPick a number > ").strip()

        if choice == '0':
            # Generate new recipe
            print("\nGenerating recipe...")
            recipe = prompter.generate_recipe(user_input)
            
        elif choice.isdigit() and 1 <= int(choice) <= len(top_recipes):
            # Fetch from S3 and format
            selected = top_recipes[int(choice) - 1]
            print(f"\nFetching {selected['name']}...")
            
            raw = s3.get_object(AWS_RESOURCES['s3_clean_bucket_name'], selected['s3_key'])
            if raw:
                raw_recipe = json.loads(raw.decode('utf-8'))
                recipe = prompter.format_recipe(raw_recipe)
            else:
                print("Failed to fetch recipe from S3.")
                continue
        else:
            print("Invalid choice.\n")
            continue

        # Display recipe and enter conversation mode
        if recipe:
            _print_recipe(recipe)
            _recipe_conversation(prompter)
        else:
            print("Failed to process recipe.\n")

    print("\nGoodbye!")


if __name__ == '__main__':
    recipe_search()