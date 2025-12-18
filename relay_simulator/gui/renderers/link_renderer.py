"""Renderer for Link component."""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class LinkRenderer(ComponentRenderer):
    """Renderer for Link components.

    Visual:
    - Small rectangle (30x10)
    - Turns green when powered (any connected VNET HIGH)
    - Displays the standard component label (if set)
    - Single tab (drawn via base draw_tabs)
    """

    WIDTH_PX = 30
    HEIGHT_PX = 10

    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing."""
        cx, cy = self.component.position
        half_w = self.WIDTH_PX / 2
        half_h = self.HEIGHT_PX / 2

        rot = int(getattr(self.component, 'rotation', 0) or 0) % 360
        if rot in (90, 270):
            half_w, half_h = half_h, half_w

        return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)

    def render(self, zoom: float = 1.0) -> None:
        self.clear()

        cx, cy = self.get_position()
        rotation = self.get_rotation()
        w = self.WIDTH_PX * zoom
        h = self.HEIGHT_PX * zoom

        x = cx - (w / 2)
        y = cy - (h / 2)

        fill_color = VSCodeTheme.ACCENT_GREEN if self.powered else VSCodeTheme.COMPONENT_FILL
        outline_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        outline_width = 3 if self.selected else 2

        self.draw_rectangle(
            x,
            y,
            w,
            h,
            fill=fill_color,
            outline=outline_color,
            width_px=outline_width,
            tags=("component", f"component_{self.component.component_id}"),
        )

        # Label: use standard Label property (not link_name), and keep it canvas-aligned.
        label = self.component.properties.get('label', '')
        if isinstance(label, str):
            label = label.strip()
        else:
            label = ''

        if label:
            label_pos = self.component.properties.get('label_position', 'bottom')

            # Account for 90/270 degree rotations swapping width/height.
            if rotation in (0, 180):
                bbox_w = w
                bbox_h = h
            else:
                bbox_w = h
                bbox_h = w

            margin = 20 * zoom
            offset_h = (bbox_w / 2) + margin
            offset_v = (bbox_h / 2) + margin

            if label_pos == 'top':
                label_x, label_y = cx, cy - offset_v
                anchor = 's'
            elif label_pos == 'bottom':
                label_x, label_y = cx, cy + offset_v
                anchor = 'n'
            elif label_pos == 'left':
                label_x, label_y = cx - offset_h, cy
                anchor = 'e'
            else:  # right
                label_x, label_y = cx + offset_h, cy
                anchor = 'w'

            self.draw_text(
                label_x,
                label_y,
                text=label,
                font_size=12,
                fill='#a0a0a0',
                anchor=anchor,
                tags=("component_label", f"label_{self.component.component_id}"),
            )

        self.draw_tabs(zoom)
