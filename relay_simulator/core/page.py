"""
Page class - Represents a single page in a document.
Contains components and wires.
"""

from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from components.base import Component


class Page:
    """
    Page represents a single schematic page in the document.
    Contains components and wires.
    """
    
    def __init__(self, page_id: str, name: str = "Untitled"):
        """
        Initialize page.
        
        Args:
            page_id: Unique page ID (8-char UUID)
            name: Page name/title
        """
        self.page_id = page_id
        self.name = name
        self.components: Dict[str, 'Component'] = {}
        self.wires: Dict[str, 'Wire'] = {}  # Will be implemented later
    
    # === Component Management ===
    
    def add_component(self, component: 'Component'):
        """
        Add a component to this page.
        
        Args:
            component: Component instance
        """
        self.components[component.component_id] = component
    
    def remove_component(self, component_id: str) -> Optional['Component']:
        """
        Remove a component from this page.
        
        Args:
            component_id: Component ID to remove
            
        Returns:
            Component: Removed component or None
        """
        return self.components.pop(component_id, None)
    
    def get_component(self, component_id: str) -> Optional['Component']:
        """
        Get component by ID.
        
        Args:
            component_id: Component ID
            
        Returns:
            Component: Component instance or None
        """
        return self.components.get(component_id)
    
    def get_all_components(self) -> List['Component']:
        """
        Get all components on this page.
        
        Returns:
            list: List of components
        """
        return list(self.components.values())
    
    # === Wire Management ===
    
    def add_wire(self, wire):
        """
        Add a wire to this page.
        
        Args:
            wire: Wire instance
        """
        # Wire class to be implemented later
        self.wires[wire.wire_id] = wire
    
    def remove_wire(self, wire_id: str):
        """
        Remove a wire from this page.
        
        Args:
            wire_id: Wire ID to remove
            
        Returns:
            Wire: Removed wire or None
        """
        return self.wires.pop(wire_id, None)
    
    def get_wire(self, wire_id: str):
        """
        Get wire by ID.
        
        Args:
            wire_id: Wire ID
            
        Returns:
            Wire: Wire instance or None
        """
        return self.wires.get(wire_id)
    
    def get_all_wires(self) -> list:
        """
        Get all wires on this page.
        
        Returns:
            list: List of wires
        """
        return list(self.wires.values())
    
    # === Serialization ===
    
    def to_dict(self) -> dict:
        """
        Serialize page to dict.
        
        Returns:
            dict: Page data
        """
        return {
            'page_id': self.page_id,
            'name': self.name,
            'components': {
                comp_id: comp.to_dict() 
                for comp_id, comp in self.components.items()
            },
            'wires': {
                wire_id: wire.to_dict() 
                for wire_id, wire in self.wires.items()
            }
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Page':
        """
        Deserialize page from dict.
        
        Args:
            data: Page data dict
            
        Returns:
            Page: Reconstructed page
        """
        page = Page(
            page_id=data['page_id'],
            name=data.get('name', 'Untitled')
        )
        
        # Components will be loaded by component loader
        # (because we need to instantiate correct component types)
        
        return page
    
    def __repr__(self):
        return f"Page({self.page_id}, '{self.name}', components={len(self.components)}, wires={len(self.wires)})"
