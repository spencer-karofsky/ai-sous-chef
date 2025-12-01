"""
infra/config.py

Description:
    * Stores the variable names for various AWS Services

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""

AWS_RESOURCES = {
    # VPC
    'vpc_name': 'ai-sous-chef-vpc',
    'vpc_subnet_name': 'ai-sous-chef-subnet',
    'vpc_security_group_name': 'ai-sous-chef-security-group',
    'vpc_security_description': 'AI Sous Chef Security Group',
    
    # S3
    's3_raw_bucket_name': 'ai-sous-chef-data-raw',
    's3_clean_bucket_name': 'ai-sous-chef-data-clean',
    
    # IAM
    'ec2_iam_role_name': 'ai-sous-chef-ec2-role',
    'ec2_instance_profile_name': 'ai-sous-chef-ec2-profile',
    'ec2_iam_policies': [
        'arn:aws:iam::aws:policy/AmazonS3FullAccess',
        'arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore',
        'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess',
        'arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess'
    ],
    
    # EC2
    'ec2_key_pair_name': 'ai-sous-chef-key-pair',
    'ec2_instance_name': 'ai-sous-chef-etl',
    'ec2_image_id': 'ami-0fa3fe0fa7920f68e', # Amazon Linux 2023
    'ec2_instance_type': 't3.small',
}

EC2_USER_DATA_SCRIPT = """#!/bin/bash
set -e

# Fetch Kaggle credentials from SSM
mkdir -p /home/ec2-user/.kaggle
aws ssm get-parameter --name /kaggle/credentials --with-decryption \
    --query 'Parameter.Value' --output text --region us-east-1 > /home/ec2-user/.kaggle/kaggle.json
chmod 600 /home/ec2-user/.kaggle/kaggle.json
chown ec2-user:ec2-user /home/ec2-user/.kaggle/kaggle.json

yum update -y
yum install -y python3-pip git

git clone https://github.com/spencer-karofsky/ai-sous-chef.git /home/ec2-user/ai-sous-chef
cd /home/ec2-user/ai-sous-chef

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python main.py etl

echo "ETL complete" > /home/ec2-user/etl_status.txt
"""