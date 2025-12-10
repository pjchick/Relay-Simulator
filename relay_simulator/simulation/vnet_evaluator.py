"""
VNET State Evaluator for Relay Logic Simulator

This module implements the VNET state evaluation logic that determines the electrical
state of a VNET based on all connected tabs, links, and bridges.

The evaluator:
1. Collects states from all tabs in the VNET
2. Collects states from linked VNETs (cross-page connections)
3. Collects states from bridged VNETs (relay connections)
4. Applies HIGH OR FLOAT logic to determine final state
5. Returns the computed state

This is a critical part of the simulation engine that runs during each
simulation iteration to determine electrical connectivity.
"""

from typing import Dict, Set, Optional
from core.state import PinState, combine_states
from core.vnet import VNET
from core.tab import Tab
from core.bridge import Bridge


class VnetEvaluator:
    """
    Evaluates the electrical state of VNETs during simulation.
    
    The evaluator determines the state of a VNET by examining:
    - All tabs in the VNET (reading their pin states)
    - All linked VNETs (cross-page connections via link names)
    - All bridged VNETs (dynamic connections via relay bridges)
    
    The final state is computed using HIGH OR logic:
    - If ANY input is HIGH, the result is HIGH
    - Otherwise, the result is FLOAT
    
    This class is designed to be used by the simulation engine's main loop.
    """
    
    def __init__(
        self,
        all_vnets: Dict[str, VNET],
        all_tabs: Dict[str, Tab],
        all_bridges: Dict[str, Bridge]
    ):
        """
        Initialize the VNET evaluator.
        
        Args:
            all_vnets: Dictionary mapping vnet_id -> VNET object
            all_tabs: Dictionary mapping tab_id -> Tab object
            all_bridges: Dictionary mapping bridge_id -> Bridge object
        """
        self.all_vnets = all_vnets
        self.all_tabs = all_tabs
        self.all_bridges = all_bridges
    
    def evaluate_vnet_state(self, vnet: VNET) -> PinState:
        """
        Evaluate and return the electrical state of a VNET.
        
        This is the main entry point for VNET evaluation. It collects states
        from all sources (tabs, links, bridges) and combines them using
        HIGH OR logic.
        
        Args:
            vnet: The VNET to evaluate
            
        Returns:
            PinState: The computed state (HIGH or FLOAT)
            
        Note:
            This method does NOT update the VNET's state - it only computes
            and returns what the state should be. The caller is responsible
            for updating the VNET state if needed.
        """
        # Track visited VNETs to prevent infinite recursion from circular links/bridges
        visited_vnets: Set[str] = set()
        
        return self._evaluate_recursive(vnet, visited_vnets)
    
    def _evaluate_recursive(self, vnet: VNET, visited_vnets: Set[str]) -> PinState:
        """
        Recursively evaluate VNET state, handling links and bridges.
        
        Args:
            vnet: The VNET to evaluate
            visited_vnets: Set of VNET IDs already visited (prevents cycles)
            
        Returns:
            PinState: The computed state
        """
        # Prevent infinite recursion
        if vnet.vnet_id in visited_vnets:
            return PinState.FLOAT
        
        visited_vnets.add(vnet.vnet_id)
        
        # Start with FLOAT (neutral state)
        result_state = PinState.FLOAT
        
        # 1. Read all tab states in this VNET
        tab_states = self._read_tab_states(vnet)
        for tab_state in tab_states:
            result_state = combine_states(result_state, tab_state)
            if result_state == PinState.HIGH:
                # Short-circuit: if we find HIGH, no need to check more
                return PinState.HIGH
        
        # 2. Get states from linked VNETs (cross-page connections)
        linked_states = self._read_linked_vnet_states(vnet, visited_vnets)
        for linked_state in linked_states:
            result_state = combine_states(result_state, linked_state)
            if result_state == PinState.HIGH:
                return PinState.HIGH
        
        # 3. Get states from bridged VNETs (relay connections)
        bridged_states = self._read_bridged_vnet_states(vnet, visited_vnets)
        for bridged_state in bridged_states:
            result_state = combine_states(result_state, bridged_state)
            if result_state == PinState.HIGH:
                return PinState.HIGH
        
        return result_state
    
    def _read_tab_states(self, vnet: VNET) -> list[PinState]:
        """
        Read the states of all tabs in the VNET.
        
        Args:
            vnet: The VNET containing the tabs
            
        Returns:
            List of PinState values from all tabs
        """
        states = []
        
        for tab_id in vnet.get_all_tabs():
            tab = self.all_tabs.get(tab_id)
            if tab:
                # Tab state reflects its parent pin state
                states.append(tab.state)
        
        return states
    
    def _read_linked_vnet_states(
        self,
        vnet: VNET,
        visited_vnets: Set[str]
    ) -> list[PinState]:
        """
        Read states from all VNETs that share link names with this VNET.
        
        Links enable cross-page connections. If two VNETs on different pages
        contain components with the same link name, they are electrically connected.
        
        Args:
            vnet: The VNET to check for links
            visited_vnets: Set of already-visited VNETs (prevents cycles)
            
        Returns:
            List of PinState values from linked VNETs
        """
        states = []
        
        # Get all link names from this VNET
        link_names = vnet.link_names.copy()  # Copy to avoid iteration issues
        
        # For each link name, find all other VNETs with the same link
        for link_name in link_names:
            for other_vnet_id, other_vnet in self.all_vnets.items():
                # Skip self and already-visited VNETs
                if other_vnet_id == vnet.vnet_id:
                    continue
                if other_vnet_id in visited_vnets:
                    continue
                
                # Check if other VNET has this link name
                if other_vnet.has_link(link_name):
                    # Recursively evaluate the linked VNET
                    linked_state = self._evaluate_recursive(other_vnet, visited_vnets)
                    states.append(linked_state)
        
        return states
    
    def _read_bridged_vnet_states(
        self,
        vnet: VNET,
        visited_vnets: Set[str]
    ) -> list[PinState]:
        """
        Read states from all VNETs connected to this VNET via bridges.
        
        Bridges are dynamic connections created by components (like relays)
        to electrically connect two VNETs during simulation.
        
        Args:
            vnet: The VNET to check for bridges
            visited_vnets: Set of already-visited VNETs (prevents cycles)
            
        Returns:
            List of PinState values from bridged VNETs
        """
        states = []
        
        # Get all bridge IDs from this VNET
        bridge_ids = vnet.bridge_ids.copy()  # Copy to avoid iteration issues
        
        # For each bridge, get the other connected VNET
        for bridge_id in bridge_ids:
            bridge = self.all_bridges.get(bridge_id)
            if not bridge:
                continue
            
            # Get the VNET on the other side of the bridge
            other_vnet_id = bridge.get_other_vnet(vnet.vnet_id)
            if not other_vnet_id:
                continue
            
            # Skip if already visited
            if other_vnet_id in visited_vnets:
                continue
            
            # Get the other VNET
            other_vnet = self.all_vnets.get(other_vnet_id)
            if not other_vnet:
                continue
            
            # Recursively evaluate the bridged VNET
            bridged_state = self._evaluate_recursive(other_vnet, visited_vnets)
            states.append(bridged_state)
        
        return states
    
    def evaluate_multiple_vnets(self, vnets: list[VNET]) -> Dict[str, PinState]:
        """
        Evaluate multiple VNETs and return their states.
        
        This is a convenience method for batch evaluation, useful in the
        simulation engine's main loop.
        
        Args:
            vnets: List of VNETs to evaluate
            
        Returns:
            Dictionary mapping vnet_id -> computed PinState
        """
        results = {}
        
        for vnet in vnets:
            computed_state = self.evaluate_vnet_state(vnet)
            results[vnet.vnet_id] = computed_state
        
        return results
    
    def get_all_connected_vnets(self, vnet: VNET) -> Set[str]:
        """
        Get all VNET IDs that are electrically connected to this VNET.
        
        This includes VNETs connected via:
        - Links (same link name)
        - Bridges (relay connections)
        
        This method is useful for understanding the electrical network topology.
        
        Args:
            vnet: The VNET to analyze
            
        Returns:
            Set of VNET IDs connected to this VNET (including the VNET itself)
        """
        connected = set()
        visited = set()
        
        self._collect_connected_vnets(vnet, connected, visited)
        
        return connected
    
    def _collect_connected_vnets(
        self,
        vnet: VNET,
        connected: Set[str],
        visited: Set[str]
    ):
        """
        Recursively collect all connected VNET IDs.
        
        Args:
            vnet: Current VNET to process
            connected: Set to accumulate connected VNET IDs
            visited: Set to prevent infinite recursion
        """
        if vnet.vnet_id in visited:
            return
        
        visited.add(vnet.vnet_id)
        connected.add(vnet.vnet_id)
        
        # Check links
        for link_name in vnet.link_names:
            for other_vnet_id, other_vnet in self.all_vnets.items():
                if other_vnet_id != vnet.vnet_id and other_vnet.has_link(link_name):
                    self._collect_connected_vnets(other_vnet, connected, visited)
        
        # Check bridges
        for bridge_id in vnet.bridge_ids:
            bridge = self.all_bridges.get(bridge_id)
            if bridge:
                other_vnet_id = bridge.get_other_vnet(vnet.vnet_id)
                if other_vnet_id:
                    other_vnet = self.all_vnets.get(other_vnet_id)
                    if other_vnet:
                        self._collect_connected_vnets(other_vnet, connected, visited)
