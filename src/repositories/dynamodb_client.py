"""DynamoDB client wrapper with connection and error handling"""

import os
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from ..models.errors import StorageError


class DynamoDBClient:
    """Wrapper for DynamoDB operations with error handling"""
    
    def __init__(self, table_name: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize DynamoDB client
        
        Args:
            table_name: DynamoDB table name (defaults to DYNAMODB_TABLE_NAME env var)
            region: AWS region (defaults to AWS_REGION env var or us-east-1)
        """
        self.table_name = table_name or os.environ.get("DYNAMODB_TABLE_NAME")
        if not self.table_name:
            raise ValueError("DynamoDB table name must be provided or set in DYNAMODB_TABLE_NAME")
        
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        
        try:
            self.dynamodb = boto3.resource("dynamodb", region_name=self.region)
            self.table = self.dynamodb.Table(self.table_name)
        except Exception as e:
            raise StorageError(
                f"Failed to initialize DynamoDB client: {str(e)}",
                operation="initialize",
                resource=self.table_name,
            )
    
    def put_item(self, item: Dict[str, Any]) -> None:
        """
        Put an item into DynamoDB
        
        Args:
            item: Item to store
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            self.table.put_item(Item=item)
        except ClientError as e:
            raise StorageError(
                f"Failed to put item: {e.response['Error']['Message']}",
                operation="put_item",
                resource=self.table_name,
            )
        except BotoCoreError as e:
            raise StorageError(
                f"Failed to put item: {str(e)}",
                operation="put_item",
                resource=self.table_name,
            )
    
    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get an item from DynamoDB
        
        Args:
            key: Primary key of the item
            
        Returns:
            Item if found, None otherwise
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            response = self.table.get_item(Key=key)
            return response.get("Item")
        except ClientError as e:
            raise StorageError(
                f"Failed to get item: {e.response['Error']['Message']}",
                operation="get_item",
                resource=self.table_name,
            )
        except BotoCoreError as e:
            raise StorageError(
                f"Failed to get item: {str(e)}",
                operation="get_item",
                resource=self.table_name,
            )
    
    def update_item(
        self,
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Update an item in DynamoDB
        
        Args:
            key: Primary key of the item
            update_expression: Update expression
            expression_attribute_values: Values for the update expression
            expression_attribute_names: Names for the update expression
            
        Returns:
            Updated item attributes
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            kwargs = {
                "Key": key,
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expression_attribute_values,
                "ReturnValues": "ALL_NEW",
            }
            
            if expression_attribute_names:
                kwargs["ExpressionAttributeNames"] = expression_attribute_names
            
            response = self.table.update_item(**kwargs)
            return response.get("Attributes", {})
        except ClientError as e:
            raise StorageError(
                f"Failed to update item: {e.response['Error']['Message']}",
                operation="update_item",
                resource=self.table_name,
            )
        except BotoCoreError as e:
            raise StorageError(
                f"Failed to update item: {str(e)}",
                operation="update_item",
                resource=self.table_name,
            )
    
    def delete_item(self, key: Dict[str, Any]) -> None:
        """
        Delete an item from DynamoDB
        
        Args:
            key: Primary key of the item
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            self.table.delete_item(Key=key)
        except ClientError as e:
            raise StorageError(
                f"Failed to delete item: {e.response['Error']['Message']}",
                operation="delete_item",
                resource=self.table_name,
            )
        except BotoCoreError as e:
            raise StorageError(
                f"Failed to delete item: {str(e)}",
                operation="delete_item",
                resource=self.table_name,
            )
    
    def query(
        self,
        key_condition_expression: str,
        expression_attribute_values: Dict[str, Any],
        index_name: Optional[str] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query items from DynamoDB
        
        Args:
            key_condition_expression: Key condition expression
            expression_attribute_values: Values for the expression
            index_name: Name of the GSI to query
            expression_attribute_names: Names for the expression
            limit: Maximum number of items to return
            
        Returns:
            List of items matching the query
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            kwargs = {
                "KeyConditionExpression": key_condition_expression,
                "ExpressionAttributeValues": expression_attribute_values,
            }
            
            if index_name:
                kwargs["IndexName"] = index_name
            
            if expression_attribute_names:
                kwargs["ExpressionAttributeNames"] = expression_attribute_names
            
            if limit:
                kwargs["Limit"] = limit
            
            response = self.table.query(**kwargs)
            return response.get("Items", [])
        except ClientError as e:
            raise StorageError(
                f"Failed to query items: {e.response['Error']['Message']}",
                operation="query",
                resource=self.table_name,
            )
        except BotoCoreError as e:
            raise StorageError(
                f"Failed to query items: {str(e)}",
                operation="query",
                resource=self.table_name,
            )
    
    def scan(
        self,
        filter_expression: Optional[str] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scan items from DynamoDB
        
        Args:
            filter_expression: Filter expression
            expression_attribute_values: Values for the expression
            expression_attribute_names: Names for the expression
            limit: Maximum number of items to return
            
        Returns:
            List of items matching the scan
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            kwargs = {}
            
            if filter_expression:
                kwargs["FilterExpression"] = filter_expression
            
            if expression_attribute_values:
                kwargs["ExpressionAttributeValues"] = expression_attribute_values
            
            if expression_attribute_names:
                kwargs["ExpressionAttributeNames"] = expression_attribute_names
            
            if limit:
                kwargs["Limit"] = limit
            
            response = self.table.scan(**kwargs)
            return response.get("Items", [])
        except ClientError as e:
            raise StorageError(
                f"Failed to scan items: {e.response['Error']['Message']}",
                operation="scan",
                resource=self.table_name,
            )
        except BotoCoreError as e:
            raise StorageError(
                f"Failed to scan items: {str(e)}",
                operation="scan",
                resource=self.table_name,
            )
