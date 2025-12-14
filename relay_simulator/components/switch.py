"""
Switch Component for Relay Logic Simulator

A switch component that can operate in two modes:
- Toggle mode: Click to toggle ON/OFF, stays in position
- Pushbutton mode: ON while pressed, OFF when released

Visual: Circular button, 40px diameter
Pins: 1 pin with 4 tabs at 12, 3, 6, 9 o'clock positions
"""

from typing import Dict, Any, Optional
from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState
import uuid


class Switch(Component):
    """
    Switch component - User-controlled signal source.
    
    Can operate as toggle switch (latching) or pushbutton (momentary).
    When ON, outputs HIGH. When OFF, outputs FLOAT.
    
    Properties:
        mode: "toggle" or "pushbutton"
        label: Display label (optional)
        label_position: "top", "bottom", "left", or "right"
        color: Color name (affects on/off colors)
        on_color: RGB tuple for ON state
        off_color: RGB tuple for OFF state
    """
    
    component_type = "Switch"
    
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
    
    def __init__(self, component_id: str, page_id: str):
        """
        Initialize switch component.
        
        Args:
            component_id: Unique component ID
            page_id: Page this component belongs to
        """
        super().__init__(component_id, page_id)
        
        # Internal state
        self._is_on = False  # Current switch state
        
        # Set default properties
        self.properties = {
            'mode': 'toggle',  # 'toggle' or 'pushbutton'
            'label': 'SW',
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
        
        # Create 4 tabs at 12, 3, 6, 9 o'clock positions
        # Positions relative to component center (40px diameter = 20px radius)
        radius = 20
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
    
    def simulate_logic(self, vnet_manager):
        """
        Update switch output based on current state.
        
        Switch is a signal SOURCE, so it doesn't read inputs.
        It only outputs based on its internal state.
        
        Args:
            vnet_manager: VnetManager instance for marking VNETs dirty
        """
        # Switch outputs based on its state
        new_state = PinState.HIGH if self._is_on else PinState.FLOAT
        
        # Get the pin
        pin = list(self.pins.values())[0]
        
        print(f"DEBUG Switch.simulate_logic: _is_on={self._is_on}, new_state={new_state}, current pin.state={pin.state}")
        
        # Update pin state if changed
        if pin.state != new_state:
            pin.set_state(new_state)
            print(f"DEBUG Switch: Pin state updated to {new_state}")
            
            # Mark all VNETs containing our tabs as dirty
            for tab in pin.tabs.values():
                vnet_manager.mark_tab_dirty(tab.tab_id)
        else:
            print(f"DEBUG Switch: Pin state unchanged")
    
    def sim_start(self, vnet_manager, bridge_manager):
        """
        Initialize switch for simulation start.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance (unused for switch)
        """
        # Start in OFF state by default
        self._is_on = False
        
        # Set initial pin state
        pin = list(self.pins.values())[0]
        pin.set_state(PinState.FLOAT)
        
        # Mark all our tabs dirty so VNETs get initial state
        for tab in pin.tabs.values():
            vnet_manager.mark_tab_dirty(tab.tab_id)
    
    def sim_stop(self):
        """Clean up switch state."""
        self._is_on = False
    
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
                self._is_on = not self._is_on
                return True
        
        elif mode == 'pushbutton':
            # Pushbutton mode: ON when pressed, OFF when released
            if action == 'press':
                if not self._is_on:
                    self._is_on = True
                    return True
            elif action == 'release':
                if self._is_on:
                    self._is_on = False
                    return True
        
        return False
    
    def get_visual_state(self) -> Dict[str, Any]:
        """
        Return current visual state for rendering.
        
        Returns:
            dict: Visual state including switch ON/OFF state
        """
        state = super().get_visual_state()
        state['switch_state'] = 'ON' if self._is_on else 'OFF'
        return state
    
    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        """
        Render switch component.
        
        Args:
            canvas_adapter: CanvasAdapter for drawing
            x_offset: X offset for panning
            y_offset: Y offset for panning
        """
        x, y = self.position
        x += x_offset
        y += y_offset
        
        # Get colors based on state
        color = self.properties['on_color'] if self._is_on else self.properties['off_color']
        
        # Draw circular button (40px diameter)
        canvas_adapter.draw_circle(x, y, 20, fill_color=color, outline_color=(0, 0, 0))
        
        # Draw tabs at 12, 3, 6, 9 o'clock positions
        radius = 20
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
    def from_dict(cls, data: Dict[str, Any]) -> 'Switch':
        """
        Deserialize switch from dict.
        
        Args:
            data: Component data dict
            
        Returns:
            Switch: Reconstructed switch instance
        """
        # Create switch
        switch = cls(data['component_id'], data.get('page_id', 'page001'))
        
        # Restore position (schema uses {x, y} object)
        pos = data.get('position', {'x': 0, 'y': 0})
        switch.position = (pos['x'], pos['y'])
        switch.rotation = data.get('rotation', 0)
        switch.link_name = data.get('link_name')
        
        # Restore properties
        if 'properties' in data:
            switch.properties.update(data['properties'])
            
            # Update color presets if color changed
            color = switch.properties.get('color', 'red')
            if color in cls.COLOR_PRESETS:
                switch.properties['on_color'] = cls.COLOR_PRESETS[color]['on']
                switch.properties['off_color'] = cls.COLOR_PRESETS[color]['off']
        
        # Restore pins and tabs (schema uses arrays)
        if 'pins' in data:
            # Clear default pins
            switch.pins.clear()
            
            # Recreate pins from data
            from core.pin import Pin
            from core.tab import Tab
            
            for pin_data in data['pins']:
                pin = Pin(pin_data['pin_id'], switch)
                
                # Restore tabs (array in schema)
                if 'tabs' in pin_data:
                    for tab_data in pin_data['tabs']:
                        # Position is {x, y} in schema
                        pos = tab_data.get('position', {'x': 0, 'y': 0})
                        position = (pos['x'], pos['y'])
                        tab = Tab(tab_data['tab_id'], pin, position)
                        pin.add_tab(tab)
                
                switch.add_pin(pin)
        
        return switch
    
    def set_color(self, color_name: str):
        """
        Set switch color from preset.
        
        Args:
            color_name: Color name from COLOR_PRESETS
        """
        if color_name in self.COLOR_PRESETS:
            self.properties['color'] = color_name
            self.properties['on_color'] = self.COLOR_PRESETS[color_name]['on']
            self.properties['off_color'] = self.COLOR_PRESETS[color_name]['off']
    
    def get_state(self) -> bool:
        """
        Get switch state.
        
        Returns:
            bool: True if ON, False if OFF
        """
        return self._is_on
    
    def set_state(self, is_on: bool):
        """
        Set switch state programmatically.
        
        Args:
            is_on: True for ON, False for OFF
        """
        self._is_on = is_on
    
    def toggle_switch(self):
        """
        Toggle the switch state (ON ↔ OFF).
        Used in simulation mode for user interaction.
        """
        self._is_on = not self._is_on
    
    def get_state(self) -> bool:
        """
        Get current switch state.
        
        Returns:
            True if ON, False if OFF
        """
        return self._is_on
