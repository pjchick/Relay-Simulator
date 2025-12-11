# Simulation Engine Usage Guide

This guide explains how to create and configure simulation engines with the factory pattern.

## Quick Start

### Auto Mode (Recommended)

The simplest way to create an engine - automatically selects single or multi-threaded based on circuit size:

```python
from simulation.engine_factory import create_engine

# Create engine (auto-selects based on component count)
engine = create_engine(vnets, tabs, bridges, components)

# Initialize and run
engine.initialize()
stats = engine.run()
print(f"Stable in {stats.iterations} iterations")
```

**Auto mode thresholds:**
- `< 2000 components` → Single-threaded (2x faster)
- `≥ 2000 components` → Multi-threaded (4 threads)

---

## Explicit Mode Selection

### Force Single-Threaded

For circuits where you know single-threaded is optimal:

```python
from simulation.engine_factory import create_engine

# Force single-threaded mode
engine = create_engine(
    vnets, tabs, bridges, components,
    mode='single'
)
```

### Force Multi-Threaded

For large circuits or testing:

```python
from simulation.engine_factory import create_engine

# Force multi-threaded with 8 threads
engine = create_engine(
    vnets, tabs, bridges, components,
    mode='multi',
    thread_count=8
)
```

---

## Using EngineConfig

For more control over configuration:

```python
from simulation.engine_factory import SimulationEngineFactory, EngineConfig

# Create custom configuration
config = EngineConfig(
    mode='auto',              # 'single', 'multi', or 'auto'
    thread_count=4,           # For multi-threaded mode
    auto_threshold=2000,      # Components for auto switch
    max_iterations=10000,     # Oscillation detection
    timeout_seconds=30.0      # Timeout limit
)

# Create engine with config
engine = SimulationEngineFactory.create_engine(
    vnets, tabs, bridges, components, config
)
```

---

## Convenience Methods

### Direct Single-Threaded Creation

```python
from simulation.engine_factory import SimulationEngineFactory

engine = SimulationEngineFactory.create_single_threaded(
    vnets, tabs, bridges, components,
    max_iterations=5000,
    timeout_seconds=60.0
)
```

### Direct Multi-Threaded Creation

```python
from simulation.engine_factory import SimulationEngineFactory

engine = SimulationEngineFactory.create_multi_threaded(
    vnets, tabs, bridges, components,
    thread_count=8,
    max_iterations=5000,
    timeout_seconds=60.0
)
```

---

## Performance Recommendations

### Get Recommendation for Your Circuit

```python
from simulation.engine_factory import SimulationEngineFactory

# Get recommendation
component_count = len(components)
SimulationEngineFactory.print_recommendation(component_count)
```

**Output:**
```
============================================================
ENGINE PERFORMANCE RECOMMENDATION
============================================================
Component count: 500
Recommended mode: SINGLE

Rationale:
  • Circuit has <2000 components
  • Single-threaded is ~2x faster for this size
  • Threading overhead exceeds parallelism benefit

To override, use:
  config = EngineConfig(mode='multi')  # Force multi-threaded
============================================================
```

---

## When to Use Each Mode

### Use Single-Threaded When:
- Circuit has < 2000 components ✓ **RECOMMENDED**
- Maximum performance needed for small/medium circuits
- Debugging (simpler execution flow)
- Testing component logic

### Use Multi-Threaded When:
- Circuit has ≥ 2000 components
- Large-scale simulation required
- Testing threading behavior
- Parallel processing beneficial

### Use Auto Mode When:
- Circuit size varies ✓ **DEFAULT**
- Want optimal performance automatically
- Don't want to manage mode selection
- Building general-purpose tools

---

## Performance Data

Based on comprehensive profiling (`THREADING_BOTTLENECK_ANALYSIS.md`):

| Components | Single-Threaded | Multi-Threaded (4 threads) | Speedup |
|------------|----------------|---------------------------|---------|
| 21         | 0.6ms          | 1.7ms                     | 0.35x   |
| 101        | 2.8ms          | 6.1ms                     | 0.46x   |
| 201        | 8.1ms          | 10.2ms                    | 0.79x   |
| 1001       | 30.0ms         | 48.5ms                    | 0.62x   |

