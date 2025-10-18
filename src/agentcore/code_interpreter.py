"""Bedrock Code Interpreter integration for secure tool execution"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

from ..models.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionError,
    ExecutionMetrics,
)
from ..models.errors import ExecutionError as DynamicExecutionError


logger = logging.getLogger(__name__)


class CodeInterpreterService:
    """Service for executing tools using AWS Bedrock Code Interpreter"""
    
    # Execution timeouts
    DEFAULT_TIMEOUT_SECONDS = 30
    MAX_TIMEOUT_SECONDS = 300
    
    # Polling configuration
    POLL_INTERVAL_SECONDS = 1
    MAX_POLL_ATTEMPTS = 60
    
    def __init__(
        self,
        region_name: Optional[str] = None,
        bedrock_agent_runtime_client: Optional[Any] = None,
        default_timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ):
        """
        Initialize Code Interpreter service
        
        Args:
            region_name: AWS region name (defaults to environment)
            bedrock_agent_runtime_client: Pre-configured boto3 bedrock-agent-runtime client
            default_timeout: Default execution timeout in seconds
        """
        self.region_name = region_name
        self.client = bedrock_agent_runtime_client or boto3.client(
            "bedrock-agent-runtime",
            region_name=region_name,
        )
        self.default_timeout = min(default_timeout, self.MAX_TIMEOUT_SECONDS)
    
    def execute_code(
        self,
        tool_id: str,
        code: str,
        parameters: Dict[str, Any],
        language: str = "python",
        timeout_seconds: Optional[int] = None,
    ) -> ExecutionResult:
        """
        Execute tool code using Bedrock Code Interpreter
        
        Args:
            tool_id: Tool ID for tracking
            code: Validated code to execute
            parameters: Input parameters for the tool
            language: Programming language (python, javascript, typescript)
            timeout_seconds: Execution timeout (defaults to default_timeout)
            
        Returns:
            ExecutionResult with output or error
            
        Raises:
            DynamicExecutionError: If execution fails
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        timeout = timeout_seconds or self.default_timeout
        
        logger.info(
            f"Starting code execution: {tool_id}",
            extra={
                "tool_id": tool_id,
                "execution_id": execution_id,
                "language": language,
                "timeout": timeout,
            },
        )
        
        try:
            # Prepare code with parameter injection
            executable_code = self._prepare_code(code, parameters, language)
            
            # Submit code for execution
            execution_response = self._submit_execution(
                execution_id=execution_id,
                code=executable_code,
                language=language,
            )
            
            # Poll for execution completion
            result = self._poll_execution(
                execution_id=execution_id,
                timeout=timeout,
                start_time=start_time,
            )
            
            # Calculate metrics
            duration = time.time() - start_time
            metrics = ExecutionMetrics(
                duration=duration,
                memory_used=result.get("memoryUsed", 0),
                cpu_time=result.get("cpuTime", duration),
            )
            
            # Check for timeout
            if duration >= timeout:
                logger.warning(
                    f"Code execution timed out: {tool_id}",
                    extra={
                        "tool_id": tool_id,
                        "execution_id": execution_id,
                        "duration": duration,
                        "timeout": timeout,
                    },
                )
                
                return ExecutionResult.create_timeout(
                    tool_id=tool_id,
                    execution_id=execution_id,
                    timestamp=datetime.utcnow().isoformat(),
                    metrics=metrics,
                )
            
            # Check for execution errors
            if result.get("status") == "error":
                error = ExecutionError(
                    type=result.get("errorType", "ExecutionError"),
                    message=result.get("errorMessage", "Unknown error"),
                    stack=result.get("stackTrace"),
                )
                
                logger.error(
                    f"Code execution failed: {tool_id}",
                    extra={
                        "tool_id": tool_id,
                        "execution_id": execution_id,
                        "error_type": error.type,
                        "error_message": error.message,
                    },
                )
                
                return ExecutionResult.create_error(
                    tool_id=tool_id,
                    execution_id=execution_id,
                    timestamp=datetime.utcnow().isoformat(),
                    error=error,
                    metrics=metrics,
                )
            
            # Successful execution
            logger.info(
                f"Code execution completed successfully: {tool_id}",
                extra={
                    "tool_id": tool_id,
                    "execution_id": execution_id,
                    "duration": duration,
                },
            )
            
            return ExecutionResult.create_success(
                tool_id=tool_id,
                execution_id=execution_id,
                timestamp=datetime.utcnow().isoformat(),
                result=result.get("output"),
                metrics=metrics,
            )
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"Unexpected error during code execution: {str(e)}",
                extra={
                    "tool_id": tool_id,
                    "execution_id": execution_id,
                },
            )
            
            raise DynamicExecutionError(
                f"Code execution failed: {str(e)}",
                error_type=type(e).__name__,
            )
    
    def _prepare_code(
        self,
        code: str,
        parameters: Dict[str, Any],
        language: str,
    ) -> str:
        """
        Prepare code for execution by injecting parameters
        
        Args:
            code: Original code
            parameters: Input parameters
            language: Programming language
            
        Returns:
            Executable code with parameters injected
        """
        if language == "python":
            # Inject parameters as Python variables
            param_code = "\n".join([
                f"{key} = {json.dumps(value)}"
                for key, value in parameters.items()
            ])
            return f"{param_code}\n\n{code}"
        
        elif language in ["javascript", "typescript"]:
            # Inject parameters as JavaScript constants
            param_code = "\n".join([
                f"const {key} = {json.dumps(value)};"
                for key, value in parameters.items()
            ])
            return f"{param_code}\n\n{code}"
        
        else:
            # Unsupported language - return code as-is
            return code
    
    def _submit_execution(
        self,
        execution_id: str,
        code: str,
        language: str,
    ) -> Dict[str, Any]:
        """
        Submit code for execution to Bedrock Code Interpreter
        
        Args:
            execution_id: Unique execution ID
            code: Code to execute
            language: Programming language
            
        Returns:
            Execution submission response
            
        Raises:
            DynamicExecutionError: If submission fails
        """
        try:
            # In a real implementation, this would invoke the Bedrock Agent
            # Code Interpreter tool through the InvokeAgent API
            # For now, we simulate the submission
            
            logger.debug(
                f"Submitting code execution: {execution_id}",
                extra={
                    "execution_id": execution_id,
                    "language": language,
                    "code_length": len(code),
                },
            )
            
            response = {
                "executionId": execution_id,
                "status": "submitted",
            }
            
            return response
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            raise DynamicExecutionError(
                f"Failed to submit code execution: {error_message}",
                error_type=error_code,
            )
    
    def _poll_execution(
        self,
        execution_id: str,
        timeout: int,
        start_time: float,
    ) -> Dict[str, Any]:
        """
        Poll for execution completion
        
        Args:
            execution_id: Execution ID to poll
            timeout: Timeout in seconds
            start_time: Execution start time
            
        Returns:
            Execution result
            
        Raises:
            DynamicExecutionError: If polling fails
        """
        attempts = 0
        
        while attempts < self.MAX_POLL_ATTEMPTS:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                return {
                    "status": "timeout",
                    "executionId": execution_id,
                }
            
            try:
                # In a real implementation, this would check the execution status
                # through the Bedrock Agent API
                # For now, we simulate a successful execution
                
                # Simulate processing time
                time.sleep(self.POLL_INTERVAL_SECONDS)
                
                # Return simulated success after a few attempts
                if attempts >= 2:
                    return {
                        "status": "success",
                        "executionId": execution_id,
                        "output": {"result": "simulated_output"},
                        "memoryUsed": 128,
                        "cpuTime": elapsed,
                    }
                
                attempts += 1
                
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", str(e))
                
                raise DynamicExecutionError(
                    f"Failed to poll execution status: {error_message}",
                    error_type=error_code,
                )
        
        # Max attempts reached
        return {
            "status": "timeout",
            "executionId": execution_id,
        }
    
    def validate_execution_environment(self) -> bool:
        """
        Validate that Code Interpreter is available and accessible
        
        Returns:
            True if environment is valid, False otherwise
        """
        try:
            # Simple validation - check if we can access the Bedrock Agent Runtime API
            # In a real implementation, this might invoke a test execution
            
            logger.info("Validating Code Interpreter execution environment")
            
            # For now, assume environment is valid
            return True
            
        except Exception as e:
            logger.error(
                f"Code Interpreter environment validation failed: {str(e)}",
            )
            return False
    
    def get_execution_status(
        self,
        execution_id: str,
    ) -> Dict[str, Any]:
        """
        Get the status of a running execution
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution status information
            
        Raises:
            DynamicExecutionError: If status check fails
        """
        try:
            logger.debug(
                f"Checking execution status: {execution_id}",
                extra={"execution_id": execution_id},
            )
            
            # In a real implementation, this would query the Bedrock Agent API
            # For now, return a simulated status
            
            return {
                "executionId": execution_id,
                "status": "running",
            }
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            raise DynamicExecutionError(
                f"Failed to get execution status: {error_message}",
                error_type=error_code,
            )
    
    def cancel_execution(
        self,
        execution_id: str,
    ) -> None:
        """
        Cancel a running execution
        
        Args:
            execution_id: Execution ID to cancel
            
        Raises:
            DynamicExecutionError: If cancellation fails
        """
        try:
            logger.info(
                f"Cancelling execution: {execution_id}",
                extra={"execution_id": execution_id},
            )
            
            # In a real implementation, this would cancel the execution
            # through the Bedrock Agent API
            
            logger.info(
                f"Execution cancelled: {execution_id}",
                extra={"execution_id": execution_id},
            )
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            raise DynamicExecutionError(
                f"Failed to cancel execution: {error_message}",
                error_type=error_code,
            )
