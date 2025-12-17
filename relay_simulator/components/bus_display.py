"""Bus Display Component.

A passive, pinless display that shows the state of multiple bus lines as a row
of small indicators.

Each indicator reads a link state by name:
  {bus_name}_{start_pin + bit_index}

Properties:
- bus_name: base name for links
- start_pin: first bit index
- number_of_pins: number of indicators to display
- pin_spacing: spacing between indicators in grid squares

The component has no pins/tabs and does not drive signals.
"""

from __future__ import annotations

from typing import Any, Dict

from components.base import Component


class BusDisplay(Component):
    """Passive bus-bit indicator display driven by linked bus lines."""

    component_type = "BusDisplay"

    # Geometry (kept consistent with renderer)
    GRID_SQUARE_PX = 20
    BODY_WIDTH_PX = 20
    BODY_MARGIN_PX = 10

    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)

        self.properties = {
            'bus_name': 'Bus',
            'start_pin': 0,
            'number_of_pins': 8,
            'pin_spacing': 1,
        }

        # Pinless visual component.
        self.pins = {}

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

    def _get_number_of_pins(self) -> int:
        try:
            count = int(self.properties.get('number_of_pins', 1))
        except Exception:
            count = 1
        return max(1, count)

    def _get_pin_spacing(self) -> int:
        try:
            spacing = int(self.properties.get('pin_spacing', 1))
        except Exception:
            spacing = 1
        return max(1, min(15, spacing))

    @property
    def link_ids(self) -> str:
        """Read-only display of the generated link range (e.g., Bus_0...Bus_7)."""
        bus_name = self._get_bus_name()
        if not bus_name:
            return ""

        start_pin = self._get_start_pin()
        count = self._get_number_of_pins()
        end_pin = start_pin + count - 1

        return f"{bus_name}_{start_pin}...{bus_name}_{end_pin}"

    def get_bit_link_name(self, bit_index: int) -> str:
        """Return the link name for a given displayed bit index (0-based)."""
        bus_name = self._get_bus_name()
        if not bus_name:
            return ""
        start_pin = self._get_start_pin()
        return f"{bus_name}_{start_pin + int(bit_index)}"

    # --- Simulation interface (passive) ---

    def simulate_logic(self, vnet_manager, bridge_manager=None):
        pass

    def sim_start(self, vnet_manager, bridge_manager):
        pass

    def sim_stop(self):
        pass

    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        # Not used by the Tkinter GUI (it uses renderers), kept for compatibility.
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BusDisplay':
        disp = cls(data['component_id'], data.get('page_id', 'page001'))

        pos = data.get('position', {'x': 0, 'y': 0})
        disp.position = (pos['x'], pos['y'])
        disp.rotation = data.get('rotation', 0)
        disp.link_name = data.get('link_name')

        if 'properties' in data and isinstance(data['properties'], dict):
            disp.properties.update(data['properties'])

        disp.pins = {}
        return disp
