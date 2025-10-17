"""Cached tool artifact data models"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    """Result of code validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "isValid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "securityIssues": self.security_issues,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationResult":
        """Create from dictionary"""
        return cls(
            is_valid=data["isValid"],
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            security_issues=data.get("securityIssues", []),
        )


@dataclass
class ExecutionMetadata:
    """Metadata about tool execution capabilities"""
    estimated_memory_mb: int
    estimated_cpu_ms: int
    timeout_seconds: int
    requires_network: bool = False
    requires_filesystem: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "estimatedMemoryMb": self.estimated_memory_mb,
            "estimatedCpuMs": self.estimated_cpu_ms,
            "timeoutSeconds": self.timeout_seconds,
            "requiresNetwork": self.requires_network,
            "requiresFilesystem": self.requires_filesystem,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionMetadata":
        """Create from dictionary"""
        return cls(
            estimated_memory_mb=data["estimatedMemoryMb"],
            estimated_cpu_ms=data["estimatedCpuMs"],
            timeout_seconds=data["timeoutSeconds"],
            requires_network=data.get("requiresNetwork", False),
            requires_filesystem=data.get("requiresFilesystem", False),
        )


@dataclass
class CachedToolArtifact:
    """Cached tool artifact stored in S3"""
    code_hash: str
    validated_code: str
    validation_result: ValidationResult
    dependencies: List[str]
    execution_metadata: ExecutionMetadata
    created_at: str
    usage_count: int = 0
    language: str = "python"
    original_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for S3 storage"""
        result = {
            "codeHash": self.code_hash,
            "validatedCode": self.validated_code,
            "validationResult": self.validation_result.to_dict(),
            "dependencies": self.dependencies,
            "executionMetadata": self.execution_metadata.to_dict(),
            "createdAt": self.created_at,
            "usageCount": self.usage_count,
            "language": self.language,
        }
        
        if self.original_code:
            result["originalCode"] = self.original_code
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachedToolArtifact":
        """Create from dictionary"""
        validation_result = ValidationResult.from_dict(data["validationResult"])
        execution_metadata = ExecutionMetadata.from_dict(data["executionMetadata"])
        
        return cls(
            code_hash=data["codeHash"],
            validated_code=data["validatedCode"],
            validation_result=validation_result,
            dependencies=data["dependencies"],
            execution_metadata=execution_metadata,
            created_at=data["createdAt"],
            usage_count=data.get("usageCount", 0),
            language=data.get("language", "python"),
            original_code=data.get("originalCode"),
        )
    
    def increment_usage(self) -> None:
        """Increment usage count"""
        self.usage_count += 1
