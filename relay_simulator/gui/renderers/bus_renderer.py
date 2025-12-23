"""BUS component renderer.

Renders a simple vertical (or rotated) bus bar with a tab per pin.
The number of pins is dynamic (BUS.properties['number_of_pins']).

The BUS is passive; it exists to provide a convenient place to wire into
named links.
"""

from gui.renderers.base_renderer import ComponentRenderer
from gui.theme import VSCodeTheme


def _try_parse_bus_pin_index(pin_id: str) -> int:
    """Best-effort parse of BUS pin index from a pin_id like '{comp_id}.pin0'."""
    if not isinstance(pin_id, str):
        return 0
    marker = '.pin'
    if marker not in pin_id:
        return 0
    suffix = pin_id.split(marker, 1)[1]
    digits = ''
    for ch in suffix:
        if ch.isdigit():
            digits += ch
        else:
            break
    try:
        return int(digits) if digits else 0
    except Exception:
        return 0


class BUSRenderer(ComponentRenderer):
    """Renderer for BUS components."""

    # Keep geometry consistent with components.bus.BUS
    GRID_SQUARE_PX = 20
    BODY_WIDTH_PX = 20
    BODY_MARGIN_PX = 10

    def get_bounds(self, zoom: float = 1.0):
        """Return world-space bounds for selection hit testing (bus body only, no label)."""
        cx, cy = self.component.position
        rotation = int(getattr(self.component, 'rotation', 0) or 0) % 360
        
        pin_count = self._get_pin_count()
        span = (pin_count - 1) * self._get_pin_spacing_px()
        height = span + (2 * self.BODY_MARGIN_PX)
        width = self.BODY_WIDTH_PX
        
        # Account for rotation swapping width/height
        if rotation in (90, 270):
            half_w = height / 2
            half_h = width / 2
        else:
            half_w = width / 2
            half_h = height / 2
        
        return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)

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
        spacing = max(1, min(20, spacing))
        return self.GRID_SQUARE_PX * spacing

    def _get_label(self) -> str:
        label = self.component.properties.get('label', '')
        return label if isinstance(label, str) else ''

    def _get_first_tab_relative_position(self):
        """Return the relative (dx, dy) of the first BUS tab (pin0)."""
        if not getattr(self.component, 'pins', None):
            return None

        # Prefer stable ordering by parsing the numeric index from pin_id.
        pins = list(self.component.pins.values())
        if not pins:
            return None

        pins_sorted = sorted(pins, key=lambda p: _try_parse_bus_pin_index(getattr(p, 'pin_id', '')))
        first_pin = pins_sorted[0]
        if not getattr(first_pin, 'tabs', None):
            return None

        # BUS pins are expected to have exactly one tab.
        first_tab = next(iter(first_pin.tabs.values()), None)
        if not first_tab:
            return None
        return first_tab.relative_position

    def _draw_first_pin_box(self, zoom: float, outline_color: str) -> None:
        """Draw a small outline box around the first BUS pin/tab."""
        rel = self._get_first_tab_relative_position()
        if not rel:
            return

        cx, cy = self.get_position()
        tab_dx, tab_dy = rel

        # Tab.relative_position is defined in unzoomed (world) coordinates.
        # Apply zoom so the marker stays aligned with the rendered tabs/body.
        tab_dx *= zoom
        tab_dy *= zoom

        # Use unrotated coordinates; draw_rectangle applies component rotation.
        tab_x = cx + tab_dx
        tab_y = cy + tab_dy

        tab_size = VSCodeTheme.TAB_SIZE * zoom
        box_size = max(tab_size + (4 * zoom), tab_size * 1.6)
        x = tab_x - (box_size / 2)
        y = tab_y - (box_size / 2)

        self.draw_rectangle(
            x,
            y,
            box_size,
            box_size,
            fill='',
            outline=outline_color,
            width_px=max(1, int(round(2 * zoom))),
            tags=('tab', 'bus_first_pin', f'component_{self.component.component_id}')
        )

    def render(self, zoom: float = 1.0) -> None:
        # Clear previous rendering
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

        # Label: use the standard "Label" property (not bus_name), and keep it
        # canvas-aligned (not rotated with the component). Offsets adapt to
        # vertical/horizontal orientation like RelayRenderer.
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

        # Tabs
        self.draw_tabs(zoom)

        # Identify the first pin (pin0) with a small box marker.
        self._draw_first_pin_box(zoom=zoom, outline_color=outline_color)
