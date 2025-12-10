"""
VNET (Virtual Network) Class for Relay Logic Simulator

A VNET represents a collection of electrically connected tabs that share the same
signal state. VNETs are created by the VNET builder algorithm which traverses wire
connections to group connected tabs together.

VNETs handle:
- State evaluation (HIGH OR logic from all connected tabs)
- Cross-page connections via link names
- Bridge connections for advanced routing
- Dirty flag optimization for simulation
- Thread-safe state updates
"""

import threading
from typing import Set, Optional, List
from core.state import PinState, combine_states


class VNET:
    """
    Virtual Network - A collection of electrically connected tabs.
    
    VNETs are the fundamental unit of electrical connectivity in the simulator.
    All tabs in a VNET share the same electrical state, which is determined by
    combining the states of all connected tabs using HIGH OR logic.
    
    Attributes:
        vnet_id: Unique 8-character identifier
        tab_ids: Set of tab IDs in this network
        link_names: Set of link names for cross-page connections
        bridge_ids: Set of bridge IDs for advanced routing
        state: Current electrical state (HIGH or FLOAT)
        dirty: Flag indicating state needs re-evaluation
        page_id: Page ID for single-page VNETs (None for cross-page)
    """
    
    def __init__(self, vnet_id: str, page_id: Optional[str] = None):
        """
        Initialize a VNET.
        
        Args:
            vnet_id: Unique 8-character identifier for this VNET
            page_id: Optional page ID for single-page VNETs
        """
        self.vnet_id = vnet_id
        self.page_id = page_id
        
        # Collections
        self.tab_ids: Set[str] = set()
        self.link_names: Set[str] = set()
        self.bridge_ids: Set[str] = set()
        
        # State management
        self._state = PinState.FLOAT
        self._dirty = True  # Start dirty to force initial evaluation
        
        # Thread safety
        self._lock = threading.RLock()  # Reentrant lock for nested calls
    
    @property
    def state(self) -> PinState:
        """
        Get current VNET state (thread-safe).
        
        Returns:
            Current PinState (HIGH or FLOAT)
        """
        with self._lock:
            return self._state
    
    @state.setter
    def state(self, value: PinState):
        """
        Set VNET state (thread-safe).
        
        Args:
            value: New PinState value
        """
        with self._lock:
            if self._state != value:
                self._state = value
                self._dirty = True
    
    def add_tab(self, tab_id: str) -> bool:
        """
        Add a tab to this VNET (thread-safe).
        
        Args:
            tab_id: ID of tab to add
            
        Returns:
            True if tab was added, False if already exists
        """
        with self._lock:
            if tab_id in self.tab_ids:
                return False
            
            self.tab_ids.add(tab_id)
            self._dirty = True  # State needs re-evaluation
            return True
    
    def remove_tab(self, tab_id: str) -> bool:
        """
        Remove a tab from this VNET (thread-safe).
        
        Args:
            tab_id: ID of tab to remove
            
        Returns:
            True if tab was removed, False if not found
        """
        with self._lock:
            if tab_id not in self.tab_ids:
                return False
            
            self.tab_ids.remove(tab_id)
            self._dirty = True  # State needs re-evaluation
            return True
    
    def has_tab(self, tab_id: str) -> bool:
        """
        Check if VNET contains a tab (thread-safe).
        
        Args:
            tab_id: ID of tab to check
            
        Returns:
            True if tab is in this VNET
        """
        with self._lock:
            return tab_id in self.tab_ids
    
    def get_all_tabs(self) -> List[str]:
        """
        Get all tab IDs in this VNET (thread-safe).
        
        Returns:
            List of all tab IDs (copy to prevent external modification)
        """
        with self._lock:
            return list(self.tab_ids)
    
    def get_tab_count(self) -> int:
        """
        Get number of tabs in this VNET (thread-safe).
        
        Returns:
            Number of tabs
        """
        with self._lock:
            return len(self.tab_ids)
    
    def add_link(self, link_name: str) -> bool:
        """
        Add a link name to this VNET (thread-safe).
        
        Link names enable cross-page connections by linking VNETs
        that contain components with matching link names.
        
        Args:
            link_name: Link name to add
            
        Returns:
            True if link was added, False if already exists
        """
        with self._lock:
            if link_name in self.link_names:
                return False
            
            self.link_names.add(link_name)
            return True
    
    def remove_link(self, link_name: str) -> bool:
        """
        Remove a link name from this VNET (thread-safe).
        
        Args:
            link_name: Link name to remove
            
        Returns:
            True if link was removed, False if not found
        """
        with self._lock:
            if link_name not in self.link_names:
                return False
            
            self.link_names.remove(link_name)
            return True
    
    def has_link(self, link_name: str) -> bool:
        """
        Check if VNET has a link name (thread-safe).
        
        Args:
            link_name: Link name to check
            
        Returns:
            True if link name exists in this VNET
        """
        with self._lock:
            return link_name in self.link_names
    
    def get_all_links(self) -> List[str]:
        """
        Get all link names in this VNET (thread-safe).
        
        Returns:
            List of all link names (copy to prevent external modification)
        """
        with self._lock:
            return list(self.link_names)
    
    def add_bridge(self, bridge_id: str) -> bool:
        """
        Add a bridge ID to this VNET (thread-safe).
        
        Bridges are used for advanced routing scenarios. Adding a bridge
        marks the VNET dirty since it may affect state evaluation.
        
        Args:
            bridge_id: Bridge ID to add
            
        Returns:
            True if bridge was added, False if already exists
        """
        with self._lock:
            if bridge_id in self.bridge_ids:
                return False
            
            self.bridge_ids.add(bridge_id)
            self._dirty = True  # Mark dirty when bridge added
            return True
    
    def remove_bridge(self, bridge_id: str) -> bool:
        """
        Remove a bridge ID from this VNET (thread-safe).
        
        Removing a bridge marks the VNET dirty since it may affect
        state evaluation.
        
        Args:
            bridge_id: Bridge ID to remove
            
        Returns:
            True if bridge was removed, False if not found
        """
        with self._lock:
            if bridge_id not in self.bridge_ids:
                return False
            
            self.bridge_ids.remove(bridge_id)
            self._dirty = True  # Mark dirty when bridge removed
            return True
    
    def has_bridge(self, bridge_id: str) -> bool:
        """
        Check if VNET has a bridge ID (thread-safe).
        
        Args:
            bridge_id: Bridge ID to check
            
        Returns:
            True if bridge ID exists in this VNET
        """
        with self._lock:
            return bridge_id in self.bridge_ids
    
    def get_all_bridges(self) -> List[str]:
        """
        Get all bridge IDs in this VNET (thread-safe).
        
        Returns:
            List of all bridge IDs (copy to prevent external modification)
        """
        with self._lock:
            return list(self.bridge_ids)
    
    def evaluate_state(self, tab_states: dict) -> PinState:
        """
        Evaluate VNET state from tab states using HIGH OR logic (thread-safe).
        
        The VNET state is determined by combining all tab states:
        - If any tab is HIGH, VNET is HIGH
        - If all tabs are FLOAT, VNET is FLOAT
        
        Args:
            tab_states: Dictionary mapping tab_id -> PinState
            
        Returns:
            Evaluated PinState (HIGH or FLOAT)
        """
        with self._lock:
            result_state = PinState.FLOAT
            
            # Combine states from all tabs in this VNET
            for tab_id in self.tab_ids:
                if tab_id in tab_states:
                    result_state = combine_states(result_state, tab_states[tab_id])
            
            self._state = result_state
            return result_state
    
    def mark_dirty(self):
        """
        Mark VNET as dirty (needs re-evaluation) (thread-safe).
        
        Used by the simulation engine to track which VNETs need
        their state recalculated in the next simulation step.
        """
        with self._lock:
            self._dirty = True
    
    def clear_dirty(self):
        """
        Clear dirty flag (thread-safe).
        
        Called after VNET state has been evaluated.
        """
        with self._lock:
            self._dirty = False
    
    def is_dirty(self) -> bool:
        """
        Check if VNET is dirty (thread-safe).
        
        Returns:
            True if VNET needs re-evaluation
        """
        with self._lock:
            return self._dirty
    
    def to_dict(self) -> dict:
        """
        Serialize VNET to dictionary (thread-safe).
        
        Returns:
            Dictionary representation of VNET
        """
        with self._lock:
            return {
                'vnet_id': self.vnet_id,
                'page_id': self.page_id,
                'tab_ids': list(self.tab_ids),
                'link_names': list(self.link_names),
                'bridge_ids': list(self.bridge_ids),
                'state': self._state.value,
                'dirty': self._dirty
            }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VNET':
        """
        Deserialize VNET from dictionary.
        
        Args:
            data: Dictionary containing VNET data
            
        Returns:
            New VNET instance
        """
        vnet = cls(
            vnet_id=data['vnet_id'],
            page_id=data.get('page_id')
        )
        
        # Restore collections
        vnet.tab_ids = set(data.get('tab_ids', []))
        vnet.link_names = set(data.get('link_names', []))
        vnet.bridge_ids = set(data.get('bridge_ids', []))
        
        # Restore state
        vnet._state = PinState(data.get('state', PinState.FLOAT.value))
        vnet._dirty = data.get('dirty', True)
        
        return vnet
    
    def __repr__(self):
        """String representation of VNET."""
        with self._lock:
            state_str = "HIGH" if self._state == PinState.HIGH else "FLOAT"
            dirty_str = " (dirty)" if self._dirty else ""
            page_str = f" page={self.page_id}" if self.page_id else " cross-page"
            return f"VNET({self.vnet_id}: {len(self.tab_ids)} tabs, {state_str}{dirty_str},{page_str})"
