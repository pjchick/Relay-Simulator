# Relay Logic Simulator - Architecture Document

## Executive Summary

A Python-based relay logic simulator with clean separation between simulation engine and GUI designer. The engine runs as a pure Python library with an optional socket server for remote access. The tkinter designer runs on the same machine and communicates via direct Python API for maximum performance.

---

## 1. ARCHITECTURE OVERVIEW

### 1.1 Design Principles

1. **Separation of Concerns**: Engine has ZERO GUI dependencies
2. **Component Isolation**: Each component in separate file, dynamically loaded
3. **Performance First**: Target 5+ GUI updates/second during simulation
4. **Clean Interfaces**: Well-defined APIs between layers
5. **Small Files**: Keep all .py files focused and manageable

### 1.2 Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                        │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  Designer GUI    │  │  Telnet Clients  │                 │
│  │  (tkinter)       │  │  Test Scripts    │                 │
│  │  Local/Fast      │  │  Logic Analyzer  │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
└───────────┼────────────────────┼───────────────────────────┘
            │                    │
            │ Direct Python API  │ Socket API (JSON)
            │                    │
┌───────────▼────────────────────▼───────────────────────────┐
│                     API LAYER                               │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  EngineAPI           │  │  SocketServer         │        │
│  │  (Direct Interface)  │  │  (Remote Interface)   │        │
│  └──────────┬───────────┘  └──────────┬───────────┘        │
└─────────────┼───────────────────────────┼──────────────────┘
              │                           │
              └───────────┬───────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     ENGINE CORE                              │
│              (Pure Python - No GUI deps)                     │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Document        │  │ Simulation      │  │ VNET        │ │
│  │ Manager         │  │ Engine          │  │ Builder     │ │
│  │ (Load/Save)     │  │ (Main Loop)     │  │             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Component Registry & Loader                │   │
│  │           (Dynamic Discovery)                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ./components/                                       │   │
│  │    ├── base.py           (Component base class)      │   │
│  │    ├── toggle_switch.py  (ToggleSwitch)             │   │
│  │    ├── indicator.py      (Indicator)                │   │
│  │    ├── dpdt_relay.py     (DPDTRelay)                │   │
│  │    └── vcc_power.py      (VCCPower)                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Pin/Tab         │  │ Wire/Junction   │  │ Bridge      │ │
│  │ System          │  │ System          │  │ Manager     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ ID Manager      │  │ Thread Pool     │                   │
│  │                 │  │ Manager         │                   │
│  └─────────────────┘  └─────────────────┘                   │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. COMMUNICATION ARCHITECTURE

### 2.1 Designer ↔ Engine (Direct Python API)

**Why Direct API:**
- Designer and engine on same machine
- Maximum performance (5+ updates/sec target)
- No serialization overhead
- Direct Python object access

**Implementation:**
```python
# Designer imports and uses engine directly
from engine.api import SimulationEngine

engine = SimulationEngine()
engine.load_file("circuit.rsim")
engine.register_stable_callback(designer.on_stable)
engine.start_simulation()
```

**Event Flow:**
```
Designer                    Engine
   │                          │
   ├──load_file()────────────>│
   │                          │
   ├──register_callback()────>│
   │                          │
   ├──start_simulation()─────>│
   │                          │
   │                          ├─ (simulation running)
   │                          ├─ (process VNETs)
   │                          ├─ (achieve stability)
   │                          │
   │<────on_stable(state)─────┤
   │                          │
   ├─ (render components)     │
   │                          │
   ├──interact(comp_id)──────>│
   │                          │
   │                          ├─ (mark VNETs dirty)
   │                          ├─ (process)
   │                          │
   │<────on_stable(state)─────┤
```

### 2.2 Remote Clients ↔ Engine (Socket API)

**Why Socket API:**
- Test scripts, telnet clients, logic analyzer
- Standard interface
- Language agnostic (could use from other languages)

