"""
Base renderer class for component visualization.

All component renderers inherit from ComponentRenderer and implement
the render() method to draw components on the canvas.
"""

import tkinter as tk
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional, Dict, Any
from gui.theme import VSCodeTheme
from components.base import Component
import math


class ComponentRenderer(ABC):
    """
    Base class for rendering components on a tkinter Canvas.
    
    Provides utility methods for:
    - Drawing rotated shapes
    - Converting component coordinates to canvas coordinates
    - Drawing tabs/pins
    - Managing selection state
    """
    
    def __init__(self, canvas: tk.Canvas, component: Component):
        """
        Initialize the renderer.
        
        Args:
            canvas: tkinter Canvas to draw on
            component: Component instance to render
        """
        self.canvas = canvas
        self.component = component
        self.canvas_items: List[int] = []  # Canvas item IDs created by this renderer
        self.selected = False
        self.powered = False  # For simulation mode
        
    @abstractmethod
    def render(self, zoom: float = 1.0) -> None:
        """
        Render the component on the canvas.
        
        Args:
            zoom: Current zoom level (1.0 = 100%)
        """
        pass
        
    def clear(self) -> None:
        """Remove all canvas items created by this renderer."""
        for item_id in self.canvas_items:
            try:
                self.canvas.delete(item_id)
            except:
                pass
        self.canvas_items.clear()
        
    def set_selected(self, selected: bool) -> None:
        """
        Update selection state and re-render.
        
        Args:
            selected: Whether component is selected
        """
        self.selected = selected
        
    def set_powered(self, powered: bool) -> None:
        """
        Update powered state for simulation mode.
        
        Args:
            powered: Whether component is powered
        """
        self.powered = powered
        
    def get_position(self) -> Tuple[float, float]:
        """
        Get component position.
        
        Returns:
            (x, y) position tuple
        """
        return self.component.position
        
    def get_rotation(self) -> int:
        """
        Get component rotation in degrees.
        
        Returns:
            Rotation angle (0, 90, 180, or 270)
        """
        return self.component.rotation
        
    def rotate_point(self, x: float, y: float, cx: float, cy: float, angle: int) -> Tuple[float, float]:
        """
        Rotate a point around a center.
        
        Args:
            x, y: Point to rotate
            cx, cy: Center of rotation
            angle: Rotation angle in degrees
            
        Returns:
            (x', y') rotated point
        """
        if angle == 0:
            return (x, y)
            
        # Convert to radians
        rad = math.radians(angle)
        
        # Translate to origin
        tx = x - cx
        ty = y - cy
        
        # Rotate
        rx = tx * math.cos(rad) - ty * math.sin(rad)
        ry = tx * math.sin(rad) + ty * math.cos(rad)
        
        # Translate back
        return (rx + cx, ry + cy)
        
    def draw_rectangle(self, x: float, y: float, width: float, height: float,
                      fill: str, outline: str, width_px: int = 1,
                      tags: Tuple[str, ...] = ()) -> int:
        """
        Draw a rectangle (rotated if needed).
        
        Args:
            x, y: Top-left corner
            width, height: Rectangle dimensions
            fill: Fill color
            outline: Outline color
            width_px: Outline width
            tags: Canvas tags
            
        Returns:
            Canvas item ID
        """
        cx, cy = self.get_position()
        rotation = self.get_rotation()
        
        # Calculate corners
        corners = [
            (x, y),
            (x + width, y),
            (x + width, y + height),
            (x, y + height)
        ]
        
        # Rotate corners if needed
        if rotation != 0:
            corners = [self.rotate_point(px, py, cx, cy, rotation) for px, py in corners]
            
        # Draw polygon
        item_id = self.canvas.create_polygon(
            *[coord for point in corners for coord in point],
            fill=fill,
            outline=outline,
            width=width_px,
            tags=tags
        )
        
        self.canvas_items.append(item_id)
        return item_id
        
    def draw_circle(self, cx: float, cy: float, radius: float,
                   fill: str, outline: str, width_px: int = 1,
                   tags: Tuple[str, ...] = ()) -> int:
        """
        Draw a circle.
        
        Args:
            cx, cy: Center position
            radius: Circle radius
            fill: Fill color
            outline: Outline color
            width_px: Outline width
            tags: Canvas tags
            
        Returns:
            Canvas item ID
        """
        item_id = self.canvas.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            fill=fill,
            outline=outline,
            width=width_px,
            tags=tags
        )
        
        self.canvas_items.append(item_id)
        return item_id
        
    def draw_line(self, x1: float, y1: float, x2: float, y2: float,
                 fill: str, width_px: int = 2,
                 tags: Tuple[str, ...] = ()) -> int:
        """
        Draw a line (rotated if needed).
        
        Args:
            x1, y1: Start point
            x2, y2: End point
            fill: Line color
            width_px: Line width
            tags: Canvas tags
            
        Returns:
            Canvas item ID
        """
        cx, cy = self.get_position()
        rotation = self.get_rotation()
        
        # Rotate endpoints if needed
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
        return item_id
        
    def draw_text(self, x: float, y: float, text: str,
                 fill: str = None, font: Tuple = None,
                 anchor: str = 'center',
                 tags: Tuple[str, ...] = ()) -> int:
        """
        Draw text.
        
        Args:
            x, y: Text position
            text: Text to draw
            fill: Text color
            font: Font tuple (family, size, weight)
            anchor: Text anchor point
            tags: Canvas tags
            
        Returns:
            Canvas item ID
        """
        if fill is None:
            fill = VSCodeTheme.COMPONENT_TEXT
        if font is None:
            font = VSCodeTheme.get_font('small')
            
        item_id = self.canvas.create_text(
            x, y,
            text=text,
            fill=fill,
            font=font,
            anchor=anchor,
            tags=tags
        )
        
        self.canvas_items.append(item_id)
        return item_id
        
    def draw_tabs(self, zoom: float = 1.0) -> None:
        """
        Draw tabs for all component pins.
        
        Args:
            zoom: Current zoom level
        """
        cx, cy = self.get_position()
        rotation = self.get_rotation()
        
        for pin in self.component.pins.values():
            for tab in pin.tabs.values():
                # Get tab position relative to component
                tx, ty = tab.relative_position
                
                # Rotate tab position
                if rotation != 0:
                    tx, ty = self.rotate_point(
                        cx + tx, cy + ty,
                        cx, cy,
                        rotation
                    )
                else:
                    tx = cx + tx
                    ty = cy + ty
                    
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
