"""
Implements all DynamoDB functionalities.
"""
from infra.utils.logger import logger
from infra.interfaces.dynamodb_interface import DynamoDBTableInterface, DynamoDBItemInterface
from botocore.exceptions import ClientError
from botocore.client import BaseClient
from typing import List, Dict, Optional
from time import sleep

class DynamoDBTableManager(DynamoDBTableInterface):
    def __init__(
            self,
            dynamodb_client: BaseClient
    ) -> None:
        """
        Creates object to manage DynamoDB tables

        Args:
            dynamodb_client: the injected boto3 client for DynamoDB
        """
        self.client = dynamodb_client
        self.tables = []
        self.table_names = []

    def create_table(
        self,
        table_name: str,
        partition_key: str,
        partition_key_type: str,
        sort_key: str = None,
        sort_key_type: str = None,
        billing_mode: str = 'PAY_PER_REQUEST',
    ) -> bool:
        """
        Attempts to Create a DynamoDB Table

        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/create_table.html
        
        Args:
            table_name: the table name
            partition_key: the primary key
            partition_key_type: either string ('S'), number ('N'), or binary ('B')
            sort_key: enables storing multiple items with the same primary key
            sort_key_type: either string ('S'), number ('N'), or binary ('B')
            billing_mode: either 'PAY_PER_REQUEST' (more flexible) or 'PROVISIONED' (safer)
        
        Returns:
            True/False to indicate success/failure
        """
        KEY_TYPES = ['S', 'N', 'B']
        BILLING_TYPES = ['PAY_PER_REQUEST', 'PROVISIONED']

        # Parameter validation
        assert isinstance(table_name, str), 'table_name must be a string'
        assert isinstance(partition_key, str), 'partition_key must be a string'
        assert partition_key_type in KEY_TYPES, f'partition_key_type must be one of {KEY_TYPES}'
        assert billing_mode in BILLING_TYPES, f'billing_mode must be one of {BILLING_TYPES}'
        
        if sort_key:
            assert isinstance(sort_key, str), 'sort_key must be a string'
            assert sort_key_type in KEY_TYPES, f'sort_key_type must be one of {KEY_TYPES}'

        # Build attribute definitions
        attribute_definitions = [
            {'AttributeName': partition_key, 'AttributeType': partition_key_type}
        ]
        
        # Build key schema
        key_schema = [
            {'AttributeName': partition_key, 'KeyType': 'HASH'}
        ]
        
        # Add sort key if provided
        if sort_key:
            attribute_definitions.append(
                {'AttributeName': sort_key, 'AttributeType': sort_key_type}
            )
            key_schema.append(
                {'AttributeName': sort_key, 'KeyType': 'RANGE'}
            )

        # Attempt to create table
        try:
            response = self.client.create_table(
                TableName=table_name,
                AttributeDefinitions=attribute_definitions,
                KeySchema=key_schema,
                BillingMode=billing_mode,
            )
        except ClientError as e:
            logger.error(f'[FAIL] Cannot create DynamoDB table ({e})')
            return False

        # Store table info
        self.tables.append({
            'TableName': table_name,
            'TableArn': response['TableDescription']['TableArn'],
            'TableStatus': response['TableDescription']['TableStatus'],
        })
        self.table_names.append(table_name)

        logger.info(f'[SUCCESS] Created DynamoDB table "{table_name}"')
        return True

    def delete_table(
        self,
        table_name: str,
    ) -> bool:
        """
        Attempts to Delete an Existing DynamoDB Table

        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/delete_table.html

        Args:
            table_name: to identify the table name

        Returns:
            True/False to indicate success/failure
        """
        # Validate table_name is a string and corresponds to an existing table
        assert isinstance(table_name, str), 'table_name must be a string'

        if table_name not in self.table_names:
            raise Exception(f'{table_name} not an existing table; choose to delete one of {self.table_names}')
        
        try:
            self.client.delete_table(
                TableName=table_name
            )
        except Exception as e:
            logger.error(f'[FAIL] Cannot delete DynamoDB table ({e})')
            return False
        
        # Remove table from self.tables
        table_i = self.table_names.index(table_name)
        del self.tables[table_i]
        self.table_names.remove(table_name)

        logger.info(f'[SUCCESS] Deleted DynamoDB table "{table_name}"')
        return True

    def list_tables(self) -> List[str]:
        """
        Lists all DynamoDB tables
            * Instead of returning self.table_names, it queries from boto3
        
        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/list_tables.html
        
        Returns:
            list of table names
        """
        try:
            response = self.client.list_tables()
        except ClientError as e:
            logger.error(f'[FAIL] Cannot fetch DynamoDB table names ({e})')
            return False
        
        return response['TableNames']

    def wait_table_active(
        self,
        table_name: str,
        timeout: int = 120,
    ) -> bool:
        """
        Waits for DynamoDB table status to switch to 'ACTIVE'
            * Necessary to know when to interact with a new table after calling self.create_table
        
        Args:
            table_name: the table name
            timeout: how long to wait before timing out
        
        Returns:
            True/False to indicate success/failure
        """
        elapsed = 0
        poll_interval = 5

        while elapsed < timeout:
            try:
                response = self.client.describe_table(TableName=table_name)
                status = response['Table']['TableStatus']
                
                if status == 'ACTIVE':
                    logger.info(f'[SUCCESS] Table "{table_name}" is now ACTIVE')
                    return True
                
                logger.info(f'[WAITING] Table "{table_name}" status: {status}')
                
            except ClientError as e:
                logger.error(f'[FAIL] Cannot describe table "{table_name}" ({e})')
                return False

            sleep(poll_interval)
            elapsed += poll_interval

        logger.error(f'[FAIL] Timeout waiting for table "{table_name}" to become ACTIVE')
        return False
    
