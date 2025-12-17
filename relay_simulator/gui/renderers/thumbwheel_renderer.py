"""Thumbwheel renderer.

Draws a 3x3 grid-square body with three buttons:
- '+' (top)
- 'C' (middle)
- '-' (bottom)

This renderer is purely visual; simulation behavior is implemented in
components.thumbwheel.Thumbwheel.
"""

from __future__ import annotations

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class ThumbwheelRenderer(ComponentRenderer):
    GRID_SQUARE_PX = 20
    WIDTH_SQUARES = 3
    HEIGHT_SQUARES = 3

    def render(self, zoom: float = 1.0) -> None:
        self.clear()

        cx, cy = self.get_position()
        width = (self.WIDTH_SQUARES * self.GRID_SQUARE_PX) * zoom
        height = (self.HEIGHT_SQUARES * self.GRID_SQUARE_PX) * zoom

        x0 = cx - (width / 2)
        y0 = cy - (height / 2)

        fill_color = VSCodeTheme.BG_SECONDARY
        outline_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        outline_width = 3 if self.selected else 2

        tag = ('component', f'component_{self.component.component_id}')

        # Body
        self.draw_rectangle(
            x0,
            y0,
            width,
            height,
            fill=fill_color,
            outline=outline_color,
            width_px=outline_width,
            tags=tag,
        )

        # Button rows
        row_h = (self.GRID_SQUARE_PX * zoom)
        button_outline = VSCodeTheme.BORDER_DEFAULT
        text_color = VSCodeTheme.FG_PRIMARY

        labels = ['+', 'C', '-']
        for i, label in enumerate(labels):
            ry = y0 + (i * row_h)
            self.draw_rectangle(
                x0,
                ry,
                width,
                row_h,
                fill=VSCodeTheme.BG_TERTIARY,
                outline=button_outline,
                width_px=1,
                tags=tag,
            )
            self.draw_text(
                x0 + (width / 2),
                ry + (row_h / 2),
                label,
                fill=text_color,
                font=(VSCodeTheme.FONT_FAMILY_UI, int(VSCodeTheme.FONT_SIZE_LARGE * zoom), 'bold'),
                tags=tag,
            )
