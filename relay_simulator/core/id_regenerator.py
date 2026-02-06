"""
ID Regeneration Utilities for Sub-Circuit Instantiation.

When creating a sub-circuit instance, all IDs from the template must be regenerated:
- Page IDs
- Component IDs  
- Pin IDs
- Tab IDs
- Wire IDs
- Waypoint IDs
- Junction IDs

This module provides utilities to deep-copy pages with  complete ID remapping.
"""

from typing import Dict, List, Optional
from copy import deepcopy
import json

from core.page import Page
from core.id_manager import IDManager
from components.factory import ComponentFactory


class IDMapper:
    """
    Tracks old ID -> new ID mappings during deep copy.
    Ensures all references are updated correctly.
    """
    
    def __init__(self, id_manager: IDManager):
        self.id_manager = id_manager
        self._mapping: Dict[str, str] = {}
    
    def generate_new_id(self, old_id: str) -> str:
        """
        Generate and register a new ID for an old ID.
        
        Args:
            old_id: Original ID from template
            
        Returns:
            str: New 8-char UUID
        """
        if old_id in self._mapping:
            return self._mapping[old_id]
        
        new_id = self.id_manager.generate_id()
        self._mapping[old_id] = new_id
        return new_id
    
    def get_mapped_id(self, old_id: str) -> Optional[str]:
        """
        Get the mapped new ID for an old ID.
        
        Args:
            old_id: Original ID
            
        Returns:
            str: New ID or None if not mapped
        """
        return self._mapping.get(old_id)
    
    def remap_hierarchical_id(self, hierarchical_id: str) -> str:
        """
        Remap a hierarchical ID (e.g., component_id.pin_name.tab_name).
        
        CRITICAL: Only the FIRST part (component_id) is a UUID that needs remapping.
        The remaining parts (pin_name, tab_name) are semantic identifiers that must be preserved.
        
        Examples:
        - "afccd56d.pin1.tab1" → "e83b0191.pin1.tab1" (only component ID changes)
        - "e2830e6e.COIL.tab0" → "78f462e5.COIL.tab0" (pin/tab names preserved)
        
        Args:
            hierarchical_id: Original hierarchical ID
            
        Returns:
            str: Remapped hierarchical ID
        """
        parts = hierarchical_id.split('.')
        
        if not parts:
            return hierarchical_id
        
        # Only remap the first part (component ID)
        first_part = parts[0]
        mapped_first = self.get_mapped_id(first_part)
        
        if mapped_first:
            # Use mapped component ID + preserve rest
            return '.'.join([mapped_first] + parts[1:])
        else:
            # Component ID not in mapping - generate new one
            new_first = self.generate_new_id(first_part)
            return '.'.join([new_first] + parts[1:])
    
    def get_all_mappings(self) -> Dict[str, str]:
        """Get all ID mappings."""
        return self._mapping.copy()


