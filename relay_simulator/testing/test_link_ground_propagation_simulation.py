"""
Test for Link Ground Propagation Fix

Tests that ground propagation through Link objects works correctly
when bridges change state.
"""

import sys
import os

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fileio.document_loader import load_document
from core.vnet_builder import VnetBuilder
from core.link_resolver import LinkResolver
from core.state import PinState
from simulation.vnet_manager import VnetManager
from simulation.bridge_manager import BridgeManager
from core.id_manager import IDManager
from simulation.component_update_coordinator import ComponentUpdateCoordinator
from simulation.dirty_flag_manager import DirtyFlagManager


def test_link_ground_propagation_simulation():
    """Test that ground propagates correctly when relay state changes."""
    print("\n=== Testing Link Ground Propagation with Simulation ===")
    
    # Load the example file
    filepath = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'Link Ground Propergation.rsim')
    doc = load_document(filepath)
    
    print(f"✓ Loaded document with {len(doc.get_all_pages())} page(s)")
    
    # Build VNETs for all pages
    builder = VnetBuilder()
    all_vnets = []
    for page in doc.get_all_pages():
        page_vnets = builder.build_vnets_for_page(page)
        all_vnets.extend(page_vnets)
    
    print(f"✓ Built {len(all_vnets)} VNETs")
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, all_vnets)
    print(f"✓ Link resolution: {result.total_links} links, {result.vnets_with_links} VNETs with links")
    
    # Create VNET manager
    vnets_dict = {vnet.vnet_id: vnet for vnet in all_vnets}
    tabs_dict = {}
    for page in doc.get_all_pages():
        for component in page.get_all_components():
            for pin in component.get_all_pins().values():
                for tab in pin.tabs.values():
                    tabs_dict[tab.tab_id] = tab
    
    components_dict = {}
    for page in doc.get_all_pages():
        for component in page.get_all_components():
            components_dict[component.component_id] = component
    
    coordinator = ComponentUpdateCoordinator(components_dict, vnets_dict)
    dirty_manager = DirtyFlagManager(vnets_dict)
    vnet_manager = VnetManager(vnets_dict, tabs_dict, dirty_manager)
    bridge_manager = BridgeManager({}, IDManager(), vnets_dict, coordinator)
    
    # Get the relay components
    relay_a = None
    relay_b = None
    switch_a = None
    switch_b = None
    
    for page in doc.get_all_pages():
        for component in page.get_all_components():
            if hasattr(component, 'component_type'):
                if component.component_type == "GroundDPDTRelay":
                    relay_a = component
                    print(f"✓ Found Relay A: {component.component_id}")
                elif component.component_type == "DPDTRelay":
                    relay_b = component
                    print(f"✓ Found Relay B: {component.component_id}")
                elif component.component_type == "Switch":
                    # Identify which switch is which based on position
                    if component.position[0] < 300:  # Left switch controls Relay A
                        switch_a = component
                        print(f"✓ Found Switch A: {component.component_id}")
                    else:  # Right switch controls Relay B
                        switch_b = component
                        print(f"✓ Found Switch B: {component.component_id}")
    
    # Initialize simulation
    print("\n=== Initializing Simulation ===")
    for component in components_dict.values():
        component.sim_start(vnet_manager, bridge_manager)
    
    print(f"Relay A energized: {relay_a._is_energized}")
    print(f"Relay B energized: {relay_b._is_energized}")
    
    # Test 1: Power Relay A first, then Relay B
    print("\n=== Test 1: Power Relay A first, then Relay B ===")
    
    # Power Relay A coil
    switch_a_pin = list(switch_a.get_all_pins().values())[0]
    switch_a_pin.set_state(PinState.HIGH)
    for tab in switch_a_pin.tabs.values():
        vnet = vnet_manager.get_vnet_for_tab(tab.tab_id)
        if vnet:
            vnet.state = PinState.HIGH
    
    print("Powered Relay A coil")
    
    # Check if Relay A can see ground (should not yet, because Relay B is not energized)
    gnd_connected_before = relay_a._is_gnd_connected(vnet_manager, bridge_manager)
    print(f"Relay A GND connected (before Relay B): {gnd_connected_before}")
    
    # Simulate Relay A
    relay_a.simulate_logic(vnet_manager, bridge_manager)
    print(f"Relay A energized (after simulate): {relay_a._is_energized}")
    print(f"Relay A target energized: {relay_a._target_energized}")
    
    # Now power Relay B coil
    switch_b_pin = list(switch_b.get_all_pins().values())[0]
    switch_b_pin.set_state(PinState.HIGH)
    for tab in switch_b_pin.tabs.values():
        vnet = vnet_manager.get_vnet_for_tab(tab.tab_id)
        if vnet:
            vnet.state = PinState.HIGH
    
    print("\nPowered Relay B coil")
    
    # Simulate Relay B
    relay_b.simulate_logic(vnet_manager, bridge_manager)
    print(f"Relay B energized (after simulate): {relay_b._is_energized}")
    print(f"Relay B target energized: {relay_b._target_energized}")
    
    # Wait for timer (simulate)
    import time
    time.sleep(0.015)  # Wait for 15ms (longer than 10ms switching delay)
    
    # Check if Relay B has created the bridge
    relay_b_bridges = bridge_manager.get_bridges_for_component(relay_b.component_id)
    print(f"Relay B bridges: {len(relay_b_bridges)} created")
    
    # Now check if Relay A can see ground (should now work with the fix!)
    gnd_connected_after = relay_a._is_gnd_connected(vnet_manager, bridge_manager)
    print(f"\nRelay A GND connected (after Relay B energized): {gnd_connected_after}")
    
    # The fix should ensure Relay A was queued for re-evaluation when Relay B's bridge was created
    # So let's simulate Relay A again
    relay_a.simulate_logic(vnet_manager, bridge_manager)
    print(f"Relay A target energized (after Relay B bridge): {relay_a._target_energized}")
    
    # Wait for timer
    time.sleep(0.015)
    
    print(f"Relay A energized (final): {relay_a._is_energized}")
    
    if relay_a._is_energized:
        print("\n✓ SUCCESS: Relay A energized after Relay B created bridge to GND!")
    else:
        print("\n✗ FAILED: Relay A did not energize even though ground path exists")
    
    print("\n✓ Link ground propagation simulation test complete")
    
    return relay_a._is_energized


if __name__ == "__main__":
    success = test_link_ground_propagation_simulation()
    if not success:
        print("\n⚠ Test revealed the issue still exists")
        sys.exit(1)
