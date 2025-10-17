"""Tool definition data models"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
from enum import Enum


class ParameterType(str, Enum):
    """Supported parameter types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ValidationRule:
    """Validation rule for parameters"""
    rule_type: str
    value: Any
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "rule_type": self.rule_type,
            "value": self.value,
        }
        if self.message:
            result["message"] = self.message
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationRule":
        """Create from dictionary"""
        return cls(
            rule_type=data["rule_type"],
            value=data["value"],
            message=data.get("message"),
        )


@dataclass
class ParameterSchema:
    """Schema definition for tool parameters"""
    type: str
    description: str
    required: bool = False
    default: Optional[Any] = None
    validation: List[ValidationRule] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "type": self.type,
            "description": self.description,
            "required": self.required,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.validation:
            result["validation"] = [rule.to_dict() for rule in self.validation]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterSchema":
        """Create from dictionary"""
        validation_rules = []
        if "validation" in data:
            validation_rules = [
                ValidationRule.from_dict(rule) for rule in data["validation"]
            ]
        
        return cls(
            type=data["type"],
            description=data["description"],
            required=data.get("required", False),
            default=data.get("default"),
            validation=validation_rules,
        )


@dataclass
class ReturnSchema:
    """Schema definition for tool return values"""
    type: str
    description: str
    properties: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "type": self.type,
            "description": self.description,
        }
        if self.properties:
            result["properties"] = self.properties
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReturnSchema":
        """Create from dictionary"""
        return cls(
            type=data["type"],
            description=data["description"],
            properties=data.get("properties"),
        )


@dataclass
class ToolSchema:
    """Complete schema for tool including parameters and return type"""
    parameters: Dict[str, ParameterSchema]
    returns: ReturnSchema

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "parameters": {
                name: param.to_dict() for name, param in self.parameters.items()
            },
            "returns": self.returns.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolSchema":
        """Create from dictionary"""
        parameters = {
            name: ParameterSchema.from_dict(param_data)
            for name, param_data in data["parameters"].items()
        }
        returns = ReturnSchema.from_dict(data["returns"])
        return cls(parameters=parameters, returns=returns)


@dataclass
class ToolDefinition:
    """Complete tool definition submitted by agents"""
    name: str
    description: str
    version: str
    language: Literal["python", "javascript", "typescript"]
    code: str
    schema: ToolSchema
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "language": self.language,
            "code": self.code,
            "schema": self.schema.to_dict(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolDefinition":
        """Create from dictionary"""
        schema = ToolSchema.from_dict(data["schema"])
        return cls(
            name=data["name"],
            description=data["description"],
            version=data["version"],
            language=data["language"],
            code=data["code"],
            schema=schema,
            metadata=data.get("metadata", {}),
        )

    def validate_structure(self) -> List[str]:
        """Validate the structure of the tool definition"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Tool name is required")
        
        if not self.description or not self.description.strip():
            errors.append("Tool description is required")
        
        if not self.version or not self.version.strip():
            errors.append("Tool version is required")
        
        if self.language not in ["python", "javascript", "typescript"]:
            errors.append(f"Unsupported language: {self.language}")
        
        if not self.code or not self.code.strip():
            errors.append("Tool code is required")
        
        return errors
