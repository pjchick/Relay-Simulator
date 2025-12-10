"""
Bridge System for Relay Logic Simulator

This module implements the bridge system that allows components (like relays) to
dynamically connect and disconnect VNETs during simulation.

Bridges are runtime-only constructs (not saved to file) that connect two VNETs,
allowing electrical continuity across the bridge. When a component creates a bridge,
the two VNETs become electrically connected and their states must be synchronized.

Key concepts:
- Bridge: Connects two VNETs, owned by a component
- BridgeManager: Manages all bridges in the simulation
- VNETs track which bridges reference them
- Bridges mark VNETs dirty when created/removed
"""

from typing import Optional, Dict, List, Set
from threading import RLock
import uuid


class Bridge:
    """
    Represents a dynamic electrical connection between two VNETs.
    
    Bridges are created by components (like relays) to connect different
    electrical networks. They are runtime-only and not persisted to file.
    
    Attributes:
        bridge_id: Unique identifier (8 char UUID, runtime only)
        vnet_id1: ID of first connected VNET
        vnet_id2: ID of second connected VNET
        owner_component_id: ID of component that owns this bridge
    """
    
    def __init__(
        self,
        vnet_id1: str,
        vnet_id2: str,
        owner_component_id: str,
        bridge_id: Optional[str] = None
    ):
        """
        Create a new bridge between two VNETs.
        
        Args:
            vnet_id1: ID of first VNET to connect
            vnet_id2: ID of second VNET to connect
            owner_component_id: ID of component creating this bridge
            bridge_id: Optional bridge ID (generated if not provided)
        
        Raises:
            ValueError: If vnet_id1 and vnet_id2 are the same
        """
        if vnet_id1 == vnet_id2:
            raise ValueError(f"Cannot bridge VNET to itself: {vnet_id1}")
        
        self.bridge_id = bridge_id or str(uuid.uuid4())[:8]
        self.vnet_id1 = vnet_id1
        self.vnet_id2 = vnet_id2
        self.owner_component_id = owner_component_id
    
    def get_connected_vnets(self) -> tuple[str, str]:
        """
        Get the IDs of both connected VNETs.
        
        Returns:
            Tuple of (vnet_id1, vnet_id2)
        """
        return (self.vnet_id1, self.vnet_id2)
    
    def get_other_vnet(self, vnet_id: str) -> Optional[str]:
        """
        Get the ID of the VNET on the other side of this bridge.
        
        Args:
            vnet_id: ID of one VNET
            
        Returns:
            ID of the other VNET, or None if vnet_id not in this bridge
        """
        if vnet_id == self.vnet_id1:
            return self.vnet_id2
        elif vnet_id == self.vnet_id2:
            return self.vnet_id1
        else:
            return None
    
    def contains_vnet(self, vnet_id: str) -> bool:
        """
        Check if this bridge connects to the given VNET.
        
        Args:
            vnet_id: VNET ID to check
            
        Returns:
            True if this bridge connects to the VNET
        """
        return vnet_id == self.vnet_id1 or vnet_id == self.vnet_id2
    
    def __repr__(self) -> str:
        return (f"Bridge({self.bridge_id}: {self.vnet_id1}↔{self.vnet_id2}, "
                f"owner={self.owner_component_id})")