**Protocol: JSON over TCP**
```json
// Request
{
    "command": "load_file",
    "args": {
        "filepath": "circuit.rsim"
    },
    "request_id": "12345"
}

// Response
{
    "status": "success",
    "result": {...},
    "request_id": "12345"
}

// Event (pushed from engine)
{
    "event": "stable",
    "data": {
        "components": [...],
        "vnets": [...]
    }
}
```

---

## 3. COMPONENT ARCHITECTURE

### 3.1 Component Class Structure

Each component is a separate file in `./components/` directory.

**Base Component Interface:**
```python
# components/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class Component(ABC):
    """Base class for all components"""
    
    # Class attributes
    component_type: str = None  # Override in subclass
    
    def __init__(self, component_id: str, page_id: str):
        self.component_id = component_id
        self.page_id = page_id
        self.position = (0, 0)  # X, Y
        self.rotation = 0  # degrees (if applicable)
        self.properties = {}  # Component-specific properties
        self.pins = {}  # pin_id -> Pin object
        self.link_name = None  # Optional, for cross-page links
    
    # === SIMULATION INTERFACE (Engine uses these) ===
    
    @abstractmethod
    def simulate_logic(self, vnet_manager):
        """
        Calculate new component state based on pin states.
        Update pins if state changes.
        Mark VNETs dirty via vnet_manager if needed.
        
        Called by engine when component's VNETs are dirty.
        """
        pass
    
    @abstractmethod
    def sim_start(self, vnet_manager, bridge_manager):
        """
        Initialize component for simulation start.
        Set default pin states.
        Create bridges if needed (e.g., relay contacts).
        Read connected VNETs.
        """
        pass
    
    def sim_stop(self):
        """
        Clean up component state at simulation stop.
        Bridges are removed by engine.
        """
        pass
    
    # === INTERACTION INTERFACE (Designer/Remote uses these) ===
    
    def interact(self, action: str, params: Dict[str, Any] = None):
        """
        Handle user interaction with component.
        Examples: toggle switch, press button
        
        Args:
            action: Action name (e.g., "toggle", "press")
            params: Optional parameters
        
        Returns:
            bool: True if state changed
        """
        return False
    
    # === VISUAL INTERFACE (Designer uses these) ===
    
    def get_visual_state(self) -> Dict[str, Any]:
        """
        Return current visual state for rendering.
        
        Returns dict with keys:
            - type: Component type
            - position: (x, y)
            - rotation: degrees
            - state: Component-specific state
            - pin_states: Dict of pin_id -> state
            - any other visual properties
        """
        return {
            'type': self.component_type,
            'position': self.position,
            'rotation': self.rotation,
            'properties': self.properties.copy(),
            'pin_states': {pin_id: pin.state for pin_id, pin in self.pins.items()}
        }
    
    @abstractmethod
    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        """
        Render component using canvas adapter.
        
        Args:
            canvas_adapter: CanvasAdapter instance
            x_offset: X offset for panning
            y_offset: Y offset for panning
        """
        pass
    
    # === SERIALIZATION INTERFACE ===
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dict for saving"""
        return {
            'component_id': self.component_id,
            'type': self.component_type,
            'position': self.position,
            'rotation': self.rotation,
            'properties': self.properties,
            'link_name': self.link_name,
            'pins': {pin_id: pin.to_dict() for pin_id, pin in self.pins.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        """Deserialize component from dict"""
        pass  # Override in subclass
```

### 3.2 Canvas Adapter Pattern

**Why:** Components need to render without depending on tkinter.

