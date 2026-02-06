"""
DPDT Relay component renderer.

Renders a relay with coil and two sets of contacts (poles).
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class RelayRenderer(ComponentRenderer):
    """
    Renderer for DPDTRelay components.
    Supports rotation and flipping transformations.
    """
    
    WIDTH = 60   # Relay width in pixels
    HEIGHT = 200  # Relay height in pixels
    
    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing (relay body only, no label)."""
        cx, cy = self.component.position
        rotation = int(getattr(self.component, 'rotation', 0) or 0) % 360
        
        # Account for rotation swapping width/height
        if rotation in (90, 270):
            half_w = self.HEIGHT / 2
            half_h = self.WIDTH / 2
        else:
            half_w = self.WIDTH / 2
            half_h = self.HEIGHT / 2
        
        return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)
    
    def _apply_flip(self, x: float, y: float, cx: float, cy: float) -> tuple:
        """
        Apply flip transformations to a coordinate (rotation is handled by base renderer).
        
        Args:
            x, y: Absolute coordinate to transform
            cx, cy: Component center position
            
        Returns:
            (flipped_x, flipped_y)
        """
        # Get flip properties
        flip_h = self.component.properties.get('flip_horizontal', False)
        flip_v = self.component.properties.get('flip_vertical', False)
        
        # Convert to offset from center
        offset_x = x - cx
        offset_y = y - cy
        
        # Apply flipping to offsets
        if flip_h:
            offset_x = -offset_x
        if flip_v:
            offset_y = -offset_y
        
        # Convert back to absolute coordinates
        return cx + offset_x, cy + offset_y
    
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
        
        # Determine fill color based on energized state.
        # Base body color is user-configurable via component properties.
        is_energized = self.component._is_energized
        body_base = self.component.properties.get('body_color', '#3a4a5a')
        if not (isinstance(body_base, str) and len(body_base) == 7 and body_base.startswith('#')):
            body_base = '#3a4a5a'

        body_fill = body_base
        if is_energized and self.powered:
            # Legacy behavior: brighten body fill slightly when energized.
            try:
                r = int(body_base[1:3], 16)
                g = int(body_base[3:5], 16)
                b = int(body_base[5:7], 16)
                bump = 0x10
                r = min(255, r + bump)
                g = min(255, g + bump)
                b = min(255, b + bump)
                body_fill = f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                body_fill = body_base
            
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
        
        # Draw coil section (40px wide x 20px tall, positioned at top of relay)
        # Horizontally centered on relay body, vertically at y=-80 (COIL pin position)
        coil_width = 40 * zoom
        coil_height = 20 * zoom
        
        # Coil center point (before transformations)
        # Centered horizontally on relay body, positioned at COIL pin height
        coil_center_x = cx  # Horizontally centered
        coil_center_y = cy - 80 * zoom  # Offset up to COIL pin position
        
        # Apply flip transformations (rotation handled by draw_rectangle)
        coil_cx, coil_cy = self._apply_flip(coil_center_x, coil_center_y, cx, cy)
        
        # Calculate coil top-left corner
        coil_x = coil_cx - coil_width / 2
        coil_y = coil_cy - coil_height / 2
        
        coil_fill = '#2a3a4a' if not is_energized else '#3a4a6a'
        
        # Draw the coil rectangle
        self.draw_rectangle(
            coil_x, coil_y, coil_width, coil_height,
            fill=coil_fill,
            outline='#606060',
            width_px=1,
            tags=('coil', f'coil_{self.component.component_id}')
        )
        
        # Draw label with position support
        label = self.component.properties.get('label', '')
        if label:
            label_pos = self.component.properties.get('label_position', 'top')
            rotation = self.get_rotation()
            
            # Calculate offset based on relay orientation
            # Relay is 60x200 normally
            # At 0° or 180°: relay is vertical (tall), needs larger offset for top/bottom
            # At 90° or 270°: relay is horizontal (wide), needs larger offset for left/right
            if rotation in [0, 180]:
                # Vertical orientation
                offset_v = 120 * zoom  # For top/bottom (200/2 + 20 margin)
                offset_h = 50 * zoom   # For left/right (60/2 + 20 margin)
            else:
                # Horizontal orientation (90° or 270°)
                offset_v = 50 * zoom   # For top/bottom (60/2 + 20 margin)
                offset_h = 120 * zoom  # For left/right (200/2 + 20 margin)
            
            # Label position is ALWAYS relative to canvas axes (not rotated with component)
            if label_pos == 'top':
                label_x, label_y = cx, cy - offset_v
                anchor = 'center'
            elif label_pos == 'bottom':
                label_x, label_y = cx, cy + offset_v
                anchor = 'center'
            elif label_pos == 'left':
                label_x, label_y = cx - offset_h, cy
                anchor = 'e'  # East (right-justified) when label is on left
            else:  # right
                label_x, label_y = cx + offset_h, cy
                anchor = 'w'  # West (left-justified) when label is on right
            
            self.draw_text(
                label_x, label_y,
                text=label,
                font_size=12,
                fill='#a0a0a0',
                anchor=anchor,
                tags=('component_label', f'label_{self.component.component_id}')
            )
        
        # Draw contact lines showing relay state
        
        # Import PinState for checking if pins are HIGH
        from core.state import PinState
        
        line_width = 2
        
        # Helper function to check if a pin is HIGH via VNET state
        def is_pin_high(pin) -> bool:
            if not self.simulation_engine or not pin:
                return False
            # Check all tabs on this pin
            for tab in pin.tabs.values():
                # Find VNET containing this tab
                for vnet in self.simulation_engine.vnets.values():
                    if tab.tab_id in vnet.tab_ids:
                        if vnet.state == PinState.HIGH:
                            return True
            return False
        
        # Pole 1: COM1 to NC1 (de-energized) or NO1 (energized)
        com1_x, com1_y = self._apply_flip(cx - 30 * zoom, cy - 20 * zoom, cx, cy)
        
        if is_energized:
            # Energized: COM1 -> NO1
            no1_x, no1_y = self._apply_flip(cx + 30 * zoom, cy - 40 * zoom, cx, cy)
            # Check if either COM1 or NO1 pin is HIGH via VNET state
            com1_high = is_pin_high(self.component._com1_pin) if hasattr(self.component, '_com1_pin') else False
            no1_high = is_pin_high(self.component._no1_pin) if hasattr(self.component, '_no1_pin') else False
            line_color = '#00ff00' if (com1_high or no1_high) else '#606060'
            self.draw_line(
                com1_x, com1_y, no1_x, no1_y,
                fill=line_color,
                width_px=line_width,
                tags=('contact_line', 'pole1')
            )
        else:
            # De-energized: COM1 -> NC1
            nc1_x, nc1_y = self._apply_flip(cx + 30 * zoom, cy + 0 * zoom, cx, cy)
            # Check if either COM1 or NC1 pin is HIGH via VNET state
            com1_high = is_pin_high(self.component._com1_pin) if hasattr(self.component, '_com1_pin') else False
            nc1_high = is_pin_high(self.component._nc1_pin) if hasattr(self.component, '_nc1_pin') else False
            line_color = '#00ff00' if (com1_high or nc1_high) else '#606060'
            self.draw_line(
                com1_x, com1_y, nc1_x, nc1_y,
                fill=line_color,
                width_px=line_width,
                tags=('contact_line', 'pole1')
            )
        
        # Pole 2: COM2 to NC2 (de-energized) or NO2 (energized)
        com2_x, com2_y = self._apply_flip(cx - 30 * zoom, cy + 60 * zoom, cx, cy)
        
        if is_energized:
            # Energized: COM2 -> NO2
            no2_x, no2_y = self._apply_flip(cx + 30 * zoom, cy + 40 * zoom, cx, cy)
            # Check if either COM2 or NO2 pin is HIGH via VNET state
            com2_high = is_pin_high(self.component._com2_pin) if hasattr(self.component, '_com2_pin') else False
            no2_high = is_pin_high(self.component._no2_pin) if hasattr(self.component, '_no2_pin') else False
            line_color = '#00ff00' if (com2_high or no2_high) else '#606060'
            self.draw_line(
                com2_x, com2_y, no2_x, no2_y,
                fill=line_color,
                width_px=line_width,
                tags=('contact_line', 'pole2')
            )
        else:
            # De-energized: COM2 -> NC2
            nc2_x, nc2_y = self._apply_flip(cx + 30 * zoom, cy + 80 * zoom, cx, cy)
            # Check if either COM2 or NC2 pin is HIGH via VNET state
            com2_high = is_pin_high(self.component._com2_pin) if hasattr(self.component, '_com2_pin') else False
            nc2_high = is_pin_high(self.component._nc2_pin) if hasattr(self.component, '_nc2_pin') else False
            line_color = '#00ff00' if (com2_high or nc2_high) else '#606060'
            self.draw_line(
                com2_x, com2_y, nc2_x, nc2_y,
                fill=line_color,
                width_px=line_width,
                tags=('contact_line', 'pole2')
            )
        
        # Draw tabs for all pins (no visible contact indicators, just tabs)
        self.draw_tabs(zoom)
    
    def draw_tabs(self, zoom: float = 1.0) -> None:
        """
        Draw tabs for all component pins with flip and rotation transformations applied.
        
        Args:
            zoom: Current zoom level
        """
        cx, cy = self.get_position()
        
        for pin in self.component.pins.values():
            for tab in pin.tabs.values():
                # Get tab position relative to component
                tx_offset, ty_offset = tab.relative_position
                
                # Calculate absolute position (before flip)
                tx_base = cx + tx_offset * zoom
                ty_base = cy + ty_offset * zoom
                
                # Apply flip transformations
                tx_flipped, ty_flipped = self._apply_flip(tx_base, ty_base, cx, cy)
                
                # Apply rotation manually (draw_circle doesn't auto-rotate center like draw_rectangle does)
                rotation = self.get_rotation()
                tx, ty = self.rotate_point(tx_flipped, ty_flipped, cx, cy, rotation)
                
                # Draw tab as small circle
                tab_size = VSCodeTheme.TAB_SIZE * zoom
                self.draw_circle(
                    tx, ty,
                    radius=tab_size / 2,
                    fill='#00ff00',  # Bright green for visibility
                    outline='#ffffff',  # White outline
                    width_px=1,
                    tags=('tab', f'tab_{tab.tab_id}')
                )