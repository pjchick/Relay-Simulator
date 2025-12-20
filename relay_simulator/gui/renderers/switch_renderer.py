"""
Switch component renderer.

Renders a circular switch button with tabs at clock positions.
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class SwitchRenderer(ComponentRenderer):
    """
    Renderer for Switch components.
    
    Visual appearance:
    - Circular button (40px diameter)
    - Color changes based on ON/OFF state
    - Label below (or at specified position)
    - 4 tabs at 12, 3, 6, 9 o'clock positions
    """
    
    DIAMETER = 40  # Switch diameter in pixels

    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing (button circle only, no label)."""
        cx, cy = self.component.position
        radius = self.DIAMETER / 2
        return (cx - radius, cy - radius, cx + radius, cy + radius)

    @staticmethod
    def _to_hex(color) -> str:
        """Convert (r,g,b) or [r,g,b] to '#rrggbb'. Pass through hex strings."""
        if isinstance(color, str):
            return color
        if isinstance(color, (tuple, list)) and len(color) >= 3:
            try:
                r, g, b = int(color[0]), int(color[1]), int(color[2])
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                return f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                pass
        return VSCodeTheme.SWITCH_OFF
    
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the switch component.
        
        Args:
            zoom: Current zoom level
        """
        # Clear previous rendering
        self.clear()
        
        cx, cy = self.get_position()
        radius = (self.DIAMETER / 2) * zoom
        
        # Determine fill color based on state:
        # - Bright when ON
        # - Dull when OFF but seeing HIGH (powered)
        # - Dark when OFF
        is_on = self.component._is_on
        if is_on:
            fill_color = self._to_hex(self.component.properties.get('on_color', VSCodeTheme.SWITCH_ON))
        elif self.powered:
            fill_color = self._to_hex(self.component.properties.get('dull_color', '#804040'))
        else:
            fill_color = self._to_hex(self.component.properties.get('off_color', VSCodeTheme.SWITCH_OFF))
            
        # Outline color (highlight if selected)
        outline_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        outline_width = 3 if self.selected else 2
        
        # Draw circular button
        self.draw_circle(
            cx, cy, radius,
            fill=fill_color,
            outline=outline_color,
            width_px=outline_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw label
        label = self.component.properties.get('label', 'SW')
        label_position = self.component.properties.get('label_position', 'bottom')
        
        # Calculate label position
        label_offset = (radius + 15) * zoom
        label_x = cx
        label_y = cy
        anchor = 'center'
        
        if label_position == 'bottom':
            label_y = cy + label_offset
            anchor = 'n'
        elif label_position == 'top':
            label_y = cy - label_offset
            anchor = 's'
        elif label_position == 'left':
            label_x = cx - label_offset
            anchor = 'e'  # right-justified when on the left
        elif label_position == 'right':
            label_x = cx + label_offset
            anchor = 'w'  # left-justified when on the right
            
        self.draw_text(
            label_x, label_y,
            text=label,
            anchor=anchor,
            tags=('component_label', f'label_{self.component.component_id}')
        )
        
        # Draw tabs
        self.draw_tabs(zoom)
