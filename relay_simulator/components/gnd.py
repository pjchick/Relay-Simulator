"""
Relay GND Component for Relay Logic Simulator

A ground reference component specifically designed for relay circuits.
This component marks a net as grounded and is used by Ground DPDT Relays
to determine energization state.

Visual: Ground symbol (three horizontal lines decreasing in length)
Pins: 1 pin with 1 tab at 12 o'clock position (top)
State: Always FLOAT (passive component), but identifiable by component type
"""

from typing import Dict, Any
from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class GND(Component):
    """
    Relay GND component - Ground reference point for relay circuits.
    
    This is a passive component that marks a net as connected to ground.
    Ground DPDT Relays check if their GND pin is connected to this component
    to determine if they should energize.
    
    Properties:
        label: Display label (optional, defaults to "GND")
    """
    
    component_type = "GND"
    
    def __init__(self, component_id: str, page_id: str):
        """
        Initialize GND component.
        
        Args:
            component_id: Unique identifier for this component
            page_id: ID of the page this component belongs to
        """
        super().__init__(component_id, page_id)
        
        # Pin reference (set during pin creation)
        self._gnd_pin: Pin = None
        
        # Properties
        self.properties["label"] = ""
        
        # Set default rotation
        self.rotation = 0
        
        # Create pin and tab
        self._create_pin_and_tab()
    
    def _create_pin_and_tab(self):
        """Create the single pin with 1 tab at top (12 o'clock)."""
        # Create pin
        pin_id = f"{self.component_id}.pin1"
        self._gnd_pin = Pin(pin_id, self)
        
        # Create tab at top (0, 0) - renderer will position symbol below
        tab_id = f"{pin_id}.tab1"
        tab = Tab(tab_id, self._gnd_pin, (0, 0))
        self._gnd_pin.add_tab(tab)
        
        self.add_pin(self._gnd_pin)
    
    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """
        Execute GND logic.
        
        GND is a passive component - no logic needed during simulation.
        It simply marks the net as grounded for other components to check.
        
        Args:
            vnet_manager: VnetManager instance (unused)
            bridge_manager: BridgeManager instance (unused)
        """
        # No active logic - GND is passive
        pass
    
    def sim_start(self, vnet_manager, bridge_manager=None):
        """
        Initialize GND for simulation start.
        
        Sets pin to FLOAT (passive component).
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance (unused)
        """
        if self._gnd_pin:
            # Set to FLOAT (passive component)
            self._gnd_pin.set_state(PinState.FLOAT)
    
    def sim_stop(self):
        """
        Clean up GND state on simulation stop.
        
        No cleanup needed for passive component.
        """
        pass
    
    def interact(self, action: str, params: Dict[str, Any] = None) -> bool:
        """
        Handle user interaction with GND.
        
        GND components don't support user interaction.
        
        Args:
            action: Interaction type
            params: Additional parameters
            
        Returns:
            False (no interaction supported)
        """
        return False
    
    def get_visual_state(self) -> Dict[str, Any]:
        """
        Get GND visual state for rendering.
        
        Returns:
            Dictionary with component state info
        """
        return {
            "component_type": "GND"
        }
    
    def render(self, canvas_adapter, x_offset: int = 0, y_offset: int = 0):
        """
        Render GND symbol on canvas.
        
        Args:
            canvas_adapter: Canvas adapter for drawing
            x_offset: X position offset
            y_offset: Y position offset
        """
        # Get absolute position
        abs_x = self.position[0] + x_offset
        abs_y = self.position[1] + y_offset
        
        # Draw ground symbol (three horizontal lines decreasing in width)
        # This is a placeholder - actual rendering handled by renderer
        line_color = (0, 0, 0)  # Black
        
        # Top line (widest)
        canvas_adapter.draw_line(abs_x - 15, abs_y + 5, abs_x + 15, abs_y + 5, line_color)
        # Middle line
        canvas_adapter.draw_line(abs_x - 10, abs_y + 10, abs_x + 10, abs_y + 10, line_color)
        # Bottom line (narrowest)
        canvas_adapter.draw_line(abs_x - 5, abs_y + 15, abs_x + 5, abs_y + 15, line_color)
        
        # Draw connection line to top
        canvas_adapter.draw_line(abs_x, abs_y, abs_x, abs_y + 5, line_color)
        
        # Draw label if present
        if self.properties.get("label"):
            canvas_adapter.draw_text(
                self.properties["label"],
                abs_x, abs_y - 10,
                position="top"
            )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GND':
        """
        Deserialize GND component from dictionary.
        
        Args:
            data: Serialized component data
            
        Returns:
            GND instance
        """
        gnd = cls(data["component_id"], data.get("page_id", "page001"))
        
        # Restore position (schema uses {x, y} object)
        if "position" in data:
            pos = data["position"]
            gnd.position = (pos['x'], pos['y'])
        if "rotation" in data:
            gnd.rotation = data["rotation"]
        if "link_name" in data:
            gnd.link_name = data["link_name"]
        
        # Restore properties
        if "properties" in data:
            gnd.properties.update(data["properties"])
        
        return gnd
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize GND component to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "page_id": self.page_id,
            "position": {"x": self.position[0], "y": self.position[1]},
            "rotation": self.rotation,
            "properties": self.properties.copy(),
            "link_name": self.link_name
        }
