"""
infra/tear_down_aws_etl.py

Description:
    * Tears down AWS Infrastructure for the ETL pipeline (except the clean S3 bucket)

Instructions:
    * Run via CLI:
        cd ./ai-sous-chef/
        python -m infra.tear_down_aws_etl

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import time
import boto3
from botocore.exceptions import ClientError

from infra.config import AWS_RESOURCES
from infra.managers.s3_manager import S3BucketManager, S3ObjectManager
from infra.managers.ec2_manager import EC2KeyPairManager


def find_vpc_by_name(ec2_client, vpc_name: str) -> str | None:
    """Find VPC ID by Name tag"""
    response = ec2_client.describe_vpcs(
        Filters=[{'Name': 'tag:Name', 'Values': [vpc_name]}]
    )
    vpcs = response.get('Vpcs', [])
    return vpcs[0]['VpcId'] if vpcs else None


def find_instance_by_name(ec2_client, instance_name: str) -> str | None:
    """Find EC2 instance ID by Name tag (excludes terminated)"""
    response = ec2_client.describe_instances(
        Filters=[
            {'Name': 'tag:Name', 'Values': [instance_name]},
            {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']}
        ]
    )
    for reservation in response.get('Reservations', []):
        for instance in reservation.get('Instances', []):
            return instance['InstanceId']
    return None


def find_security_group_by_name(ec2_client, vpc_id: str, group_name: str) -> str | None:
    """Find security group ID by name within a VPC"""
    response = ec2_client.describe_security_groups(
        Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]},
            {'Name': 'group-name', 'Values': [group_name]}
        ]
    )
    groups = response.get('SecurityGroups', [])
    return groups[0]['GroupId'] if groups else None


def find_subnets_by_vpc(ec2_client, vpc_id: str) -> list[str]:
    """Find all subnet IDs in a VPC."""
    response = ec2_client.describe_subnets(
        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
    )
    return [s['SubnetId'] for s in response.get('Subnets', [])]


def find_igw_by_vpc(ec2_client, vpc_id: str) -> str | None:
    """Find Internet Gateway attached to VPC"""
    response = ec2_client.describe_internet_gateways(
        Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
    )
    igws = response.get('InternetGateways', [])
    return igws[0]['InternetGatewayId'] if igws else None


def find_route_tables_by_vpc(ec2_client, vpc_id: str) -> list[str]:
    """Find non-main route table IDs in a VPC"""
    response = ec2_client.describe_route_tables(
        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
    )
    # Skip the main route table (auto-deleted with VPC)
    return [
        rt['RouteTableId'] for rt in response.get('RouteTables', [])
        if not any(assoc.get('Main', False) for assoc in rt.get('Associations', []))
    ]


def wait_for_instance_termination(ec2_client, instance_id: str, timeout: int = 120):
    """Wait for an instance to reach terminated state"""
    print(f"Waiting for instance {instance_id} to terminate...")
    start = time.time()
    while time.time() - start < timeout:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        if state == 'terminated':
            print(f"Instance {instance_id} terminated.")
            return True
        time.sleep(5)
    print(f"Timeout waiting for instance termination.")
    return False


def tear_down_aws_etl():
    ec2_client = boto3.client('ec2')

    # Terminate EC2 instance first (must be gone before deleting VPC resources)
    instance_id = find_instance_by_name(ec2_client, AWS_RESOURCES['ec2_instance_name'])
    if instance_id:
        print(f"Terminating EC2 instance: {instance_id}")
        ec2_client.terminate_instances(InstanceIds=[instance_id])
        wait_for_instance_termination(ec2_client, instance_id)
    else:
        print("No EC2 instance found to terminate.")

    # Delete key pair
    key_pairs = EC2KeyPairManager(ec2_client)
    key_pairs.delete_key_pair(AWS_RESOURCES['ec2_key_pair_name'])

    # Delete raw S3 bucket (keep clean bucket)
    raw_bucket = AWS_RESOURCES['s3_raw_bucket_name']
    s3_bucket = S3BucketManager()
    s3_objects = S3ObjectManager()
    raw_objects = s3_objects.list_objects(raw_bucket)
    for (key, _, _) in raw_objects:
        s3_objects.delete_object(raw_bucket, key)
    s3_bucket.delete_bucket(raw_bucket)

    # Find VPC
    vpc_id = find_vpc_by_name(ec2_client, AWS_RESOURCES['vpc_name'])
    if not vpc_id:
        print("No VPC found. Teardown complete.")
        return

    print(f"Found VPC: {vpc_id}")

    # Delete security group
    sg_id = find_security_group_by_name(
        ec2_client, vpc_id, AWS_RESOURCES['vpc_security_group_name']
    )
    if sg_id:
        try:
            ec2_client.delete_security_group(GroupId=sg_id)
            print(f"Deleted security group: {sg_id}")
        except ClientError as e:
            print(f"Could not delete security group: {e}")

    # Delete subnets
    subnet_ids = find_subnets_by_vpc(ec2_client, vpc_id)
    for subnet_id in subnet_ids:
        try:
            ec2_client.delete_subnet(SubnetId=subnet_id)
            print(f"Deleted subnet: {subnet_id}")
        except ClientError as e:
            print(f"Could not delete subnet {subnet_id}: {e}")

    # Delete custom route tables
    route_table_ids = find_route_tables_by_vpc(ec2_client, vpc_id)
    for rt_id in route_table_ids:
        try:
            ec2_client.delete_route_table(RouteTableId=rt_id)
            print(f"Deleted route table: {rt_id}")
        except ClientError as e:
            print(f"Could not delete route table {rt_id}: {e}")

    # Detach and delete Internet Gateway
    igw_id = find_igw_by_vpc(ec2_client, vpc_id)
    if igw_id:
        try:
            ec2_client.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
            ec2_client.delete_internet_gateway(InternetGatewayId=igw_id)
            print(f"Deleted internet gateway: {igw_id}")
        except ClientError as e:
            print(f"Could not delete internet gateway: {e}")

    # Delete VPC
    try:
        ec2_client.delete_vpc(VpcId=vpc_id)
        print(f"Deleted VPC: {vpc_id}")
    except ClientError as e:
        print(f"Could not delete VPC: {e}")

    print('Teardown complete!')

if __name__ == '__main__':
    tear_down_aws_etl()