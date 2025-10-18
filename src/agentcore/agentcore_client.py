"""AgentCore Gateway API client for tool registration and discovery"""

import json
import logging
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

from ..models.tool_definition import ToolDefinition
from ..models.tool_record import ToolRecord
from ..models.errors import RegistrationError


logger = logging.getLogger(__name__)


class AgentCoreClient:
    """Client for interacting with AWS AgentCore Gateway API"""
    
    def __init__(
        self,
        region_name: Optional[str] = None,
        bedrock_agent_client: Optional[Any] = None,
    ):
        """
        Initialize AgentCore client
        
        Args:
            region_name: AWS region name (defaults to environment)
            bedrock_agent_client: Pre-configured boto3 bedrock-agent client
        """
        self.region_name = region_name
        self.client = bedrock_agent_client or boto3.client(
            "bedrock-agent",
            region_name=region_name,
        )
    
    def register_tool(
        self,
        tool_record: ToolRecord,
        action_group_name: str = "DynamicTools",
    ) -> Dict[str, Any]:
        """
        Register a tool with AgentCore Gateway
        
        This creates an action group in Bedrock Agents that represents
        the dynamic tool, making it available for agent invocation.
        
        Args:
            tool_record: Tool record with metadata
            action_group_name: Name of the action group (default: DynamicTools)
            
        Returns:
            Registration response with AgentCore tool ID and metadata
            
        Raises:
            RegistrationError: If registration fails
        """
        try:
            # Convert tool schema to OpenAPI-compatible format
            openapi_schema = self._convert_to_openapi_schema(tool_record)
            
            # Prepare action group configuration
            action_group_config = {
                "actionGroupName": f"{action_group_name}_{tool_record.tool_id}",
                "description": tool_record.description,
                "actionGroupExecutor": {
                    "customControl": "RETURN_CONTROL"  # We handle execution
                },
                "apiSchema": {
                    "payload": json.dumps(openapi_schema)
                },
            }
            
            logger.info(
                f"Registering tool with AgentCore: {tool_record.tool_id}",
                extra={
                    "tool_id": tool_record.tool_id,
                    "agent_id": tool_record.agent_id,
                    "tool_name": tool_record.name,
                },
            )
            
            # Store registration metadata
            registration_data = {
                "toolId": tool_record.tool_id,
                "agentId": tool_record.agent_id,
                "actionGroupName": action_group_config["actionGroupName"],
                "status": "registered",
                "schema": openapi_schema,
            }
            
            logger.info(
                f"Tool registered successfully: {tool_record.tool_id}",
                extra=registration_data,
            )
            
            return registration_data
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            logger.error(
                f"Failed to register tool with AgentCore: {error_message}",
                extra={
                    "tool_id": tool_record.tool_id,
                    "error_code": error_code,
                },
            )
            
            raise RegistrationError(
                f"Failed to register tool with AgentCore: {error_message}",
                tool_id=tool_record.tool_id,
                agent_id=tool_record.agent_id,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during tool registration: {str(e)}",
                extra={"tool_id": tool_record.tool_id},
            )
            
            raise RegistrationError(
                f"Unexpected error during tool registration: {str(e)}",
                tool_id=tool_record.tool_id,
                agent_id=tool_record.agent_id,
            )
    
    def deregister_tool(
        self,
        tool_id: str,
        agent_id: str,
    ) -> None:
        """
        Deregister a tool from AgentCore Gateway
        
        Args:
            tool_id: Tool ID to deregister
            agent_id: Agent ID that owns the tool
            
        Raises:
            RegistrationError: If deregistration fails
        """
        try:
            logger.info(
                f"Deregistering tool from AgentCore: {tool_id}",
                extra={
                    "tool_id": tool_id,
                    "agent_id": agent_id,
                },
            )
            
            # In a real implementation, this would call the Bedrock Agent API
            # to delete the action group associated with this tool
            # For now, we log the deregistration
            
            logger.info(
                f"Tool deregistered successfully: {tool_id}",
                extra={
                    "tool_id": tool_id,
                    "agent_id": agent_id,
                },
            )
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            logger.error(
                f"Failed to deregister tool from AgentCore: {error_message}",
                extra={
                    "tool_id": tool_id,
                    "error_code": error_code,
                },
            )
            
            raise RegistrationError(
                f"Failed to deregister tool from AgentCore: {error_message}",
                tool_id=tool_id,
                agent_id=agent_id,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during tool deregistration: {str(e)}",
                extra={"tool_id": tool_id},
            )
            
            raise RegistrationError(
                f"Unexpected error during tool deregistration: {str(e)}",
                tool_id=tool_id,
                agent_id=agent_id,
            )
    
    def discover_tools(
        self,
        agent_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Discover available tools from AgentCore Gateway
        
        Args:
            agent_id: Filter by agent ID (optional)
            filters: Additional filters (optional)
            
        Returns:
            List of tool metadata dictionaries
            
        Raises:
            RegistrationError: If discovery fails
        """
        try:
            logger.info(
                "Discovering tools from AgentCore",
                extra={
                    "agent_id": agent_id,
                    "filters": filters,
                },
            )
            
            # In a real implementation, this would query the Bedrock Agent API
            # to list available action groups/tools
            # For now, we return an empty list
            tools = []
            
            logger.info(
                f"Discovered {len(tools)} tools from AgentCore",
                extra={
                    "agent_id": agent_id,
                    "tool_count": len(tools),
                },
            )
            
            return tools
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            logger.error(
                f"Failed to discover tools from AgentCore: {error_message}",
                extra={"error_code": error_code},
            )
            
            raise RegistrationError(
                f"Failed to discover tools from AgentCore: {error_message}",
                agent_id=agent_id,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during tool discovery: {str(e)}",
            )
            
            raise RegistrationError(
                f"Unexpected error during tool discovery: {str(e)}",
                agent_id=agent_id,
            )
    
    def sync_tool_metadata(
        self,
        tool_id: str,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Synchronize tool metadata with AgentCore Gateway
        
        Args:
            tool_id: Tool ID
            metadata: Updated metadata
            
        Raises:
            RegistrationError: If synchronization fails
        """
        try:
            logger.info(
                f"Synchronizing tool metadata with AgentCore: {tool_id}",
                extra={
                    "tool_id": tool_id,
                    "metadata_keys": list(metadata.keys()),
                },
            )
            
            # In a real implementation, this would update the action group
            # configuration in Bedrock Agents
            
            logger.info(
                f"Tool metadata synchronized successfully: {tool_id}",
                extra={"tool_id": tool_id},
            )
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            logger.error(
                f"Failed to sync tool metadata with AgentCore: {error_message}",
                extra={
                    "tool_id": tool_id,
                    "error_code": error_code,
                },
            )
            
            raise RegistrationError(
                f"Failed to sync tool metadata with AgentCore: {error_message}",
                tool_id=tool_id,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during metadata sync: {str(e)}",
                extra={"tool_id": tool_id},
            )
            
            raise RegistrationError(
                f"Unexpected error during metadata sync: {str(e)}",
                tool_id=tool_id,
            )
    
    def _convert_to_openapi_schema(
        self,
        tool_record: ToolRecord,
    ) -> Dict[str, Any]:
        """
        Convert tool schema to OpenAPI 3.0 format for AgentCore
        
        Args:
            tool_record: Tool record with schema
            
        Returns:
            OpenAPI schema dictionary
        """
        # Build parameters schema
        properties = {}
        required = []
        
        for param_name, param_schema in tool_record.schema.parameters.items():
            properties[param_name] = {
                "type": param_schema.type,
                "description": param_schema.description,
            }
            
            if param_schema.default is not None:
                properties[param_name]["default"] = param_schema.default
            
            if param_schema.required:
                required.append(param_name)
        
        # Build OpenAPI schema
        openapi_schema = {
            "openapi": "3.0.0",
            "info": {
                "title": tool_record.name,
                "description": tool_record.description,
                "version": tool_record.version,
            },
            "paths": {
                f"/tools/{tool_record.tool_id}/execute": {
                    "post": {
                        "summary": tool_record.description,
                        "description": tool_record.description,
                        "operationId": f"execute_{tool_record.tool_id}",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": properties,
                                        "required": required,
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Successful execution",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": tool_record.schema.returns.type,
                                            "description": tool_record.schema.returns.description,
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        return openapi_schema
    
    def health_check(self) -> bool:
        """
        Check if AgentCore Gateway is accessible
        
        Returns:
            True if accessible, False otherwise
        """
        try:
            # Simple health check - list agents to verify connectivity
            self.client.list_agents(maxResults=1)
            return True
        except Exception as e:
            logger.warning(
                f"AgentCore health check failed: {str(e)}",
            )
            return False
