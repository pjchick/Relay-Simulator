# Relay Simulator - AI Coding Agent Instructions

## Project Overview

A Python-based relay logic simulator with tkinter GUI designer and multi-threaded simulation engine. Simulates electrical circuits using relay components, switches, indicators, and more. Supports 100+ components per circuit with dirty-flag optimization for high-performance simulation.

## Critical Architecture Concepts

### Separation of Concerns

- **Engine has ZERO GUI dependencies** - core simulation runs independently
- **Direct Python API** for GUI (no serialization overhead)
- Components are **dynamically loaded** from `components/` directory

### ID System - 8-Character UUIDs

All IDs are **first 8 characters of UUID**, used hierarchically:

- `pageId.componentId.pinId.tabId`
- `pageId.wireId.waypointId`
- When copying: generate new IDs. When cutting/pasting same page: preserve IDs
- **NO DUPLICATE IDs across entire document**

### Pin/Tab/VNET Model (Read This Carefully!)

- **Tab**: Physical connection point on component (has position)
- **Pin**: Logical collection of tabs (e.g., Indicator has 1 pin, 4 tabs at 3/6/9/12 o'clock)
- **VNET**: Virtual network of electrically connected tabs sharing same state
- State flow: `Tab → Pin → Component logic → Pin → Tab → VNET`
- **HIGH OR logic**: If ANY tab in VNET is HIGH, entire VNET is HIGH
- Only two states: `PinState.HIGH` and `PinState.FLOAT` (NOT LOW!)

### Component Lifecycle

Every component implements 4 key methods (see [`components/base.py`](../relay_simulator/components/base.py)):

1. `simulate_logic(vnet_manager, bridge_manager)` - Calculate new state, mark VNETs dirty
2. `sim_start(vnet_manager, bridge_manager)` - Initialize on simulation start, create bridges
3. `sim_stop()` - Cleanup (bridges removed automatically)
4. `render(canvas_adapter)` - Draw component on canvas

### Simulation Engine - Performance Critical

- **Single-threaded is 2x faster** for circuits <2000 components (default)
- **Multi-threaded** only beneficial for large circuits (≥2000 components)
- See [`docs/THREADING_BOTTLENECK_ANALYSIS.md`](../docs/THREADING_BOTTLENECK_ANALYSIS.md)
- Use factory: `create_engine(vnets, tabs, bridges, components, mode='auto')`
- **Dirty flag optimization**: Only recalculate changed VNETs/components

### File Format

- `.rsim` files are JSON with hierarchical structure (see [`fileio/rsim_schema.py`](../relay_simulator/fileio/rsim_schema.py))
- Schema version 1.0.0 - check compatibility with `SchemaVersion.is_compatible()`
- Structure: `Document → Pages → Components/Wires → Pins/Tabs`

## Developer Workflows

### Running the Application

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Launch GUI designer
python relay_simulator\app.py
```

### Building Executable

```powershell
python build_exe.py
# Output: dist\RelaySimulator.exe
```

### Testing

- Test scripts in `relay_simulator/testing/`
- Example circuits in `examples/*.rsim`

## Project-Specific Conventions

### File Size Limit

**Keep all .py files under 300 lines** - split large files into focused modules

### Thread Safety

- All VNET/component state access uses `threading.RLock()` (reentrant locks)
- See [`core/vnet.py`](../relay_simulator/core/vnet.py) for pattern example

### Component Registration

- Components auto-discovered from `components/` directory
- Set `component_type` class attribute for factory registration
- See [`components/factory.py`](../relay_simulator/components/factory.py)

### Logging & Diagnostics

- Use `diagnostics.get_logger()` for logging (configured in [`diagnostics.py`](../relay_simulator/diagnostics.py))
- Logs: `%LOCALAPPDATA%\RelaySimulator\logs` (Windows)
- GUI watchdog monitors Tkinter responsiveness (env: `RSIM_WATCHDOG=0` to disable)

### State Management

```python
from core.state import PinState, combine_states

# Combine multiple pin states (HIGH OR logic)
result = combine_states(pin1.state, pin2.state)  # HIGH wins

# VNET evaluation (thread-safe)
with vnet._lock:
    vnet.state = new_state
```

### Bridge System

- Bridges are **dynamic connections** created at runtime (e.g., relay contacts)
- Created in `sim_start()`, removed automatically in `sim_stop()`
- Bridge format: `(source_tab_id, target_tab_id, bridge_id)`

## Key Integration Points

### GUI ↔ Engine

- GUI imports engine directly: `from simulation.simulation_engine import SimulationEngine`
- See [`gui/main_window.py`](../relay_simulator/gui/main_window.py) for integration

### VNET Builder

- Algorithm in [`core/vnet_builder.py`](../relay_simulator/core/vnet_builder.py)
- Traverses wire connections to create VNETs
- Handles cross-page links and bridges
- **Run after any connection change**

## Documentation Resources

- **Architecture**: [`docs/Architecture.md`](../docs/Architecture.md) - layer architecture, communication patterns
- **Engine Usage**: [`docs/SIMULATION_ENGINE_USAGE.md`](../docs/SIMULATION_ENGINE_USAGE.md) - factory patterns, configuration
- **File Format**: [`docs/RSIM_FILE_FORMAT.md`](../docs/RSIM_FILE_FORMAT.md) - schema details
- **Performance**: [`docs/THREADING_BOTTLENECK_ANALYSIS.md`](../docs/THREADING_BOTTLENECK_ANALYSIS.md) - why single-threaded wins
- **Project Status**: [`docs/PROJECT_STATUS.md`](../docs/PROJECT_STATUS.md) - current phase completion

## Common Pitfalls to Avoid

1. **Don't import tkinter in `core/`, `simulation/`, or `components/`** - engine must be GUI-independent
2. **Don't use LOW state** - only HIGH and FLOAT exist in this system
3. **Don't forget to mark VNETs dirty** - call `vnet_manager.mark_vnet_dirty(vnet_id)` when component changes state
4. **Don't access VNET state without locks** - always use `with vnet._lock:` for thread safety
5. **Don't assume multi-threading is faster** - use `mode='auto'` in factory unless you have >2000 components
