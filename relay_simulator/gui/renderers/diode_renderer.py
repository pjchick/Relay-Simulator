"""Diode renderer.

Draws a simple diode symbol with two tabs:
- Left: Anode (A)
- Right: Cathode (K)

Supports rotation via the base renderer rotate_point handling.
"""

from __future__ import annotations

import tkinter as tk

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class DiodeRenderer(ComponentRenderer):
    """Renderer for Diode components."""

    WIDTH = 70
    HEIGHT = 30

    def _draw_polygon(self, points: list[tuple[float, float]], fill: str, outline: str, width_px: int, tags: tuple[str, ...]):
        cx, cy = self.get_position()
        rotation = self.get_rotation()

        transformed: list[float] = []
        for x, y in points:
            if rotation != 0:
                x, y = self.rotate_point(x, y, cx, cy, rotation)
            transformed.extend([x, y])

        item_id = self.canvas.create_polygon(
            *transformed,
            fill=fill,
            outline=outline,
            width=width_px,
            tags=tags,
        )
        self.canvas_items.append(item_id)

    def render(self, zoom: float = 1.0) -> None:
        self.clear()

        cx, cy = self.get_position()
        rotation = self.get_rotation()

        outline_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        outline_width = 3 if self.selected else 2

        # Label (position relative to canvas axes, not rotated)
        label = self.component.properties.get('label', '')
        if isinstance(label, str):
            label = label.strip()
        else:
            label = ''

        if label:
            label_pos = self.component.properties.get('label_position', 'bottom')

            # Account for 90/270 degree rotations swapping width/height
            if rotation in (0, 180):
                w = self.WIDTH * zoom
                h = self.HEIGHT * zoom
            else:
                w = self.HEIGHT * zoom
                h = self.WIDTH * zoom

            offset_h = (w / 2) + (20 * zoom)
            offset_v = (h / 2) + (20 * zoom)

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
                tags=('component_label', f'label_{self.component.component_id}')
            )

        # Geometry (in canvas coordinates)
        left_x = cx - 30 * zoom
        right_x = cx + 30 * zoom
        mid_y = cy

        # Diode body
        base_x = cx - 10 * zoom
        tip_x = cx + 10 * zoom
        tri_h = 12 * zoom

        # Lead from anode to triangle base
        self.draw_line(
            left_x,
            mid_y,
            base_x,
            mid_y,
            fill=outline_color,
            width_px=2,
            tags=('component', f'component_{self.component.component_id}'),
        )

        # Triangle
        self._draw_polygon(
            [
                (base_x, mid_y - tri_h),
                (base_x, mid_y + tri_h),
                (tip_x, mid_y),
            ],
            fill=VSCodeTheme.BG_SECONDARY,
            outline=outline_color,
            width_px=outline_width,
            tags=('component', f'component_{self.component.component_id}'),
        )

        # Cathode bar
        bar_x = cx + 14 * zoom
        bar_h = 14 * zoom
        self.draw_line(
            bar_x,
            mid_y - bar_h,
            bar_x,
            mid_y + bar_h,
            fill=outline_color,
            width_px=outline_width,
            tags=('component', f'component_{self.component.component_id}'),
        )

        # Lead from bar to cathode
        self.draw_line(
            bar_x,
            mid_y,
            right_x,
            mid_y,
            fill=outline_color,
            width_px=2,
            tags=('component', f'component_{self.component.component_id}'),
        )

        # Tabs
        self.draw_tabs(zoom)
