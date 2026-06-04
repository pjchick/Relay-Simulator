"""
SPST Switch component renderer.

Renders a simple SPST (Single Pole Single Throw) switch symbol
with two terminals and a movable contact.
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class SPSTSwitchRenderer(ComponentRenderer):
    """
    Renderer for SPST Switch components.
    
    Visual appearance:
    - Two terminals (left and right)
    - Movable contact showing open/closed state
    - When closed: horizontal line connecting terminals
    - When open: angled line from left terminal
    - Label at specified position
    """
    
    WIDTH = 70   # Total width including terminal tabs
    HEIGHT = 30  # Height for bounds calculation

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

    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing."""
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
    
    def _draw_line_rotated(self, x1: float, y1: float, x2: float, y2: float, 
                           fill: str, width_px: int, tags: tuple):
        """Draw a line with rotation applied."""
        cx, cy = self.get_position()
        rotation = self.get_rotation()
        
        if rotation != 0:
            x1, y1 = self.rotate_point(x1, y1, cx, cy, rotation)
            x2, y2 = self.rotate_point(x2, y2, cx, cy, rotation)
        
        item_id = self.canvas.create_line(
            x1, y1, x2, y2,
            fill=fill,
            width=width_px,
            tags=tags
        )
        self.canvas_items.append(item_id)
    
    def _draw_circle_rotated(self, x: float, y: float, radius: float,
                            fill: str, outline: str, width_px: int, tags: tuple):
        """Draw a circle with rotation applied."""
        cx, cy = self.get_position()
        rotation = self.get_rotation()
        
        if rotation != 0:
            x, y = self.rotate_point(x, y, cx, cy, rotation)
        
        item_id = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=fill,
            outline=outline,
            width=width_px,
            tags=tags
        )
        self.canvas_items.append(item_id)
    
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the SPST switch component.
        
        Args:
            zoom: Current zoom level
        """
        # Clear previous rendering
        self.clear()
        
        cx, cy = self.get_position()
        rotation = self.get_rotation()
        
        # Outline color (highlight if selected)
        outline_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        outline_width = 3 if self.selected else 2
        
        # Determine switch state
        is_closed = self.component._is_closed
        
        # Check if power is flowing through the switch (either terminal is HIGH)
        from core.state import PinState
        
        def is_pin_high(pin) -> bool:
            """Check if a pin is HIGH via VNET state."""
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
        
        def is_pin_in_gnd_network(pin) -> bool:
            """Check if a pin is connected to a GND component (traversing bridges)."""
            if not self.simulation_engine or not pin:
                return False
            
            if not hasattr(self.simulation_engine, 'vnets') or not hasattr(self.simulation_engine, 'tabs'):
                return False
            
            # Find all VNETs connected to this pin (including through bridges)
            visited_vnets = set()
            vnets_to_check = []
            
            # Start with VNETs directly containing this pin's tabs
            for tab in pin.tabs.values():
                for vnet in self.simulation_engine.vnets.values():
                    if tab.tab_id in vnet.tab_ids:
                        vnets_to_check.append(vnet.vnet_id)
                        break
            
            # BFS through bridges to find all connected VNETs
            while vnets_to_check:
                vnet_id = vnets_to_check.pop(0)
                
                if vnet_id in visited_vnets:
                    continue
                    
                visited_vnets.add(vnet_id)
                vnet = self.simulation_engine.vnets.get(vnet_id)
                
                if not vnet:
                    continue
                
                # Check if this VNET contains a GND component
                for tab_id in vnet.tab_ids:
                    try:
                        # Access component through tab's parent chain
                        tab = self.simulation_engine.tabs.get(tab_id)
                        if tab and tab.parent_pin and tab.parent_pin.parent_component:
                            component = tab.parent_pin.parent_component
                            if hasattr(component, 'component_type') and component.component_type == 'GND':
                                return True
                    except Exception:
                        continue
                
                # Follow bridges to connected VNETs
                if hasattr(vnet, 'bridge_ids'):
                    for bridge_id in vnet.bridge_ids:
                        # Find other VNETs that share this bridge
                        for other_vnet_id, other_vnet in self.simulation_engine.vnets.items():
                            if other_vnet_id != vnet_id and bridge_id in other_vnet.bridge_ids:
                                if other_vnet_id not in visited_vnets:
                                    vnets_to_check.append(other_vnet_id)
            
            return False
        
        # Check if either terminal is HIGH
        terminal1_high = is_pin_high(self.component._terminal1_pin) if hasattr(self.component, '_terminal1_pin') else False
        terminal2_high = is_pin_high(self.component._terminal2_pin) if hasattr(self.component, '_terminal2_pin') else False
        is_powered = terminal1_high or terminal2_high
        
        # Check if connected to GND network
        terminal1_gnd = is_pin_in_gnd_network(self.component._terminal1_pin) if hasattr(self.component, '_terminal1_pin') else False
        terminal2_gnd = is_pin_in_gnd_network(self.component._terminal2_pin) if hasattr(self.component, '_terminal2_pin') else False
        is_gnd_network = terminal1_gnd or terminal2_gnd
        
        # Terminal positions (in component coordinates, before rotation)
        left_terminal_x = cx - 30 * zoom
        right_terminal_x = cx + 30 * zoom
        terminal_y = cy
        
        # Apply flip transformations
        left_terminal_x, terminal_y_left = self._apply_flip(left_terminal_x, terminal_y, cx, cy)
        right_terminal_x, terminal_y_right = self._apply_flip(right_terminal_x, terminal_y, cx, cy)
        
        # Draw left terminal (small circle)
        self._draw_circle_rotated(
            left_terminal_x, terminal_y_left, 3 * zoom,
            fill=VSCodeTheme.COMPONENT_OUTLINE,
            outline=outline_color,
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw right terminal (small circle)
        self._draw_circle_rotated(
            right_terminal_x, terminal_y_right, 3 * zoom,
            fill=VSCodeTheme.COMPONENT_OUTLINE,
            outline=outline_color,
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw movable contact (line from left terminal)
        contact_length = 50 * zoom
        
        # Determine contact line color based on switch state and network type
        if is_closed and is_gnd_network:
            contact_color = VSCodeTheme.WIRE_GROUNDED  # Blue when GND flows through closed switch
        elif is_closed and is_powered:
            contact_color = VSCodeTheme.WIRE_POWERED  # Green when power flows through closed switch
        else:
            contact_color = outline_color  # Default color when open or no signal
        
        if is_closed:
            # CLOSED: Draw horizontal line connecting both terminals
            contact_end_x = cx + 30 * zoom - 3 * zoom  # right terminal - small offset
            contact_end_y = cy
        else:
            # OPEN: Draw angled line (30 degrees upward)
            import math
            angle_rad = math.radians(-30)  # -30 degrees (upward)
            contact_start_x = cx - 30 * zoom  # left terminal
            contact_end_x = contact_start_x + contact_length * math.cos(angle_rad)
            contact_end_y = cy + contact_length * math.sin(angle_rad)
        
        # Apply flip to contact end position
        contact_end_x, contact_end_y = self._apply_flip(contact_end_x, contact_end_y, cx, cy)
        
        # Draw the movable contact line
        self._draw_line_rotated(
            left_terminal_x, terminal_y_left,
            contact_end_x, contact_end_y,
            fill=contact_color,
            width_px=outline_width,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw label
        label = self.component.properties.get('label', 'SW')
        label_position = self.component.properties.get('label_position', 'bottom')
        
        # Calculate label position (accounting for rotation)
        if rotation in (0, 180):
            w = self.WIDTH * zoom
            h = self.HEIGHT * zoom
        else:
            w = self.HEIGHT * zoom
            h = self.WIDTH * zoom
        
        offset_h = (w / 2) + (15 * zoom)
        offset_v = (h / 2) + (15 * zoom)
        
        label_x = cx
        label_y = cy
        anchor = 'center'
        
        if label_position == 'bottom':
            label_y = cy + offset_v
            anchor = 'n'
        elif label_position == 'top':
            label_y = cy - offset_v
            anchor = 's'
        elif label_position == 'left':
            label_x = cx - offset_h
            anchor = 'e'
        elif label_position == 'right':
            label_x = cx + offset_h
            anchor = 'w'
        
        self.draw_text(
            label_x, label_y,
            text=label,
            anchor=anchor,
            tags=('component_label', f'label_{self.component.component_id}')
        )
        
        # Draw tabs
        self.draw_tabs(zoom)
