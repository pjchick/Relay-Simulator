"""Link Component.

A small single-tab component intended as an easy way to attach a named link
(cross-page connection) to a wire.

Specs:
- 1 pin, 1 tab
- 30px wide x 10px high (rendered by LinkRenderer)
- Rotatable (0/90/180/270)
- Uses Component.link_name as the "Link Name" property
- Does not drive the network; it is a passive connection point
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class Link(Component):
    """Link component - passive named connection point."""

    component_type = "Link"

    WIDTH_PX = 30
    HEIGHT_PX = 10

    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)

        self.rotation = 0

        self._pin: Optional[Pin] = None
        self._create_pin_and_tab()

    def _create_pin_and_tab(self) -> None:
        pin_id = f"{self.component_id}.pin1"
        self._pin = Pin(pin_id, self)

        # Single connection tab aligned to 10px grid, positioned within component bounds.
        # Component is 30px wide (±15 from center), tab at x=10 is 5px from edge.
        tab_id = f"{pin_id}.tab1"
        tab = Tab(tab_id, self._pin, (10, 0))
        self._pin.add_tab(tab)

        self.add_pin(self._pin)

    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """Passive: does not drive the network."""
        # Debug: Log when Link receives HIGH signal
        if self._pin and self._pin.state == PinState.HIGH:
            print(f"Link {self.component_id} ({self.link_name}) is HIGH")
        return

    def sim_start(self, vnet_manager, bridge_manager=None):
        """Initialize to FLOAT and mark tab dirty for a clean start."""
        if not self._pin:
            return

        self._pin.set_state(PinState.FLOAT)

        # Ensure the engine considers the VNET containing this tab.
        try:
            for tab in self._pin.tabs.values():
                vnet_manager.mark_tab_dirty(tab.tab_id)
        except Exception:
            pass

    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        # Tkinter GUI uses dedicated renderers.
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Link":
        link = cls(data["component_id"], data.get("page_id", "page001"))

        pos = data.get("position", {"x": 0, "y": 0})
        link.position = (pos.get("x", 0), pos.get("y", 0))
        link.rotation = int(data.get("rotation", 0) or 0)

        if "link_name" in data:
            link.link_name = data.get("link_name")

        if "properties" in data and isinstance(data["properties"], dict):
            link.properties.update(data["properties"])

        # Backward-compatibility: some older UI paths may store link_name in properties.
        legacy = None
        try:
            legacy = link.properties.pop("link_name", None)
        except Exception:
            legacy = None
        if (not link.link_name) and isinstance(legacy, str) and legacy.strip():
            link.link_name = legacy.strip()

        return link

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()
