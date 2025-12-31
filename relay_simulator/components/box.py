"""Box Component.

A passive annotation component for drawing rectangular boxes on circuit diagrams.
The Box component does not participate in simulation - it's purely for visual documentation.

Features:
- Adjustable color for border
- Optional fill with transparency
- Resizable via corner handles
- Always rendered on bottom layer (beneath all other components)

The Box component has no pins or tabs - it's purely decorative.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from components.base import Component


class Box(Component):
    """Box annotation component - passive rectangular box for circuit documentation."""

    component_type = "Box"

    # Default dimensions
    DEFAULT_WIDTH = 200
    DEFAULT_HEIGHT = 150

    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)

        self.properties = {
            'color': '#FFFFFF',  # White border color
            'width': self.DEFAULT_WIDTH,  # Width of box
            'height': self.DEFAULT_HEIGHT,  # Height of box
            'filled': False,  # Whether to fill the box
        }

        # Box components have no pins or tabs

    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """Passive: does not participate in simulation."""
        pass

    def sim_start(self, vnet_manager, bridge_manager):
        """Passive: no initialization needed."""
        pass

    def sim_stop(self):
        """Passive: no cleanup needed."""
        pass

    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        """
        Render method for compatibility.
        
        Tkinter GUI uses dedicated renderers instead.
        """
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any], page_id: str):
        """Create Box from dictionary data."""
        component_id = data.get('id', '')
        box = cls(component_id, page_id)
        
        # Set position
        position = data.get('position', (0, 0))
        if isinstance(position, (list, tuple)) and len(position) == 2:
            box.position = tuple(position)
        
        # Set properties
        properties = data.get('properties', {})
        if properties:
            box.properties.update(properties)
        
        return box

    def to_dict(self) -> Dict[str, Any]:
        """Convert Box to dictionary for serialization."""
        return {
            'type': self.component_type,
            'id': self.component_id,
            'position': list(self.position),
            'properties': self.properties.copy()
        }
