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
        
        # Determine fill color based on powered state
        if self.powered:
            fill_color = VSCodeTheme.INDICATOR_ON
        else:
            fill_color = VSCodeTheme.INDICATOR_OFF
            
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
        label_offset = (radius + 15) * zoom
        label_x = cx
        label_y = cy
        
        if label_position == 'bottom':
            label_y = cy + label_offset
        elif label_position == 'top':
            label_y = cy - label_offset
        elif label_position == 'left':
            label_x = cx - label_offset
        elif label_position == 'right':
            label_x = cx + label_offset
            
        self.draw_text(
            label_x, label_y,
            text=label,
            tags=('component_label', f'label_{self.component.component_id}')
        )
        
        # Draw tabs
        self.draw_tabs(zoom)
