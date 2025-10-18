# Dynamic Tool Runtime - Source Code

This directory contains the core implementation of the Dynamic Tool Runtime system.

## Structure

```
src/
├── models/              # Data models and interfaces
│   ├── tool_definition.py    # Tool definition schemas
│   ├── tool_record.py        # DynamoDB tool records
│   ├── cached_artifact.py    # S3 cached artifacts
│   ├── execution_result.py   # Execution results
│   └── errors.py             # Error definitions
├── repositories/        # Data access layer
│   ├── dynamodb_client.py    # DynamoDB client wrapper
│   └── tool_repository.py    # Tool CRUD operations
├── storage/            # Storage layer
│   ├── s3_client.py          # S3 client wrapper
│   └── artifact_storage.py   # Artifact caching service
├── validation/         # Code validation system
│   ├── validator.py          # Main validation orchestrator
│   ├── python_analyzer.py    # Python code analysis
│   ├── javascript_analyzer.py # JavaScript/TypeScript analysis
│   ├── security_policy.py    # Security policy definitions
│   ├── policy_evaluator.py   # Policy evaluation engine
│   ├── validation_cache.py   # Validation result caching
│   └── validation_service.py # High-level validation service
└── agentcore/          # AgentCore integration layer
    ├── agentcore_client.py   # AgentCore Gateway API client
    ├── code_interpreter.py   # Bedrock Code Interpreter service
    └── tool_lifecycle.py     # Tool lifecycle management
```

## Models

### Tool Definition
- `ToolDefinition`: Complete tool specification from agents
- `ParameterSchema`: Parameter validation schemas
- `ReturnSchema`: Return value schemas
- `ValidationRule`: Parameter validation rules

### Tool Record
- `ToolRecord`: DynamoDB tool metadata record
- `ToolStatus`: Tool lifecycle status (active/inactive/deprecated)

### Cached Artifact
- `CachedToolArtifact`: S3-stored validated tool bundle
- `ValidationResult`: Code validation results
- `ExecutionMetadata`: Execution requirements and limits

### Execution Result
- `ExecutionResult`: Tool execution outcome
- `ExecutionStatus`: Execution status (success/error/timeout)
- `ExecutionError`: Error details
- `ExecutionMetrics`: Performance metrics

### Errors
- `DynamicToolError`: Base exception
- `ValidationError`: Code validation failures
- `ExecutionError`: Runtime execution failures
- `RegistrationError`: AgentCore registration failures
- `StorageError`: DynamoDB/S3 operation failures
- `AuthorizationError`: Permission failures
- `ResourceLimitError`: Resource limit violations

## Repositories

### DynamoDBClient
Low-level DynamoDB operations with error handling:
- `put_item()`: Store item
- `get_item()`: Retrieve item
- `update_item()`: Update item
- `delete_item()`: Delete item
- `query()`: Query with GSI support
- `scan()`: Table scan

### ToolRepository
High-level tool metadata operations:
- `create()`: Create new tool record
- `get_by_id()`: Get tool by ID
- `update()`: Update tool record
- `delete()`: Delete tool record
- `find_by_agent_id()`: Find tools by agent
- `find_by_code_hash()`: Find tool by code hash (cache lookup)
- `find_active_tools()`: Get all active tools
- `increment_execution_count()`: Track usage
- `update_status()`: Change tool status

## Storage

### S3Client
Low-level S3 operations with error handling:
- `put_object()`: Store object
- `get_object()`: Retrieve object
- `delete_object()`: Delete object
- `object_exists()`: Check existence
- `get_object_metadata()`: Get metadata
- `put_json()`: Store JSON
- `get_json()`: Retrieve JSON

### ArtifactStorage
High-level artifact caching service:
- `compute_code_hash()`: SHA-256 content addressing
- `store_artifact()`: Cache validated tool
- `retrieve_artifact()`: Get cached artifact
- `retrieve_code()`: Get validated code
- `artifact_exists()`: Check cache
- `update_usage_count()`: Track reuse
- `delete_artifact()`: Remove from cache
- `create_artifact_bundle()`: Bundle validation results

## Usage Examples

### Creating a Tool Record
```python
from src.models import ToolRecord, ToolSchema
from src.repositories import ToolRepository

# Create tool record
tool_record = ToolRecord.create_new(
    tool_id="tool-123",
    agent_id="agent-456",
    name="data_processor",
    description="Process data",
    version="1.0.0",
    code_artifact_s3_key="artifacts/abc123.json",
    schema=tool_schema,
    code_hash="abc123...",
)

# Save to DynamoDB
repo = ToolRepository()
repo.create(tool_record)
```

### Caching an Artifact
```python
from src.storage import ArtifactStorage
from src.models import ValidationResult, ExecutionMetadata

# Create artifact bundle
storage = ArtifactStorage()
artifact = storage.create_artifact_bundle(
    code="def process(data): return data",
    language="python",
    validation_result=validation_result,
    execution_metadata=execution_metadata,
    dependencies=["boto3"],
)

# Store in S3
storage.store_artifact(artifact)
```

### Cache Lookup
```python
from src.storage import ArtifactStorage

storage = ArtifactStorage()

# Compute hash
code_hash = storage.compute_code_hash(code, "python")

# Check cache
if storage.artifact_exists(code_hash):
    artifact = storage.retrieve_artifact(code_hash)
    print(f"Cache hit! Used {artifact.usage_count} times")
else:
    print("Cache miss - need to validate")
```

## Environment Variables

Required environment variables:
- `DYNAMODB_TABLE_NAME`: DynamoDB table for tool metadata
- `S3_BUCKET_NAME`: S3 bucket for code artifacts
- `AWS_REGION`: AWS region (defaults to us-east-1)

## AgentCore Integration

### AgentCoreClient
AWS AgentCore Gateway API integration:
- `register_tool()`: Register tools with AgentCore
- `deregister_tool()`: Remove tools from AgentCore
- `discover_tools()`: Query available tools
- `sync_tool_metadata()`: Synchronize metadata
- `health_check()`: Verify connectivity
- `_convert_to_openapi_schema()`: Convert to OpenAPI format

### CodeInterpreterService
Bedrock Code Interpreter integration:
- `execute_code()`: Execute tool code in sandbox
- `validate_execution_environment()`: Verify availability
- `get_execution_status()`: Check execution progress
- `cancel_execution()`: Terminate executions
- `_prepare_code()`: Inject parameters
- `_submit_execution()`: Submit to Code Interpreter
- `_poll_execution()`: Poll for completion

### ToolLifecycleManager
Complete tool lifecycle orchestration:
- `register_tool()`: Registration workflow with validation and caching
- `update_tool()`: Update tools with versioning
- `deregister_tool()`: Deregister with cleanup
- `get_tool_status()`: Retrieve tool status

See `src/agentcore/README.md` for detailed documentation.

## Next Steps

The following components need to be implemented:
1. ✅ Code validation system (Task 3) - COMPLETED
2. ✅ AgentCore integration layer (Task 4) - COMPLETED
3. Tool Manager Lambda function (Task 5)
4. API Gateway endpoints (Task 6)
5. Monitoring and observability (Task 7)
