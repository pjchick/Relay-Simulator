"""
VCC (Power Source) component renderer.

Renders a VCC symbol (+ in circle with voltage label).
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class VCCRenderer(ComponentRenderer):
    """
    Renderer for VCC (power source) components.
    
    Visual appearance:
    - Circle with + symbol (22px diameter)
    - Red color to indicate power source
    - Tab at center
    """
    
    DIAMETER = 22  # VCC symbol diameter in pixels
    
    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing (circle only, no label)."""
        cx, cy = self.component.position
        radius = self.DIAMETER / 2
        return (cx - radius, cy - radius, cx + radius, cy + radius)
    
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the VCC component.
        
        Args:
            zoom: Current zoom level
        """
        # Clear previous rendering
        self.clear()
        
        cx, cy = self.get_position()
        radius = (self.DIAMETER / 2) * zoom
        
        # Outline color (highlight if selected)
        outline_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        outline_width = 3 if self.selected else 2
        
        # Draw circle
        self.draw_circle(
            cx, cy, radius,
            fill=VSCodeTheme.VCC_COLOR,
            outline=outline_color,
            width_px=outline_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw + symbol
        plus_size = radius * 0.6
        # Horizontal line of +
        self.draw_line(
            cx - plus_size, cy,
            cx + plus_size, cy,
            fill='white',
            width_px=max(2, int(2 * zoom)),
            tags=('vcc_symbol',)
        )
        # Vertical line of +
        self.draw_line(
            cx, cy - plus_size,
            cx, cy + plus_size,
            fill='white',
            width_px=max(2, int(2 * zoom)),
            tags=('vcc_symbol',)
        )
        
        # Draw user label if present
        label = self.component.properties.get('label', '')
        if label:
            label_y = cy + radius + 15 * zoom
            self.draw_text(
                cx, label_y,
                text=label,
                tags=('component_label', f'label_{self.component.component_id}')
            )
        
        # Draw tabs
        self.draw_tabs(zoom)
