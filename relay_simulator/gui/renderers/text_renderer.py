"""Renderer for Text component."""

import tkinter as tk
from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class TextRenderer(ComponentRenderer):
    """Renderer for Text annotation components.

    Visual:
    - Multi-line text support
    - Fixed-width console font (Consolas/Courier New)
    - Configurable font size and color
    - Left or right justification
    - Semi-transparent background box when selected
    """

    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing."""
        cx, cy = self.component.position
        width = self.component.properties.get('width', 200)
        height = self.component.properties.get('height', 40)
        
        half_w = width / 2
        half_h = height / 2

        return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)

    def render(self, zoom: float = 1.0) -> None:
        """Render the text component."""
        self.clear()

        cx, cy = self.get_position()
        
        # Get properties
        text = self.component.properties.get('text', 'Text')
        font_size = int(self.component.properties.get('font_size', 12) * zoom)
        color = self.component.properties.get('color', '#FFFFFF')
        multiline = self.component.properties.get('multiline', False)
        justify = self.component.properties.get('justify', 'left')
        width = self.component.properties.get('width', 200) * zoom
        height = self.component.properties.get('height', 40) * zoom
        show_border = self.component.properties.get('border', False)

        # Fixed-width font (Consolas preferred, fallback to Courier)
        font = ('Consolas', font_size) if self._font_exists('Consolas') else ('Courier', font_size)

        # Calculate bounding box
        x1 = cx - (width / 2)
        y1 = cy - (height / 2)
        x2 = cx + (width / 2)
        y2 = cy + (height / 2)

        # Draw border if enabled or if selected
        if show_border or self.selected:
            border_color = color if show_border else VSCodeTheme.ACCENT_BLUE
            border_width = 1 if show_border else 2
            bg_fill = '' if not self.selected else VSCodeTheme.BG_HOVER
            
            border_item = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=border_color,
                width=border_width,
                fill=bg_fill,
                stipple='gray50' if self.selected and not show_border else '',
                tags=("component", f"component_{self.component.component_id}")
            )
            self.canvas_items.append(border_item)

        # Determine text anchor based on justification
        if justify == 'right':
            anchor = tk.E
            text_x = cx + (width / 2) - (5 * zoom)  # Small padding from edge
        else:  # left
            anchor = tk.W
            text_x = cx - (width / 2) + (5 * zoom)  # Small padding from edge

        # Draw text
        if multiline:
            text_item = self.canvas.create_text(
                text_x, cy,
                text=text,
                font=font,
                fill=color,
                anchor=anchor,
                width=width - (10 * zoom),  # Account for padding
                justify=tk.LEFT if justify == 'left' else tk.RIGHT,
                tags=("component", f"component_{self.component.component_id}")
            )
        else:
            text_item = self.canvas.create_text(
                text_x, cy,
                text=text,
                font=font,
                fill=color,
                anchor=anchor,
                tags=("component", f"component_{self.component.component_id}")
            )
        
        self.canvas_items.append(text_item)

        # Draw resize handles when selected
        if self.selected:
            handle_size = 6 * zoom
            handles = [
                (x1, y1, 'nw'),  # Top-left
                (x2, y1, 'ne'),  # Top-right
                (x1, y2, 'sw'),  # Bottom-left
                (x2, y2, 'se'),  # Bottom-right
            ]
            
            for hx, hy, corner in handles:
                handle = self.canvas.create_rectangle(
                    hx - handle_size/2, hy - handle_size/2,
                    hx + handle_size/2, hy + handle_size/2,
                    fill=VSCodeTheme.ACCENT_BLUE,
                    outline='white',
                    width=1,
                    tags=("resize_handle", f"resize_handle_{self.component.component_id}", f"corner_{corner}")
                )
                self.canvas_items.append(handle)

    def _font_exists(self, font_name: str) -> bool:
        """Check if a font exists on the system."""
        try:
            import tkinter.font as tkfont
            available_fonts = tkfont.families()
            return font_name in available_fonts
        except:
            return False
