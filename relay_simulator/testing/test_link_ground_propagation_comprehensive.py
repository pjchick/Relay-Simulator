"""
Comprehensive test for Link Ground Propagation issue fix

Tests both scenarios:
1. Power Relay A first, then Relay B (the problematic case)
2. Power Relay B first, then Relay A (should always work)
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
import time


def setup_simulation():
    """Set up the simulation environment."""
    # Load the example file
    filepath = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'Link Ground Propergation.rsim')
    doc = load_document(filepath)
    
    # Build VNETs for all pages
    builder = VnetBuilder()
    all_vnets = []
    for page in doc.get_all_pages():
        page_vnets = builder.build_vnets_for_page(page)
        all_vnets.extend(page_vnets)
    
    # Resolve links
    resolver = LinkResolver()
    resolver.resolve_links(doc, all_vnets)
    
    # Create managers
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
    
    # Get the relay and switch components
    relay_a = None
    relay_b = None
    switch_a = None
    switch_b = None
    
    for page in doc.get_all_pages():
        for component in page.get_all_components():
            if hasattr(component, 'component_type'):
                if component.component_type == "GroundDPDTRelay":
                    relay_a = component
                elif component.component_type == "DPDTRelay":
                    relay_b = component
                elif component.component_type == "Switch":
                    if component.position[0] < 300:
                        switch_a = component
                    else:
                        switch_b = component
    
    # Initialize simulation
    for component in components_dict.values():
        component.sim_start(vnet_manager, bridge_manager)
    
    return vnet_manager, bridge_manager, relay_a, relay_b, switch_a, switch_b


def power_switch(switch, vnet_manager, state):
    """Power or unpower a switch."""
    switch_pin = list(switch.get_all_pins().values())[0]
    switch_pin.set_state(state)
    for tab in switch_pin.tabs.values():
        vnet = vnet_manager.get_vnet_for_tab(tab.tab_id)
        if vnet:
            vnet.state = state


def test_scenario_a_then_b():
    """Test powering Relay A first, then Relay B."""
    print("\n" + "="*70)
    print("SCENARIO 1: Power Relay A first, then Relay B")
    print("="*70)
    
    vnet_manager, bridge_manager, relay_a, relay_b, switch_a, switch_b = setup_simulation()
    
    # Power Relay A coil
    print("\n1. Powering Relay A coil...")
    power_switch(switch_a, vnet_manager, PinState.HIGH)
    
    # Check if Relay A can see ground (should not yet)
    gnd_connected = relay_a._is_gnd_connected(vnet_manager, bridge_manager)
    print(f"   Relay A GND connected: {gnd_connected}")
    assert not gnd_connected, "Relay A should not see GND yet (Relay B not energized)"
    
    # Simulate Relay A
    relay_a.simulate_logic(vnet_manager, bridge_manager)
    print(f"   Relay A energized: {relay_a._is_energized}")
    assert not relay_a._is_energized, "Relay A should not energize (no ground)"
    
    # Power Relay B coil
    print("\n2. Powering Relay B coil...")
    power_switch(switch_b, vnet_manager, PinState.HIGH)
    
    # Simulate Relay B
    relay_b.simulate_logic(vnet_manager, bridge_manager)
    print(f"   Relay B target energized: {relay_b._target_energized}")
    assert relay_b._target_energized, "Relay B should be set to energize"
    
    # Wait for Relay B timer
    time.sleep(0.015)
    print(f"   Relay B energized: {relay_b._is_energized}")
    
    # Check if Relay A can now see ground
    print("\n3. Checking if Relay A can now see GND...")
    gnd_connected = relay_a._is_gnd_connected(vnet_manager, bridge_manager)
    print(f"   Relay A GND connected: {gnd_connected}")
    assert gnd_connected, "Relay A should now see GND through Link and Relay B bridge"
    
    # Simulate Relay A again (should now detect ground and energize)
    relay_a.simulate_logic(vnet_manager, bridge_manager)
    print(f"   Relay A target energized: {relay_a._target_energized}")
    assert relay_a._target_energized, "Relay A should be set to energize now"
    
    # Wait for Relay A timer
    time.sleep(0.015)
    print(f"   Relay A energized: {relay_a._is_energized}")
    assert relay_a._is_energized, "Relay A should be energized"
    
    print("\n✓ SCENARIO 1 PASSED: Relay A energized after Relay B created bridge!")
    return True


def test_scenario_b_then_a():
    """Test powering Relay B first, then Relay A."""
    print("\n" + "="*70)
    print("SCENARIO 2: Power Relay B first, then Relay A")
    print("="*70)
    
    vnet_manager, bridge_manager, relay_a, relay_b, switch_a, switch_b = setup_simulation()
    
    # Power Relay B coil
    print("\n1. Powering Relay B coil...")
    power_switch(switch_b, vnet_manager, PinState.HIGH)
    
    # Simulate Relay B
    relay_b.simulate_logic(vnet_manager, bridge_manager)
    print(f"   Relay B target energized: {relay_b._target_energized}")
    assert relay_b._target_energized, "Relay B should be set to energize"
    
    # Wait for Relay B timer
    time.sleep(0.015)
    print(f"   Relay B energized: {relay_b._is_energized}")
    assert relay_b._is_energized, "Relay B should be energized"
    
    # Power Relay A coil
    print("\n2. Powering Relay A coil...")
    power_switch(switch_a, vnet_manager, PinState.HIGH)
    
    # Check if Relay A can see ground (should work immediately)
    gnd_connected = relay_a._is_gnd_connected(vnet_manager, bridge_manager)
    print(f"   Relay A GND connected: {gnd_connected}")
    assert gnd_connected, "Relay A should see GND through Link and Relay B bridge"
    
    # Simulate Relay A
    relay_a.simulate_logic(vnet_manager, bridge_manager)
    print(f"   Relay A target energized: {relay_a._target_energized}")
    assert relay_a._target_energized, "Relay A should be set to energize"
    
    # Wait for Relay A timer
    time.sleep(0.015)
    print(f"   Relay A energized: {relay_a._is_energized}")
    assert relay_a._is_energized, "Relay A should be energized"
    
    print("\n✓ SCENARIO 2 PASSED: Relay A energized when GND already available!")
    return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST: Link Ground Propagation Fix")
    print("="*70)
    print("\nThis test verifies that ground propagation through Link objects")
    print("works correctly in both scenarios.")
    
    try:
        result1 = test_scenario_a_then_b()
        result2 = test_scenario_b_then_a()
        
        if result1 and result2:
            print("\n" + "="*70)
            print("✓ ALL TESTS PASSED!")
            print("="*70)
            print("\nThe fix successfully resolves the ground propagation issue.")
            print("Link objects now correctly propagate ground connections when")
            print("bridge states change.")
            sys.exit(0)
        else:
            print("\n✗ SOME TESTS FAILED")
            sys.exit(1)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
