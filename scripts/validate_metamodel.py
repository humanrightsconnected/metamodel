#!/usr/bin/env python
"""
Script to validate a metamodel JSON file against the core metamodel structure.
"""
import argparse
import json
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metamodel_core.models import get_core_metamodel, Metamodel
from metamodel_core.models.validators import MetamodelValidator, ChangeAnalyzer


def main():
    """Validate a metamodel JSON file against the core metamodel structure."""
    parser = argparse.ArgumentParser(
        description="Validate a metamodel JSON file against the core metamodel structure."
    )
    parser.add_argument(
        "metamodel_file", 
        help="Path to the metamodel JSON file to validate"
    )
    parser.add_argument(
        "--detect-changes", 
        "-c", 
        action="store_true",
        help="Detect changes between the input metamodel and the core metamodel"
    )
    parser.add_argument(
        "--check-compatibility", 
        "-b", 
        action="store_true",
        help="Check backward compatibility with the core metamodel"
    )
    args = parser.parse_args()
    
    try:
        # Load the input metamodel
        print(f"Loading metamodel from {args.metamodel_file}...")
        with open(args.metamodel_file, "r") as f:
            input_data = json.load(f)
        input_metamodel = Metamodel.from_dict(input_data)
        print(f"Loaded metamodel version {input_metamodel.version}")
        
        # Load the core metamodel
        print("Loading core metamodel...")
        core_metamodel = get_core_metamodel()
        print(f"Loaded core metamodel version {core_metamodel.version}")
        
        # Create a validator
        validator = MetamodelValidator()
        
        # Validate the input metamodel
        print("Validating metamodel structure...")
        is_valid, errors = validator.validate_metamodel(input_metamodel)
        
        if is_valid:
            print("Metamodel structure is valid.")
        else:
            print("Metamodel structure is invalid:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return 1
        
        # Check backward compatibility if requested
        if args.check_compatibility:
            print("Checking backward compatibility...")
            is_compatible, compatibility_errors = validator.validate_backward_compatibility(
                core_metamodel, input_metamodel
            )
            
            if is_compatible:
                print("Metamodel is backward compatible with the core metamodel.")
            else:
                print("Metamodel is not backward compatible with the core metamodel:", file=sys.stderr)
                for error in compatibility_errors:
                    print(f"  - {error}", file=sys.stderr)
                return 1
        
        # Detect changes if requested
        if args.detect_changes:
            print("Detecting changes...")
            analyzer = ChangeAnalyzer()
            changes = analyzer.detect_changes(core_metamodel, input_metamodel)
            
            if changes:
                print(f"Detected {len(changes)} changes:")
                for i, change in enumerate(changes, 1):
                    print(f"  {i}. {change.change_type}: {change.target_path}")
                    print(f"     {change.description}")
            else:
                print("No changes detected.")
        
        print("Validation completed successfully.")
        return 0
    
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())