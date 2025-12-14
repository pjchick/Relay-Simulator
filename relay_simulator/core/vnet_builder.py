"""
VNET Builder for Relay Logic Simulator

This module implements the graph traversal algorithm that builds VNETs (Virtual Networks)
from wire connections on a page. The algorithm:

1. Identifies all tabs on components
2. Traverses wire connections to group electrically connected tabs
3. Handles junctions (wire branches) for complex networks
4. Creates VNETs containing all connected tabs
5. Handles disconnected tabs (single-tab VNETs)

The builder uses a depth-first search approach to traverse wire connections
and group all electrically connected tabs into VNETs.
"""

from typing import Dict, List, Set, Optional
from core.vnet import VNET
from core.page import Page
from core.wire import Wire, Junction
from core.id_manager import IDManager


class VnetBuilder:
    """
    Builds VNETs for a page by traversing wire connections.
    
    The VNET builder analyzes the wire topology on a page and groups
    electrically connected tabs into VNETs. It handles:
    - Simple point-to-point wires
    - Junction networks (multiple branches)
    - Nested junctions
    - Disconnected tabs
    - Circular wire paths (without infinite loops)
    """
    
    def __init__(self, id_manager: Optional[IDManager] = None):
        """
        Initialize VNET builder.
        
        Args:
            id_manager: Optional ID manager for generating VNET IDs
        """
        self.id_manager = id_manager or IDManager()
    
    def build_vnets_for_page(self, page: Page) -> List[VNET]:
        """
        Build all VNETs for a page.
        
        This is the main entry point for VNET building. It:
        1. Collects all tabs from components on the page
        2. Builds a wire connectivity map
        3. Traverses connections to group tabs into VNETs
        4. Creates single-tab VNETs for disconnected tabs
        
        Args:
            page: Page to build VNETs for
            
        Returns:
            List of all VNETs on the page
        """
        # Collect all tabs from all components
        all_tabs = self._collect_all_tabs(page)
        
        # Build wire connectivity map
        connectivity = self._build_connectivity_map(page)
        
        # Track processed tabs
        processed_tabs: Set[str] = set()
        
        # Build VNETs
        vnets: List[VNET] = []
        
        # Process each unprocessed tab
        for tab_id in all_tabs:
            if tab_id not in processed_tabs:
                # Find all tabs connected to this tab
                connected_tabs = self._find_connected_tabs(tab_id, connectivity, processed_tabs)
                
                # Create VNET with all connected tabs
                vnet = self._create_vnet(page.page_id, connected_tabs)
                vnets.append(vnet)
        
        return vnets
    
    def _collect_all_tabs(self, page: Page) -> Set[str]:
        """
        Collect all tab IDs from all components on the page.
        
        Args:
            page: Page to collect tabs from
            
        Returns:
            Set of all tab IDs on the page
        """
        all_tabs: Set[str] = set()
        
        for component in page.get_all_components():
            # get_all_pins() returns dict, iterate over values
            for pin in component.get_all_pins().values():
                # tabs is a dict, iterate over values
                for tab in pin.tabs.values():
                    all_tabs.add(tab.tab_id)
        
        return all_tabs
    
    def _build_connectivity_map(self, page: Page) -> Dict[str, Set[str]]:
        """
        Build a connectivity map from wires and pin connections.
        
        The connectivity map is a dictionary where:
        - Key: tab_id
        - Value: Set of tab_ids directly connected by wires OR same pin
        
        This handles:
        - Simple wires (start_tab → end_tab)
        - Junctions (start_tab → multiple end_tabs)
        - Nested junctions (recursive)
        - Tabs of the same pin (electrically connected)
        
        Args:
            page: Page containing wires
            
        Returns:
            Connectivity map (tab_id -> set of connected tab_ids)
        """
        connectivity: Dict[str, Set[str]] = {}
        
        # First, add implicit connections for tabs of the same pin
        # All tabs on the same pin are electrically connected
        for component in page.get_all_components():
            for pin in component.get_all_pins().values():
                # Get all tab IDs for this pin
                tab_ids = list(pin.tabs.keys())
                
                # Connect all tabs to each other (they're on the same pin)
                for i, tab1 in enumerate(tab_ids):
                    if tab1 not in connectivity:
                        connectivity[tab1] = set()
                    
                    for j, tab2 in enumerate(tab_ids):
                        if i != j:
                            connectivity[tab1].add(tab2)
        
        # Create a global visited set to prevent infinite recursion across all wires
        visited_wires: Set[str] = set()
        
        # Then, process all wires on the page
        for wire in page.get_all_wires():
            self._add_wire_to_connectivity(wire, connectivity, visited_wires)
        
        return connectivity
    
    def _add_wire_to_connectivity(self, wire: Wire, connectivity: Dict[str, Set[str]], visited: Set[str]):
        """
        Add a wire's connections to the connectivity map.
        
        This recursively handles:
        - Direct connections (start → end)
        - Junctions (start → all child wire endpoints)
        - Nested junctions
        
        Args:
            wire: Wire to process
            connectivity: Connectivity map to update
            visited: Set of already-visited wire IDs (prevents infinite recursion)
        """
        # Get all tabs connected by this wire (including through junctions)
        all_wire_tabs = self._get_all_wire_tabs(wire, visited)
        
        # Add bidirectional connections between all tabs
        for tab1 in all_wire_tabs:
            if tab1 not in connectivity:
                connectivity[tab1] = set()
            
            for tab2 in all_wire_tabs:
                if tab1 != tab2:
                    connectivity[tab1].add(tab2)
    
    def _get_all_wire_tabs(self, wire: Wire, visited: Set[str] = None) -> Set[str]:
        """
        Get all tab IDs connected by a wire, including through junctions.
        
        This recursively traverses junctions to find all connected tabs.
        
        Args:
            wire: Wire to analyze
            visited: Set of already-visited wire IDs to prevent infinite recursion
            
        Returns:
            Set of all tab IDs connected by this wire
        """
        if visited is None:
            visited = set()
        
        # Prevent infinite recursion on circular wire paths
        if wire.wire_id in visited:
            return set()
        
        visited.add(wire.wire_id)
        
        tabs: Set[str] = set()
        
        # Add start tab (could be tab_id or junction_id)
        tabs.add(wire.start_tab_id)
        
        # Add end tab if present (could be tab_id or junction_id)
        if wire.end_tab_id:
            tabs.add(wire.end_tab_id)
        
        # Recursively add tabs from child wires in junctions
        for junction in wire.get_all_junctions():
            for child_wire in junction.get_all_child_wires():
                tabs.update(self._get_all_wire_tabs(child_wire, visited))
        
        return tabs
    
    def _find_connected_tabs(
        self,
        start_tab_id: str,
        connectivity: Dict[str, Set[str]],
        processed_tabs: Set[str]
    ) -> Set[str]:
        """
        Find all tabs connected to a starting tab using depth-first search.
        
        This performs a graph traversal to find all tabs that are electrically
        connected through wires. It:
        - Starts from start_tab_id
        - Follows all wire connections
        - Marks tabs as processed to avoid revisiting
        - Handles circular paths without infinite loops
        
        Args:
            start_tab_id: Tab to start search from
            connectivity: Wire connectivity map
            processed_tabs: Set to track processed tabs (modified in-place)
            
        Returns:
            Set of all tabs connected to start_tab_id
        """
        connected: Set[str] = set()
        to_process: List[str] = [start_tab_id]
        
        while to_process:
            current_tab = to_process.pop()
            
            # Skip if already processed
            if current_tab in processed_tabs:
                continue
            
            # Mark as processed and add to connected set
            processed_tabs.add(current_tab)
            connected.add(current_tab)
            
            # Add all connected tabs to the processing queue
            if current_tab in connectivity:
                for neighbor_tab in connectivity[current_tab]:
                    if neighbor_tab not in processed_tabs:
                        to_process.append(neighbor_tab)
        
        return connected
    
    def _create_vnet(self, page_id: str, tab_ids: Set[str]) -> VNET:
        """
        Create a VNET with the given tab IDs.
        
        Args:
            page_id: Page ID for single-page VNETs
            tab_ids: Set of tab IDs to include in VNET
            
        Returns:
            New VNET instance
        """
        # Generate VNET ID
        vnet_id = self.id_manager.generate_id()
        
        # Create VNET
        vnet = VNET(vnet_id, page_id)
        
        # Add all tabs
        for tab_id in tab_ids:
            vnet.add_tab(tab_id)
        
        return vnet


