"""
Bridge Manager - Interface for components to create/remove bridges

This provides components (particularly relays) with methods to:
- Create bridges between VNETs when contacts close
- Remove bridges when contacts open
- Query existing bridges
"""

from typing import Dict, Optional, TYPE_CHECKING
from core.bridge import Bridge
from core.id_manager import IDManager
from core.vnet import VNET

if TYPE_CHECKING:
    from simulation.component_update_coordinator import ComponentUpdateCoordinator


class BridgeManager:
    """
    Manager class for bridge operations during simulation.
    
    Provides components with methods to:
    - Create bridges (relay contacts, etc.)
    - Remove bridges
    - Query bridges
    """
    
    def __init__(self, bridges: Dict[str, Bridge], id_manager: IDManager, vnets: Dict[str, VNET], coordinator: Optional['ComponentUpdateCoordinator'] = None):
        """
        Initialize bridge manager.
        
        Args:
            bridges: Dictionary of all bridges by ID
            id_manager: ID manager for generating bridge IDs
            vnets: Dictionary of all VNETs by ID (needed to update bridge_ids)
            coordinator: Component update coordinator (optional, for marking components dirty)
        """
        self.bridges = bridges
        self.id_manager = id_manager
        self.vnets = vnets
        self.coordinator = coordinator
    
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
        bridge = Bridge(vnet1_id, vnet2_id, component_id, bridge_id)
        self.bridges[bridge_id] = bridge
        
        # Add bridge to both VNETs
        vnet1 = self.vnets.get(vnet1_id)
        vnet2 = self.vnets.get(vnet2_id)
        if vnet1:
            vnet1.add_bridge(bridge_id)
        if vnet2:
            vnet2.add_bridge(bridge_id)
        
        return bridge_id
    
    def remove_bridge(self, bridge_id: str) -> Optional[Bridge]:
        """
        Remove a bridge.
        
        Args:
            bridge_id: Bridge ID to remove
            
        Returns:
            Removed bridge or None if not found
        """
        bridge = self.bridges.pop(bridge_id, None)
        
        # Remove bridge from both VNETs and mark connected components dirty
        if bridge:
            vnet1 = self.vnets.get(bridge.vnet_id1)
            vnet2 = self.vnets.get(bridge.vnet_id2)
            
            if vnet1:
                vnet1.remove_bridge(bridge_id)
                # Mark all components connected to this VNET as dirty
                if self.coordinator:
                    self.coordinator.queue_components_for_vnet(vnet1)
            
            if vnet2:
                vnet2.remove_bridge(bridge_id)
                # Mark all components connected to this VNET as dirty
                if self.coordinator:
                    self.coordinator.queue_components_for_vnet(vnet2)
        
        return bridge
    
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
        """remove_bridge(bridge_id)  # Use remove_bridge to trigger component queuing
        Remove all bridges created by a component.
        
        Args:
            component_id: Component ID
        """
        bridge_ids = [bid for bid, b in self.bridges.items() if b.component_id == component_id]
        for bridge_id in bridge_ids:
            self.bridges.pop(bridge_id, None)
