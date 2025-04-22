"""
Validation logic for metamodel structures and changes.
"""
from typing import Dict, List, Optional, Tuple, Any, Set

from .metamodel import Metamodel, MetamodelChange, ChangeType, MetamodelAttribute, MetamodelGroup


class MetamodelValidator:
    """Class for validating metamodel structures and changes."""
    
    def validate_metamodel(self, metamodel: Metamodel) -> Tuple[bool, List[str]]:
        """
        Validate a complete metamodel structure.
        
        Args:
            metamodel: The metamodel to validate
            
        Returns:
            Tuple of (is_valid, list_of_validation_errors)
        """
        errors = []
        
        # Check for duplicate group names
        group_names = [group.name for group in metamodel.groups]
        if len(group_names) != len(set(group_names)):
            errors.append("Duplicate group names found")
        
        # Check for duplicate attribute names across groups
        all_attributes: Dict[str, List[str]] = {}
        for group in metamodel.groups:
            for attr in group.attributes:
                if attr.name not in all_attributes:
                    all_attributes[attr.name] = []
                all_attributes[attr.name].append(group.name)
        
        for attr_name, groups in all_attributes.items():
            if len(groups) > 1:
                errors.append(
                    f"Attribute '{attr_name}' is duplicated across groups: {', '.join(groups)}"
                )
        
        # Validate each attribute's constraints based on its type
        for group in metamodel.groups:
            for attr in group.attributes:
                # Enum values are only valid for string type
                if attr.enum is not None and attr.type != "string":
                    errors.append(
                        f"Attribute '{attr.name}' in group '{group.name}' has enum values but is not of type string"
                    )
        
        return len(errors) == 0, errors
    
    def validate_change(
        self, current_metamodel: Metamodel, change: MetamodelChange
    ) -> Tuple[bool, List[str]]:
        """
        Validate a proposed change to the metamodel.
        
        Args:
            current_metamodel: The current state of the metamodel
            change: The proposed change
            
        Returns:
            Tuple of (is_valid, list_of_validation_errors)
        """
        errors = []
        
        # Validate based on change type
        if change.change_type == ChangeType.ADD_GROUP:
            if not isinstance(change.new_value, dict):
                errors.append("New group value must be a dictionary")
            else:
                # Check if group name already exists
                if any(group.name == change.new_value.get("name") for group in current_metamodel.groups):
                    errors.append(f"Group '{change.new_value.get('name')}' already exists")
        
        elif change.change_type == ChangeType.REMOVE_GROUP:
            # Check if group exists
            if not any(group.name == change.target_path for group in current_metamodel.groups):
                errors.append(f"Group '{change.target_path}' does not exist")
                
            # Check if group contains required attributes
            for group in current_metamodel.groups:
                if group.name == change.target_path:
                    required_attrs = [attr for attr in group.attributes if attr.required]
                    if required_attrs:
                        errors.append(
                            f"Cannot remove group '{change.target_path}' because it contains required attributes"
                        )
        
        elif change.change_type == ChangeType.ADD_ATTRIBUTE:
            parts = change.target_path.split("/")
            if len(parts) != 2:
                errors.append("Target path for add_attribute must be in format 'group_name/attribute_name'")
            else:
                group_name, attr_name = parts
                
                # Check if group exists
                group = next((g for g in current_metamodel.groups if g.name == group_name), None)
                if not group:
                    errors.append(f"Group '{group_name}' does not exist")
                else:
                    # Check if attribute already exists in the group
                    if any(attr.name == attr_name for attr in group.attributes):
                        errors.append(f"Attribute '{attr_name}' already exists in group '{group_name}'")
                        
                    # Check if attribute exists in any other group
                    for other_group in current_metamodel.groups:
                        if other_group.name != group_name:
                            if any(attr.name == attr_name for attr in other_group.attributes):
                                errors.append(
                                    f"Attribute '{attr_name}' already exists in group '{other_group.name}'"
                                )
        
        elif change.change_type == ChangeType.REMOVE_ATTRIBUTE:
            parts = change.target_path.split("/")
            if len(parts) != 2:
                errors.append("Target path for remove_attribute must be in format 'group_name/attribute_name'")
            else:
                group_name, attr_name = parts
                
                # Check if group exists
                group = next((g for g in current_metamodel.groups if g.name == group_name), None)
                if not group:
                    errors.append(f"Group '{group_name}' does not exist")
                else:
                    # Check if attribute exists in the group
                    attr = next((a for a in group.attributes if a.name == attr_name), None)
                    if not attr:
                        errors.append(f"Attribute '{attr_name}' does not exist in group '{group_name}'")
                    elif attr.required:
                        errors.append(f"Cannot remove required attribute '{attr_name}' from group '{group_name}'")
        
        elif change.change_type == ChangeType.CHANGE_REQUIREMENT:
            parts = change.target_path.split("/")
            if len(parts) != 2:
                errors.append("Target path for change_requirement must be in format 'group_name/attribute_name'")
            else:
                group_name, attr_name = parts
                
                # Check if the new value is a boolean
                if not isinstance(change.new_value, bool):
                    errors.append("New value for change_requirement must be a boolean")
                    
                # Check if group exists
                group = next((g for g in current_metamodel.groups if g.name == group_name), None)
                if not group:
                    errors.append(f"Group '{group_name}' does not exist")
                else:
                    # Check if attribute exists in the group
                    attr = next((a for a in group.attributes if a.name == attr_name), None)
                    if not attr:
                        errors.append(f"Attribute '{attr_name}' does not exist in group '{group_name}'")
                    # If changing from required to not required, the attribute must be currently required
                    elif not change.new_value and not attr.required:
                        errors.append(f"Attribute '{attr_name}' is already not required")
                    # If changing from not required to required, the attribute must be currently not required
                    elif change.new_value and attr.required:
                        errors.append(f"Attribute '{attr_name}' is already required")
        
        return len(errors) == 0, errors
    
    def validate_backward_compatibility(
        self, old_metamodel: Metamodel, new_metamodel: Metamodel
    ) -> Tuple[bool, List[str]]:
        """
        Validate that a new metamodel version is backward compatible with the old version.
        
        Args:
            old_metamodel: The previous metamodel version
            new_metamodel: The new metamodel version
            
        Returns:
            Tuple of (is_compatible, list_of_compatibility_errors)
        """
        errors = []
        
        # Check that all required attributes in the old model are still present and required in the new model
        old_required = set()
        for group in old_metamodel.groups:
            for attr in group.attributes:
                if attr.required:
                    old_required.add((group.name, attr.name))
        
        new_required = set()
        for group in new_metamodel.groups:
            for attr in group.attributes:
                if attr.required:
                    new_required.add((group.name, attr.name))
        
        # Find required attributes that were removed or made optional
        for group_name, attr_name in old_required:
            if (group_name, attr_name) not in new_required:
                # Check if the group still exists
                new_group = next((g for g in new_metamodel.groups if g.name == group_name), None)
                if not new_group:
                    errors.append(f"Required group '{group_name}' was removed")
                else:
                    # Check if the attribute still exists in the group
                    new_attr = next((a for a in new_group.attributes if a.name == attr_name), None)
                    if not new_attr:
                        errors.append(f"Required attribute '{attr_name}' was removed from group '{group_name}'")
                    else:
                        errors.append(f"Required attribute '{attr_name}' in group '{group_name}' was made optional")
        
        # Check for type changes in existing attributes
        for old_group in old_metamodel.groups:
            new_group = next((g for g in new_metamodel.groups if g.name == old_group.name), None)
            if new_group:
                for old_attr in old_group.attributes:
                    new_attr = next((a for a in new_group.attributes if a.name == old_attr.name), None)
                    if new_attr and old_attr.type != new_attr.type:
                        errors.append(
                            f"Type of attribute '{old_attr.name}' in group '{old_group.name}' "
                            f"changed from '{old_attr.type}' to '{new_attr.type}'"
                        )
        
        return len(errors) == 0, errors


