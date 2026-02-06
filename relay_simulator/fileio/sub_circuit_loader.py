"""
SubCircuitLoader - Load and validate .rsub sub-circuit template files.

A valid .rsub file must:
1. Have the same JSON structure as .rsim files
2. Contain at least one page named "FOOTPRINT" (case-sensitive)
3. FOOTPRINT page should contain Link components that define the interface
4. All other pages contain the internal circuit logic
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from components.factory import ComponentFactory


class SubCircuitTemplate:
    """
    Represents a loaded .rsub template.
    
    Contains:
    - Template pages (including FOOTPRINT)
    - Metadata
    - Interface definition (Links from FOOTPRINT)
    """
    
    def __init__(self):
        self.name: str = ""
        self.source_file: str = ""
        self.pages: List[Dict] = []
        self.metadata: Dict = {}
        self.footprint_page_id: Optional[str] = None
        self.interface_links: List[Dict] = []  # Links from FOOTPRINT page
    
    def get_footprint_page(self) -> Optional[Dict]:
        """Get the FOOTPRINT page data."""
        for page in self.pages:
            if page.get('page_id') == self.footprint_page_id:
                return page
        return None


class SubCircuitLoader:
    """
    SubCircuitLoader handles loading .rsub template files.
    Validates structure and extracts interface definition.
    """
    
    FOOTPRINT_PAGE_NAME = "FOOTPRINT"
    
    def __init__(self, component_factory: Optional[ComponentFactory] = None):
        """
        Initialize sub-circuit loader.
        
        Args:
            component_factory: ComponentFactory instance (creates default if None)
        """
        self.component_factory = component_factory or ComponentFactory()
    
    def load_from_file(self, filepath: str) -> SubCircuitTemplate:
        """
        Load sub-circuit template from .rsub file.
        
        Args:
            filepath: Path to .rsub file
            
        Returns:
            SubCircuitTemplate: Loaded template with validation
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid or missing FOOTPRINT page
            json.JSONDecodeError: If JSON is malformed
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Sub-circuit file not found: {filepath}")
        
        # Read and parse JSON
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate basic structure (same as .rsim)
        self._validate_structure(data)
        
        # Parse template
        template = self._parse_template(data, path.name)
        
        # Validate FOOTPRINT page exists
        self._validate_footprint(template)
        
        return template
    
    def load_from_string(self, json_string: str, source_name: str = "unknown") -> SubCircuitTemplate:
        """
        Load sub-circuit template from JSON string.
        
        Args:
            json_string: JSON string containing .rsub data
            source_name: Name to identify the source (for error messages)
            
        Returns:
            SubCircuitTemplate: Loaded template
            
        Raises:
            ValueError: If data is invalid or missing FOOTPRINT page
            json.JSONDecodeError: If JSON is malformed
        """
        data = json.loads(json_string)
        
        # Validate structure
        self._validate_structure(data)
        
        # Parse template
        template = self._parse_template(data, source_name)
        
        # Validate FOOTPRINT page
        self._validate_footprint(template)
        
        return template
    
    def _validate_structure(self, data: dict):
        """
        Validate basic .rsub file structure (same as .rsim).
        
        Args:
            data: Parsed JSON data
            
        Raises:
            ValueError: If required fields are missing
        """
        if not isinstance(data, dict):
            raise ValueError("Sub-circuit template must be a JSON object")
        
        if 'version' not in data:
            raise ValueError("Missing required field: version")
        
        if 'pages' not in data:
            raise ValueError("Missing required field: pages")
        
        if not isinstance(data['pages'], list):
            raise ValueError("Field 'pages' must be an array")
        
        if len(data['pages']) == 0:
            raise ValueError("Sub-circuit template must contain at least one page (FOOTPRINT)")
    
    def _parse_template(self, data: dict, source_name: str) -> SubCircuitTemplate:
        """
        Parse template data into SubCircuitTemplate object.
        
        Args:
            data: Validated JSON data
            source_name: Source filename
            
        Returns:
            SubCircuitTemplate: Parsed template
        """
        template = SubCircuitTemplate()
        template.source_file = source_name
        template.pages = data.get('pages', [])
        template.metadata = data.get('metadata', {})
        
        # Extract name from metadata or filename
        template.name = template.metadata.get('title', '')
        if not template.name:
            # Use filename without extension as name
            template.name = Path(source_name).stem
        
        # Find FOOTPRINT page
        for page in template.pages:
            if page.get('name') == self.FOOTPRINT_PAGE_NAME:
                template.footprint_page_id = page.get('page_id')
                break
        
        # Extract interface Links from FOOTPRINT
        if template.footprint_page_id:
            footprint = template.get_footprint_page()
            if footprint:
                components = footprint.get('components', [])
                template.interface_links = [
                    comp for comp in components
                    if comp.get('component_type') == 'Link'
                ]
        
        return template
    
    def _validate_footprint(self, template: SubCircuitTemplate):
        """
        Validate that FOOTPRINT page exists and is valid.
        
        Args:
            template: Template to validate
            
        Raises:
            ValueError: If FOOTPRINT page is missing or invalid
        """
        if not template.footprint_page_id:
            raise ValueError(
                f"Sub-circuit template '{template.name}' must contain a page "
                f"named '{self.FOOTPRINT_PAGE_NAME}'"
            )
        
        footprint = template.get_footprint_page()
        if not footprint:
            raise ValueError(
                f"FOOTPRINT page not found in template '{template.name}'"
            )
        
        # Check for Link components (interface definition)
        if not template.interface_links:
            # Warning: FOOTPRINT with no Links means no external interface
            # This is technically valid but probably not useful
            pass
        
        # Validate that all Links have link_name set
        for i, link in enumerate(template.interface_links):
            link_name = link.get('link_name', '').strip()
            if not link_name:
                raise ValueError(
                    f"Link component #{i+1} on FOOTPRINT page must have 'link_name' property set"
                )
    
    def save_to_file(self, template: SubCircuitTemplate, filepath: str, indent: int = 2):
        """
        Save sub-circuit template to .rsub file.
        
        Args:
            template: Template to save
            filepath: Path to save file
            indent: JSON indentation (default: 2)
        """
        path = Path(filepath)
        
        # Reconstruct JSON structure
        data = {
            'version': '1.0.0',
            'pages': template.pages,
            'metadata': template.metadata
        }
        
        # Write JSON
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
