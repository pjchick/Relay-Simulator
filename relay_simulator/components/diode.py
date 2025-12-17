"""Diode Component.

A simple 2-pin diode that allows HIGH to propagate one way:
- Anode (A) -> Cathode (K)

Behavior:
- If Anode's connected VNET is HIGH, the Cathode pin is driven HIGH.
- Otherwise, Cathode is FLOAT.
- No reverse propagation is performed.

Rotation:
- Supports 0/90/180/270 via the base Component.rotation attribute.
"""

from __future__ import annotations

from typing import Dict, Any, Optional

from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class Diode(Component):
    """Diode component - one-way HIGH propagation (A -> K)."""

    component_type = "Diode"

    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)

        # Standard label support (matches other components)
        self.properties = {
            'label': '',
            'label_position': 'bottom',
        }
        self.rotation = 0

        self._anode_pin: Optional[Pin] = None
        self._cathode_pin: Optional[Pin] = None

        self._create_pins_and_tabs()

    def _create_pins_and_tabs(self) -> None:
        """Create the two pins and single tabs."""

        def create_pin_with_tab(pin_name: str, x: int, y: int) -> Pin:
            pin_id = f"{self.component_id}.{pin_name}"
            pin = Pin(pin_id, self)
            tab_id = f"{pin_id}.tab0"
            tab = Tab(tab_id, pin, (x, y))
            pin.add_tab(tab)
            return pin

        # Default orientation: Anode on left, Cathode on right
        self._anode_pin = create_pin_with_tab("A", -30, 0)
        self._cathode_pin = create_pin_with_tab("K", 30, 0)

        self.add_pin(self._anode_pin)
        self.add_pin(self._cathode_pin)

    def _read_pin_high(self, vnet_manager, pin: Optional[Pin]) -> bool:
        """Passive input read from VNET state."""
        if not vnet_manager or not pin or not pin.tabs:
            return False

        try:
            tab = next(iter(pin.tabs.values()))
        except Exception:
            return False

        try:
            vnet = vnet_manager.get_vnet_for_tab(tab.tab_id)
        except Exception:
            vnet = None

        state = getattr(vnet, 'state', None) if vnet else None
        return state == PinState.HIGH or state is True or state == 1

    def _set_pin_state(self, vnet_manager, pin: Optional[Pin], new_state: PinState) -> None:
        if not vnet_manager or not pin:
            return

        if pin.state == new_state:
            return

        pin.set_state(new_state)
        for tab in pin.tabs.values():
            vnet_manager.mark_tab_dirty(tab.tab_id)

    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """Propagate HIGH from Anode to Cathode."""
        anode_high = self._read_pin_high(vnet_manager, self._anode_pin)

        # Drive cathode only based on anode state.
        cathode_state = PinState.HIGH if anode_high else PinState.FLOAT
        self._set_pin_state(vnet_manager, self._cathode_pin, cathode_state)

        # Never drive anode based on cathode.
        # (Leaving anode FLOAT ensures no reverse propagation.)

    def sim_start(self, vnet_manager, bridge_manager):
        """Initialize diode pin states."""
        # Start with no drive on the cathode.
        self._set_pin_state(vnet_manager, self._cathode_pin, PinState.FLOAT)

    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        # Not used by Tkinter GUI (uses renderers)
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Diode':
        diode = cls(data['component_id'], data.get('page_id', 'page001'))

        pos = data.get('position', {'x': 0, 'y': 0})
        diode.position = (pos['x'], pos['y'])
        diode.rotation = data.get('rotation', 0)
        diode.link_name = data.get('link_name')

        if 'properties' in data and isinstance(data['properties'], dict):
            diode.properties.update(data['properties'])

        return diode

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()