class ChangeAnalyzer:
    """Analyzes changes between metamodel versions."""
    
    def detect_changes(
        self, old_metamodel: Metamodel, new_metamodel: Metamodel
    ) -> List[MetamodelChange]:
        """
        Detect changes between two metamodel versions.
        
        Args:
            old_metamodel: The previous metamodel version
            new_metamodel: The new metamodel version
            
        Returns:
            List of detected changes
        """
        changes = []
        
        # Track groups in old and new metamodels
        old_groups = {group.name: group for group in old_metamodel.groups}
        new_groups = {group.name: group for group in new_metamodel.groups}
        
        # Detect added and removed groups
        for group_name in set(new_groups.keys()) - set(old_groups.keys()):
            group = new_groups[group_name]
            changes.append(
                MetamodelChange(
                    change_type=ChangeType.ADD_GROUP,
                    target_path=group_name,
                    new_value=group.model_dump(),
                    description=f"Added new group '{group_name}'"
                )
            )
        
        for group_name in set(old_groups.keys()) - set(new_groups.keys()):
            group = old_groups[group_name]
            changes.append(
                MetamodelChange(
                    change_type=ChangeType.REMOVE_GROUP,
                    target_path=group_name,
                    old_value=group.model_dump(),
                    description=f"Removed group '{group_name}'"
                )
            )
        
        # Detect changes within groups that exist in both versions
        for group_name in set(old_groups.keys()) & set(new_groups.keys()):
            old_group = old_groups[group_name]
            new_group = new_groups[group_name]
            
            # Check for changes in group description
            if old_group.description != new_group.description:
                changes.append(
                    MetamodelChange(
                        change_type=ChangeType.MODIFY_GROUP,
                        target_path=group_name,
                        old_value={"description": old_group.description},
                        new_value={"description": new_group.description},
                        description=f"Modified description of group '{group_name}'"
                    )
                )
            
            # Track attributes in old and new groups
            old_attrs = {attr.name: attr for attr in old_group.attributes}
            new_attrs = {attr.name: attr for attr in new_group.attributes}
            
            # Detect added and removed attributes
            for attr_name in set(new_attrs.keys()) - set(old_attrs.keys()):
                attr = new_attrs[attr_name]
                changes.append(
                    MetamodelChange(
                        change_type=ChangeType.ADD_ATTRIBUTE,
                        target_path=f"{group_name}/{attr_name}",
                        new_value=attr.model_dump(),
                        description=f"Added new attribute '{attr_name}' to group '{group_name}'"
                    )
                )
            
            for attr_name in set(old_attrs.keys()) - set(new_attrs.keys()):
                attr = old_attrs[attr_name]
                changes.append(
                    MetamodelChange(
                        change_type=ChangeType.REMOVE_ATTRIBUTE,
                        target_path=f"{group_name}/{attr_name}",
                        old_value=attr.model_dump(),
                        description=f"Removed attribute '{attr_name}' from group '{group_name}'"
                    )
                )
            
            # Detect changes within attributes that exist in both versions
            for attr_name in set(old_attrs.keys()) & set(new_attrs.keys()):
                old_attr = old_attrs[attr_name]
                new_attr = new_attrs[attr_name]
                
                # Check for changes in attribute properties
                changes_in_attr = {}
                if old_attr.description != new_attr.description:
                    changes_in_attr["description"] = (old_attr.description, new_attr.description)
                if old_attr.type != new_attr.type:
                    changes_in_attr["type"] = (old_attr.type, new_attr.type)
                if old_attr.enum != new_attr.enum:
                    changes_in_attr["enum"] = (old_attr.enum, new_attr.enum)
                
                if changes_in_attr:
                    changes.append(
                        MetamodelChange(
                            change_type=ChangeType.MODIFY_ATTRIBUTE,
                            target_path=f"{group_name}/{attr_name}",
                            old_value={k: v[0] for k, v in changes_in_attr.items()},
                            new_value={k: v[1] for k, v in changes_in_attr.items()},
                            description=f"Modified properties of attribute '{attr_name}' in group '{group_name}'"
                        )
                    )
                
                # Check for changes in required status
                if old_attr.required != new_attr.required:
                    changes.append(
                        MetamodelChange(
                            change_type=ChangeType.CHANGE_REQUIREMENT,
                            target_path=f"{group_name}/{attr_name}",
                            old_value=old_attr.required,
                            new_value=new_attr.required,
                            description=(
                                f"Changed attribute '{attr_name}' in group '{group_name}' to "
                                f"{'required' if new_attr.required else 'optional'}"
                            )
                        )
                    )
        
        return changes


