"""
Defines interfaces for all Bedrock Functionalities.

Bedrock Manager:
1. Invoke Model
2. Invoke Model With System Prompt
3. Extract Search Params
4. Rank Recipes
5. Format Recipe
6. Generate Recipe
"""
from typing import Protocol, List, Dict
from botocore.client import BaseClient

class BedrockInterface(Protocol):
    def __init__(
        self,
        bedrock_client: BaseClient
    ) -> None:
        raise NotImplementedError

    def invoke_model(
        self,
        prompt: str,
        model_id: str = 'claude-haiku-3',
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        raise NotImplementedError

    def invoke_model_with_system(
        self,
        prompt: str,
        system_prompt: str,
        model_id: str = 'claude-haiku-3',
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        raise NotImplementedError

    def extract_search_params(
        self,
        user_input: str,
    ) -> Dict:
        raise NotImplementedError

    def rank_recipes(
        self,
        user_input: str,
        recipe_options: List[Dict],
        top_n: int = 5,
    ) -> List[Dict]:
        raise NotImplementedError

    def format_recipe(
        self,
        recipe: Dict,
    ) -> Dict:
        raise NotImplementedError

    def generate_recipe(
        self,
        user_input: str,
    ) -> Dict:
        raise NotImplementedError