"""Execution result data models"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ExecutionStatus(str, Enum):
    """Execution status"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ExecutionError:
    """Error information from execution"""
    type: str
    message: str
    stack: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "type": self.type,
            "message": self.message,
        }
        if self.stack:
            result["stack"] = self.stack
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionError":
        """Create from dictionary"""
        return cls(
            type=data["type"],
            message=data["message"],
            stack=data.get("stack"),
        )


@dataclass
class ExecutionMetrics:
    """Metrics from tool execution"""
    duration: float
    memory_used: int
    cpu_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "duration": self.duration,
            "memoryUsed": self.memory_used,
            "cpuTime": self.cpu_time,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionMetrics":
        """Create from dictionary"""
        return cls(
            duration=data["duration"],
            memory_used=data["memoryUsed"],
            cpu_time=data["cpuTime"],
        )


@dataclass
class ExecutionResult:
    """Result of tool execution"""
    tool_id: str
    execution_id: str
    status: ExecutionStatus
    timestamp: str
    result: Optional[Any] = None
    error: Optional[ExecutionError] = None
    metrics: Optional[ExecutionMetrics] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result_dict = {
            "toolId": self.tool_id,
            "executionId": self.execution_id,
            "status": self.status.value,
            "timestamp": self.timestamp,
        }
        
        if self.result is not None:
            result_dict["result"] = self.result
        
        if self.error:
            result_dict["error"] = self.error.to_dict()
        
        if self.metrics:
            result_dict["metrics"] = self.metrics.to_dict()
        
        return result_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionResult":
        """Create from dictionary"""
        status = ExecutionStatus(data["status"])
        
        error = None
        if "error" in data:
            error = ExecutionError.from_dict(data["error"])
        
        metrics = None
        if "metrics" in data:
            metrics = ExecutionMetrics.from_dict(data["metrics"])
        
        return cls(
            tool_id=data["toolId"],
            execution_id=data["executionId"],
            status=status,
            timestamp=data["timestamp"],
            result=data.get("result"),
            error=error,
            metrics=metrics,
        )
    
    @classmethod
    def create_success(
        cls,
        tool_id: str,
        execution_id: str,
        timestamp: str,
        result: Any,
        metrics: ExecutionMetrics,
    ) -> "ExecutionResult":
        """Create a successful execution result"""
        return cls(
            tool_id=tool_id,
            execution_id=execution_id,
            status=ExecutionStatus.SUCCESS,
            timestamp=timestamp,
            result=result,
            metrics=metrics,
        )
    
    @classmethod
    def create_error(
        cls,
        tool_id: str,
        execution_id: str,
        timestamp: str,
        error: ExecutionError,
        metrics: Optional[ExecutionMetrics] = None,
    ) -> "ExecutionResult":
        """Create an error execution result"""
        return cls(
            tool_id=tool_id,
            execution_id=execution_id,
            status=ExecutionStatus.ERROR,
            timestamp=timestamp,
            error=error,
            metrics=metrics,
        )
    
    @classmethod
    def create_timeout(
        cls,
        tool_id: str,
        execution_id: str,
        timestamp: str,
        metrics: Optional[ExecutionMetrics] = None,
    ) -> "ExecutionResult":
        """Create a timeout execution result"""
        return cls(
            tool_id=tool_id,
            execution_id=execution_id,
            status=ExecutionStatus.TIMEOUT,
            timestamp=timestamp,
            error=ExecutionError(
                type="TimeoutError",
                message="Tool execution exceeded timeout limit",
            ),
            metrics=metrics,
        )
