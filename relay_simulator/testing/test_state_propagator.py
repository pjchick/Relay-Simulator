"""
Test Suite for State Propagation System (Phase 4.2)

This test suite validates the state propagation logic that updates VNET states
and propagates those changes throughout the electrical network.

Tests cover:
1. Basic propagation to single VNET
2. Tab and pin state updates
3. Link-based propagation across pages
4. Bridge-based propagation via relays
5. Circular link detection and handling
6. Circular bridge detection and handling
7. Batch propagation of multiple VNETs
8. Propagation chain analysis
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.state import PinState
from core.vnet import VNET
from core.tab import Tab
from core.pin import Pin
from components.base import Component
from core.bridge import Bridge, BridgeManager
from simulation.state_propagator import StatePropagator


# Mock component for testing
class MockComponent(Component):
    """Minimal component for testing."""
    
    component_type = "mock"
    
    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)
    
    def simulate_logic(self, vnet_manager):
        pass
    
    def sim_start(self, vnet_manager, bridge_manager):
        pass
    
    def sim_stop(self):
        pass
    
    def interact(self, interaction_type: str) -> bool:
        return False
    
    def render(self, canvas_adapter) -> dict:
        return {'type': 'mock'}


def test_basic_propagation():
    """Test basic state propagation to a single VNET."""
    print("Test 1: Basic propagation to single VNET")
    
    # Create component and pin
    comp = MockComponent(component_id="comp001", page_id="page001")
    pin = Pin(pin_id="pin001", parent_component=comp)
    tab = Tab(tab_id="tab001", parent_pin=pin, relative_position=(0, 10))
    
    # Create VNET
    vnet = VNET(vnet_id="vnet001", page_id="page001")
    vnet.add_tab("tab001")
    vnet.state = PinState.FLOAT  # Start at FLOAT
    
    # Create propagator
    all_vnets = {"vnet001": vnet}
    all_tabs = {"tab001": tab}
    all_bridges = {}
    propagator = StatePropagator(all_vnets, all_tabs, all_bridges)
    
    # Propagate HIGH state
    affected = propagator.propagate_vnet_state(vnet, PinState.HIGH)
    
    # Verify VNET state updated
    assert vnet.state == PinState.HIGH, f"VNET state should be HIGH, got {vnet.state}"
    assert "vnet001" in affected, "VNET should be in affected set"
    assert len(affected) == 1, f"Only 1 VNET should be affected, got {len(affected)}"
    
    print("  ✓ VNET state updated to HIGH")
    print("  ✓ Affected VNETs tracked correctly")
    print()


def test_pin_tab_update():
    """Test that propagation updates pins and tabs."""
    print("Test 2: Pin and tab state updates")
    
    # Create component with multiple tabs on one pin
    comp = MockComponent(component_id="comp001", page_id="page001")
    pin = Pin(pin_id="pin001", parent_component=comp)
    tab1 = Tab(tab_id="tab001", parent_pin=pin, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin, relative_position=(10, 0))
    tab3 = Tab(tab_id="tab003", parent_pin=pin, relative_position=(0, -10))
    
    # Set initial state
    pin.set_state(PinState.FLOAT)
    
    # Create VNET with all tabs
    vnet = VNET(vnet_id="vnet001", page_id="page001")
    vnet.add_tab("tab001")
    vnet.add_tab("tab002")
    vnet.add_tab("tab003")
    vnet.state = PinState.FLOAT
    
    # Create propagator
    all_vnets = {"vnet001": vnet}
    all_tabs = {"tab001": tab1, "tab002": tab2, "tab003": tab3}
    all_bridges = {}
    propagator = StatePropagator(all_vnets, all_tabs, all_bridges)
    
    # Propagate HIGH state
    propagator.propagate_vnet_state(vnet, PinState.HIGH)
    
    # Verify pin state updated
    assert pin.state == PinState.HIGH, f"Pin state should be HIGH, got {pin.state}"
    
    # Verify all tabs reflect the new state
    assert tab1.state == PinState.HIGH, "Tab1 should be HIGH"
    assert tab2.state == PinState.HIGH, "Tab2 should be HIGH"
    assert tab3.state == PinState.HIGH, "Tab3 should be HIGH"
    
    print("  ✓ Pin state updated to HIGH")
    print("  ✓ All tabs reflect new state")
    print()


def test_link_propagation():
    """Test propagation through linked VNETs."""
    print("Test 3: Link-based propagation across pages")
    
    # Create two components on different pages
    comp1 = MockComponent(component_id="comp001", page_id="page001")
    comp2 = MockComponent(component_id="comp002", page_id="page002")
    
    pin1 = Pin(pin_id="pin001", parent_component=comp1)
    pin2 = Pin(pin_id="pin002", parent_component=comp2)
    
    tab1 = Tab(tab_id="tab001", parent_pin=pin1, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin2, relative_position=(10, 0))
    
    # Set initial states
    pin1.set_state(PinState.FLOAT)
    pin2.set_state(PinState.FLOAT)
    
    # Create two VNETs with same link name
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet1.add_tab("tab001")
    vnet1.add_link("POWER")
    vnet1.state = PinState.FLOAT
    
    vnet2 = VNET(vnet_id="vnet002", page_id="page002")
    vnet2.add_tab("tab002")
    vnet2.add_link("POWER")
    vnet2.state = PinState.FLOAT
    
    # Create propagator
    all_vnets = {"vnet001": vnet1, "vnet002": vnet2}
    all_tabs = {"tab001": tab1, "tab002": tab2}
    all_bridges = {}
    propagator = StatePropagator(all_vnets, all_tabs, all_bridges)
    
    # Propagate HIGH to vnet1
    affected = propagator.propagate_vnet_state(vnet1, PinState.HIGH)
    
    # Verify both VNETs updated (linked)
    assert vnet1.state == PinState.HIGH, "VNET1 should be HIGH"
    assert vnet2.state == PinState.HIGH, "VNET2 should be HIGH (linked)"
    assert len(affected) == 2, f"Both VNETs should be affected, got {len(affected)}"
    assert "vnet001" in affected and "vnet002" in affected, "Both VNETs in affected set"
    
    # Verify pins updated
    assert pin1.state == PinState.HIGH, "Pin1 should be HIGH"
    assert pin2.state == PinState.HIGH, "Pin2 should be HIGH (linked)"
    
    print("  ✓ State propagated through link")
    print("  ✓ Both VNETs updated to HIGH")
    print("  ✓ Both pins updated to HIGH")
    print()


def test_bridge_propagation():
    """Test propagation through bridged VNETs."""
    print("Test 4: Bridge-based propagation via relays")
    
    # Create components
    comp1 = MockComponent(component_id="comp001", page_id="page001")
    comp2 = MockComponent(component_id="comp002", page_id="page001")
    
    pin1 = Pin(pin_id="pin001", parent_component=comp1)
    pin2 = Pin(pin_id="pin002", parent_component=comp2)
    
    tab1 = Tab(tab_id="tab001", parent_pin=pin1, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin2, relative_position=(10, 0))
    
    # Set initial states
    pin1.set_state(PinState.FLOAT)
    pin2.set_state(PinState.FLOAT)
    
    # Create two separate VNETs
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet1.add_tab("tab001")
    vnet1.state = PinState.FLOAT
    
    vnet2 = VNET(vnet_id="vnet002", page_id="page001")
    vnet2.add_tab("tab002")
    vnet2.state = PinState.FLOAT
    
    # Create bridge connecting the VNETs
    bridge_mgr = BridgeManager()
    bridge = bridge_mgr.create_bridge("vnet001", "vnet002", "relay001")
    vnet1.add_bridge(bridge.bridge_id)
    vnet2.add_bridge(bridge.bridge_id)
    
    # Create propagator
    all_vnets = {"vnet001": vnet1, "vnet002": vnet2}
    all_tabs = {"tab001": tab1, "tab002": tab2}
    all_bridges = {bridge.bridge_id: bridge}
    propagator = StatePropagator(all_vnets, all_tabs, all_bridges)
    
    # Propagate HIGH to vnet1
    affected = propagator.propagate_vnet_state(vnet1, PinState.HIGH)
    
    # Verify both VNETs updated (bridged)
    assert vnet1.state == PinState.HIGH, "VNET1 should be HIGH"
    assert vnet2.state == PinState.HIGH, "VNET2 should be HIGH (bridged)"
    assert len(affected) == 2, f"Both VNETs should be affected, got {len(affected)}"
    
    # Verify pins updated
    assert pin1.state == PinState.HIGH, "Pin1 should be HIGH"
    assert pin2.state == PinState.HIGH, "Pin2 should be HIGH (bridged)"
    
    print("  ✓ State propagated through bridge")
    print("  ✓ Both VNETs updated to HIGH")
    print("  ✓ Both pins updated to HIGH")
    print()


def test_circular_links():
    """Test propagation with circular link connections."""
    print("Test 5: Circular link detection and handling")
    
    # Create three components with circular links
    comp1 = MockComponent(component_id="comp001", page_id="page001")
    comp2 = MockComponent(component_id="comp002", page_id="page002")
    comp3 = MockComponent(component_id="comp003", page_id="page003")
    
    pin1 = Pin(pin_id="pin001", parent_component=comp1)
    pin2 = Pin(pin_id="pin002", parent_component=comp2)
    pin3 = Pin(pin_id="pin003", parent_component=comp3)
    
    tab1 = Tab(tab_id="tab001", parent_pin=pin1, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin2, relative_position=(10, 0))
    tab3 = Tab(tab_id="tab003", parent_pin=pin3, relative_position=(0, -10))
    
    pin1.set_state(PinState.FLOAT)
    pin2.set_state(PinState.FLOAT)
    pin3.set_state(PinState.FLOAT)
    
    # Create circular link structure: A↔B, B↔C, C↔A
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet1.add_tab("tab001")
    vnet1.add_link("LINK_AB")
    vnet1.add_link("LINK_CA")
    vnet1.state = PinState.FLOAT
    
    vnet2 = VNET(vnet_id="vnet002", page_id="page002")
    vnet2.add_tab("tab002")
    vnet2.add_link("LINK_AB")
    vnet2.add_link("LINK_BC")
    vnet2.state = PinState.FLOAT
    
    vnet3 = VNET(vnet_id="vnet003", page_id="page003")
    vnet3.add_tab("tab003")
    vnet3.add_link("LINK_BC")
    vnet3.add_link("LINK_CA")
    vnet3.state = PinState.FLOAT
    
    # Create propagator
    all_vnets = {"vnet001": vnet1, "vnet002": vnet2, "vnet003": vnet3}
    all_tabs = {"tab001": tab1, "tab002": tab2, "tab003": tab3}
    all_bridges = {}
    propagator = StatePropagator(all_vnets, all_tabs, all_bridges)
    
    # Propagate HIGH to vnet1 (should not hang)
    affected = propagator.propagate_vnet_state(vnet1, PinState.HIGH)
    
    # Verify all VNETs updated
    assert vnet1.state == PinState.HIGH, "VNET1 should be HIGH"
    assert vnet2.state == PinState.HIGH, "VNET2 should be HIGH"
    assert vnet3.state == PinState.HIGH, "VNET3 should be HIGH"
    assert len(affected) == 3, f"All 3 VNETs should be affected, got {len(affected)}"
    
    print("  ✓ Circular links handled (no infinite loop)")
    print("  ✓ All VNETs in circular network updated")
    print()


def test_circular_bridges():
    """Test propagation with circular bridge connections."""
    print("Test 6: Circular bridge detection and handling")
    
    # Create components
    comp1 = MockComponent(component_id="comp001", page_id="page001")
    comp2 = MockComponent(component_id="comp002", page_id="page001")
    comp3 = MockComponent(component_id="comp003", page_id="page001")
    
    pin1 = Pin(pin_id="pin001", parent_component=comp1)
    pin2 = Pin(pin_id="pin002", parent_component=comp2)
    pin3 = Pin(pin_id="pin003", parent_component=comp3)
    
    tab1 = Tab(tab_id="tab001", parent_pin=pin1, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin2, relative_position=(10, 0))
    tab3 = Tab(tab_id="tab003", parent_pin=pin3, relative_position=(0, -10))
    
    pin1.set_state(PinState.FLOAT)
    pin2.set_state(PinState.FLOAT)
    pin3.set_state(PinState.FLOAT)
    
    # Create VNETs
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet1.add_tab("tab001")
    vnet1.state = PinState.FLOAT
    
    vnet2 = VNET(vnet_id="vnet002", page_id="page001")
    vnet2.add_tab("tab002")
    vnet2.state = PinState.FLOAT
    
    vnet3 = VNET(vnet_id="vnet003", page_id="page001")
    vnet3.add_tab("tab003")
    vnet3.state = PinState.FLOAT
    
    # Create circular bridges: 1→2, 2→3, 3→1
    bridge_mgr = BridgeManager()
    bridge1 = bridge_mgr.create_bridge("vnet001", "vnet002", "relay001")
    bridge2 = bridge_mgr.create_bridge("vnet002", "vnet003", "relay002")
    bridge3 = bridge_mgr.create_bridge("vnet003", "vnet001", "relay003")
    
    vnet1.add_bridge(bridge1.bridge_id)
    vnet1.add_bridge(bridge3.bridge_id)
    vnet2.add_bridge(bridge1.bridge_id)
    vnet2.add_bridge(bridge2.bridge_id)
    vnet3.add_bridge(bridge2.bridge_id)
    vnet3.add_bridge(bridge3.bridge_id)
    
    # Create propagator
    all_vnets = {"vnet001": vnet1, "vnet002": vnet2, "vnet003": vnet3}
    all_tabs = {"tab001": tab1, "tab002": tab2, "tab003": tab3}
    all_bridges = {
        bridge1.bridge_id: bridge1,
        bridge2.bridge_id: bridge2,
        bridge3.bridge_id: bridge3
    }
    propagator = StatePropagator(all_vnets, all_tabs, all_bridges)
    
    # Propagate HIGH to vnet1 (should not hang)
    affected = propagator.propagate_vnet_state(vnet1, PinState.HIGH)
    
    # Verify all VNETs updated
    assert vnet1.state == PinState.HIGH, "VNET1 should be HIGH"
    assert vnet2.state == PinState.HIGH, "VNET2 should be HIGH"
    assert vnet3.state == PinState.HIGH, "VNET3 should be HIGH"
    assert len(affected) == 3, f"All 3 VNETs should be affected, got {len(affected)}"
    
    print("  ✓ Circular bridges handled (no infinite loop)")
    print("  ✓ All VNETs in circular network updated")
    print()


def test_batch_propagation():
    """Test batch propagation to multiple VNETs."""
    print("Test 7: Batch propagation of multiple VNETs")
    
    # Create several independent VNETs
    vnets = []
    pins = []
    tabs = []
    
    for i in range(5):
        comp = MockComponent(component_id=f"comp{i:03d}", page_id="page001")
        pin = Pin(pin_id=f"pin{i:03d}", parent_component=comp)
        tab = Tab(tab_id=f"tab{i:03d}", parent_pin=pin, relative_position=(0, 10))
        vnet = VNET(vnet_id=f"vnet{i:03d}", page_id="page001")
        vnet.add_tab(f"tab{i:03d}")
        vnet.state = PinState.FLOAT
        
        pin.set_state(PinState.FLOAT)
        
        vnets.append(vnet)
        pins.append(pin)
        tabs.append(tab)
    
    # Create propagator
    all_vnets = {vnet.vnet_id: vnet for vnet in vnets}
    all_tabs = {tab.tab_id: tab for tab in tabs}
    all_bridges = {}
    propagator = StatePropagator(all_vnets, all_tabs, all_bridges)
    
    # Batch propagate: set vnets 0, 2, 4 to HIGH
    vnet_states = {
        "vnet000": PinState.HIGH,
        "vnet002": PinState.HIGH,
        "vnet004": PinState.HIGH
    }
    
    affected = propagator.propagate_multiple_vnets(vnet_states)
    
    # Verify correct VNETs updated
    assert vnets[0].state == PinState.HIGH, "VNET0 should be HIGH"
    assert vnets[1].state == PinState.FLOAT, "VNET1 should be FLOAT"
    assert vnets[2].state == PinState.HIGH, "VNET2 should be HIGH"
    assert vnets[3].state == PinState.FLOAT, "VNET3 should be FLOAT"
    assert vnets[4].state == PinState.HIGH, "VNET4 should be HIGH"
    
    assert len(affected) == 3, f"3 VNETs should be affected, got {len(affected)}"
    
    print("  ✓ Batch propagation successful")
    print(f"  ✓ Updated {len(affected)} VNETs")
    print()


def test_propagation_chain():
    """Test propagation chain analysis."""
    print("Test 8: Propagation chain analysis")
    
    # Create linked network: vnet1 ↔ vnet2, vnet1 → vnet3 (bridge)
    comp1 = MockComponent(component_id="comp001", page_id="page001")
    comp2 = MockComponent(component_id="comp002", page_id="page002")
    comp3 = MockComponent(component_id="comp003", page_id="page001")
    
    pin1 = Pin(pin_id="pin001", parent_component=comp1)
    pin2 = Pin(pin_id="pin002", parent_component=comp2)
    pin3 = Pin(pin_id="pin003", parent_component=comp3)
    
    tab1 = Tab(tab_id="tab001", parent_pin=pin1, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin2, relative_position=(10, 0))
    tab3 = Tab(tab_id="tab003", parent_pin=pin3, relative_position=(0, -10))
    
    # Create VNETs
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet1.add_tab("tab001")
    vnet1.add_link("POWER")
    
    vnet2 = VNET(vnet_id="vnet002", page_id="page002")
    vnet2.add_tab("tab002")
    vnet2.add_link("POWER")
    
    vnet3 = VNET(vnet_id="vnet003", page_id="page001")
    vnet3.add_tab("tab003")
    
    # Create bridge vnet1 → vnet3
    bridge_mgr = BridgeManager()
    bridge = bridge_mgr.create_bridge("vnet001", "vnet003", "relay001")
    vnet1.add_bridge(bridge.bridge_id)
    vnet3.add_bridge(bridge.bridge_id)
    
    # Create propagator
    all_vnets = {"vnet001": vnet1, "vnet002": vnet2, "vnet003": vnet3}
    all_tabs = {"tab001": tab1, "tab002": tab2, "tab003": tab3}
    all_bridges = {bridge.bridge_id: bridge}
    propagator = StatePropagator(all_vnets, all_tabs, all_bridges)
    
    # Get propagation chain for vnet1
    chain = propagator.get_propagation_chain(vnet1)
    
    # Verify all connected VNETs in chain
    assert "vnet001" in chain, "VNET1 should be in chain"
    assert "vnet002" in chain, "VNET2 should be in chain (linked)"
    assert "vnet003" in chain, "VNET3 should be in chain (bridged)"
    assert len(chain) == 3, f"Chain should have 3 VNETs, got {len(chain)}"
    
    print("  ✓ Propagation chain identified correctly")
    print(f"  ✓ Chain: {sorted(chain)}")
    print()


def test_no_propagation_when_same_state():
    """Test that propagation is skipped when state doesn't change."""
    print("Test 9: No propagation when state unchanged")
    
    # Create VNET already at HIGH
    comp = MockComponent(component_id="comp001", page_id="page001")
    pin = Pin(pin_id="pin001", parent_component=comp)
    tab = Tab(tab_id="tab001", parent_pin=pin, relative_position=(0, 10))
    
    pin.set_state(PinState.HIGH)
    
    vnet = VNET(vnet_id="vnet001", page_id="page001")
    vnet.add_tab("tab001")
    vnet.state = PinState.HIGH  # Already HIGH
    
    # Create propagator
    all_vnets = {"vnet001": vnet}
    all_tabs = {"tab001": tab}
    all_bridges = {}
    propagator = StatePropagator(all_vnets, all_tabs, all_bridges)
    
    # Try to propagate HIGH (same state)
    affected = propagator.propagate_vnet_state(vnet, PinState.HIGH)
    
    # Verify no VNETs affected (no change)
    assert len(affected) == 0, f"No VNETs should be affected, got {len(affected)}"
    assert vnet.state == PinState.HIGH, "VNET should still be HIGH"
    
    print("  ✓ No propagation when state unchanged")
    print("  ✓ Optimization working correctly")
    print()


