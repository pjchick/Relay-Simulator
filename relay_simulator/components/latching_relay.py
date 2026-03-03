"""
Latching Relay Component for Relay Logic Simulator

A latching (bistable) Double Pole Double Throw relay with two coils.
The relay switches two independent poles between normally-closed (NC) and 
normally-open (NO) contacts based on which coil is energized. The relay 
maintains its state after coil de-energization (latching behavior).

Visual: Relay symbol with two coils (SET and RESET) and two poles
Pins: 8 pins total
  - 2 coil pins (COIL_SET, COIL_RESET)
  - Pole 1: COM1, NO1, NC1 (3 pins)
  - Pole 2: COM2, NO2, NC2 (3 pins)

Timing: 10ms delay when coil state changes before contacts switch
State: 
  - SET state (energized): Triggered when COIL_SET is HIGH (and COIL_RESET is not), maintains until RESET
  - RESET state (de-energized): Triggered when COIL_RESET is HIGH (and COIL_SET is not), maintains until SET
  - Both coils HIGH: Relay maintains current state (no change)
"""

from typing import Dict, Any, Optional
import time
import threading
from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class LatchingRelay(Component):
    """
    Latching Relay component - Bistable relay with two coils.
    
    Each pole switches between NC (normally-closed) and NO (normally-open)
    contacts when SET coil is energized, and back when RESET coil is energized.
    The relay maintains its state after coil de-energization.
    
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
        COIL_SET: Switches relay to SET state (COM -> NO) when HIGH
        COIL_RESET: Switches relay to RESET state (COM -> NC) when HIGH
        Pole 1: COM1, NO1, NC1
        Pole 2: COM2, NO2, NC2
    
    Bridge Behavior:
        RESET state: COM1→NC1, COM2→NC2
        SET state: COM1→NO1, COM2→NO2
    """
    
    component_type = "LatchingRelay"
    
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
        Initialize latching relay component.
        
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
        self._coil_reset_pin: Optional[Pin] = None
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
        # GUI-only: relay body/background fill color (hex). Used by LatchingRelayRenderer.
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
        Create all 8 pins with a single tab each.
        
        Visual layout:
        - Component: 60px wide x 240px tall (taller than standard DPDT to fit second coil)
        - Pins arranged vertically along left and right edges
        
        Pin positions (relative to component center):
        Left side (x = -30, at left edge):
          - COIL_SET: top-left (y = -100, 3 grid squares above COM1)
          - COM1: upper-mid-left (y = -40)
          - COM2: lower-mid-left (y = +40)
          - COIL_RESET: bottom-left (y = +100, 3 grid squares below COM2)
        
        Right side (x = +30, at right edge):
          - NO1: top-right (y = -60)
          - NC1: upper-mid-right (y = -20)
          - NO2: lower-mid-right (y = +20)
          - NC2: bottom-right (y = +60)
        """
        
        # Helper function to create a pin with a single tab
        def create_pin_with_tab(pin_name: str, pin_offset_x: int, pin_offset_y: int) -> Pin:
            """
            Create a pin with a single tab at the pin position.
            
            Args:
                pin_name: Name of the pin (COIL_SET, COIL_RESET, COM1, etc.)
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
        
        # NO1 pin (top-right, y = -60)
        self._no1_pin = create_pin_with_tab("NO1", right_x, -60)
        self.add_pin(self._no1_pin)
        
        # NC1 pin (upper-mid-right, y = -20)
        self._nc1_pin = create_pin_with_tab("NC1", right_x, -20)
        self.add_pin(self._nc1_pin)
        
        # NO2 pin (lower-mid-right, y = +20)
        self._no2_pin = create_pin_with_tab("NO2", right_x, 20)
        self.add_pin(self._no2_pin)
        
        # NC2 pin (bottom-right, y = +60)
        self._nc2_pin = create_pin_with_tab("NC2", right_x, 60)
        self.add_pin(self._nc2_pin)
    
    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """
        Execute relay logic with timer-based switching.
        
        Reads both coil pin states and starts a 10ms timer if state change detected.
        SET coil HIGH (alone) -> switches to SET state (COM->NO)
        RESET coil HIGH (alone) -> switches to RESET state (COM->NC)
        Both coils HIGH -> maintains current state (no change)
        State is maintained (latched) until opposite coil is energized.
        
        Args:
            vnet_manager: VnetManager instance for state tracking
            bridge_manager: BridgeManager instance for bridge operations (required)
        """
        if bridge_manager is None:
            return  # Cannot operate without bridge_manager

        if not self._coil_set_pin or not self._coil_reset_pin:
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
        
        # Determine target state based on coil inputs
        # RESET has priority when both coils are HIGH (safer default state)
        target_set = None
        set_high = (set_coil_state == PinState.HIGH)
        reset_high = (reset_coil_state == PinState.HIGH)
        
        if reset_high:
            # RESET coil HIGH - switch to RESET state (has priority)
            target_set = False
        elif set_high:
            # Only SET coil HIGH - switch to SET state
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
        """Switch relay contacts by moving bridges."""
        
        # Remove existing bridges
        if self._pole1_bridge_id:
            bridge_manager.remove_bridge(self._pole1_bridge_id)
            self._pole1_bridge_id = None
        
        if self._pole2_bridge_id:
            bridge_manager.remove_bridge(self._pole2_bridge_id)
            self._pole2_bridge_id = None
        
        # Create new bridges based on state
        if self._is_set:
            # SET state: COM→NO
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
            # RESET state: COM→NC
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
    
    def set_on_contacts_switched_callback(self, callback):
        """
        Set callback function to be called when contacts are switched.
        
        This allows the relay to trigger a simulation restart after the timer completes.
        Args:
            callback: Function to call when contacts switch (no arguments)
        """
        self._on_contacts_switched_callback = callback
    
    def sim_start(self, vnet_manager, bridge_manager):
        """
        Initialize relay for simulation start.
        
        Sets both coils to FLOAT and creates initial bridges in RESET state.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance
        """
        # Reset state to RESET (de-energized)
        self._is_set = False
        self._target_set = False
        self._timer_active = False
        
        # Initialize coil pins to FLOAT
        if self._coil_set_pin:
            self._coil_set_pin.set_state(PinState.FLOAT)
        if self._coil_reset_pin:
            self._coil_reset_pin.set_state(PinState.FLOAT)
        
        # Initialize all contact pins to FLOAT
        for pin in [self._com1_pin, self._no1_pin, self._nc1_pin,
                    self._com2_pin, self._no2_pin, self._nc2_pin]:
            if pin:
                pin.set_state(PinState.FLOAT)
        
        # Create initial bridges (RESET state: COM→NC)
        self._switch_contacts(vnet_manager, bridge_manager)
    
    def sim_stop(self, vnet_manager=None, bridge_manager=None):
        """
        Clean up relay state on simulation stop.
        
        Bridges are removed automatically by the engine via BridgeManager.
        
        Args:
            vnet_manager: VnetManager instance (unused)
            bridge_manager: BridgeManager instance (unused)
        """
        # Cancel any active timer
        with self._timer_lock:
            self._timer_active = False
        
        # Wait for timer thread to complete
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=0.1)
        
        # Clear bridge references (actual bridges removed by engine)
        self._pole1_bridge_id = None
        self._pole2_bridge_id = None
        
        # Reset state
        self._is_set = False
        self._target_set = False
    
    def interact(self, action: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Handle user interaction with relay.
        
        Relays don't support direct user interaction (controlled by coils).
        
        Args:
            action: Interaction type
            params: Additional parameters
            
        Returns:
            False (no interaction supported)
        """
        return False
    
    def get_visual_state(self) -> Dict[str, Any]:
        """
        Get relay visual state for rendering.
        
        Returns:
            Dictionary with relay_state, set_coil_state, and reset_coil_state
        """
        return {
            "relay_state": "SET" if self._is_set else "RESET",
            "set_coil_state": "HIGH" if self._coil_set_pin and self._coil_set_pin.state == PinState.HIGH else "FLOAT",
            "reset_coil_state": "HIGH" if self._coil_reset_pin and self._coil_reset_pin.state == PinState.HIGH else "FLOAT",
            "timer_active": self._timer_active
        }
    
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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LatchingRelay':
        """
        Deserialize relay from dictionary.
        
        Args:
            data: Serialized component data
            
        Returns:
            LatchingRelay instance
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
        
        # Restore color from properties
        if "color" in relay.properties:
            relay.set_color(relay.properties["color"])
        
        # Note: Pins/tabs are recreated in __init__
        # Runtime state (bridges, timers) is not serialized
        
        return relay
    
    def set_color(self, color_name: str):
        """
        Set relay color from presets.
        
        Args:
            color_name: Color name from COLOR_PRESETS
        """
        if color_name in self.COLOR_PRESETS:
            self.properties["color"] = color_name
            self.properties["on_color"] = self.COLOR_PRESETS[color_name]["on"]
            self.properties["off_color"] = self.COLOR_PRESETS[color_name]["off"]
    
    def is_set(self) -> bool:
        """
        Check if relay is currently in SET state.
        
        Returns:
            True if in SET state, False if in RESET state
        """
        return self._is_set
    
    def is_timer_active(self) -> bool:
        """
        Check if switching timer is currently active.
        
        Returns:
            True if timer running, False otherwise
        """
        with self._timer_lock:
            return self._timer_active
    
    def get_pin_by_name(self, name: str) -> Optional[Pin]:
        """
        Get pin by name for testing/debugging.
        
        Args:
            name: Pin name (COIL_SET, COIL_RESET, COM1, NO1, NC1, COM2, NO2, NC2)
            
        Returns:
            Pin instance or None
        """
        pin_map = {
            "COIL_SET": self._coil_set_pin,
            "COIL_RESET": self._coil_reset_pin,
            "COM1": self._com1_pin,
            "NO1": self._no1_pin,
            "NC1": self._nc1_pin,
            "COM2": self._com2_pin,
            "NO2": self._no2_pin,
            "NC2": self._nc2_pin,
        }
        return pin_map.get(name)
