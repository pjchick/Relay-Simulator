"""Thumbwheel Component.

A Thumbwheel is an interactive 4-bit source that drives four linked bus lines:
  {bus_name}_{start_pin + bit_index} for bit_index in 0..3

UI:
- 3x3 grid-squares in size
- Three buttons: '+' (top), 'C' (middle), '-' (bottom)

Behavior:
- '+' increments internal value (0..15) with wraparound
- '-' decrements internal value (0..15) with wraparound
- 'C' clears value to 0

Connectivity:
- Like BUS/SevenSegmentDisplay, it uses link names derived from Bus Name + Start Pin.
- Internally it has 4 hidden output pins (one per bit) so the simulation engine
  can evaluate state through the standard tab/VNET/link pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class Thumbwheel(Component):
    """Interactive 4-bit thumbwheel source."""

    component_type = "Thumbwheel"

    GRID_SQUARE_PX = 20
    WIDTH_SQUARES = 3
    HEIGHT_SQUARES = 3

    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)

        self.properties = {
            'bus_name': 'Data',
            'start_pin': 0,
            'value': 0,
        }

        self._create_hidden_output_pins()

    def _get_bus_name(self) -> str:
        name = self.properties.get('bus_name', '')
        if not isinstance(name, str):
            return ''
        return name.strip()

    def _get_start_pin(self) -> int:
        try:
            return int(self.properties.get('start_pin', 0))
        except Exception:
            return 0

    def _get_value(self) -> int:
        try:
            value = int(self.properties.get('value', 0))
        except Exception:
            value = 0
        return value & 0xF

    def _set_value(self, value: int) -> None:
        self.properties['value'] = int(value) & 0xF

    @property
    def link_ids(self) -> str:
        """Read-only display of the generated link range (e.g., Data_0...Data_3)."""
        bus_name = self._get_bus_name()
        if not bus_name:
            return ""
        start_pin = self._get_start_pin()
        return f"{bus_name}_{start_pin}...{bus_name}_{start_pin + 3}"

    def _create_hidden_output_pins(self) -> None:
        """Create 4 output pins (bit0..bit3) with tabs positioned off-body."""
        self.pins.clear()

        # Put tabs far away from the component body so they won't interfere with
        # clicking the buttons in design mode.
        hidden_x = 0
        hidden_y_base = 1000

        for bit_index in range(4):
            pin_id = f"{self.component_id}.pin{bit_index}"
            pin = Pin(pin_id, self)
            tab_id = f"{pin_id}.tab"
            tab = Tab(tab_id, pin, (hidden_x, hidden_y_base + (bit_index * 20)))
            pin.add_tab(tab)
            self.add_pin(pin)

    # --- Link integration ---

    def get_link_mappings(self) -> Dict[str, list[str]]:
        """Return per-bit link name -> tab_ids mapping."""
        bus_name = self._get_bus_name()
        if not bus_name:
            return {}

        start_pin = self._get_start_pin()
        mappings: Dict[str, list[str]] = {}
        for bit_index in range(4):
            link_name = f"{bus_name}_{start_pin + bit_index}"
            pin = self.pins.get(f"{self.component_id}.pin{bit_index}")
            if not pin:
                continue
            tab_ids = [tab.tab_id for tab in pin.tabs.values()]
            if tab_ids:
                mappings[link_name] = tab_ids
        return mappings

    # --- Simulation interface ---

    def _apply_outputs(self, vnet_manager) -> bool:
        """Apply pin outputs based on current value. Returns True if any pin changed."""
        value = self._get_value()
        changed_any = False

        for bit_index in range(4):
            pin = self.pins.get(f"{self.component_id}.pin{bit_index}")
            if not pin:
                continue

            bit_set = bool(value & (1 << bit_index))
            new_state = PinState.HIGH if bit_set else PinState.FLOAT

            if pin.state != new_state:
                pin.set_state(new_state)
                changed_any = True

                for tab in pin.tabs.values():
                    try:
                        vnet_manager.mark_tab_dirty(tab.tab_id)
                    except Exception:
                        pass

        return changed_any

    def simulate_logic(self, vnet_manager, bridge_manager=None):
        # Source component: output depends solely on internal value.
        self._apply_outputs(vnet_manager)

    def sim_start(self, vnet_manager, bridge_manager):
        # Reset value to 0 at simulation start
        self._set_value(0)
        
        # Ensure we have pins and drive initial value.
        if not self.pins or len(self.pins) != 4:
            self._create_hidden_output_pins()
        self._apply_outputs(vnet_manager)

    def sim_stop(self):
        pass

    # --- Interaction ---

    def interact(self, action: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Handle user interaction.

        Actions:
- inc: increment
- dec: decrement
- clear: set to 0
        """
        old_value = self._get_value()
        new_value = old_value

        if action == 'inc':
            new_value = (old_value + 1) & 0xF
        elif action == 'dec':
            new_value = (old_value - 1) & 0xF
        elif action in ('c', 'C', 'clear', 'reset'):
            new_value = 0
        else:
            return False

        if new_value != old_value:
            self._set_value(new_value)
            return True

        return False

    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        # Not used by the Tkinter GUI (it uses renderers), kept for compatibility.
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Thumbwheel':
        tw = cls(data['component_id'], data.get('page_id', 'page001'))

        pos = data.get('position', {'x': 0, 'y': 0})
        tw.position = (pos['x'], pos['y'])
        tw.rotation = data.get('rotation', 0)
        tw.link_name = data.get('link_name')

        if 'properties' in data and isinstance(data['properties'], dict):
            tw.properties.update(data['properties'])

        # Recreate pins to ensure the 4 outputs exist.
        tw._create_hidden_output_pins()
        return tw