```python
# rendering/canvas_adapter.py
from abc import ABC, abstractmethod
from typing import Tuple

class CanvasAdapter(ABC):
    """Abstract interface for drawing operations"""
    
    @abstractmethod
    def draw_circle(self, x: float, y: float, radius: float, 
                   fill: str = None, outline: str = None, width: int = 1):
        """Draw a circle"""
        pass
    
    @abstractmethod
    def draw_rectangle(self, x1: float, y1: float, x2: float, y2: float,
                      fill: str = None, outline: str = None, width: int = 1):
        """Draw a rectangle"""
        pass
    
    @abstractmethod
    def draw_line(self, x1: float, y1: float, x2: float, y2: float,
                 fill: str = None, width: int = 1):
        """Draw a line"""
        pass
    
    @abstractmethod
    def draw_polygon(self, points: list, fill: str = None, 
                    outline: str = None, width: int = 1):
        """Draw a polygon from list of (x,y) points"""
        pass
    
    @abstractmethod
    def draw_text(self, x: float, y: float, text: str, 
                 font: Tuple = None, fill: str = None, anchor: str = 'center'):
        """Draw text"""
        pass
```

**Designer Implementation:**
```python
# designer/tkinter_adapter.py
from rendering.canvas_adapter import CanvasAdapter
import tkinter as tk

class TkinterCanvasAdapter(CanvasAdapter):
    """Tkinter implementation of CanvasAdapter"""
    
    def __init__(self, tkinter_canvas: tk.Canvas):
        self.canvas = tkinter_canvas
        self.items = []  # Track created items for cleanup
    
    def draw_circle(self, x, y, radius, fill=None, outline=None, width=1):
        item = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=fill or '', outline=outline or 'black', width=width
        )
        self.items.append(item)
        return item
    
    def draw_rectangle(self, x1, y1, x2, y2, fill=None, outline=None, width=1):
        item = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=fill or '', outline=outline or 'black', width=width
        )
        self.items.append(item)
        return item
    
    # ... other methods ...
    
    def clear(self):
        """Clear all drawn items"""
        for item in self.items:
            self.canvas.delete(item)
        self.items.clear()
```

### 3.3 Component Example: Toggle Switch

```python
# components/toggle_switch.py
from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState

class ToggleSwitch(Component):
    """Toggle switch with internal power"""
    
    component_type = "ToggleSwitch"
    
    def __init__(self, component_id, page_id):
        super().__init__(component_id, page_id)
        
        # Component-specific state
        self.is_on = False  # OFF by default
        
        # Component-specific properties
        self.properties = {
            'label': 'SW',
            'color': '#808080'
        }
        
        # Create pin with 4 tabs (12, 3, 6, 9 o'clock)
        self._create_pins()
    
    def _create_pins(self):
        """Create pin structure"""
        pin_id = f"{self.component_id}.pin1"
        pin = Pin(pin_id, self)
        
        # Create 4 tabs at clock positions
        # Positions relative to component center (0,0)
        tab_positions = [
            (0, -20),   # 12 o'clock
            (20, 0),    # 3 o'clock
            (0, 20),    # 6 o'clock
            (-20, 0)    # 9 o'clock
        ]
        
        for i, (dx, dy) in enumerate(tab_positions):
            tab_id = f"{pin_id}.tab{i+1}"
            tab = Tab(tab_id, pin, (dx, dy))
            pin.add_tab(tab)
        
        self.pins[pin_id] = pin
    
    def simulate_logic(self, vnet_manager):
        """Update pin state based on switch position"""
        pin = list(self.pins.values())[0]
        
        # Determine new state
        new_state = PinState.HIGH if self.is_on else PinState.FLOAT
        
        # Update pin state (this will mark VNET dirty if changed)
        if pin.state != new_state:
            pin.set_state(new_state)
            vnet_manager.mark_pin_dirty(pin)
    
    def sim_start(self, vnet_manager, bridge_manager):
        """Initialize switch to OFF state"""
        self.is_on = False
        pin = list(self.pins.values())[0]
        pin.set_state(PinState.FLOAT)
    
    def interact(self, action, params=None):
        """Toggle switch on/off"""
        if action == "toggle":
            self.is_on = not self.is_on
            return True
        return False
    
    def get_visual_state(self):
        """Return visual state"""
        state = super().get_visual_state()
        state['is_on'] = self.is_on
        return state
    
    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        """Render toggle switch"""
        x, y = self.position
        x += x_offset
        y += y_offset
        
        # Draw circular body
        radius = 25
        fill_color = '#00FF00' if self.is_on else '#808080'
        canvas_adapter.draw_circle(x, y, radius, fill=fill_color, outline='black', width=2)
        
        # Draw label
        label = self.properties.get('label', 'SW')
        canvas_adapter.draw_text(x, y, label, fill='black')
        
        # Draw tabs (small circles at connection points)
        pin = list(self.pins.values())[0]
        for tab in pin.tabs.values():
            tab_x = x + tab.relative_position[0]
            tab_y = y + tab.relative_position[1]
            
            # Color tab based on state
            tab_color = '#FF0000' if pin.state == PinState.HIGH else '#CCCCCC'
            canvas_adapter.draw_circle(tab_x, tab_y, 3, fill=tab_color, outline='black')
```

