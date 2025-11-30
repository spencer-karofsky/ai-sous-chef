"""
etl/build_json.py

Description:
    * Converts cleaned recipe records from S3 into canonical JSON format
    * Uploads individual recipe JSON files to S3
    * Prepares data for downstream embedding, indexing, and RAG retrieval

Instructions:
    * Run via CLI: python main.py build

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import json
import tempfile
import os

from infra.managers.s3_manager import S3ObjectManager
from infra.config import AWS_RESOURCES


class RecipeJSONBuilder:
    """
    Takes cleaned recipe dictionaries from S3 and converts them into
    canonical JSON recipe files, uploading each to S3.
    """

    def __init__(self):
        self.s3 = S3ObjectManager()
        self.clean_bucket = AWS_RESOURCES['s3_clean_bucket_name']

    def load_cleaned_records(self, object_key: str = 'clean/cleaned_records.jsonl') -> list[dict]:
        """
        Downloads cleaned JSONL from S3 and parses into list of dicts
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as tmp:
                tmp_path = tmp.name

            self.s3.download_object(self.clean_bucket, object_key, tmp_path)

            records = []
            with open(tmp_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))

            os.remove(tmp_path)
            print(f'[build_json] Loaded {len(records)} records from S3')
            return records
        except Exception as e:
            print(f'[build_json] Failed to load cleaned records: {e}')
            return []

    def _build_canonical_json(self, record: dict) -> dict:
        """
        Builds the canonical JSON format for a single recipe.
        """
        # Map ingredients
        ingredients = []
        parts = record.get("RecipeIngredientParts", [])
        quantities = record.get("RecipeIngredientQuantities", [])

        for p, q in zip(parts, quantities):
            ingredients.append({
                "quantity": q,
                "item": p
            })

        # Build nutrition block
        nutrition = {
            "calories": record.get("Calories"),
            "fat": record.get("FatContent"),
            "saturated_fat": record.get("SaturatedFatContent"),
            "cholesterol": record.get("CholesterolContent"),
            "sodium": record.get("SodiumContent"),
            "carbs": record.get("CarbohydrateContent"),
            "fiber": record.get("FiberContent"),
            "sugar": record.get("SugarContent"),
            "protein": record.get("ProteinContent")
        }

        # Build metadata block
        metadata = {
            "prep_time": record.get("PrepTime"),
            "cook_time": record.get("CookTime"),
            "total_time": record.get("TotalTime"),
            "review_count": record.get("ReviewCount"),
            "aggregated_rating": record.get("AggregatedRating")
        }

        # Canonical JSON structure
        canonical = {
            "id": record["RecipeId"],
            "name": record.get("Name"),
            "description": record.get("Description"),
            "category": record.get("RecipeCategory"),
            "ingredients": ingredients,
            "instructions": record.get("RecipeInstructions", []),
            "keywords": record.get("Keywords", []),
            "author": record.get("AuthorName"),
            "nutrition": nutrition,
            "metadata": metadata
        }

        return canonical

    def upload_recipe(self, recipe_id: int, recipe_obj: dict, prefix: str = 'recipes') -> bool:
        """
        Uploads a single canonical recipe JSON to S3
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
                json.dump(recipe_obj, tmp, indent=2, sort_keys=True)
                tmp_path = tmp.name

            object_key = f'{prefix}/{recipe_id}.json'
            success = self.s3.upload_object(self.clean_bucket, object_key, tmp_path)

            os.remove(tmp_path)
            return success
        except Exception as e:
            print(f'[build_json] Failed to upload recipe {recipe_id}: {e}')
            return False

    def build_all(self) -> tuple[int, int]:
        """
        Runs the entire JSON-building process:
        1. Load cleaned records from S3
        2. Convert each to canonical format
        3. Upload each as individual JSON to S3
        """
        records = self.load_cleaned_records()

        if not records:
            print('[build_json] No records to process')
            return 0, 0

        total = len(records)
        uploaded = 0
        failed = 0

        for rec in records:
            try:
                recipe_id = rec.get("RecipeId")
                if not recipe_id:
                    failed += 1
                    continue

                recipe_json = self._build_canonical_json(rec)
                if self.upload_recipe(recipe_id, recipe_json):
                    uploaded += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"[build_json] Error processing recipe {rec.get('RecipeId')}: {e}")
                failed += 1

        print(f"[build_json] Successfully uploaded {uploaded}/{total} recipe JSON files to S3.")
        return uploaded, failed


def build_json():
    """Main entry point for building and uploading recipe JSONs"""
    builder = RecipeJSONBuilder()
    builder.build_all()


if __name__ == "__main__":
    build_json()