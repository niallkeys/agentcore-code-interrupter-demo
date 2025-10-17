"""Artifact storage service for code caching and retrieval"""

import hashlib
import json
from datetime import datetime
from typing import Optional

from ..models.cached_artifact import CachedToolArtifact, ValidationResult, ExecutionMetadata
from ..models.errors import StorageError
from .s3_client import S3Client


class ArtifactStorage:
    """Service for storing and retrieving cached tool artifacts"""
    
    # S3 key prefixes
    ARTIFACTS_PREFIX = "artifacts"
    CODE_PREFIX = "code"
    
    def __init__(self, s3_client: Optional[S3Client] = None):
        """
        Initialize artifact storage
        
        Args:
            s3_client: S3 client instance (creates new if not provided)
        """
        self.s3_client = s3_client or S3Client()
    
    @staticmethod
    def compute_code_hash(code: str, language: str = "python") -> str:
        """
        Compute SHA-256 hash of code for content-based addressing
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            SHA-256 hash as hex string
        """
        # Normalize code before hashing
        normalized = code.strip()
        
        # Include language in hash to differentiate same code in different languages
        content = f"{language}:{normalized}"
        
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def _get_artifact_key(self, code_hash: str) -> str:
        """
        Get S3 key for artifact
        
        Args:
            code_hash: Code hash
            
        Returns:
            S3 key
        """
        return f"{self.ARTIFACTS_PREFIX}/{code_hash}.json"
    
    def _get_code_key(self, code_hash: str, language: str) -> str:
        """
        Get S3 key for raw code
        
        Args:
            code_hash: Code hash
            language: Programming language
            
        Returns:
            S3 key
        """
        extension = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
        }.get(language, "txt")
        
        return f"{self.CODE_PREFIX}/{code_hash}.{extension}"
    
    def store_artifact(self, artifact: CachedToolArtifact) -> str:
        """
        Store a cached tool artifact
        
        Args:
            artifact: Cached tool artifact
            
        Returns:
            S3 key where artifact was stored
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            key = self._get_artifact_key(artifact.code_hash)
            
            # Store artifact metadata as JSON
            self.s3_client.put_json(
                key=key,
                data=artifact.to_dict(),
                metadata={
                    "code-hash": artifact.code_hash,
                    "language": artifact.language,
                    "usage-count": str(artifact.usage_count),
                },
            )
            
            # Also store raw validated code separately for quick access
            code_key = self._get_code_key(artifact.code_hash, artifact.language)
            self.s3_client.put_object(
                key=code_key,
                body=artifact.validated_code.encode("utf-8"),
                content_type="text/plain",
                metadata={
                    "code-hash": artifact.code_hash,
                    "language": artifact.language,
                },
            )
            
            return key
        except Exception as e:
            raise StorageError(
                f"Failed to store artifact: {str(e)}",
                operation="store_artifact",
                resource=artifact.code_hash,
            )
    
    def retrieve_artifact(self, code_hash: str) -> Optional[CachedToolArtifact]:
        """
        Retrieve a cached tool artifact by code hash
        
        Args:
            code_hash: SHA-256 hash of the code
            
        Returns:
            Cached artifact if found, None otherwise
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            key = self._get_artifact_key(code_hash)
            data = self.s3_client.get_json(key)
            
            if data is None:
                return None
            
            return CachedToolArtifact.from_dict(data)
        except Exception as e:
            raise StorageError(
                f"Failed to retrieve artifact: {str(e)}",
                operation="retrieve_artifact",
                resource=code_hash,
            )
    
    def retrieve_code(self, code_hash: str, language: str) -> Optional[str]:
        """
        Retrieve validated code by hash
        
        Args:
            code_hash: SHA-256 hash of the code
            language: Programming language
            
        Returns:
            Validated code if found, None otherwise
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            key = self._get_code_key(code_hash, language)
            content = self.s3_client.get_object(key)
            
            if content is None:
                return None
            
            return content.decode("utf-8")
        except Exception as e:
            raise StorageError(
                f"Failed to retrieve code: {str(e)}",
                operation="retrieve_code",
                resource=code_hash,
            )
    
    def artifact_exists(self, code_hash: str) -> bool:
        """
        Check if an artifact exists in cache
        
        Args:
            code_hash: SHA-256 hash of the code
            
        Returns:
            True if artifact exists, False otherwise
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            key = self._get_artifact_key(code_hash)
            return self.s3_client.object_exists(key)
        except Exception as e:
            raise StorageError(
                f"Failed to check artifact existence: {str(e)}",
                operation="artifact_exists",
                resource=code_hash,
            )
    
    def update_usage_count(self, code_hash: str) -> None:
        """
        Increment usage count for an artifact
        
        Args:
            code_hash: SHA-256 hash of the code
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            # Retrieve current artifact
            artifact = self.retrieve_artifact(code_hash)
            if artifact is None:
                raise StorageError(
                    f"Artifact not found: {code_hash}",
                    operation="update_usage_count",
                    resource=code_hash,
                )
            
            # Increment usage count
            artifact.increment_usage()
            
            # Store updated artifact
            self.store_artifact(artifact)
        except Exception as e:
            raise StorageError(
                f"Failed to update usage count: {str(e)}",
                operation="update_usage_count",
                resource=code_hash,
            )
    
    def delete_artifact(self, code_hash: str, language: str) -> None:
        """
        Delete an artifact and its associated code
        
        Args:
            code_hash: SHA-256 hash of the code
            language: Programming language
            
        Raises:
            StorageError: If the operation fails
        """
        try:
            # Delete artifact metadata
            artifact_key = self._get_artifact_key(code_hash)
            self.s3_client.delete_object(artifact_key)
            
            # Delete raw code
            code_key = self._get_code_key(code_hash, language)
            self.s3_client.delete_object(code_key)
        except Exception as e:
            raise StorageError(
                f"Failed to delete artifact: {str(e)}",
                operation="delete_artifact",
                resource=code_hash,
            )
    
    def create_artifact_bundle(
        self,
        code: str,
        language: str,
        validation_result: ValidationResult,
        execution_metadata: ExecutionMetadata,
        dependencies: Optional[list] = None,
    ) -> CachedToolArtifact:
        """
        Create a new artifact bundle from validation results
        
        Args:
            code: Validated source code
            language: Programming language
            validation_result: Validation result
            execution_metadata: Execution metadata
            dependencies: List of dependencies
            
        Returns:
            Created cached artifact
        """
        code_hash = self.compute_code_hash(code, language)
        now = datetime.utcnow().isoformat()
        
        return CachedToolArtifact(
            code_hash=code_hash,
            validated_code=code,
            validation_result=validation_result,
            dependencies=dependencies or [],
            execution_metadata=execution_metadata,
            created_at=now,
            usage_count=0,
            language=language,
            original_code=code,
        )
