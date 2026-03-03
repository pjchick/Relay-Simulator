"""
Ground Latching Relay Component for Relay Logic Simulator

A latching (bistable) Double Pole Double Throw relay with two coils and 
ground reference requirement. The relay switches two independent poles between 
normally-closed (NC) and normally-open (NO) contacts based on which coil is 
energized. The relay maintains its state after coil de-energization (latching behavior).

Each coil requires both a HIGH signal AND a proper ground connection to activate.

Visual: Relay symbol with two coils (SET with GND and RESET with GND) and two poles
Pins: 10 pins total
  - 4 coil pins (COIL_SET, GND_SET, COIL_RESET, GND_RESET)
  - Pole 1: COM1, NO1, NC1 (3 pins)
  - Pole 2: COM2, NO2, NC2 (3 pins)

Timing: 10ms delay when coil state changes before contacts switch
State: 
  - SET state (energized): Triggered when COIL_SET is HIGH AND GND_SET is connected (and COIL_RESET is not active), maintains until RESET
  - RESET state (de-energized): Triggered when COIL_RESET is HIGH AND GND_RESET is connected (and COIL_SET is not active), maintains until SET
  - Both coils active: Relay maintains current state (no change)
"""

from typing import Dict, Any, Optional
import time
import threading
from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class GroundLatchingRelay(Component):
    """
    Ground Latching Relay component - Bistable relay with two coils and ground references.
    
    Each pole switches between NC (normally-closed) and NO (normally-open)
    contacts when SET coil is energized (with ground), and back when RESET coil 
    is energized (with ground). The relay maintains its state after coil de-energization.
    
    Requires both coil pin HIGH and corresponding GND pin connected to a GND component.
    
    Properties:
        label: Display label (optional)
        label_position: "top", "bottom", "left", or "right"
        color: Color name (affects coil on/off colors)
        on_color: RGB tuple for set state
        off_color: RGB tuple for reset state
        rotation: 0, 90, 180, 270 degrees
        flip_horizontal: True/False
        flip_vertical: True/False
    
    Pin Configuration:
        COIL_SET: Switches relay to SET state (COM -> NO) when HIGH (if GND_SET is connected)
        GND_SET: Must be connected to a GND component for SET coil to function
        COIL_RESET: Switches relay to RESET state (COM -> NC) when HIGH (if GND_RESET is connected)
        GND_RESET: Must be connected to a GND component for RESET coil to function
        Pole 1: COM1, NO1, NC1
        Pole 2: COM2, NO2, NC2
    
    Bridge Behavior:
        RESET state: COM1→NC1, COM2→NC2
        SET state: COM1→NO1, COM2→NO2
    """
    
    component_type = "GroundLatchingRelay"
    
    # Default colors for different color options
    COLOR_PRESETS = {
        "red": {"on": (255, 0, 0), "off": (128, 0, 0)},
        "green": {"on": (0, 255, 0), "off": (0, 128, 0)},
        "blue": {"on": (0, 0, 255), "off": (0, 0, 128)},
        "yellow": {"on": (255, 255, 0), "off": (128, 128, 0)},
        "orange": {"on": (255, 165, 0), "off": (128, 82, 0)},
        "white": {"on": (255, 255, 255), "off": (192, 192, 192)},
        "gray": {"on": (200, 200, 200), "off": (128, 128, 128)},
    }
    
    # Switching delay in seconds (10ms)
    SWITCHING_DELAY = 0.010
    
    def __init__(self, component_id: str, page_id: str):
        """
        Initialize ground latching relay component.
        
        Args:
            component_id: Unique identifier for this component
            page_id: ID of the page this component belongs to
        """
        super().__init__(component_id, page_id)
        
        # Internal state
        self._is_set = False  # Current relay state (False = RESET, True = SET)
        self._target_set = False  # Target state after timer
        self._timer_active = False  # Whether timer is running
        self._timer_thread: Optional[threading.Thread] = None
        self._timer_lock = threading.Lock()
        self._on_contacts_switched_callback = None  # Callback to trigger simulation restart
        
        # Bridge references (runtime only)
        self._pole1_bridge_id: Optional[str] = None
        self._pole2_bridge_id: Optional[str] = None
        
        # Pin references (set during pin creation)
        self._coil_set_pin: Optional[Pin] = None
        self._gnd_set_pin: Optional[Pin] = None
        self._coil_reset_pin: Optional[Pin] = None
        self._gnd_reset_pin: Optional[Pin] = None
        self._com1_pin: Optional[Pin] = None
        self._no1_pin: Optional[Pin] = None
        self._nc1_pin: Optional[Pin] = None
        self._com2_pin: Optional[Pin] = None
        self._no2_pin: Optional[Pin] = None
        self._nc2_pin: Optional[Pin] = None
        
        # Properties
        self.properties["label"] = ""
        self.properties["label_position"] = "top"
        self.properties["color"] = "blue"
        # GUI-only: relay body/background fill color (hex). Used by GroundLatchingRelayRenderer.
        # Default matches the legacy hardcoded renderer color.
        self.properties["body_color"] = "#CCCCCC"
        self.properties["flip_horizontal"] = False
        self.properties["flip_vertical"] = False
        
        # Rotation is handled by base Component.rotation attribute
        # Set default rotation
        self.rotation = 0
        
        # Set default colors
        self.set_color("blue")
        
        # Create pins and tabs
        self._create_pins_and_tabs()
    
    def _create_pins_and_tabs(self):
        """
        Create all 10 pins with a single tab each.
        
        Visual layout:
        - Component: 60px wide x 240px tall (same as regular latching relay)
        - Pins arranged vertically along left and right edges
        
        Pin positions (relative to component center):
        Left side (x = -30, at left edge):
          - COIL_SET: top-left (y = -100, 3 grid squares above COM1)
          - COM1: upper-mid-left (y = -40)
          - COM2: lower-mid-left (y = +40)
          - COIL_RESET: bottom-left (y = +100, 3 grid squares below COM2)
        
        Right side (x = +30, at right edge):
          - GND_SET: top-right (y = -100, aligned with COIL_SET)
          - NO1: top-mid-right (y = -60)
          - NC1: upper-mid-right (y = -20)
          - NO2: lower-mid-right (y = +20)
          - NC2: bottom-mid-right (y = +60)
          - GND_RESET: bottom-right (y = +100, aligned with COIL_RESET)
        """
        
        # Helper function to create a pin with a single tab
        def create_pin_with_tab(pin_name: str, pin_offset_x: int, pin_offset_y: int) -> Pin:
            """
            Create a pin with a single tab at the pin position.
            
            Args:
                pin_name: Name of the pin (COIL_SET, GND_SET, etc.)
                pin_offset_x: X offset from component center
                pin_offset_y: Y offset from component center
            """
            pin_id = f"{self.component_id}.{pin_name}"
            pin = Pin(pin_id, self)
            
            # Create single tab at the pin position
            tab_id = f"{pin_id}.tab0"
            tab = Tab(tab_id, pin, (pin_offset_x, pin_offset_y))
            pin.add_tab(tab)
            
            return pin
        
        # Left side pins (x = -30, touching left edge of relay box)
        left_x = -30
        
        # COIL_SET pin (top-left, y = -100, 3 grid squares above COM1)
        self._coil_set_pin = create_pin_with_tab("COIL_SET", left_x, -100)
        self.add_pin(self._coil_set_pin)
        
        # COM1 pin (upper-mid-left, y = -40)
        self._com1_pin = create_pin_with_tab("COM1", left_x, -40)
        self.add_pin(self._com1_pin)
        
        # COM2 pin (lower-mid-left, y = +40)
        self._com2_pin = create_pin_with_tab("COM2", left_x, 40)
        self.add_pin(self._com2_pin)
        
        # COIL_RESET pin (bottom-left, y = +100, 3 grid squares below COM2)
        self._coil_reset_pin = create_pin_with_tab("COIL_RESET", left_x, 100)
        self.add_pin(self._coil_reset_pin)
        
        # Right side pins (x = +30, touching right edge of relay box)
        right_x = 30
        
        # GND_SET pin (top-right, y = -100, aligned with COIL_SET)
        self._gnd_set_pin = create_pin_with_tab("GND_SET", right_x, -100)
        self.add_pin(self._gnd_set_pin)
        
        # NO1 pin (top-mid-right, y = -60)
        self._no1_pin = create_pin_with_tab("NO1", right_x, -60)
        self.add_pin(self._no1_pin)
        
        # NC1 pin (upper-mid-right, y = -20)
        self._nc1_pin = create_pin_with_tab("NC1", right_x, -20)
        self.add_pin(self._nc1_pin)
        
        # NO2 pin (lower-mid-right, y = +20)
        self._no2_pin = create_pin_with_tab("NO2", right_x, 20)
        self.add_pin(self._no2_pin)
        
        # NC2 pin (bottom-mid-right, y = +60)
        self._nc2_pin = create_pin_with_tab("NC2", right_x, 60)
        self.add_pin(self._nc2_pin)
        
        # GND_RESET pin (bottom-right, y = +100, aligned with COIL_RESET)
        self._gnd_reset_pin = create_pin_with_tab("GND_RESET", right_x, 100)
        self.add_pin(self._gnd_reset_pin)
    
    def _is_gnd_connected(self, vnet_manager, gnd_pin: Pin) -> bool:
        """
        Check if a GND pin is connected to a GND component.
        Traverses bridges to find GND components through relay contacts.
        
        Args:
            vnet_manager: VnetManager instance
            gnd_pin: The GND pin to check (GND_SET or GND_RESET)
            
        Returns:
            True if GND pin is connected to a GND component, False otherwise
        """
        if not gnd_pin or not gnd_pin.tabs:
            return False
        
        # Get the VNET for the GND pin
        gnd_tab = next(iter(gnd_pin.tabs.values()))
        start_vnet = vnet_manager.get_vnet_for_tab(gnd_tab.tab_id)
        
        if not start_vnet:
            return False
        
        # Use BFS to traverse VNETs through bridges to find a GND component
        visited_vnets = set()
        queue = [start_vnet.vnet_id]
        
        while queue:
            current_vnet_id = queue.pop(0)
            
            if current_vnet_id in visited_vnets:
                continue
            
            visited_vnets.add(current_vnet_id)
            current_vnet = vnet_manager.vnets.get(current_vnet_id)
            
            if not current_vnet:
                continue
            
            # Check all tabs in this VNET for a GND component
            for tab_id in current_vnet.tab_ids:
                tab = vnet_manager.tabs.get(tab_id)
                if tab and tab.parent_pin and tab.parent_pin.parent_component:
                    component = tab.parent_pin.parent_component
                    if hasattr(component, 'component_type') and component.component_type == "GND":
                        return True
            
            # Follow bridges to connected VNETs
            for bridge_id in current_vnet.bridge_ids:
                # Get the bridge to find the other VNET
                # Bridges connect two VNETs, so we need to find the other one
                for other_vnet_id, other_vnet in vnet_manager.vnets.items():
                    if other_vnet_id != current_vnet_id and bridge_id in other_vnet.bridge_ids:
                        if other_vnet_id not in visited_vnets:
                            queue.append(other_vnet_id)
            
            # Follow link names to connected VNETs (cross-page connections)
            for link_name in current_vnet.link_names:
                for other_vnet_id, other_vnet in vnet_manager.vnets.items():
                    if other_vnet_id != current_vnet_id and other_vnet.has_link(link_name):
                        if other_vnet_id not in visited_vnets:
                            queue.append(other_vnet_id)
        
        return False
    
    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """
        Execute relay logic with timer-based switching.
        
        Reads both coil pin states and ground connections, starts a 10ms timer if state change detected.
        SET coil HIGH AND GND_SET connected (alone) -> switches to SET state (COM->NO)
        RESET coil HIGH AND GND_RESET connected (alone) -> switches to RESET state (COM->NC)
        Both coils active -> maintains current state (no change)
        State is maintained (latched) until opposite coil is energized with ground.
        
        Args:
            vnet_manager: VnetManager instance for state tracking
            bridge_manager: BridgeManager instance for bridge operations (required)
        """
        if bridge_manager is None:
            return  # Cannot operate without bridge_manager

        if not self._coil_set_pin or not self._coil_reset_pin:
            return
        if not self._gnd_set_pin or not self._gnd_reset_pin:
            return

        # Read SET coil state
        if not self._coil_set_pin.tabs:
            return
        set_tab = next(iter(self._coil_set_pin.tabs.values()))
        set_vnet = vnet_manager.get_vnet_for_tab(set_tab.tab_id)
        if not set_vnet:
            return
        set_coil_state = set_vnet.state
        
        # Read RESET coil state
        if not self._coil_reset_pin.tabs:
            return
        reset_tab = next(iter(self._coil_reset_pin.tabs.values()))
        reset_vnet = vnet_manager.get_vnet_for_tab(reset_tab.tab_id)
        if not reset_vnet:
            return
        reset_coil_state = reset_vnet.state
        
        # Check ground connections
        set_gnd_connected = self._is_gnd_connected(vnet_manager, self._gnd_set_pin)
        reset_gnd_connected = self._is_gnd_connected(vnet_manager, self._gnd_reset_pin)
        
        # Determine if each coil is active (both signal HIGH and ground connected)
        set_active = (set_coil_state == PinState.HIGH) and set_gnd_connected
        reset_active = (reset_coil_state == PinState.HIGH) and reset_gnd_connected
        
        # Determine target state based on coil inputs
        # RESET has priority when both coils are active (safer default state)
        target_set = None
        
        if reset_active:
            # RESET coil active - switch to RESET state (has priority)
            target_set = False
        elif set_active:
            # Only SET coil active - switch to SET state
            target_set = True
        
        # If we have a state change command, start/update timer
        if target_set is not None and target_set != self._is_set:
            with self._timer_lock:
                self._target_set = target_set
                
                if not self._timer_active:
                    self._timer_active = True
                    self._timer_thread = threading.Thread(
                        target=self._timer_callback,
                        args=(vnet_manager, bridge_manager),
                        daemon=True
                    )
                    self._timer_thread.start()
    
    def _timer_callback(self, vnet_manager, bridge_manager):
        """
        Timer callback that executes after SWITCHING_DELAY.
        
        Switches bridges and updates relay state, then triggers simulation restart.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance
        """
        time.sleep(self.SWITCHING_DELAY)

        with self._timer_lock:
            # Apply the state change
            if self._target_set != self._is_set:
                self._is_set = self._target_set
                self._switch_contacts(vnet_manager, bridge_manager)

                if self._on_contacts_switched_callback:
                    self._on_contacts_switched_callback()

            self._timer_active = False
    
    def _switch_contacts(self, vnet_manager, bridge_manager):
        """
        Switch relay contacts by removing old bridges and creating new ones.
        
        Called by timer callback after delay completes.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance
        """
        # Remove existing bridges (if any)
        if self._pole1_bridge_id:
            bridge_manager.remove_bridge(self._pole1_bridge_id)
            self._pole1_bridge_id = None
        
        if self._pole2_bridge_id:
            bridge_manager.remove_bridge(self._pole2_bridge_id)
            self._pole2_bridge_id = None
        
        # Create new bridges based on current state
        if self._is_set:
            # SET state: COM -> NO
            vnet_com1 = vnet_manager.get_vnet_for_pin(self._com1_pin.pin_id)
            vnet_no1 = vnet_manager.get_vnet_for_pin(self._no1_pin.pin_id)
            if vnet_com1 and vnet_no1:
                self._pole1_bridge_id = bridge_manager.create_bridge(
                    vnet_com1.vnet_id, vnet_no1.vnet_id, self.component_id
                )
            
            vnet_com2 = vnet_manager.get_vnet_for_pin(self._com2_pin.pin_id)
            vnet_no2 = vnet_manager.get_vnet_for_pin(self._no2_pin.pin_id)
            if vnet_com2 and vnet_no2:
                self._pole2_bridge_id = bridge_manager.create_bridge(
                    vnet_com2.vnet_id, vnet_no2.vnet_id, self.component_id
                )
        else:
            # RESET state: COM -> NC
            vnet_com1 = vnet_manager.get_vnet_for_pin(self._com1_pin.pin_id)
            vnet_nc1 = vnet_manager.get_vnet_for_pin(self._nc1_pin.pin_id)
            if vnet_com1 and vnet_nc1:
                self._pole1_bridge_id = bridge_manager.create_bridge(
                    vnet_com1.vnet_id, vnet_nc1.vnet_id, self.component_id
                )
            
            vnet_com2 = vnet_manager.get_vnet_for_pin(self._com2_pin.pin_id)
            vnet_nc2 = vnet_manager.get_vnet_for_pin(self._nc2_pin.pin_id)
            if vnet_com2 and vnet_nc2:
                self._pole2_bridge_id = bridge_manager.create_bridge(
                    vnet_com2.vnet_id, vnet_nc2.vnet_id, self.component_id
                )

    
    def set_color(self, color_name: str):
        """
        Set the relay color from preset.
        
        Args:
            color_name: Color name from COLOR_PRESETS
        """
        if color_name in self.COLOR_PRESETS:
            preset = self.COLOR_PRESETS[color_name]
            self.properties["on_color"] = preset["on"]
            self.properties["off_color"] = preset["off"]
            self.properties["color"] = color_name
    
    def get_property_definitions(self) -> list:
        """
        Return property definitions for UI editing.
        
        Returns:
            List of property definition dictionaries
        """
        return [
            {
                "name": "label",
                "type": "string",
                "default": "",
                "description": "Text label"
            },
            {
                "name": "label_position",
                "type": "choice",
                "choices": ["top", "bottom", "left", "right"],
                "default": "top",
                "description": "Label position"
            },
            {
                "name": "color",
                "type": "choice",
                "choices": list(self.COLOR_PRESETS.keys()),
                "default": "blue",
                "description": "Coil color preset"
            },
            {
                "name": "body_color",
                "type": "color",
                "default": "#CCCCCC",
                "description": "Relay body color"
            },
            {
                "name": "flip_horizontal",
                "type": "boolean",
                "default": False,
                "description": "Flip horizontally"
            },
            {
                "name": "flip_vertical",
                "type": "boolean",
                "default": False,
                "description": "Flip vertically"
            }
        ]
    
    def set_property(self, prop_name: str, value: Any):
        """
        Set a component property with validation.
        
        Args:
            prop_name: Property name
            value: Property value
        """
        if prop_name == "color":
            self.set_color(value)
        else:
            self.properties[prop_name] = value
    
    def sim_start(self, vnet_manager, bridge_manager):
        """
        Initialize relay state at simulation start.
        
        Relay starts in RESET state (COM -> NC connections).
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance
        """
        # Initialize to RESET state
        self._is_set = False
        self._target_set = False
        self._timer_active = False
        
        # Create initial bridges (RESET state: COM -> NC)
        self._switch_contacts(vnet_manager, bridge_manager)
    
    def sim_stop(self):
        """
        Clean up when simulation stops.
        
        Cancels any pending timers and resets state.
        """
        with self._timer_lock:
            self._timer_active = False
            if self._timer_thread and self._timer_thread.is_alive():
                # Timer thread will exit when it completes
                pass
            
            self._pole1_bridge_id = None
            self._pole2_bridge_id = None
    
    def set_on_contacts_switched_callback(self, callback):
        """
        Register callback to be called when contacts switch.
        
        Used by simulation engine to restart simulation when relay changes state.
        
        Args:
            callback: Callable with no arguments
        """
        self._on_contacts_switched_callback = callback
    
    def render(self, canvas_adapter, x_offset: int = 0, y_offset: int = 0):
        """
        Render relay on canvas.
        
        Args:
            canvas_adapter: Canvas adapter for drawing
            x_offset: X position offset
            y_offset: Y position offset
        """
        # Get absolute position
        abs_x = self.position[0] + x_offset
        abs_y = self.position[1] + y_offset
        
        # Choose color based on set state
        color = self.properties["on_color"] if self._is_set else self.properties["off_color"]
        
        # Draw relay symbol (simplified - actual rendering depends on canvas adapter)
        # This is a placeholder for the visual representation
        # Body from -120 to +120 (240px height, centered)
        canvas_adapter.draw_rectangle(abs_x - 30, abs_y - 120, 60, 240, color)
        
        # Draw label if present
        if self.properties.get("label"):
            label_pos = self.properties.get("label_position", "top")
            canvas_adapter.draw_text(
                self.properties["label"],
                abs_x, abs_y,
                position=label_pos
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize component to dictionary.
        
        Returns:
            Dictionary representation of the component
        """
        data = super().to_dict()
        # State is not persisted - relay always starts in RESET state
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GroundLatchingRelay':
        """
        Deserialize relay from dictionary.
        
        Args:
            data: Serialized component data
            
        Returns:
            GroundLatchingRelay instance
        """
        relay = cls(data["component_id"], data.get("page_id", "page001"))
        
        # Restore position (schema uses {x, y} object)
        if "position" in data:
            pos = data["position"]
            relay.position = (pos['x'], pos['y'])
        if "rotation" in data:
            relay.rotation = data["rotation"]
        if "link_name" in data:
            relay.link_name = data["link_name"]
        
        # Restore properties
        if "properties" in data:
            relay.properties.update(data["properties"])
        
        # Apply color preset if specified
        if "color" in relay.properties:
            relay.set_color(relay.properties["color"])
        
        return relay
