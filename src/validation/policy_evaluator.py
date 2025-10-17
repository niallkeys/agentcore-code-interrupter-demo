"""Security policy evaluation engine"""

from typing import List
from .security_policy import (
    SecurityPolicy,
    PolicyViolation,
    PolicyViolationType,
    SecurityPolicyManager,
)
from .validation_result import ValidationResult, ResourceEstimate


class PolicyEvaluator:
    """
    Evaluates validation results against security policies
    """
    
    def __init__(self, policy: SecurityPolicy = None):
        """
        Initialize policy evaluator
        
        Args:
            policy: Security policy to enforce (uses default if None)
        """
        self.policy = policy or SecurityPolicyManager.get_default_policy()
    
    def evaluate(self, validation_result: ValidationResult) -> List[PolicyViolation]:
        """
        Evaluate validation result against security policy
        
        Args:
            validation_result: Result from code analysis
            
        Returns:
            List of policy violations found
        """
        violations: List[PolicyViolation] = []
        
        # Check resource limits
        if validation_result.resource_estimate:
            violations.extend(
                self._check_resource_limits(validation_result.resource_estimate)
            )
        
        # Convert security issues to policy violations
        for issue in validation_result.security_issues:
            violation_type = self._map_issue_to_violation_type(issue.issue_type)
            
            violations.append(
                PolicyViolation(
                    violation_type=violation_type,
                    rule_id=self._get_rule_id_for_type(violation_type),
                    severity=issue.severity.value,
                    message=issue.message,
                    line_number=issue.line_number,
                    code_snippet=issue.code_snippet,
                    remediation=self._get_remediation(violation_type),
                )
            )
        
        return violations
    
    def _check_resource_limits(
        self,
        resource_estimate: ResourceEstimate,
    ) -> List[PolicyViolation]:
        """Check if resource estimates exceed policy limits"""
        violations: List[PolicyViolation] = []
        limits = self.policy.resource_limits
        
        # Check memory limit
        if resource_estimate.estimated_memory_mb > limits.max_memory_mb:
            violations.append(
                PolicyViolation(
                    violation_type=PolicyViolationType.RESOURCE_LIMIT,
                    rule_id="RES001",
                    severity="high",
                    message=(
                        f"Estimated memory usage ({resource_estimate.estimated_memory_mb}MB) "
                        f"exceeds limit ({limits.max_memory_mb}MB)"
                    ),
                    remediation="Reduce code complexity or data structures",
                )
            )
        
        # Check CPU time limit
        if resource_estimate.estimated_cpu_seconds > limits.max_cpu_seconds:
            violations.append(
                PolicyViolation(
                    violation_type=PolicyViolationType.RESOURCE_LIMIT,
                    rule_id="RES001",
                    severity="high",
                    message=(
                        f"Estimated CPU time ({resource_estimate.estimated_cpu_seconds}s) "
                        f"exceeds limit ({limits.max_cpu_seconds}s)"
                    ),
                    remediation="Optimize algorithms or reduce iterations",
                )
            )
        
        # Check complexity limit
        if resource_estimate.complexity_score > limits.max_complexity:
            violations.append(
                PolicyViolation(
                    violation_type=PolicyViolationType.RESOURCE_LIMIT,
                    rule_id="RES001",
                    severity="medium",
                    message=(
                        f"Code complexity ({resource_estimate.complexity_score}) "
                        f"exceeds limit ({limits.max_complexity})"
                    ),
                    remediation="Simplify code structure and reduce nesting",
                )
            )
        
        # Check nesting depth limit
        if resource_estimate.max_depth > limits.max_nesting_depth:
            violations.append(
                PolicyViolation(
                    violation_type=PolicyViolationType.RESOURCE_LIMIT,
                    rule_id="RES001",
                    severity="medium",
                    message=(
                        f"Nesting depth ({resource_estimate.max_depth}) "
                        f"exceeds limit ({limits.max_nesting_depth})"
                    ),
                    remediation="Reduce nesting by extracting functions",
                )
            )
        
        # Check recursion policy
        if resource_estimate.has_recursion and not limits.allow_recursion:
            violations.append(
                PolicyViolation(
                    violation_type=PolicyViolationType.RESOURCE_LIMIT,
                    rule_id="RES001",
                    severity="high",
                    message="Recursion is not allowed by security policy",
                    remediation="Convert recursive logic to iterative approach",
                )
            )
        
        return violations
    
    def _map_issue_to_violation_type(self, issue_type: str) -> PolicyViolationType:
        """Map security issue type to policy violation type"""
        mapping = {
            "prohibited_import": PolicyViolationType.PROHIBITED_IMPORT,
            "prohibited_builtin": PolicyViolationType.DANGEROUS_FUNCTION,
            "dangerous_pattern": PolicyViolationType.DANGEROUS_FUNCTION,
            "prohibited_global": PolicyViolationType.DANGEROUS_FUNCTION,
        }
        return mapping.get(issue_type, PolicyViolationType.DANGEROUS_FUNCTION)
    
    def _get_rule_id_for_type(self, violation_type: PolicyViolationType) -> str:
        """Get rule ID for a violation type"""
        rule_map = {
            PolicyViolationType.FILE_SYSTEM_ACCESS: "FS001",
            PolicyViolationType.NETWORK_ACCESS: "NET001",
            PolicyViolationType.SYSTEM_CALL: "SYS001",
            PolicyViolationType.DANGEROUS_FUNCTION: "FUNC001",
            PolicyViolationType.RESOURCE_LIMIT: "RES001",
            PolicyViolationType.PROHIBITED_IMPORT: "IMP001",
        }
        return rule_map.get(violation_type, "UNKNOWN")
    
    def _get_remediation(self, violation_type: PolicyViolationType) -> str:
        """Get remediation advice for a violation type"""
        remediation_map = {
            PolicyViolationType.FILE_SYSTEM_ACCESS: (
                "Remove file system operations or use approved temporary storage APIs"
            ),
            PolicyViolationType.NETWORK_ACCESS: (
                "Remove network calls or use approved API endpoints"
            ),
            PolicyViolationType.SYSTEM_CALL: (
                "Remove system calls and process spawning operations"
            ),
            PolicyViolationType.DANGEROUS_FUNCTION: (
                "Replace dynamic code execution with safe alternatives"
            ),
            PolicyViolationType.RESOURCE_LIMIT: (
                "Optimize code to reduce resource usage"
            ),
            PolicyViolationType.PROHIBITED_IMPORT: (
                "Remove prohibited module imports and use approved alternatives"
            ),
        }
        return remediation_map.get(
            violation_type,
            "Review code against security policy requirements",
        )
    
    def has_critical_violations(self, violations: List[PolicyViolation]) -> bool:
        """Check if there are any critical violations"""
        return any(v.severity == "critical" for v in violations)
    
    def get_violation_summary(self, violations: List[PolicyViolation]) -> dict:
        """Get summary statistics of violations"""
        summary = {
            "total": len(violations),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "by_type": {},
        }
        
        for violation in violations:
            # Count by severity
            if violation.severity in summary:
                summary[violation.severity] += 1
            
            # Count by type
            vtype = violation.violation_type.value
            summary["by_type"][vtype] = summary["by_type"].get(vtype, 0) + 1
        
        return summary