---

## 4. ENGINE API

### 4.1 Direct Python API (For Designer)

```python
# engine/api.py
from typing import Callable, Dict, Any, List
from core.document import Document
from core.simulation_engine import SimulationEngine as SimEngine
from core.vnet_manager import VnetManager
from threading import Lock

class SimulationEngine:
    """
    Public API for simulation engine.
    Thread-safe interface for designer and other local clients.
    """
    
    def __init__(self):
        self.document: Document = None
        self.sim_engine: SimEngine = None
        self.vnet_manager: VnetManager = None
        self._stable_callbacks: List[Callable] = []
        self._lock = Lock()
        self._running = False
    
    # === FILE OPERATIONS ===
    
    def load_file(self, filepath: str) -> Dict[str, Any]:
        """
        Load .rsim file.
        
        Returns:
            {
                'success': bool,
                'message': str,
                'document_info': {...}
            }
        """
        pass
    
    def save_file(self, filepath: str) -> Dict[str, Any]:
        """Save current document to .rsim file"""
        pass
    
    # === SIMULATION CONTROL ===
    
    def start_simulation(self) -> Dict[str, Any]:
        """
        Start simulation.
        - Builds VNETs
        - Calls SimStart on components
        - Starts main loop
        
        Returns:
            {'success': bool, 'message': str}
        """
        pass
    
    def stop_simulation(self) -> Dict[str, Any]:
        """
        Stop simulation.
        - Stops main loop
        - Calls SimStop on components
        - Clears VNETs
        """
        pass
    
    def is_running(self) -> bool:
        """Check if simulation is running"""
        return self._running
    
    def is_stable(self) -> bool:
        """Check if simulation is in stable state (no dirty VNETs)"""
        pass
    
    # === STATE QUERIES ===
    
    def get_component_states(self, page_id: str = None) -> List[Dict[str, Any]]:
        """
        Get visual states of all components (or specific page).
        
        Returns list of component visual states suitable for rendering.
        """
        pass
    
    def get_vnet_info(self) -> List[Dict[str, Any]]:
        """Get information about all VNETs"""
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get simulation statistics.
        
        Returns:
            {
                'iterations': int,
                'time_to_stable': float,
                'dirty_vnets': int,
                'total_vnets': int,
                'components': int
            }
        """
        pass
    
    # === COMPONENT INTERACTION ===
    
    def interact_with_component(self, component_id: str, 
                               action: str, params: Dict = None) -> Dict[str, Any]:
        """
        Interact with a component (e.g., toggle switch).
        
        Args:
            component_id: Component ID
            action: Action name (e.g., "toggle")
            params: Optional parameters
        
        Returns:
            {'success': bool, 'message': str}
        """
        pass
    
    # === CALLBACKS ===
    
    def register_stable_callback(self, callback: Callable[[Dict], None]):
        """
        Register callback for stable state notifications.
        
        Callback signature: callback(state_data: Dict)
        
        Called when simulation reaches stable state.
        State data includes component states for rendering.
        """
        with self._lock:
            self._stable_callbacks.append(callback)
    
    def unregister_stable_callback(self, callback: Callable):
        """Unregister a stable callback"""
        with self._lock:
            if callback in self._stable_callbacks:
                self._stable_callbacks.remove(callback)
    
    def _notify_stable(self, state_data: Dict):
        """Internal: notify all registered callbacks"""
        with self._lock:
            callbacks = self._stable_callbacks.copy()
        
        for callback in callbacks:
            try:
                callback(state_data)
            except Exception as e:
                print(f"Error in stable callback: {e}")
```

