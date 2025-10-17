# Code Validation System

This module provides comprehensive code validation for the Dynamic Tool Runtime system.

## Components

### 1. Static Code Analysis Engine (`validator.py`, `python_analyzer.py`, `javascript_analyzer.py`)

Performs AST-based analysis and security scanning:

- **Python Analysis**: Uses built-in `ast` module and `bandit` for security scanning
- **JavaScript/TypeScript Analysis**: Regex-based pattern matching for security issues
- **Syntax Validation**: Checks for syntax errors and structural issues
- **Security Scanning**: Detects prohibited imports, dangerous functions, and security vulnerabilities

### 2. Security Policy Validation (`security_policy.py`, `policy_evaluator.py`)

Enforces security policies and resource limits:

- **Policy Rules**: Configurable rules for file system, network, and system call restrictions
- **Resource Limits**: Memory, CPU, complexity, and nesting depth constraints
- **Violation Reporting**: Detailed violation messages with remediation advice
- **Policy Management**: Default and permissive policy templates

### 3. Validation Result Caching (`validation_cache.py`)

Caches validation results in S3 for performance:

- **Content-Based Addressing**: Uses SHA-256 hash for deduplication
- **Cache Invalidation**: Supports policy-based cache invalidation
- **Audit Logging**: Tracks all validation events for compliance
- **Usage Tracking**: Monitors tool reuse across agents

### 4. Integrated Validation Service (`validation_service.py`)

High-level orchestration of all validation components:

- **Unified Interface**: Single entry point for code validation
- **Automatic Caching**: Transparent cache management
- **Policy Enforcement**: Automatic policy evaluation
- **Error Handling**: Comprehensive error reporting

## Usage Examples

### Basic Validation

```python
from src.validation import ValidationService

# Initialize service with default policy
service = ValidationService()

# Validate Python code
code = """
def add(a, b):
    return a + b
"""

try:
    result, violations = service.validate_code(code, "python")
    print(f"Validation passed: {result.is_valid}")
    print(f"Violations: {len(violations)}")
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Errors: {e.errors}")
```

### With Custom Policy

```python
from src.validation import ValidationService, SecurityPolicyManager

# Use permissive policy
policy = SecurityPolicyManager.get_permissive_policy()
service = ValidationService(policy=policy)

result, violations = service.validate_code(code, "python")
```

### Without Caching

```python
# Disable caching for testing
service = ValidationService(enable_cache=False)

result, violations = service.validate_code(code, "python", use_cache=False)
```

### Direct Analyzer Usage

```python
from src.validation import PythonAnalyzer

analyzer = PythonAnalyzer()
result = analyzer.analyze(code)

print(f"Valid: {result.is_valid}")
print(f"Errors: {result.errors}")
print(f"Security Issues: {len(result.security_issues)}")
print(f"Complexity: {result.resource_estimate.complexity_score}")
```

## Security Policies

### Default Policy

The default policy enforces strict security:

- **No file system access** (except temp directories)
- **No network access** (all protocols blocked)
- **No system calls** (subprocess, exec, etc.)
- **No dynamic code execution** (eval, exec, Function)
- **Resource limits**: 512MB memory, 30s CPU, complexity < 50
- **No recursion allowed**

### Prohibited Operations

#### Python
- Modules: `os`, `subprocess`, `socket`, `urllib`, `requests`, `sys`, `ctypes`, etc.
- Functions: `eval`, `exec`, `compile`, `__import__`, `open`, `input`

#### JavaScript/TypeScript
- Modules: `fs`, `child_process`, `net`, `http`, `https`, `os`, `process`, etc.
- Functions: `eval`, `Function`, `require`, `XMLHttpRequest`, `fetch`, `WebSocket`

## Validation Result Structure

```python
@dataclass
class ValidationResult:
    is_valid: bool
    language: str
    code_hash: str
    errors: List[str]
    warnings: List[str]
    security_issues: List[SecurityIssue]
    resource_estimate: Optional[ResourceEstimate]
    validation_timestamp: Optional[str]
```

## Resource Estimation

The system estimates resource usage:

- **Memory**: Base 64MB + complexity factor (capped at 512MB)
- **CPU Time**: Base 0.1s + complexity factor (capped at 30s)
- **Complexity Score**: Based on loops, recursion, nesting
- **Penalties**: +0.5s for loops, +1.0s for recursion

## Caching Strategy

### Cache Keys

- **Artifacts**: `artifacts/{code_hash}.json`
- **Code**: `code/{code_hash}.{ext}`
- **Audit Logs**: `audit-logs/{date}/{code_hash}-{timestamp}.json`
- **Policies**: `policies/{policy_id}-{version}.json`

### Cache Benefits

- **First-time validation**: ~2-5 seconds
- **Cached validation**: ~1-2 seconds (60% faster)
- **Cross-agent reuse**: Shared validated tools
- **Automatic deduplication**: Content-based addressing

## Performance Targets

- **Syntax validation**: < 100ms
- **Security scanning**: < 200ms (Python with bandit)
- **Resource estimation**: < 100ms
- **Total validation**: < 500ms
- **Cache retrieval**: < 50ms

## Error Handling

The system provides detailed error information:

- **Syntax errors**: Line number and error message
- **Security issues**: Severity, type, line number, code snippet
- **Policy violations**: Rule ID, severity, remediation advice
- **Resource violations**: Limit exceeded, actual value, remediation

## Audit Logging

All validation events are logged:

- **Validation attempts**: Success/failure, code hash, timestamp
- **Policy updates**: Policy ID, version, timestamp
- **Cache operations**: Invalidations, usage counts
- **Security violations**: Critical issues, patterns detected

## Integration Points

### With Tool Manager

```python
from src.validation import ValidationService
from src.models.tool_definition import ToolDefinition

service = ValidationService()

def validate_tool(tool_def: ToolDefinition):
    result, violations = service.validate_code(
        code=tool_def.code,
        language=tool_def.language,
    )
    return result.is_valid
```

### With Artifact Storage

```python
from src.validation import ValidationCache
from src.storage import ArtifactStorage

storage = ArtifactStorage()
cache = ValidationCache(storage)

# Cache validation result
code_hash = cache.cache_validation_result(
    code=code,
    language="python",
    validation_result=result,
    dependencies=["numpy", "pandas"],
)
```

## Testing

The validation system can be tested with sample code:

```python
# Safe code - should pass
safe_code = """
def calculate(x, y):
    return x + y
"""

# Unsafe code - should fail
unsafe_code = """
import os
os.system('rm -rf /')
"""

# Test validation
service = ValidationService()

# This should pass
result1, _ = service.validate_code_safe(safe_code, "python")
assert result1.is_valid

# This should fail
result2, violations = service.validate_code_safe(unsafe_code, "python")
assert not result2.is_valid
assert len(violations) > 0
```

## Requirements

- Python 3.8+
- boto3 (AWS SDK)
- bandit (Python security scanner)
- radon (Python complexity analyzer)

## Future Enhancements

- Support for more languages (Go, Rust, etc.)
- Machine learning-based anomaly detection
- Real-time security threat intelligence integration
- Advanced static analysis with data flow tracking
- Integration with external security scanning services
