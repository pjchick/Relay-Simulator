"""Renderer for Box component."""

import tkinter as tk
from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class BoxRenderer(ComponentRenderer):
    """Renderer for Box annotation components.

    Visual:
    - Rectangular outline with configurable color
    - Optional fill with 75% transparency
    - Rendered on bottom layer (beneath all other components)
    - Resize handles when selected
    """

    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing."""
        cx, cy = self.component.position
        width = self.component.properties.get('width', 200)
        height = self.component.properties.get('height', 150)
        
        half_w = width / 2
        half_h = height / 2

        return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)

    def render(self, zoom: float = 1.0) -> None:
        """Render the box component."""
        self.clear()

        cx, cy = self.get_position()
        
        # Get properties
        color = self.component.properties.get('color', '#FFFFFF')
        width = self.component.properties.get('width', 200) * zoom
        height = self.component.properties.get('height', 150) * zoom
        filled = self.component.properties.get('filled', False)

        # Calculate bounding box
        x1 = cx - (width / 2)
        y1 = cy - (height / 2)
        x2 = cx + (width / 2)
        y2 = cy + (height / 2)

        # Determine fill
        if filled:
            # Create a very dark shade of the border color for the fill
            fill_color = self._darken_color(color, 0.7)  # 70% darker
        else:
            fill_color = ''

        # Draw box rectangle
        box_item = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=color,
            width=2,
            fill=fill_color,
            tags=("component", f"component_{self.component.component_id}")
        )
        self.canvas_items.append(box_item)
        
        # Position box just above grid (below all other components)
        # First lower it to the bottom, then raise it above the grid
        self.canvas.tag_lower(f"component_{self.component.component_id}")
        try:
            self.canvas.tag_raise(f"component_{self.component.component_id}", "grid")
        except:
            # If grid doesn't exist yet, just keep it at the bottom
            pass

        # Draw selection overlay if selected
        if self.selected:
            selection_item = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=VSCodeTheme.ACCENT_BLUE,
                width=2,
                dash=(5, 5),
                fill='',
                tags=("component", f"component_{self.component.component_id}")
            )
            self.canvas_items.append(selection_item)

            # Draw resize handles at corners
            handle_size = 6
            corners = {
                'nw': (x1, y1),
                'ne': (x2, y1),
                'sw': (x1, y2),
                'se': (x2, y2)
            }

            for corner_name, (hx, hy) in corners.items():
                handle = self.canvas.create_rectangle(
                    hx - handle_size/2, hy - handle_size/2,
                    hx + handle_size/2, hy + handle_size/2,
                    fill=VSCodeTheme.ACCENT_BLUE,
                    outline=VSCodeTheme.ACCENT_BLUE,
                    tags=("resize_handle", f"resize_handle_{self.component.component_id}", f"corner_{corner_name}")
                )
                self.canvas_items.append(handle)

    def _darken_color(self, color: str, amount: float) -> str:
        """Darken a hex color by moving it closer to black.
        
        Args:
            color: Hex color string (e.g., '#FF0000')
            amount: Amount to darken (0-1), where 1 is black
            
        Returns:
            Darkened hex color string
        """
        # Remove '#' if present
        if color.startswith('#'):
            color = color[1:]
        
        # Convert hex to RGB
        try:
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
        except (ValueError, IndexError):
            # If parsing fails, return black
            return '#000000'
        
        # Darken by interpolating towards black (0, 0, 0)
        r = int(r * (1 - amount))
        g = int(g * (1 - amount))
        b = int(b * (1 - amount))
        
        # Clamp values to 0-255
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        # Convert back to hex
        return f'#{r:02X}{g:02X}{b:02X}'

    def _lighten_color(self, color: str, amount: float) -> str:
        """Lighten a hex color by moving it closer to white.
        
        Args:
            color: Hex color string (e.g., '#FF0000')
            amount: Amount to lighten (0-1), where 1 is white
            
        Returns:
            Lightened hex color string
        """
        # Remove '#' if present
        if color.startswith('#'):
            color = color[1:]
        
        # Convert hex to RGB
        try:
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
        except (ValueError, IndexError):
            # If parsing fails, return white
            return '#FFFFFF'
        
        # Lighten by interpolating towards white (255, 255, 255)
        r = int(r + (255 - r) * amount)
        g = int(g + (255 - g) * amount)
        b = int(b + (255 - b) * amount)
        
        # Clamp values to 0-255
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        # Convert back to hex
        return f'#{r:02X}{g:02X}{b:02X}'

    def _get_transparent_color(self, color: str, alpha: float) -> str:
        """Get a stippled fill color to simulate transparency.
        
        Args:
            color: Hex color string
            alpha: Alpha value (0-1) - ignored, uses stipple pattern instead
            
        Returns:
            Color string (Tkinter doesn't support true alpha, so we return the base color
            and use stipple pattern for transparency effect)
        """
        return color

    def _font_exists(self, font_name: str) -> bool:
        """Check if a font exists."""
        try:
            import tkinter.font as tkfont
            return font_name in tkfont.families()
        except Exception:
            return False
