"""
Bridge Manager - Interface for components to create/remove bridges

This provides components (particularly relays) with methods to:
- Create bridges between VNETs when contacts close
- Remove bridges when contacts open
- Query existing bridges
"""

from typing import Dict, Optional
from core.bridge import Bridge
from core.id_manager import IDManager


class BridgeManager:
    """
    Manager class for bridge operations during simulation.
    
    Provides components with methods to:
    - Create bridges (relay contacts, etc.)
    - Remove bridges
    - Query bridges
    """
    
    def __init__(self, bridges: Dict[str, Bridge], id_manager: IDManager):
        """
        Initialize bridge manager.
        
        Args:
            bridges: Dictionary of all bridges by ID
            id_manager: ID manager for generating bridge IDs
        """
        self.bridges = bridges
        self.id_manager = id_manager
    
    def create_bridge(self, vnet1_id: str, vnet2_id: str, component_id: str) -> str:
        """
        Create a bridge between two VNETs.
        
        Args:
            vnet1_id: First VNET ID
            vnet2_id: Second VNET ID
            component_id: ID of component creating the bridge
            
        Returns:
            Bridge ID
        """
        bridge_id = self.id_manager.generate_id()
        bridge = Bridge(bridge_id, vnet1_id, vnet2_id, component_id)
        self.bridges[bridge_id] = bridge
        return bridge_id
    
    def remove_bridge(self, bridge_id: str) -> Optional[Bridge]:
        """
        Remove a bridge.
        
        Args:
            bridge_id: Bridge ID to remove
            
        Returns:
            Removed bridge or None if not found
        """
        return self.bridges.pop(bridge_id, None)
    
    def get_bridges_for_component(self, component_id: str) -> list:
        """
        Get all bridges created by a component.
        
        Args:
            component_id: Component ID
            
        Returns:
            List of Bridge instances
        """
        return [b for b in self.bridges.values() if b.component_id == component_id]
    
    def remove_bridges_for_component(self, component_id: str):
        """
        Remove all bridges created by a component.
        
        Args:
            component_id: Component ID
        """
        bridge_ids = [bid for bid, b in self.bridges.items() if b.component_id == component_id]
        for bridge_id in bridge_ids:
            self.bridges.pop(bridge_id, None)
