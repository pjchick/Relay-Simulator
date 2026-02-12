# Simulation Rate Limiting

## Problem

The Relay Simulator was experiencing GUI unresponsiveness on complex circuits (e.g., the Sequencer page with 2000+ wires) because:

1. **Unlimited simulation loop**: The simulation was running as fast as possible with `after(0, ...)`, potentially hundreds of times per second
2. **GUI thread saturation**: Even with 30 FPS render throttling, the simulation loop was constantly scheduling work on the GUI thread
3. **Event queue blocking**: User events (like clicking Stop button) couldn't be processed because the GUI thread was too busy

## Solution

### Adaptive Simulation Rate Limiting

Limited the simulation loop to run at a maximum of **30 Hz** (33.3ms between steps):

```python
# Added in MainWindow.__init__
self._last_sim_step_time = 0.0
self._min_sim_step_time = 1.0 / 30.0  # 30 Hz = 33.3ms between simulation steps
```

```python
# Modified in _on_simulation_run_complete()
if run_again:
    # Adaptive rate limiting: Calculate delay needed to maintain target update rate
    now = time.perf_counter()
    time_since_last = now - self._last_sim_step_time
    delay_needed = max(0, self._min_sim_step_time - time_since_last)
    delay_ms = int(delay_needed * 1000)  # Convert to milliseconds
    self._last_sim_step_time = now
    self.root.after(delay_ms, self._run_simulation_step)
```

### Diagnostic Statistics

Added tracking to measure actual simulation frequency:

```python
self._sim_step_count = 0
self._sim_step_time_total = 0.0
```

Added menu item: **Tools > Simulation Statistics** (Ctrl+Shift+I) to view:
- Target rate vs. actual rate
- Total simulation steps
- VNET and component counts
- Render frame rate

## Performance Impact

### Before
- Simulation loop: **Unlimited Hz** (as fast as possible)
- Rendering: **30 FPS** (throttled)
- GUI responsiveness: **Poor** on complex circuits

### After
- Simulation loop: **30 Hz max** (33.3ms minimum delay)
- Rendering: **30 FPS** (throttled)
- GUI responsiveness: **Much improved** - GUI thread has breathing room

## Configuration

The simulation rate is controlled by `_min_sim_step_time` in [main_window.py](../relay_simulator/gui/main_window.py#L92):

```python
self._min_sim_step_time = 1.0 / 30.0  # 30 Hz = 33.3ms between simulation steps
```

To adjust:
- **Slower rate** (better GUI responsiveness): Increase denominator (e.g., `1.0 / 20.0` for 20 Hz)
- **Faster rate** (more responsive simulation): Increase denominator (e.g., `1.0 / 60.0` for 60 Hz)

**Note**: Higher rates may cause GUI unresponsiveness on complex circuits.

## Testing

1. Open **12-bit Relay Computer.rsim**
2. Navigate to **Sequencer** page (2000+ wires)
3. Press **F5** to start simulation
4. Press **Ctrl+Shift+I** to view simulation statistics
5. Try clicking **Stop** button (Shift+F5) - should respond immediately

## Related Optimizations

This rate limiting works together with:
1. **Render throttling** (30 FPS) - Limits visual updates
2. **VNET powered state caching** - Reduces per-wire computation cost
3. **Performance profiling** (Ctrl+Shift+P) - Measures actual bottlenecks

See also:
- [OPTIMIZATIONS_IMPLEMENTED.md](OPTIMIZATIONS_IMPLEMENTED.md)
- [PERFORMANCE_PROFILING.md](PERFORMANCE_PROFILING.md)
- [PERFORMANCE_ANALYSIS_SUMMARY.md](PERFORMANCE_ANALYSIS_SUMMARY.md)
