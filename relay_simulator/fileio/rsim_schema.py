"""
.rsim File Format Schema Definition

This module defines the JSON schema for .rsim (Relay Simulator) files.
The schema uses a hierarchical structure: Document → Pages → Components/Wires → Pins/Tabs

Schema Version: 1.0
"""

from typing import Any, Dict, List, Optional
from enum import Enum


class SchemaVersion:
    """Version information for .rsim file format"""
    MAJOR = 1
    MINOR = 0
    PATCH = 0
    
    @classmethod
    def to_string(cls) -> str:
        """Get version as string (e.g., '1.0.0')"""
        return f"{cls.MAJOR}.{cls.MINOR}.{cls.PATCH}"
    
    @classmethod
    def from_string(cls, version_str: str) -> tuple[int, int, int]:
        """Parse version string to tuple (major, minor, patch)"""
        parts = version_str.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version string: {version_str}")
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    
    @classmethod
    def is_compatible(cls, file_version: str) -> bool:
        """Check if file version is compatible with current schema"""
        major, minor, patch = cls.from_string(file_version)
        
        # Major version must match
        if major != cls.MAJOR:
            return False
        
        # Minor version can be older or same (forward compatible within major)
        if minor > cls.MINOR:
            return False
        
        return True


class FieldType(Enum):
    """Data types for schema fields"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    ENUM = "enum"
    UUID = "uuid"  # 8-character UUID string


# Schema definition as nested dictionaries
# Structure: {field_name: {type, required, description, default, validation}}

TAB_SCHEMA = {
    "tab_id": {
        "type": FieldType.UUID,
        "required": True,
        "description": "Unique 8-character identifier for this tab"
    },
    "position": {
        "type": FieldType.OBJECT,
        "required": True,
        "description": "Relative position of tab on component",
        "fields": {
            "x": {"type": FieldType.FLOAT, "required": True},
            "y": {"type": FieldType.FLOAT, "required": True}
        }
    },
    "state": {
        "type": FieldType.ENUM,
        "required": False,
        "description": "Current state of tab (runtime only, not saved)",
        "values": ["FLOAT", "HIGH"],
        "default": "FLOAT"
    }
}

PIN_SCHEMA = {
    "pin_id": {
        "type": FieldType.UUID,
        "required": True,
        "description": "Unique 8-character identifier for this pin"
    },
    "tabs": {
        "type": FieldType.ARRAY,
        "required": True,
        "description": "Collection of tabs on this pin",
        "item_schema": TAB_SCHEMA,
        "min_items": 1
    },
    "state": {
        "type": FieldType.ENUM,
        "required": False,
        "description": "Current state of pin (runtime only, not saved)",
        "values": ["FLOAT", "HIGH"],
        "default": "FLOAT"
    }
}

COMPONENT_SCHEMA = {
    "component_id": {
        "type": FieldType.UUID,
        "required": True,
        "description": "Unique 8-character identifier for this component"
    },
    "component_type": {
        "type": FieldType.STRING,
        "required": True,
        "description": "Type of component (ToggleSwitch, Indicator, DPDTRelay, VCC, etc.)",
        "examples": ["ToggleSwitch", "Indicator", "DPDTRelay", "VCC"]
    },
    "position": {
        "type": FieldType.OBJECT,
        "required": True,
        "description": "Position on page canvas",
        "fields": {
            "x": {"type": FieldType.FLOAT, "required": True},
            "y": {"type": FieldType.FLOAT, "required": True}
        }
    },
    "rotation": {
        "type": FieldType.INTEGER,
        "required": False,
        "description": "Rotation in degrees (0, 90, 180, 270)",
        "default": 0,
        "validation": {"values": [0, 90, 180, 270]}
    },
    "link_name": {
        "type": FieldType.STRING,
        "required": False,
        "description": "Optional link name for cross-page connections",
        "default": None
    },
    "pins": {
        "type": FieldType.ARRAY,
        "required": True,
        "description": "Collection of pins on this component",
        "item_schema": PIN_SCHEMA,
        "min_items": 1
    },
    "properties": {
        "type": FieldType.OBJECT,
        "required": False,
        "description": "Component-specific properties (label, color, mode, etc.)",
        "default": {}
    }
}

WAYPOINT_SCHEMA = {
    "waypoint_id": {
        "type": FieldType.UUID,
        "required": True,
        "description": "Unique 8-character identifier for this waypoint"
    },
    "position": {
        "type": FieldType.OBJECT,
        "required": True,
        "description": "Position on page canvas",
        "fields": {
            "x": {"type": FieldType.FLOAT, "required": True},
            "y": {"type": FieldType.FLOAT, "required": True}
        }
    }
}

JUNCTION_SCHEMA = {
    "junction_id": {
        "type": FieldType.UUID,
        "required": True,
        "description": "Unique 8-character identifier for this junction"
    },
    "position": {
        "type": FieldType.OBJECT,
        "required": True,
        "description": "Position on page canvas",
        "fields": {
            "x": {"type": FieldType.FLOAT, "required": True},
            "y": {"type": FieldType.FLOAT, "required": True}
        }
    },
    "child_wires": {
        "type": FieldType.ARRAY,
        "required": True,
        "description": "Wires branching from this junction",
        "item_schema": None,  # Circular reference - defined as WIRE_SCHEMA below
        "min_items": 1
    }
}

WIRE_SCHEMA = {
    "wire_id": {
        "type": FieldType.UUID,
        "required": True,
        "description": "Unique 8-character identifier for this wire"
    },
    "start_tab_id": {
        "type": FieldType.UUID,
        "required": True,
        "description": "ID of tab where wire starts"
    },
    "end_tab_id": {
        "type": FieldType.UUID,
        "required": False,
        "description": "ID of tab where wire ends (null if ends at junction)",
        "default": None
    },
    "waypoints": {
        "type": FieldType.ARRAY,
        "required": False,
        "description": "Intermediate points along wire path",
        "item_schema": WAYPOINT_SCHEMA,
        "default": []
    },
    "junctions": {
        "type": FieldType.ARRAY,
        "required": False,
        "description": "Junction points with branching wires",
        "item_schema": JUNCTION_SCHEMA,
        "default": []
    }
}

# Update circular reference
JUNCTION_SCHEMA["child_wires"]["item_schema"] = WIRE_SCHEMA

PAGE_SCHEMA = {
    "page_id": {
        "type": FieldType.UUID,
        "required": True,
        "description": "Unique 8-character identifier for this page"
    },
    "name": {
        "type": FieldType.STRING,
        "required": True,
        "description": "Display name of page"
    },
    "components": {
        "type": FieldType.ARRAY,
        "required": False,
        "description": "Components on this page",
        "item_schema": COMPONENT_SCHEMA,
        "default": []
    },
    "wires": {
        "type": FieldType.ARRAY,
        "required": False,
        "description": "Wires on this page",
        "item_schema": WIRE_SCHEMA,
        "default": []
    }
}

DOCUMENT_SCHEMA = {
    "version": {
        "type": FieldType.STRING,
        "required": True,
        "description": "Schema version (e.g., '1.0.0')",
        "validation": {"pattern": r"^\d+\.\d+\.\d+$"}
    },
    "metadata": {
        "type": FieldType.OBJECT,
        "required": False,
        "description": "Document metadata",
        "default": {},
        "fields": {
            "title": {"type": FieldType.STRING, "required": False},
            "author": {"type": FieldType.STRING, "required": False},
            "description": {"type": FieldType.STRING, "required": False},
            "created": {"type": FieldType.STRING, "required": False, "description": "ISO 8601 datetime"},
            "modified": {"type": FieldType.STRING, "required": False, "description": "ISO 8601 datetime"}
        }
    },
    "pages": {
        "type": FieldType.ARRAY,
        "required": True,
        "description": "Collection of pages in document",
        "item_schema": PAGE_SCHEMA,
        "min_items": 1
    }
}


def get_schema_for_type(type_name: str) -> Optional[Dict[str, Any]]:
    """Get schema definition for a given type"""
    schemas = {
        "document": DOCUMENT_SCHEMA,
        "page": PAGE_SCHEMA,
        "component": COMPONENT_SCHEMA,
        "wire": WIRE_SCHEMA,
        "junction": JUNCTION_SCHEMA,
        "waypoint": WAYPOINT_SCHEMA,
        "pin": PIN_SCHEMA,
        "tab": TAB_SCHEMA
    }
    return schemas.get(type_name.lower())


def get_required_fields(schema: Dict[str, Any]) -> List[str]:
    """Get list of required field names from schema"""
    return [
        field_name
        for field_name, field_def in schema.items()
        if field_def.get("required", False)
    ]


def get_default_value(field_def: Dict[str, Any]) -> Any:
    """Get default value for a field, if defined"""
    return field_def.get("default")
