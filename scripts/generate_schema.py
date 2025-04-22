#!/usr/bin/env python
"""
Script to generate Protocol Buffer schema files from the core metamodel.
"""
import argparse
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metamodel_core.models import get_core_metamodel
from metamodel_core.schema.protobuf_generator import ProtobufGenerator


def main():
    """Generate Protocol Buffer schema files from the core metamodel."""
    parser = argparse.ArgumentParser(
        description="Generate Protocol Buffer schema files from the core metamodel."
    )
    parser.add_argument(
        "--output-dir", 
        "-o", 
        default="generated",
        help="Directory where generated files will be saved (default: generated)"
    )
    parser.add_argument(
        "--filename", 
        "-f", 
        default="metamodel",
        help="Base filename for the generated schema files (default: metamodel)"
    )
    parser.add_argument(
        "--descriptor-set", 
        "-d", 
        action="store_true",
        help="Generate a Protocol Buffer FileDescriptorSet (.pb) file"
    )
    args = parser.parse_args()
    
    # Create the output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Load the core metamodel
        print("Loading core metamodel...")
        metamodel = get_core_metamodel()
        print(f"Loaded core metamodel version {metamodel.version}")
        
        # Create a Protocol Buffer generator
        generator = ProtobufGenerator(args.output_dir)
        
        # Generate the schema
        print(f"Generating Protocol Buffer schema in {args.output_dir}...")
        proto_file = generator.generate_schema(metamodel, args.filename)
        print(f"Generated schema file: {proto_file}")
        
        # Generate a descriptor set if requested
        if args.descriptor_set:
            print("Generating Protocol Buffer descriptor set...")
            try:
                descriptor_file = generator.generate_descriptor_set(proto_file)
                print(f"Generated descriptor set: {descriptor_file}")
            except RuntimeError as e:
                print(f"Failed to generate descriptor set: {e}", file=sys.stderr)
                print("Make sure protoc (Protocol Buffer Compiler) is installed and in your PATH.", file=sys.stderr)
                return 1
        
        print("Done!")
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())