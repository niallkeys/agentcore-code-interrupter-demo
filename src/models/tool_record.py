"""Tool record data model for DynamoDB storage"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from .tool_definition import ToolSchema


class ToolStatus(str, Enum):
    """Tool lifecycle status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


@dataclass
class ToolRecord:
    """Tool metadata record stored in DynamoDB"""
    tool_id: str
    agent_id: str
    name: str
    description: str
    version: str
    status: ToolStatus
    code_artifact_s3_key: str
    schema: ToolSchema
    created_at: str
    updated_at: str
    execution_count: int = 0
    last_executed: Optional[str] = None
    code_hash: Optional[str] = None
    language: str = "python"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format"""
        item = {
            "toolId": self.tool_id,
            "agentId": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "codeArtifactS3Key": self.code_artifact_s3_key,
            "schema": self.schema.to_dict(),
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "executionCount": self.execution_count,
            "language": self.language,
            "metadata": self.metadata,
        }
        
        if self.last_executed:
            item["lastExecuted"] = self.last_executed
        
        if self.code_hash:
            item["codeHash"] = self.code_hash
        
        return item

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> "ToolRecord":
        """Create from DynamoDB item"""
        schema = ToolSchema.from_dict(item["schema"])
        status = ToolStatus(item["status"])
        
        return cls(
            tool_id=item["toolId"],
            agent_id=item["agentId"],
            name=item["name"],
            description=item["description"],
            version=item["version"],
            status=status,
            code_artifact_s3_key=item["codeArtifactS3Key"],
            schema=schema,
            created_at=item["createdAt"],
            updated_at=item["updatedAt"],
            execution_count=item.get("executionCount", 0),
            last_executed=item.get("lastExecuted"),
            code_hash=item.get("codeHash"),
            language=item.get("language", "python"),
            metadata=item.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {
            "toolId": self.tool_id,
            "agentId": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "codeArtifactS3Key": self.code_artifact_s3_key,
            "schema": self.schema.to_dict(),
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "executionCount": self.execution_count,
            "language": self.language,
            "metadata": self.metadata,
        }
        
        if self.last_executed:
            result["lastExecuted"] = self.last_executed
        
        if self.code_hash:
            result["codeHash"] = self.code_hash
        
        return result

    @classmethod
    def create_new(
        cls,
        tool_id: str,
        agent_id: str,
        name: str,
        description: str,
        version: str,
        code_artifact_s3_key: str,
        schema: ToolSchema,
        code_hash: str,
        language: str = "python",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ToolRecord":
        """Create a new tool record with default values"""
        now = datetime.utcnow().isoformat()
        
        return cls(
            tool_id=tool_id,
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            status=ToolStatus.ACTIVE,
            code_artifact_s3_key=code_artifact_s3_key,
            schema=schema,
            created_at=now,
            updated_at=now,
            execution_count=0,
            code_hash=code_hash,
            language=language,
            metadata=metadata or {},
        )
