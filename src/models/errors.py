"""Error definitions for Dynamic Tool Runtime"""

from typing import Any, Dict, List, Optional


class DynamicToolError(Exception):
    """Base exception for Dynamic Tool Runtime"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(DynamicToolError):
    """Error during code validation"""
    
    def __init__(
        self,
        message: str,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        security_issues: Optional[List[str]] = None,
    ):
        details = {}
        if errors:
            details["errors"] = errors
        if warnings:
            details["warnings"] = warnings
        if security_issues:
            details["securityIssues"] = security_issues
        
        super().__init__(message, details)
        self.errors = errors or []
        self.warnings = warnings or []
        self.security_issues = security_issues or []


class ExecutionError(DynamicToolError):
    """Error during tool execution"""
    
    def __init__(
        self,
        message: str,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ):
        details = {}
        if error_type:
            details["errorType"] = error_type
        if stack_trace:
            details["stackTrace"] = stack_trace
        
        super().__init__(message, details)
        self.error_type = error_type
        self.stack_trace = stack_trace


class RegistrationError(DynamicToolError):
    """Error during tool registration with AgentCore"""
    
    def __init__(
        self,
        message: str,
        tool_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        details = {}
        if tool_id:
            details["toolId"] = tool_id
        if agent_id:
            details["agentId"] = agent_id
        
        super().__init__(message, details)
        self.tool_id = tool_id
        self.agent_id = agent_id


class StorageError(DynamicToolError):
    """Error during storage operations (DynamoDB or S3)"""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        resource: Optional[str] = None,
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if resource:
            details["resource"] = resource
        
        super().__init__(message, details)
        self.operation = operation
        self.resource = resource


class AuthorizationError(DynamicToolError):
    """Error during authorization checks"""
    
    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        required_permission: Optional[str] = None,
    ):
        details = {}
        if agent_id:
            details["agentId"] = agent_id
        if required_permission:
            details["requiredPermission"] = required_permission
        
        super().__init__(message, details)
        self.agent_id = agent_id
        self.required_permission = required_permission


class ResourceLimitError(DynamicToolError):
    """Error when resource limits are exceeded"""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        limit: Optional[Any] = None,
        actual: Optional[Any] = None,
    ):
        details = {}
        if resource_type:
            details["resourceType"] = resource_type
        if limit is not None:
            details["limit"] = limit
        if actual is not None:
            details["actual"] = actual
        
        super().__init__(message, details)
        self.resource_type = resource_type
        self.limit = limit
        self.actual = actual
