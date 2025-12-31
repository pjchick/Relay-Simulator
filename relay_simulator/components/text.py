"""Text Component.

A passive annotation component for adding text labels to circuit diagrams.
The Text component does not participate in simulation - it's purely for visual documentation.

Features:
- Multi-line text support
- Adjustable font size
- Adjustable text color
- Fixed-width console font (Consolas/Courier New)
- Left or right text justification
- Configurable width for multi-line wrapping

The Text component has no pins or tabs - it's purely decorative.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from components.base import Component


class Text(Component):
    """Text annotation component - passive label for circuit documentation."""

    component_type = "Text"

    # Default dimensions (can be adjusted based on content)
    DEFAULT_WIDTH = 200
    DEFAULT_HEIGHT = 40

    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)

        self.properties = {
            'text': 'Text',
            'font_size': 12,
            'color': '#FFFFFF',  # White
            'multiline': False,
            'justify': 'left',  # 'left' or 'right'
            'width': self.DEFAULT_WIDTH,  # Width for text wrapping
            'height': self.DEFAULT_HEIGHT,  # Height of text box
            'border': False,  # Whether to show border
        }

        # Text components have no pins or tabs

    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """Passive: does not participate in simulation."""
        pass

    def sim_start(self, vnet_manager, bridge_manager=None):
        """Passive: no initialization needed."""
        pass

    def sim_stop(self):
        """Passive: no cleanup needed."""
        pass

    def interact(self, action: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Text components don't respond to interaction during simulation.
        
        Returns:
            False (no interaction supported)
        """
        return False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Text":
        """Deserialize Text component from dictionary."""
        text = cls(data["component_id"], data.get("page_id", "page001"))

        pos = data.get("position", {"x": 0, "y": 0})
        text.position = (pos.get("x", 0), pos.get("y", 0))

        if "properties" in data and isinstance(data["properties"], dict):
            text.properties.update(data["properties"])

        return text

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Text component to dictionary."""
        return super().to_dict()

    def get_visual_state(self) -> Dict[str, Any]:
        """
        Get visual state for rendering.
        
        Returns:
            Dictionary with text properties
        """
        return {
            'text': self.properties.get('text', 'Text'),
            'font_size': self.properties.get('font_size', 12),
            'color': self.properties.get('color', '#FFFFFF'),
            'multiline': self.properties.get('multiline', False),
            'justify': self.properties.get('justify', 'left'),
            'width': self.properties.get('width', self.DEFAULT_WIDTH),
            'height': self.properties.get('height', self.DEFAULT_HEIGHT),
            'border': self.properties.get('border', False),
        }

    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        """
        Render method for compatibility.
        
        Tkinter GUI uses dedicated renderers instead.
        """
        pass
