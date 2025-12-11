"""
VCC Component for Relay Logic Simulator

A constant power source that outputs HIGH continuously.
This component provides power to circuits and always outputs HIGH.

Visual: Power symbol
Pins: 1 pin with 1 tab at 6 o'clock position (bottom)
State: Always outputs HIGH during simulation
"""

from typing import Dict, Any
from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class VCC(Component):
    """
    VCC component - Constant power source.
    
    Provides continuous HIGH signal during simulation.
    This is a power source component with no user interaction.
    
    Properties:
        label: Display label (optional, defaults to "VCC")
    """
    
    component_type = "VCC"
    
    def __init__(self, component_id: str, page_id: str):
        """
        Initialize VCC component.
        
        Args:
            component_id: Unique identifier for this component
            page_id: ID of the page this component belongs to
        """
        super().__init__(component_id, page_id)
        
        # Pin reference (set during pin creation)
        self._output_pin: Pin = None
        
        # Properties
        self.properties["label"] = "VCC"
        
        # Create pin and tab
        self._create_pin_and_tab()
    
    def _create_pin_and_tab(self):
        """Create the single pin with 1 tab at bottom position."""
        # Create pin
        pin_id = f"{self.component_id}.pin1"
        self._output_pin = Pin(pin_id, self)
        
        # Create 1 tab at 6 o'clock position (bottom)
        # Position relative to component center
        tab_id = f"{pin_id}.tab1"
        tab = Tab(tab_id, self._output_pin, (0, 20))  # 20px below center
        self._output_pin.add_tab(tab)
        
        self.add_pin(self._output_pin)
    
    def simulate_logic(self, vnet_manager):
        """
        Execute VCC logic.
        
        VCC is a constant source - no logic needed during simulation.
        Output is set to HIGH at SimStart and remains HIGH.
        
        Args:
            vnet_manager: VnetManager instance (unused)
        """
        # No logic - VCC just provides constant HIGH
        pass
    
    def sim_start(self, vnet_manager, bridge_manager=None):
        """
        Initialize VCC for simulation start.
        
        Sets output pin to HIGH.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance (unused)
        """
        if self._output_pin:
            # Set output to HIGH
            self._output_pin.set_state(PinState.HIGH)
            
            # Mark all tabs dirty so VNET gets updated
            for tab in self._output_pin.tabs.values():
                vnet = vnet_manager.get_vnet_for_tab(tab.tab_id)
                if vnet:
                    vnet.mark_dirty()
    
    def sim_stop(self, vnet_manager=None, bridge_manager=None):
        """
        Clean up VCC state on simulation stop.
        
        Sets pin to FLOAT.
        
        Args:
            vnet_manager: VnetManager instance (unused)
            bridge_manager: BridgeManager instance (unused)
        """
        if self._output_pin:
            self._output_pin.set_state(PinState.FLOAT)
    
    def interact(self, action: str, params: Dict[str, Any] = None) -> bool:
        """
        Handle user interaction with VCC.
        
        VCC has no user interaction.
        
        Args:
            action: Interaction type
            params: Additional parameters
            
        Returns:
            False (no interaction supported)
        """
        return False
    
    def get_visual_state(self) -> Dict[str, Any]:
        """
        Get VCC visual state for rendering.
        
        Returns:
            Dictionary with output state
        """
        return {
            "output_state": "HIGH" if self._output_pin and self._output_pin.state == PinState.HIGH else "FLOAT"
        }
    
    def render(self, canvas_adapter, x_offset: int = 0, y_offset: int = 0):
        """
        Render VCC on canvas.
        
        Args:
            canvas_adapter: Canvas adapter for drawing
            x_offset: X position offset
            y_offset: Y position offset
        """
        # Get absolute position
        abs_x = self.position[0] + x_offset
        abs_y = self.position[1] + y_offset
        
        # Draw VCC symbol (simplified - actual rendering depends on canvas adapter)
        # This is a placeholder for the visual representation
        color = (255, 0, 0) if self._output_pin.state == PinState.HIGH else (128, 128, 128)
        canvas_adapter.draw_circle(abs_x, abs_y, 15, color)
        
        # Draw label if present
        if self.properties.get("label"):
            canvas_adapter.draw_text(
                self.properties["label"],
                abs_x, abs_y - 25,
                position="top"
            )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VCC':
        """
        Deserialize VCC from dictionary.
        
        Args:
            data: Serialized component data
            
        Returns:
            VCC instance
        """
        vcc = cls(data["component_id"], data.get("page_id", "page001"))
        
        # Restore position (schema uses {x, y} object)
        if "position" in data:
            pos = data["position"]
            vcc.position = (pos['x'], pos['y'])
        if "rotation" in data:
            vcc.rotation = data["rotation"]
        if "link_name" in data:
            vcc.link_name = data["link_name"]
        
        # Restore properties
        if "properties" in data:
            vcc.properties.update(data["properties"])
        
        # Note: Pins/tabs are recreated in __init__
        # Runtime state is not serialized
        
        return vcc
    
    def is_on(self) -> bool:
        """
        Check if VCC is outputting HIGH.
        
        Returns:
            True if output is HIGH, False otherwise
        """
        return self._output_pin and self._output_pin.state == PinState.HIGH
    
    def get_output_pin(self) -> Pin:
        """
        Get the output pin for testing/debugging.
        
        Returns:
            Output pin instance
        """
        return self._output_pin
