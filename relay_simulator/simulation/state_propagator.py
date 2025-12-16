"""
State Propagation System for Relay Logic Simulator

This module implements the state propagation logic that updates VNET states
and propagates those states to all connected tabs, pins, linked VNETs, and
bridged VNETs.

The propagator:
1. Updates the VNET's state to the new value
2. Propagates state to all tabs in the VNET
3. Updates pins associated with those tabs
4. Propagates to linked VNETs (cross-page connections)
5. Propagates to bridged VNETs (relay connections)
6. Marks affected VNETs dirty for re-evaluation
7. Prevents infinite loops in circular networks

This is a critical part of the simulation engine that runs after state
evaluation to ensure electrical continuity across the entire circuit.
"""

from typing import Dict, Set, Optional
from core.state import PinState
from core.vnet import VNET
from core.tab import Tab
from core.bridge import Bridge


class StatePropagator:
    """
    Propagates electrical states through VNETs and connected networks.
    
    The propagator ensures that when a VNET's state changes, that change
    is reflected throughout the entire electrical network:
    - All tabs in the VNET are updated
    - Pins associated with those tabs are updated
    - Linked VNETs (same link name) are propagated to
    - Bridged VNETs (relay connections) are propagated to
    
    The propagator uses a visited set to prevent infinite loops when
    dealing with circular link or bridge connections.
    """
    
    def __init__(
        self,
        all_vnets: Dict[str, VNET],
        all_tabs: Dict[str, Tab],
        all_bridges: Dict[str, Bridge]
    ):
        """
        Initialize the state propagator.
        
        Args:
            all_vnets: Dictionary mapping vnet_id -> VNET object
            all_tabs: Dictionary mapping tab_id -> Tab object
            all_bridges: Dictionary mapping bridge_id -> Bridge object
        """
        self.all_vnets = all_vnets
        self.all_tabs = all_tabs
        self.all_bridges = all_bridges
    
    def propagate_vnet_state(self, vnet: VNET, new_state: PinState, include_bridges: bool = True) -> Set[str]:
        """
        Propagate a new state to a VNET and all connected networks.
        
        This is the main entry point for state propagation. It updates the
        VNET's state and propagates to all connected tabs, pins, links, and bridges.
        
        Args:
            vnet: The VNET to update
            new_state: The new state to propagate
            
        Returns:
            Set of VNET IDs that were affected by this propagation
            
        Note:
            This method handles circular connections automatically using a
            visited set to prevent infinite recursion.
        """
        # Track which VNETs we've already propagated to
        visited_vnets: Set[str] = set()
        affected_vnets: Set[str] = set()
        
        # Start recursive propagation
        self._propagate_recursive(vnet, new_state, visited_vnets, affected_vnets, include_bridges)
        
        return affected_vnets
    
    def _propagate_recursive(
        self,
        vnet: VNET,
        new_state: PinState,
        visited_vnets: Set[str],
        affected_vnets: Set[str],
        include_bridges: bool
    ):
        """
        Recursively propagate state through connected VNETs.
        
        Args:
            vnet: Current VNET to propagate to
            new_state: State to propagate
            visited_vnets: Set of VNET IDs already visited (prevents cycles)
            affected_vnets: Set to accumulate affected VNET IDs
        """
        # Prevent infinite recursion
        if vnet.vnet_id in visited_vnets:
            return
        
        visited_vnets.add(vnet.vnet_id)
        
        # Only propagate if state actually changed
        if vnet.state == new_state:
            return
        
        # Update VNET state
        vnet.state = new_state
        affected_vnets.add(vnet.vnet_id)
        
        # Propagate to all tabs in this VNET
        self._propagate_to_tabs(vnet, new_state)
        
        # Propagate to linked VNETs (cross-page connections)
        linked_vnets = self._find_linked_vnets(vnet)
        for linked_vnet in linked_vnets:
            self._propagate_recursive(linked_vnet, new_state, visited_vnets, affected_vnets, include_bridges)
        
        # Propagate to bridged VNETs (relay connections)
        # NOTE: Some engine modes resolve bridges separately to avoid oscillation.
        if include_bridges:
            bridged_vnets = self._find_bridged_vnets(vnet)
            for bridged_vnet in bridged_vnets:
                self._propagate_recursive(bridged_vnet, new_state, visited_vnets, affected_vnets, include_bridges)
    
    def _propagate_to_tabs(self, vnet: VNET, new_state: PinState):
        """
        Propagate state to all tabs in the VNET.
        
        NOTE: This does NOT update pin states. Pins drive VNETs, not the
        other way around. Passive components should read VNET states via
        tab.state property (which reflects the VNET state).
        
        Args:
            vnet: VNET containing the tabs
            new_state: State to propagate
        """
        # VNET state is already updated in _propagate_recursive()
        # Tabs will automatically reflect this via their state property
        # which reads from the VNET through the parent pin
        # 
        # We don't update pin._state here because:
        # 1. Active components set their pin states, which drive VNETs
        # 2. Passive components read VNET states through tab.state
        # 3. Updating pin._state here would create conflicts when a pin
        #    has multiple tabs in different VNETs
        pass
    
    def _find_linked_vnets(self, vnet: VNET) -> list[VNET]:
        """
        Find all VNETs that share link names with this VNET.
        
        Links enable cross-page connections. If two VNETs on different pages
        contain components with the same link name, they are electrically connected.
        
        Args:
            vnet: The VNET to check for links
            
        Returns:
            List of VNETs with matching link names
        """
        linked_vnets = []
        
        # Get all link names from this VNET
        link_names = vnet.link_names.copy()
        
        # For each link name, find all other VNETs with the same link
        for link_name in link_names:
            for other_vnet_id, other_vnet in self.all_vnets.items():
                # Skip self
                if other_vnet_id == vnet.vnet_id:
                    continue
                
                # Check if other VNET has this link name
                if other_vnet.has_link(link_name):
                    linked_vnets.append(other_vnet)
        
        return linked_vnets
    
    def _find_bridged_vnets(self, vnet: VNET) -> list[VNET]:
        """
        Find all VNETs connected to this VNET via bridges.
        
        Bridges are dynamic connections created by components (like relays)
        to electrically connect two VNETs during simulation.
        
        Args:
            vnet: The VNET to check for bridges
            
        Returns:
            List of VNETs connected via bridges
        """
        bridged_vnets = []
        
        # Get all bridge IDs from this VNET
        bridge_ids = vnet.bridge_ids.copy()
        
        # For each bridge, get the other connected VNET
        for bridge_id in bridge_ids:
            bridge = self.all_bridges.get(bridge_id)
            if not bridge:
                continue
            
            # Get the VNET on the other side of the bridge
            other_vnet_id = bridge.get_other_vnet(vnet.vnet_id)
            if not other_vnet_id:
                continue
            
            # Get the other VNET
            other_vnet = self.all_vnets.get(other_vnet_id)
            if other_vnet:
                bridged_vnets.append(other_vnet)
        
        return bridged_vnets
    
    def propagate_multiple_vnets(
        self,
        vnet_states: Dict[str, PinState]
    ) -> Set[str]:
        """
        Propagate states to multiple VNETs in batch.
        
        This is a convenience method for batch propagation, useful in the
        simulation engine's main loop.
        
        Args:
            vnet_states: Dictionary mapping vnet_id -> new PinState
            
        Returns:
            Set of all VNET IDs affected by propagation
        """
        all_affected = set()
        
        for vnet_id, new_state in vnet_states.items():
            vnet = self.all_vnets.get(vnet_id)
            if vnet:
                affected = self.propagate_vnet_state(vnet, new_state)
                all_affected.update(affected)
        
        return all_affected
    
    def mark_affected_vnets_dirty(self, affected_vnet_ids: Set[str]):
        """
        Mark all affected VNETs as dirty for re-evaluation.
        
        This is typically called after propagation to ensure the simulation
        engine knows which VNETs need to be re-evaluated in the next iteration.
        
        Args:
            affected_vnet_ids: Set of VNET IDs to mark dirty
        """
        for vnet_id in affected_vnet_ids:
            vnet = self.all_vnets.get(vnet_id)
            if vnet:
                vnet.mark_dirty()
    
    def get_propagation_chain(self, vnet: VNET) -> Set[str]:
        """
        Get all VNET IDs that would be affected by propagating to this VNET.
        
        This is useful for understanding the propagation scope without
        actually performing the propagation. It returns all VNETs that are
        electrically connected via links and bridges.
        
        Args:
            vnet: The starting VNET
            
        Returns:
            Set of VNET IDs in the propagation chain
        """
        chain = set()
        visited = set()
        
        self._collect_propagation_chain(vnet, chain, visited)
        
        return chain
    
    def _collect_propagation_chain(
        self,
        vnet: VNET,
        chain: Set[str],
        visited: Set[str]
    ):
        """
        Recursively collect all VNETs in the propagation chain.
        
        Args:
            vnet: Current VNET
            chain: Set to accumulate VNET IDs
            visited: Set to prevent infinite recursion
        """
        if vnet.vnet_id in visited:
            return
        
        visited.add(vnet.vnet_id)
        chain.add(vnet.vnet_id)
        
        # Add linked VNETs
        linked_vnets = self._find_linked_vnets(vnet)
        for linked_vnet in linked_vnets:
            self._collect_propagation_chain(linked_vnet, chain, visited)
        
        # Add bridged VNETs
        bridged_vnets = self._find_bridged_vnets(vnet)
        for bridged_vnet in bridged_vnets:
            self._collect_propagation_chain(bridged_vnet, chain, visited)
