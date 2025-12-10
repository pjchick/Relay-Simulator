"""
Component Factory/Registry for Relay Logic Simulator

Provides centralized component creation and type registration.
Supports creating components by type string and deserialization from file data.
"""

from typing import Dict, Type, Any, List
from components.base import Component
from components.switch import Switch
from components.indicator import Indicator
from components.dpdt_relay import DPDTRelay
from components.vcc import VCC


class ComponentFactory:
    """
    Factory for creating component instances.
    
    Maintains a registry of component types and provides methods for:
    - Creating components by type string
    - Deserializing components from file data
    - Listing available component types
    """
    
    def __init__(self):
        """Initialize component factory with empty registry."""
        self._registry: Dict[str, Type[Component]] = {}
        self._register_built_in_components()
    
    def _register_built_in_components(self):
        """Register all built-in component types."""
        self.register_component("Switch", Switch)
        self.register_component("Indicator", Indicator)
        self.register_component("DPDTRelay", DPDTRelay)
        self.register_component("VCC", VCC)
    
    def register_component(self, type_name: str, component_class: Type[Component]):
        """
        Register a component type.
        
        Args:
            type_name: Type identifier string (e.g., "Switch", "DPDTRelay")
            component_class: Component class to register
            
        Raises:
            ValueError: If type_name already registered
        """
        if type_name in self._registry:
            raise ValueError(f"Component type '{type_name}' is already registered")
        
        self._registry[type_name] = component_class
    
    def create_component(self, type_name: str, component_id: str, page_id: str) -> Component:
        """
        Create a component instance by type.
        
        Args:
            type_name: Type identifier string (e.g., "Switch", "DPDTRelay")
            component_id: Unique component ID
            page_id: Page ID where component will be placed
            
        Returns:
            Component instance
            
        Raises:
            ValueError: If type_name not registered
        """
        if type_name not in self._registry:
            raise ValueError(f"Unknown component type: '{type_name}'")
        
        component_class = self._registry[type_name]
        return component_class(component_id, page_id)
    
    def create_from_dict(self, data: Dict[str, Any]) -> Component:
        """
        Create a component from serialized data.
        
        Uses the component's from_dict() class method for deserialization.
        
        Args:
            data: Serialized component data (must include 'type' field)
            
        Returns:
            Component instance restored from data
            
        Raises:
            ValueError: If 'type' field missing or type not registered
        """
        if 'type' not in data:
            raise ValueError("Component data missing 'type' field")
        
        type_name = data['type']
        
        if type_name not in self._registry:
            raise ValueError(f"Unknown component type: '{type_name}'")
        
        component_class = self._registry[type_name]
        
        # Use the component's from_dict class method
        return component_class.from_dict(data)
    
    def list_component_types(self) -> List[str]:
        """
        Get list of all registered component types.
        
        Returns:
            List of type identifier strings
        """
        return sorted(self._registry.keys())
    
    def is_registered(self, type_name: str) -> bool:
        """
        Check if a component type is registered.
        
        Args:
            type_name: Type identifier string
            
        Returns:
            True if registered, False otherwise
        """
        return type_name in self._registry
    
    def get_component_class(self, type_name: str) -> Type[Component]:
        """
        Get the component class for a type.
        
        Args:
            type_name: Type identifier string
            
        Returns:
            Component class
            
        Raises:
            ValueError: If type_name not registered
        """
        if type_name not in self._registry:
            raise ValueError(f"Unknown component type: '{type_name}'")
        
        return self._registry[type_name]
    
    def get_registry_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed information about all registered components.
        
        Returns:
            Dictionary mapping type names to component info
        """
        info = {}
        
        for type_name, component_class in self._registry.items():
            info[type_name] = {
                'type': type_name,
                'class_name': component_class.__name__,
                'module': component_class.__module__,
            }
        
        return info


# Global factory instance
_global_factory: ComponentFactory = None


def get_factory() -> ComponentFactory:
    """
    Get the global component factory instance.
    
    Creates factory on first access (singleton pattern).
    
    Returns:
        ComponentFactory instance
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = ComponentFactory()
    return _global_factory


def reset_factory():
    """
    Reset the global factory instance.
    
    Useful for testing - clears all registrations.
    """
    global _global_factory
    _global_factory = None
