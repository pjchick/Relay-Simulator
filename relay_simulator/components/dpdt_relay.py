"""
DPDT Relay Component for Relay Logic Simulator

A Double Pole Double Throw (DPDT) relay with realistic timing behavior.
The relay switches two independent poles between normally-closed (NC) and 
normally-open (NO) contacts based on coil energization.

Visual: Relay symbol with coil and two poles
Pins: 7 pins total
  - 1 coil pin (COIL)
  - Pole 1: COM1, NO1, NC1 (3 pins)
  - Pole 2: COM2, NO2, NC2 (3 pins)

Timing: 10ms delay when coil state changes before contacts switch
State: Energized when coil is HIGH, De-energized when coil is FLOAT
"""

from typing import Dict, Any, Optional
import time
import threading
from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class DPDTRelay(Component):
    """
    DPDT Relay component - Electromechanical relay with two poles.
    
    Each pole switches between NC (normally-closed) and NO (normally-open)
    contacts when the coil is energized. Includes realistic 10ms switching delay.
    
    Properties:
        label: Display label (optional)
        label_position: "top", "bottom", "left", or "right"
        color: Color name (affects coil on/off colors)
        on_color: RGB tuple for energized state
        off_color: RGB tuple for de-energized state
        rotation: 0, 90, 180, 270 degrees
        flip_horizontal: True/False
        flip_vertical: True/False
    
    Pin Configuration:
        COIL: Energizes relay when HIGH
        Pole 1: COM1, NO1, NC1
        Pole 2: COM2, NO2, NC2
    
    Bridge Behavior:
        De-energized: COM1→NC1, COM2→NC2
        Energized: COM1→NO1, COM2→NO2
    """
    
    component_type = "DPDTRelay"
    
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
        Initialize DPDT relay component.
        
        Args:
            component_id: Unique identifier for this component
            page_id: ID of the page this component belongs to
        """
        super().__init__(component_id, page_id)
        
        # Internal state
        self._is_energized = False  # Current relay state
        self._target_energized = False  # Target state after timer
        self._timer_active = False  # Whether timer is running
        self._timer_thread: Optional[threading.Thread] = None
        self._timer_lock = threading.Lock()
        
        # Bridge references (runtime only)
        self._pole1_bridge_id: Optional[str] = None
        self._pole2_bridge_id: Optional[str] = None
        
        # Pin references (set during pin creation)
        self._coil_pin: Optional[Pin] = None
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
        self.properties["rotation"] = 0
        self.properties["flip_horizontal"] = False
        self.properties["flip_vertical"] = False
        
        # Set default colors
        self.set_color("blue")
        
        # Create pins and tabs
        self._create_pins_and_tabs()
    
    def _create_pins_and_tabs(self):
        """Create all 7 pins with 4 tabs each at clock positions."""
        radius = 20  # Distance from center to tab
        
        # Helper function to create a pin with 4 tabs
        def create_pin_with_tabs(pin_name: str) -> Pin:
            pin_id = f"{self.component_id}.{pin_name}"
            pin = Pin(pin_id, self)
            
            # Create 4 tabs at clock positions
            tab_positions = [
                (0, -radius),   # 12 o'clock (top)
                (radius, 0),    # 3 o'clock (right)
                (0, radius),    # 6 o'clock (bottom)
                (-radius, 0),   # 9 o'clock (left)
            ]
            
            for idx, pos in enumerate(tab_positions):
                tab_id = f"{pin_id}.tab{idx}"
                tab = Tab(tab_id, pin, pos)
                pin.add_tab(tab)
            
            return pin
        
        # Create all 7 pins
        self._coil_pin = create_pin_with_tabs("COIL")
        self.add_pin(self._coil_pin)
        
        self._com1_pin = create_pin_with_tabs("COM1")
        self.add_pin(self._com1_pin)
        
        self._no1_pin = create_pin_with_tabs("NO1")
        self.add_pin(self._no1_pin)
        
        self._nc1_pin = create_pin_with_tabs("NC1")
        self.add_pin(self._nc1_pin)
        
        self._com2_pin = create_pin_with_tabs("COM2")
        self.add_pin(self._com2_pin)
        
        self._no2_pin = create_pin_with_tabs("NO2")
        self.add_pin(self._no2_pin)
        
        self._nc2_pin = create_pin_with_tabs("NC2")
        self.add_pin(self._nc2_pin)
    
    def simulate_logic(self, vnet_manager, bridge_manager):
        """
        Execute relay logic with timer-based switching.
        
        Reads coil pin state and starts a 10ms timer if state change detected.
        When timer completes, switches bridges between NC and NO contacts.
        
        Args:
            vnet_manager: VnetManager instance for state tracking
            bridge_manager: BridgeManager instance for bridge operations
        """
        if not self._coil_pin:
            return
        
        # Read current coil state
        coil_state = self._coil_pin.state
        target_energized = (coil_state == PinState.HIGH)
        
        # Check if state change needed
        with self._timer_lock:
            if target_energized != self._target_energized:
                # State change detected - start timer
                self._target_energized = target_energized
                
                if not self._timer_active:
                    # Start new timer
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
        
        Switches bridges and updates relay state.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance
        """
        # Wait for switching delay
        time.sleep(self.SWITCHING_DELAY)
        
        with self._timer_lock:
            # Check if target state still matches
            if self._target_energized != self._is_energized:
                # Update energized state first
                self._is_energized = self._target_energized
                # Then switch bridges based on new state
                self._switch_contacts(vnet_manager, bridge_manager)
            
            self._timer_active = False
    
    def _switch_contacts(self, vnet_manager, bridge_manager):
        """
        Switch relay contacts by moving bridges.
        
        Removes old bridges and creates new ones based on energized state.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance
        """
        # Remove existing bridges
        if self._pole1_bridge_id:
            bridge_manager.remove_bridge(self._pole1_bridge_id)
            self._pole1_bridge_id = None
        
        if self._pole2_bridge_id:
            bridge_manager.remove_bridge(self._pole2_bridge_id)
            self._pole2_bridge_id = None
        
        # Create new bridges based on state
        if self._is_energized:
            # Energized: COM→NO
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
            # De-energized: COM→NC
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
    
    def sim_start(self, vnet_manager, bridge_manager):
        """
        Initialize relay for simulation start.
        
        Sets coil to FLOAT and creates initial bridges in de-energized state.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance
        """
        # Reset state
        self._is_energized = False
        self._target_energized = False
        self._timer_active = False
        
        # Initialize coil pin to FLOAT
        if self._coil_pin:
            self._coil_pin.set_state(PinState.FLOAT)
        
        # Initialize all contact pins to FLOAT
        for pin in [self._com1_pin, self._no1_pin, self._nc1_pin,
                    self._com2_pin, self._no2_pin, self._nc2_pin]:
            if pin:
                pin.set_state(PinState.FLOAT)
        
        # Create initial bridges (de-energized: COM→NC)
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
        self._is_energized = False
        self._target_energized = False
    
    def interact(self, action: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Handle user interaction with relay.
        
        Relays don't support direct user interaction (controlled by coil).
        
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
            Dictionary with relay_state and coil_state
        """
        return {
            "relay_state": "ENERGIZED" if self._is_energized else "DE-ENERGIZED",
            "coil_state": "HIGH" if self._coil_pin and self._coil_pin.state == PinState.HIGH else "FLOAT",
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
        
        # Choose color based on energized state
        color = self.properties["on_color"] if self._is_energized else self.properties["off_color"]
        
        # Draw relay symbol (simplified - actual rendering depends on canvas adapter)
        # This is a placeholder for the visual representation
        canvas_adapter.draw_rectangle(abs_x - 30, abs_y - 40, 60, 80, color)
        
        # Draw label if present
        if self.properties.get("label"):
            label_pos = self.properties.get("label_position", "top")
            canvas_adapter.draw_text(
                self.properties["label"],
                abs_x, abs_y,
                position=label_pos
            )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DPDTRelay':
        """
        Deserialize relay from dictionary.
        
        Args:
            data: Serialized component data
            
        Returns:
            DPDTRelay instance
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
    
    def is_energized(self) -> bool:
        """
        Check if relay is currently energized.
        
        Returns:
            True if energized, False if de-energized
        """
        return self._is_energized
    
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
            name: Pin name (COIL, COM1, NO1, NC1, COM2, NO2, NC2)
            
        Returns:
            Pin instance or None
        """
        pin_map = {
            "COIL": self._coil_pin,
            "COM1": self._com1_pin,
            "NO1": self._no1_pin,
            "NC1": self._nc1_pin,
            "COM2": self._com2_pin,
            "NO2": self._no2_pin,
            "NC2": self._nc2_pin,
        }
        return pin_map.get(name)
