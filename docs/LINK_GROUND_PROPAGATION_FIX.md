# Link Ground Propagation Fix

## Issue Description

When using Link objects to connect components across pages or within the same page, ground propagation was not working correctly when relay bridge states changed. 

**Specific Problem:**
- If Relay A (GroundDPDTRelay) is powered first, then Relay B is energized to create a bridge to GND
- Relay A would not detect the newly available ground connection
- Relay A would fail to energize even though a valid ground path exists

**Root Cause:**
The `BridgeManager._get_connected_vnet_network()` method only followed bridge connections when determining which components to re-evaluate after a bridge state change. It did not follow link names, so components connected via Link objects were not notified when bridges changed state on link-connected VNETs.

## Circuit Example

```
Switch A -> Relay A COIL
            Relay A GND -> Link "GND"
            
Switch B -> Relay B COIL
            Relay B COM1 -> Link "GND"
            Relay B NO1 -> GND component
```

When Relay B energizes:
1. Creates bridge: COM1 <-> NO1
2. This connects Link "GND" to the actual GND component
3. But Relay A (also connected to Link "GND") was not notified of this change
4. Relay A never re-checked its ground connection

## Solution

### File: `relay_simulator/simulation/bridge_manager.py`

#### Change 1: Follow link names in network traversal

Modified `_get_connected_vnet_network()` to follow both bridges AND link names when building the connected network:

```python
def _get_connected_vnet_network(self, start_vnet_id: str) -> set:
    """
    Get all VNETs transitively connected through bridges and links.
    ...
    """
    connected = set()
    queue = [start_vnet_id]
    
    while queue:
        current_id = queue.pop(0)
        
        if current_id in connected:
            continue
            
        connected.add(current_id)
        current_vnet = self.vnets.get(current_id)
        
        if not current_vnet:
            continue
        
        # Follow all bridges from this VNET
        for bridge_id in current_vnet.bridge_ids:
            bridge = self.bridges.get(bridge_id)
            if bridge:
                other_id = bridge.get_other_vnet(current_id)
                if other_id and other_id not in connected:
                    queue.append(other_id)
        
        # Follow all link names from this VNET (NEW!)
        for link_name in current_vnet.link_names:
            for other_vnet_id, other_vnet in self.vnets.items():
                if other_vnet_id != current_id and other_vnet.has_link(link_name):
                    if other_vnet_id not in connected:
                        queue.append(other_vnet_id)
    
    return connected
```

#### Change 2: Fix attribute name bug

Fixed `get_bridges_for_component()` and `remove_bridges_for_component()` to use the correct attribute name:
- Changed `b.component_id` to `b.owner_component_id` (the correct Bridge attribute)

```python
def get_bridges_for_component(self, component_id: str) -> list:
    return [b for b in self.bridges.values() if b.owner_component_id == component_id]

def remove_bridges_for_component(self, component_id: str):
    bridge_ids = [bid for bid, b in self.bridges.items() if b.owner_component_id == component_id]
    for bridge_id in bridge_ids:
        self.remove_bridge(bridge_id)  # Use remove_bridge to trigger component queuing
```

## Testing

Created comprehensive tests in:
- `relay_simulator/testing/test_link_ground_propagation.py` - Basic link resolution verification
- `relay_simulator/testing/test_link_ground_propagation_simulation.py` - Single scenario simulation test  
- `relay_simulator/testing/test_link_ground_propagation_comprehensive.py` - Both scenarios verification

### Test Results

Both scenarios now work correctly:

**Scenario 1: Power Relay A first, then Relay B**
- ✓ Relay A detects no ground initially (correct)
- ✓ Relay B energizes and creates bridge to GND
- ✓ Relay A is notified via link-connected network traversal
- ✓ Relay A re-checks and finds ground connection
- ✓ Relay A energizes successfully

**Scenario 2: Power Relay B first, then Relay A**  
- ✓ Relay B energizes first, creating bridge to GND
- ✓ Relay A detects ground immediately through link (correct)
- ✓ Relay A energizes successfully

## Impact

This fix ensures that:
1. Ground propagation works correctly through Link objects
2. Components are properly notified when bridge states change on link-connected VNETs
3. Complex circuits with cross-page connections via Links work as expected
4. GroundDPDTRelay and GroundLatchingRelay components can detect ground through any combination of bridges and links

## Backward Compatibility

The fix is fully backward compatible:
- No file format changes
- No API changes
- Existing circuits continue to work as before
- Only fixes the previously broken case
