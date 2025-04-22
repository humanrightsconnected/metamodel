"""
Models for the metamodel-core package.
"""
import json
import os
from typing import Optional

from .metamodel import Metamodel

# Path to the core metamodel JSON file
CORE_METAMODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    "data", 
    "core_metamodel.json"
)


def get_core_metamodel() -> Metamodel:
    """
    Load and return the core metamodel from the package's data directory.
    
    Returns:
        The core metamodel as a Metamodel instance
    
    Raises:
        FileNotFoundError: If the core metamodel JSON file is not found
        ValueError: If the core metamodel JSON is invalid
    """
    try:
        with open(CORE_METAMODEL_PATH, "r") as f:
            data = json.load(f)
        return Metamodel.from_dict(data)
    except FileNotFoundError:
        raise FileNotFoundError(f"Core metamodel JSON file not found at {CORE_METAMODEL_PATH}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in core metamodel file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load core metamodel: {e}")