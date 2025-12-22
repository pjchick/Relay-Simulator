"""
Wire Renderer - Renders wires, waypoints, and junctions on canvas.

Handles visual rendering of wire connections between component tabs,
including waypoints for routing and junctions for branching.
"""

import tkinter as tk
import math
from typing import List, Tuple, Optional, Dict
from gui.theme import VSCodeTheme
from core.wire import Wire, Waypoint, Junction
from core.page import Page


class WireRenderer:
    """
    Renderer for wire connections on the canvas.
    
    Renders:
    - Wire segments (lines between points)
    - Waypoints (small squares along wire path)
    - Junctions (circles where wires branch)
    
    Supports:
    - Selection highlighting
    - Powered state visualization
    - Zoom scaling
    """
    
    def __init__(
        self,
        canvas: tk.Canvas,
        wire: Wire,
        page: Page,
        hovered_waypoint: Optional[Tuple[str, str]] = None,
        selected_waypoints: Optional[set] = None,
    ):
        """
        Initialize wire renderer.
        
        Args:
            canvas: Tkinter canvas to draw on
            wire: Wire object to render
            page: Page containing the wire (for looking up tab positions)
            hovered_waypoint: Optional tuple of (wire_id, waypoint_id) for waypoint being hovered
            selected_waypoints: Optional set of (wire_id, waypoint_id) tuples to render as selected
        """
        self.canvas = canvas
        self.wire = wire
        self.page = page
        self.canvas_items = []  # Track created canvas items for cleanup
        self.selected = False
        self.powered = False
        self.hovered_waypoint = hovered_waypoint
        self.selected_waypoints = selected_waypoints
    
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the wire on canvas.
        
        Args:
            zoom: Current zoom level
        """
        self.clear()
        
        # Get wire path points (world coords)
        points = self._get_wire_path()
        if len(points) < 2:
            return  # Need at least 2 points to draw a wire

        def to_canvas(pt: Tuple[float, float]) -> Tuple[float, float]:
            x, y = pt
            return (x * zoom, y * zoom)
        
        # Determine wire color
        if self.selected:
            color = VSCodeTheme.WIRE_SELECTED
        elif self.powered:
            color = VSCodeTheme.WIRE_POWERED
        else:
            color = VSCodeTheme.WIRE_UNPOWERED
        
        # Draw wire segments
        for i in range(len(points) - 1):
            x1, y1 = to_canvas(points[i])
            x2, y2 = to_canvas(points[i + 1])
            
            item = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=VSCodeTheme.WIRE_WIDTH * zoom,
                tags=(f"wire_{self.wire.wire_id}", "wire")
            )
            self.canvas_items.append(item)
        
        # Draw waypoints
        for waypoint in self.wire.waypoints.values():
            self._draw_waypoint(waypoint, zoom)
        
        # Draw junctions
        for junction in self.wire.junctions.values():
            self._draw_junction(junction, zoom)
            # Recursively render child wires from this junction
            for child_wire in junction.child_wires.values():
                child_renderer = WireRenderer(
                    self.canvas,
                    child_wire,
                    self.page,
                    self.hovered_waypoint,
                    selected_waypoints=self.selected_waypoints,
                )
                child_renderer.selected = self.selected
                child_renderer.powered = self.powered
                child_renderer.render(zoom)
    
    def _get_wire_path(self) -> List[Tuple[float, float]]:
        """
        Get ordered list of points defining the wire path.
        
        Returns:
            List of (x, y) tuples representing wire path
        """
        points = []
        
        # Start point from start tab
        start_pos = self._get_tab_position(self.wire.start_tab_id)
        if start_pos:
            points.append(start_pos)
        
        # Add waypoints (in order - assume they're already ordered in wire.waypoints)
        # For proper ordering, waypoints should be stored in an ordered dict or list
        # For now, we'll just add them in dictionary order
        for waypoint in self.wire.waypoints.values():
            points.append(waypoint.position)
        
        # End point from end tab or junction
        if self.wire.end_tab_id:
            end_pos = self._get_tab_position(self.wire.end_tab_id)
            if end_pos:
                points.append(end_pos)
        elif self.wire.junctions:
            # If wire ends at junction, use first junction position
            # Note: Typically there should be only one junction per wire
            first_junction = next(iter(self.wire.junctions.values()))
            points.append(first_junction.position)
        
        return points
    
    def _get_tab_position(self, tab_id: str) -> Optional[Tuple[float, float]]:
        """
        Get absolute position of a tab or junction.
        
        Args:
            tab_id: ID of tab or junction to locate
            
        Returns:
            (x, y) position or None if not found
        """
        # First check if this is a junction ID (junctions are stored in page.junctions)
        junction = self.page.junctions.get(tab_id)
        if junction:
            return junction.position
        
        # Otherwise parse as tab_id
        # Format: {component_id}.{pin_name}.{tab_name}
        # Example: 7ab1d562.pin1.tab3
        parts = tab_id.split('.')
        if len(parts) < 3:
            return None
        
        component_id = parts[0]
        pin_name = parts[1]
        
        # Find component in page
        component = self.page.components.get(component_id)
        if not component:
            return None
        
        # Find pin
        pin_id = f"{component_id}.{pin_name}"
        pin = component.pins.get(pin_id)
        if not pin:
            return None
        
        # Find tab
        tab = pin.tabs.get(tab_id)
        if not tab:
            return None
        
        # Get absolute position
        comp_x, comp_y = component.position
        rotation = getattr(component, 'rotation', 0) or 0
        tab_dx, tab_dy = tab.relative_position

        # Apply component flips in local space (around component center) before rotation.
        try:
            props = getattr(component, 'properties', {}) or {}
            flip_h = bool(props.get('flip_horizontal', False))
            flip_v = bool(props.get('flip_vertical', False))
        except Exception:
            flip_h = False
            flip_v = False

        if flip_h:
            tab_dx = -tab_dx
        if flip_v:
            tab_dy = -tab_dy

        x = comp_x + tab_dx
        y = comp_y + tab_dy
        if rotation:
            rad = math.radians(rotation % 360)
            tx = x - comp_x
            ty = y - comp_y
            rx = (tx * math.cos(rad)) - (ty * math.sin(rad))
            ry = (tx * math.sin(rad)) + (ty * math.cos(rad))
            x = rx + comp_x
            y = ry + comp_y

        return (x, y)
    
    def _draw_waypoint(self, waypoint: Waypoint, zoom: float) -> None:
        """
        Draw a waypoint marker (only visible when hovered).
        
        Args:
            waypoint: Waypoint to draw
            zoom: Current zoom level
        """
        # Draw waypoint marker when hovered or explicitly selected
        # hovered_waypoint format: (wire_id, waypoint_id)
        is_hovered = (
            self.hovered_waypoint
            and self.hovered_waypoint[0] == self.wire.wire_id
            and self.hovered_waypoint[1] == waypoint.waypoint_id
        )
        is_selected = bool(self.selected_waypoints) and ((self.wire.wire_id, waypoint.waypoint_id) in self.selected_waypoints)

        if not (is_hovered or is_selected):
            return
        
        x, y = waypoint.position
        x *= zoom
        y *= zoom
        size = 4 * zoom  # Waypoint size
        
        fill = VSCodeTheme.WIRE_SELECTED if (self.selected or is_selected) else VSCodeTheme.COMPONENT_OUTLINE
        outline = VSCodeTheme.COMPONENT_OUTLINE

        # Draw as small circle
        item = self.canvas.create_oval(
            x - size, y - size,
            x + size, y + size,
            fill=fill,
            outline=outline,
            width=1,
            tags=(f"waypoint_{self.wire.wire_id}_{waypoint.waypoint_id}", "waypoint")
        )
        self.canvas_items.append(item)
    
    def _draw_junction(self, junction: Junction, zoom: float) -> None:
        """
        Draw a junction marker as a circle.
        
        Args:
            junction: Junction to draw
            zoom: Current zoom level
        """
        x, y = junction.position
        x *= zoom
        y *= zoom
        radius = 5 * zoom  # Junction radius
        
        # Determine junction color: red if powered, gray if unpowered, blue if selected
        if self.selected:
            fill_color = VSCodeTheme.WIRE_SELECTED  # Blue when selected
        elif self.powered:
            fill_color = '#ff0000'  # Red when powered (HIGH)
        else:
            fill_color = VSCodeTheme.WIRE_UNPOWERED  # Gray when unpowered
        
        # Draw as circle
        item = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=fill_color,
            outline=VSCodeTheme.COMPONENT_OUTLINE,
            width=2,
            tags=(f"junction_{junction.junction_id}", "junction")
        )
        self.canvas_items.append(item)
    
    def clear(self) -> None:
        """Remove all canvas items created by this renderer."""
        for item in self.canvas_items:
            self.canvas.delete(item)
        self.canvas_items.clear()
    
    def set_selected(self, selected: bool) -> None:
        """
        Set wire selection state.
        
        Args:
            selected: True if selected, False otherwise
        """
        self.selected = selected
    
    def set_powered(self, powered: bool) -> None:
        """
        Set wire powered state (for simulation mode).
        
        Args:
            powered: True if wire is powered, False otherwise
        """
        self.powered = powered
