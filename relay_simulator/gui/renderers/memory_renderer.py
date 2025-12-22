"""Memory renderer.

Renders a memory component with:
- Memory viewer grid (16 columns wide)
- Visible rows based on memory size
- Control pins (Enable, Read, Write) on left side
- Hex values in cells
- Highlight for last accessed address
- Click-to-edit cells in simulation mode
"""

from __future__ import annotations

import tkinter as tk
from tkinter import simpledialog
from typing import Optional

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class MemoryRenderer(ComponentRenderer):
    """Renderer for Memory components."""

    GRID_SQUARE_PX = 20

    # Memory viewer dimensions
    CELL_WIDTH = 40
    CELL_HEIGHT = 20
    COLUMNS = 16
    HEADER_HEIGHT = 20
    SIDE_HEADER_WIDTH = 60
    SCROLLBAR_WIDTH = 16
    RESIZE_HANDLE_HEIGHT = 8

    # Pins on left side
    PIN_OFFSET_X = -440
    PIN_SPACING = 70

    def __init__(self, canvas, component):
        super().__init__(canvas, component)
        self.scrollbar_dragging = False
        self.resize_dragging = False
        self._scrollbar_drag_offset_y = 0.0

    def _get_address_bits(self) -> int:
        try:
            bits = int(self.component.properties.get('address_bits', 8))
        except Exception:
            bits = 8
        return max(3, min(16, bits))

    def _get_data_bits(self) -> int:
        try:
            bits = int(self.component.properties.get('data_bits', 8))
        except Exception:
            bits = 8
        return max(1, min(16, bits))

    def _get_visible_rows(self) -> int:
        """Get number of visible rows in viewer."""
        try:
            rows = int(self.component.properties.get('visible_rows', 16))
        except Exception:
            rows = 16
        return max(1, min(rows, self._get_total_rows()))

    def _get_total_rows(self) -> int:
        """Calculate total number of rows for all memory."""
        size = self._get_memory_size()
        return (size + self.COLUMNS - 1) // self.COLUMNS

    def _get_scroll_offset(self) -> int:
        """Get current scroll offset (in rows)."""
        return getattr(self.component, 'scroll_offset', 0)

    def _set_scroll_offset(self, offset: int) -> None:
        """Set scroll offset, clamped to valid range."""
        total_rows = self._get_total_rows()
        visible_rows = self._get_visible_rows()
        max_offset = max(0, total_rows - visible_rows)
        self.component.scroll_offset = max(0, min(offset, max_offset))

    def _get_label(self) -> str:
        label = self.component.properties.get('label', '')
        return label if isinstance(label, str) else ''

    def _get_memory_size(self) -> int:
        return 1 << self._get_address_bits()

    def _get_rows(self) -> int:
        """Calculate number of rows needed for memory grid (alias for _get_total_rows)."""
        return self._get_total_rows()

    def _format_hex_value(self, value: int) -> str:
        """Format value as hex string with appropriate width."""
        data_bits = self._get_data_bits()
        hex_digits = (data_bits + 3) // 4
        return f"{value:0{hex_digits}X}"

    def _format_hex_address(self, address: int) -> str:
        """Format address as hex string."""
        addr_bits = self._get_address_bits()
        hex_digits = (addr_bits + 3) // 4
        return f"{address:0{hex_digits}X}"

    def get_bounds(self, zoom: float = 1.0) -> tuple[float, float, float, float]:
        """Get the bounding box of the memory component.
        
        Returns (x1, y1, x2, y2) in world/model coordinates.
        """
        cx, cy = self.component.position
        visible_rows = self._get_visible_rows()
        viewer_width = (self.SIDE_HEADER_WIDTH + self.COLUMNS * self.CELL_WIDTH + self.SCROLLBAR_WIDTH)
        viewer_height = (self.HEADER_HEIGHT + visible_rows * self.CELL_HEIGHT)

        x1 = cx - (viewer_width / 2)
        y1 = cy - (viewer_height / 2)
        x2 = x1 + viewer_width
        y2 = y1 + viewer_height

        return (x1, y1, x2, y2)

    def render(self, zoom: float = 1.0) -> None:
        self.clear()

        cx, cy = self.get_position()
        rotation = self.get_rotation()

        # Calculate dimensions
        visible_rows = self._get_visible_rows()
        total_rows = self._get_total_rows()
        scroll_offset = self._get_scroll_offset()
        
        viewer_width = (self.SIDE_HEADER_WIDTH + self.COLUMNS * self.CELL_WIDTH + self.SCROLLBAR_WIDTH) * zoom
        viewer_height = (self.HEADER_HEIGHT + visible_rows * self.CELL_HEIGHT) * zoom

        # Viewer area (centered on component position)
        viewer_x = cx - (viewer_width / 2)
        viewer_y = cy - (viewer_height / 2)

        outline_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        outline_width = 3 if self.selected else 2

        # Background
        self.draw_rectangle(
            viewer_x,
            viewer_y,
            viewer_width,
            viewer_height,
            fill=VSCodeTheme.BG_PRIMARY,
            outline=outline_color,
            width_px=outline_width,
            tags=('component', f'component_{self.component.component_id}')
        )

        # Draw label above viewer
        label = self._get_label().strip()
        if label:
            label_y = viewer_y - (15 * zoom)
            self.draw_text(
                cx,
                label_y,
                text=label,
                font_size=12,
                fill='#a0a0a0',
                anchor='s',
                tags=('component_label', f'label_{self.component.component_id}')
            )

        # Draw column headers (0x0, 0x1, ..., 0xF)
        header_y = viewer_y
        for col in range(self.COLUMNS):
            header_x = viewer_x + (self.SIDE_HEADER_WIDTH + col * self.CELL_WIDTH) * zoom
            self.draw_rectangle(
                header_x,
                header_y,
                self.CELL_WIDTH * zoom,
                self.HEADER_HEIGHT * zoom,
                fill=VSCodeTheme.BG_SECONDARY,
                outline='#404040',
                width_px=1,
                tags=('component', f'component_{self.component.component_id}')
            )
            self.draw_text(
                header_x + (self.CELL_WIDTH * zoom / 2),
                header_y + (self.HEADER_HEIGHT * zoom / 2),
                text=f"0x{col:X}",
                font_size=9,
                fill='#808080',
                anchor='center',
                tags=('component', f'component_{self.component.component_id}')
            )

        # Draw row headers and cells (only visible rows)
        last_addr = getattr(self.component, 'last_address', None)
        last_op = getattr(self.component, 'last_operation', None)

        for display_row in range(visible_rows):
            actual_row = scroll_offset + display_row
            if actual_row >= total_rows:
                break
                
            row_y = viewer_y + (self.HEADER_HEIGHT + display_row * self.CELL_HEIGHT) * zoom
            base_addr = actual_row * self.COLUMNS

            # Row header
            header_x = viewer_x
            self.draw_rectangle(
                header_x,
                row_y,
                self.SIDE_HEADER_WIDTH * zoom,
                self.CELL_HEIGHT * zoom,
                fill=VSCodeTheme.BG_SECONDARY,
                outline='#404040',
                width_px=1,
                tags=('component', f'component_{self.component.component_id}')
            )
            self.draw_text(
                header_x + (self.SIDE_HEADER_WIDTH * zoom / 2),
                row_y + (self.CELL_HEIGHT * zoom / 2),
                text=f"0x{base_addr:04X}",
                font_size=9,
                fill='#808080',
                anchor='center',
                tags=('component', f'component_{self.component.component_id}')
            )

            # Memory cells
            for col in range(self.COLUMNS):
                address = base_addr + col
                if address >= self._get_memory_size():
                    break

                cell_x = viewer_x + (self.SIDE_HEADER_WIDTH + col * self.CELL_WIDTH) * zoom
                cell_y = row_y

                # Determine cell appearance
                value = self.component.read_memory(address)
                is_accessed = (address == last_addr and last_op is not None)

                if is_accessed:
                    if last_op == 'read':
                        cell_fill = '#1a3a1a'  # Dark green for read
                    else:  # write
                        cell_fill = '#3a1a1a'  # Dark red for write
                else:
                    cell_fill = VSCodeTheme.BG_PRIMARY

                # Cell background
                cell_tag = f'memory_cell_{self.component.component_id}_{address}'
                self.draw_rectangle(
                    cell_x,
                    cell_y,
                    self.CELL_WIDTH * zoom,
                    self.CELL_HEIGHT * zoom,
                    fill=cell_fill,
                    outline='#404040',
                    width_px=1,
                    tags=('component', f'component_{self.component.component_id}', cell_tag, 'memory_cell')
                )

                # Cell value
                value_text = self._format_hex_value(value)
                text_color = '#ffffff' if value != 0 else '#606060'
                self.draw_text(
                    cell_x + (self.CELL_WIDTH * zoom / 2),
                    cell_y + (self.CELL_HEIGHT * zoom / 2),
                    text=value_text,
                    font_size=9,
                    fill=text_color,
                    anchor='center',
                    tags=('component', f'component_{self.component.component_id}', cell_tag)
                )

        # Draw scrollbar if needed
        if total_rows > visible_rows:
            self._render_scrollbar(viewer_x, viewer_y, viewer_width, viewer_height, zoom, outline_color)

        # Draw resize handle at bottom
        self._render_resize_handle(viewer_x, viewer_y, viewer_width, viewer_height, zoom, outline_color)

        # Draw pins (Enable, Read, Write) on left side
        self._render_pins(cx, cy, zoom, outline_color)

        # Draw tabs (connection points for wires)
        # Use the shared base implementation so rotation/selection behavior matches
        # other components and avoids renderer-specific coordinate bugs.
        self.draw_tabs(zoom)

    def draw_tabs(self, zoom: float = 1.0) -> None:
        """Draw only the left-side control tabs.

        The Memory component uses internal DATA_* pins to drive the Data bus via
        link mappings, but those tabs are not intended for user wiring.
        """
        cx, cy = self.get_position()
        rotation = self.get_rotation()

        for pin_id, pin in self.component.pins.items():
            # Hide right-side per-bit DATA tabs.
            if '.DATA_' in pin_id:
                continue

            # Hide internal per-bit ADDR tabs (used for simulation dependency tracking).
            if '.ADDR_' in pin_id:
                continue

            for tab in pin.tabs.values():
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

                tab_size = VSCodeTheme.TAB_SIZE * zoom
                self.draw_circle(
                    tx, ty,
                    radius=tab_size / 2,
                    fill='#00ff00',
                    outline='#ffffff',
                    width_px=1,
                    tags=('tab', f'tab_{tab.tab_id}')
                )

    def _render_pins(self, cx: float, cy: float, zoom: float, outline_color: str) -> None:
        """Render the control pins on the left side."""
        pin_names = ['Enable', 'Read', 'Write']

        for index, pin_name in enumerate(pin_names):
            # Pin position
            pin_x = cx + (self.PIN_OFFSET_X * zoom)
            pin_y = cy + ((-40 + index * self.PIN_SPACING) * zoom)

            # Pin circle
            radius = 6 * zoom
            self.draw_circle(
                pin_x,
                pin_y,
                radius=radius,
                fill=VSCodeTheme.BG_SECONDARY,
                outline=outline_color,
                width_px=2,
                tags=('component', f'component_{self.component.component_id}')
            )

            # Pin label
            self.draw_text(
                pin_x + (15 * zoom),
                pin_y,
                text=pin_name,
                font_size=10,
                fill='#a0a0a0',
                anchor='w',
                tags=('component', f'component_{self.component.component_id}')
            )

    def _render_tabs(self, zoom: float) -> None:
        """Backward-compatible: delegate to base draw_tabs()."""
        self.draw_tabs(zoom)

    def _render_scrollbar(self, viewer_x: float, viewer_y: float, viewer_width: float, 
                          viewer_height: float, zoom: float, outline_color: str) -> None:
        """Render scrollbar on the right side."""
        total_rows = self._get_total_rows()
        visible_rows = self._get_visible_rows()
        scroll_offset = self._get_scroll_offset()
        
        # Scrollbar track
        scrollbar_x = viewer_x + viewer_width - (self.SCROLLBAR_WIDTH * zoom)
        scrollbar_y = viewer_y + (self.HEADER_HEIGHT * zoom)
        scrollbar_track_height = (visible_rows * self.CELL_HEIGHT) * zoom
        
        self.draw_rectangle(
            scrollbar_x,
            scrollbar_y,
            self.SCROLLBAR_WIDTH * zoom,
            scrollbar_track_height,
            fill='#2a2a2a',
            outline='#404040',
            width_px=1,
            tags=('component', f'component_{self.component.component_id}', 'scrollbar_track')
        )
        
        # Scrollbar thumb
        if total_rows > visible_rows:
            thumb_height_ratio = visible_rows / total_rows
            thumb_height = max(20 * zoom, scrollbar_track_height * thumb_height_ratio)
            
            max_scroll = total_rows - visible_rows
            thumb_travel = scrollbar_track_height - thumb_height
            thumb_offset = (scroll_offset / max_scroll) * thumb_travel if max_scroll > 0 else 0
            
            thumb_y = scrollbar_y + thumb_offset
            
            self.draw_rectangle(
                scrollbar_x + (2 * zoom),
                thumb_y,
                (self.SCROLLBAR_WIDTH - 4) * zoom,
                thumb_height,
                fill='#505050',
                outline='#606060',
                width_px=1,
                tags=('component', f'component_{self.component.component_id}', 'scrollbar_thumb')
            )

    def _get_scrollbar_metrics(self, zoom: float) -> Optional[dict]:
        """Return scrollbar geometry and scroll mapping values.

        Returns None if a scrollbar is not needed.
        """
        visible_rows = self._get_visible_rows()
        total_rows = self._get_total_rows()
        if total_rows <= visible_rows:
            return None

        cx, cy = self.get_position()
        viewer_width = (self.SIDE_HEADER_WIDTH + self.COLUMNS * self.CELL_WIDTH + self.SCROLLBAR_WIDTH) * zoom
        viewer_height = (self.HEADER_HEIGHT + visible_rows * self.CELL_HEIGHT) * zoom

        viewer_x = cx - (viewer_width / 2)
        viewer_y = cy - (viewer_height / 2)

        scrollbar_x = viewer_x + viewer_width - (self.SCROLLBAR_WIDTH * zoom)
        scrollbar_y = viewer_y + (self.HEADER_HEIGHT * zoom)
        scrollbar_track_height = (visible_rows * self.CELL_HEIGHT) * zoom

        max_scroll = max(0, total_rows - visible_rows)
        thumb_height_ratio = visible_rows / total_rows
        thumb_height = max(20 * zoom, scrollbar_track_height * thumb_height_ratio)
        thumb_travel = max(1e-6, scrollbar_track_height - thumb_height)

        scroll_offset = self._get_scroll_offset()
        thumb_offset = (scroll_offset / max_scroll) * thumb_travel if max_scroll > 0 else 0
        thumb_y = scrollbar_y + thumb_offset

        return {
            'viewer_x': viewer_x,
            'viewer_y': viewer_y,
            'viewer_width': viewer_width,
            'viewer_height': viewer_height,
            'scrollbar_x': scrollbar_x,
            'scrollbar_y': scrollbar_y,
            'track_height': scrollbar_track_height,
            'thumb_y': thumb_y,
            'thumb_height': thumb_height,
            'thumb_travel': thumb_travel,
            'max_scroll': max_scroll,
        }

    def handle_scrollbar_press(self, canvas_x: float, canvas_y: float, zoom: float) -> bool:
        """Begin scrollbar interaction and update scroll offset.

        Returns True if the press was within the scrollbar and was handled.
        """
        metrics = self._get_scrollbar_metrics(zoom)
        if not metrics:
            return False

        sx = metrics['scrollbar_x']
        sy = metrics['scrollbar_y']
        track_h = metrics['track_height']
        if not (sx <= canvas_x <= sx + (self.SCROLLBAR_WIDTH * zoom) and sy <= canvas_y <= sy + track_h):
            return False

        thumb_y = metrics['thumb_y']
        thumb_h = metrics['thumb_height']
        max_scroll = metrics['max_scroll']
        thumb_travel = metrics['thumb_travel']

        # Click inside thumb -> start dragging
        if thumb_y <= canvas_y <= thumb_y + thumb_h:
            self.scrollbar_dragging = True
            self._scrollbar_drag_offset_y = float(canvas_y - thumb_y)
            return True

        # Click on track -> jump so thumb centers around click
        target_thumb_y = float(canvas_y - (thumb_h / 2))
        target_thumb_y = max(sy, min(target_thumb_y, sy + track_h - thumb_h))
        new_thumb_offset = target_thumb_y - sy
        new_scroll = int(round((new_thumb_offset / thumb_travel) * max_scroll)) if max_scroll > 0 else 0
        self._set_scroll_offset(new_scroll)
        return True

    def handle_scrollbar_drag(self, canvas_y: float, zoom: float) -> bool:
        """Update scrollbar position while dragging.

        Returns True if scroll offset changed.
        """
        if not self.scrollbar_dragging:
            return False

        metrics = self._get_scrollbar_metrics(zoom)
        if not metrics:
            return False

        sy = metrics['scrollbar_y']
        track_h = metrics['track_height']
        thumb_h = metrics['thumb_height']
        max_scroll = metrics['max_scroll']
        thumb_travel = metrics['thumb_travel']

        old_offset = self._get_scroll_offset()

        target_thumb_y = float(canvas_y - self._scrollbar_drag_offset_y)
        target_thumb_y = max(sy, min(target_thumb_y, sy + track_h - thumb_h))
        new_thumb_offset = target_thumb_y - sy
        new_scroll = int(round((new_thumb_offset / thumb_travel) * max_scroll)) if max_scroll > 0 else 0
        self._set_scroll_offset(new_scroll)
        return self._get_scroll_offset() != old_offset

    def handle_scrollbar_release(self) -> None:
        """End scrollbar interaction."""
        self.scrollbar_dragging = False
        self._scrollbar_drag_offset_y = 0.0

    def _render_resize_handle(self, viewer_x: float, viewer_y: float, viewer_width: float,
                               viewer_height: float, zoom: float, outline_color: str) -> None:
        """Render resize handle at bottom."""
        handle_y = viewer_y + viewer_height - (self.RESIZE_HANDLE_HEIGHT * zoom)
        handle_height = self.RESIZE_HANDLE_HEIGHT * zoom
        
        self.draw_rectangle(
            viewer_x,
            handle_y,
            viewer_width,
            handle_height,
            fill='#3a3a3a',
            outline='#404040',
            width_px=1,
            tags=('component', f'component_{self.component.component_id}', 'resize_handle')
        )
        
        # Draw grip lines
        grip_y = handle_y + (handle_height / 2)
        grip_spacing = 4 * zoom
        for i in range(-1, 2):
            line_x1 = viewer_x + (viewer_width / 2) + (i * grip_spacing) - (8 * zoom)
            line_x2 = viewer_x + (viewer_width / 2) + (i * grip_spacing) + (8 * zoom)
            self.canvas.create_line(
                line_x1, grip_y, line_x2, grip_y,
                fill='#606060',
                width=1,
                tags=('component', f'component_{self.component.component_id}')
            )
            self.canvas_items.append(self.canvas.find_all()[-1])

    def on_click(self, canvas_x: float, canvas_y: float, zoom: float, simulation_mode: bool = False) -> Optional[str]:
        """Handle click events on memory component.
        
        Returns the type of click target:
        - 'scrollbar' for scrollbar clicks
        - 'resize_handle' for resize handle clicks
        - 'memory_cell' if a cell was clicked (only in simulation mode)
        - 'component' if the component (header area) was clicked
        - None if click was outside component
        """
        # Check if click is on the component
        cx, cy = self.get_position()
        visible_rows = self._get_visible_rows()
        total_rows = self._get_total_rows()
        viewer_width = (self.SIDE_HEADER_WIDTH + self.COLUMNS * self.CELL_WIDTH + self.SCROLLBAR_WIDTH) * zoom
        viewer_height = (self.HEADER_HEIGHT + visible_rows * self.CELL_HEIGHT) * zoom

        viewer_x = cx - (viewer_width / 2)
        viewer_y = cy - (viewer_height / 2)

        # Check if click is within viewer bounds
        if not (viewer_x <= canvas_x <= viewer_x + viewer_width and
                viewer_y <= canvas_y <= viewer_y + viewer_height):
            return None

        rel_x = canvas_x - viewer_x
        rel_y = canvas_y - viewer_y

        # Check resize handle (bottom edge)
        handle_y = viewer_height - (self.RESIZE_HANDLE_HEIGHT * zoom)
        if rel_y >= handle_y:
            return 'resize_handle'

        # Check scrollbar area
        scrollbar_x = viewer_width - (self.SCROLLBAR_WIDTH * zoom)
        if rel_x >= scrollbar_x and rel_y >= self.HEADER_HEIGHT * zoom:
            return 'scrollbar'

        # Header row or side header column - always draggable/selectable
        if rel_y < self.HEADER_HEIGHT * zoom or rel_x < self.SIDE_HEADER_WIDTH * zoom:
            return 'component'

        # Memory cell area - only editable in simulation mode
        if simulation_mode and rel_x < scrollbar_x:
            scroll_offset = self._get_scroll_offset()
            display_row = int((rel_y - self.HEADER_HEIGHT * zoom) / (self.CELL_HEIGHT * zoom))
            col = int((rel_x - self.SIDE_HEADER_WIDTH * zoom) / (self.CELL_WIDTH * zoom))

            if 0 <= display_row < visible_rows and 0 <= col < self.COLUMNS:
                actual_row = scroll_offset + display_row
                address = actual_row * self.COLUMNS + col
                if address < self._get_memory_size():
                    return 'memory_cell'

        # In design mode, treat cell area as component (for selection/dragging)
        return 'component'

    def get_cell_at_position(self, canvas_x: float, canvas_y: float, zoom: float) -> Optional[int]:
        """Get the memory address of the cell at the given canvas position.
        
        Returns address if click is on a valid cell, None otherwise.
        Accounts for scroll offset.
        """
        cx, cy = self.get_position()
        visible_rows = self._get_visible_rows()
        scroll_offset = self._get_scroll_offset()
        
        viewer_width = (self.SIDE_HEADER_WIDTH + self.COLUMNS * self.CELL_WIDTH + self.SCROLLBAR_WIDTH) * zoom
        viewer_height = (self.HEADER_HEIGHT + visible_rows * self.CELL_HEIGHT) * zoom

        viewer_x = cx - (viewer_width / 2)
        viewer_y = cy - (viewer_height / 2)

        if not (viewer_x <= canvas_x <= viewer_x + viewer_width and
                viewer_y <= canvas_y <= viewer_y + viewer_height):
            return None

        rel_x = canvas_x - viewer_x
        rel_y = canvas_y - viewer_y

        if rel_y < self.HEADER_HEIGHT * zoom or rel_x < self.SIDE_HEADER_WIDTH * zoom:
            return None

        # Check scrollbar area
        scrollbar_x = viewer_width - (self.SCROLLBAR_WIDTH * zoom)
        if rel_x >= scrollbar_x:
            return None

        display_row = int((rel_y - self.HEADER_HEIGHT * zoom) / (self.CELL_HEIGHT * zoom))
        col = int((rel_x - self.SIDE_HEADER_WIDTH * zoom) / (self.CELL_WIDTH * zoom))

        if 0 <= display_row < visible_rows and 0 <= col < self.COLUMNS:
            actual_row = scroll_offset + display_row
            address = actual_row * self.COLUMNS + col
            if address < self._get_memory_size():
                return address

        return None