class DynamoDBItemManager(DynamoDBItemInterface):
    def __init__(
            self,
            dynamodb_client: BaseClient
    ) -> None:
        """
        Manages items within a DynamoDB table

        Args:
            dynamodb_client: the boto3 injected client for DynamoDB
        """
        self.client = dynamodb_client

    def _serialize_item(self, item: Dict) -> Dict:
        """
        Converts a Python dict to DynamoDB item format
        
        Args:
            item: plain Python dictionary
        
        Returns:
            DynamoDB-formatted item with type descriptors
        """
        from decimal import Decimal
        
        dynamo_item = {}
        for key, value in item.items():
            if value is None:
                continue # DynamoDB doesn't accept None
            elif isinstance(value, str):
                dynamo_item[key] = {'S': value}
            elif isinstance(value, bool): # Must check before int (bool is subclass of int)
                dynamo_item[key] = {'BOOL': value}
            elif isinstance(value, (int, float, Decimal)):
                dynamo_item[key] = {'N': str(value)}
            elif isinstance(value, list):
                dynamo_item[key] = {'L': [self._serialize_value(v) for v in value]}
            elif isinstance(value, dict):
                dynamo_item[key] = {'M': self._serialize_item(value)}
            else:
                dynamo_item[key] = {'S': str(value)} # Fallback to string
        
        return dynamo_item

    def _serialize_value(self, value) -> Dict:
        """Serialize a single value for use in lists"""
        from decimal import Decimal
        
        if value is None:
            return {'NULL': True}
        elif isinstance(value, str):
            return {'S': value}
        elif isinstance(value, bool):
            return {'BOOL': value}
        elif isinstance(value, (int, float, Decimal)):
            return {'N': str(value)}
        elif isinstance(value, list):
            return {'L': [self._serialize_value(v) for v in value]}
        elif isinstance(value, dict):
            return {'M': self._serialize_item(value)}
        else:
            return {'S': str(value)}
        
    def _deserialize_item(self, dynamo_item: Dict) -> Dict:
        """
        Converts DynamoDB item format back to plain Python dict

        Args:
            dynamo_item: DynamoDB-formatted item with type descriptors

        Returns:
            Plain Python dictionary
        """
        item = {}
        for key, value in dynamo_item.items():
            item[key] = self._deserialize_value(value)
        return item

    def _deserialize_value(self, value: Dict):
        """Deserialize a single DynamoDB value"""
        if 'S' in value:
            return value['S']
        elif 'N' in value:
            num_str = value['N']
            return int(num_str) if '.' not in num_str else float(num_str)
        elif 'BOOL' in value:
            return value['BOOL']
        elif 'NULL' in value:
            return None
        elif 'L' in value:
            return [self._deserialize_value(v) for v in value['L']]
        elif 'M' in value:
            return self._deserialize_item(value['M'])
        else:
            return None

    def put_item(
        self,
        table_name: str,
        item: Dict,
    ) -> bool:
        """
        Puts/Adds an entry to the table

        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/put_item.html

        Args:
            table_name: the table name
            item: dictionary of attribute names to values

        Returns:
            True/False to indicate success/failure
        """
        try:
            # Convert item to DynamoDB format
            dynamo_item = self._serialize_item(item)
            
            self.client.put_item(
                TableName=table_name,
                Item=dynamo_item
            )
        except ClientError as e:
            logger.error(f'[FAIL] Cannot put item into "{table_name}" ({e})')
            return False

        logger.info(f'[SUCCESS] Put item into "{table_name}"')
        return True

    def batch_write_items(
        self,
        table_name: str,
        items: List[Dict],
        max_retries: int = 5,
    ) -> tuple:
        """
        Batch writes multiple items to the table (max 25 per batch)

        Returns:
            Tuple of (total_written, total_failed)
        """
        BATCH_SIZE = 25

        batches = [items[i:i + BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]
        total_written = 0
        total_failed = 0

        for batch in batches:
            put_requests = [
                {'PutRequest': {'Item': self._serialize_item(item)}}
                for item in batch
            ]

            request_items = {table_name: put_requests}
            retries = 0
            batch_size = len(batch)

            while request_items and retries < max_retries:
                try:
                    response = self.client.batch_write_item(RequestItems=request_items)
                    unprocessed = response.get('UnprocessedItems', {})

                    if not unprocessed:
                        # All remaining items succeeded
                        remaining = len(request_items.get(table_name, []))
                        total_written += remaining
                        request_items = {}
                        break

                    # Some succeeded, some didn't
                    succeeded = len(request_items.get(table_name, [])) - len(unprocessed.get(table_name, []))
                    total_written += succeeded

                    request_items = unprocessed
                    retries += 1
                    sleep(2 ** retries * 0.1)

                except ClientError as e:
                    logger.error(f'[FAIL] Batch write failed ({e})')
                    total_failed += len(request_items.get(table_name, []))
                    request_items = {}
                    break

            # Count any items still unprocessed after retries
            if request_items:
                failed_count = len(request_items.get(table_name, []))
                total_failed += failed_count
                logger.warning(f'[WARNING] {failed_count} items unprocessed after retries')

        logger.info(f'[SUCCESS] Batch write complete: {total_written} written, {total_failed} failed')
        return (total_written, total_failed)

    def get_item(
        self,
        table_name: str,
        key: Dict,
    ) -> Optional[Dict]:
        """
        Retrieves a single item by its key

        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/get_item.html

        Args:
            table_name: the table name
            key: partition key (and sort key if applicable), e.g. {'recipe_id': '12345'}

        Returns:
            Deserialized item dict, or None if not found
        """
        try:
            dynamo_key = self._serialize_item(key)
            
            response = self.client.get_item(
                TableName=table_name,
                Key=dynamo_key
            )
        except ClientError as e:
            logger.error(f'[FAIL] Cannot get item from "{table_name}" ({e})')
            return None

        item = response.get('Item')
        if not item:
            logger.info(f'[INFO] Item not found in "{table_name}"')
            return None

        logger.info(f'[SUCCESS] Retrieved item from "{table_name}"')
        return self._deserialize_item(item)

    def query(
        self,
        table_name: str,
        key_condition: str,
        expression_values: Dict,
        filter_expression: str = None,
    ) -> List[Dict]:
        """
        Queries items by partition key (and optionally sort key)

        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/query.html

        Args:
            table_name: the table name
            key_condition: key condition expression, e.g. 'recipe_id = :id'
            expression_values: values for expression, e.g. {':id': '12345'}
            filter_expression: optional filter to apply after query

        Returns:
            List of deserialized items
        """
        try:
            dynamo_values = self._serialize_item(expression_values)

            kwargs = {
                'TableName': table_name,
                'KeyConditionExpression': key_condition,
                'ExpressionAttributeValues': dynamo_values,
            }

            if filter_expression:
                kwargs['FilterExpression'] = filter_expression

            items = []
            while True:
                response = self.client.query(**kwargs)
                items.extend(response.get('Items', []))

                # Handle pagination
                if 'LastEvaluatedKey' not in response:
                    break
                kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

        except ClientError as e:
            logger.error(f'[FAIL] Cannot query "{table_name}" ({e})')
            return []

        logger.info(f'[SUCCESS] Query returned {len(items)} items from "{table_name}"')
        return [self._deserialize_item(item) for item in items]

    def scan_table(
        self,
        table_name: str,
        filter_expression: str = None,
        expression_values: Dict = None,
        expression_names: Dict = None,
        limit: int = None,
    ) -> List[Dict]:
        """
        Scans entire table with optional filtering

        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/scan.html

        Args:
            table_name: the table name
            filter_expression: optional filter expression
            expression_values: values for filter expression
            limit: max number of items to return

        Returns:
            List of deserialized items
        """
        try:
            kwargs = {'TableName': table_name}

            if filter_expression:
                kwargs['FilterExpression'] = filter_expression
            if expression_values:
                kwargs['ExpressionAttributeValues'] = self._serialize_item(expression_values)
            if expression_names:
                kwargs['ExpressionAttributeNames'] = expression_names
            if limit:
                kwargs['Limit'] = limit

            items = []
            while True:
                response = self.client.scan(**kwargs)
                items.extend(response.get('Items', []))

                if limit and len(items) >= limit:
                    items = items[:limit]
                    break

                if 'LastEvaluatedKey' not in response:
                    break
                kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

        except ClientError as e:
            logger.error(f'[FAIL] Cannot scan "{table_name}" ({e})')
            return []

        logger.info(f'[SUCCESS] Scan returned {len(items)} items from "{table_name}"')
        return [self._deserialize_item(item) for item in items]

    def delete_item(
        self,
        table_name: str,
        key: Dict,
    ) -> bool:
        """
        Deletes a single item by its key

        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/delete_item.html

        Args:
            table_name: the table name
            key: partition key (and sort key if applicable)

        Returns:
            True/False to indicate success/failure
        """
        try:
            dynamo_key = self._serialize_item(key)

            self.client.delete_item(
                TableName=table_name,
                Key=dynamo_key
            )
        except ClientError as e:
            logger.error(f'[FAIL] Cannot delete item from "{table_name}" ({e})')
            return False

        logger.info(f'[SUCCESS] Deleted item from "{table_name}"')
        return True

    def update_item(
        self,
        table_name: str,
        key: Dict,
        update_expression: str,
        expression_values: Dict,
    ) -> bool:
        """
        Updates attributes of an existing item

        Docs:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/update_item.html

        Args:
            table_name: the table name
            key: partition key (and sort key if applicable)
            update_expression: update expression, e.g. 'SET rating = :r, review_count = :c'
            expression_values: values for expression, e.g. {':r': 4.5, ':c': 100}

        Returns:
            True/False to indicate success/failure
        """
        try:
            dynamo_key = self._serialize_item(key)
            dynamo_values = self._serialize_item(expression_values)

            self.client.update_item(
                TableName=table_name,
                Key=dynamo_key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=dynamo_values,
            )
        except ClientError as e:
            logger.error(f'[FAIL] Cannot update item in "{table_name}" ({e})')
            return False

        logger.info(f'[SUCCESS] Updated item in "{table_name}"')
        return True