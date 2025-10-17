"""Validation result data models"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class SeverityLevel(str, Enum):
    """Severity levels for validation issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityIssue:
    """Security issue found during validation"""
    severity: SeverityLevel
    issue_type: str
    message: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "severity": self.severity.value,
            "issueType": self.issue_type,
            "message": self.message,
        }
        if self.line_number is not None:
            result["lineNumber"] = self.line_number
        if self.code_snippet:
            result["codeSnippet"] = self.code_snippet
        return result


@dataclass
class ResourceEstimate:
    """Estimated resource usage for code execution"""
    estimated_memory_mb: int
    estimated_cpu_seconds: float
    complexity_score: int
    has_loops: bool
    has_recursion: bool
    max_depth: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "estimatedMemoryMb": self.estimated_memory_mb,
            "estimatedCpuSeconds": self.estimated_cpu_seconds,
            "complexityScore": self.complexity_score,
            "hasLoops": self.has_loops,
            "hasRecursion": self.has_recursion,
            "maxDepth": self.max_depth,
        }


@dataclass
class ValidationResult:
    """Complete validation result for code"""
    is_valid: bool
    language: str
    code_hash: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    security_issues: List[SecurityIssue] = field(default_factory=list)
    resource_estimate: Optional[ResourceEstimate] = None
    validation_timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "isValid": self.is_valid,
            "language": self.language,
            "codeHash": self.code_hash,
            "errors": self.errors,
            "warnings": self.warnings,
            "securityIssues": [issue.to_dict() for issue in self.security_issues],
        }
        if self.resource_estimate:
            result["resourceEstimate"] = self.resource_estimate.to_dict()
        if self.validation_timestamp:
            result["validationTimestamp"] = self.validation_timestamp
        return result
    
    def has_critical_issues(self) -> bool:
        """Check if there are any critical security issues"""
        return any(
            issue.severity == SeverityLevel.CRITICAL
            for issue in self.security_issues
        )
    
    def get_all_issues(self) -> List[str]:
        """Get all issues as a flat list of strings"""
        issues = []
        issues.extend(self.errors)
        issues.extend(self.warnings)
        issues.extend([
            f"[{issue.severity.value.upper()}] {issue.message}"
            for issue in self.security_issues
        ])
        return issues
