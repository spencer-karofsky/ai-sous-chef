"""
Defines interfaces for all DynamoBD Functionalities.

Table Manager:
1. Create Table
2. Delete Table
3. List Tables
4. Wait for Table Active

Item Manager:
1. Put Item
2. Get Item
3. Scan Table
4. Delete Item
5. Update Item
"""
from typing import Protocol, List, Dict

class DynamoDBTableInterface(Protocol):
    def create_table(
        self,
        table_name: str,
        partition_key: str,
        partition_key_type: str,
        sort_key: str = None,
        sort_key_type: str = None,
        billing_mode: str = 'PAY_PER_REQUEST',
    ) -> bool:
        raise NotImplementedError

    def delete_table(
        self,
        table_name: str,
    ) -> bool:
        raise NotImplementedError

    def list_tables(self) -> List[str]:
        raise NotImplementedError

    def wait_table_active(
        self,
        table_name: str,
        timeout: int = 300,
    ) -> bool:
        raise NotImplementedError
    
class DynamoDBItemInterface(Protocol):
    def put_item(
        self,
        table_name: str,
        item: Dict,
    ) -> bool:
        raise NotImplementedError

    def batch_write_items(
        self,
        table_name: str,
        items: List[Dict],
    ) -> bool:
        raise NotImplementedError

    def get_item(
        self,
        table_name: str,
        key: Dict,
    ) -> Dict | None:
        raise NotImplementedError

    def query(
        self,
        table_name: str,
        key_condition: str,
        expression_values: Dict,
        filter_expression: str = None,
    ) -> List[Dict]:
        raise NotImplementedError

    def scan_table(
        self,
        table_name: str,
        filter_expression: str = None,
        expression_values: Dict = None,
        limit: int = None,
    ) -> List[Dict]:
        raise NotImplementedError

    def delete_item(
        self,
        table_name: str,
        key: Dict,
    ) -> bool:
        raise NotImplementedError

    def update_item(
        self,
        table_name: str,
        key: Dict,
        update_expression: str,
        expression_values: Dict,
    ) -> bool:
        raise NotImplementedError