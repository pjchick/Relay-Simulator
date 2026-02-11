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
        rotation = int(getattr(self.component, 'rotation', 0) or 0) % 360
        
        half_width = self.SYMBOL_WIDTH / 2
        # Symbol is offset below the pin
        symbol_offset = self.SYMBOL_HEIGHT / 2
        top = cy  # Tab position
        bottom = cy + symbol_offset + (self.SYMBOL_HEIGHT / 2)
        
        # Account for rotation swapping width/height
        if rotation in (90, 270):
            # Horizontal orientation - swap bounds
            total_height = self.SYMBOL_WIDTH / 2
            total_width = symbol_offset + (self.SYMBOL_HEIGHT / 2)
            return (cx - total_width, cy - total_height, cx + total_width, cy + total_height)
        else:
            # Vertical orientation (0, 180)
            return (cx - half_width, top, cx + half_width, bottom)
    
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the GND component.
        
        Args:
            zoom: Current zoom level
        """
        # Clear previous rendering
        self.clear()
        
        cx, cy = self.get_position()
        rotation = self.get_rotation()
        
        # Offset symbol below the pin/tab
        # Tab is at (cx, cy), symbol should be below it
        symbol_offset = (self.SYMBOL_HEIGHT / 2) * zoom
        
        # Line color (highlight if selected)
        line_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        line_width = 3 if self.selected else 2
        
        # Draw vertical connection line from tab (top) down to symbol
        # Note: draw_line automatically applies rotation, so keep coordinates unrotated
        self.draw_line(
            cx, cy,
            cx, cy + symbol_offset,
            fill=line_color,
            width_px=line_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw three horizontal lines (decreasing in width)
        # Start at bottom of vertical line
        # Note: draw_line automatically applies rotation, so keep coordinates unrotated
        y_spacing = (self.SYMBOL_HEIGHT / 4) * zoom
        
        # Top line (widest - full width)
        top_y = cy + symbol_offset
        top_width = (self.SYMBOL_WIDTH) * zoom
        self.draw_line(
            cx - top_width / 2, top_y,
            cx + top_width / 2, top_y,
            fill=line_color,
            width_px=line_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Middle line (2/3 width)
        mid_y = cy + symbol_offset + y_spacing
        mid_width = (self.SYMBOL_WIDTH * 0.67) * zoom
        self.draw_line(
            cx - mid_width / 2, mid_y,
            cx + mid_width / 2, mid_y,
            fill=line_color,
            width_px=line_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Bottom line (1/3 width)
        bot_y = cy + symbol_offset + y_spacing * 2
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
            # Position label "below" the ground symbol, accounting for rotation
            # Label remains canvas-aligned (not rotated), but position adjusts
            margin = 15 * zoom
            
            if rotation == 0:
                # Default: label below (south)
                label_x = cx
                label_y = cy + symbol_offset + (self.SYMBOL_HEIGHT / 2) * zoom + margin
            elif rotation == 90:
                # Rotated 90°: label to the right (east)
                label_x = cx + symbol_offset + (self.SYMBOL_HEIGHT / 2) * zoom + margin
                label_y = cy
            elif rotation == 180:
                # Rotated 180°: label above (north)
                label_x = cx
                label_y = cy - symbol_offset - (self.SYMBOL_HEIGHT / 2) * zoom - margin
            else:  # 270
                # Rotated 270°: label to the left (west)
                label_x = cx - symbol_offset - (self.SYMBOL_HEIGHT / 2) * zoom - margin
                label_y = cy
            
            self.draw_text(
                label_x, label_y,
                text=label,
                tags=('component_label', f'label_{self.component.component_id}')
            )
        
        # Draw tabs
        self.draw_tabs(zoom)
