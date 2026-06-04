"""
SPDT Switch component renderer.

Renders a SPDT (Single Pole Dual Throw) switch symbol
with common terminal on left, two throw terminals on right.
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme
from core.state import PinState


class SPDTSwitchRenderer(ComponentRenderer):
    """
    Renderer for SPDT Switch components.
    
    Visual appearance:
    - Common terminal on left
    - Terminal 1 on upper right
    - Terminal 2 on lower right
    - Movable contact showing current position
    - Color indicates power/GND flow
    - Label at specified position
    """
    
    WIDTH = 70   # Total width including terminal tabs
    HEIGHT = 50  # Height for bounds calculation

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
        Render the SPDT switch component.
        
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
        
        # Determine switch position
        position = self.component._position
        
        # Helper function to check if a pin is HIGH via VNET state
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
        
        # Check power/GND status on all terminals
        common_high = is_pin_high(self.component._common_pin) if hasattr(self.component, '_common_pin') else False
        terminal1_high = is_pin_high(self.component._terminal1_pin) if hasattr(self.component, '_terminal1_pin') else False
        terminal2_high = is_pin_high(self.component._terminal2_pin) if hasattr(self.component, '_terminal2_pin') else False
        
        common_gnd = is_pin_in_gnd_network(self.component._common_pin) if hasattr(self.component, '_common_pin') else False
        terminal1_gnd = is_pin_in_gnd_network(self.component._terminal1_pin) if hasattr(self.component, '_terminal1_pin') else False
        terminal2_gnd = is_pin_in_gnd_network(self.component._terminal2_pin) if hasattr(self.component, '_terminal2_pin') else False
        
        # Terminal positions (in component coordinates, before flip/rotation)
        common_x = cx - 30 * zoom
        common_y = cy
        terminal1_x = cx + 30 * zoom
        terminal1_y = cy - 20 * zoom
        terminal2_x = cx + 30 * zoom
        terminal2_y = cy + 20 * zoom
        
        # Apply flip transformations
        common_x, common_y = self._apply_flip(common_x, common_y, cx, cy)
        terminal1_x, terminal1_y = self._apply_flip(terminal1_x, terminal1_y, cx, cy)
        terminal2_x, terminal2_y = self._apply_flip(terminal2_x, terminal2_y, cx, cy)
        
        # Draw common terminal (small circle)
        self._draw_circle_rotated(
            common_x, common_y, 3 * zoom,
            fill=VSCodeTheme.COMPONENT_OUTLINE,
            outline=outline_color,
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw terminal 1 (small circle)
        self._draw_circle_rotated(
            terminal1_x, terminal1_y, 3 * zoom,
            fill=VSCodeTheme.COMPONENT_OUTLINE,
            outline=outline_color,
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Draw terminal 2 (small circle)
        self._draw_circle_rotated(
            terminal2_x, terminal2_y, 3 * zoom,
            fill=VSCodeTheme.COMPONENT_OUTLINE,
            outline=outline_color,
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )
        
        # Determine contact line color and target
        if position == 0:
            # Connected to terminal1
            target_x, target_y = terminal1_x, terminal1_y
            is_powered = common_high or terminal1_high
            is_gnd = common_gnd or terminal1_gnd
        else:
            # Connected to terminal2
            target_x, target_y = terminal2_x, terminal2_y
            is_powered = common_high or terminal2_high
            is_gnd = common_gnd or terminal2_gnd
        
        # Determine contact line color
        if is_gnd:
            contact_color = VSCodeTheme.WIRE_GROUNDED
        elif is_powered:
            contact_color = VSCodeTheme.WIRE_POWERED
        else:
            contact_color = outline_color
        
        # Draw the movable contact line from common to active terminal
        self._draw_line_rotated(
            common_x, common_y,
            target_x - 3 * zoom, target_y,  # Small offset from terminal
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
        
        if label_position == 'top':
            label_y -= offset_v
        elif label_position == 'bottom':
            label_y += offset_v
        elif label_position == 'left':
            label_x -= offset_h
            anchor = 'e'
        elif label_position == 'right':
            label_x += offset_h
            anchor = 'w'
        
        self.draw_text(
            label_x, label_y,
            text=label,
            font_size=10,
            fill=VSCodeTheme.FG_SECONDARY,
            anchor=anchor,
            tags=('component_label', f'label_{self.component.component_id}')
        )
