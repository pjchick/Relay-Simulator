"""Indicator (LED) Component for Relay Logic Simulator.

A passive visual indicator that displays the state of an electrical signal.
The indicator reads the state from its pin and displays it visually.

Visual: Circular LED, 30px diameter
Pins: 1 pin with 4 tabs at 12, 3, 6, 9 o'clock positions (on the circle edge)
State: Displays ON (bright) when pin is HIGH, OFF (dim) when pin is FLOAT
"""

from typing import Dict, Any
from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class Indicator(Component):
    """
    Indicator (LED) component - Passive signal display.
    
    Reads pin state and displays visually. Does not drive signals.
    When pin is HIGH, indicator is ON (bright).
    When pin is FLOAT, indicator is OFF (dim).
    
    Properties:
        label: Display label (optional)
        label_position: "top", "bottom", "left", or "right"
        color: Color name (affects on/off colors)
        on_color: RGB tuple for ON state (bright)
        off_color: RGB tuple for OFF state (dim)
    """
    
    component_type = "Indicator"

    # Keep component geometry consistent with the GUI renderer.
    DIAMETER_PX = 30
    RADIUS_PX = DIAMETER_PX / 2
    
    # Default colors for different color options
    COLOR_PRESETS = {
        "red": {"on": (255, 0, 0), "off": (64, 0, 0)},
        "green": {"on": (0, 255, 0), "off": (0, 64, 0)},
        "blue": {"on": (0, 0, 255), "off": (0, 0, 64)},
        "yellow": {"on": (255, 255, 0), "off": (64, 64, 0)},
        "orange": {"on": (255, 165, 0), "off": (64, 42, 0)},
        "white": {"on": (255, 255, 255), "off": (64, 64, 64)},
        "amber": {"on": (255, 191, 0), "off": (64, 48, 0)},
    }
    
    def __init__(self, component_id: str, page_id: str):
        """
        Initialize indicator component.
        
        Args:
            component_id: Unique component ID
            page_id: Page this component belongs to
        """
        super().__init__(component_id, page_id)
        
        # Set default properties
        self.properties = {
            'label': 'LED',
            'label_position': 'bottom',  # 'top', 'bottom', 'left', 'right'
            'color': 'red',
            'on_color': self.COLOR_PRESETS['red']['on'],
            'off_color': self.COLOR_PRESETS['red']['off'],
        }
        
        # Create pin and tabs
        self._create_pin_and_tabs()
    
    def _create_pin_and_tabs(self):
        """Create the single pin with 4 tabs at clock positions."""
        # Create pin
        pin_id = f"{self.component_id}.pin1"
        pin = Pin(pin_id, self)
        
        # Create 4 tabs at 12, 3, 6, 9 o'clock positions.
        # Positions relative to component center, placed on the LED circle edge.
        radius = self.RADIUS_PX
        tab_positions = {
            '12': (0, -radius),    # 12 o'clock (top)
            '3': (radius, 0),       # 3 o'clock (right)
            '6': (0, radius),       # 6 o'clock (bottom)
            '9': (-radius, 0),      # 9 o'clock (left)
        }
        
        for position_name, (x, y) in tab_positions.items():
            tab_id = f"{pin_id}.tab{position_name}"
            tab = Tab(tab_id, pin, (x, y))
            pin.add_tab(tab)
        
        self.add_pin(pin)
    
    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """
        Read pin state for display.
        
        Indicator is PASSIVE - it only reads state, never writes.
        The pin state ALWAYS stays FLOAT (indicator doesn't drive).
        The indicator determines its lit state by reading VNET states.
        
        Args:
            vnet_manager: VnetManager instance (unused - indicator never drives)
        """
        # Passive component - don't update pin state
        # Pin state should always be FLOAT (not driving)
        # Indicator determines if it should light up by checking VNETs in render code
        pass
    
    def sim_start(self, vnet_manager, bridge_manager):
        """
        Initialize indicator for simulation start.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance (unused for indicator)
        """
        # Initialize pin to FLOAT (no signal)
        pin = list(self.pins.values())[0]
        pin.set_state(PinState.FLOAT)
        
        # No need to mark tabs dirty - indicator is passive and reads state
    
    def sim_stop(self):
        """Clean up indicator state (no cleanup needed)."""
        pass
    
    def interact(self, action: str, params: Dict[str, Any] = None) -> bool:
        """
        Handle user interaction.
        
        Indicator is passive - no user interaction.
        
        Args:
            action: Action name
            params: Optional parameters
            
        Returns:
            bool: Always False (no interaction)
        """
        return False
    
    def get_visual_state(self) -> Dict[str, Any]:
        """
        Return current visual state for rendering.
        
        Returns:
            dict: Visual state including indicator ON/OFF state
        """
        state = super().get_visual_state()
        
        # Determine if indicator is ON based on pin state
        pin = list(self.pins.values())[0]
        state['indicator_state'] = 'ON' if pin.state == PinState.HIGH else 'OFF'
        
        return state
    
    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        """
        Render indicator component.
        
        Args:
            canvas_adapter: CanvasAdapter for drawing
            x_offset: X offset for panning
            y_offset: Y offset for panning
        """
        x, y = self.position
        x += x_offset
        y += y_offset
        
        # Get pin state
        pin = list(self.pins.values())[0]
        is_on = (pin.state == PinState.HIGH)
        
        # Get colors based on state
        color = self.properties['on_color'] if is_on else self.properties['off_color']
        
        # Draw circular LED (30px diameter)
        canvas_adapter.draw_circle(x, y, self.RADIUS_PX, fill_color=color, outline_color=(0, 0, 0))
        
        # Draw tabs at 12, 3, 6, 9 o'clock positions (on the circle edge)
        radius = self.RADIUS_PX
        tab_positions = [
            (x, y - radius),      # 12 o'clock
            (x + radius, y),      # 3 o'clock
            (x, y + radius),      # 6 o'clock
            (x - radius, y),      # 9 o'clock
        ]
        
        for tab_x, tab_y in tab_positions:
            canvas_adapter.draw_small_circle(tab_x, tab_y, 3, fill_color=(128, 128, 128))
        
        # Draw label if present
        label = self.properties.get('label', '')
        if label:
            label_pos = self.properties.get('label_position', 'bottom')
            label_offset = 30  # Distance from center
            
            if label_pos == 'top':
                label_x, label_y = x, y - label_offset
            elif label_pos == 'bottom':
                label_x, label_y = x, y + label_offset
            elif label_pos == 'left':
                label_x, label_y = x - label_offset, y
            else:  # right
                label_x, label_y = x + label_offset, y
            
            canvas_adapter.draw_text(label_x, label_y, label, font_size=12)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Indicator':
        """
        Deserialize indicator from dict.
        
        Args:
            data: Component data dict
            
        Returns:
            Indicator: Reconstructed indicator instance
        """
        # Create indicator
        indicator = cls(data['component_id'], data.get('page_id', 'page001'))
        
        # Restore position (schema uses {x, y} object)
        pos = data.get('position', {'x': 0, 'y': 0})
        indicator.position = (pos['x'], pos['y'])
        indicator.rotation = data.get('rotation', 0)
        indicator.link_name = data.get('link_name')
        
        # Restore properties
        if 'properties' in data:
            indicator.properties.update(data['properties'])

            # Backward-compatibility: older files/UI may have stored link_name inside properties.
            # Canonical storage is the component attribute `link_name`.
            legacy_link = None
            try:
                legacy_link = indicator.properties.pop('link_name', None)
            except Exception:
                legacy_link = None

            if (not indicator.link_name) and isinstance(legacy_link, str) and legacy_link.strip():
                indicator.link_name = legacy_link.strip()
            
            # Update color presets if color changed
            color = indicator.properties.get('color', 'red')
            if color in cls.COLOR_PRESETS:
                indicator.properties['on_color'] = cls.COLOR_PRESETS[color]['on']
                indicator.properties['off_color'] = cls.COLOR_PRESETS[color]['off']
        
        # Restore pins and tabs (schema uses arrays)
        if 'pins' in data:
            # Clear default pins
            indicator.pins.clear()
            
            # Recreate pins from data
            from core.pin import Pin
            from core.tab import Tab
            
            for pin_data in data['pins']:
                pin = Pin(pin_data['pin_id'], indicator)
                
                # Restore tabs (array in schema)
                if 'tabs' in pin_data:
                    for tab_data in pin_data['tabs']:
                        # Position is {x, y} in schema
                        pos = tab_data.get('position', {'x': 0, 'y': 0})
                        position = (pos['x'], pos['y'])
                        tab = Tab(tab_data['tab_id'], pin, position)
                        pin.add_tab(tab)
                
                indicator.add_pin(pin)
        
        return indicator
    
    def set_color(self, color_name: str):
        """
        Set indicator color from preset.
        
        Args:
            color_name: Color name from COLOR_PRESETS
        """
        if color_name in self.COLOR_PRESETS:
            self.properties['color'] = color_name
            self.properties['on_color'] = self.COLOR_PRESETS[color_name]['on']
            self.properties['off_color'] = self.COLOR_PRESETS[color_name]['off']
    
    def is_on(self) -> bool:
        """
        Check if indicator is currently ON.
        
        Returns:
            bool: True if pin state is HIGH, False otherwise
        """
        pin = list(self.pins.values())[0]
        return pin.state == PinState.HIGH
