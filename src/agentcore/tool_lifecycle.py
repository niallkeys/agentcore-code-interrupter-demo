"""Tool lifecycle management for registration, updates, and deregistration"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Any

from ..models.tool_definition import ToolDefinition
from ..models.tool_record import ToolRecord, ToolStatus
from ..models.cached_artifact import CachedToolArtifact, ExecutionMetadata
from ..models.errors import RegistrationError, ValidationError, StorageError
from ..repositories.tool_repository import ToolRepository
from ..storage.artifact_storage import ArtifactStorage
from ..validation.validation_service import ValidationService
from .agentcore_client import AgentCoreClient
from .code_interpreter import CodeInterpreterService


logger = logging.getLogger(__name__)


class ToolLifecycleManager:
    """
    Manages the complete lifecycle of dynamic tools including:
    - Registration with validation and caching
    - Updates and versioning
    - Deregistration and cleanup
    """
    
    def __init__(
        self,
        tool_repository: Optional[ToolRepository] = None,
        artifact_storage: Optional[ArtifactStorage] = None,
        validation_service: Optional[ValidationService] = None,
        agentcore_client: Optional[AgentCoreClient] = None,
        code_interpreter: Optional[CodeInterpreterService] = None,
    ):
        """
        Initialize tool lifecycle manager
        
        Args:
            tool_repository: Repository for tool metadata
            artifact_storage: Storage for code artifacts
            validation_service: Service for code validation
            agentcore_client: Client for AgentCore integration
            code_interpreter: Service for code execution
        """
        self.tool_repository = tool_repository or ToolRepository()
        self.artifact_storage = artifact_storage or ArtifactStorage()
        self.validation_service = validation_service or ValidationService()
        self.agentcore_client = agentcore_client or AgentCoreClient()
        self.code_interpreter = code_interpreter or CodeInterpreterService()
    
    def register_tool(
        self,
        tool_definition: ToolDefinition,
        agent_id: str,
        skip_cache: bool = False,
    ) -> ToolRecord:
        """
        Register a new tool with validation and caching
        
        This implements the complete tool registration workflow:
        1. Validate tool definition structure
        2. Check cache for existing validated code
        3. If cache miss: validate code and create artifact
        4. Store tool metadata in DynamoDB
        5. Register with AgentCore Gateway
        
        Args:
            tool_definition: Tool definition to register
            agent_id: ID of the agent creating the tool
            skip_cache: Skip cache lookup (force validation)
            
        Returns:
            Created tool record
            
        Raises:
            ValidationError: If validation fails
            RegistrationError: If registration fails
            StorageError: If storage operations fail
        """
        logger.info(
            f"Starting tool registration: {tool_definition.name}",
            extra={
                "tool_name": tool_definition.name,
                "agent_id": agent_id,
                "language": tool_definition.language,
            },
        )
        
        try:
            # Step 1: Validate tool definition structure
            structure_errors = tool_definition.validate_structure()
            if structure_errors:
                raise ValidationError(
                    "Tool definition structure is invalid",
                    errors=structure_errors,
                )
            
            # Step 2: Compute code hash for cache lookup
            code_hash = self.artifact_storage.compute_code_hash(
                tool_definition.code,
                tool_definition.language,
            )
            
            logger.debug(
                f"Computed code hash: {code_hash}",
                extra={
                    "tool_name": tool_definition.name,
                    "code_hash": code_hash,
                },
            )
            
            # Step 3: Check cache for existing artifact
            cached_artifact = None
            if not skip_cache:
                cached_artifact = self.artifact_storage.retrieve_artifact(code_hash)
                
                if cached_artifact:
                    logger.info(
                        f"Cache hit for tool: {tool_definition.name}",
                        extra={
                            "tool_name": tool_definition.name,
                            "code_hash": code_hash,
                            "usage_count": cached_artifact.usage_count,
                        },
                    )
            
            # Step 4: If cache miss, validate and create artifact
            if cached_artifact is None:
                logger.info(
                    f"Cache miss - validating tool: {tool_definition.name}",
                    extra={
                        "tool_name": tool_definition.name,
                        "code_hash": code_hash,
                    },
                )
                
                # Validate code
                validation_result = self.validation_service.validate_code(
                    code=tool_definition.code,
                    language=tool_definition.language,
                )
                
                if not validation_result.is_valid:
                    raise ValidationError(
                        "Code validation failed",
                        errors=validation_result.errors,
                        warnings=validation_result.warnings,
                        security_issues=validation_result.security_issues,
                    )
                
                # Create execution metadata
                execution_metadata = ExecutionMetadata(
                    estimated_memory_mb=128,  # Default values
                    estimated_cpu_ms=1000,
                    timeout_seconds=30,
                    requires_network=False,
                    requires_filesystem=False,
                )
                
                # Create and store artifact
                cached_artifact = self.artifact_storage.create_artifact_bundle(
                    code=tool_definition.code,
                    language=tool_definition.language,
                    validation_result=validation_result,
                    execution_metadata=execution_metadata,
                    dependencies=[],
                )
                
                artifact_key = self.artifact_storage.store_artifact(cached_artifact)
                
                logger.info(
                    f"Artifact created and stored: {artifact_key}",
                    extra={
                        "tool_name": tool_definition.name,
                        "artifact_key": artifact_key,
                    },
                )
            else:
                # Update usage count for cached artifact
                self.artifact_storage.update_usage_count(code_hash)
            
            # Step 5: Create tool record
            tool_id = str(uuid.uuid4())
            artifact_key = self.artifact_storage._get_artifact_key(code_hash)
            
            tool_record = ToolRecord.create_new(
                tool_id=tool_id,
                agent_id=agent_id,
                name=tool_definition.name,
                description=tool_definition.description,
                version=tool_definition.version,
                code_artifact_s3_key=artifact_key,
                schema=tool_definition.schema,
                code_hash=code_hash,
                language=tool_definition.language,
                metadata=tool_definition.metadata,
            )
            
            # Step 6: Store tool record in DynamoDB
            self.tool_repository.create(tool_record)
            
            logger.info(
                f"Tool record created: {tool_id}",
                extra={
                    "tool_id": tool_id,
                    "tool_name": tool_definition.name,
                },
            )
            
            # Step 7: Register with AgentCore Gateway
            try:
                registration_data = self.agentcore_client.register_tool(tool_record)
                
                logger.info(
                    f"Tool registered with AgentCore: {tool_id}",
                    extra={
                        "tool_id": tool_id,
                        "registration_data": registration_data,
                    },
                )
            except RegistrationError as e:
                # Rollback: delete tool record if AgentCore registration fails
                logger.error(
                    f"AgentCore registration failed, rolling back: {str(e)}",
                    extra={"tool_id": tool_id},
                )
                
                try:
                    self.tool_repository.delete(tool_id)
                except Exception as rollback_error:
                    logger.error(
                        f"Rollback failed: {str(rollback_error)}",
                        extra={"tool_id": tool_id},
                    )
                
                raise
            
            logger.info(
                f"Tool registration completed successfully: {tool_id}",
                extra={
                    "tool_id": tool_id,
                    "tool_name": tool_definition.name,
                    "agent_id": agent_id,
                },
            )
            
            return tool_record
            
        except (ValidationError, RegistrationError, StorageError):
            # Re-raise known errors
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during tool registration: {str(e)}",
                extra={
                    "tool_name": tool_definition.name,
                    "agent_id": agent_id,
                },
            )
            raise RegistrationError(
                f"Tool registration failed: {str(e)}",
                agent_id=agent_id,
            )
    
    def update_tool(
        self,
        tool_id: str,
        tool_definition: ToolDefinition,
        agent_id: str,
    ) -> ToolRecord:
        """
        Update an existing tool with new definition
        
        This implements versioning logic:
        1. Retrieve existing tool record
        2. Validate ownership (agent_id match)
        3. Validate new definition
        4. Create new artifact if code changed
        5. Update tool record with new version
        6. Sync metadata with AgentCore
        
        Args:
            tool_id: ID of tool to update
            tool_definition: New tool definition
            agent_id: ID of agent updating the tool
            
        Returns:
            Updated tool record
            
        Raises:
            ValidationError: If validation fails
            RegistrationError: If update fails
            StorageError: If storage operations fail
        """
        logger.info(
            f"Starting tool update: {tool_id}",
            extra={
                "tool_id": tool_id,
                "agent_id": agent_id,
            },
        )
        
        try:
            # Step 1: Retrieve existing tool
            existing_tool = self.tool_repository.get_by_id(tool_id)
            if existing_tool is None:
                raise RegistrationError(
                    f"Tool not found: {tool_id}",
                    tool_id=tool_id,
                )
            
            # Step 2: Validate ownership
            if existing_tool.agent_id != agent_id:
                raise RegistrationError(
                    f"Agent {agent_id} does not own tool {tool_id}",
                    tool_id=tool_id,
                    agent_id=agent_id,
                )
            
            # Step 3: Validate new definition
            structure_errors = tool_definition.validate_structure()
            if structure_errors:
                raise ValidationError(
                    "Tool definition structure is invalid",
                    errors=structure_errors,
                )
            
            # Step 4: Check if code changed
            new_code_hash = self.artifact_storage.compute_code_hash(
                tool_definition.code,
                tool_definition.language,
            )
            
            code_changed = new_code_hash != existing_tool.code_hash
            
            if code_changed:
                logger.info(
                    f"Code changed, creating new artifact: {tool_id}",
                    extra={
                        "tool_id": tool_id,
                        "old_hash": existing_tool.code_hash,
                        "new_hash": new_code_hash,
                    },
                )
                
                # Validate new code
                validation_result = self.validation_service.validate_code(
                    code=tool_definition.code,
                    language=tool_definition.language,
                )
                
                if not validation_result.is_valid:
                    raise ValidationError(
                        "Code validation failed",
                        errors=validation_result.errors,
                        warnings=validation_result.warnings,
                        security_issues=validation_result.security_issues,
                    )
                
                # Create new artifact
                execution_metadata = ExecutionMetadata(
                    estimated_memory_mb=128,
                    estimated_cpu_ms=1000,
                    timeout_seconds=30,
                    requires_network=False,
                    requires_filesystem=False,
                )
                
                new_artifact = self.artifact_storage.create_artifact_bundle(
                    code=tool_definition.code,
                    language=tool_definition.language,
                    validation_result=validation_result,
                    execution_metadata=execution_metadata,
                    dependencies=[],
                )
                
                artifact_key = self.artifact_storage.store_artifact(new_artifact)
            else:
                artifact_key = existing_tool.code_artifact_s3_key
            
            # Step 5: Update tool record
            existing_tool.name = tool_definition.name
            existing_tool.description = tool_definition.description
            existing_tool.version = tool_definition.version
            existing_tool.schema = tool_definition.schema
            existing_tool.code_artifact_s3_key = artifact_key
            existing_tool.code_hash = new_code_hash
            existing_tool.language = tool_definition.language
            existing_tool.metadata = tool_definition.metadata
            
            updated_tool = self.tool_repository.update(existing_tool)
            
            # Step 6: Sync with AgentCore
            try:
                self.agentcore_client.sync_tool_metadata(
                    tool_id=tool_id,
                    metadata=updated_tool.to_dict(),
                )
            except RegistrationError as e:
                logger.warning(
                    f"Failed to sync metadata with AgentCore: {str(e)}",
                    extra={"tool_id": tool_id},
                )
                # Don't fail the update if sync fails
            
            logger.info(
                f"Tool update completed successfully: {tool_id}",
                extra={
                    "tool_id": tool_id,
                    "version": tool_definition.version,
                },
            )
            
            return updated_tool
            
        except (ValidationError, RegistrationError, StorageError):
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during tool update: {str(e)}",
                extra={"tool_id": tool_id},
            )
            raise RegistrationError(
                f"Tool update failed: {str(e)}",
                tool_id=tool_id,
                agent_id=agent_id,
            )
    
    def deregister_tool(
        self,
        tool_id: str,
        agent_id: str,
        delete_artifact: bool = False,
    ) -> None:
        """
        Deregister a tool and perform cleanup
        
        This implements the deregistration workflow:
        1. Retrieve tool record
        2. Validate ownership
        3. Deregister from AgentCore
        4. Update status to inactive or delete record
        5. Optionally delete artifact if not shared
        
        Args:
            tool_id: ID of tool to deregister
            agent_id: ID of agent deregistering the tool
            delete_artifact: Whether to delete the artifact (default: False)
            
        Raises:
            RegistrationError: If deregistration fails
            StorageError: If storage operations fail
        """
        logger.info(
            f"Starting tool deregistration: {tool_id}",
            extra={
                "tool_id": tool_id,
                "agent_id": agent_id,
                "delete_artifact": delete_artifact,
            },
        )
        
        try:
            # Step 1: Retrieve tool record
            tool_record = self.tool_repository.get_by_id(tool_id)
            if tool_record is None:
                raise RegistrationError(
                    f"Tool not found: {tool_id}",
                    tool_id=tool_id,
                )
            
            # Step 2: Validate ownership
            if tool_record.agent_id != agent_id:
                raise RegistrationError(
                    f"Agent {agent_id} does not own tool {tool_id}",
                    tool_id=tool_id,
                    agent_id=agent_id,
                )
            
            # Step 3: Deregister from AgentCore
            try:
                self.agentcore_client.deregister_tool(
                    tool_id=tool_id,
                    agent_id=agent_id,
                )
            except RegistrationError as e:
                logger.warning(
                    f"Failed to deregister from AgentCore: {str(e)}",
                    extra={"tool_id": tool_id},
                )
                # Continue with cleanup even if AgentCore deregistration fails
            
            # Step 4: Update status or delete record
            if delete_artifact:
                # Delete tool record
                self.tool_repository.delete(tool_id)
                
                logger.info(
                    f"Tool record deleted: {tool_id}",
                    extra={"tool_id": tool_id},
                )
            else:
                # Mark as inactive
                self.tool_repository.update_status(tool_id, ToolStatus.INACTIVE)
                
                logger.info(
                    f"Tool marked as inactive: {tool_id}",
                    extra={"tool_id": tool_id},
                )
            
            # Step 5: Optionally delete artifact
            if delete_artifact and tool_record.code_hash:
                # Check if artifact is shared by other tools
                other_tools = self.tool_repository.find_by_code_hash(
                    tool_record.code_hash
                )
                
                if other_tools is None or other_tools.tool_id == tool_id:
                    # No other tools use this artifact, safe to delete
                    self.artifact_storage.delete_artifact(
                        code_hash=tool_record.code_hash,
                        language=tool_record.language,
                    )
                    
                    logger.info(
                        f"Artifact deleted: {tool_record.code_hash}",
                        extra={
                            "tool_id": tool_id,
                            "code_hash": tool_record.code_hash,
                        },
                    )
                else:
                    logger.info(
                        f"Artifact shared by other tools, not deleting: {tool_record.code_hash}",
                        extra={
                            "tool_id": tool_id,
                            "code_hash": tool_record.code_hash,
                        },
                    )
            
            logger.info(
                f"Tool deregistration completed successfully: {tool_id}",
                extra={"tool_id": tool_id},
            )
            
        except (RegistrationError, StorageError):
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during tool deregistration: {str(e)}",
                extra={"tool_id": tool_id},
            )
            raise RegistrationError(
                f"Tool deregistration failed: {str(e)}",
                tool_id=tool_id,
                agent_id=agent_id,
            )
    
    def get_tool_status(
        self,
        tool_id: str,
    ) -> Dict[str, Any]:
        """
        Get the current status of a tool
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool status information
            
        Raises:
            StorageError: If retrieval fails
        """
        tool_record = self.tool_repository.get_by_id(tool_id)
        if tool_record is None:
            raise StorageError(
                f"Tool not found: {tool_id}",
                operation="get_tool_status",
                resource=tool_id,
            )
        
        return {
            "toolId": tool_id,
            "status": tool_record.status.value,
            "version": tool_record.version,
            "executionCount": tool_record.execution_count,
            "lastExecuted": tool_record.last_executed,
            "createdAt": tool_record.created_at,
            "updatedAt": tool_record.updated_at,
        }
