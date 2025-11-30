"""
data/data_download.py

Description:
    * Downloads Recipes Dataset to S3
    * Using Kaggle Dataset: Food.com - Recipes and Reviews
        - https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews

Instructions:
    * Run this Program Once Via the CLI:
        1. cd ./ai-sous-chef/data
        2. python data_download.py
        
Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import kagglehub
import os

from infra.managers.s3_manager import S3ObjectManager
from infra.config import AWS_RESOURCES

def download_and_upload_to_s3():
    # Download to EC2 local storage (temporary)
    cache_path = kagglehub.dataset_download('irkaal/foodcom-recipes-and-reviews')
    print(f'Downloaded to cache: {cache_path}')
    
    # Upload each file to S3 raw bucket
    s3 = S3ObjectManager()
    bucket = AWS_RESOURCES['s3_raw_bucket_name']
    
    for filename in os.listdir(cache_path):
        filepath = os.path.join(cache_path, filename)
        if os.path.isfile(filepath):
            object_key = f"raw/{filename}"
            s3.upload_object(bucket, object_key, filepath)
    
    print('Upload complete')

if __name__ == '__main__':
    download_and_upload_to_s3()