class VnetBuilderStats:
    """
    Statistics from VNET building process.
    
    Useful for debugging and performance analysis.
    """
    
    def __init__(self):
        self.total_vnets = 0
        self.single_tab_vnets = 0
        self.multi_tab_vnets = 0
        self.largest_vnet_size = 0
        self.total_tabs = 0
    
    def analyze_vnets(self, vnets: List[VNET]) -> 'VnetBuilderStats':
        """
        Analyze a list of VNETs and populate statistics.
        
        Args:
            vnets: List of VNETs to analyze
            
        Returns:
            Self (for chaining)
        """
        self.total_vnets = len(vnets)
        
        for vnet in vnets:
            tab_count = vnet.get_tab_count()
            self.total_tabs += tab_count
            
            if tab_count == 1:
                self.single_tab_vnets += 1
            else:
                self.multi_tab_vnets += 1
            
            if tab_count > self.largest_vnet_size:
                self.largest_vnet_size = tab_count
        
        return self
    
    def __repr__(self):
        return (f"VnetBuilderStats(total_vnets={self.total_vnets}, "
                f"single_tab={self.single_tab_vnets}, "
                f"multi_tab={self.multi_tab_vnets}, "
                f"largest={self.largest_vnet_size}, "
                f"total_tabs={self.total_tabs})")
