# Engine Selection Quick Reference

## TL;DR

```python
from simulation.engine_factory import create_engine

# Just use this - it's automatic and optimal
engine = create_engine(vnets, tabs, bridges, components)
```

---

## When to Override

### Force Single-Threaded (for debugging or small circuits)
```python
engine = create_engine(vnets, tabs, bridges, components, mode='single')
```

### Force Multi-Threaded (for very large circuits >2000 components)
```python
engine = create_engine(vnets, tabs, bridges, components, mode='multi')
```

---

## Performance Quick Facts

| Circuit Size | Use | Why |
|--------------|-----|-----|
| < 500 components | Single-threaded | 2x faster |
| 500-2000 components | Single-threaded | Still faster |
| ≥ 2000 components | Multi-threaded | Benefits from parallelism |

**Default AUTO mode handles this automatically.**

---

## Troubleshooting

**Problem:** Simulation is slow  
**Solution:** Check if using multi-threaded for small circuit. Force single-threaded.

**Problem:** Want to test threading  
**Solution:** Force multi-threaded mode with `mode='multi'`

**Problem:** Want specific thread count  
**Solution:** `create_engine(..., mode='multi', thread_count=4)`

---

## See Full Documentation

- `SIMULATION_ENGINE_USAGE.md` - Complete usage guide
- `THREADING_BOTTLENECK_ANALYSIS.md` - Performance analysis
- `PHASE_5.4_SUMMARY.md` - Implementation summary
