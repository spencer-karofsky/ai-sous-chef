"""
Implements IAM functionalities.
"""
from infra.utils.logger import logger
from botocore.exceptions import ClientError
from infra.interfaces.iam_interface import IAMRoleInterface
from botocore.client import BaseClient
from typing import Optional

class IAMRoleManager(IAMRoleInterface):
    def __init__(self, iam_client: BaseClient):
        """Initialize IAM resources
        Args:
            iam_client: the IAM client, injectable for unit testing
        """
        self.client = iam_client

    def create_role(self,
                    role_name: str,
                    policy_doc: Optional[str] = None) -> bool:
        """Creates a role with permissions
        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/create_role.html
        Args:
            role_name: the name of the role
            policy_doc: the permissions, in JSON format
        Return:
            True/False to indicate success/failure
        """
        try:
            self.client.create_role(RoleName=role_name,
                                    AssumeRolePolicyDocument=policy_doc)
        except ClientError as e:
            logger.error(f'[FAIL] cannot create IAM Role ({e})')
            return False
        logger.info(f'[SUCCESS] created IAM Role')
        return True

    def get_role_arn(self, role_name: str) -> str:
        """Gets the role ARN
        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/get_role.html
        Args:
            role_name: The name of the ARN role in IAM
        Return:
            The role ARN if retrieval is successful, otherwise the function returns an empty string.
        """
        try:
            response = self.client.get_role(RoleName=role_name)
        except ClientError as e:
            logger.error(f'[FAIL] cannot retrieve the ARN for the IAM Role ({e})')
            return ''
        
        # Extract Role ID
        arn = response['Role']['Arn']

        logger.info(f'[SUCCESS] retrieved and returned the ARN for the IAM Role')
        return arn

    def attach_policy(self, role_name: str, policy_arn: str) -> bool:
        """Attach a managed policy to a role
        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/attach_role_policy.html
        Args:
            role_name: the IAM role name
            policy_arn: the ARN of the managed policy
        Return:
            True/False to indicate success/failure
        """
        try:
            self.client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        except ClientError as e:
            logger.error(f'[FAIL] cannot attach policy to role ({e})')
            return False
        logger.info(f'[SUCCESS] attached policy "{policy_arn}" to role "{role_name}"')
        return True

    def create_instance_profile(self, profile_name: str) -> bool:
        """Create an instance profile for EC2
        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/create_instance_profile.html
        Args:
            profile_name: name for the instance profile
        Return:
            True/False to indicate success/failure
        """
        try:
            self.client.create_instance_profile(InstanceProfileName=profile_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                logger.info(f'[SKIP] instance profile "{profile_name}" already exists')
                return True
            logger.error(f'[FAIL] cannot create instance profile ({e})')
            return False
        logger.info(f'[SUCCESS] created instance profile "{profile_name}"')
        return True

    def add_role_to_instance_profile(self, profile_name: str, role_name: str) -> bool:
        """Add a role to an instance profile
        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/add_role_to_instance_profile.html
        Args:
            profile_name: the instance profile name
            role_name: the IAM role name
        Return:
            True/False to indicate success/failure
        """
        try:
            self.client.add_role_to_instance_profile(
                InstanceProfileName=profile_name,
                RoleName=role_name
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'LimitExceeded':
                logger.info(f'[SKIP] role already attached to instance profile')
                return True
            logger.error(f'[FAIL] cannot add role to instance profile ({e})')
            return False
        logger.info(f'[SUCCESS] added role "{role_name}" to instance profile "{profile_name}"')
        return True