### 4.2 Socket API (For Remote Clients)

```python
# networking/socket_server.py
import socket
import json
import threading
from engine.api import SimulationEngine

class SocketServer:
    """
    Socket server for remote clients.
    JSON-based protocol.
    """
    
    def __init__(self, engine: SimulationEngine, host='127.0.0.1', port=5000):
        self.engine = engine
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.running = False
    
    def start(self):
        """Start socket server"""
        pass
    
    def stop(self):
        """Stop socket server"""
        pass
    
    def _handle_client(self, client_socket, address):
        """Handle individual client connection"""
        pass
    
    def _process_command(self, command_data: Dict) -> Dict:
        """
        Process command from client.
        
        Command format:
        {
            'command': 'load_file',
            'args': {...},
            'request_id': '12345'
        }
        
        Returns response dict.
        """
        pass
    
    def _broadcast_event(self, event_name: str, data: Dict):
        """Broadcast event to all connected clients"""
        pass
```

---

## 5. FILE ORGANIZATION

### 5.1 Project Structure

```
relay_simulator/
├── main.py                      # Entry point for designer
├── engine_server.py             # Entry point for standalone engine
├── requirements.txt             # Python dependencies
├── README.md
│
├── engine/                      # Engine core (no GUI deps)
│   ├── __init__.py
│   ├── api.py                   # SimulationEngine API
│   └── version.py               # Version info
│
├── core/                        # Core simulation classes
│   ├── __init__.py
│   ├── document.py              # Document class
│   ├── page.py                  # Page class
│   ├── pin.py                   # Pin class
│   ├── tab.py                   # Tab class
│   ├── state.py                 # PinState enum
│   ├── wire.py                  # Wire class
│   ├── junction.py              # Junction class
│   ├── waypoint.py              # Waypoint class
│   ├── vnet.py                  # VNET class
│   ├── vnet_builder.py          # VNET builder algorithm
│   ├── vnet_manager.py          # VNET management
│   ├── bridge.py                # Bridge class
│   ├── bridge_manager.py        # Bridge management
│   ├── link_resolver.py         # Link resolution
│   ├── simulation_engine.py     # Main simulation loop
│   ├── id_manager.py            # ID generation/validation
│   ├── thread_pool.py           # Thread pool wrapper
│   └── file_io.py               # JSON serialization
│
├── components/                  # Component implementations
│   ├── __init__.py
│   ├── base.py                  # Component base class
│   ├── component_loader.py      # Dynamic component loading
│   ├── toggle_switch.py         # ToggleSwitch component
│   ├── indicator.py             # Indicator component
│   ├── dpdt_relay.py            # DPDTRelay component
│   └── vcc_power.py             # VCCPower component
│
├── rendering/                   # Rendering abstraction
│   ├── __init__.py
│   └── canvas_adapter.py        # CanvasAdapter abstract class
│
├── networking/                  # Socket server
│   ├── __init__.py
│   ├── socket_server.py         # Socket server
│   └── protocol.py              # JSON protocol definitions
│
├── designer/                    # tkinter GUI (separate from engine)
│   ├── __init__.py
│   ├── main_window.py           # Main GUI window
│   ├── canvas_view.py           # Canvas for drawing
│   ├── tkinter_adapter.py       # TkinterCanvasAdapter
│   ├── component_palette.py     # Component selection
│   ├── properties_panel.py      # Component properties
│   └── toolbar.py               # Toolbar
│
├── testing/                     # Test scripts
│   ├── __init__.py
│   ├── test_socket_client.py    # Test socket interface
│   └── test_circuits/           # Test .rsim files
│       ├── simple_switch_led.rsim
│       ├── relay_circuit.rsim
│       └── complex.rsim
│
└── examples/                    # Example circuits
    └── ...
```

