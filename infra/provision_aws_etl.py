"""
infra/provision_aws_etl.py

Description:
    * Provisions the AWS Infrastructure to run ETL Pipeline

Instructions:
    * Run via CLI:
        python main.py provision

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import json
import time
import boto3

from infra.managers.vpc_manager import VPCNetworkManager, VPCSecurityManager, VPCSetupManager
from infra.managers.s3_manager import S3BucketManager
from infra.managers.ec2_manager import EC2InstancesManager, EC2KeyPairManager
from infra.managers.iam_manager import IAMRoleManager
from infra.config import AWS_RESOURCES, EC2_USER_DATA_SCRIPT


def provision_aws_etl():
    # Create Clients
    ec2_client = boto3.client('ec2')
    iam_client = boto3.client('iam')

    # VPC
    vpc_setup = VPCSetupManager(ec2_client)
    vpc_setup.create_vpc(AWS_RESOURCES['vpc_name'])
    vpc_id = vpc_setup.get_vpc_id()

    # Subnet (use a /24 subset, not the full /16)
    vpc_network = VPCNetworkManager(ec2_client, vpc_id)
    vpc_network.create_subnet('10.0.1.0/24', subnet_name=AWS_RESOURCES['vpc_subnet_name'])
    vpc_subnet_id = vpc_network.subnet_id

    # Internet Gateway (required for public internet access)
    vpc_network.create_internet_gateway()

    # Route Table with public route
    vpc_network.create_route_table()
    vpc_network.add_route('0.0.0.0/0') # Route all traffic to IGW
    vpc_network.associate_route_table()

    # Security Group
    vpc_security = VPCSecurityManager(
        ec2_client,
        vpc_id,
        description=AWS_RESOURCES['vpc_security_description'],
        group_name=AWS_RESOURCES['vpc_security_group_name']
    )
    vpc_security.create_security_group(egress=True, ssh=True)
    vpc_security_group_id = vpc_security.security_group_id

    # S3
    s3_bucket = S3BucketManager()
    s3_bucket.create_bucket(AWS_RESOURCES['s3_raw_bucket_name'])
    s3_bucket.create_bucket(AWS_RESOURCES['s3_clean_bucket_name'])

    # IAM: Role and Instance Profile
    ec2_trust_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    })

    iam_manager = IAMRoleManager(iam_client)
    role_name = AWS_RESOURCES['ec2_iam_role_name']
    profile_name = AWS_RESOURCES['ec2_instance_profile_name']

    iam_manager.create_role(role_name, ec2_trust_policy)
    for policy_arn in AWS_RESOURCES['ec2_iam_policies']:
        iam_manager.attach_policy(role_name, policy_arn)
    iam_manager.create_instance_profile(profile_name)
    iam_manager.add_role_to_instance_profile(profile_name, role_name)

    # Wait for IAM instance profile to propagate
    print("Waiting for IAM instance profile to propagate...")
    time.sleep(15)

    # EC2
    ec2_key_pair = EC2KeyPairManager(ec2_client)
    ec2_key_pair.create_key_pair(AWS_RESOURCES['ec2_key_pair_name'])

    ec2_instance_manager = EC2InstancesManager(ec2_client)
    ec2_instance_manager.launch_instance(
        instance_name=AWS_RESOURCES['ec2_instance_name'],
        image_id=AWS_RESOURCES['ec2_image_id'],
        instance_type=AWS_RESOURCES['ec2_instance_type'],
        subnet_id=vpc_subnet_id,
        key_name=AWS_RESOURCES['ec2_key_pair_name'],
        security_group_ids=[vpc_security_group_id],
        iam_instance_profile=profile_name,
        user_data=EC2_USER_DATA_SCRIPT
    )

    # Wait for public IP assignment
    print("Waiting for public IP assignment...")
    instance_id = ec2_instance_manager.instances[0]['InstanceId']
    time.sleep(30)
    
    ips = ec2_instance_manager.list_instance_public_ips([instance_id])
    public_ip = ips.get(instance_id)
    
    print('Provisioning complete!')
    print('')
    print('To SSH into EC2:')
    print(f'   ssh -i {ec2_key_pair.key_path} ec2-user@{public_ip}')
    print('To see debugging information from inside EC2:')
    print('   sudo tail -f /var/log/cloud-init-output.log')
    print(f'To view uploading progress:')
    print('   aws s3 ls s3://ai-sous-chef-data-clean/recipes/ | wc -l')


if __name__ == '__main__':
    provision_aws_etl()