**Conclusion:** Single-threaded is 2x faster for typical circuits.

**Thread Scaling (100 components):**

| Threads | Time   | Throughput  | vs 1 thread |
|---------|--------|-------------|-------------|
| 1       | 9.0ms  | 222 iter/s  | Baseline    |
| 2       | 9.3ms  | 216 iter/s  | 3% slower   |
| 4       | 9.6ms  | 208 iter/s  | 6% slower   |
| 8       | 13.4ms | 150 iter/s  | 32% slower  |
| 16      | 12.1ms | 165 iter/s  | 26% slower  |

**Conclusion:** More threads = worse performance for small circuits.

---

## Complete Example

```python
from simulation.engine_factory import create_engine
from simulation.vnet_builder import VnetBuilder
from simulation.link_resolver import LinkResolver

# Build VNETs from circuit
vnets = {}
for page in document.pages.values():
    page_vnets = VnetBuilder.build_vnets_for_page(page)
    vnets.update(page_vnets)

# Resolve links
LinkResolver.resolve_links(document, vnets)

# Collect all tabs, bridges, components
tabs = {}
bridges = {}
components = {}

for page in document.pages.values():
    for comp in page.components.values():
        components[comp.component_id] = comp
        for pin in comp.pins.values():
            for tab in pin.tabs.values():
                tabs[tab.tab_id] = tab

# Create engine (auto mode)
engine = create_engine(vnets, tabs, bridges, components)

# Run simulation
if engine.initialize():
    print("Simulation initialized")
    
    stats = engine.run()
    
    print(f"\nSimulation complete!")
    print(f"  State: {engine.state}")
    print(f"  Iterations: {stats.iterations}")
    print(f"  Time to stability: {stats.time_to_stability:.6f}s")
    print(f"  Components updated: {stats.components_updated}")
    
    # Shutdown
    engine.shutdown()
else:
    print("Failed to initialize simulation")
```

---

## Migration from Old Code

### Before (Phase 4 - Manual Selection)

```python
# Old approach - manual engine creation
from simulation.simulation_engine import SimulationEngine
from simulation.threaded_simulation_engine import ThreadedSimulationEngine

# Had to manually choose
if component_count > 1000:
    engine = ThreadedSimulationEngine(vnets, tabs, bridges, components)
else:
    engine = SimulationEngine(vnets, tabs, bridges, components)
```

### After (Phase 5.4 - Factory Pattern)

```python
# New approach - automatic selection
from simulation.engine_factory import create_engine

# Factory handles selection
engine = create_engine(vnets, tabs, bridges, components)
```

**Benefits:**
- Automatic optimal selection
- Easier to use
- Consistent API
- Performance-based defaults
- Easy to override when needed

---

## Advanced: Custom Threshold

If your use case has different performance characteristics:

```python
from simulation.engine_factory import create_engine

# Custom threshold: use multi-threaded only for 5000+ components
engine = create_engine(
    vnets, tabs, bridges, components,
    mode='auto',
    auto_threshold=5000
)
```

---

## Troubleshooting

### Engine Not Initializing

```python
if not engine.initialize():
    # Check for errors
    print("Initialization failed")
    # Common causes:
    # - Components missing pins
    # - VNETs not built correctly
    # - Bridge manager issues
```

### Slow Performance

```python
# Check which engine type was selected
print(f"Engine type: {type(engine).__name__}")
print(f"Component count: {len(components)}")

# If using multi-threaded for small circuit, force single:
engine = create_engine(vnets, tabs, bridges, components, mode='single')
```

### Thread Count Issues

```python
# Check thread count
if hasattr(engine, 'thread_pool'):
    print(f"Using {engine.thread_pool.thread_count} threads")

# Reduce thread count if too high
engine = create_engine(
    vnets, tabs, bridges, components,
    mode='multi',
    thread_count=2  # Lower thread count
)
```

---

## See Also

- `THREADING_BOTTLENECK_ANALYSIS.md` - Detailed performance analysis
- `testing/performance_benchmark.py` - Benchmarking tool
- `testing/threading_overhead_profiler.py` - Profiling tool
- `simulation/simulation_engine.py` - Single-threaded engine
- `simulation/threaded_simulation_engine.py` - Multi-threaded engine
