"""S3 client wrapper with error handling"""

import os
import json
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from ..models.errors import StorageError


class S3Client:
    """Wrapper for S3 operations with error handling"""
    
    def __init__(self, bucket_name: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize S3 client
        
        Args:
            bucket_name: S3 bucket name (defaults to S3_BUCKET_NAME env var)
            region: AWS region (defaults to AWS_REGION env var or us-east-1)
        """
        self.bucket_name = bucket_name or os.environ.get("S3_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("S3 bucket name must be provided or set in S3_BUCKET_NAME")
        
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        
        try:
            self.s3_client = boto3.client("s3", region_name=self.region)
        except Exception as e:
            raise StorageError(
                f"Failed to initialize S3 client: {str(e)}",
                operation="initialize",
                resource=self.bucket_name,
            )
    
    def put_object(
        self,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Put an object into S3
        
        Args:
            key: S3 object key
            body: Object content as bytes
            content_type: Content type
            metadata: Object metadata
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            kwargs = {
                "Bucket": self.bucket_name,
                "Key": key,
                "Body": body,
                "ContentType": content_type,
            }
            
            if metadata:
                kwargs["Metadata"] = metadata
            
            self.s3_client.put_object(**kwargs)
        except ClientError as e:
            raise StorageError(
                f"Failed to put object: {e.response['Error']['Message']}",
                operation="put_object",
                resource=key,
            )
        except BotoCoreError as e:
            raise StorageError(
                f"Failed to put object: {str(e)}",
                operation="put_object",
                resource=key,
            )
    
    def get_object(self, key: str) -> Optional[bytes]:
        """
        Get an object from S3
        
        Args:
            key: S3 object key
            
        Returns:
            Object content as bytes if found, None otherwise
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise StorageError(
                f"Failed to get object: {e.response['Error']['Message']}",
                operation="get_object",
                resource=key,
            )
        except BotoCoreError as e:
            raise StorageError(
                f"Failed to get object: {str(e)}",
                operation="get_object",
                resource=key,
            )
    
    def delete_object(self, key: str) -> None:
        """
        Delete an object from S3
        
        Args:
            key: S3 object key
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            raise StorageError(
                f"Failed to delete object: {e.response['Error']['Message']}",
                operation="delete_object",
                resource=key,
            )
        except BotoCoreError as e:
            raise StorageError(
                f"Failed to delete object: {str(e)}",
                operation="delete_object",
                resource=key,
            )
    
    def object_exists(self, key: str) -> bool:
        """
        Check if an object exists in S3
        
        Args:
            key: S3 object key
            
        Returns:
            True if object exists, False otherwise
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise StorageError(
                f"Failed to check object existence: {e.response['Error']['Message']}",
                operation="object_exists",
                resource=key,
            )
        except BotoCoreError as e:
            raise StorageError(
                f"Failed to check object existence: {str(e)}",
                operation="object_exists",
                resource=key,
            )
    
    def get_object_metadata(self, key: str) -> Optional[Dict[str, str]]:
        """
        Get object metadata from S3
        
        Args:
            key: S3 object key
            
        Returns:
            Object metadata if found, None otherwise
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return response.get("Metadata", {})
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return None
            raise StorageError(
                f"Failed to get object metadata: {e.response['Error']['Message']}",
                operation="get_object_metadata",
                resource=key,
            )
        except BotoCoreError as e:
            raise StorageError(
                f"Failed to get object metadata: {str(e)}",
                operation="get_object_metadata",
                resource=key,
            )
    
    def put_json(self, key: str, data: Dict[str, Any], metadata: Optional[Dict[str, str]] = None) -> None:
        """
        Put a JSON object into S3
        
        Args:
            key: S3 object key
            data: Data to store as JSON
            metadata: Object metadata
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            json_bytes = json.dumps(data, indent=2).encode("utf-8")
            self.put_object(key, json_bytes, content_type="application/json", metadata=metadata)
        except Exception as e:
            raise StorageError(
                f"Failed to put JSON object: {str(e)}",
                operation="put_json",
                resource=key,
            )
    
    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a JSON object from S3
        
        Args:
            key: S3 object key
            
        Returns:
            Parsed JSON data if found, None otherwise
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            content = self.get_object(key)
            if content is None:
                return None
            return json.loads(content.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise StorageError(
                f"Failed to parse JSON object: {str(e)}",
                operation="get_json",
                resource=key,
            )
        except Exception as e:
            raise StorageError(
                f"Failed to get JSON object: {str(e)}",
                operation="get_json",
                resource=key,
            )