def run_all_tests():
    """Run all state propagation tests."""
    print("=" * 60)
    print("STATE PROPAGATION SYSTEM TEST SUITE (Phase 4.2)")
    print("=" * 60)
    print()
    
    tests = [
        test_basic_propagation,
        test_pin_tab_update,
        test_link_propagation,
        test_bridge_propagation,
        test_circular_links,
        test_circular_bridges,
        test_batch_propagation,
        test_propagation_chain,
        test_no_propagation_when_same_state,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All tests PASSED!")
        print("\nState Propagation System implementation verified:")
        print("  ✓ PropagateVnetState(vnet, newState) - Main method")
        print("  ✓ Update VNET state")
        print("  ✓ Update all tab states in VNET")
        print("  ✓ Update pins associated with tabs")
        print("  ✓ Propagate to linked VNETs")
        print("  ✓ Propagate to bridged VNETs")
        print("  ✓ Find all VNETs with same link name")
        print("  ✓ Propagate state to linked VNETs")
        print("  ✓ Avoid infinite loops (links)")
        print("  ✓ Find connected VNETs via bridges")
        print("  ✓ Propagate state to bridged VNETs")
        print("  ✓ Avoid infinite loops (bridges)")
        print("  ✓ Batch propagation support")
        print("  ✓ Propagation chain analysis")
        return 0
    else:
        print(f"\n✗ {failed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
