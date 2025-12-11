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
        
        # Determine fill color based on state
        is_on = self.component._is_on
        if self.powered and is_on:
            fill_color = VSCodeTheme.SWITCH_ON
        elif is_on:
            fill_color = '#800000'  # Dark red when ON but not powered
        else:
            fill_color = VSCodeTheme.SWITCH_OFF
            
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
