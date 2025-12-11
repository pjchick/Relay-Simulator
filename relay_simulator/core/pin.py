"""
Pin class - Logical electrical connection with multiple physical tabs.
"""

from typing import Dict, TYPE_CHECKING
from core.state import PinState, combine_states
from core.tab import Tab

if TYPE_CHECKING:
    from components.base import Component


class Pin:
    """
    Pin represents a logical electrical connection point on a component.
    A pin can have multiple tabs (physical connection points).
    
    State propagation:
    - Any tab goes HIGH → Pin goes HIGH → All tabs go HIGH
    - Pin goes HIGH → All tabs go HIGH
    - State is read from PIN, not individual tabs
    """
    
    def __init__(self, pin_id: str, parent_component: 'Component'):
        """
        Initialize pin.
        
        Args:
            pin_id: Unique pin ID (hierarchical: PageId.CompId.PinId)
            parent_component: Component this pin belongs to
        """
        self.pin_id = pin_id
        self.parent_component = parent_component
        self.tabs: Dict[str, Tab] = {}
        self._state = PinState.FLOAT
    
    @property
    def state(self) -> PinState:
        """
        Get pin state.
        
        Returns:
            PinState: Current state
        """
        return self._state
    
    def set_state(self, new_state: PinState, source_tab: Tab = None):
        """
        Set pin state and propagate to all tabs.
        
        This can be called by:
        - A tab when it receives a signal from VNET
        - The component when updating its outputs
        
        Args:
            new_state: New state to set
            source_tab: Tab that initiated the change (if any)
        """
        old_state = self._state
        
        # Update pin state
        self._state = new_state
        
        # Propagate to all tabs (except source to avoid loop)
        for tab in self.tabs.values():
            if tab != source_tab:
                tab._state = new_state
        
        # If state changed, component might need to be notified
        # (handled by VNET system marking component dirty)
        return old_state != new_state
    
    def evaluate_state_from_tabs(self) -> PinState:
        """
        Evaluate pin state from all tab states using HIGH OR FLOAT logic.
        This is used when tabs are driven by VNETs.
        
        Returns:
            PinState: Combined state (HIGH if any tab is HIGH)
        """
        if not self.tabs:
            return PinState.FLOAT
        
        tab_states = [tab._state for tab in self.tabs.values()]
        combined = combine_states(*tab_states)
        
        # Update pin state if different
        if combined != self._state:
            self.set_state(combined)
        
        return combined
    
    def add_tab(self, tab: Tab):
        """
        Add a tab to this pin.
        
        Args:
            tab: Tab instance to add
        """
        self.tabs[tab.tab_id] = tab
        tab.parent_pin = self
        # Set tab state to match pin
        tab._state = self._state
    
    def remove_tab(self, tab_id: str):
        """
        Remove a tab from this pin.
        
        Args:
            tab_id: ID of tab to remove
        """
        if tab_id in self.tabs:
            del self.tabs[tab_id]
    
    def get_tab(self, tab_id: str) -> Tab:
        """
        Get tab by ID.
        
        Args:
            tab_id: Tab ID
            
        Returns:
            Tab: Tab instance or None
        """
        return self.tabs.get(tab_id)
    
    def to_dict(self) -> dict:
        """
        Serialize pin to dict (matches .rsim schema).
        
        Returns:
            dict: Pin data
        """
        return {
            'pin_id': self.pin_id,
            'tabs': [tab.to_dict() for tab in self.tabs.values()]
        }
    
    @staticmethod
    def from_dict(data: dict, parent_component: 'Component') -> 'Pin':
        """
        Deserialize pin from dict (matches .rsim schema).
        
        Args:
            data: Pin data dict
            parent_component: Parent component reference
            
        Returns:
            Pin: Reconstructed pin
        """
        pin = Pin(
            pin_id=data['pin_id'],
            parent_component=parent_component
        )
        
        # Reconstruct tabs (tabs is an array in schema)
        for tab_data in data.get('tabs', []):
            tab = Tab.from_dict(tab_data, pin)
            pin.add_tab(tab)
        
        return pin
    
    def __repr__(self):
        return f"Pin({self.pin_id}, tabs={len(self.tabs)}, state={self.state})"
