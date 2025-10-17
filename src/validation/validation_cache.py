"""Validation result caching system"""

import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from .validation_result import ValidationResult as DetailedValidationResult
from .security_policy import SecurityPolicy, SecurityPolicyManager
from ..models.cached_artifact import (
    CachedToolArtifact,
    ValidationResult,
    ExecutionMetadata,
)
from ..models.errors import StorageError
from ..storage.artifact_storage import ArtifactStorage


class ValidationCache:
    """
    Manages caching of validation results in S3
    """
    
    # S3 key prefix for validation results
    VALIDATION_PREFIX = "validation-results"
    POLICY_PREFIX = "policies"
    AUDIT_PREFIX = "audit-logs"
    
    def __init__(self, artifact_storage: Optional[ArtifactStorage] = None):
        """
        Initialize validation cache
        
        Args:
            artifact_storage: Artifact storage instance
        """
        self.storage = artifact_storage or ArtifactStorage()
    
    def get_cached_validation(
        self,
        code: str,
        language: str,
    ) -> Optional[DetailedValidationResult]:
        """
        Retrieve cached validation result for code
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Cached validation result if found, None otherwise
        """
        try:
            code_hash = self.storage.compute_code_hash(code, language)
            
            # Check if artifact exists
            if not self.storage.artifact_exists(code_hash):
                return None
            
            # Retrieve artifact
            artifact = self.storage.retrieve_artifact(code_hash)
            if artifact is None:
                return None
            
            # Convert to detailed validation result
            return self._convert_to_detailed_result(
                artifact.validation_result,
                code_hash,
                language,
            )
        
        except Exception as e:
            # Log error but don't fail - just return None to trigger re-validation
            print(f"Error retrieving cached validation: {e}")
            return None
    
    def cache_validation_result(
        self,
        code: str,
        language: str,
        validation_result: DetailedValidationResult,
        dependencies: Optional[List[str]] = None,
    ) -> str:
        """
        Cache validation result in S3
        
        Args:
            code: Validated source code
            language: Programming language
            validation_result: Detailed validation result
            dependencies: List of dependencies
            
        Returns:
            Code hash of cached artifact
            
        Raises:
            StorageError: If caching fails
        """
        try:
            code_hash = self.storage.compute_code_hash(code, language)
            
            # Convert detailed validation result to simple format
            simple_result = self._convert_to_simple_result(validation_result)
            
            # Create execution metadata from resource estimate
            execution_metadata = self._create_execution_metadata(validation_result)
            
            # Create artifact bundle
            artifact = self.storage.create_artifact_bundle(
                code=code,
                language=language,
                validation_result=simple_result,
                execution_metadata=execution_metadata,
                dependencies=dependencies,
            )
            
            # Store artifact
            self.storage.store_artifact(artifact)
            
            # Log to audit trail
            self._log_validation_audit(
                code_hash=code_hash,
                language=language,
                is_valid=validation_result.is_valid,
                has_critical_issues=validation_result.has_critical_issues(),
            )
            
            return code_hash
        
        except Exception as e:
            raise StorageError(
                f"Failed to cache validation result: {str(e)}",
                operation="cache_validation_result",
            )
    
    def invalidate_cache(self, code_hash: str, language: str) -> None:
        """
        Invalidate cached validation result
        
        Args:
            code_hash: Code hash to invalidate
            language: Programming language
            
        Raises:
            StorageError: If invalidation fails
        """
        try:
            self.storage.delete_artifact(code_hash, language)
            
            # Log invalidation
            self._log_validation_audit(
                code_hash=code_hash,
                language=language,
                is_valid=False,
                has_critical_issues=False,
                action="invalidated",
            )
        
        except Exception as e:
            raise StorageError(
                f"Failed to invalidate cache: {str(e)}",
                operation="invalidate_cache",
                resource=code_hash,
            )
    
    def invalidate_all_for_policy_update(self, policy_id: str) -> int:
        """
        Invalidate all cached results when security policy is updated
        
        Args:
            policy_id: ID of the updated policy
            
        Returns:
            Number of cache entries invalidated
            
        Note:
            This is a placeholder - full implementation would require
            listing all artifacts and checking their policy versions
        """
        # Log policy update
        self._log_policy_update(policy_id)
        
        # In a full implementation, this would:
        # 1. List all artifacts in S3
        # 2. Check which ones were validated with the old policy
        # 3. Delete those artifacts
        # For now, return 0 as this is a complex operation
        return 0
    
    def store_policy(self, policy: SecurityPolicy) -> str:
        """
        Store security policy in S3 for audit purposes
        
        Args:
            policy: Security policy to store
            
        Returns:
            S3 key where policy was stored
        """
        try:
            key = f"{self.POLICY_PREFIX}/{policy.policy_id}-{policy.version}.json"
            
            self.storage.s3_client.put_json(
                key=key,
                data=policy.to_dict(),
                metadata={
                    "policy-id": policy.policy_id,
                    "version": policy.version,
                },
            )
            
            return key
        
        except Exception as e:
            raise StorageError(
                f"Failed to store policy: {str(e)}",
                operation="store_policy",
                resource=policy.policy_id,
            )
    
    def _convert_to_simple_result(
        self,
        detailed: DetailedValidationResult,
    ) -> ValidationResult:
        """Convert detailed validation result to simple format"""
        return ValidationResult(
            is_valid=detailed.is_valid,
            errors=detailed.errors,
            warnings=detailed.warnings,
            security_issues=[issue.message for issue in detailed.security_issues],
        )
    
    def _convert_to_detailed_result(
        self,
        simple: ValidationResult,
        code_hash: str,
        language: str,
    ) -> DetailedValidationResult:
        """Convert simple validation result to detailed format"""
        from .validation_result import SecurityIssue, SeverityLevel
        
        # Convert security issues back to detailed format
        security_issues = [
            SecurityIssue(
                severity=SeverityLevel.HIGH,  # Default severity for cached issues
                issue_type="cached_issue",
                message=issue,
            )
            for issue in simple.security_issues
        ]
        
        return DetailedValidationResult(
            is_valid=simple.is_valid,
            language=language,
            code_hash=code_hash,
            errors=simple.errors,
            warnings=simple.warnings,
            security_issues=security_issues,
            resource_estimate=None,  # Not stored in simple format
        )
    
    def _create_execution_metadata(
        self,
        validation_result: DetailedValidationResult,
    ) -> ExecutionMetadata:
        """Create execution metadata from validation result"""
        if validation_result.resource_estimate:
            est = validation_result.resource_estimate
            return ExecutionMetadata(
                estimated_memory_mb=est.estimated_memory_mb,
                estimated_cpu_ms=int(est.estimated_cpu_seconds * 1000),
                timeout_seconds=30,  # Default timeout
                requires_network=False,
                requires_filesystem=False,
            )
        else:
            # Default values if no estimate available
            return ExecutionMetadata(
                estimated_memory_mb=128,
                estimated_cpu_ms=1000,
                timeout_seconds=30,
                requires_network=False,
                requires_filesystem=False,
            )
    
    def _log_validation_audit(
        self,
        code_hash: str,
        language: str,
        is_valid: bool,
        has_critical_issues: bool,
        action: str = "validated",
    ) -> None:
        """
        Log validation event to audit trail
        
        Args:
            code_hash: Code hash
            language: Programming language
            is_valid: Whether validation passed
            has_critical_issues: Whether critical issues were found
            action: Action performed (validated, invalidated, etc.)
        """
        try:
            timestamp = datetime.utcnow().isoformat() + "Z"
            audit_entry = {
                "timestamp": timestamp,
                "action": action,
                "codeHash": code_hash,
                "language": language,
                "isValid": is_valid,
                "hasCriticalIssues": has_critical_issues,
            }
            
            # Create audit log key with timestamp for uniqueness
            date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
            key = f"{self.AUDIT_PREFIX}/{date_prefix}/{code_hash}-{timestamp}.json"
            
            self.storage.s3_client.put_json(
                key=key,
                data=audit_entry,
                metadata={
                    "code-hash": code_hash,
                    "action": action,
                },
            )
        
        except Exception as e:
            # Don't fail validation if audit logging fails
            print(f"Warning: Failed to log validation audit: {e}")
    
    def _log_policy_update(self, policy_id: str) -> None:
        """
        Log security policy update
        
        Args:
            policy_id: ID of updated policy
        """
        try:
            timestamp = datetime.utcnow().isoformat() + "Z"
            audit_entry = {
                "timestamp": timestamp,
                "action": "policy_updated",
                "policyId": policy_id,
            }
            
            date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
            key = f"{self.AUDIT_PREFIX}/{date_prefix}/policy-{policy_id}-{timestamp}.json"
            
            self.storage.s3_client.put_json(
                key=key,
                data=audit_entry,
                metadata={"policy-id": policy_id},
            )
        
        except Exception as e:
            print(f"Warning: Failed to log policy update: {e}")
