"""Clock component renderer.

Renders a 40px square clock source with tabs at 12/3/6/9.
Fill color indicates current output (HIGH vs FLOAT) when enabled.
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


class ClockRenderer(ComponentRenderer):
    SIZE = 40

    @staticmethod
    def _to_hex(color) -> str:
        """Convert (r,g,b) or [r,g,b] to '#rrggbb'. Pass through hex strings."""
        if isinstance(color, str):
            return color
        if isinstance(color, (tuple, list)) and len(color) >= 3:
            try:
                r, g, b = int(color[0]), int(color[1]), int(color[2])
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                return f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                pass
        return VSCodeTheme.COMPONENT_FILL

    def render(self, zoom: float = 1.0) -> None:
        self.clear()

        cx, cy = self.get_position()
        half = (self.SIZE / 2) * zoom

        enabled = bool(getattr(self.component, "_is_enabled", False))
        output_high = bool(getattr(self.component, "_output_high", False))

        on_color = self._to_hex(self.component.properties.get('on_color', VSCodeTheme.SWITCH_ON))
        off_color = self._to_hex(self.component.properties.get('off_color', VSCodeTheme.SWITCH_OFF))

        # Match switch-like behavior: ON uses on_color; otherwise use off_color.
        fill_color = on_color if (enabled and output_high) else off_color

        outline_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        outline_width = 3 if self.selected else 2

        self.draw_rectangle(
            cx - half,
            cy - half,
            width=2 * half,
            height=2 * half,
            fill=fill_color,
            outline=outline_color,
            width_px=outline_width,
            tags=("component", f"component_{self.component.component_id}"),
        )

        # Pulse symbol (square wave) on the face
        pad = 8 * zoom
        left = cx - half + pad
        right = cx + half - pad
        top = cy - half + pad
        bottom = cy + half - pad
        width_px = max(1, int(2 * zoom))

        low_y = top + (bottom - top) * 0.65
        high_y = top + (bottom - top) * 0.35
        x1 = left + (right - left) * 0.35
        x2 = left + (right - left) * 0.70

        wave_color = VSCodeTheme.FG_BRIGHT
        self.draw_line(left, low_y, x1, low_y, fill=wave_color, width_px=width_px, tags=("clock_wave",))
        self.draw_line(x1, low_y, x1, high_y, fill=wave_color, width_px=width_px, tags=("clock_wave",))
        self.draw_line(x1, high_y, x2, high_y, fill=wave_color, width_px=width_px, tags=("clock_wave",))
        self.draw_line(x2, high_y, x2, low_y, fill=wave_color, width_px=width_px, tags=("clock_wave",))
        self.draw_line(x2, low_y, right, low_y, fill=wave_color, width_px=width_px, tags=("clock_wave",))

        label = self.component.properties.get("label", "CLK")
        label_position = self.component.properties.get("label_position", "bottom")

        label_offset = (half + 15) * zoom
        label_x = cx
        label_y = cy
        anchor = "center"

        if label_position == "bottom":
            label_y = cy + label_offset
            anchor = "n"
        elif label_position == "top":
            label_y = cy - label_offset
            anchor = "s"
        elif label_position == "left":
            label_x = cx - label_offset
            anchor = "e"
        elif label_position == "right":
            label_x = cx + label_offset
            anchor = "w"

        if label:
            self.draw_text(
                label_x,
                label_y,
                text=label,
                anchor=anchor,
                tags=("component_label", f"label_{self.component.component_id}"),
            )

        self.draw_tabs(zoom)
