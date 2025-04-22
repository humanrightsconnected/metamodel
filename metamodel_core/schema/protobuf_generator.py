"""
Generates Protocol Buffer schema files from metamodel definitions.
"""
import os
from typing import Dict, List, Optional, Set, Tuple

from metamodel_core.models.metamodel import AttributeType, Metamodel, MetamodelAttribute


class ProtobufGenerator:
    """Generates Protocol Buffer schema files from metamodel definitions."""
    
    def __init__(self, output_dir: str = "generated"):
        """
        Initialize the generator.
        
        Args:
            output_dir: Directory where generated files will be saved
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def _type_to_protobuf(self, attr_type: AttributeType) -> str:
        """
        Convert a metamodel attribute type to its Protocol Buffer equivalent.
        
        Args:
            attr_type: The metamodel attribute type
            
        Returns:
            The corresponding Protocol Buffer type
        """
        type_mapping = {
            AttributeType.STRING: "string",
            AttributeType.BOOLEAN: "bool",
            AttributeType.INTEGER: "int32",
            AttributeType.NUMBER: "double",
            AttributeType.ARRAY: "repeated string",  # Default to string array
            AttributeType.OBJECT: "bytes",  # JSON serialized as bytes
            AttributeType.DATETIME: "google.protobuf.Timestamp"
        }
        return type_mapping.get(attr_type, "string")
    
    def _format_field_name(self, name: str) -> str:
        """
        Format an attribute name to a valid Protocol Buffer field name.
        
        Args:
            name: The original attribute name
            
        Returns:
            A Protocol Buffer compatible field name
        """
        # Replace spaces with underscores and convert to snake_case
        import re
        s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1)
        return re.sub(r'[^a-zA-Z0-9_]', '_', s2).lower()
    
    def _get_imports(self, metamodel: Metamodel) -> Set[str]:
        """
        Determine the necessary Protocol Buffer imports based on the metamodel.
        
        Args:
            metamodel: The metamodel to analyze
            
        Returns:
            Set of import statements needed
        """
        imports = set()
        
        # Check if any datetime fields are present
        for group in metamodel.groups:
            for attr in group.attributes:
                if attr.type == AttributeType.DATETIME:
                    imports.add('import "google/protobuf/timestamp.proto";')
        
        return imports
    
    def generate_schema(self, metamodel: Metamodel, filename: str) -> str:
        """
        Generate a Protocol Buffer schema file from a metamodel.
        
        Args:
            metamodel: The metamodel to convert
            filename: The filename for the generated schema (without extension)
            
        Returns:
            Path to the generated .proto file
        """
        # Prepare the output
        proto_content = [
            'syntax = "proto3";',
            f'package {filename};',
            ''
        ]
        
        # Add necessary imports
        imports = self._get_imports(metamodel)
        for import_statement in sorted(imports):
            proto_content.append(import_statement)
        
        if imports:
            proto_content.append('')
        
        # Add file-level documentation
        proto_content.append(f'// Generated from metamodel "{metamodel.name}" version {metamodel.version}')
        proto_content.append(f'// {metamodel.description}')
        proto_content.append('')
        
        # Generate message types for each group
        group_messages = []
        
        # First, create the main metadata message that will contain all groups
        proto_content.append('// Main metadata message containing all groups')
        proto_content.append('message Metadata {')
        
        field_index = 1
        for group in metamodel.groups:
            group_name = self._format_field_name(group.name)
            message_name = f"{group_name.title().replace('_', '')}Group"
            proto_content.append(f'  // {group.description}')
            proto_content.append(f'  {message_name} {group_name} = {field_index};')
            field_index += 1
            
            # Prepare the group message
            group_message = []
            group_message.append(f'// {group.description}')
            group_message.append(f'message {message_name} {{')
            
            # Add fields for each attribute in the group
            attr_index = 1
            for attr in group.attributes:
                proto_type = self._type_to_protobuf(attr.type)
                field_name = self._format_field_name(attr.name)
                
                # Handle array type specially
                if attr.type == AttributeType.ARRAY:
                    proto_type = "string"  # Base type
                    proto_type = f"repeated {proto_type}"
                
                # Add comment for the attribute
                group_message.append(f'  // {attr.description}')
                
                # For enum types, create an enum definition
                if attr.enum:
                    enum_name = f"{field_name.title().replace('_', '')}Enum"
                    group_message.append(f'  enum {enum_name} {{')
                    group_message.append(f'    {enum_name.upper()}_UNSPECIFIED = 0;')
                    
                    for i, enum_value in enumerate(attr.enum, 1):
                        enum_field = self._format_field_name(enum_value).upper()
                        group_message.append(f'    {enum_name.upper()}_{enum_field} = {i};')
                    
                    group_message.append('  }')
                    proto_type = enum_name
                
                # Add the field
                group_message.append(f'  {proto_type} {field_name} = {attr_index};')
                attr_index += 1
            
            group_message.append('}')
            group_message.append('')
            group_messages.extend(group_message)
        
        proto_content.append('}')
        proto_content.append('')
        
        # Add all group messages
        proto_content.extend(group_messages)
        
        # Write the schema to disk
        output_path = os.path.join(self.output_dir, f"{filename}.proto")
        with open(output_path, "w") as f:
            f.write("\n".join(proto_content))
        
        return output_path
    
    def generate_descriptor_set(self, proto_file: str, output_file: Optional[str] = None) -> str:
        """
        Generate a Protocol Buffer FileDescriptorSet from a .proto file.
        
        Args:
            proto_file: Path to the .proto file
            output_file: Path for the output file (defaults to proto_file with .pb extension)
            
        Returns:
            Path to the generated descriptor set
        """
        import subprocess
        
        if output_file is None:
            output_file = os.path.splitext(proto_file)[0] + ".pb"
        
        # Run protoc to generate descriptor set
        cmd = [
            "protoc",
            f"--descriptor_set_out={output_file}",
            "--include_imports",
            proto_file
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to generate descriptor set: {e.stderr.decode()}")
        
        return output_file