class MigrationPlanner:
    """Plans migrations for metamodel changes."""
    
    def generate_migration_plan(
        self, changes: List[MetamodelChange]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate a migration plan for a set of metamodel changes.
        
        Args:
            changes: List of metamodel changes
            
        Returns:
            Dictionary containing migration steps categorized by impact level
        """
        migration_plan = {
            "high_impact": [],
            "medium_impact": [],
            "low_impact": []
        }
        
        for change in changes:
            if change.change_type == ChangeType.ADD_ATTRIBUTE and change.new_value.get("required", False):
                # Adding a required attribute is high impact
                migration_plan["high_impact"].append({
                    "change": change.model_dump(),
                    "action": "Add required attribute and populate existing data",
                    "steps": [
                        "Define default value for existing data",
                        "Create migration script to populate attribute",
                        "Update all data ingestion processes",
                        "Notify data product owners"
                    ]
                })
            elif change.change_type == ChangeType.CHANGE_REQUIREMENT and change.new_value:
                # Making an attribute required is high impact
                migration_plan["high_impact"].append({
                    "change": change.model_dump(),
                    "action": "Make attribute required and populate existing data",
                    "steps": [
                        "Define default value for null/missing values",
                        "Create migration script to populate attribute",
                        "Update validation rules",
                        "Notify data product owners"
                    ]
                })
            elif change.change_type == ChangeType.REMOVE_ATTRIBUTE:
                # Removing an attribute is medium impact
                migration_plan["medium_impact"].append({
                    "change": change.model_dump(),
                    "action": "Remove attribute from schema and data",
                    "steps": [
                        "Update schema definition",
                        "Create migration script to remove attribute from existing data",
                        "Update all dependent applications",
                        "Notify data product owners"
                    ]
                })
            elif change.change_type == ChangeType.MODIFY_ATTRIBUTE:
                # Changing attribute properties is medium impact
                migration_plan["medium_impact"].append({
                    "change": change.model_dump(),
                    "action": "Modify attribute properties",
                    "steps": [
                        "Update schema definition",
                        "Update validation rules",
                        "Create migration script for type conversions if needed",
                        "Notify data product owners"
                    ]
                })
            elif change.change_type == ChangeType.ADD_GROUP:
                # Adding a group is medium impact
                migration_plan["medium_impact"].append({
                    "change": change.model_dump(),
                    "action": "Add new group to schema",
                    "steps": [
                        "Update schema definition",
                        "Create database migration if needed",
                        "Update validation rules",
                        "Notify data product owners"
                    ]
                })
            elif change.change_type == ChangeType.REMOVE_GROUP:
                # Removing a group is high impact
                migration_plan["high_impact"].append({
                    "change": change.model_dump(),
                    "action": "Remove group from schema and data",
                    "steps": [
                        "Archive existing data",
                        "Update schema definition",
                        "Create database migration",
                        "Update all dependent applications",
                        "Notify data product owners"
                    ]
                })
            elif change.change_type == ChangeType.CHANGE_REQUIREMENT and not change.new_value:
                # Making an attribute optional is low impact
                migration_plan["low_impact"].append({
                    "change": change.model_dump(),
                    "action": "Make attribute optional",
                    "steps": [
                        "Update schema definition",
                        "Update validation rules",
                        "Notify data product owners"
                    ]
                })
            elif change.change_type == ChangeType.ADD_ATTRIBUTE and not change.new_value.get("required", False):
                # Adding an optional attribute is low impact
                migration_plan["low_impact"].append({
                    "change": change.model_dump(),
                    "action": "Add optional attribute",
                    "steps": [
                        "Update schema definition",
                        "Update validation rules",
                        "Notify data product owners"
                    ]
                })
            elif change.change_type == ChangeType.MODIFY_GROUP:
                # Modifying group properties is low impact
                migration_plan["low_impact"].append({
                    "change": change.model_dump(),
                    "action": "Modify group properties",
                    "steps": [
                        "Update schema definition",
                        "Update documentation",
                        "Notify data product owners"
                    ]
                })
        
        return migration_plan