"""Memory Component.

A RAM memory component with:
- Configurable address space (3-16 bits)
- Configurable byte size (1-16 bits)
- Address and Data buses (linked by name)
- Enable, Read, Write control pins
- Memory viewer/editor grid (16 addresses wide)
- File load/save capability
- Auto-load from default file on simulation start

Properties:
- address_bits: Address space size in bits (3-16)
- data_bits: Byte/word size in bits (1-16)
- address_bus_name: Name of the address bus
- data_bus_name: Name of the data bus
- default_memory_file: Optional default file to load on sim start
"""

from __future__ import annotations

import os
from typing import Dict, Any, Optional

from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class Memory(Component):
    """Memory component - RAM with bus interface and viewer."""

    component_type = "Memory"

    # Geometry
    GRID_SQUARE_PX = 20
    VIEWER_WIDTH_PX = 640  # 16 cells * 40px
    VIEWER_HEIGHT_PX = 320  # Default height for viewer
    PIN_OFFSET_X = -440  # Pins on left side
    PIN_SPACING = 70     # Vertical spacing between pins

    def _debug_enabled(self) -> bool:
        return os.getenv('RSIM_DEBUG_MEMORY', '').strip().lower() in (
            '1', 'true', 'yes', 'y', 'on'
        )

    def _debug(self, message: str) -> None:
        """Emit debug output if RSIM_DEBUG_MEMORY is enabled.

        If RSIM_DEBUG_MEMORY_FILE is set, append logs to that file.
        Otherwise, print to stdout with flushing.
        """
        if not self._debug_enabled():
            return

        try:
            path = os.getenv('RSIM_DEBUG_MEMORY_FILE', '').strip()
            if path:
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(message + "\n")
                return
        except Exception:
            # Fall back to stdout
            pass

        try:
            print(message, flush=True)
        except Exception:
            pass

    def _read_input_pin_high(self, vnet_manager, pin: Optional[Pin]) -> bool:
        """Read a passive input pin by looking at its VNET state.

        In this simulator architecture, VNETs are evaluated from tab/pin outputs,
        but pins are not automatically driven from VNET state (StatePropagator
        intentionally doesn't push VNET -> pin). Passive inputs must therefore
        read their connected VNET state explicitly.
        """
        if not vnet_manager or not pin or not pin.tabs:
            return False

        try:
            tab = next(iter(pin.tabs.values()))
        except Exception:
            return False

        try:
            vnet = vnet_manager.get_vnet_for_tab(tab.tab_id)
        except Exception:
            vnet = None

        state = getattr(vnet, 'state', None) if vnet else None
        return state == PinState.HIGH or state is True or state == 1

    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)

        self.properties = {
            'address_bits': 8,      # 3-16 bits
            'data_bits': 8,         # 1-16 bits
            'address_bus_name': 'ADDR',
            'data_bus_name': 'DATA',
            'default_memory_file': '',  # Optional file path
            'is_volatile': False,        # If True, clears on sim start and not saved to .rsim
            'label': 'RAM',
            'label_position': 'top',
            'visible_rows': 16,     # Number of rows visible in viewer (resizable)
        }

        # Memory storage: dict[address: int] -> value: int
        # Only stores non-zero values to save memory
        self.memory: Dict[int, int] = {}

        # Viewer state
        self.scroll_offset = 0  # Row offset for scrolling

        # Current operation state (for visualization)
        self.last_operation = None  # 'read', 'write', or None
        self.last_address = None
        self.last_data = None

        self._rebuild_pins()

    def _get_address_bits(self) -> int:
        try:
            bits = int(self.properties.get('address_bits', 8))
        except Exception:
            bits = 8
        return max(3, min(16, bits))

    def _get_data_bits(self) -> int:
        try:
            bits = int(self.properties.get('data_bits', 8))
        except Exception:
            bits = 8
        return max(1, min(16, bits))

    def _get_address_bus_name(self) -> str:
        name = self.properties.get('address_bus_name', '')
        if not isinstance(name, str):
            return ''
        return name.strip()

    def _get_data_bus_name(self) -> str:
        name = self.properties.get('data_bus_name', '')
        if not isinstance(name, str):
            return ''
        return name.strip()

    def _get_default_memory_file(self) -> str:
        path = self.properties.get('default_memory_file', '')
        if not isinstance(path, str):
            return ''
        return path.strip()

    def _is_volatile(self) -> bool:
        """Whether this memory is volatile.

        - If True: memory contents are cleared on every sim_start and are NOT
          persisted into the .rsim file.
        - If False: memory contents are persisted in the .rsim file.
        """
        value = self.properties.get('is_volatile', False)
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in ('1', 'true', 'yes', 'y', 'on')
        return False

    @property
    def memory_size(self) -> int:
        """Total number of addressable locations."""
        return 1 << self._get_address_bits()

    @property
    def max_value(self) -> int:
        """Maximum value that can be stored (based on data_bits)."""
        return (1 << self._get_data_bits()) - 1

    def _rebuild_pins(self) -> None:
        """Create the control pins (Enable, Read, Write) and data bus pins."""
        self.pins.clear()

        # Control pin positions (relative to component center, on left side)
        control_pins = [
            ('Enable', 0),
            ('Read', 1),
            ('Write', 2),
        ]

        for pin_name, index in control_pins:
            pin_id = f"{self.component_id}.{pin_name}"
            pin = Pin(pin_id, self)

            tab_id = f"{pin_id}.tab"
            # Control pins stacked vertically on left side
            tab_x = self.PIN_OFFSET_X
            tab_y = -40 + (index * self.PIN_SPACING)
            tab = Tab(tab_id, pin, (tab_x, tab_y))
            pin.add_tab(tab)
            self.add_pin(pin)

        # Create data bus pins (right side, stacked vertically)
        data_bits = self._get_data_bits()
        data_pin_spacing = 20  # Closer spacing for data pins
        data_start_y = -(data_bits - 1) * data_pin_spacing // 2
        data_pin_x = 360  # Right side of memory viewer

        for bit_index in range(data_bits):
            pin_id = f"{self.component_id}.DATA_{bit_index}"
            pin = Pin(pin_id, self)

            tab_id = f"{pin_id}.tab"
            tab_x = data_pin_x
            tab_y = data_start_y + (bit_index * data_pin_spacing)
            tab = Tab(tab_id, pin, (tab_x, tab_y))
            pin.add_tab(tab)
            self.add_pin(pin)

    def on_property_changed(self, key: str) -> None:
        """Hook called by the UI when a property changes."""
        if key in ('address_bits', 'data_bits'):
            # Clear memory if dimensions change
            self.memory.clear()
            self.last_operation = None
            self.last_address = None
            self.last_data = None

            # Rebuild pins so DATA_0..DATA_n matches data_bits.
            self._rebuild_pins()

    # --- Link integration ---

    def get_link_mappings(self) -> Dict[str, list[str]]:
        """Return link mappings for Address and Data buses."""
        # Map our DATA_* output pins to the configured DATA bus link names.
        # This lets us drive the bus by setting pin states (HIGH/FLOAT), and the
        # link resolver will tie together VNETs that share the same link name.
        mappings: Dict[str, list[str]] = {}

        data_bus = self._get_data_bus_name()
        if not data_bus:
            return mappings

        data_bits = self._get_data_bits()
        for bit_index in range(data_bits):
            link_name = f"{data_bus}_{bit_index}"
            pin = self.pins.get(f"{self.component_id}.DATA_{bit_index}")
            if not pin:
                continue

            tab_ids = [tab.tab_id for tab in pin.tabs.values()]
            if tab_ids:
                mappings[link_name] = tab_ids

        return mappings

    # --- Memory operations ---

    def read_memory(self, address: int) -> int:
        """Read value at address (returns 0 if not written)."""
        address = address & ((1 << self._get_address_bits()) - 1)
        return self.memory.get(address, 0)

    def write_memory(self, address: int, value: int) -> None:
        """Write value to address."""
        address = address & ((1 << self._get_address_bits()) - 1)
        value = value & self.max_value

        if value == 0:
            # Remove zero entries to save space
            self.memory.pop(address, None)
        else:
            self.memory[address] = value

    def clear_memory(self) -> None:
        """Clear all memory contents."""
        self.memory.clear()
        self.last_operation = None
        self.last_address = None
        self.last_data = None

    def load_from_file(self, filepath: str) -> bool:
        """Load memory contents from file.
        
        File format: text file with lines of "address:value" in hex.
        Example:
            0000:FF
            0001:A5
            
        Returns True if successful.
        """
        if not filepath or not os.path.isfile(filepath):
            return False

        try:
            self.memory.clear()
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    if ':' not in line:
                        continue

                    addr_str, val_str = line.split(':', 1)
                    addr = int(addr_str.strip(), 16)
                    val = int(val_str.strip(), 16)

                    self.write_memory(addr, val)

            return True
        except Exception as e:
            print(f"Error loading memory file {filepath}: {e}")
            return False

    def save_to_file(self, filepath: str) -> bool:
        """Save memory contents to file.
        
        Only saves non-zero entries.
        Returns True if successful.
        """
        if not filepath:
            return False

        try:
            # Create directory if needed
            dir_path = os.path.dirname(filepath)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

            with open(filepath, 'w') as f:
                f.write("# Memory contents\n")
                f.write(f"# Address bits: {self._get_address_bits()}\n")
                f.write(f"# Data bits: {self._get_data_bits()}\n")
                f.write("#\n")

                # Sort by address
                for addr in sorted(self.memory.keys()):
                    val = self.memory[addr]
                    addr_width = (self._get_address_bits() + 3) // 4  # Hex digits
                    val_width = (self._get_data_bits() + 3) // 4
                    f.write(f"{addr:0{addr_width}X}:{val:0{val_width}X}\n")

            return True
        except Exception as e:
            print(f"Error saving memory file {filepath}: {e}")
            return False

    # --- Bus reading helpers ---

    def _read_bus_value(self, vnet_manager, bus_name: str, num_bits: int) -> int:
        """Read a multi-bit value from a bus by reading individual link states.
        
        Reads links: {bus_name}_0, {bus_name}_1, ..., {bus_name}_{num_bits-1}
        Returns an integer with bit 0 = LSB.
        """
        if not bus_name or not vnet_manager:
            return 0

        value = 0
        for bit_index in range(num_bits):
            link_name = f"{bus_name}_{bit_index}"

            # Check if link exists and is HIGH
            is_high = False
            vnets = getattr(vnet_manager, 'vnets', {})
            if isinstance(vnets, dict):
                for vnet in vnets.values():
                    try:
                        if not vnet.has_link(link_name):
                            continue
                        state = getattr(vnet, 'state', None)
                        if state == PinState.HIGH or state is True or state == 1:
                            is_high = True
                            break
                    except Exception:
                        continue

            if is_high:
                value |= (1 << bit_index)

        return value

    def _drive_data_bus_pins(self, vnet_manager, value: int | None) -> None:
        """Drive (or float) the DATA bus using our DATA_* pins.

        If value is None, all DATA pins are floated.
        If value is an int, DATA_i is HIGH when bit i is set, else FLOAT.
        """
        data_bits = self._get_data_bits()

        for bit_index in range(data_bits):
            pin = self.pins.get(f"{self.component_id}.DATA_{bit_index}")
            if not pin:
                continue

            if value is None:
                new_state = PinState.FLOAT
            else:
                bit_high = bool(value & (1 << bit_index))
                new_state = PinState.HIGH if bit_high else PinState.FLOAT

            if pin.state == new_state:
                continue

            pin.set_state(new_state)

            try:
                data_bus = self._get_data_bus_name()
                link_name = f"{data_bus}_{bit_index}" if data_bus else ""
                tab = next(iter(pin.tabs.values()), None)
                vnet = vnet_manager.get_vnet_for_tab(tab.tab_id) if (vnet_manager and tab) else None
                vnet_id = getattr(vnet, 'vnet_id', None)
                has_link = bool(vnet.has_link(link_name)) if (vnet and link_name) else False
                self._debug(
                    f"[RSIM_DEBUG_MEMORY] {self.component_id} drive bit{bit_index}={new_state} "
                    f"(link={link_name} vnet={vnet_id} has_link={has_link})"
                )
            except Exception:
                pass

            # Mark connected VNET(s) dirty so the simulation engine re-evaluates.
            if vnet_manager:
                for tab in pin.tabs.values():
                    try:
                        vnet_manager.mark_tab_dirty(tab.tab_id)
                    except Exception:
                        pass

    # --- Simulation interface ---

    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """Perform memory read/write based on control pins and bus state."""
        # Read control pins
        enable_pin = self.pins.get(f"{self.component_id}.Enable")
        read_pin = self.pins.get(f"{self.component_id}.Read")
        write_pin = self.pins.get(f"{self.component_id}.Write")

        # Passive inputs: read from VNET state (not pin.state)
        enable = self._read_input_pin_high(vnet_manager, enable_pin)
        read = self._read_input_pin_high(vnet_manager, read_pin)
        write = self._read_input_pin_high(vnet_manager, write_pin)

        debug_enabled = self._debug_enabled()

        addr_bus = self._get_address_bus_name()
        data_bus = self._get_data_bus_name()
        addr_bits = self._get_address_bits()
        data_bits = self._get_data_bits()

        # Clear last operation
        self.last_operation = None
        self.last_address = None
        self.last_data = None

        if not enable:
            # Float data bus when not enabled
            self._drive_data_bus_pins(vnet_manager, None)
            if debug_enabled:
                self._debug(f"[RSIM_DEBUG_MEMORY] {self.component_id} EN=0 -> float Data bus")
            return

        # Read address from address bus
        address = self._read_bus_value(vnet_manager, addr_bus, addr_bits)

        if debug_enabled:
            self._debug(
                f"[RSIM_DEBUG_MEMORY] {self.component_id} EN={int(enable)} R={int(read)} W={int(write)} "
                f"addr_bus={addr_bus} data_bus={data_bus} addr=0x{address:X}"
            )

        if read and not write:
            # Read operation: output memory[address] to data bus
            value = self.read_memory(address)
            self._drive_data_bus_pins(vnet_manager, value)

            if debug_enabled:
                self._debug(f"[RSIM_DEBUG_MEMORY] {self.component_id} READ addr=0x{address:X} -> 0x{value:X}")

            self.last_operation = 'read'
            self.last_address = address
            self.last_data = value

        elif write and not read:
            # Write operation: write data bus to memory[address]
            value = self._read_bus_value(vnet_manager, data_bus, data_bits)
            self.write_memory(address, value)
            # Don't drive the bus during write.
            self._drive_data_bus_pins(vnet_manager, None)

            if debug_enabled:
                self._debug(f"[RSIM_DEBUG_MEMORY] {self.component_id} WRITE addr=0x{address:X} <- 0x{value:X}")

            self.last_operation = 'write'
            self.last_address = address
            self.last_data = value

        else:
            # Both or neither: float data bus
            self._drive_data_bus_pins(vnet_manager, None)

    def sim_start(self, vnet_manager, bridge_manager):
        """Initialize simulation state and load default memory file if specified."""
        self.last_operation = None
        self.last_address = None
        self.last_data = None

        # Volatile RAM: clear contents at each simulation start.
        if self._is_volatile():
            self.memory.clear()

        # IMPORTANT: Do NOT rebuild pins/tabs here.
        # The GUI builds the simulation `tabs`/`vnets` structures BEFORE calling
        # sim_start(). Rebuilding would create new Tab objects that the engine
        # doesn't know about, preventing bus outputs from propagating.
        # Just ensure the bus is floated initially.
        self._drive_data_bus_pins(vnet_manager, None)

        # Debug banner so it's obvious whether the running process sees the env var.
        if self._debug_enabled():
            self._debug(
                f"[RSIM_DEBUG_MEMORY] {self.component_id} sim_start: addr_bus={self._get_address_bus_name()} "
                f"data_bus={self._get_data_bus_name()} addr_bits={self._get_address_bits()} data_bits={self._get_data_bits()}"
            )

        # Load default memory file if specified
        default_file = self._get_default_memory_file()
        if default_file:
            # Try to resolve relative paths
            if not os.path.isabs(default_file):
                # Try relative to current working directory
                if not os.path.isfile(default_file):
                    # Could also try relative to .rsim file location, but we don't have that info here
                    pass

            self.load_from_file(default_file)

    def sim_stop(self):
        """Clean up simulation state."""
        self.last_operation = None
        self.last_address = None
        self.last_data = None

    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        # Not used by Tkinter GUI (uses renderers), kept for compatibility
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """Deserialize from dictionary."""
        mem = cls(data['component_id'], data.get('page_id', 'page001'))

        pos = data.get('position', {'x': 0, 'y': 0})
        mem.position = (pos['x'], pos['y'])
        mem.rotation = data.get('rotation', 0)
        mem.link_name = data.get('link_name')

        if 'properties' in data and isinstance(data['properties'], dict):
            mem.properties.update(data['properties'])

        # Load memory contents only when non-volatile.
        if (not mem._is_volatile()) and 'memory' in data and isinstance(data['memory'], dict):
            mem.memory = {int(k): int(v) for k, v in data['memory'].items()}

        # Load viewer state
        if 'scroll_offset' in data:
            mem.scroll_offset = int(data.get('scroll_offset', 0))

        mem._rebuild_pins()
        return mem

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = super().to_dict()

        # Include memory contents (only non-zero values) when non-volatile.
        if (not self._is_volatile()) and self.memory:
            result['memory'] = {str(k): v for k, v in self.memory.items()}

        # Include viewer state
        result['scroll_offset'] = self.scroll_offset

        return result
