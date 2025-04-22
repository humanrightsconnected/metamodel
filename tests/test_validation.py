"""
Test suite for metamodel validation.
"""
import json
import os
import pytest
from copy import deepcopy

from metamodel_core.models import get_core_metamodel, Metamodel
from metamodel_core.models.metamodel import MetamodelAttribute, MetamodelGroup
from metamodel_core.models.validators import MetamodelValidator, ChangeAnalyzer


class TestMetamodelValidator:
    def test_validate_enum_attribute_type(self):
        """Test validation of an attribute with enum values that is not a string type."""
        # Get the core metamodel
        metamodel = get_core_metamodel()
        
        # Find a string attribute to modify
        test_group = None
        test_attr = None
        
        for group in metamodel.groups:
            for attr in group.attributes:
                if attr.type == "string" and not attr.enum:
                    test_group = group
                    test_attr = attr
                    break
            if test_attr:
                break
        
        assert test_attr is not None, "Could not find a string attribute to modify"
        
        # Create a copy with an invalid enum attribute
        invalid_metamodel = deepcopy(metamodel)
        invalid_group = next(g for g in invalid_metamodel.groups if g.name == test_group.name)
        invalid_attr = next(a for a in invalid_group.attributes if a.name == test_attr.name)
        
        # Change the type to boolean but add enum values
        invalid_attr.type = "boolean"
        invalid_attr.enum = ["True", "False"]
        
        validator = MetamodelValidator()
        
        # Validate the metamodel
        is_valid, errors = validator.validate_metamodel(invalid_metamodel)
        
        # Check the result
        assert not is_valid, "Metamodel with enum values for non-string attribute should be invalid"
        assert errors, "There should be validation errors"
        assert any("has enum values but is not of type string" in error for error in errors), \
            "Error should mention invalid enum usage"
    
    def test_backward_compatibility_required_attribute_removal(self):
        """Test backward compatibility validation when a required attribute is removed."""
        # Get the core metamodel
        metamodel = get_core_metamodel()
        
        # Create a modified version with a required attribute removed
        modified_metamodel = deepcopy(metamodel)
        
        # Find a group with required attributes
        test_group = None
        for group in modified_metamodel.groups:
            if any(attr.required for attr in group.attributes):
                test_group = group
                break
        
        assert test_group is not None, "Could not find a group with required attributes"
        
        # Find a required attribute to remove
        required_attr = next(attr for attr in test_group.attributes if attr.required)
        
        # Remove the attribute
        test_group.attributes = [attr for attr in test_group.attributes if attr.name != required_attr.name]
        
        validator = MetamodelValidator()
        
        # Validate backward compatibility
        is_compatible, errors = validator.validate_backward_compatibility(metamodel, modified_metamodel)
        
        # Check the result
        assert not is_compatible, "Removing a required attribute should break backward compatibility"
        assert errors, "There should be compatibility errors"
        assert any(f"Required attribute '{required_attr.name}' was removed" in error for error in errors), \
            "Error should mention the removed required attribute"
    
    def test_backward_compatibility_required_to_optional(self):
        """Test backward compatibility validation when a required attribute is made optional."""
        # Get the core metamodel
        metamodel = get_core_metamodel()
        
        # Create a modified version with a required attribute made optional
        modified_metamodel = deepcopy(metamodel)
        
        # Find a group with required attributes
        test_group = None
        test_attr = None
        
        for group in modified_metamodel.groups:
            for attr in group.attributes:
                if attr.required:
                    test_group = group
                    test_attr = attr
                    break
            if test_attr:
                break
        
        assert test_attr is not None, "Could not find a required attribute to modify"
        
        # Make the attribute optional
        test_attr.required = False
        
        validator = MetamodelValidator()
        
        # Validate backward compatibility
        is_compatible, errors = validator.validate_backward_compatibility(metamodel, modified_metamodel)
        
        # Check the result
        assert not is_compatible, "Making a required attribute optional should break backward compatibility"
        assert errors, "There should be compatibility errors"
        assert any(f"Required attribute '{test_attr.name}' in group '{test_group.name}' was made optional" in error for error in errors), \
            "Error should mention the attribute made optional"
    
    def test_backward_compatibility_type_change(self):
        """Test backward compatibility validation when an attribute type is changed."""
        # Get the core metamodel
        metamodel = get_core_metamodel()
        
        # Create a modified version with an attribute type changed
        modified_metamodel = deepcopy(metamodel)
        
        # Find a string attribute to change
        test_group = None
        test_attr = None
        
        for group in modified_metamodel.groups:
            for attr in group.attributes:
                if attr.type == "string":
                    test_group = group
                    test_attr = attr
                    break
            if test_attr:
                break
        
        assert test_attr is not None, "Could not find a string attribute to modify"
        
        # Change the type
        original_type = test_attr.type
        test_attr.type = "boolean"
        
        validator = MetamodelValidator()
        
        # Validate backward compatibility
        is_compatible, errors = validator.validate_backward_compatibility(metamodel, modified_metamodel)
        
        # Check the result
        assert not is_compatible, "Changing an attribute type should break backward compatibility"
        assert errors, "There should be compatibility errors"
        assert any(f"Type of attribute '{test_attr.name}' in group '{test_group.name}' changed from '{original_type}' to '{test_attr.type}'" in error for error in errors), \
            "Error should mention the type change"
    """Tests for the MetamodelValidator class."""
    
    def test_validate_valid_metamodel(self):
        """Test validation of a valid metamodel."""
        # Get the core metamodel (should be valid)
        metamodel = get_core_metamodel()
        validator = MetamodelValidator()
        
        # Validate the metamodel
        is_valid, errors = validator.validate_metamodel(metamodel)
        
        # Check the result
        assert is_valid, f"Core metamodel should be valid, but got errors: {errors}"
        assert not errors, "There should be no validation errors"
    
    def test_validate_duplicate_group_names(self):
        """Test validation of a metamodel with duplicate group names."""
        # Get the core metamodel
        metamodel = get_core_metamodel()
        
        # Create a copy with a duplicate group name
        duplicate_metamodel = deepcopy(metamodel)
        first_group = duplicate_metamodel.groups[0]
        duplicate_group = deepcopy(first_group)
        duplicate_metamodel.groups.append(duplicate_group)
        
        validator = MetamodelValidator()
        
        # Validate the metamodel
        is_valid, errors = validator.validate_metamodel(duplicate_metamodel)
        
        # Check the result
        assert not is_valid, "Metamodel with duplicate group names should be invalid"
        assert errors, "There should be validation errors"
        assert any("Duplicate group names" in error for error in errors), "Error should mention duplicate group names"
    
    def test_validate_duplicate_attribute_names(self):
        """Test validation of a metamodel with duplicate attribute names across groups."""
        # Get the core metamodel
        metamodel = get_core_metamodel()
        
        # Create a copy with a duplicate attribute name across groups
        duplicate_metamodel = deepcopy(metamodel)
        first_group = duplicate_metamodel.groups[0]
        second_group = duplicate_metamodel.groups[1]
        first_attr = first_group.attributes[0]
        
        # Add a copy of the first attribute to the second group
        duplicate_attr = deepcopy(first_attr)
        second_group.attributes.append(duplicate_attr)
        
        validator = MetamodelValidator()
        
        # Validate the metamodel
        is_valid, errors = validator.validate_metamodel(duplicate_metamodel)
        
        # Check the result
        assert not is_valid, "Metamodel with duplicate attribute names should be invalid"
        assert errors, "There should be validation errors"
        assert any(f"Attribute '{first_attr.name}' is duplicated" in error for error in errors), \
            "Error should mention duplicated attribute"