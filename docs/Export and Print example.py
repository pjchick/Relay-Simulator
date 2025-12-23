"""
Canvas Manager - Handles the drawing canvas and component/wire management
"""

import math
import os
import shutil
import subprocess
import tempfile
import tkinter as tk
import traceback
import time
import threading
from pathlib import Path
from tkinter import Canvas
import re

from src.core.junction import Junction
from src.core.wire import Wire
from src.components.memory import Memory

class CanvasManager:
    def __init__(self, parent, toolbar):
        """
        Initialize the canvas manager
        
        Args:
            parent: Parent widget
            toolbar: Toolbar widget reference
        """
        self.parent = parent
        self.toolbar = toolbar
        self.properties_panel = None
        
        # Add scrollbars first (before canvas)
        h_scroll = tk.Scrollbar(parent, orient=tk.HORIZONTAL)
        v_scroll = tk.Scrollbar(parent, orient=tk.VERTICAL)
        
        # Create canvas with scrollbar commands
        self.canvas = Canvas(parent, bg='white', cursor='crosshair',
                           xscrollcommand=h_scroll.set, 
                           yscrollcommand=v_scroll.set)
        
        # Configure scrollbar commands
        h_scroll.config(command=self.canvas.xview)
        v_scroll.config(command=self.canvas.yview)
        
        # Pack scrollbars and canvas in correct order
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrolling region - larger canvas for more space
        self.canvas.config(scrollregion=(0, 0, 4000, 4000))
        
        # Center the canvas view - schedule after widgets are created
        self.canvas.after(100, self.center_canvas_view)
        
        # Page management
        self.pages = {}  # Dictionary of page_name: {components, wires, junctions, zoom, scroll_x, scroll_y}
        self.current_page = "Page 1"
        self.pages[self.current_page] = {
            'components': [],
            'wires': [],
            'junctions': [],
            'zoom': 1.0,
            'scroll_x': 0.5,
            'scroll_y': 0.5
        }
        
        # Component and wire storage (references to current page)
        self.components = self.pages[self.current_page]['components']
        self.wires = self.pages[self.current_page]['wires']
        self.junctions = self.pages[self.current_page]['junctions']
        
        # Interaction state
        self.selected_component = None
        self.selected_components = []  # Multiple selected components
        self.selected_wire = None
        self.dragging_component = None
        self.dragging_selection = False  # Dragging multiple selected components
        self.drag_start = None
        self.selection_rect = None  # Rectangle selection
        self.selection_rect_start = None
        self.wiring_mode = False
        self.wire_start_pin = None
        self.wire_waypoints = []  # Waypoints for current wire being created
        self.temp_wire_lines = []  # Temporary line segments while routing
        self.panning = False  # Canvas panning mode
        self.pan_start = None  # Starting position for pan
        self.left_button_down = False  # Track left mouse button state
        self.right_button_down = False  # Track right mouse button state
        self.pending_wire_start = None  # Delayed wire start to allow double-click detection
        self.zoom_level = 1.0
        self.grid_size = 10  # Grid snap size in pixels
        self.wire_angle_mode = 90  # 90 or 45 degree routing
        self.update_counter = 0  # Counter to reduce visual update frequency
        
        # Waypoint dragging
        self.dragging_waypoint = False
        self.dragging_waypoint_wire = None
        self.dragging_waypoint_index = None
        
        # Junction click-and-hold for dragging
        self.junction_hold_timer = None
        self.junction_hold_active = False
        self.junction_clicked = None
        
        # Rectangle resizing
        self.resizing_rectangle = False
        self.resize_rectangle = None
        self.resize_handle = None  # 'se', 'sw', 'ne', 'nw', 'e', 'w', 'n', 's'
        self.resize_start_pos = None
        self.resize_start_size = None
        self.resize_start_rect_pos = None  # Original (x, y) of rectangle
        
        # Logic processing control
        self.logic_running = False  # True = processing logic, False = stopped (start in STOP mode)
        
        # Debug: Track where we are in update cycle
        self.current_operation = "idle"
        self.operation_start_time = 0
        self._update_call_count = 0
        self._last_update_count_reset = time.time()
        self._update_scheduled = False  # Track if an update is already scheduled
        
        # Undo/Redo stacks
        self.undo_stack = []  # Stack of previous states
        self.redo_stack = []  # Stack of undone states
        self.max_undo_levels = 50  # Maximum number of undo levels
        
        # Clipboard for copy/cut/paste
        self.clipboard_components = []  # List of component data to paste
        self.clipboard_junctions = []  # List of junction data to paste
        self.clipboard_wires = []  # List of wire data to paste
        self.clipboard_manual_pin_states = {}  # Manual pin states
        self.clipboard_is_cut = False  # True if cut, False if copy
        self.clipboard_source_page = None  # Page where cut/copy occurred
        
        # Track last mouse position for paste operation
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # Context menu
        self.context_menu = None
        self.context_menu_x = 0
        self.context_menu_y = 0
        self.pending_right_click = None  # Delayed right-click to detect double-click
        
        # Bind events
        self.canvas.bind('<Button-1>', self.on_left_press)
        self.canvas.bind('<Double-Button-1>', self.on_double_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_left_release)
        self.canvas.bind('<Button-3>', self.on_right_press)
        self.canvas.bind('<Double-Button-3>', self.on_right_double_click)
        self.canvas.bind('<ButtonRelease-3>', self.on_right_release)
        self.canvas.bind('<Motion>', self.on_motion)
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)  # Windows/Mac
        self.canvas.bind('<Button-4>', self.on_mousewheel)    # Linux scroll up
        self.canvas.bind('<Button-5>', self.on_mousewheel)    # Linux scroll down
        
        # Start watchdog immediately to detect freezes anytime
        self.start_watchdog()
        
        # Make canvas focusable
        self.canvas.config(takefocus=True)
        self.canvas.focus_set()
        
        # Status bar references
        self.status_bar_label = None
        self.zoom_label = None
        
        # Set up toolbar drag and drop
        self.toolbar.set_canvas_manager(self)
        
        # Start update loop
        self.update()
        
    def set_status_bar(self, status_bar, zoom_label, grid_label=None):
        """Set reference to status bar labels"""
        self.status_bar_label = status_bar
        self.zoom_label = zoom_label
        self.grid_label = grid_label
        self.update_zoom_display()
        if self.grid_label:
            self.grid_label.config(text="Grid: 20px")
        
    def set_properties_panel(self, properties_panel):
        """Set reference to properties panel"""
        self.properties_panel = properties_panel
    
    def setup_keybindings(self, root_window):
        """Setup keyboard bindings on the root window"""
        root_window.bind('<Key-r>', self.on_rotate_key)
        root_window.bind('<Key-R>', self.on_rotate_key)
        root_window.bind('<Key-d>', self.on_delete_key)
        root_window.bind('<Key-D>', self.on_delete_key)
        root_window.bind('<Escape>', self.on_escape_key)
        # Copy/Cut/Paste bindings - try both lowercase and uppercase Control
        root_window.bind('<Control-c>', self.on_copy_key)
        root_window.bind('<Control-C>', self.on_copy_key)
        root_window.bind('<Control-x>', self.on_cut_key)
        root_window.bind('<Control-X>', self.on_cut_key)
        root_window.bind('<Control-v>', self.on_paste_key)
        root_window.bind('<Control-V>', self.on_paste_key)
        # Undo/Redo bindings
        root_window.bind('<Control-z>', self.on_undo_key)
        root_window.bind('<Control-Z>', self.on_undo_key)
        root_window.bind('<Control-y>', self.on_redo_key)
        root_window.bind('<Control-Y>', self.on_redo_key)
        
    def on_click(self, event):
        """Handle mouse click"""
        try:
            self._on_click_impl(event)
        except Exception as e:
            print(f"❌ ERROR in on_click: {e}")
            traceback.print_exc()
    
    def _on_click_impl(self, event):
        """Handle mouse click - implementation"""
        # Set focus to canvas so keyboard events work
        self.canvas.focus_set()
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Convert from zoomed canvas coordinates to logical coordinates
        x, y = self.unapply_zoom_coords(x, y)
        
        # Check for junction FIRST (before pins) since junctions have pins
        clicked_junction = self.get_junction_at_position(x, y)
        if clicked_junction:
            # Store the junction and start a timer for hold detection
            self.junction_clicked = clicked_junction
            self.drag_start = (x, y)
            
            # Check if Ctrl is held for multi-select
            if event.state & 0x4:  # Ctrl key
                if clicked_junction in self.selected_components:
                    # Remove from selection
                    self.selected_components.remove(clicked_junction)
                    clicked_junction.selected = False
                else:
                    # Add to selection
                    self.selected_components.append(clicked_junction)
                    clicked_junction.selected = True
                self.junction_clicked = None  # Don't enable dragging in multi-select
            else:
                # Start a timer - if mouse is still down after 200ms, enable dragging
                self.junction_hold_timer = self.canvas.after(200, self.enable_junction_drag)
            return
        
        # Check if clicking on a pin (for wiring)
        pin = self.get_pin_at_position(x, y)
        if pin:
            # Single click on pin does nothing - wiring requires double-click
            return
        
        # If in wiring mode and clicking on a wire, create a junction
        if self.wiring_mode:
            clicked_wire = self.get_wire_at_position(x, y)
            if clicked_wire:
                # Find the exact point on the wire closest to the click
                # This prevents wires from jumping when a junction is added
                old_pin1 = clicked_wire.pin1
                old_pin2 = clicked_wire.pin2
                old_waypoints = clicked_wire.waypoints
                
                # Build the complete path including endpoints
                all_points = [old_pin1.get_position()] + old_waypoints + [old_pin2.get_position()]
                
                # Find which segment the click is closest to and the exact point on that segment
                min_dist = float('inf')
                best_point_x = x
                best_point_y = y
                split_index = 0
                
                for i in range(len(all_points) - 1):
                    x1, y1 = all_points[i]
                    x2, y2 = all_points[i + 1]
                    
                    # Find the closest point on this segment to the click
                    dx = x2 - x1
                    dy = y2 - y1
                    
                    if dx == 0 and dy == 0:
                        # Degenerate segment
                        closest_x, closest_y = x1, y1
                    else:
                        # Calculate projection parameter t
                        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
                        closest_x = x1 + t * dx
                        closest_y = y1 + t * dy
                    
                    # Calculate distance from click to this point
                    dist = ((x - closest_x) ** 2 + (y - closest_y) ** 2) ** 0.5
                    
                    if dist < min_dist:
                        min_dist = dist
                        best_point_x = closest_x
                        best_point_y = closest_y
                        split_index = i
                
                # Snap the junction point to grid for cleaner layout
                junction_x, junction_y = self.snap_to_grid(best_point_x, best_point_y)
                
                # Create junction at the snapped position
                junction = Junction(junction_x, junction_y)
                self.junctions.append(junction)
                
                # Save state before modifying wires
                self.save_state()
                
                # Split waypoints based on where the junction was placed
                # split_index tells us which segment (0-based) the junction is on
                # The segments are: pin1->wp[0], wp[0]->wp[1], ..., wp[n-1]->pin2
                # If split_index is i, the junction is between all_points[i] and all_points[i+1]
                waypoints_before = []
                waypoints_after = []
                
                if old_waypoints:
                    # The split_index is relative to all_points (which includes endpoints)
                    # We need to convert this to waypoint indices
                    # all_points = [pin1, wp[0], wp[1], ..., wp[n-1], pin2]
                    # split_index=0 means between pin1 and wp[0] (or pin1 and pin2 if no waypoints)
                    # split_index=1 means between wp[0] and wp[1]
                    # etc.
                    
                    # Waypoints before the junction (indices 0 to split_index-1)
                    # split_index=0: no waypoints before (junction right after pin1)
                    # split_index=1: waypoint[0] goes before
                    # split_index=2: waypoints[0,1] go before
                    if split_index > 0:
                        waypoints_before = old_waypoints[:split_index]
                    
                    # Waypoints after the junction (indices split_index onwards)
                    # split_index=0: all waypoints go after
                    # split_index=1: waypoints[1:] go after
                    # split_index=len(waypoints): no waypoints after (junction right before pin2)
                    if split_index < len(old_waypoints):
                        waypoints_after = old_waypoints[split_index:]
                
                # Disconnect and remove the old wire
                clicked_wire.disconnect()
                self.wires.remove(clicked_wire)
                
                # Create two new wires: pin1 -> junction and junction -> pin2
                # Each wire gets only the waypoints on its side of the junction
                wire1 = Wire(old_pin1, junction.pin, waypoints_before)
                wire2 = Wire(junction.pin, old_pin2, waypoints_after)
                self.wires.append(wire1)
                self.wires.append(wire2)
                
                # Complete the wire being drawn to the junction
                self.complete_wire(junction.pin)
                return            
            # Otherwise, add a waypoint
            snapped_x, snapped_y = self.snap_to_grid(x, y)
            self.wire_waypoints.append((snapped_x, snapped_y))
            self.update_wire_preview(x, y)
            return
        
        # Check if clicking on a resize handle of a selected Rectangle (BEFORE component selection)
        from src.components.rectangle import Rectangle
        for component in self.selected_components:
            if isinstance(component, Rectangle):
                handle = self.get_resize_handle_at_position(x, y, component)
                if handle:
                    self.resizing_rectangle = True
                    self.resize_rectangle = component
                    self.resize_handle = handle
                    self.resize_start_pos = (x, y)
                    self.resize_start_size = (component.width, component.height)
                    self.resize_start_rect_pos = (component.x, component.y)
                    self.save_state()  # Save state before resizing
                    # Don't set dragging_component!
                    return
        
        # Check if clicking on a waypoint of a selected wire (before other checks)
        clicked_waypoint_wire, clicked_waypoint_index = self.get_waypoint_at_position(x, y)
        if clicked_waypoint_wire is not None:
            # Start dragging the waypoint
            self.dragging_waypoint = True
            self.dragging_waypoint_wire = clicked_waypoint_wire
            self.dragging_waypoint_index = clicked_waypoint_index
            self.drag_start = (x, y)
            self.save_state()  # Save state before moving waypoint
            return
            
        # Check if clicking on a junction
        clicked_junction = self.get_junction_at_position(x, y)
        if clicked_junction:
            # Store the junction and start a timer for hold detection
            self.junction_clicked = clicked_junction
            self.drag_start = (x, y)
            
            # Check if Ctrl is held for multi-select
            if event.state & 0x4:  # Ctrl key
                if clicked_junction in self.selected_components:
                    # Remove from selection
                    self.selected_components.remove(clicked_junction)
                    clicked_junction.selected = False
                else:
                    # Add to selection
                    self.selected_components.append(clicked_junction)
                    clicked_junction.selected = True
                self.junction_clicked = None  # Don't enable dragging in multi-select
            else:
                # Start a timer - if mouse is still down after 200ms, enable dragging
                self.junction_hold_timer = self.canvas.after(200, self.enable_junction_drag)
            return
        
        # Check if clicking on a component
        clicked_component = self.get_component_at_position(x, y)
        if clicked_component:
            # If this is a selected Rectangle, check if we're clicking a resize handle
            from src.components.rectangle import Rectangle
            if isinstance(clicked_component, Rectangle) and clicked_component.selected:
                handle = self.get_resize_handle_at_position(x, y, clicked_component)
                if handle:
                    # This is handled above, but double-check we don't start dragging
                    return
            
            # Check if component has a handle_click method (e.g., HexKeypad)
            if hasattr(clicked_component, 'handle_click'):
                # Call handle_click and if it returns True, the click was handled
                if clicked_component.handle_click(x, y, self.logic_running):
                    self.update()  # Redraw to show any visual changes
                    return
            
            # Check if Ctrl is held for multi-select
            if event.state & 0x4:  # Ctrl key
                if clicked_component in self.selected_components:
                    # Remove from selection
                    self.selected_components.remove(clicked_component)
                    clicked_component.selected = False
                else:
                    # Add to selection
                    self.selected_components.append(clicked_component)
                    clicked_component.selected = True
            else:
                # Single selection (or start dragging selection)
                if clicked_component not in self.selected_components:
                    self.deselect_all()
                    self.select_component(clicked_component)
                # Prepare to drag (either single or multiple)
                # Check if there are selected wires in addition to components
                has_selected_wires = any(wire.selected for wire in self.wires)
                # Use selection drag if multiple components OR if there are selected wires
                if len(self.selected_components) > 1 or has_selected_wires:
                    self.dragging_component = None
                    self.dragging_selection = True
                else:
                    self.dragging_component = clicked_component
                    self.dragging_selection = False
            self.drag_start = (x, y)
            if self.dragging_component or self.dragging_selection:
                self.save_state()  # Save state before moving components
            return
            
        # Check if clicking on a wire
        clicked_wire = self.get_wire_at_position(x, y)
        if clicked_wire:
            self.select_wire(clicked_wire)
            return
            
        # Clicked on empty space - start selection rectangle
        self.deselect_all()
        self.selection_rect_start = (x, y)
    
    def on_double_click(self, event):
        """Handle double-click to toggle component state, edit name, or start/end wiring"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        x, y = self.unapply_zoom_coords(x, y)
        
        # First check if we double-clicked on a pin or junction
        pin = self.get_pin_at_position(x, y)
        if pin:
            # Check if we're in wiring mode
            if self.wiring_mode:
                # Complete wire connection
                self.complete_wire(pin)
                return
            
            # Start wiring from this pin/junction
            self.start_wiring(pin)
            return
        
        # Check if double-clicking on a component body
        clicked_component = self.get_component_at_position(x, y)
        if clicked_component:
            # Check if component has its own double-click handler
            if hasattr(clicked_component, 'on_double_click'):
                clicked_component.on_double_click()
                return
            
            # Check if it's a Label component - edit text directly
            if hasattr(clicked_component, 'type') and clicked_component.type == "Label":
                self.edit_label_text(clicked_component)
                return
            
            # Memory component: open viewer window
            if isinstance(clicked_component, Memory):
                clicked_component.open_memory_viewer(self.canvas.winfo_toplevel())
                return
            
            # Check if component has a toggle method
            if hasattr(clicked_component, 'toggle'):
                # Only allow toggling if logic is running (not in STOP mode)
                if self.logic_running:
                    clicked_component.toggle()
                    self.update()
                return
        
        # Check all components to see if we clicked on their label area
        for component in self.components:
            # Check if clicking on the label area (below the component)
            label_y = component.y + component.height/2
            label_x_start = component.x - component.width/2
            label_x_end = component.x + component.width/2
            
            if (x >= label_x_start and x <= label_x_end and 
                y >= label_y and y <= label_y + 20):
                # Double-clicked on label - edit name
                self.edit_component_name(component)
                return
        
    def on_drag(self, event):
        """Handle mouse drag"""
        try:
            self._on_drag_impl(event)
        except Exception as e:
            print(f"❌ ERROR in on_drag: {e}")
            traceback.print_exc()
    
    def _on_drag_impl(self, event):
        """Handle mouse drag - implementation"""
        # If panning (both buttons down), handle pan drag
        if self.panning and self.pan_start:
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        x, y = self.unapply_zoom_coords(x, y)
        
        if self.resizing_rectangle and self.resize_rectangle and self.resize_start_pos:
            # Resize the rectangle
            dx = x - self.resize_start_pos[0]
            dy = y - self.resize_start_pos[1]
            start_w, start_h = self.resize_start_size
            start_x, start_y = self.resize_start_rect_pos
            
            # Calculate new size and position based on handle type
            # Rectangle is centered at (x, y), so when we resize:
            # - East/South: increase size and move center right/down by half the increase
            # - West/North: increase size and move center left/up by half the increase
            handle = self.resize_handle
            new_w, new_h = start_w, start_h
            new_x, new_y = start_x, start_y
            
            if 'e' in handle:  # East: expand right
                new_w = max(20, start_w + dx)
                new_x = start_x + (new_w - start_w) / 2
            elif 'w' in handle:  # West: expand left
                new_w = max(20, start_w - dx)
                new_x = start_x - (new_w - start_w) / 2
                
            if 's' in handle:  # South: expand down
                new_h = max(20, start_h + dy)
                new_y = start_y + (new_h - start_h) / 2
            elif 'n' in handle:  # North: expand up
                new_h = max(20, start_h - dy)
                new_y = start_y - (new_h - start_h) / 2
            
            # Update rectangle size and position
            self.resize_rectangle.width = new_w
            self.resize_rectangle.height = new_h
            self.resize_rectangle.x = new_x
            self.resize_rectangle.y = new_y
            
            # Update properties dict so undo/redo works correctly
            self.resize_rectangle.properties["width"] = new_w
            self.resize_rectangle.properties["height"] = new_h
            
        elif self.dragging_waypoint and self.drag_start:
            # Move the waypoint
            snapped_x, snapped_y = self.snap_to_grid(x, y)
            self.dragging_waypoint_wire.waypoints[self.dragging_waypoint_index] = (snapped_x, snapped_y)
            self.drag_start = (x, y)
            
        elif self.wiring_mode:
            # Update temporary wire routing preview
            self.update_wire_preview(x, y)
            
        elif self.selection_rect_start:
            # Draw selection rectangle - convert logical coords to canvas coords for drawing
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
            x1, y1 = self.selection_rect_start
            # Convert both points to canvas (zoomed) coordinates
            zx1, zy1 = self.apply_zoom_coords(x1, y1)
            zx2, zy2 = self.apply_zoom_coords(x, y)
            self.selection_rect = self.canvas.create_rectangle(
                zx1, zy1, zx2, zy2, outline='blue', dash=(4, 4), width=2, tags='selection_rect'
            )
            
        elif self.dragging_selection and self.drag_start:
            # Move all selected components
            dx = x - self.drag_start[0]
            dy = y - self.drag_start[1]
            for component in self.selected_components:
                component.move_to(component.x + dx, component.y + dy)
            
            # Move waypoints of selected wires
            for wire in self.wires:
                if wire.selected:
                    # Move each waypoint by the delta
                    wire.waypoints = [(wx + dx, wy + dy) for wx, wy in wire.waypoints]
            
            self.drag_start = (x, y)
            
        elif self.dragging_component and self.drag_start:
            # Move single component smoothly (no snapping during drag)
            dx = x - self.drag_start[0]
            dy = y - self.drag_start[1]
            
            self.dragging_component.move_to(
                self.dragging_component.x + dx,
                self.dragging_component.y + dy
            )
            self.drag_start = (x, y)
            
    def draw_components_immediate(self):
        """Immediately redraw components during drag"""
        # Just update component positions without full redraw
        pass
            
    def on_release(self, event):
        """Handle mouse release"""
        try:
            self._on_release_impl(event)
        except Exception as e:
            print(f"❌ ERROR in on_release: {e}")
            traceback.print_exc()
    
    def _on_release_impl(self, event):
        """Handle mouse release - implementation"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        x, y = self.unapply_zoom_coords(x, y)
        
        # Complete rectangle resize
        if self.resizing_rectangle:
            self.resizing_rectangle = False
            # Refresh properties panel to show updated width/height
            if self.resize_rectangle and self.properties_panel and self.resize_rectangle in self.selected_components:
                self.properties_panel.show_component_properties(self.resize_rectangle)
            self.resize_rectangle = None
            self.resize_handle = None
            self.resize_start_pos = None
            self.resize_start_size = None
            self.resize_start_rect_pos = None
        
        # Complete selection rectangle
        if self.selection_rect_start:
            x1, y1 = self.selection_rect_start
            x2, y2 = x, y
            
            # Select all components, junctions, and wires within rectangle
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_y, max_y = min(y1, y2), max(y1, y2)
            
            for component in self.components:
                if (min_x <= component.x <= max_x and min_y <= component.y <= max_y):
                    self.selected_components.append(component)
                    component.selected = True
            
            for junction in self.junctions:
                if (min_x <= junction.x <= max_x and min_y <= junction.y <= max_y):
                    self.selected_components.append(junction)
                    junction.selected = True
            
            # Select wires that have any waypoints or endpoints within the rectangle
            for wire in self.wires:
                wire_in_rect = False
                
                # Check wire endpoints
                p1 = wire.pin1.get_position()
                p2 = wire.pin2.get_position()
                if ((min_x <= p1[0] <= max_x and min_y <= p1[1] <= max_y) or
                    (min_x <= p2[0] <= max_x and min_y <= p2[1] <= max_y)):
                    wire_in_rect = True
                
                # Check waypoints
                for wx, wy in wire.waypoints:
                    if (min_x <= wx <= max_x and min_y <= wy <= max_y):
                        wire_in_rect = True
                        break
                
                if wire_in_rect:
                    wire.selected = True
            
            # Clean up selection rectangle
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
                self.selection_rect = None
            self.selection_rect_start = None
            return
        
        # Reset waypoint dragging
        if self.dragging_waypoint:
            self.dragging_waypoint = False
            self.dragging_waypoint_wire = None
            self.dragging_waypoint_index = None
            self.drag_start = None
            return
        
        # Clean up junction hold state
        if self.junction_hold_timer:
            self.canvas.after_cancel(self.junction_hold_timer)
            self.junction_hold_timer = None
        self.junction_clicked = None
        self.junction_hold_active = False
        
        # Snap component(s) to grid when released
        if self.dragging_selection:
            # Find the first component to determine snap offset
            if self.selected_components:
                first_comp = self.selected_components[0]
                snapped_x, snapped_y = self.snap_to_grid(first_comp.x, first_comp.y)
                
                # Calculate the offset needed to snap to grid
                snap_dx = snapped_x - first_comp.x
                snap_dy = snapped_y - first_comp.y
                
                # Apply the same offset to all selected components
                for component in self.selected_components:
                    component.move_to(component.x + snap_dx, component.y + snap_dy)
                
                # Apply the same offset to waypoints of selected wires
                for wire in self.wires:
                    if wire.selected:
                        wire.waypoints = [(wx + snap_dx, wy + snap_dy) for wx, wy in wire.waypoints]
            
            self.dragging_selection = False
        elif self.dragging_component:
            snapped_x, snapped_y = self.snap_to_grid(
                self.dragging_component.x,
                self.dragging_component.y
            )
            self.dragging_component.move_to(snapped_x, snapped_y)
        
        self.dragging_component = None
        self.drag_start = None
    
    def on_left_press(self, event):
        """Handle left mouse button press"""
        self.left_button_down = True
        
        # If both buttons are now down, start panning
        if self.right_button_down:
            self.start_panning(event)
        else:
            # Normal click handling
            self.on_click(event)
    
    def on_right_press(self, event):
        """Handle right mouse button press"""
        self.right_button_down = True
        
        # If both buttons are now down, start panning
        if self.left_button_down:
            self.start_panning(event)
    
    def on_right_double_click(self, event):
        """Handle right mouse button double-click - show context menu"""
        # Cancel any pending single-click action
        if self.pending_right_click:
            self.canvas.after_cancel(self.pending_right_click)
            self.pending_right_click = None
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        x, y = self.unapply_zoom_coords(x, y)
        
        self.context_menu_x = x
        self.context_menu_y = y
        
        # Show context menu everywhere (no need to check for blank canvas)
        self.show_context_menu(event)
    
    def on_left_release(self, event):
        """Handle left mouse button release"""
        self.left_button_down = False
        
        # If panning, stop it
        if self.panning:
            self.stop_panning()
        else:
            # Normal release handling
            self.on_release(event)
    
    def on_right_release(self, event):
        """Handle right mouse button release"""
        self.right_button_down = False
        
        # If panning, stop it
        if self.panning:
            self.stop_panning()
    
    def start_panning(self, event):
        """Start panning mode"""
        # Cancel any ongoing operations
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
            self.selection_rect_start = None
        
        self.panning = True
        self.pan_start = (event.x, event.y)
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.config(cursor='fleur')  # Four-way arrow cursor
    
    def stop_panning(self):
        """Stop panning mode"""
        self.panning = False
        self.pan_start = None
        # Restore appropriate cursor based on mode
        if self.wiring_mode:
            self.canvas.config(cursor='tcross')
        else:
            self.canvas.config(cursor='crosshair')
    
    def show_context_menu(self, event):
        """Show context menu at cursor position"""
        import tkinter as tk
        
        # Create context menu if it doesn't exist
        if self.context_menu is None:
            self.context_menu = tk.Menu(self.canvas, tearoff=0)
            self.context_menu.add_command(label="Cut", command=self.cut_selected)
            self.context_menu.add_command(label="Copy", command=self.copy_selected)
            self.context_menu.add_command(label="Paste", command=lambda: self.paste(self.context_menu_x, self.context_menu_y))
        
        # Show the menu at cursor position
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
            
    def on_motion(self, event):
        """Handle mouse motion"""
        # Don't change cursor while panning
        if self.panning:
            return
        
        # Show hand cursor when actively dragging
        if self.dragging_component or self.dragging_selection or self.dragging_waypoint or self.resizing_rectangle:
            if self.canvas.cget('cursor') != 'hand2':
                self.canvas.config(cursor='hand2')
            return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        x, y = self.unapply_zoom_coords(x, y)
        
        # Track mouse position for paste operation
        self.last_mouse_x = x
        self.last_mouse_y = y
        
        # Update wire preview if in wiring mode
        if self.wiring_mode:
            self.update_wire_preview(x, y)
        
        # Change cursor based on what's under the mouse
        # Check for resize handles on selected rectangles first
        from src.components.rectangle import Rectangle
        resize_handle = None
        for component in self.selected_components:
            if isinstance(component, Rectangle):
                resize_handle = self.get_resize_handle_at_position(x, y, component)
                if resize_handle:
                    # Set cursor based on handle direction
                    # Using cross-platform compatible cursor names
                    if resize_handle in ['nw', 'se']:
                        # Diagonal NW-SE
                        cursor = 'size_nw_se'
                    elif resize_handle in ['ne', 'sw']:
                        # Diagonal NE-SW
                        cursor = 'size_ne_sw'
                    elif resize_handle in ['n', 's']:
                        # Vertical
                        cursor = 'sb_v_double_arrow'
                    elif resize_handle in ['e', 'w']:
                        # Horizontal
                        cursor = 'sb_h_double_arrow'
                    else:
                        cursor = 'sizing'
                    
                    self.canvas.config(cursor=cursor)
                    return
        
        # Default cursor logic
        pin = self.get_pin_at_position(x, y)
        junction = self.get_junction_at_position(x, y)
        
        new_cursor = None
        # Show wiring cursor for all pins (including junctions)
        if pin:
            new_cursor = 'circle'
        elif self.get_component_at_position(x, y):
            new_cursor = 'hand2'
        elif self.get_wire_at_position(x, y):
            new_cursor = 'tcross'
        else:
            new_cursor = 'crosshair'
        
        current_cursor = self.canvas.cget('cursor')
        if new_cursor != current_cursor:
            self.canvas.config(cursor=new_cursor)
    
    def on_mousewheel(self, event):
        """Handle mouse wheel for zooming"""
        # Determine zoom direction
        if event.num == 5 or event.delta < 0:  # Scroll down / zoom out
            zoom_change = -0.1
        elif event.num == 4 or event.delta > 0:  # Scroll up / zoom in
            zoom_change = 0.1
        else:
            return
        
        # Calculate new zoom level and clamp it
        new_zoom = self.zoom_level + zoom_change
        if new_zoom < 0.3 or new_zoom > 1.5:  # Limit zoom range 30% to 150%
            return
        
        # Apply zoom
        self.zoom_level = new_zoom
        self.update_zoom_display()
        
        # Cancel any pending zoom update
        if hasattr(self, '_zoom_update_id') and self._zoom_update_id:
            self.canvas.after_cancel(self._zoom_update_id)
        
        # Schedule update with a small delay to batch rapid zoom changes
        self._zoom_update_id = self.canvas.after(50, self._perform_zoom_update)
    
    def _perform_zoom_update(self):
        """Perform the actual zoom update (called after delay)"""
        self._zoom_update_id = None
        
        # Update scroll region based on zoom level
        self._update_scroll_region()
        
        # Only redraw visual elements, don't recalculate circuit logic
        self.redraw_visual()
    
    def on_rotate_key(self, event):
        """Handle 'r' key to rotate selected diodes and relays"""
        from src.components.diode import Diode
        from src.components.dpdt_relay import DPDTRelay
        
        # Rotate all selected diodes and DPDT relays
        rotated_any = False
        for component in self.selected_components:
            if isinstance(component, (Diode, DPDTRelay)):
                component.rotate()
                rotated_any = True
        
        # If we rotated anything, update the display
        if rotated_any:
            self.update()
    
    def on_delete_key(self, event):
        """Handle 'd' key to delete selected objects"""
        # Only delete if focus is on canvas, not on an input field
        focused_widget = self.canvas.focus_get()
        if focused_widget and (isinstance(focused_widget, __import__('tkinter').Entry) or 
                               isinstance(focused_widget, __import__('tkinter').Text)):
            # Focus is on a text input widget, don't delete
            return
        self.delete_selected()
        return "break"  # Prevent further propagation
    
    def on_escape_key(self, event):
        """Handle Escape key to cancel wiring mode"""
        if self.wiring_mode:
            self.cancel_wiring()
        return "break"
    
    def on_copy_key(self, event):
        """Handle Ctrl+C to copy selected objects"""
        self.copy_selected()
        return "break"  # Prevent default behavior
    
    def on_cut_key(self, event):
        """Handle Ctrl+X to cut selected objects"""
        self.cut_selected()
        return "break"  # Prevent default behavior
    
    def on_paste_key(self, event):
        """Handle Ctrl+V to paste objects from clipboard"""
        self.paste()
        return "break"  # Prevent default behavior
    
    def on_undo_key(self, event):
        """Handle Ctrl+Z to undo last action"""
        self.undo()
        return "break"  # Prevent default behavior
    
    def on_redo_key(self, event):
        """Handle Ctrl+Y to redo last undone action"""
        self.redo()
        return "break"  # Prevent default behavior
            
    def start_wiring(self, pin):
        """Start wiring mode from a pin"""
        self.wiring_mode = True
        self.wire_start_pin = pin
        self.wire_waypoints = []
        self.temp_wire_lines = []
    
    def enable_junction_drag(self):
        """Enable dragging for a junction after hold timer expires"""
        if self.junction_clicked:
            junction = self.junction_clicked
            self.junction_hold_active = True
            
            # Select the junction if not already selected
            if junction not in self.selected_components:
                self.deselect_all()
                self.selected_components.append(junction)
                junction.selected = True
            
            # Set up dragging state
            self.dragging_component = junction if len(self.selected_components) <= 1 else None
            self.dragging_selection = len(self.selected_components) > 1
            self.save_state()  # Save state before moving
        
    def snap_to_grid(self, x, y):
        """Snap coordinates to grid"""
        return (
            round(x / self.grid_size) * self.grid_size,
            round(y / self.grid_size) * self.grid_size
        )
    
    def constrain_to_angle(self, x1, y1, x2, y2):
        """Constrain a line to 90° or 45° angles"""
        dx = x2 - x1
        dy = y2 - y1
        
        if self.wire_angle_mode == 90:
            # Constrain to horizontal or vertical
            if abs(dx) > abs(dy):
                return x2, y1  # Horizontal
            else:
                return x1, y2  # Vertical
        else:  # 45 degree mode
            # Constrain to horizontal, vertical, or 45-degree diagonal
            if abs(dx) < 0.1:
                return x1, y2  # Vertical
            if abs(dy) < 0.1:
                return x2, y1  # Horizontal
                
            angle = abs(dy / dx)
            if angle < 0.5:  # More horizontal
                return x2, y1
            elif angle > 2.0:  # More vertical
                return x1, y2
            else:  # 45 degree diagonal
                # Make it exactly 45 degrees
                dist = min(abs(dx), abs(dy))
                return x1 + (dist if dx > 0 else -dist), y1 + (dist if dy > 0 else -dist)
        
    def complete_wire(self, end_pin):
        """Complete a wire connection"""
        if end_pin != self.wire_start_pin:
            # Save state before creating wire
            self.save_state()
            
            # Clear any manual states on the pins being connected
            if hasattr(self.wire_start_pin, 'manual_state'):
                self.wire_start_pin.manual_state = None
            if hasattr(end_pin, 'manual_state'):
                end_pin.manual_state = None
            
            # Create wire with waypoints
            wire = Wire(self.wire_start_pin, end_pin, self.wire_waypoints.copy())
            self.wires.append(wire)
            
        self.cancel_wiring()
        
    def cancel_wiring(self):
        """Cancel wiring mode"""
        self.wiring_mode = False
        for line in self.temp_wire_lines:
            self.canvas.delete(line)
        self.temp_wire_lines = []
        self.wire_start_pin = None
        self.wire_waypoints = []
    
    def toggle_wire_angle_mode(self):
        """Toggle between 90° and 45° wire routing"""
        self.wire_angle_mode = 45 if self.wire_angle_mode == 90 else 90
        print(f"Wire routing mode: {self.wire_angle_mode}°")
        return "break"  # Prevent Tab from changing focus
    
    def update_wire_preview(self, x, y):
        """Update the temporary wire preview while routing"""
        # Clear existing preview lines
        for line in self.temp_wire_lines:
            self.canvas.delete(line)
        self.temp_wire_lines = []
        
        # Build the points for the wire
        points = [self.wire_start_pin.get_position()]
        points.extend(self.wire_waypoints)
        
        # Add current mouse position (snapped and constrained)
        snapped_x, snapped_y = self.snap_to_grid(x, y)
        if len(points) > 0:
            last_x, last_y = points[-1]
            constrained_x, constrained_y = self.constrain_to_angle(last_x, last_y, snapped_x, snapped_y)
            points.append((constrained_x, constrained_y))
        else:
            points.append((snapped_x, snapped_y))
        
        # Draw preview segments with zoom applied
        for i in range(len(points) - 1):
            x1, y1 = self.apply_zoom_coords(points[i][0], points[i][1])
            x2, y2 = self.apply_zoom_coords(points[i+1][0], points[i+1][1])
            line = self.canvas.create_line(x1, y1, x2, y2, fill='blue', 
                                          width=max(2, int(3 * self.zoom_level)), 
                                          dash=(8, 4), tags='temp_wire')
            self.temp_wire_lines.append(line)
        
    def add_component(self, component):
        """Add a component to the canvas"""
        self.save_state()  # Save state before adding component
        
        # Assign name with type-specific counter (duplicates allowed)
        self.assign_unique_name(component)
        
        self.components.append(component)
    
    def assign_unique_name(self, component):
        """Assign a name to a component based on its type"""
        from src.core.component import Component
        
        type_name = component.__class__.__name__
        base_name = component.base_name if hasattr(component, 'base_name') else type_name
        
        # Generate name with suffix
        counter = Component.get_next_type_number(type_name)
        new_name = f"{base_name}_{counter}"
        
        component.name = new_name
        component.properties["name"] = new_name
    
    def ensure_unique_component_name(self, component, proposed_name):
        """Allow any component name (duplicates allowed)"""
        # Simply return the proposed name without checking for uniqueness
        return proposed_name
        
    def get_component_at_position(self, x, y):
        """Get component at position (checks non-Rectangle components first, then Rectangles)"""
        from src.components.rectangle import Rectangle
        
        # First check all non-Rectangle components (in reverse order - top to bottom)
        for component in reversed(self.components):
            if not isinstance(component, Rectangle) and component.contains_point(x, y):
                return component
        
        # Then check Rectangle components (so they don't block other components)
        for component in reversed(self.components):
            if isinstance(component, Rectangle) and component.contains_point(x, y):
                return component
        
        return None
    
    def get_junction_at_position(self, x, y):
        """Get junction at position"""
        for junction in self.junctions:
            if junction.contains_point(x, y):
                return junction
        return None
        
    def get_pin_at_position(self, x, y):
        """Get pin at position (including junction pins)"""
        # Check junctions first (they're smaller and should be easier to click)
        for junction in self.junctions:
            if junction.contains_point(x, y):
                return junction.pin
        
        # Check component pins
        for component in self.components:
            pin = component.get_pin_at_position(x, y)
            if pin:
                return pin
        return None
        
    def get_wire_at_position(self, x, y):
        """Get wire at position"""
        for wire in self.wires:
            if wire.contains_point(x, y):
                return wire
        return None
    
    def _point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        """Calculate the minimum distance from a point to a line segment"""
        # Vector from segment start to point
        dx = x2 - x1
        dy = y2 - y1
        
        # Handle degenerate case (segment is a point)
        if dx == 0 and dy == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        
        # Calculate projection parameter t
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        
        # Find the closest point on the segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Return distance to closest point
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
    
    def get_resize_handle_at_position(self, x, y, rect_comp):
        """Get resize handle at position for a Rectangle component.
        Returns handle name: 'se', 'sw', 'ne', 'nw', 'e', 'w', 'n', 's' or None"""
        from src.components.rectangle import Rectangle
        if not isinstance(rect_comp, Rectangle):
            return None
            
        handle_size = 8  # Size of resize handles
        rx, ry = rect_comp.x, rect_comp.y  # Center position
        rw, rh = rect_comp.width, rect_comp.height
        
        # Corner handles (priority) - rectangle is centered at (rx, ry)
        corners = {
            'nw': (rx - rw/2, ry - rh/2),
            'ne': (rx + rw/2, ry - rh/2),
            'sw': (rx - rw/2, ry + rh/2),
            'se': (rx + rw/2, ry + rh/2)
        }
        for name, (cx, cy) in corners.items():
            if abs(x - cx) <= handle_size and abs(y - cy) <= handle_size:
                return name
        
        # Edge handles
        edges = {
            'n': (rx, ry - rh/2),
            's': (rx, ry + rh/2),
            'w': (rx - rw/2, ry),
            'e': (rx + rw/2, ry)
        }
        for name, (cx, cy) in edges.items():
            if abs(x - cx) <= handle_size and abs(y - cy) <= handle_size:
                return name
                
        return None
    
    def get_waypoint_at_position(self, x, y, tolerance=8):
        """Get waypoint at position - returns (wire, waypoint_index) or (None, None)"""
        for wire in self.wires:
            if wire.selected:  # Only check waypoints on selected wires
                for idx, (wx, wy) in enumerate(wire.waypoints):
                    distance = ((x - wx) ** 2 + (y - wy) ** 2) ** 0.5
                    if distance <= tolerance:
                        return (wire, idx)
        return (None, None)
    
    def is_pin_connected(self, pin):
        """Check if a pin is connected to any wire"""
        for wire in self.wires:
            if wire.pin1 == pin or wire.pin2 == pin:
                return True
        return False
    
    def toggle_pin_state(self, pin):
        """Toggle a pin between HIGH and FLOAT"""
        if not hasattr(pin, 'manual_state'):
            pin.manual_state = None
        
        if pin.manual_state == 'HIGH':
            # Switch to FLOAT
            pin.manual_state = None
        else:
            # Switch to HIGH
            pin.manual_state = 'HIGH'
        
    def select_component(self, component):
        """Select a component"""
        self.deselect_all()
        component.selected = True
        self.selected_component = component
        self.selected_components = [component]
        if self.properties_panel:
            self.properties_panel.show_component_properties(component)
            
    def select_wire(self, wire):
        """Select a wire"""
        self.deselect_all()
        wire.selected = True
        self.selected_wire = wire
        
    def deselect_all(self):
        """Deselect all items"""
        for component in self.components:
            component.selected = False
        for junction in self.junctions:
            junction.selected = False
        for wire in self.wires:
            wire.selected = False
        self.selected_component = None
        self.selected_components = []
        self.selected_wire = None
    
    def edit_component_name(self, component):
        """Open a dialog to edit component name"""
        from tkinter import simpledialog
        new_name = simpledialog.askstring("Edit Name", 
                                          "Enter new name:", 
                                          initialvalue=component.name)
        if new_name:
            component.name = new_name
            component.properties["name"] = new_name
            self.update()
            # Update properties panel if it's showing this component
            if self.properties_panel and component in self.selected_components:
                self.properties_panel.show_component_properties(component)
        if self.properties_panel:
            self.properties_panel.clear()
    
    def edit_label_text(self, label):
        """Open a dialog to edit label text"""
        from tkinter import simpledialog
        current_text = label.properties.get("Text", "Label")
        new_text = simpledialog.askstring("Edit Label", 
                                          "Enter label text:", 
                                          initialvalue=current_text)
        if new_text is not None:  # Allow empty string
            label.set_property("Text", new_text)
            self.update()
            # Update properties panel if it's showing this label
            if self.properties_panel and label in self.selected_components:
                self.properties_panel.show_component_properties(label)
            
    def delete_selected(self):
        """Delete selected component(s), junction(s), or wire"""
        # Save state before deleting
        self.save_state()
        
        # Delete multiple selected components/junctions
        if self.selected_components:
            for item in self.selected_components[:]:  # Copy list to avoid modification during iteration
                # Check if it's a junction
                if item in self.junctions:
                    # Remove all wires connected to this junction
                    wires_to_remove = []
                    for wire in self.wires:
                        if wire.pin1 == item.pin or wire.pin2 == item.pin:
                            wire.disconnect()
                            wires_to_remove.append(wire)
                    for wire in wires_to_remove:
                        self.wires.remove(wire)
                    self.junctions.remove(item)
                else:
                    # It's a component
                    wires_to_remove = []
                    for wire in self.wires:
                        if wire.pin1.component == item or wire.pin2.component == item:
                            wire.disconnect()
                            wires_to_remove.append(wire)
                    for wire in wires_to_remove:
                        self.wires.remove(wire)
                    self.components.remove(item)
            
            self.selected_components = []
            self.selected_component = None
            
        elif self.selected_component:
            # Remove all wires connected to this component
            wires_to_remove = []
            for wire in self.wires:
                if wire.pin1.component == self.selected_component or wire.pin2.component == self.selected_component:
                    wire.disconnect()
                    wires_to_remove.append(wire)
            for wire in wires_to_remove:
                self.wires.remove(wire)
                
            self.components.remove(self.selected_component)
            self.selected_component = None
            
        elif self.selected_wire:
            self.selected_wire.disconnect()
            self.wires.remove(self.selected_wire)
            self.selected_wire = None
            
        if self.properties_panel:
            self.properties_panel.clear()
            
    def copy_selected(self):
        """Copy selected components and wires to clipboard"""
        if not self.selected_components:
            return
        
        self.clipboard_components = []
        self.clipboard_junctions = []
        self.clipboard_wires = []
        self.clipboard_is_cut = False
        self.clipboard_source_page = self.current_page
        
        # Build sets of selected component IDs and LIST of selected junctions (order matters!)
        selected_comp_ids = set()
        selected_junctions = []  # Use list instead of set to maintain order
        
        for item in self.selected_components:
            if item in self.junctions:
                if item not in selected_junctions:  # Avoid duplicates
                    selected_junctions.append(item)
            else:
                selected_comp_ids.add(item.id)
        
        # Copy component data
        for item in self.selected_components:
            if item in self.junctions:
                # Copy junction
                junction_dict = {
                    'x': item.x,
                    'y': item.y
                }
                self.clipboard_junctions.append(junction_dict)
            else:
                # Copy component
                comp_dict = item.to_dict()
                self.clipboard_components.append(comp_dict)
        
        # Save manual pin states for selected components
        selected_components_only = [item for item in self.selected_components if item not in self.junctions]
        self.clipboard_manual_pin_states = self._save_manual_pin_states(selected_components_only)
        
        # Copy wires that connect selected items OR are explicitly selected
        for wire in self.wires:
            # First check if wire is explicitly selected (e.g., via selection rectangle)
            if wire.selected:
                # Need to determine pin types and IDs for this selected wire
                pin1_type = None
                pin1_id = None
                pin2_type = None
                pin2_id = None
                
                # Determine pin1 info
                if hasattr(wire.pin1, 'junction'):
                    pin1_type = 'junction'
                    if wire.pin1.junction in selected_junctions:
                        pin1_id = selected_junctions.index(wire.pin1.junction)
                    else:
                        # Junction not in selection - we need to add it
                        selected_junctions.append(wire.pin1.junction)
                        pin1_id = len(selected_junctions) - 1
                        # Also add junction data to clipboard
                        junction_dict = {
                            'x': wire.pin1.junction.x,
                            'y': wire.pin1.junction.y
                        }
                        self.clipboard_junctions.append(junction_dict)
                elif hasattr(wire.pin1, 'component'):
                    pin1_type = 'component'
                    pin1_id = wire.pin1.component.id
                    if wire.pin1.component.id not in selected_comp_ids:
                        # Component not in selection - add it
                        selected_comp_ids.add(wire.pin1.component.id)
                        comp_dict = wire.pin1.component.to_dict()
                        self.clipboard_components.append(comp_dict)
                
                # Determine pin2 info
                if hasattr(wire.pin2, 'junction'):
                    pin2_type = 'junction'
                    if wire.pin2.junction in selected_junctions:
                        pin2_id = selected_junctions.index(wire.pin2.junction)
                    else:
                        # Junction not in selection - we need to add it
                        selected_junctions.append(wire.pin2.junction)
                        pin2_id = len(selected_junctions) - 1
                        # Also add junction data to clipboard
                        junction_dict = {
                            'x': wire.pin2.junction.x,
                            'y': wire.pin2.junction.y
                        }
                        self.clipboard_junctions.append(junction_dict)
                elif hasattr(wire.pin2, 'component'):
                    pin2_type = 'component'
                    pin2_id = wire.pin2.component.id
                    if wire.pin2.component.id not in selected_comp_ids:
                        # Component not in selection - add it
                        selected_comp_ids.add(wire.pin2.component.id)
                        comp_dict = wire.pin2.component.to_dict()
                        self.clipboard_components.append(comp_dict)
                
                # Create wire data
                wire_data = {
                    "pin1_type": pin1_type,
                    "pin1_id": pin1_id,
                    "pin2_type": pin2_type,
                    "pin2_id": pin2_id,
                    "waypoints": wire.waypoints.copy()
                }
                
                # Add pin names for component pins
                if pin1_type == 'component':
                    wire_data["pin1_name"] = wire.pin1.name
                if pin2_type == 'component':
                    wire_data["pin2_name"] = wire.pin2.name
                
                self.clipboard_wires.append(wire_data)
                continue  # Skip the endpoint check below
            
            # If wire not explicitly selected, check if both endpoints are in selection
            pin1_valid = False
            pin2_valid = False
            pin1_comp_id = None
            pin2_comp_id = None
            pin1_junction_idx = None
            pin2_junction_idx = None
            
            # Check pin1
            if hasattr(wire.pin1, 'junction'):
                # This is a junction pin
                if wire.pin1.junction in selected_junctions:
                    pin1_valid = True
                    pin1_junction_idx = selected_junctions.index(wire.pin1.junction)  # Now uses list.index()
            elif hasattr(wire.pin1, 'component') and hasattr(wire.pin1.component, 'id'):
                # This is a component pin
                if wire.pin1.component.id in selected_comp_ids:
                    pin1_valid = True
                    pin1_comp_id = wire.pin1.component.id
            
            # Check pin2
            if hasattr(wire.pin2, 'junction'):
                # This is a junction pin
                if wire.pin2.junction in selected_junctions:
                    pin2_valid = True
                    pin2_junction_idx = selected_junctions.index(wire.pin2.junction)  # Now uses list.index()
            elif hasattr(wire.pin2, 'component') and hasattr(wire.pin2.component, 'id'):
                # This is a component pin
                if wire.pin2.component.id in selected_comp_ids:
                    pin2_valid = True
                    pin2_comp_id = wire.pin2.component.id
            
            # Only copy wire if both endpoints are in the selection
            if pin1_valid and pin2_valid:
                wire_data = {
                    "pin1_type": "junction" if pin1_junction_idx is not None else "component",
                    "pin1_id": pin1_junction_idx if pin1_junction_idx is not None else pin1_comp_id,
                    "pin2_type": "junction" if pin2_junction_idx is not None else "component",
                    "pin2_id": pin2_junction_idx if pin2_junction_idx is not None else pin2_comp_id,
                    "waypoints": wire.waypoints.copy()
                }
                
                # Add pin names for component pins
                if pin1_junction_idx is None:
                    wire_data["pin1_name"] = wire.pin1.name
                if pin2_junction_idx is None:
                    wire_data["pin2_name"] = wire.pin2.name
                
                self.clipboard_wires.append(wire_data)
    
    def cut_selected(self):
        """Cut selected components and wires to clipboard"""
        if not self.selected_components:
            return
        
        # First copy the selection
        self.copy_selected()
        
        # Mark as cut operation
        self.clipboard_is_cut = True
        
        # Delete the selected items
        self.delete_selected()
    
    def paste(self, mouse_x=None, mouse_y=None):
        """Paste components and wires from clipboard at mouse position"""
        if not self.clipboard_components and not self.clipboard_junctions:
            return
        
        # Save state before pasting
        self.save_state()
        
        from src.components.toggle_button import ToggleButton
        from src.components.indicator import Indicator
        from src.components.dpdt_relay import DPDTRelay
        from src.components.vcc import VCC
        from src.components.clock import Clock
        from src.components.diode import Diode
        from src.components.link import Link
        from src.components.bus import Bus
        from src.components.label import Label
        from src.components.rectangle import Rectangle
        from src.components.seven_segment import SevenSegment
        from src.components.hex_keypad import HexKeypad
        from src.components.memory import Memory
        from src.core.wire import Wire
        from src.core.junction import Junction
        import copy
        
        # Create class name to class mapping (same as load_project)
        class_library = {
            "ToggleButton": ToggleButton,
            "Indicator": Indicator,
            "DPDTRelay": DPDTRelay,
            "VCC": VCC,
            "Clock": Clock,
            "Diode": Diode,
            "Link": Link,
            "Bus": Bus,
            "Label": Label,
            "Rectangle": Rectangle,
            "SevenSegment": SevenSegment,
            "HexKeypad": HexKeypad,
            "Memory": Memory
        }
        
        # Calculate offset for pasted components
        # Find the center of the clipboard contents
        all_x = [comp['x'] for comp in self.clipboard_components] + [j['x'] for j in self.clipboard_junctions]
        all_y = [comp['y'] for comp in self.clipboard_components] + [j['y'] for j in self.clipboard_junctions]
        
        if all_x and all_y:
            clipboard_center_x = (min(all_x) + max(all_x)) / 2
            clipboard_center_y = (min(all_y) + max(all_y)) / 2
        else:
            clipboard_center_x = 0
            clipboard_center_y = 0
        
        # Use mouse position if provided, otherwise use last known mouse position
        if mouse_x is None:
            mouse_x = self.last_mouse_x
        if mouse_y is None:
            mouse_y = self.last_mouse_y
        
        # Snap mouse position to grid
        mouse_x, mouse_y = self.snap_to_grid(mouse_x, mouse_y)
        
        # Calculate offset to place clipboard center at mouse position
        offset_x = mouse_x - clipboard_center_x
        offset_y = mouse_y - clipboard_center_y
        
        # If it's a cut operation from the same page, don't offset
        if self.clipboard_is_cut and self.clipboard_source_page == self.current_page:
            offset_x = 0
            offset_y = 0
        
        # Map old IDs to new components and junctions
        id_map = {}
        junction_map = {}
        new_components = []
        new_junctions = []
        new_wires = []  # Track newly created wires so we can select them after clearing previous selection
        
        # Create junctions first
        for i, junction_data in enumerate(self.clipboard_junctions):
            new_x = junction_data['x'] + offset_x
            new_y = junction_data['y'] + offset_y
            new_junction = Junction(new_x, new_y)
            self.junctions.append(new_junction)
            new_junctions.append(new_junction)
            junction_map[i] = new_junction
        
        # Create components
        for comp_data in self.clipboard_components:
            comp_type = comp_data.get('type')
            if comp_type in class_library:
                old_id = comp_data['id']
                
                # Calculate new position with offset
                new_x = comp_data['x'] + offset_x
                new_y = comp_data['y'] + offset_y
                
                # Create component with x, y parameters
                new_comp = class_library[comp_type](new_x, new_y)
                
                # For cut from different page, keep the same ID
                if self.clipboard_is_cut and self.clipboard_source_page != self.current_page:
                    new_comp.id = old_id
                # Otherwise new ID is auto-generated
                
                # Restore properties if available
                if 'properties' in comp_data:
                    new_comp.properties = copy.deepcopy(comp_data['properties'])
                    # Apply properties to component attributes
                    for key, value in new_comp.properties.items():
                        if hasattr(new_comp, key):
                            setattr(new_comp, key, value)
                    
                    # For components with transformation (rotation/flip), update pin positions
                    if hasattr(new_comp, 'update_pin_positions'):
                        new_comp.update_pin_positions()
                
                # Assign unique name to pasted component (not for cut from same page)
                if not (self.clipboard_is_cut and self.clipboard_source_page == self.current_page):
                    self.assign_unique_name(new_comp)
                
                self.components.append(new_comp)
                new_components.append(new_comp)
                id_map[old_id] = new_comp
        
        # Restore manual pin states using the id_map to translate old IDs to new components
        if self.clipboard_manual_pin_states:
            remapped_states = {}
            for old_id_str, pin_states in self.clipboard_manual_pin_states.items():
                old_id = int(old_id_str)
                if old_id in id_map:
                    new_comp = id_map[old_id]
                    remapped_states[str(new_comp.id)] = pin_states
            
            if remapped_states:
                self._load_manual_pin_states(new_components, remapped_states)
        
        # Create wires between pasted components and junctions
        for wire_data in self.clipboard_wires:
            pin1 = None
            pin2 = None
            
            # Get pin1
            if wire_data['pin1_type'] == 'junction':
                junction_idx = wire_data['pin1_id']
                if junction_idx in junction_map:
                    pin1 = junction_map[junction_idx].pin
            else:  # component
                comp_id = wire_data['pin1_id']
                if comp_id in id_map:
                    pin1 = id_map[comp_id].get_pin(wire_data['pin1_name'])
            
            # Get pin2
            if wire_data['pin2_type'] == 'junction':
                junction_idx = wire_data['pin2_id']
                if junction_idx in junction_map:
                    pin2 = junction_map[junction_idx].pin
            else:  # component
                comp_id = wire_data['pin2_id']
                if comp_id in id_map:
                    pin2 = id_map[comp_id].get_pin(wire_data['pin2_name'])
            
            # Create wire if both pins found
            if pin1 and pin2:
                # Offset waypoints
                waypoints = [(wx + offset_x, wy + offset_y) for wx, wy in wire_data['waypoints']]
                wire = Wire(pin1, pin2, waypoints)
                self.wires.append(wire)
                new_wires.append(wire)
        
        # Preserve selection of newly pasted items: clear previous selection then add all components, junctions, and wires
        self.deselect_all()  # Clear any previous selection
        self.selected_components = new_components + new_junctions
        for comp in new_components:
            comp.selected = True
        for junction in new_junctions:
            junction.selected = True
        # Mark wires selected and also store them in selected_components to unify selection handling for movement
        for wire in new_wires:
            wire.selected = True
        
        # Clear clipboard if it was a cut operation
        if self.clipboard_is_cut:
            self.clipboard_components = []
            self.clipboard_junctions = []
            self.clipboard_wires = []
            self.clipboard_manual_pin_states = {}
            self.clipboard_is_cut = False
            self.clipboard_source_page = None
    
    def save_state(self):
        """Save current state for undo/redo"""
        import copy
        
        # Serialize the current state
        state = {
            'components': [],
            'wires': [],
            'junctions': [],
            'page': self.current_page
        }
        
        # Save component data
        for comp in self.components:
            comp_data = {
                'type': comp.__class__.__name__,
                'x': comp.x,
                'y': comp.y,
                'properties': copy.deepcopy(comp.properties),
                'comp_id': comp.id  # Use component's ID, not Python's id()
            }
            state['components'].append(comp_data)
        
        # Save junction data (assign temporary IDs to junctions)
        for idx, junction in enumerate(self.junctions):
            junction_data = {
                'x': junction.x,
                'y': junction.y,
                'junction_id': idx  # Use index as temporary ID
            }
            state['junctions'].append(junction_data)
        
        # Save wire data
        for wire in self.wires:
            # Check if pins belong to junctions or components
            if hasattr(wire.pin1, 'junction'):
                pin1_type = 'junction'
                pin1_id = self.junctions.index(wire.pin1.junction)
            else:
                pin1_type = 'component'
                pin1_id = wire.pin1.component.id
            
            if hasattr(wire.pin2, 'junction'):
                pin2_type = 'junction'
                pin2_id = self.junctions.index(wire.pin2.junction)
            else:
                pin2_type = 'component'
                pin2_id = wire.pin2.component.id
            
            wire_data = {
                'pin1_type': pin1_type,
                'pin1_id': pin1_id,
                'pin1_name': wire.pin1.name,
                'pin2_type': pin2_type,
                'pin2_id': pin2_id,
                'pin2_name': wire.pin2.name,
                'waypoints': [(x, y) for x, y in wire.waypoints]
            }
            state['wires'].append(wire_data)
        
        # Add to undo stack
        self.undo_stack.append(state)
        
        # Limit stack size
        if len(self.undo_stack) > self.max_undo_levels:
            self.undo_stack.pop(0)
        
        # Clear redo stack when new action is performed
        self.redo_stack.clear()
    
    def undo(self):
        """Undo the last action"""
        if not self.undo_stack:
            print("Nothing to undo")
            return
        
        print("\n========== BEFORE UNDO ==========")
        print(f"Number of wires: {len(self.wires)}")
        for i, wire in enumerate(self.wires):
            p1 = wire.pin1.get_position()
            p2 = wire.pin2.get_position()
            print(f"Wire {i}: ({p1[0]:.1f},{p1[1]:.1f}) -> ({p2[0]:.1f},{p2[1]:.1f}), waypoints: {wire.waypoints}")
        
        # Save current state to redo stack before undoing
        current_state = self._get_current_state()
        self.redo_stack.append(current_state)
        
        # Pop the last state from undo stack
        state = self.undo_stack.pop()
        
        # Restore the state
        self._restore_state(state)
        
        print("\n========== AFTER UNDO ==========")
        print(f"Number of wires: {len(self.wires)}")
        for i, wire in enumerate(self.wires):
            p1 = wire.pin1.get_position()
            p2 = wire.pin2.get_position()
            print(f"Wire {i}: ({p1[0]:.1f},{p1[1]:.1f}) -> ({p2[0]:.1f},{p2[1]:.1f}), waypoints: {wire.waypoints}")
        print("===================================\n")
        
    def redo(self):
        """Redo the last undone action"""
        if not self.redo_stack:
            print("Nothing to redo")
            return
        
        # Save current state to undo stack before redoing
        current_state = self._get_current_state()
        self.undo_stack.append(current_state)
        
        # Pop the last state from redo stack
        state = self.redo_stack.pop()
        
        # Restore the state
        self._restore_state(state)
    
    def _get_current_state(self):
        """Get the current canvas state"""
        import copy
        
        state = {
            'components': [],
            'wires': [],
            'junctions': [],
            'page': self.current_page
        }
        
        for comp in self.components:
            comp_data = {
                'type': comp.__class__.__name__,
                'x': comp.x,
                'y': comp.y,
                'properties': copy.deepcopy(comp.properties),
                'comp_id': comp.id  # Use component's ID, not Python's id()
            }
            state['components'].append(comp_data)
        
        # Save junction data
        for idx, junction in enumerate(self.junctions):
            junction_data = {
                'x': junction.x,
                'y': junction.y,
                'junction_id': idx
            }
            state['junctions'].append(junction_data)
        
        # Save wire data
        for wire in self.wires:
            # Check if pins belong to junctions or components
            if hasattr(wire.pin1, 'junction'):
                pin1_type = 'junction'
                pin1_id = self.junctions.index(wire.pin1.junction)
            else:
                pin1_type = 'component'
                pin1_id = wire.pin1.component.id
            
            if hasattr(wire.pin2, 'junction'):
                pin2_type = 'junction'
                pin2_id = self.junctions.index(wire.pin2.junction)
            else:
                pin2_type = 'component'
                pin2_id = wire.pin2.component.id
            
            wire_data = {
                'pin1_type': pin1_type,
                'pin1_id': pin1_id,
                'pin1_name': wire.pin1.name,
                'pin2_type': pin2_type,
                'pin2_id': pin2_id,
                'pin2_name': wire.pin2.name,
                'waypoints': [(x, y) for x, y in wire.waypoints]
            }
            state['wires'].append(wire_data)
        
        return state
    
    def _restore_state(self, state):
        """Restore canvas to a saved state"""
        import copy
        from src.components.toggle_button import ToggleButton
        from src.components.indicator import Indicator
        from src.components.dpdt_relay import DPDTRelay
        from src.components.vcc import VCC
        from src.components.clock import Clock
        from src.components.diode import Diode
        from src.components.link import Link
        from src.components.bus import Bus
        from src.components.label import Label
        from src.components.rectangle import Rectangle
        from src.components.seven_segment import SevenSegment
        from src.components.hex_keypad import HexKeypad
        from src.components.memory import Memory
        from src.core.wire import Wire
        
        # Class library for creating components by type name
        class_library = {
            'ToggleButton': ToggleButton,
            'Indicator': Indicator,
            'DPDTRelay': DPDTRelay,
            'VCC': VCC,
            'Clock': Clock,
            'Diode': Diode,
            'Link': Link,
            'Bus': Bus,
            'Label': Label,
            'Rectangle': Rectangle,
            'SevenSegment': SevenSegment,
            'HexKeypad': HexKeypad,
            'Memory': Memory
        }
        
        # Clear current canvas
        self.deselect_all()
        for wire in self.wires:
            wire.disconnect()
        self.wires.clear()
        self.components.clear()
        self.junctions.clear()
        
        # Restore components
        id_map = {}  # Maps component ID to component object
        max_id = 0  # Track the highest component ID
        for comp_data in state['components']:
            comp_type = comp_data['type']
            if comp_type in class_library:
                # Create new component
                new_comp = class_library[comp_type](comp_data['x'], comp_data['y'])
                
                # Restore the original component ID
                new_comp.id = comp_data['comp_id']
                max_id = max(max_id, comp_data['comp_id'])
                
                # Restore properties
                for key, value in comp_data['properties'].items():
                    if hasattr(new_comp, key):
                        setattr(new_comp, key, value)
                new_comp.properties = comp_data['properties']
                
                # For components with transformation (rotation/flip), update pin positions
                if hasattr(new_comp, 'update_pin_positions'):
                    new_comp.update_pin_positions()
                
                self.components.append(new_comp)
                id_map[comp_data['comp_id']] = new_comp  # Use comp_id
        
        # Update the component counter to avoid ID conflicts
        from src.core.component import Component
        Component._id_counter = max(Component._id_counter, max_id)
        
        # Restore junctions
        from src.core.junction import Junction
        junction_map = {}  # Maps junction ID to junction object
        for junction_data in state.get('junctions', []):
            new_junction = Junction(junction_data['x'], junction_data['y'])
            self.junctions.append(new_junction)
            junction_map[junction_data['junction_id']] = new_junction
        
        # Restore wires
        for wire_data in state['wires']:
            # Get pin1
            if wire_data.get('pin1_type') == 'junction':
                junction_id = wire_data['pin1_id']
                if junction_id in junction_map:
                    pin1 = junction_map[junction_id].pin
                else:
                    continue
            else:
                # Legacy format or component pin
                comp_id = wire_data.get('pin1_id') or wire_data.get('pin1_comp_id')
                if comp_id in id_map:
                    pin1 = id_map[comp_id].get_pin(wire_data['pin1_name'])
                else:
                    continue
            
            # Get pin2
            if wire_data.get('pin2_type') == 'junction':
                junction_id = wire_data['pin2_id']
                if junction_id in junction_map:
                    pin2 = junction_map[junction_id].pin
                else:
                    continue
            else:
                # Legacy format or component pin
                comp_id = wire_data.get('pin2_id') or wire_data.get('pin2_comp_id')
                if comp_id in id_map:
                    pin2 = id_map[comp_id].get_pin(wire_data['pin2_name'])
                else:
                    continue
            
            if pin1 and pin2:
                # Convert waypoints to list of tuples to ensure they're immutable coordinates
                waypoints = [(x, y) for x, y in wire_data['waypoints']]
                wire = Wire(pin1, pin2, waypoints)
                self.wires.append(wire)
    
    def clear(self):
        """Clear all components, wires, and junctions on current page"""
        for wire in self.wires:
            wire.disconnect()
        self.wires.clear()
        self.components.clear()
        self.junctions.clear()
        self.deselect_all()
    
    def add_page(self, page_name):
        """Add a new page"""
        if page_name not in self.pages:
            self.pages[page_name] = {
                'components': [],
                'wires': [],
                'junctions': [],
                'zoom': 1.0,
                'scroll_x': 0.5,
                'scroll_y': 0.5
            }
            return True
        return False
    
    def switch_page(self, page_name):
        """Switch to a different page"""
        if page_name in self.pages:
            # Save current page's zoom and scroll position
            if self.current_page in self.pages:
                self.pages[self.current_page]['zoom'] = self.zoom_level
                self.pages[self.current_page]['scroll_x'] = self.canvas.xview()[0]
                self.pages[self.current_page]['scroll_y'] = self.canvas.yview()[0]
            
            # Switch to new page
            self.current_page = page_name
            self.components = self.pages[page_name]['components']
            self.wires = self.pages[page_name]['wires']
            self.junctions = self.pages[page_name]['junctions']
            
            # Restore zoom and scroll position
            self.zoom_level = self.pages[page_name].get('zoom', 1.0)
            self.update_zoom_display()
            self._update_scroll_region()  # Update scroll region for the zoom level
            
            # Deselect and redraw
            self.deselect_all()
            self.redraw_visual()
            
            # Restore scroll position after a brief delay (to ensure canvas is ready)
            scroll_x = self.pages[page_name].get('scroll_x', 0.5)
            scroll_y = self.pages[page_name].get('scroll_y', 0.5)
            self.canvas.after(10, lambda: self.canvas.xview_moveto(scroll_x))
            self.canvas.after(10, lambda: self.canvas.yview_moveto(scroll_y))
            
            return True
        return False
    
    def rename_page(self, old_name, new_name):
        """Rename a page"""
        if old_name in self.pages and new_name not in self.pages:
            self.pages[new_name] = self.pages.pop(old_name)
            if self.current_page == old_name:
                self.current_page = new_name
            return True
        return False
    
    def delete_page(self, page_name):
        """Delete a page (cannot delete if it's the only page)"""
        if len(self.pages) > 1 and page_name in self.pages:
            # If deleting current page, switch to another
            if self.current_page == page_name:
                # Switch to first available page
                for name in self.pages:
                    if name != page_name:
                        self.switch_page(name)
                        break
            del self.pages[page_name]
            return True
        return False
    
    def get_page_names(self):
        """Get list of all page names"""
        return list(self.pages.keys())
    
    def center_canvas_view(self):
        """Center the canvas view on the middle of the scrolling region"""
        # Get the scroll region size
        scroll_region = self.canvas.cget('scrollregion').split()
        if len(scroll_region) == 4:
            canvas_width = int(scroll_region[2])
            canvas_height = int(scroll_region[3])
            
            # Get visible area size
            visible_width = self.canvas.winfo_width()
            visible_height = self.canvas.winfo_height()
            
            # Calculate center position as fractions (0.0 to 1.0)
            center_x = (canvas_width / 2 - visible_width / 2) / canvas_width
            center_y = (canvas_height / 2 - visible_height / 2) / canvas_height
            
            # Move view to center
            self.canvas.xview_moveto(max(0, center_x))
            self.canvas.yview_moveto(max(0, center_y))
    
    def apply_zoom(self, value):
        """Apply zoom scaling to a value (size, offset, etc.)"""
        return value * self.zoom_level
    
    def apply_zoom_coords(self, x, y):
        """Apply zoom scaling to coordinates"""
        return (x * self.zoom_level, y * self.zoom_level)
    
    def unapply_zoom_coords(self, x, y):
        """Convert zoomed canvas coordinates back to logical coordinates"""
        return (x / self.zoom_level, y / self.zoom_level)
    
    def update_zoom_display(self):
        """Update the zoom level display in the status bar"""
        if self.zoom_label:
            zoom_percent = int(self.zoom_level * 100)
            self.zoom_label.config(text=f"Zoom: {zoom_percent}%")
        
    def zoom_in(self):
        """Zoom in"""
        self.zoom_level = min(1.5, self.zoom_level + 0.1)
        self.update_zoom_display()
        self._update_scroll_region()
        self.update()
        
    def zoom_out(self):
        """Zoom out"""
        self.zoom_level = max(0.3, self.zoom_level - 0.1)
        self.update_zoom_display()
        self._update_scroll_region()
        self.update()
        
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.zoom_level = 1.0
        self.update_zoom_display()
        self._update_scroll_region()
        self.update()
    
    def _update_scroll_region(self):
        """Update the canvas scroll region based on zoom level"""
        # The logical canvas size is 4000x4000
        # When zoomed, the visual size becomes base_size * zoom_level
        # Add extra padding to ensure components at edges are fully visible
        base_size = 4000
        padding = 500  # Extra space around edges for components and panning
        zoomed_size = int((base_size + padding) * self.zoom_level)
        self.canvas.config(scrollregion=(0, 0, zoomed_size, zoomed_size))
    
    def redraw_visual(self):
        """Redraw only visual elements without recalculating circuit logic"""
        # Delete visual elements
        self.canvas.delete('wire')
        self.canvas.delete('component')
        self.canvas.delete('pin')
        self.canvas.delete('grid')
        self.canvas.delete('junction')
        
        # Draw grid
        self.draw_grid()
        
        # Draw wires
        for wire in self.wires:
            points = wire.get_all_points()
            color = 'red' if wire.is_active() else 'gray'
            width = max(1, int(3 * self.zoom_level)) if wire.selected else max(1, int(2 * self.zoom_level))
            
            # Draw each segment with zoom applied
            for i in range(len(points) - 1):
                x1, y1 = self.apply_zoom_coords(points[i][0], points[i][1])
                x2, y2 = self.apply_zoom_coords(points[i+1][0], points[i+1][1])
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, tags='wire')
            
            # Draw waypoint markers if wire is selected
            if wire.selected:
                for wx, wy in wire.waypoints:
                    zwx, zwy = self.apply_zoom_coords(wx, wy)
                    r = self.apply_zoom(3)
                    self.canvas.create_oval(zwx-r, zwy-r, zwx+r, zwy+r, 
                                           fill='yellow', outline='black', tags='wire')
        
        # Draw junctions
        for junction in self.junctions:
            zx, zy = self.apply_zoom_coords(junction.x, junction.y)
            r = self.apply_zoom(5)
            self.canvas.create_oval(zx-r, zy-r, zx+r, zy+r,
                                   fill='red', outline='black', width=2, tags='junction')
                                   
        # Draw components
        for component in self.components:
            self.draw_component_zoomed(component)
            
            # Draw pins
            for pin in component.pins:
                px, py = pin.get_position()
                zpx, zpy = self.apply_zoom_coords(px, py)
                
                # Check if pin has manual state and is not connected
                has_manual_state = (hasattr(pin, 'manual_state') and 
                                  pin.manual_state is not None and 
                                  len(pin.wires) == 0)
                
                if has_manual_state:
                    # Draw with special indicator for manually set pins
                    color = 'orange' if pin.manual_state == 'HIGH' else 'lightgray'
                    r = self.apply_zoom(4)
                    # Draw outer ring to indicate manual control
                    self.canvas.create_oval(zpx-r-2, zpy-r-2, zpx+r+2, zpy+r+2,
                                           outline='blue', width=2, tags='pin')
                    self.canvas.create_oval(zpx-r, zpy-r, zpx+r, zpy+r,
                                           fill=color, outline='black', tags='pin')
                else:
                    color = 'green' if pin.is_high() else 'lightgray'
                    r = self.apply_zoom(4)
                    self.canvas.create_oval(zpx-r, zpy-r, zpx+r, zpy+r,
                                           fill=color, outline='black', tags='pin')
    
    def draw_component_zoomed(self, component):
        """Draw a component with zoom applied"""
        # Temporarily set component position to zoomed coordinates for drawing
        original_x, original_y = component.x, component.y
        original_width, original_height = component.width, component.height
        
        component.x, component.y = self.apply_zoom_coords(original_x, original_y)
        component.width = self.apply_zoom(original_width)
        component.height = self.apply_zoom(original_height)
        
        # Draw the component
        component.draw(self.canvas)
        
        # Restore original position and size
        component.x, component.y = original_x, original_y
        component.width, component.height = original_width, original_height
    
    def stop_logic(self):
        """Stop logic processing and reset circuit to FLOAT state"""
        self.logic_running = False
        
        # Import component types that need state reset
        from src.components.dpdt_relay import DPDTRelay
        from src.components.indicator import Indicator
        from src.components.toggle_button import ToggleButton
        from src.components.link import Link
        
        # Clear all pin states and component states on ALL pages
        for page_content in self.pages.values():
            for component in page_content['components']:
                # Reset all pins to FLOAT (but preserve manual_state)
                for pin in component.pins:
                    pin.state = None
                    # Do NOT clear manual_state - it should persist through stop/reset
                
                # Reset component-specific states to default
                if isinstance(component, DPDTRelay):
                    component.is_energized = False
                    component.target_state = False
                    component.state_change_time = None
                    component.update_contacts()  # Reset contact connections to default (NC)
                elif isinstance(component, Indicator):
                    component.is_active = False
                elif isinstance(component, ToggleButton):
                    component.is_pressed = False
                    component.properties["is_pressed"] = False
                    
            # Reset junction pins (but preserve manual_state)
            for junction in page_content['junctions']:
                junction.pin.state = None
                # Do NOT clear manual_state - it should persist through stop/reset
        
        # Reset Link states (used by both Link and Bus components)
        Link.reset_link_states()
    
    def start_logic(self):
        """Start logic processing"""
        # Auto-load binary files for Memory components when Play is pressed
        for page_content in self.pages.values():
            for component in page_content['components']:
                if hasattr(component, 'auto_load_bin_file'):
                    component.auto_load_bin_file()
        
        self.logic_running = True
    
    def start_watchdog(self):
        """Start a background thread to monitor for freezes"""
        def watchdog():
            while True:  # Run forever, not just when logic running
                time.sleep(2)  # Check every 2 seconds
                current_time = time.time()
                if self.operation_start_time > 0:
                    elapsed = current_time - self.operation_start_time
                    if elapsed > 3:  # If stuck in one operation for >3 seconds
                        print(f"🔴 FREEZE DETECTED!")
                        print(f"   Stuck in: {self.current_operation}")
                        print(f"   Duration: {elapsed:.1f}s")
                        print(f"   Components: {len(self.components)}")
                        print(f"   Wires: {len(self.wires)}")
                        print(f"   Pages: {len(self.pages)}")
                        print(f"   Logic running: {self.logic_running}")
        
        watchdog_thread = threading.Thread(target=watchdog, daemon=True)
        watchdog_thread.start()
    
    def pause_logic(self):
        """Pause logic processing - maintain current states but stop updates"""
        self.logic_running = False
        
    def update(self):
        """Update canvas - logic and visual updates"""
        # Track update call frequency
        self._update_call_count += 1
        current_time = time.time()
        if current_time - self._last_update_count_reset >= 1.0:
            if self._update_call_count > 20:  # More than 20 updates per second
                print(f"⚠️ EXCESSIVE UPDATES: {self._update_call_count} calls in 1 second")
            self._update_call_count = 0
            self._last_update_count_reset = current_time
        
        start_time = time.time()
        try:
            self._update_impl()
            duration_ms = (time.time() - start_time) * 1000
            if duration_ms > 100:  # Log slow updates
                print(f"⚠️ SLOW UPDATE: {duration_ms:.1f}ms")
        except Exception as e:
            print(f"❌ ERROR in update: {e}")
            traceback.print_exc()
    
    def _update_impl(self):
        """Update canvas - implementation"""
        self.current_operation = "update_start"
        self.operation_start_time = time.time()
        self.update_counter += 1
        
        # Redraw every cycle for responsive visual feedback
        should_redraw = True
        
        redraw_start = time.time()
        if should_redraw:
            self.current_operation = "clearing_canvas"
            # Delete everything except temporary wire preview
            self.canvas.delete('wire')
            self.canvas.delete('component')
            self.canvas.delete('pin')
            self.canvas.delete('grid')
            self.canvas.delete('junction')
        
        # Draw grid (optional) - only when redrawing
        if should_redraw:
            self.current_operation = "draw_grid"
            self.draw_grid()
            
            # Draw rectangles first (in background) - import Rectangle class
            from src.components.rectangle import Rectangle
            for component in self.components:
                if isinstance(component, Rectangle):
                    self.draw_component_zoomed(component)
        
            # Draw wires
            for wire in self.wires:
                points = wire.get_all_points()
                color = 'red' if wire.is_active() else 'gray'
                width = max(1, int(3 * self.zoom_level)) if wire.selected else max(1, int(2 * self.zoom_level))
                
                # Draw each segment with zoom applied
                for i in range(len(points) - 1):
                    x1, y1 = self.apply_zoom_coords(points[i][0], points[i][1])
                    x2, y2 = self.apply_zoom_coords(points[i+1][0], points[i+1][1])
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, tags='wire')
                
                # Draw waypoint markers (small circles) if wire is selected
                if wire.selected:
                    for wx, wy in wire.waypoints:
                        zwx, zwy = self.apply_zoom_coords(wx, wy)
                        r = self.apply_zoom(3)
                        self.canvas.create_oval(zwx-r, zwy-r, zwx+r, zwy+r, 
                                               fill='yellow', outline='black', tags='wire')
            
            # Draw junctions
            for junction in self.junctions:
                zx, zy = self.apply_zoom_coords(junction.x, junction.y)
                r = self.apply_zoom(5)
                self.canvas.create_oval(zx-r, zy-r, zx+r, zy+r,
                                       fill='red', outline='black', width=2, tags='junction')
                                       
            # Draw components (skip rectangles - already drawn in background)
            from src.components.rectangle import Rectangle
            for component in self.components:
                # Skip rectangles as they were already drawn in the background
                if isinstance(component, Rectangle):
                    continue
                    
                # Apply zoom to component drawing
                self.draw_component_zoomed(component)
                
                # Draw pins
                for pin in component.pins:
                    px, py = pin.get_position()
                    zpx, zpy = self.apply_zoom_coords(px, py)
                    
                    # Check if pin has manual state and is not connected
                    has_manual_state = (hasattr(pin, 'manual_state') and 
                                      pin.manual_state is not None and 
                                      len(pin.wires) == 0)
                    
                    if has_manual_state:
                        # Draw with special indicator for manually set pins
                        color = 'orange' if pin.manual_state == 'HIGH' else 'lightgray'
                        r = self.apply_zoom(4)
                        # Draw outer ring to indicate manual control
                        self.canvas.create_oval(zpx-r-2, zpy-r-2, zpx+r+2, zpy+r+2,
                                               outline='blue', width=2, tags='pin')
                        self.canvas.create_oval(zpx-r, zpy-r, zpx+r, zpy+r,
                                               fill=color, outline='black', tags='pin')
                    else:
                        # Color: green = HIGH, gray = FLOAT
                        color = 'green' if pin.is_high() else 'lightgray'
                        r = self.apply_zoom(4)
                        self.canvas.create_oval(zpx-r, zpy-r, zpx+r, zpy+r,
                                               fill=color, outline='black', tags='pin')
                                       
        # Import Link and Bus classes (needed for logic processing)
        from src.components.link import Link
        from src.components.bus import Bus
        
        # Only process logic if logic_running is True
        if self.logic_running:
            # Don't reset link states - they should persist across pages and update cycles
            # Link states will be updated during the collect phase based on actual pin states
            
            # Clear all pin states on ALL pages first (reset to FLOAT)
            self.current_operation = "logic_clear_pins"
            for page_content in self.pages.values():
                for component in page_content['components']:
                    for pin in component.pins:
                        pin.state = None
                for junction in page_content['junctions']:
                    junction.pin.state = None
            
            # Apply manual pin states (pins that user has manually set to HIGH)
            self.current_operation = "logic_manual_states"
            for page_content in self.pages.values():
                for component in page_content['components']:
                    for pin in component.pins:
                        if hasattr(pin, 'manual_state') and pin.manual_state == 'HIGH':
                            pin.state = True
                for junction in page_content['junctions']:
                    if hasattr(junction.pin, 'manual_state') and junction.pin.manual_state == 'HIGH':
                        junction.pin.state = True
            
            # PASS 1: Update all components on ALL pages (active components drive signals)
            self.current_operation = "logic_pass1"
            for page_content in self.pages.values():
                for component in page_content['components']:
                    component.first_pass = True  # Always set, don't check hasattr
                    component.update_logic()
            
            # Resolve wire states on ALL pages (propagate signals through wires)
            self.current_operation = "logic_resolve1"
            for page_content in self.pages.values():
                visited_pins = set()
                all_pins = []
                for comp in page_content['components']:
                    all_pins.extend(comp.pins)
                for junc in page_content['junctions']:
                    all_pins.append(junc.pin)
            
                for pin in all_pins:
                    if pin in visited_pins:
                        continue
                    
                    # Get all pins in this network
                    network = self.get_pin_network(pin)
                    visited_pins.update(network)
                    
                    # Check if any pin in the network is HIGH
                    has_high = any(p.is_high() for p in network)
                    
                    # Set all pins in network to the resolved state
                    target_state = True if has_high else None
                    for p in network:
                        p.state = target_state
            
            # COLLECT PHASE: Links collect their local pin states into global dictionary
            # Process all pages for Link components and other link-participating components
            self.current_operation = "logic_collect_links"
            Link.disable_publishing()  # Don't publish during collect - states may be unstable
            
            # First, reset all link states to None (FLOAT)
            # We'll rebuild them based on what's actually driven
            Link._link_states = {}
            
            # Track which link names we've seen
            seen_links = set()
            
            for page_content in self.pages.values():
                for component in page_content['components']:
                    if isinstance(component, Link):
                        seen_links.add(component.link_name)
                        # Check if any pins are HIGH from wire resolution
                        local_state = any(pin.state is True for pin in component.pins)
                        if local_state:
                            Link.set_link_state(component.link_name, True)
                    elif isinstance(component, Bus):
                        # Check each pin on the bus and set individual link states
                        for i in range(component.pin_count):
                            pin_number = component.start_pin + i
                            pin = component.get_pin(f"Pin{pin_number}")
                            if pin:
                                link_name = f"{component.bus_name}_{pin_number}"
                                seen_links.add(link_name)
                                if pin.state is True:
                                    Link.set_link_state(link_name, True)
                    elif hasattr(component, 'link_name') and component.link_name:
                        # Handle other components with link_name (Toggle Button, etc.)
                        seen_links.add(component.link_name)
                        # Check if component is actively driving (any pin HIGH)
                        local_state = any(pin.state is True for pin in component.pins)
                        if local_state:
                            Link.set_link_state(component.link_name, True)
            
            # Ensure all seen link names have a state (even if None/FLOAT)
            for link_name in seen_links:
                if link_name not in Link._link_states:
                    Link.set_link_state(link_name, None)
                    
            Link.enable_publishing()  # Re-enable for pass3
            
            # PASS 2: Update all components on ALL pages with resolved states
            self.current_operation = "logic_pass2"
            for page_content in self.pages.values():
                for component in page_content['components']:
                    component.first_pass = False  # Always set, don't check hasattr
                    component.update_logic()
            
            # Resolve wire states on ALL pages again
            for page_content in self.pages.values():
                visited_pins = set()
                all_pins = []
                for comp in page_content['components']:
                    all_pins.extend(comp.pins)
                for junc in page_content['junctions']:
                    all_pins.append(junc.pin)
                
                for pin in all_pins:
                    if pin in visited_pins:
                        continue
                    
                    network = self.get_pin_network(pin)
                    visited_pins.update(network)
                    
                    has_high = any(p.is_high() for p in network)
                    target_state = True if has_high else None
                    for p in network:
                        p.state = target_state
            
            # PASS 3: Final update for passive components on ALL pages
            self.current_operation = "logic_pass3"
            for page_content in self.pages.values():
                for component in page_content['components']:
                    component.first_pass = False  # Always set, ensure it's still False for pass 3
                    component.update_logic()
            
            # After pass3, publish final stable Link states to network
            Link.publish_all_states()
        
        # Schedule next update with interval to balance responsiveness and performance
        # Only schedule if not already scheduled to prevent multiple pending updates
        if not self._update_scheduled:
            self._update_scheduled = True
            self.canvas.after(50, self._schedule_update)  # 50ms for responsive updates (~20 FPS)
    
    def _schedule_update(self):
        """Schedule an update - runs after the delay"""
        self._update_scheduled = False  # Mark that the scheduled update is now running
        self.update()
        
    def draw_grid(self, spacing=20):
        """Draw a grid on the canvas - optimized for zoom"""
        # Don't draw grid if zoomed out too far (it becomes too dense and slow)
        if self.zoom_level < 0.3:
            return
        
        # Get visible area of canvas
        x1 = self.canvas.canvasx(0)
        y1 = self.canvas.canvasy(0)
        x2 = self.canvas.canvasx(self.canvas.winfo_width())
        y2 = self.canvas.canvasy(self.canvas.winfo_height())
        
        # Convert to logical coordinates
        lx1, ly1 = self.unapply_zoom_coords(x1, y1)
        lx2, ly2 = self.unapply_zoom_coords(x2, y2)
        
        # Adjust spacing based on zoom level
        if self.zoom_level < 0.5:
            spacing = spacing * 5  # Fewer lines when zoomed out
        elif self.zoom_level < 0.8:
            spacing = spacing * 2
        
        # Calculate grid bounds in logical space
        start_x = int(lx1 / spacing) * spacing
        start_y = int(ly1 / spacing) * spacing
        end_x = int(lx2 / spacing + 1) * spacing
        end_y = int(ly2 / spacing + 1) * spacing
        
        # Draw only visible grid lines
        for i in range(start_x, end_x, spacing):
            x_screen = i * self.zoom_level
            self.canvas.create_line(x_screen, y1, x_screen, y2, fill='lightgray', tags='grid')
        
        for i in range(start_y, end_y, spacing):
            y_screen = i * self.zoom_level
            self.canvas.create_line(x1, y_screen, x2, y_screen, fill='lightgray', tags='grid')
    
    def _get_canvas_bounds(self, padding=40):
        """Use actual canvas items to determine export bounds."""
        bbox = self.canvas.bbox('component', 'wire', 'pin', 'junction')
        if not bbox:
            return None

        min_x, min_y, max_x, max_y = bbox
        min_x = min_x - padding
        min_y = min_y - padding
        max_x += padding
        max_y += padding

        width = max(1, int(math.ceil(max_x - min_x)))
        height = max(1, int(math.ceil(max_y - min_y)))

        return (int(math.floor(min_x)), int(math.floor(min_y)), width, height)

    def export_png(self, output_path, ghostscript_hint=None, padding=40):
        """Export the current page contents to a PNG image."""
        normalized_path = self._normalize_png_path(output_path)
        export_state = self._prepare_export_state()

        bg_id = None
        try:
            self.redraw_visual()
            self.canvas.update_idletasks()

            bounds = self._get_canvas_bounds(padding=padding)
            if not bounds:
                raise ValueError("There is nothing on the canvas to export.")

            min_x, min_y, width, height = bounds
            print(f"[PNG Export] bounds=({min_x},{min_y},{width},{height})")
            bg_id = self.canvas.create_rectangle(
                min_x,
                min_y,
                min_x + width,
                min_y + height,
                fill='white',
                outline='',
                tags='export_bg'
            )
            self.canvas.tag_lower(bg_id)
            self.canvas.update_idletasks()

            ps_data = self.canvas.postscript(
                colormode='color',
                x=min_x,
                y=min_y,
                width=width,
                height=height,
                pagewidth=f"{width}p",
                pageheight=f"{height}p"
            )
            bbox = self._extract_ps_bbox(ps_data)
            if bbox:
                print(f"[PNG Export] postscript bbox={bbox}")
                ps_data, adjusted = self._normalize_postscript_bbox(ps_data, bbox)
                if adjusted:
                    print(f"[PNG Export] applied ps translate {adjusted}")
        finally:
            if bg_id is not None:
                self.canvas.delete(bg_id)
            self._restore_export_state(export_state)

        self._postscript_to_png(ps_data, normalized_path, width, height, ghostscript_hint)
        return normalized_path

    def _prepare_export_state(self):
        """Snapshot canvas state so it can be restored after exporting."""
        state = {
            "zoom": self.zoom_level,
            "logic_running": self.logic_running,
            "xview": self.canvas.xview(),
            "yview": self.canvas.yview(),
            "scrollregion": self.canvas.cget('scrollregion')
        }

        self.logic_running = False
        self.zoom_level = 1.0
        self.update_zoom_display()
        self._update_scroll_region()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        return state

    def _restore_export_state(self, state):
        """Restore canvas state after an export attempt."""
        self.zoom_level = state.get("zoom", 1.0)
        self.update_zoom_display()
        self._update_scroll_region()

        xview = state.get("xview", (0, 1))
        yview = state.get("yview", (0, 1))
        self.canvas.xview_moveto(xview[0])
        self.canvas.yview_moveto(yview[0])

        scrollregion = state.get("scrollregion")
        if scrollregion:
            self.canvas.config(scrollregion=scrollregion)

        self.canvas.update_idletasks()

        if state.get("logic_running"):
            self.start_logic()

        self.update()

    def _normalize_png_path(self, filename):
        """Ensure the output path ends with .png and exists."""
        path = Path(filename).expanduser()
        if path.suffix.lower() != '.png':
            path = path.with_suffix('.png')

        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        return str(path)

    def _extract_ps_bbox(self, ps_content):
        """Extract BoundingBox from PostScript content for debugging."""
        match = re.search(r"%%BoundingBox:\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)", ps_content)
        if match:
            return tuple(int(part) for part in match.groups())
        return None

    def _normalize_postscript_bbox(self, ps_content, bbox):
        """Translate PostScript so bounding box starts at (0,0). Returns (content, (dx, dy))."""
        min_x, min_y, max_x, max_y = bbox
        shift_x = -min(0, min_x)
        shift_y = -min(0, min_y)
        if shift_x == 0 and shift_y == 0:
            return ps_content, None

        injection = f"{shift_x} {shift_y} translate\n"
        marker = "%%EndProlog\n"
        idx = ps_content.find(marker)
        if idx != -1:
            idx += len(marker)
            ps_content = ps_content[:idx] + injection + ps_content[idx:]
        else:
            ps_content = injection + ps_content

        new_bbox = (min_x + shift_x, min_y + shift_y, max_x + shift_x, max_y + shift_y)
        ps_content = re.sub(
            r"%%BoundingBox:\s*-?\d+\s+-?\d+\s+-?\d+\s+-?\d+",
            f"%%BoundingBox: {new_bbox[0]} {new_bbox[1]} {new_bbox[2]} {new_bbox[3]}",
            ps_content,
            count=1
        )
        ps_content = re.sub(
            r"%%HiResBoundingBox:\s*-?[\d\.]+\s+-?[\d\.]+\s+-?[\d\.]+\s+-?[\d\.]+",
            f"%%HiResBoundingBox: {float(new_bbox[0]):.3f} {float(new_bbox[1]):.3f} {float(new_bbox[2]):.3f} {float(new_bbox[3]):.3f}",
            ps_content,
            count=1
        )

        return ps_content, (shift_x, shift_y)

    def _postscript_to_png(self, ps_data, output_path, width, height, ghostscript_hint=None):
        """Convert PostScript data to PNG using Ghostscript."""
        ghostscript_executable = self._find_ghostscript_executable(ghostscript_hint)

        bbox = self._extract_ps_bbox(ps_data)
        if bbox:
            print(f"[PNG Export] postscript bbox={bbox}")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.ps', mode='w', encoding='utf-8') as temp_ps:
            temp_ps.write(ps_data)
            ps_path = temp_ps.name

        try:
            cmd = [
                ghostscript_executable,
                '-dSAFER',
                '-dBATCH',
                '-dNOPAUSE',
                '-sDEVICE=pngalpha',
                '-dGraphicsAlphaBits=4',
                '-dTextAlphaBits=4',
                '-dBackgroundColor=16#FFFFFF',
                '-dUseTransparency=false',
                '-r72',
                f'-g{width}x{height}',
                f'-sOutputFile={output_path}',
                ps_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode('utf-8', errors='ignore') if exc.stderr else ''
            raise RuntimeError(f"Ghostscript conversion failed: {stderr.strip()}") from exc
        finally:
            if os.path.exists(ps_path):
                os.remove(ps_path)

    def _find_ghostscript_executable(self, user_hint=None):
        """Locate a Ghostscript executable using several strategies."""
        candidates = []
        seen = set()

        def add_candidate(path_like):
            if not path_like:
                return
            resolved = Path(path_like)
            if resolved.is_file():
                seen_key = resolved.resolve()
                if seen_key not in seen:
                    candidates.append(resolved)
                    seen.add(seen_key)

        def add_directory(directory):
            if not directory:
                return
            dir_path = Path(directory)
            if dir_path.is_dir():
                for exe_name in ('gswin64c.exe', 'gswin32c.exe', 'gs.exe'):
                    add_candidate(dir_path / 'bin' / exe_name)
                    add_candidate(dir_path / exe_name)

        add_directory(user_hint)
        add_directory(os.environ.get('GHOSTSCRIPT_PATH'))
        add_directory(os.environ.get('GHOSTSCRIPT_HOME'))

        for exe_name in ('gswin64c', 'gswin32c', 'gs'):
            which_path = shutil.which(exe_name)
            if which_path:
                add_candidate(which_path)

        possible_roots = [
            Path(os.environ.get('ProgramFiles', r'C:\\Program Files')) / 'gs',
            Path(os.environ.get('ProgramFiles(x86)', r'C:\\Program Files (x86)')) / 'gs'
        ]

        for root in possible_roots:
            if root.exists():
                for version_dir in sorted(root.iterdir(), reverse=True):
                    add_directory(version_dir)

        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)

        raise FileNotFoundError(
            "Ghostscript executable not found. Install Ghostscript or set the GHOSTSCRIPT_PATH environment variable."
        )

    def resolve_wire_states(self):
        """
        Resolve electrical states across all wire networks.
        If any pin in a connected network is HIGH, all pins in that network become HIGH.
        Otherwise all pins in the network are FLOAT.
        """
        # Build wire networks (groups of connected pins)
        visited_pins = set()
        
        # Include both component pins and junction pins
        all_pins = []
        for component in self.components:
            all_pins.extend(component.pins)
        for junction in self.junctions:
            all_pins.append(junction.pin)
        
        for pin in all_pins:
            if pin in visited_pins:
                continue
            
            # Get all pins in this network
            network = self.get_pin_network(pin)
            visited_pins.update(network)
            
            # Check if any pin in the network is HIGH (driven by a component)
            has_high = any(p.is_high() for p in network)
            
            # Set all pins in network to the resolved state
            target_state = True if has_high else None
            for p in network:
                p.state = target_state
    
    def get_pin_network(self, start_pin):
        """
        Get all pins connected to the start pin through wires (recursive network traversal).
        Returns a set of all pins in the connected network.
        """
        network = set()
        to_visit = [start_pin]
        
        while to_visit:
            pin = to_visit.pop()
            if pin in network:
                continue
                
            network.add(pin)
            
            # Add all directly connected pins
            for connected_pin in pin.get_connected_pins():
                if connected_pin not in network:
                    to_visit.append(connected_pin)
        
        return network
    
    def _get_pin_network_for_page(self, start_pin, wires):
        """Get all pins connected to start_pin through wires AND internal connections on a specific page"""
        network = {start_pin}
        to_visit = [start_pin]
        
        while to_visit:
            current_pin = to_visit.pop()
            
            # Check all wires on this page
            for wire in wires:
                if wire.pin1 == current_pin and wire.pin2 not in network:
                    network.add(wire.pin2)
                    to_visit.append(wire.pin2)
                elif wire.pin2 == current_pin and wire.pin1 not in network:
                    network.add(wire.pin1)
                    to_visit.append(wire.pin1)
            
            # Also follow internal connections (e.g., diode, relay contacts)
            for connected_pin in current_pin.internal_connections:
                if connected_pin not in network:
                    network.add(connected_pin)
                    to_visit.append(connected_pin)
        
        return network
    
    def _save_manual_pin_states(self, components):
        """Save manual pin states for all components"""
        manual_states = {}
        for comp in components:
            comp_manual_states = {}
            for pin in comp.pins:
                if hasattr(pin, 'manual_state') and pin.manual_state is not None:
                    comp_manual_states[pin.name] = pin.manual_state
            if comp_manual_states:
                manual_states[comp.id] = comp_manual_states
        return manual_states
    
    def _load_manual_pin_states(self, components, manual_states_data):
        """Restore manual pin states for all components"""
        # Create component ID to component mapping
        comp_map = {comp.id: comp for comp in components}
        
        for comp_id, pin_states in manual_states_data.items():
            comp = comp_map.get(int(comp_id))
            if comp:
                for pin_name, state in pin_states.items():
                    # Find the pin by name
                    pin = next((p for p in comp.pins if p.name == pin_name), None)
                    if pin:
                        pin.manual_state = state
            
    def get_empty_project(self):
        """Return an empty project structure"""
        return {
            "pages": {
                "Page 1": {
                    "components": [],
                    "junctions": [],
                    "wires": [],
                    "zoom": 1.0,
                    "scroll_x": 0.5,
                    "scroll_y": 0.5,
                    "manual_pin_states": {}
                }
            },
            "current_page": "Page 1"
        }
    
    def save_project(self):
        """Save project to dictionary including all pages"""
        # Save current page's zoom and scroll position before saving
        if self.current_page in self.pages:
            self.pages[self.current_page]['zoom'] = self.zoom_level
            self.pages[self.current_page]['scroll_x'] = self.canvas.xview()[0]
            self.pages[self.current_page]['scroll_y'] = self.canvas.yview()[0]
        
        pages_data = {}
        
        # Save each page
        for page_name, page_content in self.pages.items():
            # Save junctions with unique IDs
            junction_map = {}
            junctions_data = []
            for i, junction in enumerate(page_content['junctions']):
                junction_id = f"junction_{i}"
                junction_map[junction] = junction_id
                junctions_data.append({
                    "id": junction_id,
                    "x": junction.x,
                    "y": junction.y
                })
            
            # Save wires with waypoints and junction support
            wires_data = []
            for wire in page_content['wires']:
                # Determine pin1 info
                if hasattr(wire.pin1, 'junction'):
                    pin1_type = "junction"
                    pin1_id = junction_map.get(wire.pin1.junction, None)
                else:
                    pin1_type = "component"
                    pin1_id = wire.pin1.component.id
                    pin1_name = wire.pin1.name
                
                # Determine pin2 info
                if hasattr(wire.pin2, 'junction'):
                    pin2_type = "junction"
                    pin2_id = junction_map.get(wire.pin2.junction, None)
                else:
                    pin2_type = "component"
                    pin2_id = wire.pin2.component.id
                    pin2_name = wire.pin2.name
                
                wire_data = {
                    "pin1_type": pin1_type,
                    "pin1_id": pin1_id,
                    "pin2_type": pin2_type,
                    "pin2_id": pin2_id,
                    "waypoints": wire.waypoints
                }
                
                if pin1_type == "component":
                    wire_data["pin1_name"] = pin1_name
                if pin2_type == "component":
                    wire_data["pin2_name"] = pin2_name
                
                wires_data.append(wire_data)
            
            pages_data[page_name] = {
                "components": [comp.to_dict() for comp in page_content['components']],
                "junctions": junctions_data,
                "wires": wires_data,
                "zoom": page_content.get('zoom', 1.0),
                "scroll_x": page_content.get('scroll_x', 0.5),
                "scroll_y": page_content.get('scroll_y', 0.5),
                "manual_pin_states": self._save_manual_pin_states(page_content['components'])
            }
        
        return {
            "pages": pages_data,
            "current_page": self.current_page
        }
        
    def load_project(self, data):
        """Load project from dictionary including all pages"""
        from src.core.component import Component
        from src.components.toggle_button import ToggleButton
        from src.components.indicator import Indicator
        from src.components.dpdt_relay import DPDTRelay
        from src.components.vcc import VCC
        from src.components.clock import Clock
        from src.components.diode import Diode
        from src.components.link import Link
        from src.components.bus import Bus
        from src.components.label import Label
        from src.components.rectangle import Rectangle
        from src.components.seven_segment import SevenSegment
        from src.components.hex_keypad import HexKeypad
        from src.components.memory import Memory
        from src.components.logic_analyzer import LogicAnalyzer
        from src.core.junction import Junction
        from src.core.wire import Wire
        
        # Create class name to class mapping
        class_library = {
            "ToggleButton": ToggleButton,
            "Indicator": Indicator,
            "DPDTRelay": DPDTRelay,
            "Relay2": DPDTRelay,  # Support legacy name for backward compatibility
            "VCC": VCC,
            "Clock": Clock,
            "Diode": Diode,
            "Link": Link,
            "Bus": Bus,
            "Label": Label,
            "Rectangle": Rectangle,
            "SevenSegment": SevenSegment,
            "HexKeypad": HexKeypad,
            "Memory": Memory,
            "LogicAnalyzer": LogicAnalyzer
        }
        
        Component.reset_id_counter()
        Component.reset_type_counters()
        
        # Check if this is a multi-page format
        if "pages" in data:
            # Clear all pages
            self.pages = {}
            
            # Load each page
            for page_name, page_data in data["pages"].items():
                self.pages[page_name] = {
                    'components': [],
                    'wires': [],
                    'junctions': [],
                    'zoom': page_data.get('zoom', 1.0),
                    'scroll_x': page_data.get('scroll_x', 0.5),
                    'scroll_y': page_data.get('scroll_y', 0.5)
                }
                
                # Load components for this page
                component_map = {}
                for comp_data in page_data.get("components", []):
                    comp_type = comp_data["type"]
                    if comp_type in class_library:
                        component = class_library[comp_type](comp_data["x"], comp_data["y"])
                        component.name = comp_data["name"]
                        component.id = comp_data["id"]
                        component.properties = comp_data.get("properties", {})
                        
                        # Re-apply properties after loading
                        for key, value in component.properties.items():
                            if hasattr(component, key):
                                setattr(component, key, value)
                        
                        # For components with transformation (rotation/flip), update pin positions
                        if hasattr(component, 'update_pin_positions'):
                            component.update_pin_positions()
                        
                        # For Link components, restore link_name from properties
                        if comp_type == "Link" and "link_name" in component.properties:
                            component.link_name = component.properties["link_name"]
                        
                        self.pages[page_name]['components'].append(component)
                        component_map[component.id] = component
                
                # Load junctions for this page
                junction_map = {}
                for junction_data in page_data.get("junctions", []):
                    junction = Junction(junction_data["x"], junction_data["y"])
                    self.pages[page_name]['junctions'].append(junction)
                    junction_map[junction_data["id"]] = junction
                
                # Load wires for this page
                for wire_data in page_data.get("wires", []):
                    # Get pin1
                    if wire_data.get("pin1_type") == "junction":
                        junction = junction_map.get(wire_data["pin1_id"])
                        if junction:
                            pin1 = junction.pin
                        else:
                            continue
                    else:
                        comp1 = component_map.get(wire_data.get("pin1_id") or wire_data.get("pin1_component_id"))
                        if comp1:
                            pin1 = next((p for p in comp1.pins if p.name == wire_data.get("pin1_name")), None)
                            if not pin1:
                                continue
                        else:
                            continue
                    
                    # Get pin2
                    if wire_data.get("pin2_type") == "junction":
                        junction = junction_map.get(wire_data["pin2_id"])
                        if junction:
                            pin2 = junction.pin
                        else:
                            continue
                    else:
                        comp2 = component_map.get(wire_data.get("pin2_id") or wire_data.get("pin2_component_id"))
                        if comp2:
                            pin2 = next((p for p in comp2.pins if p.name == wire_data.get("pin2_name")), None)
                            if not pin2:
                                continue
                        else:
                            continue
                    
                    # Create wire with waypoints
                    waypoints_data = wire_data.get("waypoints", [])
                    waypoints = [(float(x), float(y)) for x, y in waypoints_data]
                    wire = Wire(pin1, pin2, waypoints)
                    self.pages[page_name]['wires'].append(wire)
                
                # Restore manual pin states for this page
                manual_states_data = page_data.get("manual_pin_states", {})
                if manual_states_data:
                    self._load_manual_pin_states(self.pages[page_name]['components'], manual_states_data)
            
            # Update ID counter from all pages
            all_components = []
            for page_content in self.pages.values():
                all_components.extend(page_content['components'])
            if all_components:
                Component._id_counter = max(c.id for c in all_components)
            
            # Rebuild type counters from loaded component names
            self.rebuild_type_counters()
            
            # Switch to the saved current page or first page
            page_to_load = data.get("current_page", list(self.pages.keys())[0] if self.pages else "Page 1")
            if page_to_load not in self.pages and self.pages:
                page_to_load = list(self.pages.keys())[0]
            self.switch_page(page_to_load)
            
        else:
            # Legacy single-page format - load into "Page 1"
            self.pages = {"Page 1": {'components': [], 'wires': [], 'junctions': []}}
            self.current_page = "Page 1"
            
            # Load components
            component_map = {}
            for comp_data in data.get("components", []):
                comp_type = comp_data["type"]
                if comp_type in class_library:
                    component = class_library[comp_type](comp_data["x"], comp_data["y"])
                    component.name = comp_data["name"]
                    component.id = comp_data["id"]
                    component.properties = comp_data.get("properties", {})
                    
                    # Re-apply properties after loading
                    for key, value in component.properties.items():
                        if hasattr(component, key):
                            setattr(component, key, value)
                    
                    # For components with transformation (rotation/flip), update pin positions
                    if hasattr(component, 'update_pin_positions'):
                        component.update_pin_positions()
                    
                    self.pages["Page 1"]['components'].append(component)
                    component_map[component.id] = component
            
            # Update ID counter
            if self.pages["Page 1"]['components']:
                Component._id_counter = max(c.id for c in self.pages["Page 1"]['components'])
            
            # Load junctions
            junction_map = {}
            for junction_data in data.get("junctions", []):
                junction = Junction(junction_data["x"], junction_data["y"])
                self.pages["Page 1"]['junctions'].append(junction)
                junction_map[junction_data["id"]] = junction
            
            # Load wires
            for wire_data in data.get("wires", []):
                # Get pin1
                if wire_data.get("pin1_type") == "junction":
                    junction = junction_map.get(wire_data["pin1_id"])
                    if junction:
                        pin1 = junction.pin
                    else:
                        continue
                else:
                    comp1 = component_map.get(wire_data.get("pin1_id") or wire_data.get("pin1_component_id"))
                    if comp1:
                        pin1 = next((p for p in comp1.pins if p.name == wire_data.get("pin1_name")), None)
                        if not pin1:
                            continue
                    else:
                        continue
                
                # Get pin2
                if wire_data.get("pin2_type") == "junction":
                    junction = junction_map.get(wire_data["pin2_id"])
                    if junction:
                        pin2 = junction.pin
                    else:
                        continue
                else:
                    comp2 = component_map.get(wire_data.get("pin2_id") or wire_data.get("pin2_component_id"))
                    if comp2:
                        pin2 = next((p for p in comp2.pins if p.name == wire_data.get("pin2_name")), None)
                        if not pin2:
                            continue
                    else:
                        continue
                
                # Create wire with waypoints
                waypoints_data = wire_data.get("waypoints", [])
                waypoints = [(float(x), float(y)) for x, y in waypoints_data]
                wire = Wire(pin1, pin2, waypoints)
                self.pages["Page 1"]['wires'].append(wire)
            
            # Set references to current page
            self.components = self.pages["Page 1"]['components']
            self.wires = self.pages["Page 1"]['wires']
            self.junctions = self.pages["Page 1"]['junctions']
            
            # Rebuild type counters from loaded component names
            self.rebuild_type_counters()
        
        # Auto-load binary files for Memory components
        for page_content in self.pages.values():
            for component in page_content['components']:
                if hasattr(component, 'auto_load_bin_file'):
                    component.auto_load_bin_file()
        
        # Redraw everything and update the circuit state
        self.update()
    
    def rebuild_type_counters(self):
        """Rebuild type counters from existing component names"""
        from src.core.component import Component
        import re
        
        # Reset counters
        Component.reset_type_counters()
        
        # Scan all components across all pages
        for page_content in self.pages.values():
            for component in page_content['components']:
                type_name = component.__class__.__name__
                
                # Try to extract number from component name
                # Expected format: TypeName_123
                match = re.search(r'_(\d+)$', component.name)
                if match:
                    number = int(match.group(1))
                    Component.update_type_counter(type_name, number)
