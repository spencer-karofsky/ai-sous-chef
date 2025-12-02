"""
infra/create_recipes_table.py

Description:
    * Creates the DynamoDB recipes table

Instructions:
    * Run via CLI (Local):
        cd ./ai-sous-chef/
        python -m infra.create_recipes_table

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import json
import boto3
from typing import Dict

from infra.managers.s3_manager import S3BucketManager, S3ObjectManager
from infra.managers.dynamodb_manager import DynamoDBTableManager, DynamoDBItemManager
from infra.managers.ec2_manager import EC2InstancesManager
from infra.managers.iam_manager import IAMRoleManager
from infra.managers.vpc_manager import VPCSetupManager, VPCNetworkManager, VPCSecurityManager
from infra.config import AWS_RESOURCES, EC2_TABLE_STARTUP_SCRIPT

def _json_recipe_to_table_entry(json_recipe: Dict) -> Dict:
    """
    Transform individual JSON recipe to DynamoDB entry
    
    Args:
        json_recipe: canonical JSON recipe from S3
        
    Returns:
        Flattened dict for DynamoDB (searchable fields + s3 pointer)
    """
    recipe_id = str(json_recipe.get('id'))
    
    return {
        'recipe_id': recipe_id,
        'name': json_recipe.get('name', ''),
        'description': json_recipe.get('description', ''),
        'category': json_recipe.get('category', ''),
        'keywords': json_recipe.get('keywords', []),
        'author': json_recipe.get('author', ''),
        's3_key': f"recipes/{recipe_id}.json",
        # Flatten nutrition for filtering
        'calories': json_recipe.get('nutrition', {}).get('calories'),
        'protein': json_recipe.get('nutrition', {}).get('protein'),
        'carbs': json_recipe.get('nutrition', {}).get('carbs'),
        'fat': json_recipe.get('nutrition', {}).get('fat'),
        # Flatten metadata for filtering
        'rating': json_recipe.get('metadata', {}).get('aggregated_rating'),
        'review_count': json_recipe.get('metadata', {}).get('review_count'),
        'prep_time': json_recipe.get('metadata', {}).get('prep_time'),
        'cook_time': json_recipe.get('metadata', {}).get('cook_time'),
        'total_time': json_recipe.get('metadata', {}).get('total_time'),
    }

def _launch_ec2() -> None:
    """
    Launches EC2 instance to run the loader
    """
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    
    # Look up VPC resources by name
    vpc_setup = VPCSetupManager(ec2_client)
    vpc_setup.get_vpc_by_name(AWS_RESOURCES['vpc_name'])
    vpc_id = vpc_setup.get_vpc_id()
    
    vpc_network = VPCNetworkManager(ec2_client, vpc_id)
    vpc_network.get_subnet_by_name(AWS_RESOURCES['vpc_subnet_name'])
    subnet_id = vpc_network.subnet_id
    
    vpc_security = VPCSecurityManager(
        ec2_client,
        vpc_id,
        description=AWS_RESOURCES['vpc_security_description'],
        group_name=AWS_RESOURCES['vpc_security_group_name']
    )
    vpc_security.get_security_group_by_name()
    security_group_id = vpc_security.security_group_id

    # Launch instance
    ec2_manager = EC2InstancesManager(ec2_client)
    success = ec2_manager.launch_instance(
        instance_name='dynamodb-loader',
        image_id=AWS_RESOURCES['ec2_image_id'],
        instance_type=AWS_RESOURCES['ec2_instance_type'],
        subnet_id=subnet_id,
        key_name=AWS_RESOURCES['ec2_key_pair_name'],
        security_group_ids=[security_group_id],
        iam_instance_profile=AWS_RESOURCES['ec2_instance_profile_name'],
        user_data=EC2_TABLE_STARTUP_SCRIPT
    )

    if success:
        instance_id = ec2_manager.instances[0]['InstanceId']
        print(f'[SUCCESS] Launched dynamodb-loader: {instance_id}')
        print(f'[INFO] Instance will auto-shutdown when complete')
        print(f'[INFO] Logs at /var/log/dynamodb-loader.log')
    else:
        print('[FAIL] Could not launch instance')

def create_recipes_table() -> None:
    """
    Creates DynamoDB table to store all recipes and uploads recipes in batches
    """
    # IAM Permissions
    iam_client = boto3.client('iam', region_name='us-east-1')
    iam_manager = IAMRoleManager(iam_client)

    iam_manager.attach_policy(
        role_name=AWS_RESOURCES['ec2_iam_role_name'],
        policy_arn='arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'
    )

    # Create AWS clients
    dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')

    s3_bucket_manager = S3BucketManager()
    s3_object_manager = S3ObjectManager()
    dynamodb_table_manager = DynamoDBTableManager(dynamodb_client)
    dynamodb_item_manager = DynamoDBItemManager(dynamodb_client)

    # Retrieve Recipes in S3
    s3_buckets = s3_bucket_manager.list_buckets()
    assert AWS_RESOURCES['s3_clean_bucket_name'] in s3_buckets, \
        f'[FAIL] [create_recipes_table] Bucket "{AWS_RESOURCES["s3_clean_bucket_name"]}" does not exist.'

    clean_recipe_objects = s3_object_manager.list_objects(AWS_RESOURCES['s3_clean_bucket_name'])
    assert len(clean_recipe_objects) != 0, f'[FAIL] [create_recipes_table] No objects in bucket {AWS_RESOURCES["s3_clean_bucket_name"]}'

    # Filter to only recipe JSON files
    recipe_keys = [obj[0] for obj in clean_recipe_objects if obj[0].startswith('recipes/') and obj[0].endswith('.json')]
    print(f'[INFO] [create_recipes_table] {len(recipe_keys)} recipe files to process')

    # Create recipes table and wait for active
    dynamodb_table_manager.create_table(
        table_name=AWS_RESOURCES['dynamodb_recipes_table_name'],
        partition_key=AWS_RESOURCES['dynamodb_recipes_table_partition_key'],
        partition_key_type='S',
        billing_mode='PAY_PER_REQUEST'
    )
    dynamodb_table_manager.wait_table_active(AWS_RESOURCES['dynamodb_recipes_table_name'])

    # Process in batches to avoid memory issues
    BATCH_SIZE = 500
    total_uploaded = 0
    total_failed = 0

    for batch_start in range(0, len(recipe_keys), BATCH_SIZE):
        batch_keys = recipe_keys[batch_start:batch_start + BATCH_SIZE]
        items = []

        for key in batch_keys:
            try:
                json_bytes = s3_object_manager.get_object(
                    AWS_RESOURCES['s3_clean_bucket_name'],
                    key
                )
                json_recipe = json.loads(json_bytes.decode('utf-8'))
                item = _json_recipe_to_table_entry(json_recipe)
                items.append(item)
            except Exception as e:
                total_failed += 1

        # Write this batch to DynamoDB
        if items:
            success = dynamodb_item_manager.batch_write_items(
                table_name=AWS_RESOURCES['dynamodb_recipes_table_name'],
                items=items
            )
            if success:
                total_uploaded += len(items)

        print(f'[INFO] [create_recipes_table] Progress: {batch_start + len(batch_keys)}/{len(recipe_keys)}')

    print(f'[SUCCESS] [create_recipes_table] Uploaded {total_uploaded}, failed {total_failed}')

if __name__ == '__main__':
    import sys
    if '--run' in sys.argv:
        create_recipes_table()
    else:
        _launch_ec2()