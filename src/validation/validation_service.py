"""Integrated validation service combining all validation components"""

from typing import Literal, Optional, Tuple, List
from datetime import datetime

from .validator import CodeValidator
from .policy_evaluator import PolicyEvaluator
from .validation_cache import ValidationCache
from .security_policy import SecurityPolicy, SecurityPolicyManager, PolicyViolation
from .validation_result import ValidationResult
from ..models.errors import ValidationError


class ValidationService:
    """
    High-level validation service that orchestrates:
    - Code analysis
    - Security policy evaluation
    - Result caching
    - Audit logging
    """
    
    def __init__(
        self,
        policy: Optional[SecurityPolicy] = None,
        enable_cache: bool = True,
    ):
        """
        Initialize validation service
        
        Args:
            policy: Security policy to enforce (uses default if None)
            enable_cache: Whether to enable validation result caching
        """
        self.validator = CodeValidator()
        self.policy = policy or SecurityPolicyManager.get_default_policy()
        self.policy_evaluator = PolicyEvaluator(self.policy)
        self.cache = ValidationCache() if enable_cache else None
        self.enable_cache = enable_cache
    
    def validate_code(
        self,
        code: str,
        language: Literal["python", "javascript", "typescript"],
        use_cache: bool = True,
        dependencies: Optional[List[str]] = None,
    ) -> Tuple[ValidationResult, List[PolicyViolation]]:
        """
        Perform complete validation with caching and policy evaluation
        
        Args:
            code: Source code to validate
            language: Programming language
            use_cache: Whether to use cached results
            dependencies: List of dependencies
            
        Returns:
            Tuple of (ValidationResult, List of PolicyViolations)
            
        Raises:
            ValidationError: If validation fails with critical issues
        """
        # Step 1: Check cache if enabled
        if self.enable_cache and use_cache and self.cache:
            cached_result = self.cache.get_cached_validation(code, language)
            if cached_result:
                # Evaluate cached result against current policy
                violations = self.policy_evaluator.evaluate(cached_result)
                
                # Update usage count
                try:
                    code_hash = self.cache.storage.compute_code_hash(code, language)
                    self.cache.storage.update_usage_count(code_hash)
                except Exception:
                    pass  # Don't fail if usage count update fails
                
                return cached_result, violations
        
        # Step 2: Perform validation
        validation_result = self.validator.validate_safe(code, language)
        
        # Step 3: Evaluate against security policy
        violations = self.policy_evaluator.evaluate(validation_result)
        
        # Step 4: Check for critical violations
        has_critical = self.policy_evaluator.has_critical_violations(violations)
        
        if has_critical or not validation_result.is_valid:
            # Update validation result to reflect policy violations
            validation_result.is_valid = False
            
            # Raise detailed error
            raise ValidationError(
                "Code validation failed due to security policy violations",
                errors=validation_result.errors,
                warnings=validation_result.warnings,
                security_issues=[v.message for v in violations if v.severity == "critical"],
            )
        
        # Step 5: Cache successful validation result
        if self.enable_cache and self.cache and validation_result.is_valid:
            try:
                self.cache.cache_validation_result(
                    code=code,
                    language=language,
                    validation_result=validation_result,
                    dependencies=dependencies,
                )
            except Exception as e:
                # Don't fail validation if caching fails
                print(f"Warning: Failed to cache validation result: {e}")
        
        return validation_result, violations
    
    def validate_code_safe(
        self,
        code: str,
        language: Literal["python", "javascript", "typescript"],
        use_cache: bool = True,
        dependencies: Optional[List[str]] = None,
    ) -> Tuple[ValidationResult, List[PolicyViolation]]:
        """
        Validate code without raising exceptions
        
        Args:
            code: Source code to validate
            language: Programming language
            use_cache: Whether to use cached results
            dependencies: List of dependencies
            
        Returns:
            Tuple of (ValidationResult, List of PolicyViolations)
        """
        try:
            return self.validate_code(code, language, use_cache, dependencies)
        except ValidationError:
            # Return the validation result even if it failed
            validation_result = self.validator.validate_safe(code, language)
            violations = self.policy_evaluator.evaluate(validation_result)
            return validation_result, violations
    
    def invalidate_cache_for_code(
        self,
        code: str,
        language: Literal["python", "javascript", "typescript"],
    ) -> None:
        """
        Invalidate cached validation result for specific code
        
        Args:
            code: Source code
            language: Programming language
        """
        if not self.enable_cache or not self.cache:
            return
        
        try:
            code_hash = self.cache.storage.compute_code_hash(code, language)
            self.cache.invalidate_cache(code_hash, language)
        except Exception as e:
            print(f"Warning: Failed to invalidate cache: {e}")
    
    def update_policy(self, new_policy: SecurityPolicy) -> None:
        """
        Update security policy and invalidate affected cache entries
        
        Args:
            new_policy: New security policy
        """
        old_policy_id = self.policy.policy_id
        self.policy = new_policy
        self.policy_evaluator = PolicyEvaluator(new_policy)
        
        # Store new policy for audit
        if self.enable_cache and self.cache:
            try:
                self.cache.store_policy(new_policy)
                
                # Invalidate all cached results (they were validated with old policy)
                invalidated = self.cache.invalidate_all_for_policy_update(old_policy_id)
                print(f"Policy updated. Invalidated {invalidated} cached results.")
            except Exception as e:
                print(f"Warning: Failed to update policy in cache: {e}")
    
    def get_validation_summary(
        self,
        validation_result: ValidationResult,
        violations: List[PolicyViolation],
    ) -> dict:
        """
        Get summary of validation results
        
        Args:
            validation_result: Validation result
            violations: Policy violations
            
        Returns:
            Summary dictionary
        """
        summary = {
            "isValid": validation_result.is_valid,
            "language": validation_result.language,
            "codeHash": validation_result.code_hash,
            "errorCount": len(validation_result.errors),
            "warningCount": len(validation_result.warnings),
            "securityIssueCount": len(validation_result.security_issues),
            "policyViolationCount": len(violations),
            "hasCriticalIssues": validation_result.has_critical_issues(),
            "violationSummary": self.policy_evaluator.get_violation_summary(violations),
        }
        
        if validation_result.resource_estimate:
            summary["resourceEstimate"] = validation_result.resource_estimate.to_dict()
        
        return summary
