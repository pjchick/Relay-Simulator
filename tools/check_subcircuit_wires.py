"""
Debug script to verify SubTest1.rsim wire connections.

Run this to check if wires are correctly connected to SubCircuit tabs.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def check_subcircuit_connections():
    """Verify SubCircuit tab IDs match wire endpoints."""
    
    with open('examples/SubTest1.rsim', 'r') as f:
        data = json.load(f)
    
    # Get main page
    main_page = data['pages'][0]
    
    # Find SubCircuit component
    subcircuit = None
    for comp in main_page['components']:
        if comp['component_type'] == 'SubCircuit':
            subcircuit = comp
            break
    
    if not subcircuit:
        print("❌ No SubCircuit found!")
        return False
    
    print(f"SubCircuit ID: {subcircuit['component_id']}")
    print(f"SubCircuit Name: {subcircuit['properties']['sub_circuit_name']}")
    print()
    
    # Get all tab IDs from SubCircuit
    subcircuit_tabs = set()
    for pin in subcircuit['pins']:
        print(f"Pin: {pin['pin_id']}")
        for tab in pin['tabs']:
            tab_id = tab['tab_id']
            tab_pos = tab['position']
            subcircuit_tabs.add(tab_id)
            print(f"  Tab: {tab_id} @ ({tab_pos['x']}, {tab_pos['y']})")
    
    print()
    print(f"Total SubCircuit tabs: {len(subcircuit_tabs)}")
    print()
    
    # Check wires
    print("Wires on main page:")
    all_valid = True
    for wire in main_page['wires']:
        wire_id = wire['wire_id']
        start = wire['start_tab_id']
        end = wire['end_tab_id']
        
        start_is_subcircuit = start in subcircuit_tabs
        end_is_subcircuit = end in subcircuit_tabs
        
        status = "✓" if (start_is_subcircuit or end_is_subcircuit) else "○"
        print(f"{status} Wire {wire_id[:8]}...")
        print(f"  Start: {start}")
        print(f"  End:   {end}")
        
        if start_is_subcircuit:
            print(f"  → Start connects to SubCircuit")
        if end_is_subcircuit:
            print(f"  → End connects to SubCircuit")
        
        if not start_is_subcircuit and not end_is_subcircuit:
            print(f"  → No connection to SubCircuit")
        
        # Verify tab IDs have correct format
        for tab_id in [start, end]:
            parts = tab_id.split('.')
            if len(parts) != 3:
                print(f"  ❌ INVALID tab ID format: {tab_id} (should be comp_id.pin_name.tab_name)")
                all_valid = False
        
        print()
    
    return all_valid


if __name__ == "__main__":
    print("="*70)
    print("SubCircuit Wire Connection Checker")
    print("="*70)
    print()
    
    all_valid = check_subcircuit_connections()
    
    print("="*70)
    if all_valid:
        print("✓ All wire connections are valid")
    else:
        print("❌ Some connections are invalid")
    print("="*70)
