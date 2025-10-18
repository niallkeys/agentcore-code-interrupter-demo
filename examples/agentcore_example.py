"""Example usage of AgentCore integration layer"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agentcore import ToolLifecycleManager, AgentCoreClient, CodeInterpreterService
from src.models.tool_definition import (
    ToolDefinition,
    ToolSchema,
    ParameterSchema,
    ReturnSchema,
)


def example_register_tool():
    """Example: Register a new dynamic tool"""
    
    # Create tool definition
    tool_definition = ToolDefinition(
        name="string_reverser",
        description="Reverses a string",
        version="1.0.0",
        language="python",
        code="""
def reverse_string(text):
    return text[::-1]

result = reverse_string(input_text)
""",
        schema=ToolSchema(
            parameters={
                "input_text": ParameterSchema(
                    type="string",
                    description="Text to reverse",
                    required=True,
                )
            },
            returns=ReturnSchema(
                type="string",
                description="Reversed text",
            ),
        ),
        metadata={
            "author": "example_agent",
            "tags": ["string", "utility"],
        },
    )
    
    # Initialize lifecycle manager
    manager = ToolLifecycleManager()
    
    # Register tool
    print("Registering tool...")
    tool_record = manager.register_tool(
        tool_definition=tool_definition,
        agent_id="agent-123",
        skip_cache=False,
    )
    
    print(f"Tool registered successfully!")
    print(f"  Tool ID: {tool_record.tool_id}")
    print(f"  Name: {tool_record.name}")
    print(f"  Version: {tool_record.version}")
    print(f"  Status: {tool_record.status.value}")
    print(f"  Code Hash: {tool_record.code_hash}")
    
    return tool_record


def example_execute_tool(tool_record):
    """Example: Execute a registered tool"""
    
    # Initialize code interpreter
    interpreter = CodeInterpreterService()
    
    # Retrieve validated code from artifact storage
    from src.storage import ArtifactStorage
    storage = ArtifactStorage()
    
    artifact = storage.retrieve_artifact(tool_record.code_hash)
    if not artifact:
        print("Error: Artifact not found")
        return
    
    # Execute tool
    print("\nExecuting tool...")
    result = interpreter.execute_code(
        tool_id=tool_record.tool_id,
        code=artifact.validated_code,
        parameters={"input_text": "Hello, World!"},
        language=tool_record.language,
        timeout_seconds=30,
    )
    
    print(f"Execution completed!")
    print(f"  Status: {result.status.value}")
    print(f"  Result: {result.result}")
    print(f"  Duration: {result.metrics.duration:.2f}s")
    
    return result


def example_update_tool(tool_id):
    """Example: Update an existing tool"""
    
    # Create updated definition
    updated_definition = ToolDefinition(
        name="string_reverser",
        description="Reverses a string (improved version)",
        version="1.1.0",
        language="python",
        code="""
def reverse_string(text):
    # Improved version with validation
    if not text:
        return ""
    return text[::-1]

result = reverse_string(input_text)
""",
        schema=ToolSchema(
            parameters={
                "input_text": ParameterSchema(
                    type="string",
                    description="Text to reverse",
                    required=True,
                )
            },
            returns=ReturnSchema(
                type="string",
                description="Reversed text",
            ),
        ),
    )
    
    # Initialize lifecycle manager
    manager = ToolLifecycleManager()
    
    # Update tool
    print("\nUpdating tool...")
    updated_record = manager.update_tool(
        tool_id=tool_id,
        tool_definition=updated_definition,
        agent_id="agent-123",
    )
    
    print(f"Tool updated successfully!")
    print(f"  Version: {updated_record.version}")
    print(f"  Updated At: {updated_record.updated_at}")
    
    return updated_record


def example_deregister_tool(tool_id):
    """Example: Deregister a tool"""
    
    # Initialize lifecycle manager
    manager = ToolLifecycleManager()
    
    # Deregister tool
    print("\nDeregistering tool...")
    manager.deregister_tool(
        tool_id=tool_id,
        agent_id="agent-123",
        delete_artifact=False,  # Keep artifact for other tools
    )
    
    print(f"Tool deregistered successfully!")


def example_agentcore_client():
    """Example: Direct AgentCore client usage"""
    
    # Initialize client
    client = AgentCoreClient()
    
    # Health check
    print("\nChecking AgentCore health...")
    is_healthy = client.health_check()
    print(f"  AgentCore is {'healthy' if is_healthy else 'unhealthy'}")
    
    # Discover tools
    print("\nDiscovering tools...")
    tools = client.discover_tools(agent_id="agent-123")
    print(f"  Found {len(tools)} tools")


def main():
    """Run all examples"""
    
    print("=" * 60)
    print("AgentCore Integration Layer - Examples")
    print("=" * 60)
    
    try:
        # Example 1: Register a tool
        tool_record = example_register_tool()
        
        # Example 2: Execute the tool
        example_execute_tool(tool_record)
        
        # Example 3: Update the tool
        example_update_tool(tool_record.tool_id)
        
        # Example 4: AgentCore client
        example_agentcore_client()
        
        # Example 5: Deregister the tool
        example_deregister_tool(tool_record.tool_id)
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
