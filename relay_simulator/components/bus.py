"""BUS Component for Relay Logic Simulator.

A BUS is a collection of independent linked nets.

- The bus exposes N pins arranged along a single axis.
- Each pin corresponds to a distinct link name derived from:
    {bus_name}_{start_pin + i}

The BUS is passive (does not drive signals). It exists to provide a convenient
place to connect wires to named links.
"""

from __future__ import annotations

from typing import Dict, Any, Optional

from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class BUS(Component):
    """BUS component - a collection of linked pins."""

    component_type = "BUS"

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

        self._rebuild_pins_from_properties()

    def _clamp_pin_count(self, value: Any) -> int:
        try:
            count = int(value)
        except Exception:
            count = 1
        return max(1, count)

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
        return self._clamp_pin_count(self.properties.get('number_of_pins', 1))

    def _get_pin_spacing(self) -> int:
        """Pin spacing in grid squares (1..20)."""
        try:
            spacing = int(self.properties.get('pin_spacing', 1))
        except Exception:
            spacing = 1
        return max(1, min(20, spacing))

    @property
    def link_ids(self) -> str:
        """Read-only display of the generated link range (e.g., Bus_0...Bus_7)."""
        bus_name = self._get_bus_name()
        if not bus_name:
            return ""

        start_pin = self._get_start_pin()
        count = self._get_number_of_pins()
        end_pin = start_pin + count - 1

        first = f"{bus_name}_{start_pin}"
        last = f"{bus_name}_{end_pin}"
        return f"{first}...{last}"

    def _rebuild_pins_from_properties(self) -> None:
        """Recreate pins/tabs to match current bus properties."""
        num_pins = self._get_number_of_pins()
        pin_spacing_px = self.GRID_SQUARE_PX * self._get_pin_spacing()

        # Clear and rebuild pins.
        self.pins.clear()

        # Arrange pins along a single axis (default: vertical).
        span = (num_pins - 1) * pin_spacing_px
        start_y = -(span // 2)

        # Tabs are centered on the component (so the tab center is on-grid,
        # and not half-in/half-out on the edge of the body).
        tab_x = 0

        for i in range(num_pins):
            pin_id = f"{self.component_id}.pin{i}"
            pin = Pin(pin_id, self)

            tab_id = f"{pin_id}.tab"
            tab_y = start_y + (i * pin_spacing_px)
            tab = Tab(tab_id, pin, (tab_x, tab_y))
            pin.add_tab(tab)
            self.add_pin(pin)

    def on_property_changed(self, key: str) -> None:
        """Hook called by the UI when a property changes."""
        if key in ('bus_name', 'start_pin', 'number_of_pins', 'pin_spacing'):
            self._rebuild_pins_from_properties()

    # --- Link integration ---

    def get_link_mappings(self) -> Dict[str, list[str]]:
        """Return per-pin link name -> tab_ids mapping."""
        bus_name = self._get_bus_name()
        if not bus_name:
            return {}

        start_pin = self._get_start_pin()
        mappings: Dict[str, list[str]] = {}

        # Stable ordering based on pin index.
        pins = list(self.pins.values())
        for i, pin in enumerate(pins):
            link_name = f"{bus_name}_{start_pin + i}"
            tab_ids = [tab.tab_id for tab in pin.tabs.values()]
            if tab_ids:
                mappings[link_name] = tab_ids

        return mappings

    # --- Simulation interface (passive) ---

    def simulate_logic(self, vnet_manager, bridge_manager=None):
        # Passive: never drives. Keep pins FLOAT.
        for pin in self.pins.values():
            if pin.state != PinState.FLOAT:
                pin.set_state(PinState.FLOAT)

    def sim_start(self, vnet_manager, bridge_manager):
        # Ensure structure matches properties and pins are FLOAT.
        self._rebuild_pins_from_properties()
        for pin in self.pins.values():
            pin.set_state(PinState.FLOAT)

    def sim_stop(self):
        pass

    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        # Not used by the Tkinter GUI (it uses renderers), but keep for compatibility.
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BUS':
        bus = cls(data['component_id'], data.get('page_id', 'page001'))

        pos = data.get('position', {'x': 0, 'y': 0})
        bus.position = (pos['x'], pos['y'])
        bus.rotation = data.get('rotation', 0)

        # Restore properties first (so we can rebuild pins from them)
        if 'properties' in data and isinstance(data['properties'], dict):
            bus.properties.update(data['properties'])

        # Rebuild pins from properties to ensure count matches.
        bus._rebuild_pins_from_properties()

        return bus
