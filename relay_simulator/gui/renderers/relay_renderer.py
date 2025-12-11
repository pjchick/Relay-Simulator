"""
DPDT Relay component renderer.

Renders a relay with coil and two sets of contacts (poles).
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class RelayRenderer(ComponentRenderer):
    """
    Renderer for DPDTRelay components.
    
    Visual appearance:
    - Rectangular body (80x60 pixels)
    - Coil section on left
    - Two poles (POLE1, POLE2) on right
    - Each pole has COM, NO, NC contacts
    - Label above or below
    """
    
    WIDTH = 80   # Relay width in pixels
    HEIGHT = 60  # Relay height in pixels
    
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the relay component.
        
        Args:
            zoom: Current zoom level
        """
        # Clear previous rendering
        self.clear()
        
        cx, cy = self.get_position()
        width = self.WIDTH * zoom
        height = self.HEIGHT * zoom
        
        # Calculate top-left corner
        x = cx - width / 2
        y = cy - height / 2
        
        # Determine fill color based on energized state
        is_energized = self.component._is_energized
        if is_energized and self.powered:
            body_fill = '#404080'  # Blue-ish when energized and powered
        elif is_energized:
            body_fill = '#303050'  # Dark blue when energized but not powered
        else:
            body_fill = VSCodeTheme.COMPONENT_FILL
            
        # Outline color (highlight if selected)
        outline_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        outline_width = 3 if self.selected else 2
        
        # Draw main body
        self.draw_rectangle(
            x, y, width, height,
            fill=body_fill,
            outline=outline_color,
            width_px=outline_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw coil section (left third)
        coil_width = width / 3
        self.draw_rectangle(
            x + 5 * zoom, y + 5 * zoom,
            coil_width - 10 * zoom, height - 10 * zoom,
            fill=VSCodeTheme.RELAY_COIL,
            outline=VSCodeTheme.COMPONENT_OUTLINE,
            width_px=1,
            tags=('relay_coil', f'coil_{self.component.component_id}')
        )
        
        # Draw contact indicators (simplified)
        # POLE 1 (top right)
        pole1_x = x + width * 0.55
        pole1_y = y + height * 0.25
        self.draw_circle(
            pole1_x, pole1_y, 4 * zoom,
            fill=VSCodeTheme.RELAY_CONTACT if is_energized else '#404040',
            outline=VSCodeTheme.COMPONENT_OUTLINE,
            tags=('relay_contact', 'pole1')
        )
        
        # POLE 2 (bottom right)
        pole2_x = x + width * 0.55
        pole2_y = y + height * 0.75
        self.draw_circle(
            pole2_x, pole2_y, 4 * zoom,
            fill=VSCodeTheme.RELAY_CONTACT if is_energized else '#404040',
            outline=VSCodeTheme.COMPONENT_OUTLINE,
            tags=('relay_contact', 'pole2')
        )
        
        # Draw label
        label = self.component.properties.get('label', 'RLY')
        if label:
            label_position = self.component.properties.get('label_position', 'top')
            
            # Calculate label position
            label_offset = (height / 2 + 15) * zoom
            label_x = cx
            label_y = cy
            
            if label_position == 'bottom':
                label_y = cy + label_offset
            elif label_position == 'top':
                label_y = cy - label_offset
            elif label_position == 'left':
                label_x = cx - (width / 2 + 15) * zoom
            elif label_position == 'right':
                label_x = cx + (width / 2 + 15) * zoom
                
            self.draw_text(
                label_x, label_y,
                text=label,
                tags=('component_label', f'label_{self.component.component_id}')
            )
        
        # Draw tabs for all pins
        self.draw_tabs(zoom)
