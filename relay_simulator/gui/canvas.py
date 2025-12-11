"""
Design Canvas for Relay Simulator III

Provides DesignCanvas class with scrollable canvas, grid rendering,
zoom (mouse wheel), pan (right-click drag), and component rendering support.
"""

import tkinter as tk
from typing import Tuple, Optional, Dict, List
from gui.theme import VSCodeTheme
from gui.renderers.renderer_factory import RendererFactory
from gui.renderers.base_renderer import ComponentRenderer
from gui.renderers.wire_renderer import WireRenderer
from components.base import Component
from core.page import Page
from core.wire import Wire


class DesignCanvas:
    """
    Scrollable canvas with grid, zoom, and pan support.
    
    Features:
    - Configurable canvas size (default 3000x3000)
    - Grid rendering with configurable spacing
    - Mouse wheel zoom (0.1x to 5.0x)
    - Right-click pan
    - Coordinate conversion (canvas <-> screen)
    """
    
    def __init__(self, parent: tk.Widget, width: int = 3000, height: int = 3000, 
                 grid_size: int = 20):
        """
        Initialize design canvas.
        
        Args:
            parent: Parent widget
            width: Canvas width in pixels
            height: Canvas height in pixels
            grid_size: Grid spacing in pixels
        """
        self.parent = parent
        self.canvas_width = width
        self.canvas_height = height
        self.grid_size = grid_size
        
        # Zoom state
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # Pan state
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False
        
        # Component renderers
        self.renderers: Dict[str, ComponentRenderer] = {}  # component_id -> renderer
        self.wire_renderers: Dict[str, WireRenderer] = {}  # wire_id -> wire_renderer
        self.current_page: Optional[Page] = None
        
        # Create widgets
        self._create_widgets()
        
        # Bind events
        self._bind_events()
        
        # Draw initial grid
        self._draw_grid()
    
    def _create_widgets(self) -> None:
        """Create canvas and scrollbars."""
        # Container frame
        self.frame = tk.Frame(self.parent, bg=VSCodeTheme.BG_PRIMARY)
        
        # Horizontal scrollbar
        self.h_scrollbar = tk.Scrollbar(
            self.frame,
            orient=tk.HORIZONTAL,
            bg=VSCodeTheme.BG_SECONDARY,
            troughcolor=VSCodeTheme.BG_PRIMARY,
            activebackground=VSCodeTheme.ACCENT_BLUE
        )
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Vertical scrollbar
        self.v_scrollbar = tk.Scrollbar(
            self.frame,
            orient=tk.VERTICAL,
            bg=VSCodeTheme.BG_SECONDARY,
            troughcolor=VSCodeTheme.BG_PRIMARY,
            activebackground=VSCodeTheme.ACCENT_BLUE
        )
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas
        self.canvas = tk.Canvas(
            self.frame,
            bg=VSCodeTheme.BG_PRIMARY,
            width=800,  # Initial view size
            height=600,
            scrollregion=(0, 0, self.canvas_width, self.canvas_height),
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)
        
        # Grid layer (drawn first, stays in background)
        self.grid_items = []
    
    def _bind_events(self) -> None:
        """Bind mouse and keyboard events."""
        # Zoom with mouse wheel
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)  # Linux scroll down
        
        # Pan with right-click drag
        self.canvas.bind("<Button-3>", self._on_pan_start)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_end)
    
    def _draw_grid(self) -> None:
        """Draw grid lines on canvas."""
        # Clear existing grid
        for item in self.grid_items:
            self.canvas.delete(item)
        self.grid_items.clear()
        
        # Grid color (subtle dark gray)
        grid_color = "#2d2d2d"
        
        # Calculate visible region
        x1, y1 = 0, 0
        x2, y2 = self.canvas_width, self.canvas_height
        
        # Adjust grid size based on zoom
        effective_grid_size = self.grid_size * self.zoom_level
        
        # Don't draw grid if too small (would be too dense)
        if effective_grid_size < 5:
            return
        
        # Draw vertical lines
        x = 0
        while x <= x2:
            item = self.canvas.create_line(
                x, y1, x, y2,
                fill=grid_color,
                width=1,
                tags="grid"
            )
            self.grid_items.append(item)
            x += self.grid_size
        
        # Draw horizontal lines
        y = 0
        while y <= y2:
            item = self.canvas.create_line(
                x1, y, x2, y,
                fill=grid_color,
                width=1,
                tags="grid"
            )
            self.grid_items.append(item)
            y += self.grid_size
        
        # Lower grid to background
        self.canvas.tag_lower("grid")
    
    def _on_mouse_wheel(self, event) -> None:
        """
        Handle mouse wheel event for zooming.
        
        Args:
            event: Mouse wheel event
        """
        # Get mouse position in canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Determine zoom direction
        if event.num == 4 or event.delta > 0:
            # Zoom in
            zoom_factor = 1.1
        else:
            # Zoom out
            zoom_factor = 0.9
        
        # Calculate new zoom level
        new_zoom = self.zoom_level * zoom_factor
        
        # Clamp zoom level
        if new_zoom < self.min_zoom or new_zoom > self.max_zoom:
            return "break"  # Stop event propagation
        
        # Apply zoom
        self._apply_zoom(zoom_factor, canvas_x, canvas_y)
        
        # Return "break" to stop event propagation
        return "break"
    
    def _apply_zoom(self, zoom_factor: float, center_x: float, center_y: float) -> None:
        """
        Apply zoom transformation centered on given point.
        
        Args:
            zoom_factor: Zoom multiplier
            center_x: Center X in canvas coordinates
            center_y: Center Y in canvas coordinates
        """
        # Update zoom level
        self.zoom_level *= zoom_factor
        
        # Scale all canvas items except grid
        self.canvas.scale("all", center_x, center_y, zoom_factor, zoom_factor)
        
        # Update scroll region
        new_width = int(self.canvas_width * self.zoom_level)
        new_height = int(self.canvas_height * self.zoom_level)
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))
        
        # Redraw grid at new zoom level
        self._draw_grid()
        
        # Re-render all components at new zoom level
        for renderer in self.renderers.values():
            renderer.render(self.zoom_level)
        
        # Re-render all wires at new zoom level
        for wire_renderer in self.wire_renderers.values():
            wire_renderer.render(self.zoom_level)
        
        # Adjust scroll position to keep center point in view
        # Calculate the new position of the center point after scaling
        new_center_x = center_x * zoom_factor
        new_center_y = center_y * zoom_factor
        
        # Get current view size
        view_width = self.canvas.winfo_width()
        view_height = self.canvas.winfo_height()
        
        # Calculate new scroll position to keep center in same screen position
        scroll_x = (new_center_x - view_width / 2) / new_width
        scroll_y = (new_center_y - view_height / 2) / new_height
        
        self.canvas.xview_moveto(max(0, min(1, scroll_x)))
        self.canvas.yview_moveto(max(0, min(1, scroll_y)))
    
    def _on_pan_start(self, event) -> None:
        """
        Handle pan start (right-click press).
        
        Args:
            event: Mouse button event
        """
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
        # Change cursor to indicate panning
        self.canvas.config(cursor="fleur")
    
    def _on_pan_drag(self, event) -> None:
        """
        Handle pan drag (right-click drag).
        
        Args:
            event: Mouse motion event
        """
        if not self.is_panning:
            return
        
        # Calculate movement
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        
        # Update canvas scroll position
        # Note: canvas.scan_mark and scan_dragto provide smooth panning
        self.canvas.scan_mark(self.pan_start_x, self.pan_start_y)
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        
        # Update pan start for next drag event
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def _on_pan_end(self, event) -> None:
        """
        Handle pan end (right-click release).
        
        Args:
            event: Mouse button release event
        """
        self.is_panning = False
        self.canvas.config(cursor="")
    
    def zoom_in(self) -> None:
        """Zoom in (centered on canvas center)."""
        # Get canvas center
        view_width = self.canvas.winfo_width()
        view_height = self.canvas.winfo_height()
        center_x = self.canvas.canvasx(view_width / 2)
        center_y = self.canvas.canvasy(view_height / 2)
        
        if self.zoom_level * 1.25 <= self.max_zoom:
            self._apply_zoom(1.25, center_x, center_y)
    
    def zoom_out(self) -> None:
        """Zoom out (centered on canvas center)."""
        # Get canvas center
        view_width = self.canvas.winfo_width()
        view_height = self.canvas.winfo_height()
        center_x = self.canvas.canvasx(view_width / 2)
        center_y = self.canvas.canvasy(view_height / 2)
        
        if self.zoom_level * 0.8 >= self.min_zoom:
            self._apply_zoom(0.8, center_x, center_y)
    
    def reset_zoom(self) -> None:
        """Reset zoom to 100%."""
        # Get canvas center
        view_width = self.canvas.winfo_width()
        view_height = self.canvas.winfo_height()
        center_x = self.canvas.canvasx(view_width / 2)
        center_y = self.canvas.canvasy(view_height / 2)
        
        # Calculate zoom factor to return to 1.0
        zoom_factor = 1.0 / self.zoom_level
        self._apply_zoom(zoom_factor, center_x, center_y)
    
    def get_zoom_level(self) -> float:
        """
        Get current zoom level.
        
        Returns:
            float: Zoom level (1.0 = 100%)
        """
        return self.zoom_level
    
    def set_canvas_size(self, width: int, height: int) -> None:
        """
        Set canvas size.
        
        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        self.canvas_width = width
        self.canvas_height = height
        
        # Update scroll region
        scaled_width = int(width * self.zoom_level)
        scaled_height = int(height * self.zoom_level)
        self.canvas.config(scrollregion=(0, 0, scaled_width, scaled_height))
        
        # Redraw grid
        self._draw_grid()
    
    def set_grid_size(self, size: int) -> None:
        """
        Set grid spacing.
        
        Args:
            size: Grid spacing in pixels
        """
        self.grid_size = size
        self._draw_grid()
    
    def canvas_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert canvas coordinates to screen coordinates.
        
        Args:
            x: Canvas X coordinate
            y: Canvas Y coordinate
            
        Returns:
            Tuple of (screen_x, screen_y)
        """
        screen_x = self.canvas.canvasx(0) + (x - self.canvas.canvasx(0)) * self.zoom_level
        screen_y = self.canvas.canvasy(0) + (y - self.canvas.canvasy(0)) * self.zoom_level
        return (screen_x, screen_y)
    
    def screen_to_canvas(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert screen coordinates to canvas coordinates.
        
        Args:
            x: Screen X coordinate
            y: Screen Y coordinate
            
        Returns:
            Tuple of (canvas_x, canvas_y)
        """
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)
        return (canvas_x, canvas_y)
    
    def pack(self, **kwargs) -> None:
        """Pack the canvas frame."""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs) -> None:
        """Grid the canvas frame."""
        self.frame.grid(**kwargs)
    
    def clear(self) -> None:
        """Clear all items from canvas (except grid)."""
        # Delete all items except grid
        for item in self.canvas.find_all():
            if item not in self.grid_items:
                self.canvas.delete(item)
    
    # Canvas state management for per-page persistence
    
    def save_canvas_state(self) -> Tuple[float, float, float]:
        """
        Save current canvas state (position and zoom).
        
        Returns:
            Tuple of (canvas_x, canvas_y, zoom_level)
        """
        # Get current scroll position (0.0 to 1.0)
        x_fraction = self.canvas.xview()[0]
        y_fraction = self.canvas.yview()[0]
        
        # Convert to canvas coordinates
        scaled_width = int(self.canvas_width * self.zoom_level)
        scaled_height = int(self.canvas_height * self.zoom_level)
        
        canvas_x = x_fraction * scaled_width
        canvas_y = y_fraction * scaled_height
        
        return (canvas_x, canvas_y, self.zoom_level)
    
    def restore_canvas_state(self, canvas_x: float, canvas_y: float, zoom: float) -> None:
        """
        Restore canvas state (position and zoom).
        
        Args:
            canvas_x: Canvas X position
            canvas_y: Canvas Y position
            zoom: Zoom level
        """
        # Reset zoom to 1.0 first
        if self.zoom_level != 1.0:
            zoom_factor = 1.0 / self.zoom_level
            view_width = self.canvas.winfo_width()
            view_height = self.canvas.winfo_height()
            center_x = self.canvas.canvasx(view_width / 2)
            center_y = self.canvas.canvasy(view_height / 2)
            self._apply_zoom(zoom_factor, center_x, center_y)
        
        # Apply target zoom
        if zoom != 1.0:
            view_width = self.canvas.winfo_width()
            view_height = self.canvas.winfo_height()
            center_x = self.canvas.canvasx(view_width / 2)
            center_y = self.canvas.canvasy(view_height / 2)
            self._apply_zoom(zoom, center_x, center_y)
        
        # Restore scroll position
        scaled_width = int(self.canvas_width * self.zoom_level)
        scaled_height = int(self.canvas_height * self.zoom_level)
        
        if scaled_width > 0:
            x_fraction = canvas_x / scaled_width
            self.canvas.xview_moveto(max(0, min(1, x_fraction)))
        
        if scaled_height > 0:
            y_fraction = canvas_y / scaled_height
            self.canvas.yview_moveto(max(0, min(1, y_fraction)))
    
    # === COMPONENT RENDERING ===
    
    def set_page(self, page: Optional[Page]) -> None:
        """
        Set the current page and render its components.
        
        Args:
            page: Page to display, or None to clear
        """
        self.current_page = page
        self.render_components()
    
    def render_components(self) -> None:
        """Render all components on the current page."""
        # Clear existing renderers
        self.clear_components()
        
        if not self.current_page:
            return
            
        # Create renderers for all components
        for component in self.current_page.components.values():
            try:
                renderer = RendererFactory.create_renderer(self.canvas, component)
                self.renderers[component.component_id] = renderer
                renderer.render(self.zoom_level)
            except Exception as e:
                print(f"Error rendering component {component.component_id}: {e}")
        
        # Render all wires
        self.render_wires()
    
    def clear_components(self) -> None:
        """Clear all rendered components and wires."""
        for renderer in self.renderers.values():
            renderer.clear()
        self.renderers.clear()
        
        for wire_renderer in self.wire_renderers.values():
            wire_renderer.clear()
        self.wire_renderers.clear()
    
    def update_component(self, component_id: str) -> None:
        """
        Update rendering for a specific component.
        
        Args:
            component_id: ID of component to update
        """
        renderer = self.renderers.get(component_id)
        if renderer:
            renderer.render(self.zoom_level)
    
    def set_component_selected(self, component_id: str, selected: bool) -> None:
        """
        Set selection state for a component.
        
        Args:
            component_id: ID of component
            selected: Whether component is selected
        """
        renderer = self.renderers.get(component_id)
        if renderer:
            renderer.set_selected(selected)
            renderer.render(self.zoom_level)
    
    def set_component_powered(self, component_id: str, powered: bool) -> None:
        """
        Set powered state for a component (simulation mode).
        
        Args:
            component_id: ID of component
            powered: Whether component is powered
        """
        renderer = self.renderers.get(component_id)
        if renderer:
            renderer.set_powered(powered)
            renderer.render(self.zoom_level)
    
    # === WIRE RENDERING ===
    
    def render_wires(self) -> None:
        """Render all wires on the current page."""
        # Clear existing wire renderers
        self.clear_wires()
        
        if not self.current_page:
            return
        
        # Create renderers for all wires
        for wire in self.current_page.wires.values():
            try:
                renderer = WireRenderer(self.canvas, wire, self.current_page)
                self.wire_renderers[wire.wire_id] = renderer
                renderer.render(self.zoom_level)
            except Exception as e:
                print(f"Error rendering wire {wire.wire_id}: {e}")
    
    def clear_wires(self) -> None:
        """Clear all rendered wires."""
        for wire_renderer in self.wire_renderers.values():
            wire_renderer.clear()
        self.wire_renderers.clear()
    
    def update_wire(self, wire_id: str) -> None:
        """
        Update rendering for a specific wire.
        
        Args:
            wire_id: ID of wire to update
        """
        renderer = self.wire_renderers.get(wire_id)
        if renderer:
            renderer.render(self.zoom_level)
    
    def set_wire_selected(self, wire_id: str, selected: bool) -> None:
        """
        Set selection state for a wire.
        
        Args:
            wire_id: ID of wire
            selected: Whether wire is selected
        """
        renderer = self.wire_renderers.get(wire_id)
        if renderer:
            renderer.set_selected(selected)
            renderer.render(self.zoom_level)
    
    def set_wire_powered(self, wire_id: str, powered: bool) -> None:
        """
        Set powered state for a wire (simulation mode).
        
        Args:
            wire_id: ID of wire
            powered: Whether wire is powered
        """
        renderer = self.wire_renderers.get(wire_id)
        if renderer:
            renderer.set_powered(powered)
            renderer.render(self.zoom_level)
