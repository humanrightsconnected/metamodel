"""
Core models for representing and validating metamodel structures.
"""
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class AttributeType(str, Enum):
    """Supported attribute types in the metamodel."""
    STRING = "string"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    NUMBER = "number"
    ARRAY = "array"
    OBJECT = "object"
    DATETIME = "datetime"


class MetamodelAttribute(BaseModel):
    """Represents a single attribute in the metamodel."""
    name: str
    description: str
    type: AttributeType
    required: bool
    enum: Optional[List[str]] = None
    
    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        """Validate that the attribute name is properly formatted."""
        if not v or not v.strip():
            raise ValueError("Attribute name cannot be empty")
        if len(v) > 100:
            raise ValueError("Attribute name too long (max 100 characters)")
        return v
    
    @field_validator("description")
    @classmethod
    def description_must_be_valid(cls, v: str) -> str:
        """Validate that the attribute description is properly formatted."""
        if not v or not v.strip():
            raise ValueError("Attribute description cannot be empty")
        return v


class MetamodelGroup(BaseModel):
    """Represents a group of related attributes in the metamodel."""
    name: str
    description: str
    attributes: List[MetamodelAttribute]
    
    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        """Validate that the group name is properly formatted."""
        if not v or not v.strip():
            raise ValueError("Group name cannot be empty")
        if len(v) > 100:
            raise ValueError("Group name too long (max 100 characters)")
        return v
    
    @field_validator("description")
    @classmethod
    def description_must_be_valid(cls, v: str) -> str:
        """Validate that the group description is properly formatted."""
        if not v or not v.strip():
            raise ValueError("Group description cannot be empty")
        return v
    
    @field_validator("attributes")
    @classmethod
    def attributes_must_not_be_empty(cls, v: List[MetamodelAttribute]) -> List[MetamodelAttribute]:
        """Validate that the group contains at least one attribute."""
        if not v:
            raise ValueError("Group must contain at least one attribute")
        return v


class Metamodel(BaseModel):
    """Represents the complete metamodel structure."""
    name: str
    version: str
    description: str
    groups: List[MetamodelGroup]
    
    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        """Validate that the metamodel name is properly formatted."""
        if not v or not v.strip():
            raise ValueError("Metamodel name cannot be empty")
        return v
    
    @field_validator("version")
    @classmethod
    def version_must_be_valid(cls, v: str) -> str:
        """Validate that the metamodel version follows semantic versioning."""
        if not re.match(r"^\d+\.\d+(\.\d+)?$", v):
            raise ValueError("Version must follow semantic versioning (e.g., 1.0.0)")
        return v
    
    @field_validator("groups")
    @classmethod
    def groups_must_not_be_empty(cls, v: List[MetamodelGroup]) -> List[MetamodelGroup]:
        """Validate that the metamodel contains at least one group."""
        if not v:
            raise ValueError("Metamodel must contain at least one group")
        return v
    
    def get_required_attributes(self) -> List[Dict[str, Any]]:
        """Get all required attributes from all groups."""
        required_attributes = []
        for group in self.groups:
            for attr in group.attributes:
                if attr.required:
                    required_attributes.append({
                        "name": attr.name,
                        "type": attr.type,
                        "group": group.name
                    })
        return required_attributes
    
    def get_attribute_by_name(self, name: str) -> Optional[MetamodelAttribute]:
        """Find an attribute by its name."""
        for group in self.groups:
            for attr in group.attributes:
                if attr.name == name:
                    return attr
        return None
    
    def model_dump(self) -> Dict[str, Any]:
        """Convert the metamodel to a dictionary representation."""
        return super().model_dump()
    
    @classmethod
    def model_validate(cls, data: Dict[str, Any]) -> "Metamodel":
        """Create a Metamodel instance from a dictionary."""
        return super().model_validate(data)
    
    @classmethod
    def from_json_file(cls, file_path: str) -> "Metamodel":
        """Load a Metamodel from a JSON file."""
        import json
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.model_validate(data)


class ChangeType(str, Enum):
    """Types of changes that can be made to a metamodel."""
    ADD_GROUP = "add_group"
    REMOVE_GROUP = "remove_group"
    MODIFY_GROUP = "modify_group"
    ADD_ATTRIBUTE = "add_attribute"
    REMOVE_ATTRIBUTE = "remove_attribute"
    MODIFY_ATTRIBUTE = "modify_attribute"
    CHANGE_REQUIREMENT = "change_requirement"


class MetamodelChange(BaseModel):
    """Represents a change to the metamodel."""
    change_type: ChangeType
    target_path: str  # E.g., "group_name/attribute_name" or "group_name"
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    description: str
    
    @field_validator("target_path")
    @classmethod
    def target_path_must_be_valid(cls, v: str) -> str:
        """Validate that the target path is properly formatted."""
        if not v or not v.strip():
            raise ValueError("Target path cannot be empty")
        return v
    
    @field_validator("description")
    @classmethod
    def description_must_be_valid(cls, v: str) -> str:
        """Validate that the change description is properly formatted."""
        if not v or not v.strip():
            raise ValueError("Change description cannot be empty")
        return v