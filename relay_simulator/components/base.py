"""
Base component class that all components must inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Component(ABC):
    """
    Base class for all simulator components.
    
    Each component must implement:
    - simulate_logic(): Calculate new state based on pin states
    - sim_start(): Initialize component at simulation start
    - render(): Draw component using canvas adapter
    """
    
    # Class attribute - override in subclass
    component_type: str = None
    
    def __init__(self, component_id: str, page_id: str):
        """
        Initialize component.
        
        Args:
            component_id: Unique component ID (8 char UUID)
            page_id: Page ID this component belongs to
        """
        self.component_id = component_id
        self.page_id = page_id
        self.position = (0, 0)  # (X, Y) in pixels
        self.rotation = 0  # Rotation in degrees (if applicable)
        self.properties = {}  # Component-specific properties
        self.pins = {}  # pin_id -> Pin object
        self.link_name = None  # Optional, for cross-page links
    
    # === SIMULATION INTERFACE ===
    
    @abstractmethod
    def simulate_logic(self, vnet_manager):
        """
        Calculate new component state based on pin states.
        Update pins if state changes.
        Mark VNETs dirty via vnet_manager if needed.
        
        Called by engine when component's VNETs are dirty.
        
        Args:
            vnet_manager: VnetManager instance for marking VNETs dirty
        """
        pass
    
    @abstractmethod
    def sim_start(self, vnet_manager, bridge_manager):
        """
        Initialize component for simulation start.
        Set default pin states.
        Create bridges if needed (e.g., relay contacts).
        Read connected VNETs.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance for creating bridges
        """
        pass
    
    def sim_stop(self):
        """
        Clean up component state at simulation stop.
        Bridges are removed by engine automatically.
        Override if component needs special cleanup.
        """
        pass
    
    # === PIN MANAGEMENT ===
    
    def add_pin(self, pin):
        """
        Add a pin to this component.
        
        Args:
            pin: Pin instance to add
        """
        from core.pin import Pin
        if not isinstance(pin, Pin):
            raise TypeError("pin must be a Pin instance")
        
        self.pins[pin.pin_id] = pin
        pin.parent_component = self
    
    def get_pin(self, pin_id: str):
        """
        Get pin by ID.
        
        Args:
            pin_id: Pin ID to retrieve
            
        Returns:
            Pin instance or None if not found
        """
        return self.pins.get(pin_id)
    
    def get_all_pins(self) -> Dict:
        """
        Get all pins on this component.
        
        Returns:
            dict: Dictionary of pin_id -> Pin
        """
        return self.pins.copy()
    
    def remove_pin(self, pin_id: str):
        """
        Remove a pin from this component.
        
        Args:
            pin_id: Pin ID to remove
            
        Returns:
            bool: True if pin was removed, False if not found
        """
        if pin_id in self.pins:
            del self.pins[pin_id]
            return True
        return False
    
    # === PROPERTY MANAGEMENT ===
    
    def get_property(self, key: str, default=None) -> Any:
        """
        Get a component property.
        
        Args:
            key: Property name
            default: Default value if property not found
            
        Returns:
            Property value or default
        """
        return self.properties.get(key, default)
    
    def set_property(self, key: str, value: Any):
        """
        Set a component property.
        
        Args:
            key: Property name
            value: Property value
        """
        self.properties[key] = value
    
    def clone_properties(self) -> Dict[str, Any]:
        """
        Clone all properties for copy operation.
        Deep copies values to avoid shared references.
        
        Returns:
            dict: Cloned properties
        """
        import copy
        return copy.deepcopy(self.properties)
    
    # === INTERACTION INTERFACE ===
    
    def interact(self, action: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Handle user interaction with component.
        Examples: toggle switch, press button
        
        Args:
            action: Action name (e.g., "toggle", "press")
            params: Optional parameters
        
        Returns:
            bool: True if state changed and simulation should update
        """
        return False
    
    # === VISUAL INTERFACE ===
    
    def get_visual_state(self) -> Dict[str, Any]:
        """
        Return current visual state for rendering.
        
        Returns:
            dict with keys:
                - type: Component type
                - position: (x, y)
                - rotation: degrees
                - state: Component-specific state
                - pin_states: Dict of pin_id -> state
                - properties: Component properties
        """
        return {
            'type': self.component_type,
            'component_id': self.component_id,
            'position': self.position,
            'rotation': self.rotation,
            'properties': self.properties.copy(),
            'pin_states': {pin_id: str(pin.state) for pin_id, pin in self.pins.items()}
        }
    
    @abstractmethod
    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        """
        Render component using canvas adapter.
        
        Args:
            canvas_adapter: CanvasAdapter instance for drawing
            x_offset: X offset for panning (pixels)
            y_offset: Y offset for panning (pixels)
        """
        pass
    
    # === SERIALIZATION INTERFACE ===
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize component to dict for saving to .rsim file.
        
        Returns:
            dict: Component data
        """
        return {
            'component_id': self.component_id,
            'type': self.component_type,
            'position': self.position,
            'rotation': self.rotation,
            'properties': self.properties,
            'link_name': self.link_name,
            'pins': {pin_id: pin.to_dict() for pin_id, pin in self.pins.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        """
        Deserialize component from dict (loaded from .rsim file).
        Override in subclass to properly reconstruct component.
        
        Args:
            data: Component data dict
            
        Returns:
            Component: Reconstructed component instance
        """
        raise NotImplementedError("Subclass must implement from_dict()")
    
    def __repr__(self):
        return f"{self.component_type}({self.component_id})"
