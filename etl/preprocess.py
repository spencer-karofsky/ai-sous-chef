"""
etl/preprocess.py

Description:
    * Cleans the raw CSV into JSON format:
        0. Loads the raw CSV (./data/raw/recipes.csv)
        1. Parses R-style vectors into Python lists
        2. Normalizes missing fields
        3. Cleans text
        4. Removes bad rows
        5. Outputs list of Python dictionaries

Instructions:
    * Run this Program Once Via the CLI:
        1. cd ./ai-sous-chef/etl
        2. python preprocess.py
        
Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pandas as pd
import re
import json
import tempfile
import os

from infra.managers.s3_manager import S3ObjectManager
from infra.config import AWS_RESOURCES


class RecipesDatasetPreprocessor:
    def __init__(self) -> None:
        """
        Loads the raw CSV from S3 to be pre-processed
        """
        self.s3 = S3ObjectManager()
        self.raw_bucket = AWS_RESOURCES['s3_raw_bucket_name']
        self.clean_bucket = AWS_RESOURCES['s3_clean_bucket_name']
        self.recipes_df = None

    def load_from_s3(self, object_key: str = 'raw/recipes.csv') -> bool:
        """
        Downloads raw CSV from S3 and loads into DataFrame
        Args:
            object_key: S3 key for the raw recipes CSV
        Return:
            True/False to indicate success/failure
        """
        try:
            # Download to temp file
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
                tmp_path = tmp.name
            
            self.s3.download_object(self.raw_bucket, object_key, tmp_path)
            self.recipes_df = pd.read_csv(tmp_path)
            
            # Cleanup temp file
            os.remove(tmp_path)
            
            print(f'[preprocess] Loaded {len(self.recipes_df)} recipes from S3')
            return True
        except Exception as e:
            print(f'[preprocess] Failed to load recipes CSV from S3: {e}')
            return False

    def save_to_s3(self, records: list[dict], object_key: str = 'clean/cleaned_records.jsonl') -> bool:
        """
        Saves cleaned records as JSONL to S3 clean bucket
        Args:
            records: list of cleaned recipe dictionaries
            object_key: S3 key for the output file
        Return:
            True/False to indicate success/failure
        """
        try:
            # Write to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as tmp:
                for rec in records:
                    tmp.write(json.dumps(rec) + '\n')
                tmp_path = tmp.name
            
            # Upload to S3
            self.s3.upload_object(self.clean_bucket, object_key, tmp_path)
            
            # Cleanup temp file
            os.remove(tmp_path)
            
            print(f'[preprocess] Saved {len(records)} cleaned records to S3')
            return True
        except Exception as e:
            print(f'[preprocess] Failed to save to S3: {e}')
            return False

    # Preprocessing Helpers
    def _parse_single_r_vector(self, value):
        """
        Parses a single R-style vector string into a Python list
        """
        if not isinstance(value, str):
            return []
        value = value.strip()
        if value == "c()" or value == "c( )":
            return []
        if not value.startswith("c("):
            return []
        extracted = re.findall(r'"(.*?)"', value)
        return extracted if extracted else []

    def _parse_r_vectors(self) -> None:
        """
        Converts all R-style vector columns into Python lists
        """
        r_vector_columns = [
            'Images',
            'Keywords',
            'RecipeIngredientParts',
            'RecipeIngredientQuantities',
            'RecipeInstructions'
        ]
        for col in r_vector_columns:
            if col in self.recipes_df.columns:
                self.recipes_df[col] = self.recipes_df[col].apply(self._parse_single_r_vector)
            else:
                print(f"[WARN] Column '{col}' not found in DataFrame.")

    def _normalize_missing_fields(self) -> None:
        """
        Normalizes missing or invalid fields across the DataFrame.
        """
        df = self.recipes_df

        for col in df.columns:
            df[col] = df[col].apply(
                lambda x: None if (pd.isna(x) or x in ("", " ", "null", "NaN")) else x
            )

        list_columns = [
            "Images", "Keywords", "RecipeIngredientParts",
            "RecipeIngredientQuantities", "RecipeInstructions"
        ]
        for col in list_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: x if isinstance(x, list) else [])

        numeric_columns = [
            "AggregatedRating", "ReviewCount", "Calories", "FatContent",
            "SaturatedFatContent", "CholesterolContent", "SodiumContent",
            "CarbohydrateContent", "FiberContent", "SugarContent",
            "ProteinContent", "RecipeServings", "RecipeYield"
        ]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df[col] = df[col].apply(lambda x: None if pd.isna(x) else x)

        time_columns = ["PrepTime", "CookTime", "TotalTime"]
        for col in time_columns:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: x if (isinstance(x, str) and x.startswith("PT")) else None
                )

        required_columns = ["RecipeId", "Name"]
        for col in required_columns:
            df[col] = df[col].apply(
                lambda x: None if (x is None or str(x).strip() == "") else x
            )

        self.recipes_df = df

    def _clean_text_fields(self) -> None:
        """
        Cleans and normalizes all text-based fields.
        """
        df = self.recipes_df
        text_columns = ["Name", "Description", "AuthorName", "RecipeCategory"]

        def clean_text(value):
            if value is None:
                return None
            if not isinstance(value, str):
                return value
            cleaned = value.strip()
            cleaned = cleaned.replace("\xa0", " ")
            cleaned = cleaned.replace("\u200b", "")
            cleaned = cleaned.replace("&amp;", "&")
            cleaned = cleaned.replace("&quot;", "\"")
            cleaned = cleaned.replace("&nbsp;", " ")
            cleaned = " ".join(cleaned.split())
            return cleaned

        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].apply(clean_text)

        list_columns = [
            "Images", "Keywords", "RecipeIngredientParts",
            "RecipeIngredientQuantities", "RecipeInstructions"
        ]

        def clean_list(list_val):
            if not isinstance(list_val, list):
                return []
            cleaned_items = []
            for item in list_val:
                if item is None or not isinstance(item, str):
                    continue
                cleaned_item = clean_text(item)
                if cleaned_item:
                    cleaned_items.append(cleaned_item)
            return cleaned_items

        for col in list_columns:
            if col in df.columns:
                df[col] = df[col].apply(clean_list)

        if "Keywords" in df.columns:
            df["Keywords"] = df["Keywords"].apply(lambda lst: [kw.lower() for kw in lst])

        self.recipes_df = df

    def _remove_bad_rows(self) -> None:
        """
        Removes unusable or structurally invalid recipe rows.
        """
        df = self.recipes_df
        initial_count = len(df)

        df = df[df["RecipeId"].notna() & df["Name"].notna()]

        df = df[
            df["RecipeIngredientParts"].apply(lambda lst: isinstance(lst, list) and len(lst) > 0) &
            df["RecipeIngredientQuantities"].apply(lambda lst: isinstance(lst, list) and len(lst) > 0)
        ]

        df = df[
            df.apply(
                lambda row: len(row["RecipeIngredientParts"]) == len(row["RecipeIngredientQuantities"]),
                axis=1
            )
        ]

        df = df[
            df["RecipeInstructions"].apply(lambda lst: isinstance(lst, list) and len(lst) > 0)
        ]

        final_count = len(df)
        print(f"[preprocess] Removed {initial_count - final_count} bad rows (kept {final_count} valid recipes).")
        self.recipes_df = df

    def _to_dict_list(self) -> list[dict]:
        """
        Converts the cleaned DataFrame into a list of Python dictionaries.
        """
        records = self.recipes_df.to_dict(orient="records")
        print(f"[preprocess] Exported {len(records)} cleaned recipe dictionaries.")
        return records

    def preprocess(self) -> list[dict]:
        """Runs all Preprocessing Steps"""
        try:
            self._parse_r_vectors()
            self._normalize_missing_fields()
            self._clean_text_fields()
            self._remove_bad_rows()
            return self._to_dict_list()
        except Exception as e:
            print(f'ETL Preprocessing Error: {e}')
            return []


def run_preprocessing():
    """Main entry point for ETL preprocessing"""
    p = RecipesDatasetPreprocessor()
    
    # Load from S3
    if not p.load_from_s3():
        print("[preprocess] Failed to load data from S3")
        return
    
    # Run preprocessing
    records = p.preprocess()
    
    if not records:
        print("[preprocess] No records to save")
        return
    
    # Save to S3
    p.save_to_s3(records)

if __name__ == "__main__":
    run_preprocessing()