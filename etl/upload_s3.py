"""
etl/upload_s3.py

Description:
    * Uploads canonical JSON recipe files to S3 clean bucket.
    * Ensures one JSON file per recipe is stored in:
          s3://<bucket_name>/recipes/<id>.json
    * Prepares the dataset for downstream embedding, indexing, and RAG retrieval.

Instructions:
    * Run via CLI: python main.py upload
    
Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import os
import json
import tempfile

from infra.managers.s3_manager import S3ObjectManager
from infra.config import AWS_RESOURCES


class S3RecipeUploader:
    """
    Reads cleaned JSONL from S3 and uploads individual recipe JSON files.
    """
    def __init__(self):
        self.s3 = S3ObjectManager()
        self.clean_bucket = AWS_RESOURCES['s3_clean_bucket_name']

    def load_cleaned_records(self, object_key: str = 'clean/cleaned_records.jsonl') -> list[dict]:
        """
        Downloads cleaned JSONL from S3 and parses into list of dicts
        Args:
            object_key: S3 key for the cleaned JSONL file
        Return:
            List of recipe dictionaries
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
            print(f'[upload_s3] Loaded {len(records)} records from S3')
            return records
        except Exception as e:
            print(f'[upload_s3] Failed to load cleaned records: {e}')
            return []

    def upload_individual_recipes(self, records: list[dict], prefix: str = 'recipes') -> tuple[int, int]:
        """
        Uploads each recipe as an individual JSON file to S3
        Args:
            records: list of recipe dictionaries
            prefix: S3 key prefix for recipe files
        Return:
            Tuple of (successful uploads, failed uploads)
        """
        uploaded = 0
        failed = 0

        for record in records:
            recipe_id = record.get('RecipeId')
            if not recipe_id:
                print('[upload_s3] Skipping record with no RecipeId')
                failed += 1
                continue

            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
                    json.dump(record, tmp, indent=2)
                    tmp_path = tmp.name

                object_key = f'{prefix}/{recipe_id}.json'
                success = self.s3.upload_object(self.clean_bucket, object_key, tmp_path)

                os.remove(tmp_path)

                if success:
                    uploaded += 1
                else:
                    failed += 1
            except Exception as e:
                print(f'[upload_s3] Failed to upload recipe {recipe_id}: {e}')
                failed += 1

        print(f'[upload_s3] Upload complete: {uploaded} succeeded, {failed} failed')
        return uploaded, failed


def upload_recipes():
    """Main entry point for uploading recipes to S3"""
    uploader = S3RecipeUploader()

    # Load cleaned records from S3
    records = uploader.load_cleaned_records()
    if not records:
        print('[upload_s3] No records to upload')
        return

    # Upload individual recipe files
    uploader.upload_individual_recipes(records)


if __name__ == "__main__":
    upload_recipes()