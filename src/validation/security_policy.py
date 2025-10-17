"""Security policy definitions and validation"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Optional
from enum import Enum


class PolicyViolationType(str, Enum):
    """Types of security policy violations"""
    FILE_SYSTEM_ACCESS = "file_system_access"
    NETWORK_ACCESS = "network_access"
    SYSTEM_CALL = "system_call"
    DANGEROUS_FUNCTION = "dangerous_function"
    RESOURCE_LIMIT = "resource_limit"
    PROHIBITED_IMPORT = "prohibited_import"


@dataclass
class PolicyRule:
    """Individual security policy rule"""
    rule_id: str
    rule_type: PolicyViolationType
    description: str
    severity: str  # "low", "medium", "high", "critical"
    patterns: List[str] = field(default_factory=list)
    allowed_exceptions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "ruleId": self.rule_id,
            "ruleType": self.rule_type.value,
            "description": self.description,
            "severity": self.severity,
            "patterns": self.patterns,
            "allowedExceptions": self.allowed_exceptions,
        }


@dataclass
class ResourceLimits:
    """Resource usage limits for code execution"""
    max_memory_mb: int = 512
    max_cpu_seconds: float = 30.0
    max_complexity: int = 50
    max_nesting_depth: int = 10
    allow_loops: bool = True
    allow_recursion: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "maxMemoryMb": self.max_memory_mb,
            "maxCpuSeconds": self.max_cpu_seconds,
            "maxComplexity": self.max_complexity,
            "maxNestingDepth": self.max_nesting_depth,
            "allowLoops": self.allow_loops,
            "allowRecursion": self.allow_recursion,
        }


@dataclass
class SecurityPolicy:
    """Complete security policy for code validation"""
    policy_id: str
    policy_name: str
    version: str
    rules: List[PolicyRule] = field(default_factory=list)
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    prohibited_modules: Set[str] = field(default_factory=set)
    prohibited_functions: Set[str] = field(default_factory=set)
    allowed_file_operations: List[str] = field(default_factory=list)
    allowed_network_domains: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "policyId": self.policy_id,
            "policyName": self.policy_name,
            "version": self.version,
            "rules": [rule.to_dict() for rule in self.rules],
            "resourceLimits": self.resource_limits.to_dict(),
            "prohibitedModules": list(self.prohibited_modules),
            "prohibitedFunctions": list(self.prohibited_functions),
            "allowedFileOperations": self.allowed_file_operations,
            "allowedNetworkDomains": self.allowed_network_domains,
        }


@dataclass
class PolicyViolation:
    """Represents a security policy violation"""
    violation_type: PolicyViolationType
    rule_id: str
    severity: str
    message: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    remediation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "violationType": self.violation_type.value,
            "ruleId": self.rule_id,
            "severity": self.severity,
            "message": self.message,
        }
        if self.line_number is not None:
            result["lineNumber"] = self.line_number
        if self.code_snippet:
            result["codeSnippet"] = self.code_snippet
        if self.remediation:
            result["remediation"] = self.remediation
        return result


class SecurityPolicyManager:
    """Manages security policies and provides default policies"""
    
    @staticmethod
    def get_default_policy() -> SecurityPolicy:
        """Get the default security policy for dynamic tools"""
        # Python prohibited modules
        python_prohibited = {
            "os", "subprocess", "socket", "urllib", "urllib2", "urllib3",
            "requests", "http", "httplib", "ftplib", "telnetlib",
            "smtplib", "poplib", "imaplib", "__import__", "importlib",
            "sys", "ctypes", "multiprocessing", "threading", "asyncio",
        }
        
        # JavaScript prohibited modules
        js_prohibited = {
            "fs", "child_process", "net", "http", "https", "dgram",
            "dns", "tls", "crypto", "os", "process", "cluster",
            "worker_threads", "vm",
        }
        
        # Prohibited functions across languages
        prohibited_functions = {
            "eval", "exec", "compile", "__import__", "open", "input",
            "Function", "require", "import", "XMLHttpRequest", "fetch",
            "WebSocket",
        }
        
        rules = [
            PolicyRule(
                rule_id="FS001",
                rule_type=PolicyViolationType.FILE_SYSTEM_ACCESS,
                description="Prohibit file system access outside temp directories",
                severity="critical",
                patterns=["open(", "file(", "fs.", "readFile", "writeFile"],
            ),
            PolicyRule(
                rule_id="NET001",
                rule_type=PolicyViolationType.NETWORK_ACCESS,
                description="Prohibit all network access",
                severity="critical",
                patterns=["socket", "http", "https", "fetch", "XMLHttpRequest"],
            ),
            PolicyRule(
                rule_id="SYS001",
                rule_type=PolicyViolationType.SYSTEM_CALL,
                description="Prohibit system calls and process spawning",
                severity="critical",
                patterns=["subprocess", "child_process", "exec", "spawn"],
            ),
            PolicyRule(
                rule_id="FUNC001",
                rule_type=PolicyViolationType.DANGEROUS_FUNCTION,
                description="Prohibit dangerous dynamic code execution",
                severity="critical",
                patterns=["eval(", "exec(", "Function(", "compile("],
            ),
            PolicyRule(
                rule_id="RES001",
                rule_type=PolicyViolationType.RESOURCE_LIMIT,
                description="Enforce resource usage limits",
                severity="high",
                patterns=[],
            ),
        ]
        
        return SecurityPolicy(
            policy_id="default-v1",
            policy_name="Default Dynamic Tool Security Policy",
            version="1.0.0",
            rules=rules,
            resource_limits=ResourceLimits(
                max_memory_mb=512,
                max_cpu_seconds=30.0,
                max_complexity=50,
                max_nesting_depth=10,
                allow_loops=True,
                allow_recursion=False,
            ),
            prohibited_modules=python_prohibited | js_prohibited,
            prohibited_functions=prohibited_functions,
            allowed_file_operations=[],  # No file operations allowed
            allowed_network_domains=[],  # No network access allowed
        )
    
    @staticmethod
    def get_permissive_policy() -> SecurityPolicy:
        """Get a more permissive policy for testing/development"""
        policy = SecurityPolicyManager.get_default_policy()
        policy.policy_id = "permissive-v1"
        policy.policy_name = "Permissive Security Policy"
        policy.resource_limits.allow_recursion = True
        policy.resource_limits.max_complexity = 100
        return policy
