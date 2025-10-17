"""
Example demonstrating the code validation system

This script shows how to use the validation system to validate
Python and JavaScript code with security policies.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation import (
    ValidationService,
    SecurityPolicyManager,
    CodeValidator,
    PythonAnalyzer,
)
from src.models.errors import ValidationError


def example_1_basic_validation():
    """Example 1: Basic code validation"""
    print("=" * 60)
    print("Example 1: Basic Code Validation")
    print("=" * 60)
    
    # Safe Python code
    safe_code = """
def add_numbers(a, b):
    '''Add two numbers together'''
    return a + b

def multiply(x, y):
    '''Multiply two numbers'''
    result = x * y
    return result
"""
    
    # Initialize validation service (without cache for demo)
    service = ValidationService(enable_cache=False)
    
    try:
        result, violations = service.validate_code(safe_code, "python")
        print(f"✓ Validation passed!")
        print(f"  - Code hash: {result.code_hash[:16]}...")
        print(f"  - Errors: {len(result.errors)}")
        print(f"  - Warnings: {len(result.warnings)}")
        print(f"  - Security issues: {len(result.security_issues)}")
        print(f"  - Policy violations: {len(violations)}")
        
        if result.resource_estimate:
            est = result.resource_estimate
            print(f"  - Estimated memory: {est.estimated_memory_mb}MB")
            print(f"  - Estimated CPU: {est.estimated_cpu_seconds}s")
            print(f"  - Complexity: {est.complexity_score}")
    
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}")


def example_2_unsafe_code():
    """Example 2: Detecting unsafe code"""
    print("\n" + "=" * 60)
    print("Example 2: Detecting Unsafe Code")
    print("=" * 60)
    
    # Unsafe code with prohibited imports
    unsafe_code = """
import os
import subprocess

def dangerous_function():
    # This should be blocked!
    os.system('ls -la')
    subprocess.run(['echo', 'hello'])
    return eval('1 + 1')
"""
    
    service = ValidationService(enable_cache=False)
    
    try:
        result, violations = service.validate_code(unsafe_code, "python")
        print(f"✗ Validation should have failed but passed!")
    
    except ValidationError as e:
        print(f"✓ Validation correctly failed!")
        print(f"  - Message: {e.message}")
        print(f"  - Errors: {len(e.errors)}")
        print(f"  - Security issues: {len(e.security_issues)}")
        
        if e.security_issues:
            print(f"\n  Security Issues:")
            for issue in e.security_issues[:3]:  # Show first 3
                print(f"    - {issue}")


def example_3_resource_limits():
    """Example 3: Resource limit violations"""
    print("\n" + "=" * 60)
    print("Example 3: Resource Limit Violations")
    print("=" * 60)
    
    # Code with recursion (not allowed by default policy)
    recursive_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
"""
    
    service = ValidationService(enable_cache=False)
    
    result, violations = service.validate_code_safe(recursive_code, "python")
    
    print(f"Validation result: {'✓ Passed' if result.is_valid else '✗ Failed'}")
    print(f"Policy violations: {len(violations)}")
    
    if violations:
        print(f"\nViolations:")
        for v in violations:
            print(f"  - [{v.severity.upper()}] {v.message}")
            if v.remediation:
                print(f"    Remediation: {v.remediation}")


def example_4_javascript_validation():
    """Example 4: JavaScript validation"""
    print("\n" + "=" * 60)
    print("Example 4: JavaScript Validation")
    print("=" * 60)
    
    # Safe JavaScript code
    safe_js = """
function calculateTotal(items) {
    let total = 0;
    for (let item of items) {
        total += item.price * item.quantity;
    }
    return total;
}

const formatCurrency = (amount) => {
    return `$${amount.toFixed(2)}`;
};
"""
    
    service = ValidationService(enable_cache=False)
    
    try:
        result, violations = service.validate_code(safe_js, "javascript")
        print(f"✓ JavaScript validation passed!")
        print(f"  - Code hash: {result.code_hash[:16]}...")
        
        if result.resource_estimate:
            est = result.resource_estimate
            print(f"  - Has loops: {est.has_loops}")
            print(f"  - Complexity: {est.complexity_score}")
    
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}")


def example_5_direct_analyzer():
    """Example 5: Using analyzer directly"""
    print("\n" + "=" * 60)
    print("Example 5: Direct Analyzer Usage")
    print("=" * 60)
    
    code = """
def process_data(data):
    results = []
    for item in data:
        if item > 0:
            results.append(item * 2)
    return results
"""
    
    analyzer = PythonAnalyzer()
    result = analyzer.analyze(code)
    
    print(f"Analysis complete:")
    print(f"  - Valid: {result.is_valid}")
    print(f"  - Code hash: {result.code_hash[:16]}...")
    print(f"  - Errors: {len(result.errors)}")
    print(f"  - Warnings: {len(result.warnings)}")
    print(f"  - Security issues: {len(result.security_issues)}")
    
    if result.resource_estimate:
        est = result.resource_estimate
        print(f"\nResource Estimate:")
        print(f"  - Memory: {est.estimated_memory_mb}MB")
        print(f"  - CPU: {est.estimated_cpu_seconds}s")
        print(f"  - Complexity: {est.complexity_score}")
        print(f"  - Has loops: {est.has_loops}")
        print(f"  - Has recursion: {est.has_recursion}")
        print(f"  - Max depth: {est.max_depth}")


def example_6_policy_comparison():
    """Example 6: Comparing different policies"""
    print("\n" + "=" * 60)
    print("Example 6: Policy Comparison")
    print("=" * 60)
    
    # Code with recursion
    code = """
def countdown(n):
    if n <= 0:
        return
    print(n)
    countdown(n - 1)
"""
    
    # Test with default policy (strict)
    print("\nWith Default Policy (strict):")
    service_strict = ValidationService(
        policy=SecurityPolicyManager.get_default_policy(),
        enable_cache=False,
    )
    result1, violations1 = service_strict.validate_code_safe(code, "python")
    print(f"  - Valid: {result1.is_valid}")
    print(f"  - Violations: {len(violations1)}")
    
    # Test with permissive policy
    print("\nWith Permissive Policy:")
    service_permissive = ValidationService(
        policy=SecurityPolicyManager.get_permissive_policy(),
        enable_cache=False,
    )
    result2, violations2 = service_permissive.validate_code_safe(code, "python")
    print(f"  - Valid: {result2.is_valid}")
    print(f"  - Violations: {len(violations2)}")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Code Validation System Examples" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        example_1_basic_validation()
        example_2_unsafe_code()
        example_3_resource_limits()
        example_4_javascript_validation()
        example_5_direct_analyzer()
        example_6_policy_comparison()
        
        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60 + "\n")
    
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
