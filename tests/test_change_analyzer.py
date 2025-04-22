"""
Test suite for the ChangeAnalyzer class.
"""
import pytest
from copy import deepcopy

from metamodel_core.models import get_core_metamodel
from metamodel_core.models.metamodel import MetamodelAttribute, MetamodelGroup, ChangeType
from metamodel_core.models.validators import ChangeAnalyzer


class TestChangeAnalyzer:
    """Tests for the ChangeAnalyzer class."""
    
    def test_detect_add_group(self):
        """Test detection of an added group."""
        # Get the core metamodel
        old_metamodel = get_core_metamodel()
        
        # Create a copy with a new group
        new_metamodel = deepcopy(old_metamodel)
        new_group = MetamodelGroup(
            name="Test Group", 
            description="A test group for unit testing",
            attributes=[
                MetamodelAttribute(
                    name="Test Attribute",
                    description="A test attribute",
                    type="string",
                    required=False
                )
            ]
        )
        new_metamodel.groups.append(new_group)
        
        analyzer = ChangeAnalyzer()
        
        # Detect changes
        changes = analyzer.detect_changes(old_metamodel, new_metamodel)
        
        # Check the result
        assert changes, "Changes should be detected"
        add_group_changes = [c for c in changes if c.change_type == ChangeType.ADD_GROUP]
        assert add_group_changes, "Should detect addition of a group"
        assert add_group_changes[0].target_path == "Test Group", "Target path should be the group name"
        assert add_group_changes[0].new_value is not None, "New value should be provided"
        assert add_group_changes[0].old_value is None, "Old value should not be provided"
    
    def test_detect_remove_group(self):
        """Test detection of a removed group."""
        # Get the core metamodel
        old_metamodel = get_core_metamodel()
        
        # Create a copy with a group removed
        new_metamodel = deepcopy(old_metamodel)
        removed_group = new_metamodel.groups[0]
        new_metamodel.groups = new_metamodel.groups[1:]
        
        analyzer = ChangeAnalyzer()
        
        # Detect changes
        changes = analyzer.detect_changes(old_metamodel, new_metamodel)
        
        # Check the result
        assert changes, "Changes should be detected"
        remove_group_changes = [c for c in changes if c.change_type == ChangeType.REMOVE_GROUP]
        assert remove_group_changes, "Should detect removal of a group"
        assert remove_group_changes[0].target_path == removed_group.name, \
            "Target path should be the removed group name"
        assert remove_group_changes[0].old_value is not None, "Old value should be provided"
        assert remove_group_changes[0].new_value is None, "New value should not be provided"
    
    def test_detect_modify_group_description(self):
        """Test detection of a modified group description."""
        # Get the core metamodel
        old_metamodel = get_core_metamodel()
        
        # Create a copy with a modified group description
        new_metamodel = deepcopy(old_metamodel)
        modified_group = new_metamodel.groups[0]
        old_description = modified_group.description
        modified_group.description = "Modified description for testing"
        
        analyzer = ChangeAnalyzer()
        
        # Detect changes
        changes = analyzer.detect_changes(old_metamodel, new_metamodel)
        
        # Check the result
        assert changes, "Changes should be detected"
        modify_group_changes = [c for c in changes if c.change_type == ChangeType.MODIFY_GROUP]
        assert modify_group_changes, "Should detect modification of a group"
        assert modify_group_changes[0].target_path == modified_group.name, \
            "Target path should be the modified group name"
        assert modify_group_changes[0].old_value == {"description": old_description}, \
            "Old value should contain the original description"
        assert modify_group_changes[0].new_value == {"description": modified_group.description}, \
            "New value should contain the modified description"
    
    def test_detect_add_attribute(self):
        """Test detection of an added attribute."""
        # Get the core metamodel
        old_metamodel = get_core_metamodel()
        
        # Create a copy with a new attribute added to a group
        new_metamodel = deepcopy(old_metamodel)
        target_group = new_metamodel.groups[0]
        new_attr = MetamodelAttribute(
            name="New Test Attribute",
            description="A new attribute for testing",
            type="string",
            required=False
        )
        target_group.attributes.append(new_attr)
        
        analyzer = ChangeAnalyzer()
        
        # Detect changes
        changes = analyzer.detect_changes(old_metamodel, new_metamodel)
        
        # Check the result
        assert changes, "Changes should be detected"
        add_attr_changes = [c for c in changes if c.change_type == ChangeType.ADD_ATTRIBUTE]
        assert add_attr_changes, "Should detect addition of an attribute"
        assert add_attr_changes[0].target_path == f"{target_group.name}/{new_attr.name}", \
            "Target path should be 'group_name/attribute_name'"
        assert add_attr_changes[0].new_value is not None, "New value should be provided"
        assert add_attr_changes[0].old_value is None, "Old value should not be provided"
    
    def test_detect_remove_attribute(self):
        """Test detection of a removed attribute."""
        # Get the core metamodel
        old_metamodel = get_core_metamodel()
        
        # Create a copy with an attribute removed
        new_metamodel = deepcopy(old_metamodel)
        target_group = new_metamodel.groups[0]
        removed_attr = target_group.attributes[0]
        target_group.attributes = target_group.attributes[1:]
        
        analyzer = ChangeAnalyzer()
        
        # Detect changes
        changes = analyzer.detect_changes(old_metamodel, new_metamodel)
        
        # Check the result
        assert changes, "Changes should be detected"
        remove_attr_changes = [c for c in changes if c.change_type == ChangeType.REMOVE_ATTRIBUTE]
        assert remove_attr_changes, "Should detect removal of an attribute"
        assert remove_attr_changes[0].target_path == f"{target_group.name}/{removed_attr.name}", \
            "Target path should be 'group_name/attribute_name'"
        assert remove_attr_changes[0].old_value is not None, "Old value should be provided"
        assert remove_attr_changes[0].new_value is None, "New value should not be provided"
    
    def test_detect_modify_attribute(self):
        """Test detection of a modified attribute description."""
        # Get the core metamodel
        old_metamodel = get_core_metamodel()
        
        # Create a copy with a modified attribute description
        new_metamodel = deepcopy(old_metamodel)
        target_group = new_metamodel.groups[0]
        modified_attr = target_group.attributes[0]
        old_description = modified_attr.description
        modified_attr.description = "Modified attribute description for testing"
        
        analyzer = ChangeAnalyzer()
        
        # Detect changes
        changes = analyzer.detect_changes(old_metamodel, new_metamodel)
        
        # Check the result
        assert changes, "Changes should be detected"
        modify_attr_changes = [c for c in changes if c.change_type == ChangeType.MODIFY_ATTRIBUTE]
        assert modify_attr_changes, "Should detect modification of an attribute"
        assert modify_attr_changes[0].target_path == f"{target_group.name}/{modified_attr.name}", \
            "Target path should be 'group_name/attribute_name'"
        assert modify_attr_changes[0].old_value == {"description": old_description}, \
            "Old value should contain the original description"
        assert modify_attr_changes[0].new_value == {"description": modified_attr.description}, \
            "New value should contain the modified description"
    
    def test_detect_change_requirement(self):
        """Test detection of a changed attribute requirement."""
        # Get the core metamodel
        old_metamodel = get_core_metamodel()
        
        # Create a copy with a changed attribute requirement
        new_metamodel = deepcopy(old_metamodel)
        
        # Find an optional attribute to make required
        target_group = None
        target_attr = None
        
        for group in new_metamodel.groups:
            for attr in group.attributes:
                if not attr.required:
                    target_group = group
                    target_attr = attr
                    break
            if target_attr:
                break
        
        assert target_attr is not None, "Could not find an optional attribute to modify"
        
        # Change the requirement
        target_attr.required = True
        
        analyzer = ChangeAnalyzer()
        
        # Detect changes
        changes = analyzer.detect_changes(old_metamodel, new_metamodel)
        
        # Check the result
        assert changes, "Changes should be detected"
        req_changes = [c for c in changes if c.change_type == ChangeType.CHANGE_REQUIREMENT]
        assert req_changes, "Should detect change in attribute requirement"
        assert req_changes[0].target_path == f"{target_group.name}/{target_attr.name}", \
            "Target path should be 'group_name/attribute_name'"
        assert req_changes[0].old_value is False, "Old value should be False"
        assert req_changes[0].new_value is True, "New value should be True"