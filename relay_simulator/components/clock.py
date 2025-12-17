"""
Clock Component for Relay Logic Simulator

A user-controllable clock source.

Visual: 40px square with 4 tabs at 12, 3, 6, 9 o'clock positions (like a switch).
Behavior:
- Click in simulation mode toggles the clock ON/OFF.
- When ON, output pulses HIGH/FLOAT at the configured frequency (50% duty cycle).
- When OFF, output is FLOAT.
- If enabled on sim start, the clock starts pulsing when simulation starts.

Properties:
- frequency: One of ("4Hz", "2Hz", "1Hz", "2 sec", "4 sec", "8 sec")
- enable_on_sim_start: bool

Linking:
- Uses the standard Component.link_name attribute for cross-page links.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class Clock(Component):
    component_type = "Clock"

    # Match the Switch color presets (and related components).
    COLOR_PRESETS = {
        "red": {"on": (255, 0, 0), "dull": (128, 0, 0), "off": (64, 0, 0)},
        "green": {"on": (0, 255, 0), "dull": (0, 128, 0), "off": (0, 64, 0)},
        "blue": {"on": (0, 0, 255), "dull": (0, 0, 128), "off": (0, 0, 64)},
        "yellow": {"on": (255, 255, 0), "dull": (128, 128, 0), "off": (64, 64, 0)},
        "orange": {"on": (255, 165, 0), "dull": (128, 82, 0), "off": (64, 42, 0)},
        "white": {"on": (255, 255, 255), "dull": (128, 128, 128), "off": (64, 64, 64)},
        "amber": {"on": (255, 191, 0), "dull": (128, 96, 0), "off": (64, 48, 0)},
        "gray": {"on": (200, 200, 200), "dull": (128, 128, 128), "off": (64, 64, 64)},
    }

    FREQUENCY_OPTIONS = ("4Hz", "2Hz", "1Hz", "2 sec", "4 sec", "8 sec")

    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)

        self.properties.setdefault("label", "CLK")
        self.properties.setdefault("label_position", "bottom")
        self.properties.setdefault("color", "red")
        self.properties.setdefault("frequency", "1Hz")
        self.properties.setdefault("enable_on_sim_start", False)

        # Derived colors (kept in sync via set_color)
        if "on_color" not in self.properties or "off_color" not in self.properties or "dull_color" not in self.properties:
            self.set_color(str(self.properties.get("color", "red")))

        self._is_enabled: bool = False
        self._output_high: bool = False

        self._vnet_manager = None
        self._tick_callback = None

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._create_pin_and_tabs()

    def _create_pin_and_tabs(self) -> None:
        pin_id = f"{self.component_id}.pin1"
        pin = Pin(pin_id, self)

        radius = 20
        tab_positions = {
            "12": (0, -radius),
            "3": (radius, 0),
            "6": (0, radius),
            "9": (-radius, 0),
        }

        for position_name, (x, y) in tab_positions.items():
            tab_id = f"{pin_id}.tab{position_name}"
            tab = Tab(tab_id, pin, (x, y))
            pin.add_tab(tab)

        self.add_pin(pin)

    @staticmethod
    def _half_period_seconds(freq_value: str) -> float:
        value = (freq_value or "").strip()
        if value == "4Hz":
            return 0.125
        if value == "2Hz":
            return 0.25
        if value == "1Hz":
            return 0.5
        if value == "2 sec":
            return 1.0
        if value == "4 sec":
            return 2.0
        if value == "8 sec":
            return 4.0
        return 0.5

    def set_on_tick_callback(self, callback) -> None:
        """Set a callback to request the GUI/engine rerun simulation.

        Called by the SimulationEngine during initialization.
        """
        self._tick_callback = callback

    @staticmethod
    def _to_hex(color) -> str:
        """Convert (r,g,b) tuples/lists to '#rrggbb'. Pass through strings."""
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
        return "#2d2d2d"

    def set_color(self, color_name: str) -> None:
        """Set clock color from preset (same behavior as Switch)."""
        color_name = (color_name or "").strip().lower()
        if color_name in self.COLOR_PRESETS:
            self.properties["color"] = color_name
            self.properties["on_color"] = self.COLOR_PRESETS[color_name]["on"]
            self.properties["dull_color"] = self.COLOR_PRESETS[color_name]["dull"]
            self.properties["off_color"] = self.COLOR_PRESETS[color_name]["off"]

    def _apply_output_state(self) -> None:
        """Apply the current output state to the pin and mark its VNET dirty."""
        if not self._vnet_manager:
            return

        pin = next(iter(self.pins.values()), None)
        if not pin:
            return

        desired = PinState.HIGH if (self._is_enabled and self._output_high) else PinState.FLOAT

        if pin.state != desired:
            pin.set_state(desired)
            for tab in pin.tabs.values():
                try:
                    self._vnet_manager.mark_tab_dirty(tab.tab_id)
                except Exception:
                    pass

    def _ensure_thread_running(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_clock, name=f"Clock-{self.component_id}", daemon=True)
        self._thread.start()

    def _stop_thread(self) -> None:
        self._stop_event.set()

    def _run_clock(self) -> None:
        next_toggle = time.perf_counter()

        while not self._stop_event.is_set():
            if not self._is_enabled:
                time.sleep(0.05)
                next_toggle = time.perf_counter()
                continue

            half_period = self._half_period_seconds(self.properties.get("frequency", "1Hz"))
            now = time.perf_counter()
            if now >= next_toggle:
                self._output_high = not self._output_high
                self._apply_output_state()

                cb = self._tick_callback
                if cb:
                    try:
                        cb()
                    except Exception:
                        pass

                next_toggle = now + max(0.02, half_period)

            time.sleep(0.01)

    def simulate_logic(self, vnet_manager, bridge_manager=None):
        self._apply_output_state()

    def sim_start(self, vnet_manager, bridge_manager):
        self._vnet_manager = vnet_manager

        self._is_enabled = bool(self.properties.get("enable_on_sim_start", False))
        self._output_high = True if self._is_enabled else False

        self._apply_output_state()
        if self._is_enabled:
            self._ensure_thread_running()

    def sim_stop(self):
        self._is_enabled = False
        self._output_high = False
        self._stop_thread()
        self._vnet_manager = None

    def interact(self, action: str, params: Optional[Dict[str, Any]] = None) -> bool:
        if action not in ("toggle", "click", "press"):
            return False

        self._is_enabled = not self._is_enabled

        if self._is_enabled:
            self._output_high = True
            self._ensure_thread_running()
        else:
            self._output_high = False

        return True

    def get_visual_state(self) -> Dict[str, Any]:
        state = super().get_visual_state()
        state["clock_enabled"] = bool(self._is_enabled)
        state["clock_output"] = "HIGH" if (self._is_enabled and self._output_high) else "FLOAT"
        return state

    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        """Render the clock component.

        Note: the Tk GUI primarily uses renderer classes, but the base Component
        class requires a render() implementation.
        """
        x, y = self.position
        x += x_offset
        y += y_offset

        half = 20
        on_color = self._to_hex(self.properties.get("on_color", "#ff0000"))
        off_color = self._to_hex(self.properties.get("off_color", "#800000"))
        fill = on_color if (self._is_enabled and self._output_high) else off_color

        canvas_adapter.draw_rectangle(
            x - half,
            y - half,
            x + half,
            y + half,
            fill=fill,
            outline="#505050",
            width=2,
        )

        # Pulse symbol (square wave) in white
        pad = 8
        left = x - half + pad
        right = x + half - pad
        top = y - half + pad
        bottom = y + half - pad
        low_y = top + (bottom - top) * 0.65
        high_y = top + (bottom - top) * 0.35
        x1 = left + (right - left) * 0.35
        x2 = left + (right - left) * 0.70

        wave = "#ffffff"
        canvas_adapter.draw_line(left, low_y, x1, low_y, fill=wave, width=2)
        canvas_adapter.draw_line(x1, low_y, x1, high_y, fill=wave, width=2)
        canvas_adapter.draw_line(x1, high_y, x2, high_y, fill=wave, width=2)
        canvas_adapter.draw_line(x2, high_y, x2, low_y, fill=wave, width=2)
        canvas_adapter.draw_line(x2, low_y, right, low_y, fill=wave, width=2)

        # Draw tabs as small circles at 12/3/6/9.
        r = 20
        tab_positions = [
            (x, y - r),
            (x + r, y),
            (x, y + r),
            (x - r, y),
        ]
        for tx, ty in tab_positions:
            canvas_adapter.draw_circle(tx, ty, 3, fill="#808080", outline="#808080", width=1)

        label = self.properties.get("label", "")
        if label:
            label_pos = self.properties.get("label_position", "bottom")
            label_offset = 30
            if label_pos == "top":
                lx, ly, anchor = x, y - label_offset, "center"
            elif label_pos == "bottom":
                lx, ly, anchor = x, y + label_offset, "center"
            elif label_pos == "left":
                lx, ly, anchor = x - label_offset, y, "e"
            else:
                lx, ly, anchor = x + label_offset, y, "w"

            canvas_adapter.draw_text(lx, ly, label, fill="#cccccc", anchor=anchor)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Clock":
        clock = cls(data["component_id"], data.get("page_id", "page001"))

        if "position" in data:
            pos = data["position"]
            clock.position = (pos["x"], pos["y"])
        if "rotation" in data:
            clock.rotation = data["rotation"]
        if "link_name" in data:
            clock.link_name = data["link_name"]

        if "properties" in data and isinstance(data["properties"], dict):
            clock.properties.update(data["properties"])

            # Backward-compatibility: older files/UI may store link_name in properties.
            legacy_link = None
            try:
                legacy_link = clock.properties.pop('link_name', None)
            except Exception:
                legacy_link = None
            if (not clock.link_name) and isinstance(legacy_link, str) and legacy_link.strip():
                clock.link_name = legacy_link.strip()

            # Apply color presets if a color is set
            color = clock.properties.get('color', 'red')
            if color in cls.COLOR_PRESETS:
                clock.set_color(str(color))

        return clock
