"""
Implements all Bedrock functionalities.
"""
import json
from infra.utils.logger import logger
from infra.interfaces.bedrock_interface import BedrockInterface
from botocore.exceptions import ClientError
from botocore.client import BaseClient
from typing import List, Dict, Optional


class BedrockManager(BedrockInterface):
    def __init__(
        self,
        bedrock_client: BaseClient
    ) -> None:
        """
        Creates object to manage Bedrock interactions

        Args:
            bedrock_client: the injected boto3 bedrock-runtime client
        """
        self.client = bedrock_client

    def invoke_model(
        self,
        prompt: str,
        model_id: str = 'anthropic.claude-3-haiku-20240307-v1:0',
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """
        Base LLM call

        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/invoke_model.html

        Args:
            prompt: the user prompt
            model_id: Bedrock model identifier
            max_tokens: maximum tokens in response
            temperature: randomness (0-1)

        Returns:
            Model response text, or None if failed
        """
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })

            response = self.client.invoke_model(
                modelId=model_id,
                body=body,
                contentType='application/json',
                accept='application/json'
            )

            response_body = json.loads(response['body'].read())
            result = response_body['content'][0]['text']

            logger.info(f'[SUCCESS] Invoked model "{model_id}"')
            return result

        except ClientError as e:
            logger.error(f'[FAIL] Cannot invoke model ({e})')
            return None

    def invoke_model_with_system(
        self,
        prompt: str,
        system_prompt: str,
        model_id: str = 'anthropic.claude-3-haiku-20240307-v1:0',
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """
        LLM call with system prompt

        Args:
            prompt: the user prompt
            system_prompt: system context/instructions
            model_id: Bedrock model identifier
            max_tokens: maximum tokens in response
            temperature: randomness (0-1)

        Returns:
            Model response text, or None if failed
        """
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })

            response = self.client.invoke_model(
                modelId=model_id,
                body=body,
                contentType='application/json',
                accept='application/json'
            )

            response_body = json.loads(response['body'].read())
            result = response_body['content'][0]['text']

            logger.info(f'[SUCCESS] Invoked model "{model_id}" with system prompt')
            return result

        except ClientError as e:
            logger.error(f'[FAIL] Cannot invoke model ({e})')
            return None

    def extract_search_params(
        self,
        user_input: str,
    ) -> Optional[Dict]:
        """
        Parse natural language into structured search params

        Args:
            user_input: natural language request, e.g. "quick chicken dinner"

        Returns:
            Dict with keys: keywords, category, max_calories, max_total_time
        """
        system_prompt = """You extract structured search parameters from food requests.

Return ONLY valid JSON with these optional fields:
- keywords: list of ingredient/dish/cuisine keywords (lowercase)
- category: one of Breakfast, Lunch, Dinner, Dessert, Snack, Appetizer
- max_calories: integer if user mentions diet/light/healthy
- max_total_time: ISO 8601 duration if user mentions quick/fast (e.g. PT30M)

Example input: "quick healthy chicken dinner"
Example output: {"keywords": ["chicken"], "category": "Dinner", "max_calories": 500, "max_total_time": "PT30M"}"""

        try:
            response = self.invoke_model_with_system(
                prompt=user_input,
                system_prompt=system_prompt,
                max_tokens=256,
                temperature=0.3
            )

            if not response:
                return None

            # Parse JSON from response
            result = json.loads(response.strip())
            logger.info(f'[SUCCESS] Extracted search params: {result}')
            return result

        except json.JSONDecodeError as e:
            logger.error(f'[FAIL] Cannot parse search params JSON ({e})')
            return None

    def rank_recipes(
        self,
        user_input: str,
        recipe_options: List[Dict],
        top_n: int = 5,
    ) -> List[Dict]:
        """
        Rank recipes by relevance to user request

        Args:
            user_input: original user request
            recipe_options: list of recipe metadata from DynamoDB
            top_n: number of top results to return

        Returns:
            List of top recipes ordered by relevance
        """
        if not recipe_options:
            return []

        if len(recipe_options) <= top_n:
            return recipe_options

        system_prompt = """You rank recipes by relevance to a user's request.

Given a user request and list of recipes, return the indices of the most relevant recipes in order of best match.

Return ONLY valid JSON: {"ranked_indices": [0, 3, 1, ...]}"""

        # Build recipe summary for ranking (keep it concise)
        recipe_summaries = []
        for i, r in enumerate(recipe_options[:50]):  # Limit to 50 to save tokens
            summary = f"{i}: {r.get('name', 'Unknown')} - {r.get('category', '')} - {r.get('calories', 'N/A')} cal"
            recipe_summaries.append(summary)

        prompt = f"""User request: {user_input}

Recipes:
{chr(10).join(recipe_summaries)}

Return the indices of the top {top_n} most relevant recipes."""

        try:
            response = self.invoke_model_with_system(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=128,
                temperature=0.3
            )

            if not response:
                return recipe_options[:top_n]

            result = json.loads(response.strip())
            indices = result.get('ranked_indices', [])[:top_n]

            ranked = [recipe_options[i] for i in indices if i < len(recipe_options)]
            logger.info(f'[SUCCESS] Ranked {len(ranked)} recipes')
            return ranked

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.error(f'[FAIL] Cannot rank recipes ({e})')
            return recipe_options[:top_n]

    def format_recipe(
        self,
        recipe: Dict,
    ) -> Optional[Dict]:
        """
        Normalize recipe to uniform output structure

        Args:
            recipe: full recipe from S3

        Returns:
            Cleaned and formatted recipe dict
        """
        system_prompt = """You format recipes into a clean, consistent structure.
Return ONLY valid JSON with these fields:
- name: string
- description: brief 1-2 sentence description
- prep_time: human readable (e.g. "15 minutes")
- cook_time: human readable
- total_time: human readable
- servings: string
- ingredients: list of strings (e.g. ["1 cup flour", "2 eggs"])
- instructions: list of step strings
- nutrition: {calories, protein, carbs, fat} as strings with units
Fill in reasonable values for any missing fields based on the recipe context."""

        prompt = f"Format this recipe:\n{json.dumps(recipe, indent=2)}"

        try:
            response = self.invoke_model_with_system(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1024,
                temperature=0.3
            )

            if not response:
                return None

            result = json.loads(response.strip())
            logger.info(f'[SUCCESS] Formatted recipe: {result.get("name", "Unknown")}')
            return result

        except json.JSONDecodeError as e:
            logger.error(f'[FAIL] Cannot parse formatted recipe JSON ({e})')
            return None

    def generate_recipe(
        self,
        user_input: str,
    ) -> Optional[Dict]:
        """
        Generate a new recipe from scratch based on user request

        Args:
            user_input: user's food request

        Returns:
            Generated recipe in standard format
        """
        system_prompt = """You are a professional chef. Create a recipe based on the user's request.
Return ONLY valid JSON with these fields:
- name: string
- description: brief 1-2 sentence description
- prep_time: human readable (e.g. "15 minutes")
- cook_time: human readable
- total_time: human readable
- servings: string (e.g. "4 servings")
- ingredients: list of strings with quantities (e.g. ["1 cup flour", "2 eggs"])
- instructions: list of numbered step strings
- nutrition: {calories, protein, carbs, fat} as strings with units (estimate)
Create a practical, delicious recipe that matches the request."""

        try:
            response = self.invoke_model_with_system(
                prompt=f"Create a recipe for: {user_input}",
                system_prompt=system_prompt,
                #model_id='anthropic.claude-3-5-sonnet-20240620-v1:0',
                max_tokens=1024,
                temperature=0.4
            )

            if not response:
                return None

            result = json.loads(response.strip())
            logger.info(f'[SUCCESS] Generated recipe: {result.get("name", "Unknown")}')
            return result

        except json.JSONDecodeError as e:
            logger.error(f'[FAIL] Cannot parse generated recipe JSON ({e})')
            return None