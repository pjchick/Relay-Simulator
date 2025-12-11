"""
DocumentLoader - Load and validate .rsim files.
Handles file I/O, JSON parsing, and document reconstruction.
"""

import json
from pathlib import Path
from typing import Dict, Set, Optional
from core.document import Document
from components.factory import ComponentFactory


class DocumentLoader:
    """
    DocumentLoader handles loading .rsim files from disk.
    Performs validation, ID checking, and component instantiation.
    """
    
    def __init__(self, component_factory: Optional[ComponentFactory] = None):
        """
        Initialize document loader.
        
        Args:
            component_factory: ComponentFactory instance (creates default if None)
        """
        self.component_factory = component_factory or ComponentFactory()
    
    def load_from_file(self, filepath: str) -> Document:
        """
        Load document from .rsim file.
        
        Args:
            filepath: Path to .rsim file
            
        Returns:
            Document: Loaded document with all components and wires
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid or has duplicate IDs
            json.JSONDecodeError: If JSON is malformed
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Read and parse JSON
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate structure
        self._validate_structure(data)
        
        # Deserialize document (with component factory)
        document = Document.from_dict(data, self.component_factory)
        
        # Validate IDs are unique
        self._validate_unique_ids(document)
        
        return document
    
    def load_from_string(self, json_string: str) -> Document:
        """
        Load document from JSON string.
        
        Args:
            json_string: JSON string containing .rsim data
            
        Returns:
            Document: Loaded document
            
        Raises:
            ValueError: If data is invalid or has duplicate IDs
            json.JSONDecodeError: If JSON is malformed
        """
        data = json.loads(json_string)
        
        # Validate structure
        self._validate_structure(data)
        
        # Deserialize document
        document = Document.from_dict(data, self.component_factory)
        
        # Validate IDs
        self._validate_unique_ids(document)
        
        return document
    
    def save_to_file(self, document: Document, filepath: str, indent: int = 2):
        """
        Save document to .rsim file.
        
        Args:
            document: Document to save
            filepath: Path to save file
            indent: JSON indentation (default: 2)
        """
        path = Path(filepath)
        
        # Serialize document
        data = document.to_dict()
        
        # Write JSON
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
    
    def _validate_structure(self, data: dict):
        """
        Validate basic document structure.
        
        Args:
            data: Parsed JSON data
            
        Raises:
            ValueError: If required fields are missing
        """
        if not isinstance(data, dict):
            raise ValueError("Document must be a JSON object")
        
        if 'version' not in data:
            raise ValueError("Missing required field: version")
        
        if 'pages' not in data:
            raise ValueError("Missing required field: pages")
        
        if not isinstance(data['pages'], list):
            raise ValueError("Field 'pages' must be an array")
        
        if len(data['pages']) == 0:
            raise ValueError("Document must contain at least one page")
    
    def _validate_unique_ids(self, document: Document):
        """
        Validate that all IDs in the document are unique.
        
        Args:
            document: Document to validate
            
        Raises:
            ValueError: If duplicate IDs are found
        """
        all_ids: Set[str] = set()
        duplicates: Set[str] = set()
        
        # Check page IDs
        for page in document.get_all_pages():
            if page.page_id in all_ids:
                duplicates.add(page.page_id)
            all_ids.add(page.page_id)
            
            # Check component IDs
            for component in page.get_all_components():
                if component.component_id in all_ids:
                    duplicates.add(component.component_id)
                all_ids.add(component.component_id)
                
                # Check pin IDs
                for pin in component.pins.values():
                    if pin.pin_id in all_ids:
                        duplicates.add(pin.pin_id)
                    all_ids.add(pin.pin_id)
                    
                    # Check tab IDs
                    for tab in pin.tabs.values():
                        if tab.tab_id in all_ids:
                            duplicates.add(tab.tab_id)
                        all_ids.add(tab.tab_id)
            
            # Check wire IDs
            for wire in page.get_all_wires():
                if wire.wire_id in all_ids:
                    duplicates.add(wire.wire_id)
                all_ids.add(wire.wire_id)
                
                # Check waypoint IDs (wire stores as dict internally)
                for waypoint in wire.waypoints.values():
                    if waypoint.waypoint_id in all_ids:
                        duplicates.add(waypoint.waypoint_id)
                    all_ids.add(waypoint.waypoint_id)
                
                # Check junction IDs (recursive, wire stores as dict internally)
                self._check_junction_ids(list(wire.junctions.values()), all_ids, duplicates)
        
        if duplicates:
            raise ValueError(
                f"Duplicate IDs found in document: {', '.join(sorted(duplicates))}"
            )
    
    def _check_junction_ids(self, junctions: list, all_ids: Set[str], duplicates: Set[str]):
        """
        Recursively check junction and child wire IDs.
        
        Args:
            junctions: List of junctions to check
            all_ids: Set of all IDs seen
            duplicates: Set of duplicate IDs found
        """
        for junction in junctions:
            if junction.junction_id in all_ids:
                duplicates.add(junction.junction_id)
            all_ids.add(junction.junction_id)
            
            # Check child wires recursively (junction stores as dict internally)
            for child_wire in junction.child_wires.values():
                if child_wire.wire_id in all_ids:
                    duplicates.add(child_wire.wire_id)
                all_ids.add(child_wire.wire_id)
                
                # Check child wire waypoints (child_wire stores as dict internally)
                for waypoint in child_wire.waypoints.values():
                    if waypoint.waypoint_id in all_ids:
                        duplicates.add(waypoint.waypoint_id)
                    all_ids.add(waypoint.waypoint_id)
                
                # Recurse into child wire junctions (convert dict to list)
                self._check_junction_ids(list(child_wire.junctions.values()), all_ids, duplicates)


def load_document(filepath: str, component_factory: Optional[ComponentFactory] = None) -> Document:
    """
    Convenience function to load a document from file.
    
    Args:
        filepath: Path to .rsim file
        component_factory: Optional ComponentFactory instance
        
    Returns:
        Document: Loaded document
    """
    loader = DocumentLoader(component_factory)
    return loader.load_from_file(filepath)


def save_document(document: Document, filepath: str, indent: int = 2):
    """
    Convenience function to save a document to file.
    
    Args:
        document: Document to save
        filepath: Path to save file
        indent: JSON indentation (default: 2)
    """
    loader = DocumentLoader()
    loader.save_to_file(document, filepath, indent)
