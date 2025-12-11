"""
Wire Renderer - Renders wires, waypoints, and junctions on canvas.

Handles visual rendering of wire connections between component tabs,
including waypoints for routing and junctions for branching.
"""

import tkinter as tk
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
    
    def __init__(self, canvas: tk.Canvas, wire: Wire, page: Page):
        """
        Initialize wire renderer.
        
        Args:
            canvas: Tkinter canvas to draw on
            wire: Wire object to render
            page: Page containing the wire (for looking up tab positions)
        """
        self.canvas = canvas
        self.wire = wire
        self.page = page
        self.canvas_items = []  # Track created canvas items for cleanup
        self.selected = False
        self.powered = False
    
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the wire on canvas.
        
        Args:
            zoom: Current zoom level
        """
        self.clear()
        
        # Get wire path points
        points = self._get_wire_path()
        if len(points) < 2:
            return  # Need at least 2 points to draw a wire
        
        # Determine wire color
        if self.selected:
            color = VSCodeTheme.WIRE_SELECTED
        elif self.powered:
            color = VSCodeTheme.WIRE_POWERED
        else:
            color = VSCodeTheme.WIRE_UNPOWERED
        
        # Draw wire segments
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            
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
                child_renderer = WireRenderer(self.canvas, child_wire, self.page)
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
        Get absolute position of a tab.
        
        Args:
            tab_id: ID of tab to locate
            
        Returns:
            (x, y) position or None if tab not found
        """
        # Parse tab_id to get component_id
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
        tab_dx, tab_dy = tab.relative_position
        
        return (comp_x + tab_dx, comp_y + tab_dy)
    
    def _draw_waypoint(self, waypoint: Waypoint, zoom: float) -> None:
        """
        Draw a waypoint marker.
        
        Args:
            waypoint: Waypoint to draw
            zoom: Current zoom level
        """
        x, y = waypoint.position
        size = 4 * zoom  # Waypoint size
        
        # Draw as small square
        item = self.canvas.create_rectangle(
            x - size, y - size,
            x + size, y + size,
            fill=VSCodeTheme.WIRE_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE,
            outline=VSCodeTheme.COMPONENT_OUTLINE,
            width=1,
            tags=(f"waypoint_{waypoint.waypoint_id}", "waypoint")
        )
        self.canvas_items.append(item)
    
    def _draw_junction(self, junction: Junction, zoom: float) -> None:
        """
        Draw a junction marker.
        
        Args:
            junction: Junction to draw
            zoom: Current zoom level
        """
        x, y = junction.position
        radius = 5 * zoom  # Junction radius
        
        # Draw as circle
        item = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=VSCodeTheme.WIRE_SELECTED if self.selected else VSCodeTheme.WIRE_POWERED,
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
