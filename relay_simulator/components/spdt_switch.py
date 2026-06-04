"""
SPDT Switch Component for Relay Logic Simulator

A Single Pole Dual Throw (SPDT) switch with three terminals.
The common terminal connects to either terminal1 or terminal2.
When switched, it breaks connection with one terminal and makes connection with the other.

Can operate in two modes:
- Toggle mode: Click to toggle between positions, stays in position
- Pushbutton mode: Position 1 while pressed, Position 0 when released

Visual: SPDT switch symbol with common on left, two throws on right
Pins: 3 pins (common, terminal1, terminal2)
"""

from typing import Dict, Any, Optional
from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState
import uuid


class SPDTSwitch(Component):
    """
    SPDT Switch component - User-controlled switch between two paths.
    
    Can operate as toggle switch (latching) or pushbutton (momentary).
    Position 0: Common connected to terminal1
    Position 1: Common connected to terminal2
    
    Properties:
        mode: "toggle" or "pushbutton"
        label: Display label (optional)
        label_position: "top", "bottom", "left", or "right"
        flip_horizontal: Flip horizontally
        flip_vertical: Flip vertically
    """
    
    component_type = "SPDTSwitch"
    
    def __init__(self, component_id: str, page_id: str):
        """
        Initialize SPDT switch component.
        
        Args:
            component_id: Unique component ID
            page_id: Page this component belongs to
        """
        super().__init__(component_id, page_id)
        
        # Internal state
        self._position = 0  # 0 = terminal1, 1 = terminal2
        self._bridge_id: Optional[str] = None  # Active bridge ID
        
        # Set default properties
        self.properties = {
            'mode': 'toggle',  # 'toggle' or 'pushbutton'
            'label': 'SW',
            'label_position': 'bottom',  # 'top', 'bottom', 'left', 'right'
            'flip_horizontal': False,
            'flip_vertical': False,
        }
        self.rotation = 0  # Support rotation (0, 90, 180, 270)
        
        # Create pins and tabs
        self._common_pin: Optional[Pin] = None
        self._terminal1_pin: Optional[Pin] = None
        self._terminal2_pin: Optional[Pin] = None
        self._create_pins_and_tabs()
    
    def _create_pins_and_tabs(self):
        """Create the three terminal pins with tabs."""
        # Common pin (left side)
        common_id = f"{self.component_id}.common"
        self._common_pin = Pin(common_id, self)
        common_tab_id = f"{common_id}.tab0"
        common_tab = Tab(common_tab_id, self._common_pin, (-30, 0))  # 30px to the left
        self._common_pin.add_tab(common_tab)
        self.add_pin(self._common_pin)
        
        # Terminal 1 (right upper)
        pin1_id = f"{self.component_id}.terminal1"
        self._terminal1_pin = Pin(pin1_id, self)
        tab1_id = f"{pin1_id}.tab0"
        tab1 = Tab(tab1_id, self._terminal1_pin, (30, -20))  # 30px right, 20px up
        self._terminal1_pin.add_tab(tab1)
        self.add_pin(self._terminal1_pin)
        
        # Terminal 2 (right lower)
        pin2_id = f"{self.component_id}.terminal2"
        self._terminal2_pin = Pin(pin2_id, self)
        tab2_id = f"{pin2_id}.tab0"
        tab2 = Tab(tab2_id, self._terminal2_pin, (30, 20))  # 30px right, 20px down
        self._terminal2_pin.add_tab(tab2)
        self.add_pin(self._terminal2_pin)
    
    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """
        Update switch bridge based on current position.
        
        SPDT switch creates a bridge between common and one of the terminals.
        It doesn't drive pins directly - it connects/disconnects them.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance for bridge operations (required)
        """
        if bridge_manager is None:
            return  # Cannot operate without bridge_manager
        
        # Update bridge based on switch position
        self._update_bridge(vnet_manager, bridge_manager)
    
    def _update_bridge(self, vnet_manager, bridge_manager):
        """
        Update the bridge connection based on switch position.
        
        Position 0: Common <-> Terminal1
        Position 1: Common <-> Terminal2
        """
        # Remove old bridge if exists
        if self._bridge_id is not None:
            bridge_manager.remove_bridge(self._bridge_id)
            self._bridge_id = None
        
        # Get VNETs for the pins
        common_vnet = vnet_manager.get_vnet_for_pin(self._common_pin.pin_id)
        
        if self._position == 0:
            # Connect common to terminal1
            terminal_vnet = vnet_manager.get_vnet_for_pin(self._terminal1_pin.pin_id)
        else:
            # Connect common to terminal2
            terminal_vnet = vnet_manager.get_vnet_for_pin(self._terminal2_pin.pin_id)
        
        # Create bridge between common and selected terminal VNETs
        if common_vnet and terminal_vnet and common_vnet.vnet_id != terminal_vnet.vnet_id:
            self._bridge_id = bridge_manager.create_bridge(
                common_vnet.vnet_id,
                terminal_vnet.vnet_id,
                self.component_id
            )
    
    def sim_start(self, vnet_manager, bridge_manager=None):
        """
        Initialize switch for simulation start.
        
        Sets pins to FLOAT (passive) and creates initial bridge.
        """
        # Set all pins to FLOAT (passive - don't drive the network)
        if self._common_pin:
            self._common_pin.set_state(PinState.FLOAT)
        if self._terminal1_pin:
            self._terminal1_pin.set_state(PinState.FLOAT)
        if self._terminal2_pin:
            self._terminal2_pin.set_state(PinState.FLOAT)
        
        # Start in position 0 (terminal1)
        self._position = 0
        self._bridge_id = None
        
        # Create initial bridge
        if bridge_manager:
            self._update_bridge(vnet_manager, bridge_manager)
    
    def sim_stop(self, vnet_manager=None, bridge_manager=None):
        """
        Clean up when simulation stops.
        
        Removes any active bridges.
        
        Args:
            vnet_manager: VnetManager instance (unused)
            bridge_manager: BridgeManager instance
        """
        if bridge_manager and self._bridge_id is not None:
            bridge_manager.remove_bridge(self._bridge_id)
            self._bridge_id = None
    
    def interact(self, action: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Handle user interaction with the switch.
        
        Args:
            action: 'toggle' (toggle position), 'press' (move to position 1), 'release' (move to position 0)
            params: Optional parameters
            
        Returns:
            bool: True if state changed (triggers simulation update)
        """
        mode = self.properties.get('mode', 'toggle')
        
        if mode == 'toggle':
            # Toggle mode: flip position on any interaction
            if action in ('toggle', 'click', 'press'):
                self._position = 1 - self._position
                return True
        
        elif mode == 'pushbutton':
            # Pushbutton mode: Position 1 when pressed, Position 0 when released
            if action == 'press':
                if self._position != 1:
                    self._position = 1
                    return True
            elif action == 'release':
                if self._position != 0:
                    self._position = 0
                    return True
        
        return False
    
    def get_visual_state(self) -> str:
        """
        Get the visual state for rendering.
        
        Returns:
            'POSITION_0' or 'POSITION_1'
        """
        return 'POSITION_0' if self._position == 0 else 'POSITION_1'
    
    def render(self):
        """Placeholder for rendering (not used in Tkinter GUI)."""
        pass
