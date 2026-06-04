"""
SPST Switch Component for Relay Logic Simulator

A simple Single Pole Single Throw (SPST) switch with two terminals.
When closed, creates a bridge between the two terminals.
When open, the terminals are disconnected.

Can operate in two modes:
- Toggle mode: Click to toggle ON/OFF, stays in position
- Pushbutton mode: ON while pressed, OFF when released

Visual: Simple switch symbol with two terminals
Pins: 2 pins (terminal1 and terminal2)
"""

from typing import Dict, Any, Optional
from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState
import uuid


class SPSTSwitch(Component):
    """
    SPST Switch component - User-controlled bridge between two terminals.
    
    Can operate as toggle switch (latching) or pushbutton (momentary).
    When CLOSED, creates a bridge connecting the two terminals.
    When OPEN, the bridge is removed and terminals are disconnected.
    
    Properties:
        mode: "toggle" or "pushbutton"
        label: Display label (optional)
        label_position: "top", "bottom", "left", or "right"
    """
    
    component_type = "SPSTSwitch"
    
    def __init__(self, component_id: str, page_id: str):
        """
        Initialize SPST switch component.
        
        Args:
            component_id: Unique component ID
            page_id: Page this component belongs to
        """
        super().__init__(component_id, page_id)
        
        # Internal state
        self._is_closed = False  # Current switch state (True = closed/ON)
        self._bridge_id: Optional[str] = None  # Bridge ID when closed
        
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
        self._terminal1_pin: Optional[Pin] = None
        self._terminal2_pin: Optional[Pin] = None
        self._create_pins_and_tabs()
    
    def _create_pins_and_tabs(self):
        """Create the two terminal pins with tabs."""
        # Terminal 1 (left side)
        pin1_id = f"{self.component_id}.terminal1"
        self._terminal1_pin = Pin(pin1_id, self)
        tab1_id = f"{pin1_id}.tab0"
        tab1 = Tab(tab1_id, self._terminal1_pin, (-30, 0))  # 30px to the left
        self._terminal1_pin.add_tab(tab1)
        self.add_pin(self._terminal1_pin)
        
        # Terminal 2 (right side)
        pin2_id = f"{self.component_id}.terminal2"
        self._terminal2_pin = Pin(pin2_id, self)
        tab2_id = f"{pin2_id}.tab0"
        tab2 = Tab(tab2_id, self._terminal2_pin, (30, 0))  # 30px to the right
        self._terminal2_pin.add_tab(tab2)
        self.add_pin(self._terminal2_pin)
    
    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """
        Update switch bridge based on current state.
        
        SPST switch creates/removes a bridge between its terminals.
        It doesn't drive pins directly - it connects/disconnects them.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance for bridge operations (required)
        """
        if bridge_manager is None:
            return  # Cannot operate without bridge_manager
        
        # Update bridge based on switch state
        self._update_bridge(vnet_manager, bridge_manager)
    
    def _update_bridge(self, vnet_manager, bridge_manager):
        """Create or remove bridge based on switch state."""
        if self._is_closed:
            # Switch is closed - ensure bridge exists
            if self._bridge_id is None:
                # Create bridge between the two terminals
                vnet1 = vnet_manager.get_vnet_for_pin(self._terminal1_pin.pin_id)
                vnet2 = vnet_manager.get_vnet_for_pin(self._terminal2_pin.pin_id)
                
                if vnet1 and vnet2 and vnet1.vnet_id != vnet2.vnet_id:
                    self._bridge_id = bridge_manager.create_bridge(
                        vnet1.vnet_id, vnet2.vnet_id, self.component_id
                    )
        else:
            # Switch is open - ensure bridge is removed
            if self._bridge_id is not None:
                bridge_manager.remove_bridge(self._bridge_id)
                self._bridge_id = None
    
    def sim_start(self, vnet_manager, bridge_manager):
        """
        Initialize switch for simulation start.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance
        """
        # Start in OPEN state by default
        self._is_closed = False
        self._bridge_id = None
        
        # Initialize both terminal pins to FLOAT (passive - don't drive the network)
        if self._terminal1_pin:
            self._terminal1_pin.set_state(PinState.FLOAT)
        if self._terminal2_pin:
            self._terminal2_pin.set_state(PinState.FLOAT)
        
        # Ensure no bridge exists initially
        self._update_bridge(vnet_manager, bridge_manager)
    
    def sim_stop(self, vnet_manager=None, bridge_manager=None):
        """
        Clean up switch state.
        
        Args:
            vnet_manager: VnetManager instance (unused)
            bridge_manager: BridgeManager instance
        """
        # Remove bridge if it exists
        if bridge_manager and self._bridge_id:
            bridge_manager.remove_bridge(self._bridge_id)
            self._bridge_id = None
        
        self._is_closed = False
    
    def interact(self, action: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Handle user interaction with switch.
        
        Args:
            action: "toggle", "press", or "release"
            params: Optional parameters
            
        Returns:
            bool: True if state changed (triggers simulation update)
        """
        mode = self.properties.get('mode', 'toggle')
        
        if mode == 'toggle':
            # Toggle mode: flip state on any interaction
            if action in ('toggle', 'click', 'press'):
                self._is_closed = not self._is_closed
                return True
        
        elif mode == 'pushbutton':
            # Pushbutton mode: CLOSED when pressed, OPEN when released
            if action == 'press':
                if not self._is_closed:
                    self._is_closed = True
                    return True
            elif action == 'release':
                if self._is_closed:
                    self._is_closed = False
                    return True
        
        return False
    
    def get_visual_state(self) -> Dict[str, Any]:
        """
        Return current visual state for rendering.
        
        Returns:
            dict: Visual state including switch CLOSED/OPEN state
        """
        state = super().get_visual_state()
        state['switch_state'] = 'CLOSED' if self._is_closed else 'OPEN'
        return state
    
    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        """
        Render method (not used by Tkinter GUI, which uses renderers).
        
        Args:
            canvas_adapter: CanvasAdapter for drawing
            x_offset: X offset for panning
            y_offset: Y offset for panning
        """
        pass
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SPSTSwitch':
        """
        Deserialize SPST switch from dict.
        
        Args:
            data: Component data dict
            
        Returns:
            SPSTSwitch instance
        """
        switch = cls(data['component_id'], data.get('page_id', 'page001'))
        
        # Load position
        pos = data.get('position', {'x': 0, 'y': 0})
        switch.position = (pos['x'], pos['y'])
        
        # Load rotation
        switch.rotation = data.get('rotation', 0)
        
        # Load link name
        switch.link_name = data.get('link_name')
        
        # Load properties
        if 'properties' in data and isinstance(data['properties'], dict):
            switch.properties.update(data['properties'])
        
        return switch
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize SPST switch to dict.
        
        Returns:
            dict: Component data
        """
        return super().to_dict()
