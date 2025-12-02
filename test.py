import boto3

s3 = boto3.client('s3')

paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket='ai-sous-chef-data-clean', Prefix='recipes/')

recipe_ids = []
for page in pages:
    for obj in page.get('Contents', []):
        key = obj['Key']  # e.g., 'recipes/12345.json'
        recipe_id = key.replace('recipes/', '').replace('.json', '')
        recipe_ids.append(recipe_id)

print(f"Total keys: {len(recipe_ids)}")
print(f"Unique IDs: {len(set(recipe_ids))}")

# Find duplicates
from collections import Counter
counts = Counter(recipe_ids)
duplicates = {k: v for k, v in counts.items() if v > 1}
print(f"Duplicates: {duplicates}")