# AgentCore Integration Layer

This module provides integration with AWS AgentCore Gateway and Bedrock Code Interpreter for dynamic tool registration and execution.

## Components

### AgentCoreClient

Client for interacting with AWS AgentCore Gateway API to register, discover, and manage tools.

**Key Features:**
- Tool registration with AgentCore Gateway
- Tool deregistration and cleanup
- Tool discovery and metadata synchronization
- OpenAPI schema conversion for AgentCore compatibility
- Error handling for AgentCore API communication failures

**Usage:**
```python
from src.agentcore import AgentCoreClient
from src.models.tool_record import ToolRecord

# Initialize client
client = AgentCoreClient(region_name="us-east-1")

# Register a tool
registration_data = client.register_tool(tool_record)

# Discover tools
tools = client.discover_tools(agent_id="agent-123")

# Deregister a tool
client.deregister_tool(tool_id="tool-456", agent_id="agent-123")

# Sync metadata
client.sync_tool_metadata(tool_id="tool-456", metadata={...})

# Health check
is_healthy = client.health_check()
```

### CodeInterpreterService

Service for executing tool code using AWS Bedrock Code Interpreter in a secure sandbox environment.

**Key Features:**
- Secure code execution with resource limits
- Parameter injection for tool inputs
- Execution monitoring and timeout handling
- Support for Python, JavaScript, and TypeScript
- Detailed execution metrics and error reporting

**Usage:**
```python
from src.agentcore import CodeInterpreterService

# Initialize service
interpreter = CodeInterpreterService(
    region_name="us-east-1",
    default_timeout=30
)

# Execute code
result = interpreter.execute_code(
    tool_id="tool-123",
    code="def add(a, b): return a + b\nresult = add(x, y)",
    parameters={"x": 5, "y": 3},
    language="python",
    timeout_seconds=30
)

# Check execution status
status = interpreter.get_execution_status(execution_id="exec-789")

# Cancel execution
interpreter.cancel_execution(execution_id="exec-789")

# Validate environment
is_valid = interpreter.validate_execution_environment()
```

### ToolLifecycleManager

Orchestrates the complete lifecycle of dynamic tools including registration, updates, and deregistration.

**Key Features:**
- Complete tool registration workflow with validation and caching
- Tool update and versioning logic
- Tool deregistration with cleanup
- Automatic rollback on registration failures
- Cache-based tool reuse across agents

**Usage:**
```python
from src.agentcore import ToolLifecycleManager
from src.models.tool_definition import ToolDefinition

# Initialize manager
manager = ToolLifecycleManager()

# Register a new tool
tool_definition = ToolDefinition(
    name="my_tool",
    description="A custom tool",
    version="1.0.0",
    language="python",
    code="def process(data): return data.upper()",
    schema=tool_schema
)

tool_record = manager.register_tool(
    tool_definition=tool_definition,
    agent_id="agent-123",
    skip_cache=False
)

# Update an existing tool
updated_record = manager.update_tool(
    tool_id="tool-456",
    tool_definition=updated_definition,
    agent_id="agent-123"
)

# Deregister a tool
manager.deregister_tool(
    tool_id="tool-456",
    agent_id="agent-123",
    delete_artifact=False
)

# Get tool status
status = manager.get_tool_status(tool_id="tool-456")
```

## Tool Registration Workflow

The tool registration workflow implements the following steps:

1. **Validate Structure**: Check tool definition for required fields and valid format
2. **Cache Lookup**: Compute code hash and check if artifact already exists
3. **Validation** (cache miss): Validate code for security and compliance
4. **Artifact Creation**: Bundle validated code with metadata and store in S3
5. **Store Metadata**: Create tool record in DynamoDB
6. **AgentCore Registration**: Register tool with AgentCore Gateway
7. **Rollback**: If any step fails, rollback previous changes

## Tool Update Workflow

The tool update workflow implements versioning:

1. **Retrieve Existing**: Get current tool record from DynamoDB
2. **Validate Ownership**: Ensure agent owns the tool
3. **Validate Definition**: Check new definition structure
4. **Code Change Detection**: Compare code hashes
5. **Artifact Creation** (if changed): Validate and create new artifact
6. **Update Record**: Update tool record with new version
7. **Sync Metadata**: Synchronize changes with AgentCore

## Tool Deregistration Workflow

The tool deregistration workflow handles cleanup:

1. **Retrieve Tool**: Get tool record from DynamoDB
2. **Validate Ownership**: Ensure agent owns the tool
3. **AgentCore Deregistration**: Remove from AgentCore Gateway
4. **Update Status**: Mark as inactive or delete record
5. **Artifact Cleanup** (optional): Delete artifact if not shared

## Caching Strategy

The system implements content-based caching to optimize performance:

- **Code Hash**: SHA-256 hash of normalized code + language
- **Cache Lookup**: Check S3 for existing artifact before validation
- **Cache Hit**: Reuse validated artifact, skip validation (~500ms saved)
- **Cache Miss**: Validate code and create new artifact
- **Usage Tracking**: Increment usage count for cache analytics
- **Cross-Agent Sharing**: Multiple agents can reuse identical tools

## Error Handling

All components implement comprehensive error handling:

- **RegistrationError**: Tool registration/deregistration failures
- **ValidationError**: Code validation failures
- **ExecutionError**: Code execution failures
- **StorageError**: DynamoDB/S3 operation failures
- **Automatic Rollback**: Registration failures trigger cleanup

## Integration with Other Components

### Validation Service
- Used during tool registration to validate code
- Provides security scanning and compliance checking
- Returns validation results for artifact caching

### Tool Repository
- Stores and retrieves tool metadata from DynamoDB
- Supports queries by tool ID, agent ID, and code hash
- Manages tool status and execution counts

### Artifact Storage
- Stores validated code artifacts in S3
- Implements content-based addressing with code hashes
- Provides artifact bundling and retrieval

## AWS Services Used

- **Bedrock Agent**: Tool registration and management
- **Bedrock Agent Runtime**: Code Interpreter execution
- **DynamoDB**: Tool metadata storage
- **S3**: Code artifact storage
- **CloudWatch**: Logging and monitoring

## Configuration

The components can be configured through environment variables or constructor parameters:

- `AWS_REGION`: AWS region for services
- `DEFAULT_TIMEOUT`: Default execution timeout (seconds)
- `MAX_TIMEOUT`: Maximum allowed timeout (seconds)
- `POLL_INTERVAL`: Execution status polling interval (seconds)

## Logging

All components use structured logging with contextual information:

```python
logger.info(
    "Tool registered successfully",
    extra={
        "tool_id": tool_id,
        "agent_id": agent_id,
        "duration": duration,
    }
)
```

Log levels:
- **INFO**: Normal operations and state changes
- **WARNING**: Non-critical issues (e.g., sync failures)
- **ERROR**: Critical failures requiring attention
- **DEBUG**: Detailed diagnostic information
