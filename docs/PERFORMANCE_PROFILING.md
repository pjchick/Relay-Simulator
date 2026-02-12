# Performance Profiling Guide

## Overview

The Relay Simulator now includes comprehensive performance profiling capabilities to help identify bottlenecks in large simulations. This is especially useful when experiencing degraded performance on complex designs with many wires and components.

## Accessing the Performance Report

### Method 1: Menu
1. Run your simulation
2. Go to **Tools → Performance Report...** (or press `Ctrl+Shift+P`)
3. View the detailed timing breakdown

### Method 2: Code
```python
from performance_profiler import get_profiler, print_performance_report

# Get metrics
profiler = get_profiler()
print_performance_report(sort_by='total')  # Options: 'total', 'avg', 'max', 'count'
```

## Understanding the Report

The performance report shows timing information for key operations:

```
==================================================================================================
PERFORMANCE PROFILE
==================================================================================================
Operation                                   Count     Total        Avg     Median        P95        Min        Max
--------------------------------------------------------------------------------------------------
gui_update_simulation_visuals                  23    12.456s    541.6ms    523.1ms    678.2ms    201.3ms    892.1ms
gui_render_wires_total                         23     8.234s    358.0ms    341.2ms    445.6ms    156.7ms    623.4ms
gui_check_wire_powered                      12456     6.123s      0.5ms      0.4ms      1.2ms      0.1ms      5.3ms
gui_render_components_total                    23     3.012s    131.0ms    125.4ms    167.8ms     89.2ms    234.5ms
sim_evaluate_vnets                            145     0.867s      6.0ms      5.2ms     12.3ms      1.1ms     34.2ms
sim_component_updates                         145     0.523s      3.6ms      3.1ms      7.8ms      0.8ms     21.4ms
==================================================================================================
```

### Key Metrics:
- **Operation**: Name of the timed operation
- **Count**: Number of times the operation was executed
- **Total**: Total time spent in this operation
- **Avg**: Average time per execution
- **Median**: Median time (50th percentile)
- **P95**: 95th percentile time (excludes outliers)
- **Min/Max**: Fastest and slowest execution times

## Common Performance Issues

### 1. Excessive GUI Rendering (`gui_render_wires_total`)

**Symptom**: High total time in `gui_render_wires_total` or `gui_check_wire_powered`

**Cause**: Every simulation tick re-renders ALL wires and checks if each is powered by doing a breadth-first graph search through the VNET network.

**Impact**: On pages with thousands of wires (like the Sequencer page), this becomes very expensive.

**Current Status**: 
- The entire page is re-rendered on every simulation update
- Each wire's powered state is recalculated from scratch
- No caching of powered states

### 2. Wire Powered State Checks (`gui_check_wire_powered`)

**Symptom**: Very high count and total time for `gui_check_wire_powered`

**Cause**: Each wire does a BFS graph traversal to determine if it's connected to powered VNETs.

**Impact**: O(V+E) complexity per wire, where V=VNETs and E=bridges/links.

### 3. Component Rendering (`gui_render_components_total`)

**Symptom**: High time in component rendering

**Cause**: All component renderers are destroyed and recreated on every update.

**Impact**: Memory allocation overhead and redundant rendering of unchanged components.

## Optimization Recommendations

### Short-term Improvements (Easy):
1. **Cache Wire Powered States**: Only recalculate when VNETs change
2. **Incremental Rendering**: Only update components/wires that changed
3. **Reduce Render Frequency**: Throttle visual updates to max 30 FPS (33ms)

### Medium-term Improvements (Moderate):
1. **Dirty Flag System for GUI**: Track which components/wires need visual update
2. **Powered State in VNET**: Pre-compute and cache powered state in VNET objects
3. **Spatial Indexing**: Use quad-tree to only render visible wires/components

### Long-term Improvements (Complex):
1. **Lazy Rendering**: Use canvas virtual scrolling to only render visible region
2. **WebGL/GPU Acceleration**: For very large simulations
3. **Simulation/Rendering Decoupling**: Run simulation at full speed, render at 30 FPS

## Measuring Specific Operations

You can add custom profiling to your code:

```python
from performance_profiler import get_profiler

profiler = get_profiler()

# Method 1: Context manager
with profiler.measure("my_operation"):
    # ... do work ...
    pass

# Method 2: Manual timing
profiler.start_measure("my_operation")
# ... do work ...
profiler.end_measure("my_operation")

# Get report
print(profiler.get_report())
```

## Resetting Metrics

To start fresh measurements:
- **Menu**: Tools → Reset Performance Metrics
- **Code**: `from performance_profiler import reset_profiler; reset_profiler()`

## Performance Test Script

Run the performance test to see detailed metrics:

```bash
python relay_simulator/testing/test_performance.py
```

This will load the 12-bit Relay Computer, run the simulation, and display performance breakdown.

## Tips for Large Simulations

1. **Start Simple**: Profile with a small design first to establish baseline
2. **Page-by-Page**: Different pages may have different bottlenecks
3. **Watch the Logs**: Slow renders (>10ms) are logged as warnings
4. **Monitor Real-time**: Keep the Performance Report window open and refresh periodically
5. **Compare Designs**: Profile different page types to identify patterns

## Known Bottlenecks

Based on profiling the 12-bit Relay Computer example:

| Operation | Time % | Bottleneck |
|-----------|--------|------------|
| Wire powered checks | ~50% | BFS graph traversal per wire |
| Wire rendering | ~20% | Creating/destroying renderers |
| Component rendering | ~15% | Recreating all renderers |
| Simulation engine | ~10% | VNET evaluation |
| Other GUI | ~5% | Event handling, etc. |

**Conclusion**: The GUI rendering (particularly wire powered state checks) dominates the total time, not the simulation engine itself. Optimizing the rendering pipeline will provide the most significant performance gains.

## Future Work

- Implement incremental rendering (only update changed wires/components)
- Add powered state caching in VNET objects
- Create render throttling (max 30 FPS updates)
- Add visual indicator when rendering is slow (show FPS counter)
- Implement "performance mode" that disables some visual features

## Support

If you encounter performance issues not covered here, please:
1. Capture the Performance Report
2. Note your page complexity (# components, # wires)
3. Include your `.rsim` file if possible
4. Report the issue with these details
