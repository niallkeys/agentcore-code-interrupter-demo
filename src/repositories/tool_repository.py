"""Repository for tool metadata CRUD operations"""

from datetime import datetime
from typing import List, Optional
from boto3.dynamodb.conditions import Key, Attr

from ..models.tool_record import ToolRecord, ToolStatus
from ..models.errors import StorageError
from .dynamodb_client import DynamoDBClient


class ToolRepository:
    """Repository for managing tool records in DynamoDB"""
    
    # GSI names from Terraform configuration
    AGENT_INDEX = "agentId-index"
    CODE_HASH_INDEX = "codeHash-index"
    
    def __init__(self, dynamodb_client: Optional[DynamoDBClient] = None):
        """
        Initialize tool repository
        
        Args:
            dynamodb_client: DynamoDB client instance (creates new if not provided)
        """
        self.client = dynamodb_client or DynamoDBClient()
    
    def create(self, tool_record: ToolRecord) -> ToolRecord:
        """
        Create a new tool record
        
        Args:
            tool_record: Tool record to create
            
        Returns:
            Created tool record
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            item = tool_record.to_dynamodb_item()
            self.client.put_item(item)
            return tool_record
        except Exception as e:
            raise StorageError(
                f"Failed to create tool record: {str(e)}",
                operation="create",
                resource=tool_record.tool_id,
            )
    
    def get_by_id(self, tool_id: str) -> Optional[ToolRecord]:
        """
        Get a tool record by ID
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool record if found, None otherwise
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            item = self.client.get_item({"toolId": tool_id})
            if item:
                return ToolRecord.from_dynamodb_item(item)
            return None
        except Exception as e:
            raise StorageError(
                f"Failed to get tool record: {str(e)}",
                operation="get_by_id",
                resource=tool_id,
            )
    
    def update(self, tool_record: ToolRecord) -> ToolRecord:
        """
        Update an existing tool record
        
        Args:
            tool_record: Tool record with updated values
            
        Returns:
            Updated tool record
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            # Update timestamp
            tool_record.updated_at = datetime.utcnow().isoformat()
            
            # Build update expression
            update_parts = []
            attr_values = {}
            attr_names = {}
            
            # Update all mutable fields
            update_parts.append("#name = :name")
            attr_names["#name"] = "name"
            attr_values[":name"] = tool_record.name
            
            update_parts.append("#desc = :desc")
            attr_names["#desc"] = "description"
            attr_values[":desc"] = tool_record.description
            
            update_parts.append("#version = :version")
            attr_names["#version"] = "version"
            attr_values[":version"] = tool_record.version
            
            update_parts.append("#status = :status")
            attr_names["#status"] = "status"
            attr_values[":status"] = tool_record.status.value
            
            update_parts.append("codeArtifactS3Key = :s3key")
            attr_values[":s3key"] = tool_record.code_artifact_s3_key
            
            update_parts.append("#schema = :schema")
            attr_names["#schema"] = "schema"
            attr_values[":schema"] = tool_record.schema.to_dict()
            
            update_parts.append("updatedAt = :updated")
            attr_values[":updated"] = tool_record.updated_at
            
            update_parts.append("#metadata = :metadata")
            attr_names["#metadata"] = "metadata"
            attr_values[":metadata"] = tool_record.metadata
            
            update_expression = "SET " + ", ".join(update_parts)
            
            self.client.update_item(
                key={"toolId": tool_record.tool_id},
                update_expression=update_expression,
                expression_attribute_values=attr_values,
                expression_attribute_names=attr_names,
            )
            
            return tool_record
        except Exception as e:
            raise StorageError(
                f"Failed to update tool record: {str(e)}",
                operation="update",
                resource=tool_record.tool_id,
            )
    
    def delete(self, tool_id: str) -> None:
        """
        Delete a tool record
        
        Args:
            tool_id: Tool ID
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            self.client.delete_item({"toolId": tool_id})
        except Exception as e:
            raise StorageError(
                f"Failed to delete tool record: {str(e)}",
                operation="delete",
                resource=tool_id,
            )
    
    def find_by_agent_id(self, agent_id: str, limit: Optional[int] = None) -> List[ToolRecord]:
        """
        Find all tools created by a specific agent
        
        Args:
            agent_id: Agent ID
            limit: Maximum number of results
            
        Returns:
            List of tool records
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            items = self.client.query(
                key_condition_expression="agentId = :agent_id",
                expression_attribute_values={":agent_id": agent_id},
                index_name=self.AGENT_INDEX,
                limit=limit,
            )
            
            return [ToolRecord.from_dynamodb_item(item) for item in items]
        except Exception as e:
            raise StorageError(
                f"Failed to find tools by agent: {str(e)}",
                operation="find_by_agent_id",
                resource=agent_id,
            )
    
    def find_by_code_hash(self, code_hash: str) -> Optional[ToolRecord]:
        """
        Find a tool by its code hash (for cache lookup)
        
        Args:
            code_hash: SHA-256 hash of the code
            
        Returns:
            Tool record if found, None otherwise
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            items = self.client.query(
                key_condition_expression="codeHash = :code_hash",
                expression_attribute_values={":code_hash": code_hash},
                index_name=self.CODE_HASH_INDEX,
                limit=1,
            )
            
            if items:
                return ToolRecord.from_dynamodb_item(items[0])
            return None
        except Exception as e:
            raise StorageError(
                f"Failed to find tool by code hash: {str(e)}",
                operation="find_by_code_hash",
                resource=code_hash,
            )
    
    def find_active_tools(self, limit: Optional[int] = None) -> List[ToolRecord]:
        """
        Find all active tools
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of active tool records
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            items = self.client.scan(
                filter_expression="#status = :status",
                expression_attribute_values={":status": ToolStatus.ACTIVE.value},
                expression_attribute_names={"#status": "status"},
                limit=limit,
            )
            
            return [ToolRecord.from_dynamodb_item(item) for item in items]
        except Exception as e:
            raise StorageError(
                f"Failed to find active tools: {str(e)}",
                operation="find_active_tools",
            )
    
    def increment_execution_count(self, tool_id: str) -> None:
        """
        Increment the execution count for a tool
        
        Args:
            tool_id: Tool ID
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            now = datetime.utcnow().isoformat()
            
            self.client.update_item(
                key={"toolId": tool_id},
                update_expression="SET executionCount = executionCount + :inc, lastExecuted = :now",
                expression_attribute_values={
                    ":inc": 1,
                    ":now": now,
                },
            )
        except Exception as e:
            raise StorageError(
                f"Failed to increment execution count: {str(e)}",
                operation="increment_execution_count",
                resource=tool_id,
            )
    
    def update_status(self, tool_id: str, status: ToolStatus) -> None:
        """
        Update the status of a tool
        
        Args:
            tool_id: Tool ID
            status: New status
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            now = datetime.utcnow().isoformat()
            
            self.client.update_item(
                key={"toolId": tool_id},
                update_expression="SET #status = :status, updatedAt = :now",
                expression_attribute_values={
                    ":status": status.value,
                    ":now": now,
                },
                expression_attribute_names={"#status": "status"},
            )
        except Exception as e:
            raise StorageError(
                f"Failed to update tool status: {str(e)}",
                operation="update_status",
                resource=tool_id,
            )
