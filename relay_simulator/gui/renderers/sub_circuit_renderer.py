"""Renderer for SubCircuit component."""

import tkinter as tk
from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class SubCircuitRenderer(ComponentRenderer):
    """Renderer for SubCircuit components.
    
    Visual appearance:
    - Rectangular outline with dimensions from FOOTPRINT bounding box
    - Sub-circuit name displayed in center
    - Tabs positioned based on FOOTPRINT Link positions
    - Highlight when selected
    - Slightly transparent fill to distinguish from regular components
    """
    
    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing."""
        cx, cy = self.component.position
        width = self.component.width
        height = self.component.height
        
        half_w = width / 2
        half_h = height / 2
        
        return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)
    
    def render(self, zoom: float = 1.0) -> None:
        """Render the sub-circuit component."""
        self.clear()
        
        cx, cy = self.get_position()
        
        # Get dimensions
        width = self.component.width * zoom
        height = self.component.height * zoom
        name = self.component.sub_circuit_name or "SubCircuit"
        
        # Calculate bounding box
        x1 = cx - (width / 2)
        y1 = cy - (height / 2)
        x2 = cx + (width / 2)
        y2 = cy + (height / 2)
        
        # Determine colors based on state
        if self.selected:
            outline_color = VSCodeTheme.ACCENT_BLUE
            outline_width = 3
            fill_color = VSCodeTheme.BG_HOVER
        else:
            outline_color = VSCodeTheme.COMPONENT_OUTLINE
            outline_width = 2
            fill_color = '#1e1e1e'  # Slightly lighter than pure black for depth
        
        # Draw main rectangle
        rect_item = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=outline_color,
            width=outline_width,
            fill=fill_color,
            stipple='gray25' if not self.selected else '',  # Subtle texture
            tags=("component", f"component_{self.component.component_id}")
        )
        self.canvas_items.append(rect_item)
        
        # Draw sub-circuit name in center
        font_size = max(10, min(16, int(12 * zoom)))  # Scale font with zoom
        name_item = self.draw_text(
            cx, cy,
            text=name,
            font=('Arial', font_size, 'bold'),
            fill=VSCodeTheme.COMPONENT_TEXT,
            anchor='center',
            tags=("component", f"component_{self.component.component_id}")
        )
        
        # Draw instance ID below name (smaller text)
        if self.component.instance_id:
            id_font_size = max(8, int(10 * zoom))
            id_y = cy + (font_size + 5) * zoom
            id_item = self.draw_text(
                cx, id_y,
                text=f"[{self.component.instance_id[:8]}]",  # Show first 8 chars
                font=('Arial', id_font_size),
                fill=VSCodeTheme.FG_SECONDARY,
                anchor='center',
                tags=("component", f"component_{self.component.component_id}")
            )
        
        # Draw corner markers to indicate it's a sub-circuit (visual distinction)
        corner_size = 8 * zoom
        corner_color = VSCodeTheme.ACCENT_BLUE if self.selected else VSCodeTheme.FG_SECONDARY
        
        # Top-left corner
        tl_item = self.canvas.create_line(
            x1, y1 + corner_size,
            x1, y1,
            x1 + corner_size, y1,
            fill=corner_color,
            width=2,
            tags=("component", f"component_{self.component.component_id}")
        )
        self.canvas_items.append(tl_item)
        
        # Top-right corner
        tr_item = self.canvas.create_line(
            x2 - corner_size, y1,
            x2, y1,
            x2, y1 + corner_size,
            fill=corner_color,
            width=2,
            tags=("component", f"component_{self.component.component_id}")
        )
        self.canvas_items.append(tr_item)
        
        # Bottom-left corner
        bl_item = self.canvas.create_line(
            x1, y2 - corner_size,
            x1, y2,
            x1 + corner_size, y2,
            fill=corner_color,
            width=2,
            tags=("component", f"component_{self.component.component_id}")
        )
        self.canvas_items.append(bl_item)
        
        # Bottom-right corner
        br_item = self.canvas.create_line(
            x2 - corner_size, y2,
            x2, y2,
            x2, y2 - corner_size,
            fill=corner_color,
            width=2,
            tags=("component", f"component_{self.component.component_id}")
        )
        self.canvas_items.append(br_item)
        
        # Draw pin markers on edges (smaller than normal tabs to indicate connection points)
        # These are visual indicators only - not full tab circles
        for pin in self.component.pins.values():
            for tab in pin.tabs.values():
                # Get tab absolute position
                comp_x, comp_y = self.component.position
                tab_dx, tab_dy = tab.relative_position
                
                # Calculate absolute position
                tab_x = comp_x + tab_dx
                tab_y = comp_y + tab_dy
                
                # Convert to canvas coordinates
                canvas_x = tab_x * zoom
                canvas_y = tab_y * zoom
                
                # Draw small pin marker (3px radius instead of normal 5px)
                marker_radius = 3 * zoom
                pin_color = VSCodeTheme.ACCENT_BLUE if self.selected else VSCodeTheme.COMPONENT_OUTLINE
                
                marker_item = self.canvas.create_oval(
                    canvas_x - marker_radius,
                    canvas_y - marker_radius,
                    canvas_x + marker_radius,
                    canvas_y + marker_radius,
                    fill=pin_color,
                    outline=pin_color,
                    tags=("component", f"component_{self.component.component_id}", "pin_marker")
                )
                self.canvas_items.append(marker_item)
