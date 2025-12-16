"""
DPDT Relay component renderer.

Renders a relay with coil and two sets of contacts (poles).
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class RelayRenderer(ComponentRenderer):
    """
    Renderer for DPDTRelay components.
    
    Visual appearance matching the provided design:
    - Tall narrow rectangular body
    - Coil section (darker rectangle) at top-left
    - 7 connection points arranged vertically
    - "Relay" text label in center
    - Minimal, clean design
    """
    
    WIDTH = 60   # Relay width in pixels
    HEIGHT = 200  # Relay height in pixels
    
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the relay component matching the provided design.
        
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
            body_fill = '#4a5a6a'  # Lighter blue-gray when energized
        else:
            body_fill = '#3a4a5a'  # Dark blue-gray
            
        # Outline color (highlight if selected)
        outline_color = '#808080' if not self.selected else '#ffffff'
        outline_width = 2 if not self.selected else 3
        
        # Draw main body outline
        self.draw_rectangle(
            x, y, width, height,
            fill=body_fill,
            outline=outline_color,
            width_px=outline_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw coil section (40px wide x 20px tall, vertically centered on COIL pin)
        # COIL pin is at y = -80 from component center
        coil_pin_offset_y = -80  # From component center
        coil_width = 40 * zoom
        coil_height = 20 * zoom
        
        # Position: left edge of component, vertically centered on COIL pin
        coil_x = x + 10 * zoom  # 10px from left edge
        coil_y = cy + coil_pin_offset_y * zoom - (coil_height / 2)  # Center on pin
        
        coil_fill = '#2a3a4a' if not is_energized else '#3a4a6a'
        
        self.draw_rectangle(
            coil_x, coil_y,
            coil_width, coil_height,
            fill=coil_fill,
            outline='#505050',
            width_px=1,
            tags=('relay_coil', f'coil_{self.component.component_id}')
        )
        
        # Draw "Relay" label in center (or custom label)
        label = self.component.properties.get('label', 'Relay')
        if label:
            self.draw_text(
                cx, cy,
                text=label,
                font_size=10,
                fill='#a0a0a0',
                tags=('component_label', f'label_{self.component.component_id}')
            )
        
        # Draw contact lines showing relay state
        # Pin positions (from component):
        # Left side: COM1 (y=-20), COM2 (y=+50)
        # Right side: NO1 (y=-50), NC1 (y=+10), NO2 (y=+30), NC2 (y=+70)
        
        line_color = '#606060'  # Gray line color
        line_width = 2
        
        # Pole 1: COM1 to NC1 (de-energized) or NO1 (energized)
        com1_x = cx - 30 * zoom
        com1_y = cy - 20 * zoom
        
        if is_energized:
            # Energized: COM1 -> NO1
            no1_x = cx + 30 * zoom
            no1_y = cy - 50 * zoom
            self.draw_line(
                com1_x, com1_y, no1_x, no1_y,
                fill=line_color,
                width_px=line_width,
                tags=('contact_line', 'pole1')
            )
        else:
            # De-energized: COM1 -> NC1
            nc1_x = cx + 30 * zoom
            nc1_y = cy + 10 * zoom
            self.draw_line(
                com1_x, com1_y, nc1_x, nc1_y,
                fill=line_color,
                width_px=line_width,
                tags=('contact_line', 'pole1')
            )
        
        # Pole 2: COM2 to NC2 (de-energized) or NO2 (energized)
        com2_x = cx - 30 * zoom
        com2_y = cy + 50 * zoom
        
        if is_energized:
            # Energized: COM2 -> NO2
            no2_x = cx + 30 * zoom
            no2_y = cy + 30 * zoom
            self.draw_line(
                com2_x, com2_y, no2_x, no2_y,
                fill=line_color,
                width_px=line_width,
                tags=('contact_line', 'pole2')
            )
        else:
            # De-energized: COM2 -> NC2
            nc2_x = cx + 30 * zoom
            nc2_y = cy + 70 * zoom
            self.draw_line(
                com2_x, com2_y, nc2_x, nc2_y,
                fill=line_color,
                width_px=line_width,
                tags=('contact_line', 'pole2')
            )
        
        # Draw tabs for all pins (no visible contact indicators, just tabs)
        self.draw_tabs(zoom)
