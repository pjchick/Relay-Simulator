"""
Indicator (LED) component renderer.

Renders a circular LED indicator that lights up when powered.
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class IndicatorRenderer(ComponentRenderer):
    """
    Renderer for Indicator (LED) components.
    
    Visual appearance:
    - Circular LED (30px diameter)
    - Lights up (bright color) when powered
    - Dim when unpowered
    - Label below (or at specified position)
    - 4 tabs at 12, 3, 6, 9 o'clock positions
    """
    
    DIAMETER = 30  # Indicator diameter in pixels
    LABEL_PADDING_PX = 20  # Extra gap between LED edge and label

    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing (LED circle only, no label)."""
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
        return VSCodeTheme.INDICATOR_OFF
    
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the indicator component.
        
        Args:
            zoom: Current zoom level
        """
        # Clear previous rendering
        self.clear()
        
        cx, cy = self.get_position()
        radius = (self.DIAMETER / 2) * zoom
        
        # Determine fill color based on powered state and component-selected color
        on_rgb = self.component.properties.get('on_color')
        off_rgb = self.component.properties.get('off_color')
        fill_color = self._to_hex(on_rgb) if self.powered else self._to_hex(off_rgb)
            
        # Outline color (highlight if selected)
        outline_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        outline_width = 3 if self.selected else 2
        
        # Draw circular LED
        self.draw_circle(
            cx, cy, radius,
            fill=fill_color,
            outline=outline_color,
            width_px=outline_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw label
        label = self.component.properties.get('label', 'LED')
        label_position = self.component.properties.get('label_position', 'bottom')
        
        # Calculate label position
        # Keep label a bit away from the LED, and scale padding with zoom.
        label_offset = radius + (self.LABEL_PADDING_PX * zoom)
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
