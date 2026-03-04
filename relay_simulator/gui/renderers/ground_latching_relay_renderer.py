"""
Ground Latching Relay component renderer.

Renders a latching relay with two coils (SET with GND and RESET with GND) and two sets of contacts (poles).
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class GroundLatchingRelayRenderer(ComponentRenderer):
    """
    Renderer for GroundLatchingRelay components.
    Supports rotation and flipping transformations.
    """
    
    WIDTH = 60   # Relay width in pixels
    HEIGHT = 240  # Relay height in pixels (same as regular latching relay)
    
    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing (relay body only, no label)."""
        cx, cy = self.component.position
        rotation = int(getattr(self.component, 'rotation', 0) or 0) % 360
        
        # Body is centered: extends from -110 to +110
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
    
    def _transform_local_point(self, local_x: float, local_y: float, cx: float, cy: float, zoom: float) -> tuple:
        """
        Transform a component-local coordinate to world coordinates with flip applied.
        Does NOT apply rotation (that's handled by draw_line/draw_circle/etc).
        
        Args:
            local_x, local_y: Offset from component center in component-local space (unzoomed)
            cx, cy: Component center in world space
            zoom: Current zoom level
            
        Returns:
            (world_x, world_y) with flip applied but not rotation
        """
        # Get flip properties
        flip_h = self.component.properties.get('flip_horizontal', False)
        flip_v = self.component.properties.get('flip_vertical', False)
        
        # Apply flip in component-local space
        if flip_h:
            local_x = -local_x
        if flip_v:
            local_y = -local_y
        
        # Convert to world space (zoom and offset)
        world_x = cx + local_x * zoom
        world_y = cy + local_y * zoom
        
        return world_x, world_y
    
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the ground latching relay component.
        
        Args:
            zoom: Current zoom level
        """
        # Clear previous rendering
        self.clear()
        
        cx, cy = self.get_position()
        width = self.WIDTH * zoom
        height = self.HEIGHT * zoom
        
        # Calculate top-left corner
        # Pins range from -100 to +100, perfectly centered
        # With 20px margins: top at -120, bottom at +120, height = 240
        x = cx - width / 2
        y = cy - 120 * zoom  # Top edge at y=-120 (20px above COIL_SET at -100)
        
        # Determine fill color based on set state.
        # Base body color is user-configurable via component properties.
        is_set = self.component._is_set
        body_base = self.component.properties.get('body_color', '#3a4a5a')
        if not (isinstance(body_base, str) and len(body_base) == 7 and body_base.startswith('#')):
            body_base = '#3a4a5a'

        body_fill = body_base
        if is_set and self.powered:
            # Brighten body fill slightly when in SET state.
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
        
        # Draw SET coil section (40px wide x 20px tall, positioned at top of relay)
        # Horizontally centered on relay body, vertically at y=-100 (COIL_SET pin position)
        coil_width = 40 * zoom
        coil_height = 20 * zoom
        
        # SET coil center point (before transformations)
        set_coil_center_x = cx  # Horizontally centered
        set_coil_center_y = cy - 100 * zoom  # Offset up to COIL_SET pin position
        
        # Apply flip transformations (rotation handled by draw_rectangle)
        set_coil_cx, set_coil_cy = self._apply_flip(set_coil_center_x, set_coil_center_y, cx, cy)
        
        # Calculate SET coil top-left corner
        set_coil_x = set_coil_cx - coil_width / 2
        set_coil_y = set_coil_cy - coil_height / 2
        
        set_coil_fill = '#2a3a4a' if not is_set else '#3a4a6a'
        
        # Draw the SET coil rectangle
        self.draw_rectangle(
            set_coil_x, set_coil_y, coil_width, coil_height,
            fill=set_coil_fill,
            outline='#606060',
            width_px=1,
            tags=('coil', f'coil_set_{self.component.component_id}')
        )
        
        # Get rotation for label positioning (text needs manual rotation)
        rotation = self.get_rotation()
        
        # Draw 'S' label inside SET coil (left side)
        set_label_x, set_label_y = self._apply_flip(cx - 12 * zoom, cy - 100 * zoom, cx, cy)
        if rotation != 0:
            set_label_x, set_label_y = self.rotate_point(set_label_x, set_label_y, cx, cy, rotation)
        self.draw_text(
            set_label_x, set_label_y,
            text='S',
            font_size=10,
            fill='#a0a0a0',
            anchor='center',
            tags=('pin_label', f'set_label_{self.component.component_id}')
        )
        
        # Draw 'G' label inside SET coil (right side for GND_SET)
        gnd_set_label_x, gnd_set_label_y = self._apply_flip(cx + 12 * zoom, cy - 100 * zoom, cx, cy)
        if rotation != 0:
            gnd_set_label_x, gnd_set_label_y = self.rotate_point(gnd_set_label_x, gnd_set_label_y, cx, cy, rotation)
        self.draw_text(
            gnd_set_label_x, gnd_set_label_y,
            text='G',
            font_size=10,
            fill='#569cd6',  # Blue color to indicate ground
            anchor='center',
            tags=('pin_label', f'gnd_set_label_{self.component.component_id}')
        )
        
        # Draw RESET coil section (40px wide x 20px tall, positioned at bottom of relay)
        # Horizontally centered on relay body, vertically at y=+100 (COIL_RESET pin position)
        
        # RESET coil center point (before transformations)
        reset_coil_center_x = cx  # Horizontally centered
        reset_coil_center_y = cy + 100 * zoom  # Offset down to COIL_RESET pin position
        
        # Apply flip transformations (rotation handled by draw_rectangle)
        reset_coil_cx, reset_coil_cy = self._apply_flip(reset_coil_center_x, reset_coil_center_y, cx, cy)
        
        # Calculate RESET coil top-left corner
        reset_coil_x = reset_coil_cx - coil_width / 2
        reset_coil_y = reset_coil_cy - coil_height / 2
        
        reset_coil_fill = '#3a4a6a' if is_set else '#2a3a4a'
        
        # Draw the RESET coil rectangle
        self.draw_rectangle(
            reset_coil_x, reset_coil_y, coil_width, coil_height,
            fill=reset_coil_fill,
            outline='#606060',
            width_px=1,
            tags=('coil', f'coil_reset_{self.component.component_id}')
        )
        
        # Draw 'R' label inside RESET coil (left side)
        reset_label_x, reset_label_y = self._apply_flip(cx - 12 * zoom, cy + 100 * zoom, cx, cy)
        if rotation != 0:
            reset_label_x, reset_label_y = self.rotate_point(reset_label_x, reset_label_y, cx, cy, rotation)
        self.draw_text(
            reset_label_x, reset_label_y,
            text='R',
            font_size=10,
            fill='#a0a0a0',
            anchor='center',
            tags=('pin_label', f'reset_label_{self.component.component_id}')
        )
        
        # Draw 'G' label inside RESET coil (right side for GND_RESET)
        gnd_reset_label_x, gnd_reset_label_y = self._apply_flip(cx + 12 * zoom, cy + 100 * zoom, cx, cy)
        if rotation != 0:
            gnd_reset_label_x, gnd_reset_label_y = self.rotate_point(gnd_reset_label_x, gnd_reset_label_y, cx, cy, rotation)
        self.draw_text(
            gnd_reset_label_x, gnd_reset_label_y,
            text='G',
            font_size=10,
            fill='#569cd6',  # Blue color to indicate ground
            anchor='center',
            tags=('pin_label', f'gnd_reset_label_{self.component.component_id}')
        )
        
        # Draw contact lines to show active connections
        # Green lines indicate which contacts are currently connected
        from core.state import PinState
        
        # Check if poles are connected to show active state
        # Pole 1: COM1 -> NO1 (SET) or NC1 (RESET)
        if is_set:
            # COM1 -> NO1 connection (SET state, NO is active)
            # Draw line from COM1 to NO1
            com1_x, com1_y = self._apply_flip(cx - 30 * zoom, cy - 40 * zoom, cx, cy)
            no1_x, no1_y = self._apply_flip(cx + 30 * zoom, cy - 60 * zoom, cx, cy)
            
            self.draw_line(
                com1_x, com1_y, no1_x, no1_y,
                fill='#00ff00',  # Green for active
                width_px=2,
                tags=('contact_line', f'pole1_set_{self.component.component_id}')
            )
            
            # COM2 -> NO2 connection
            com2_x, com2_y = self._apply_flip(cx - 30 * zoom, cy + 40 * zoom, cx, cy)
            no2_x, no2_y = self._apply_flip(cx + 30 * zoom, cy + 20 *zoom, cx, cy)
            
            self.draw_line(
                com2_x, com2_y, no2_x, no2_y,
                fill='#00ff00',  # Green for active
                width_px=2,
                tags=('contact_line', f'pole2_set_{self.component.component_id}')
            )
        else:
            # COM1 -> NC1 connection (RESET state, NC is active)
            com1_x, com1_y = self._apply_flip(cx - 30 * zoom, cy - 40 * zoom, cx, cy)
            nc1_x, nc1_y = self._apply_flip(cx + 30 * zoom, cy - 20 * zoom, cx, cy)
            
            self.draw_line(
                com1_x, com1_y, nc1_x, nc1_y,
                fill='#00ff00',  # Green for active
                width_px=2,
                tags=('contact_line', f'pole1_reset_{self.component.component_id}')
            )
            
            # COM2 -> NC2 connection
            com2_x, com2_y = self._apply_flip(cx - 30 * zoom, cy + 40 * zoom, cx, cy)
            nc2_x, nc2_y = self._apply_flip(cx + 30 * zoom, cy + 60 * zoom, cx, cy)
            
            self.draw_line(
                com2_x, com2_y, nc2_x, nc2_y,
                fill='#00ff00',  # Green for active
                width_px=2,
                tags=('contact_line', f'pole2_reset_{self.component.component_id}')
            )
        
        # Draw label with position support
        label = self.component.properties.get('label', '')
        if label:
            label_pos = self.component.properties.get('label_position', 'top')
            
            # Calculate offset based on relay orientation
            # Relay is 60x240 normally, centered
            # At 0° or 180°: relay is vertical (tall), needs larger offset for top/bottom
            # At 90° or 270°: relay is horizontal (wide), needs larger offset for left/right
            if rotation in [0, 180]:
                # Vertical orientation
                offset_v = 140 * zoom  # For top/bottom (240/2 + 20 margin)
                offset_h = 50 * zoom   # For left/right (60/2 + 20 margin)
            else:
                # Horizontal orientation (90° or 270°)
                offset_v = 50 * zoom   # For top/bottom (60/2 + 20 margin)
                offset_h = 140 * zoom  # For left/right (240/2 + 20 margin)
            
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
                fill='#ffffff',
                anchor=anchor,
                tags=('label', f'label_{self.component.component_id}')
            )
        
        # Draw tabs for all pins
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
