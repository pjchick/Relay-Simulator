"""
VNET Manager - Interface for components to interact with VNETs

This provides a simplified interface for components to:
- Mark VNETs dirty when pin states change
- Read VNET states
- Query which VNET a tab belongs to
"""

from typing import Dict, Optional
from core.vnet import VNET
from core.tab import Tab
from simulation.dirty_flag_manager import DirtyFlagManager


class VnetManager:
    """
    Manager class for VNET operations during simulation.
    
    Provides components with methods to:
    - Mark VNETs dirty when pin states change
    - Get VNET state for a tab
    - Find which VNET contains a tab
    """
    
    def __init__(self, vnets: Dict[str, VNET], tabs: Dict[str, Tab], dirty_manager: DirtyFlagManager):
        """
        Initialize VNET manager.
        
        Args:
            vnets: Dictionary of all VNETs by ID
            tabs: Dictionary of all tabs by ID
            dirty_manager: DirtyFlagManager for marking VNETs dirty
        """
        self.vnets = vnets
        self.tabs = tabs
        self.dirty_manager = dirty_manager
        
        # Build reverse lookup: tab_id -> vnet_id
        self.tab_to_vnet: Dict[str, str] = {}
        for vnet_id, vnet in vnets.items():
            for tab_id in vnet.tab_ids:
                self.tab_to_vnet[tab_id] = vnet_id
    
    def get_vnet_for_tab(self, tab_id: str) -> Optional[VNET]:
        """
        Get the VNET containing a specific tab.
        
        Args:
            tab_id: Tab ID to look up
            
        Returns:
            VNET containing the tab, or None if not found
        """
        vnet_id = self.tab_to_vnet.get(tab_id)
        if vnet_id:
            return self.vnets.get(vnet_id)
        return None
    
    def get_vnet_for_pin(self, pin_id: str) -> Optional[VNET]:
        """
        Get the VNET for a pin by finding its first tab.
        
        Args:
            pin_id: Pin ID to look up
            
        Returns:
            VNET containing the pin's tab, or None if not found
        """
        # Find a tab belonging to this pin
        for tab_id, tab in self.tabs.items():
            if tab.parent_pin and tab.parent_pin.pin_id == pin_id:
                return self.get_vnet_for_tab(tab_id)
        return None
    
    def get_vnet_state(self, tab_id: str) -> bool:
        """
        Get the state of the VNET containing a tab.
        
        Args:
            tab_id: Tab ID to check
            
        Returns:
            True if VNET is HIGH, False if LOW or not found
        """
        vnet = self.get_vnet_for_tab(tab_id)
        if vnet:
            return vnet.state
        return False
    
    def mark_vnet_dirty(self, tab_id: str):
        """
        Mark the VNET containing a tab as dirty.
        
        This should be called when a component changes a pin state.
        
        Args:
            tab_id: Tab ID whose VNET should be marked dirty
        """
        vnet_id = self.tab_to_vnet.get(tab_id)
        if vnet_id:
            self.dirty_manager.mark_dirty(vnet_id)
    
    def mark_tab_dirty(self, tab_id: str):
        """
        Mark the VNET containing a tab as dirty (alias for mark_vnet_dirty).
        
        Args:
            tab_id: Tab ID whose VNET should be marked dirty
        """
        self.mark_vnet_dirty(tab_id)
    
    def get_tab(self, tab_id: str) -> Optional[Tab]:
        """
        Get a tab by ID.
        
        Args:
            tab_id: Tab ID to look up
            
        Returns:
            Tab instance or None if not found
        """
        return self.tabs.get(tab_id)
