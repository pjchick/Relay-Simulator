"""Seven Segment Display renderer.

Renders a 7-segment digit inside a 3x4 grid-square body.
The digit is driven by 4 linked bus lines named:
  {bus_name}_{start_pin + bit}

Bit order: bit0 is LSB.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme
from core.state import PinState


class SevenSegmentDisplayRenderer(ComponentRenderer):
    """Renderer for SevenSegmentDisplay components."""

    GRID_SQUARE_PX = 20
    WIDTH_SQUARES = 3
    HEIGHT_SQUARES = 4

    # segment names: a(top), b(upper-right), c(lower-right), d(bottom),
    # e(lower-left), f(upper-left), g(middle)
    _SEGMENTS_FOR_VALUE: Dict[int, Iterable[str]] = {
        0x0: ("a", "b", "c", "d", "e", "f"),
        0x1: ("b", "c"),
        0x2: ("a", "b", "g", "e", "d"),
        0x3: ("a", "b", "c", "d", "g"),
        0x4: ("f", "g", "b", "c"),
        0x5: ("a", "f", "g", "c", "d"),
        0x6: ("a", "f", "e", "d", "c", "g"),
        0x7: ("a", "b", "c"),
        0x8: ("a", "b", "c", "d", "e", "f", "g"),
        0x9: ("a", "b", "c", "d", "f", "g"),
        0xA: ("a", "b", "c", "e", "f", "g"),
        0xB: ("f", "e", "d", "c", "g"),
        0xC: ("a", "f", "e", "d"),
        0xD: ("b", "c", "d", "e", "g"),
        0xE: ("a", "f", "g", "e", "d"),
        0xF: ("a", "f", "g", "e"),
    }

    def _get_on_color(self) -> str:
        """Return the segment ON color based on the component's `color` property."""
        props = getattr(self.component, 'properties', {})
        color_name = None
        if isinstance(props, dict):
            color_name = props.get('color')

        if not isinstance(color_name, str):
            color_name = 'green'
        color_name = color_name.strip().lower()

        # Map to existing theme palette (no custom colors).
        if color_name == 'red':
            return VSCodeTheme.ACCENT_RED
        if color_name == 'green':
            return VSCodeTheme.ACCENT_GREEN
        if color_name == 'blue':
            return VSCodeTheme.ACCENT_BLUE
        if color_name == 'orange':
            return VSCodeTheme.ACCENT_ORANGE
        if color_name in ('yellow', 'amber'):
            return VSCodeTheme.ACCENT_ORANGE
        if color_name == 'white':
            return VSCodeTheme.FG_BRIGHT

        return VSCodeTheme.WIRE_POWERED

    def _read_link_state(self, link_name: str) -> bool:
        """Read a link state from the simulation engine (True if HIGH)."""
        engine = getattr(self, 'simulation_engine', None)
        if not engine:
            return False

        vnets = getattr(engine, 'vnets', None)
        if not isinstance(vnets, dict):
            return False

        # If any VNET carrying this link is HIGH, treat as 1.
        for vnet in vnets.values():
            try:
                if not vnet.has_link(link_name):
                    continue

                state = getattr(vnet, 'state', None)
                # VNET.state is a PinState (HIGH or FLOAT). Enums are always truthy,
                # so compare explicitly.
                if state == PinState.HIGH:
                    return True
                # Be defensive: some future implementations may store bool/int.
                if state is True or state == 1:
                    return True
            except Exception:
                continue

        return False

    def _read_input_value(self) -> int:
        """Compute the 4-bit input value from bus links."""
        get_links = getattr(self.component, 'get_nibble_link_names', None)
        if not callable(get_links):
            return 0

        link_names = get_links()
        if not isinstance(link_names, list) or len(link_names) != 4:
            return 0

        value = 0
        for bit_index, link_name in enumerate(link_names):
            if isinstance(link_name, str) and link_name.strip():
                if self._read_link_state(link_name.strip()):
                    value |= (1 << bit_index)

        return value & 0xF

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

        # Body
        self.draw_rectangle(
            x0,
            y0,
            width,
            height,
            fill=fill_color,
            outline=outline_color,
            width_px=outline_width,
            tags=('component', f'component_{self.component.component_id}')
        )

        value = self._read_input_value()
        segments_on = set(self._SEGMENTS_FOR_VALUE.get(value, ()))

        # Segment styling (reuse theme colors; no new palette)
        on_color = self._get_on_color()
        off_color = VSCodeTheme.COMPONENT_OUTLINE

        # Geometry within the body
        pad = 6 * zoom
        thickness = max(2 * zoom, 4 * zoom)
        inner_w = max(1.0, width - (2 * pad))
        inner_h = max(1.0, height - (2 * pad))

        # vertical segment height ensures 3 horizontal segments fit: top/mid/bottom
        vert_h = max(1.0, (inner_h - (3 * thickness)) / 2)

        def seg_fill(name: str) -> str:
            return on_color if name in segments_on else off_color

        # a
        self.draw_rectangle(
            x0 + pad + (thickness / 2),
            y0 + pad,
            inner_w - thickness,
            thickness,
            fill=seg_fill('a'),
            outline=seg_fill('a'),
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )

        # g
        self.draw_rectangle(
            x0 + pad + (thickness / 2),
            y0 + pad + vert_h + thickness,
            inner_w - thickness,
            thickness,
            fill=seg_fill('g'),
            outline=seg_fill('g'),
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )

        # d
        self.draw_rectangle(
            x0 + pad + (thickness / 2),
            y0 + pad + (2 * vert_h) + (2 * thickness),
            inner_w - thickness,
            thickness,
            fill=seg_fill('d'),
            outline=seg_fill('d'),
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )

        # f (upper-left)
        self.draw_rectangle(
            x0 + pad,
            y0 + pad + thickness,
            thickness,
            vert_h,
            fill=seg_fill('f'),
            outline=seg_fill('f'),
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )

        # b (upper-right)
        self.draw_rectangle(
            x0 + pad + inner_w - thickness,
            y0 + pad + thickness,
            thickness,
            vert_h,
            fill=seg_fill('b'),
            outline=seg_fill('b'),
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )

        # e (lower-left)
        self.draw_rectangle(
            x0 + pad,
            y0 + pad + (2 * thickness) + vert_h,
            thickness,
            vert_h,
            fill=seg_fill('e'),
            outline=seg_fill('e'),
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )

        # c (lower-right)
        self.draw_rectangle(
            x0 + pad + inner_w - thickness,
            y0 + pad + (2 * thickness) + vert_h,
            thickness,
            vert_h,
            fill=seg_fill('c'),
            outline=seg_fill('c'),
            width_px=1,
            tags=('component', f'component_{self.component.component_id}')
        )