### 5.2 File Size Guidelines

- **Maximum file size**: ~300 lines
- **Split when**:
  - Class >200 lines → Extract helper classes
  - Multiple unrelated classes → Separate files
  - Complex algorithm → Separate module

---

## 6. PERFORMANCE STRATEGY

### 6.1 Target: 5+ Updates/Second

**Calculation:**
- 5 updates/sec = 200ms per update maximum
- Budget breakdown:
  - Engine simulation: 100ms
  - State snapshot: 20ms
  - Rendering all components: 80ms

**Optimization Strategies:**

1. **Only Stable State Updates**
   - Designer blocks until simulation stable
   - No intermediate rendering
   - Reduces update frequency

2. **Efficient State Snapshot**
   ```python
   def get_component_states(self, page_id):
       """Fast state snapshot for rendering"""
       if page_id:
           components = self.document.get_page(page_id).components
       else:
           components = self.document.get_all_components()
       
       # Return cached visual states (updated during simulation)
       return [comp.get_visual_state() for comp in components]
   ```

3. **Render All Components on Page**
   - Even if off-screen
   - Simple: No culling logic needed
   - Fast enough with canvas_adapter
   - tkinter handles off-screen efficiently

4. **Thread Pool Sizing**
   - 4 threads for component logic
   - 2 threads for VNET processing
   - Adjustable based on CPU

5. **Dirty Flag Optimization**
   - Only process changed VNETs
   - Skip stable circuits

6. **Direct Python API**
   - No serialization overhead
   - Direct object references
   - Fast callback mechanism

### 6.2 Performance Monitoring

```python
# core/statistics.py
import time

class SimulationStatistics:
    """Track simulation performance"""
    
    def __init__(self):
        self.iteration_count = 0
        self.start_time = None
        self.time_to_stable = 0
        self.total_vnets = 0
        self.dirty_vnets = 0
        self.component_updates = 0
        
    def reset(self):
        """Reset statistics"""
        self.iteration_count = 0
        self.start_time = time.time()
        
    def record_iteration(self, dirty_count):
        """Record iteration"""
        self.iteration_count += 1
        self.dirty_vnets = dirty_count
        
    def record_stable(self):
        """Record stability achieved"""
        self.time_to_stable = time.time() - self.start_time
        
    def get_updates_per_second(self):
        """Calculate updates per second"""
        if self.time_to_stable > 0:
            return self.iteration_count / self.time_to_stable
        return 0
```

---

## 7. THREADING MODEL

### 7.1 Thread Allocation

- **Main Thread**: GUI event loop (tkinter)
- **Simulation Thread**: Main simulation loop
- **VNET Pool**: 2 worker threads
- **Component Pool**: 4 worker threads

### 7.2 Thread Safety

**Critical Sections:**
1. VNET state modifications
2. Component pin state changes
3. Bridge add/remove
4. Dirty flag updates

**Locking Strategy:**
```python
# Use fine-grained locks
class VNET:
    def __init__(self):
        self._lock = threading.Lock()
        self._dirty_lock = threading.Lock()
    
    def mark_dirty(self):
        with self._dirty_lock:
            self._dirty = True
    
    def update_state(self, new_state):
        with self._lock:
            self._state = new_state
```

