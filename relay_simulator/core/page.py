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
        self.junctions: Dict[str, 'Junction'] = {}  # Junction support for wire branching
        
        # Canvas state (persisted to .rsim)
        self.canvas_x: float = 0.0
        self.canvas_y: float = 0.0
        self.canvas_zoom: float = 1.0
    
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
    
    # === Junction Management ===
    
    def add_junction(self, junction):
        """
        Add a junction to this page.
        
        Args:
            junction: Junction instance
        """
        self.junctions[junction.junction_id] = junction
    
    def remove_junction(self, junction_id: str):
        """
        Remove a junction from this page.
        
        Args:
            junction_id: Junction ID to remove
            
        Returns:
            Junction: Removed junction or None
        """
        return self.junctions.pop(junction_id, None)
    
    def get_junction(self, junction_id: str):
        """
        Get junction by ID.
        
        Args:
            junction_id: Junction ID
            
        Returns:
            Junction: Junction instance or None
        """
        return self.junctions.get(junction_id)
    
    def get_all_junctions(self) -> list:
        """
        Get all junctions on this page.
        
        Returns:
            list: List of junctions
        """
        return list(self.junctions.values())
    
    # === Serialization ===
    
    def to_dict(self) -> dict:
        """
        Serialize page to dict (matches .rsim schema).
        
        Returns:
            dict: Page data
        """
        result = {
            'page_id': self.page_id,
            'name': self.name,
            'canvas_x': self.canvas_x,
            'canvas_y': self.canvas_y,
            'canvas_zoom': self.canvas_zoom
        }
        
        # Optional fields (only include if not empty)
        if self.components:
            result['components'] = [comp.to_dict() for comp in self.components.values()]
        
        if self.wires:
            result['wires'] = [wire.to_dict() for wire in self.wires.values()]
        
        if self.junctions:
            result['junctions'] = [junction.to_dict() for junction in self.junctions.values()]
        
        return result
    
    @staticmethod
    def from_dict(data: dict, component_factory=None) -> 'Page':
        """
        Deserialize page from dict (matches .rsim schema).
        
        Args:
            data: Page data dict
            component_factory: ComponentFactory instance for creating components
            
        Returns:
            Page: Reconstructed page with components and wires
        """
        from core.wire import Wire
        
        page = Page(
            page_id=data['page_id'],
            name=data.get('name', 'Untitled')
        )
        
        # Restore canvas state (with defaults for older files)
        page.canvas_x = data.get('canvas_x', 0.0)
        page.canvas_y = data.get('canvas_y', 0.0)
        page.canvas_zoom = data.get('canvas_zoom', 1.0)
        
        # Deserialize components (if factory provided)
        if component_factory and 'components' in data:
            for comp_data in data['components']:
                component = component_factory.create_from_dict(comp_data)
                page.add_component(component)
        
        # Deserialize wires
        for wire_data in data.get('wires', []):
            wire = Wire.from_dict(wire_data)
            page.add_wire(wire)
        
        # Deserialize junctions
        from core.wire import Junction
        for junction_data in data.get('junctions', []):
            junction = Junction.from_dict(junction_data)
            page.add_junction(junction)
        
        return page
    
    def __repr__(self):
        return f"Page({self.page_id}, '{self.name}', components={len(self.components)}, wires={len(self.wires)})"
