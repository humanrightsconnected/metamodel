"""
Test suite for the Protocol Buffer schema generator.
"""
import os
import re
import pytest

from metamodel_core.models import get_core_metamodel
from metamodel_core.schema.protobuf_generator import ProtobufGenerator


class TestProtobufGenerator:
    """Tests for the ProtobufGenerator class."""
    
    def test_type_to_protobuf_mapping(self):
        """Test the mapping of metamodel types to Protocol Buffer types."""
        generator = ProtobufGenerator()
        
        # Test private method directly
        assert generator._type_to_protobuf("string") == "string"
        assert generator._type_to_protobuf("boolean") == "bool"
        assert generator._type_to_protobuf("integer") == "int32"
        assert generator._type_to_protobuf("number") == "double"
        assert generator._type_to_protobuf("array") == "repeated string"
        assert generator._type_to_protobuf("object") == "bytes"
        assert generator._type_to_protobuf("datetime") == "google.protobuf.Timestamp"
        
        # Test with an unknown type
        assert generator._type_to_protobuf("unknown") == "string"  # Default to string
    
    def test_format_field_name(self):
        """Test the formatting of field names for Protocol Buffer compatibility."""
        generator = ProtobufGenerator()
        
        # Test simple names
        assert generator._format_field_name("name") == "name"
        assert generator._format_field_name("first_name") == "first_name"
        
        # Test camel case conversion
        assert generator._format_field_name("firstName") == "first_name"
        assert generator._format_field_name("FirstName") == "first_name"
        
        # Test space replacement
        assert generator._format_field_name("First Name") == "first_name"
        
        # Test special character replacement
        assert generator._format_field_name("First-Name") == "first_name"
        assert generator._format_field_name("First.Name") == "first_name"
        assert generator._format_field_name("First@Name") == "first_name"
        
        # Test complex cases
        assert generator._format_field_name("User's First Name") == "user_s_first_name"
        assert generator._format_field_name("CamelCase With Spaces") == "camel_case_with_spaces"
    
    def test_generate_schema_output_file(self, core_metamodel, output_dir):
        """Test that generate_schema creates the expected output file."""
        generator = ProtobufGenerator(output_dir)
        
        # Generate the schema
        output_path = generator.generate_schema(core_metamodel, "test_schema")
        
        # Check that the file was created
        assert os.path.exists(output_path)
        assert output_path == os.path.join(output_dir, "test_schema.proto")
    
    def test_generate_schema_content(self, sample_metamodel, output_dir):
        """Test that generate_schema produces the expected content."""
        generator = ProtobufGenerator(output_dir)
        
        # Generate the schema
        output_path = generator.generate_schema(sample_metamodel, "test_schema")
        
        # Read the generated file
        with open(output_path, "r") as f:
            content = f.read()
        
        # Check the content
        assert 'syntax = "proto3";' in content
        assert 'package test_schema;' in content
        
        # Check that the main message is present
        assert 'message Metadata {' in content
        
        # Check that all groups are present
        for group in sample_metamodel.groups:
            expected_message_name = f"{group.name.title().replace(' ', '')}Group"
            assert f"message {expected_message_name} {{" in content
            
            # Check that the group field is in the main message
            group_field_name = re.sub(r'[^a-zA-Z0-9_]', '_', group.name).lower()
            assert f"  {expected_message_name} {group_field_name} = " in content
            
            # Check that all attributes are present
            for attr in group.attributes:
                field_name = re.sub(r'[^a-zA-Z0-9_]', '_', attr.name).lower()
                if attr.type == "array":
                    assert f"  repeated string {field_name} = " in content
                elif attr.type == "datetime":
                    assert f"  google.protobuf.Timestamp {field_name} = " in content
                else:
                    proto_type = generator._type_to_protobuf(attr.type)
                    assert f"  {proto_type} {field_name} = " in content
    
    def test_generate_schema_full_metamodel(self, core_metamodel, output_dir):
        """Test generating a schema from the full core metamodel."""
        generator = ProtobufGenerator(output_dir)
        
        # Generate the schema
        output_path = generator.generate_schema(core_metamodel, "core_metamodel")
        
        # Check that the file was created
        assert os.path.exists(output_path)
        
        # Read the generated file
        with open(output_path, "r") as f:
            content = f.read()
        
        # Basic content checks
        assert 'syntax = "proto3";' in content
        assert 'package core_metamodel;' in content
        assert f'// Generated from metamodel "{core_metamodel.name}"' in content
        assert 'message Metadata {' in content
        
        # Check that datetime import is included
        assert 'import "google/protobuf/timestamp.proto";' in content
        
        # Check that all groups are present
        for group in core_metamodel.groups:
            expected_message_name = f"{group.name.title().replace(' ', '')}Group"
            assert f"message {expected_message_name} {{" in content
            
            # Check that the group description is included as a comment
            assert f"  // {group.description}" in content
    
    def test_enum_generation(self, output_dir):
        """Test that enums are properly generated for attributes with enum values."""
        from metamodel_core.models.metamodel import Metamodel, MetamodelGroup, MetamodelAttribute
        
        # Create a test metamodel with an enum attribute
        test_metamodel = Metamodel(
            name="Enum Test Metamodel",
            version="1.0",
            description="A test metamodel with enum attributes",
            groups=[
                MetamodelGroup(
                    name="Test Group",
                    description="A test group",
                    attributes=[
                        MetamodelAttribute(
                            name="Status",
                            description="Status of the item",
                            type="string",
                            required=True,
                            enum=["Active", "Inactive", "Pending"]
                        )
                    ]
                )
            ]
        )
        
        generator = ProtobufGenerator(output_dir)
        
        # Generate the schema
        output_path = generator.generate_schema(test_metamodel, "enum_test")
        
        # Read the generated file
        with open(output_path, "r") as f:
            content = f.read()
        
        # Check for enum definition
        assert "enum StatusEnum {" in content
        assert "STATUS_ENUM_UNSPECIFIED = 0;" in content
        assert "STATUS_ENUM_ACTIVE = 1;" in content
        assert "STATUS_ENUM_INACTIVE = 2;" in content
        assert "STATUS_ENUM_PENDING = 3;" in content
        
        # Check that the field uses the enum type
        assert "  StatusEnum status = 1;" in content