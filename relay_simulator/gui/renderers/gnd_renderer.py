"""
GND (Ground) component renderer.

Renders a GND symbol (three horizontal lines decreasing in length).
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class GNDRenderer(ComponentRenderer):
    """
    Renderer for GND (ground) components.
    
    Visual appearance:
    - Ground symbol: three horizontal lines decreasing in width
    - Black/dark color
    - Tab at top (12 o'clock position)
    """
    
    SYMBOL_WIDTH = 30  # Width of widest line in pixels
    SYMBOL_HEIGHT = 20  # Height of symbol in pixels
    
    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing."""
        cx, cy = self.component.position
        half_width = self.SYMBOL_WIDTH / 2
        half_height = self.SYMBOL_HEIGHT / 2
        return (cx - half_width, cy - half_height, cx + half_width, cy + half_height)
    
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the GND component.
        
        Args:
            zoom: Current zoom level
        """
        # Clear previous rendering
        self.clear()
        
        cx, cy = self.get_position()
        
        # Line color (highlight if selected)
        line_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        line_width = 3 if self.selected else 2
        
        # Draw vertical connection line from top
        line_top = cy - (self.SYMBOL_HEIGHT / 2) * zoom
        line_bottom = cy
        self.draw_line(
            cx, line_top,
            cx, line_bottom,
            fill=line_color,
            width_px=line_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw three horizontal lines (decreasing in width)
        y_spacing = (self.SYMBOL_HEIGHT / 4) * zoom
        
        # Top line (widest - full width)
        top_y = cy
        top_width = (self.SYMBOL_WIDTH) * zoom
        self.draw_line(
            cx - top_width / 2, top_y,
            cx + top_width / 2, top_y,
            fill=line_color,
            width_px=line_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Middle line (2/3 width)
        mid_y = cy + y_spacing
        mid_width = (self.SYMBOL_WIDTH * 0.67) * zoom
        self.draw_line(
            cx - mid_width / 2, mid_y,
            cx + mid_width / 2, mid_y,
            fill=line_color,
            width_px=line_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Bottom line (1/3 width)
        bot_y = cy + y_spacing * 2
        bot_width = (self.SYMBOL_WIDTH * 0.33) * zoom
        self.draw_line(
            cx - bot_width / 2, bot_y,
            cx + bot_width / 2, bot_y,
            fill=line_color,
            width_px=line_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw user label if present
        label = self.component.properties.get('label', '')
        if label:
            label_y = cy + (self.SYMBOL_HEIGHT / 2) * zoom + 15 * zoom
            self.draw_text(
                cx, label_y,
                text=label,
                tags=('component_label', f'label_{self.component.component_id}')
            )
        
        # Draw tabs
        self.draw_tabs(zoom)