class PageCloner:
    """
    Deep-copies pages with complete ID regeneration.
    Handles components, wires, junctions, and all internal references.
    """
    
    def __init__(self, component_factory: ComponentFactory, id_manager: IDManager):
        self.component_factory = component_factory
        self.id_manager = id_manager
    
    def clone_pages(self, template_pages: List[Page]) -> tuple[List[Page], IDMapper]:
        """
        Clone a list of pages with complete ID regeneration.
        
        Args:
            template_pages: List of template pages to clone
            
        Returns:
            tuple: (cloned_pages, id_mapper)
        """
        id_mapper = IDMapper(self.id_manager)
        cloned_pages = []
        
        # First pass: Generate new IDs for all pages
        for template_page in template_pages:
            id_mapper.generate_new_id(template_page.page_id)
        
        # Second pass: Clone pages with ID remapping
        for template_page in template_pages:
            cloned_page = self._clone_page(template_page, id_mapper)
            cloned_pages.append(cloned_page)
        
        return cloned_pages, id_mapper
    
    def _clone_page(self, template_page: Page, id_mapper: IDMapper) -> Page:
        """
        Clone a single page with ID remapping.
        
        Args:
            template_page: Template page to clone
            id_mapper: ID mapper for tracking mappings
            
        Returns:
            Page: Cloned page with new IDs
        """
        # Serialize page to dict
        page_data = template_page.to_dict()
        
        # Remap IDs in the data structure
        remapped_data = self._remap_page_data(page_data, id_mapper)
        
        # Deserialize to create cloned page
        cloned_page = Page.from_dict(remapped_data, self.component_factory)
        
        return cloned_page
    
    def _remap_page_data(self, page_data: dict, id_mapper: IDMapper) -> dict:
        """
        Recursively remap all IDs in page data dictionary.
        
        Args:
            page_data: Original page data
            id_mapper: ID mapper
            
        Returns:
            dict: Remapped page data
        """
        # Deep copy to avoid modifying original
        data = deepcopy(page_data)
        
        # Remap page ID
        old_page_id = data.get('page_id')
        if old_page_id:
            data['page_id'] = id_mapper.get_mapped_id(old_page_id) or id_mapper.generate_new_id(old_page_id)
        
        # Remap components
        if 'components' in data:
            data['components'] = [
                self._remap_component_data(comp, id_mapper)
                for comp in data['components']
            ]
        
        # Remap wires
        if 'wires' in data:
            data['wires'] = [
                self._remap_wire_data(wire, id_mapper)
                for wire in data['wires']
            ]
        
        # Remap junctions
        if 'junctions' in data:
            data['junctions'] = [
                self._remap_junction_data(junction, id_mapper)
                for junction in data['junctions']
            ]
        
        return data
    
    def _remap_component_data(self, comp_data: dict, id_mapper: IDMapper) -> dict:
        """Remap IDs in component data."""
        data = deepcopy(comp_data)
        
        # Remap component ID
        old_comp_id = data.get('component_id')
        if old_comp_id:
            data['component_id'] = id_mapper.generate_new_id(old_comp_id)
        
        # Remap pins
        if 'pins' in data:
            data['pins'] = [
                self._remap_pin_data(pin, id_mapper)
                for pin in data['pins']
            ]
        
        # Preserve link_name (critical for Link components)
        # Link names are not IDs - they are logical names for cross-page connections
        
        return data
    
    def _remap_pin_data(self, pin_data: dict, id_mapper: IDMapper) -> dict:
        """Remap IDs in pin data."""
        data = deepcopy(pin_data)
        
        # Remap pin ID
        old_pin_id = data.get('pin_id')
        if old_pin_id:
            data['pin_id'] = id_mapper.remap_hierarchical_id(old_pin_id)
        
        # Remap tabs
        if 'tabs' in data:
            data['tabs'] = [
                self._remap_tab_data(tab, id_mapper)
                for tab in data['tabs']
            ]
        
        return data
    
    def _remap_tab_data(self, tab_data: dict, id_mapper: IDMapper) -> dict:
        """Remap IDs in tab data."""
        data = deepcopy(tab_data)
        
        # Remap tab ID
        old_tab_id = data.get('tab_id')
        if old_tab_id:
            data['tab_id'] = id_mapper.remap_hierarchical_id(old_tab_id)
        
        return data
    
    def _remap_wire_data(self, wire_data: dict, id_mapper: IDMapper) -> dict:
        """Remap IDs in wire data."""
        data = deepcopy(wire_data)
        
        # Remap wire ID
        old_wire_id = data.get('wire_id')
        if old_wire_id:
            data['wire_id'] = id_mapper.generate_new_id(old_wire_id)
        
        # Remap start/end tab IDs
        if 'start_tab_id' in data and data['start_tab_id']:
            data['start_tab_id'] = id_mapper.remap_hierarchical_id(data['start_tab_id'])
        
        if 'end_tab_id' in data and data['end_tab_id']:
            data['end_tab_id'] = id_mapper.remap_hierarchical_id(data['end_tab_id'])
        
        # Remap waypoints
        if 'waypoints' in data:
            data['waypoints'] = [
                self._remap_waypoint_data(wp, id_mapper)
                for wp in data['waypoints']
            ]
        
        return data
    
    def _remap_waypoint_data(self, waypoint_data: dict, id_mapper: IDMapper) -> dict:
        """Remap IDs in waypoint data."""
        data = deepcopy(waypoint_data)
        
        old_waypoint_id = data.get('waypoint_id')
        if old_waypoint_id:
            data['waypoint_id'] = id_mapper.generate_new_id(old_waypoint_id)
        
        return data
    
    def _remap_junction_data(self, junction_data: dict, id_mapper: IDMapper) -> dict:
        """Remap IDs in junction data."""
        data = deepcopy(junction_data)
        
        old_junction_id = data.get('junction_id')
        if old_junction_id:
            data['junction_id'] = id_mapper.generate_new_id(old_junction_id)
        
        # Remap child wires
        if 'child_wires' in data:
            data['child_wires'] = [
                self._remap_wire_data(wire, id_mapper)
                for wire in data['child_wires']
            ]
        
        return data