---

## 8. DESIGNER INTEGRATION

### 8.1 Designer Startup Flow

```python
# main.py
from designer.main_window import MainWindow
from engine.api import SimulationEngine

def main():
    # Create engine
    engine = SimulationEngine()
    
    # Create designer GUI
    app = MainWindow(engine)
    
    # Register callback for stable states
    engine.register_stable_callback(app.on_simulation_stable)
    
    # Run GUI
    app.mainloop()

if __name__ == '__main__':
    main()
```

### 8.2 Designer Update Flow

```python
# designer/main_window.py
class MainWindow:
    def __init__(self, engine):
        self.engine = engine
        self.canvas_view = CanvasView(self)
        # ... setup GUI ...
    
    def on_simulation_stable(self, state_data):
        """Called by engine when simulation reaches stable state"""
        # This runs in simulation thread, need to marshal to GUI thread
        self.after(0, self._update_display, state_data)
    
    def _update_display(self, state_data):
        """Update display (runs in GUI thread)"""
        # Clear canvas
        self.canvas_view.clear()
        
        # Render all components on current page
        components = state_data['components']
        for comp_state in components:
            component = self.engine.document.get_component(comp_state['component_id'])
            component.render(self.canvas_view.adapter)
        
        # Update status bar
        stats = state_data['statistics']
        self.update_status(f"Stable - {stats['iterations']} iterations")
```

---

## 9. SCRIPTING INTERFACE

### 9.1 Socket API for Test Scripts

Test scripts connect via socket API:

```python
# testing/test_socket_client.py
import socket
import json

class SimulatorClient:
    """Client for connecting to simulator via socket"""
    
    def __init__(self, host='127.0.0.1', port=5000):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
    
    def send_command(self, command, args=None):
        """Send command and wait for response"""
        request = {
            'command': command,
            'args': args or {},
            'request_id': str(time.time())
        }
        
        self.socket.send(json.dumps(request).encode() + b'\n')
        
        response = self.socket.recv(4096)
        return json.loads(response.decode())
    
    def load_file(self, filepath):
        return self.send_command('load_file', {'filepath': filepath})
    
    def start_simulation(self):
        return self.send_command('start_simulation')
    
    def toggle_switch(self, component_id):
        return self.send_command('interact', {
            'component_id': component_id,
            'action': 'toggle'
        })
    
    def get_component_states(self):
        return self.send_command('get_component_states')

# Example usage
if __name__ == '__main__':
    client = SimulatorClient()
    
    # Load circuit
    result = client.load_file('test_circuits/simple_switch_led.rsim')
    print(f"Load: {result}")
    
    # Start simulation
    result = client.start_simulation()
    print(f"Start: {result}")
    
    # Toggle switch
    result = client.toggle_switch('12345678')  # component ID
    print(f"Toggle: {result}")
    
    # Get states
    states = client.get_component_states()
    print(f"States: {states}")
```

---

## 10. SUMMARY OF KEY DECISIONS

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Language** | Python | Your choice, tkinter support |
| **Designer-Engine** | Direct Python API | Same machine, max performance |
| **Remote Access** | Socket API (JSON) | Testing, remote tools |
| **Component Files** | Separate files, dynamic load | Modularity, <300 lines each |
| **Rendering** | Canvas Adapter pattern | No GUI deps in engine |
| **State Updates** | Only stable states | Target 5+ updates/sec |
| **Render Strategy** | All components on page | Simplicity, adequate perf |
| **Threading** | 4 component + 2 VNET threads | Balanced for 100s components |
| **File Format** | JSON (.rsim extension) | Easy to parse/debug |

---

## NEXT STEPS

1. **Review and approve architecture**
2. **Set up project structure** (create folders/files)
3. **Implement Phase 0**: Core foundation classes
4. **Build simple test case**: Switch → LED
5. **Iterate based on performance testing**

---

*End of Architecture Document*