class BridgeManager:
    """
    Manages all bridges in the simulation.
    
    The BridgeManager is responsible for:
    - Creating and tracking bridges
    - Removing bridges
    - Looking up bridges by ID
    - Finding bridges connected to a VNET
    - Thread-safe operations
    
    This class works with the VNET class to maintain bidirectional references:
    - Bridges know which VNETs they connect
    - VNETs know which bridges reference them
    """
    
    def __init__(self):
        """Initialize the bridge manager."""
        self._bridges: Dict[str, Bridge] = {}
        self._vnet_to_bridges: Dict[str, Set[str]] = {}  # vnet_id -> set of bridge_ids
        self._lock = RLock()
    
    def create_bridge(
        self,
        vnet_id1: str,
        vnet_id2: str,
        owner_component_id: str,
        bridge_id: Optional[str] = None
    ) -> Bridge:
        """
        Create a new bridge between two VNETs.
        
        This method:
        1. Creates the bridge object
        2. Registers it in the manager
        3. Updates VNET-to-bridge mappings
        4. Returns the bridge (caller must add to VNETs and mark them dirty)
        
        Args:
            vnet_id1: ID of first VNET
            vnet_id2: ID of second VNET
            owner_component_id: ID of owning component
            bridge_id: Optional bridge ID
            
        Returns:
            The created Bridge object
            
        Raises:
            ValueError: If bridge already exists with same ID
        """
        with self._lock:
            bridge = Bridge(vnet_id1, vnet_id2, owner_component_id, bridge_id)
            
            if bridge.bridge_id in self._bridges:
                raise ValueError(f"Bridge already exists: {bridge.bridge_id}")
            
            # Register bridge
            self._bridges[bridge.bridge_id] = bridge
            
            # Update VNET mappings
            if vnet_id1 not in self._vnet_to_bridges:
                self._vnet_to_bridges[vnet_id1] = set()
            if vnet_id2 not in self._vnet_to_bridges:
                self._vnet_to_bridges[vnet_id2] = set()
            
            self._vnet_to_bridges[vnet_id1].add(bridge.bridge_id)
            self._vnet_to_bridges[vnet_id2].add(bridge.bridge_id)
            
            return bridge
    
    def remove_bridge(self, bridge_id: str) -> Optional[Bridge]:
        """
        Remove a bridge from the manager.
        
        This removes the bridge from internal tracking. The caller is responsible
        for removing bridge references from VNETs and marking them dirty.
        
        Args:
            bridge_id: ID of bridge to remove
            
        Returns:
            The removed Bridge object, or None if not found
        """
        with self._lock:
            bridge = self._bridges.pop(bridge_id, None)
            
            if bridge:
                # Remove from VNET mappings
                if bridge.vnet_id1 in self._vnet_to_bridges:
                    self._vnet_to_bridges[bridge.vnet_id1].discard(bridge_id)
                    if not self._vnet_to_bridges[bridge.vnet_id1]:
                        del self._vnet_to_bridges[bridge.vnet_id1]
                
                if bridge.vnet_id2 in self._vnet_to_bridges:
                    self._vnet_to_bridges[bridge.vnet_id2].discard(bridge_id)
                    if not self._vnet_to_bridges[bridge.vnet_id2]:
                        del self._vnet_to_bridges[bridge.vnet_id2]
            
            return bridge
    
    def get_bridge(self, bridge_id: str) -> Optional[Bridge]:
        """
        Get a bridge by ID.
        
        Args:
            bridge_id: Bridge ID to look up
            
        Returns:
            Bridge object or None if not found
        """
        with self._lock:
            return self._bridges.get(bridge_id)
    
    def get_bridges_for_vnet(self, vnet_id: str) -> List[Bridge]:
        """
        Get all bridges connected to a VNET.
        
        Args:
            vnet_id: VNET ID
            
        Returns:
            List of Bridge objects (empty if none)
        """
        with self._lock:
            bridge_ids = self._vnet_to_bridges.get(vnet_id, set())
            return [self._bridges[bid] for bid in bridge_ids if bid in self._bridges]
    
    def get_bridges_for_component(self, component_id: str) -> List[Bridge]:
        """
        Get all bridges owned by a component.
        
        Args:
            component_id: Component ID
            
        Returns:
            List of Bridge objects owned by this component
        """
        with self._lock:
            return [b for b in self._bridges.values() if b.owner_component_id == component_id]
    
    def get_all_bridges(self) -> List[Bridge]:
        """
        Get all bridges in the manager.
        
        Returns:
            List of all Bridge objects
        """
        with self._lock:
            return list(self._bridges.values())
    
    def get_bridge_count(self) -> int:
        """
        Get total number of bridges.
        
        Returns:
            Number of bridges
        """
        with self._lock:
            return len(self._bridges)
    
    def clear_bridges_for_component(self, component_id: str) -> List[Bridge]:
        """
        Remove all bridges owned by a component.
        
        Useful when a component is removed or simulation stops.
        
        Args:
            component_id: Component ID
            
        Returns:
            List of removed Bridge objects
        """
        with self._lock:
            component_bridges = self.get_bridges_for_component(component_id)
            for bridge in component_bridges:
                self.remove_bridge(bridge.bridge_id)
            return component_bridges
    
    def clear_all_bridges(self):
        """
        Remove all bridges from the manager.
        
        Used when simulation stops or is reset.
        """
        with self._lock:
            self._bridges.clear()
            self._vnet_to_bridges.clear()
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about bridges.
        
        Returns:
            Dict with bridge statistics
        """
        with self._lock:
            vnets_with_bridges = len(self._vnet_to_bridges)
            total_bridges = len(self._bridges)
            
            # Count components with bridges
            components = set(b.owner_component_id for b in self._bridges.values())
            
            return {
                'total_bridges': total_bridges,
                'vnets_with_bridges': vnets_with_bridges,
                'components_with_bridges': len(components)
            }
    
    def __repr__(self) -> str:
        stats = self.get_statistics()
        return (f"BridgeManager({stats['total_bridges']} bridges, "
                f"{stats['vnets_with_bridges']} VNETs, "
                f"{stats['components_with_bridges']} components)")
