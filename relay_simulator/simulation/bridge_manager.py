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
    
    def _get_connected_vnet_network(self, start_vnet_id: str) -> set:
        """
        Get all VNETs transitively connected through bridges and links.
        
        Uses BFS to find all VNETs reachable from the starting VNET
        through the bridge network and link names.
        
        Args:
            start_vnet_id: Starting VNET ID
            
        Returns:
            Set of all connected VNET IDs (including start_vnet_id)
        """
        connected = set()
        queue = [start_vnet_id]
        
        while queue:
            current_id = queue.pop(0)
            
            if current_id in connected:
                continue
                
            connected.add(current_id)
            current_vnet = self.vnets.get(current_id)
            
            if not current_vnet:
                continue
            
            # Follow all bridges from this VNET
            for bridge_id in current_vnet.bridge_ids:
                bridge = self.bridges.get(bridge_id)
                if bridge:
                    other_id = bridge.get_other_vnet(current_id)
                    if other_id and other_id not in connected:
                        queue.append(other_id)
            
            # Follow all link names from this VNET
            for link_name in current_vnet.link_names:
                for other_vnet_id, other_vnet in self.vnets.items():
                    if other_vnet_id != current_id and other_vnet.has_link(link_name):
                        if other_vnet_id not in connected:
                            queue.append(other_vnet_id)
        
        return connected
    
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
        
        # Queue all components in the entire connected network
        # This ensures components multiple hops away get re-evaluated
        # (e.g., ground detection through multiple relay bridges)
        if self.coordinator and (vnet1 or vnet2):
            # Find all VNETs transitively connected through bridges
            start_id = vnet1_id if vnet1 else vnet2_id
            connected_vnets = self._get_connected_vnet_network(start_id)
            
            # Queue components on all connected VNETs
            for vnet_id in connected_vnets:
                vnet = self.vnets.get(vnet_id)
                if vnet:
                    self.coordinator.queue_components_for_vnet(vnet)
        
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
            
            # Remove bridge references from VNETs
            if vnet1:
                vnet1.remove_bridge(bridge_id)
            if vnet2:
                vnet2.remove_bridge(bridge_id)
            
            # Queue all components in both networks
            # (they may now be separate networks after bridge removal)
            if self.coordinator:
                all_affected = set()
                
                if vnet1:
                    network1 = self._get_connected_vnet_network(bridge.vnet_id1)
                    all_affected.update(network1)
                
                if vnet2:
                    network2 = self._get_connected_vnet_network(bridge.vnet_id2)
                    all_affected.update(network2)
                
                # Queue components on all affected VNETs
                for vnet_id in all_affected:
                    vnet = self.vnets.get(vnet_id)
                    if vnet:
                        self.coordinator.queue_components_for_vnet(vnet)
        
        return bridge
    
    def get_bridges_for_component(self, component_id: str) -> list:
        """
        Get all bridges created by a component.
        
        Args:
            component_id: Component ID
            
        Returns:
            List of Bridge instances
        """
        return [b for b in self.bridges.values() if b.owner_component_id == component_id]
    
    def remove_bridges_for_component(self, component_id: str):
        """
        Remove all bridges created by a component.
        
        Args:
            component_id: Component ID
        """
        bridge_ids = [bid for bid, b in self.bridges.items() if b.owner_component_id == component_id]
        for bridge_id in bridge_ids:
            self.remove_bridge(bridge_id)  # Use remove_bridge to trigger component queuing
