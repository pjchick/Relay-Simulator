"""Seven Segment Display Component.

A passive display that shows a hexadecimal digit (0..F) by reading 4 linked
bus lines.

This component has no pins/tabs. It reads link states by name:
  {bus_name}_{start_pin + bit_index} for bit_index in 0..3

Geometry (GUI): 3 grid squares wide x 4 grid squares high.
"""

from __future__ import annotations

from typing import Any, Dict, List

from components.base import Component


class SevenSegmentDisplay(Component):
    """Passive 7-segment hex display (0..F) driven by 4 bus link lines."""

    component_type = "SevenSegmentDisplay"

    GRID_SQUARE_PX = 20
    WIDTH_SQUARES = 3
    HEIGHT_SQUARES = 4

    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)

        self.properties = {
            'bus_name': 'Data',
            'start_pin': 0,
            'color': 'green',
        }

        # No pins/tabs. This component is purely visual.
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

    def get_nibble_link_names(self) -> List[str]:
        """Return the 4 link names used for input bits 0..3."""
        bus_name = self._get_bus_name()
        start_pin = self._get_start_pin()
        if not bus_name:
            return []
        return [f"{bus_name}_{start_pin + i}" for i in range(4)]

    @property
    def link_ids(self) -> str:
        """Read-only display of the generated link range (e.g., Data_0...Data_3)."""
        bus_name = self._get_bus_name()
        if not bus_name:
            return ""

        start_pin = self._get_start_pin()
        end_pin = start_pin + 3
        return f"{bus_name}_{start_pin}...{bus_name}_{end_pin}"

    # --- Simulation interface (passive) ---

    def simulate_logic(self, vnet_manager, bridge_manager=None):
        # Passive: no pins to drive.
        pass

    def sim_start(self, vnet_manager, bridge_manager):
        # No pins/tabs to initialize.
        pass

    def sim_stop(self):
        pass

    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        # Not used by the Tkinter GUI (it uses renderers), kept for compatibility.
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SevenSegmentDisplay':
        disp = cls(data['component_id'], data.get('page_id', 'page001'))

        pos = data.get('position', {'x': 0, 'y': 0})
        disp.position = (pos['x'], pos['y'])
        disp.rotation = data.get('rotation', 0)
        disp.link_name = data.get('link_name')

        if 'properties' in data and isinstance(data['properties'], dict):
            disp.properties.update(data['properties'])

        # Ensure no pins even if legacy data includes them.
        disp.pins = {}
        return disp
