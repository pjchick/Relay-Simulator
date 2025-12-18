"""Bus Display renderer.

Renders a BUS-like body with small circular indicators (10px diameter)
representing the state of each bus bit.

Each indicator reads the link state:
  {bus_name}_{start_pin + i}

The component is pinless; it is purely visual.
"""

from __future__ import annotations

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme
from core.state import PinState


class BusDisplayRenderer(ComponentRenderer):
    """Renderer for BusDisplay components."""

    GRID_SQUARE_PX = 20
    BODY_WIDTH_PX = 20
    BODY_MARGIN_PX = 10

    INDICATOR_DIAMETER_PX = 10

    def _get_pin_count(self) -> int:
        try:
            count = int(self.component.properties.get('number_of_pins', 1))
        except Exception:
            count = 1
        return max(1, count)

    def _get_pin_spacing_px(self) -> int:
        try:
            spacing = int(self.component.properties.get('pin_spacing', 1))
        except Exception:
            spacing = 1
        spacing = max(1, min(15, spacing))
        return self.GRID_SQUARE_PX * spacing

    def _get_bus_name(self) -> str:
        name = self.component.properties.get('bus_name', '')
        if not isinstance(name, str):
            return ''
        return name.strip()

    def _get_start_pin(self) -> int:
        try:
            return int(self.component.properties.get('start_pin', 0))
        except Exception:
            return 0

    def _get_label(self) -> str:
        label = self.component.properties.get('label', '')
        return label if isinstance(label, str) else ''

    def _read_link_state(self, link_name: str) -> bool:
        """Read a link state from the simulation engine (True if HIGH)."""
        engine = getattr(self, 'simulation_engine', None)
        if not engine:
            return False

        vnets = getattr(engine, 'vnets', None)
        if not isinstance(vnets, dict):
            return False

        for vnet in vnets.values():
            try:
                if not vnet.has_link(link_name):
                    continue

                state = getattr(vnet, 'state', None)
                if state == PinState.HIGH:
                    return True
                if state is True or state == 1:
                    return True
            except Exception:
                continue

        return False

    def render(self, zoom: float = 1.0) -> None:
        self.clear()

        cx, cy = self.get_position()
        rotation = self.get_rotation()

        pin_count = self._get_pin_count()
        span = (pin_count - 1) * self._get_pin_spacing_px()
        height = (span + (2 * self.BODY_MARGIN_PX)) * zoom
        width = self.BODY_WIDTH_PX * zoom

        x = cx - (width / 2)
        y = cy - (height / 2)

        fill_color = VSCodeTheme.BG_SECONDARY
        outline_color = VSCodeTheme.COMPONENT_SELECTED if self.selected else VSCodeTheme.COMPONENT_OUTLINE
        outline_width = 3 if self.selected else 2

        # Body
        self.draw_rectangle(
            x,
            y,
            width,
            height,
            fill=fill_color,
            outline=outline_color,
            width_px=outline_width,
            tags=('component', f'component_{self.component.component_id}')
        )

        # Label (canvas-aligned, not rotated)
        label = self._get_label().strip()
        if label:
            label_pos = self.component.properties.get('label_position', 'bottom')

            if rotation in (0, 180):
                bbox_w = width
                bbox_h = height
            else:
                bbox_w = height
                bbox_h = width

            margin = 20 * zoom
            offset_v = (bbox_h / 2) + margin
            offset_h = (bbox_w / 2) + margin

            if label_pos == 'top':
                label_x, label_y = cx, cy - offset_v
                anchor = 'center'
            elif label_pos == 'bottom':
                label_x, label_y = cx, cy + offset_v
                anchor = 'center'
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

        # Indicators
        bus_name = self._get_bus_name()
        start_pin = self._get_start_pin()

        spacing_px = self._get_pin_spacing_px()
        start_y = -(span / 2) * zoom
        radius = (self.INDICATOR_DIAMETER_PX / 2) * zoom

        off_fill = VSCodeTheme.INDICATOR_OFF
        on_fill = VSCodeTheme.INDICATOR_ON

        for i in range(pin_count):
            link_name = f"{bus_name}_{start_pin + i}" if bus_name else ""
            is_on = self._read_link_state(link_name) if link_name else False

            dx = 0
            dy = start_y + (i * spacing_px * zoom)

            # Rotate indicator position with component.
            px, py = (cx + dx, cy + dy)
            if rotation != 0:
                px, py = self.rotate_point(px, py, cx, cy, rotation)

            self.draw_circle(
                px,
                py,
                radius=radius,
                fill=(on_fill if is_on else off_fill),
                outline=outline_color,
                width_px=max(1, int(round(1 * zoom))),
                tags=('component', f'component_{self.component.component_id}', 'bus_display_indicator')
            )
