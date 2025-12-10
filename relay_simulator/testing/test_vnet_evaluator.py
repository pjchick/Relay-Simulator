"""
Test Suite for VNET State Evaluator (Phase 4.1)

This test suite validates the VNET state evaluation logic that determines
the electrical state of VNETs based on tabs, links, and bridges.

Tests cover:
1. All tabs FLOAT → VNET should be FLOAT
2. One tab HIGH → VNET should be HIGH
3. Multiple tabs HIGH → VNET should be HIGH
4. Links connecting VNETs → States propagate
5. Bridges connecting VNETs → States propagate
6. Circular link detection
7. Circular bridge detection
8. Multiple VNET batch evaluation
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
from simulation.vnet_evaluator import VnetEvaluator


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


def test_evaluator_all_float():
    """Test VNET evaluation with all tabs FLOAT."""
    print("Test 1: All tabs FLOAT → VNET FLOAT")
    
    # Create mock component
    comp = MockComponent(component_id="comp001", page_id="page001")
    
    # Create pin with 3 tabs
    pin = Pin(pin_id="pin001", parent_component=comp)
    tab1 = Tab(tab_id="tab001", parent_pin=pin, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin, relative_position=(10, 0))
    tab3 = Tab(tab_id="tab003", parent_pin=pin, relative_position=(0, -10))
    
    # Set all tabs to FLOAT (default state)
    pin.set_state(PinState.FLOAT)
    
    # Create VNET with these tabs
    vnet = VNET(vnet_id="vnet001", page_id="page001")
    vnet.add_tab("tab001")
    vnet.add_tab("tab002")
    vnet.add_tab("tab003")
    
    # Create evaluator
    all_vnets = {"vnet001": vnet}
    all_tabs = {"tab001": tab1, "tab002": tab2, "tab003": tab3}
    all_bridges = {}
    evaluator = VnetEvaluator(all_vnets, all_tabs, all_bridges)
    
    # Evaluate
    result = evaluator.evaluate_vnet_state(vnet)
    
    # Verify
    assert result == PinState.FLOAT, f"Expected FLOAT, got {result}"
    print("  ✓ All FLOAT tabs → FLOAT state")
    print()


def test_evaluator_one_high():
    """Test VNET evaluation with one HIGH tab."""
    print("Test 2: One tab HIGH → VNET HIGH")
    
    # Create two separate components with their own pins
    comp1 = MockComponent(component_id="comp001", page_id="page001")
    comp2 = MockComponent(component_id="comp002", page_id="page001")
    
    pin1 = Pin(pin_id="pin001", parent_component=comp1)
    pin2 = Pin(pin_id="pin002", parent_component=comp2)
    
    tab1 = Tab(tab_id="tab001", parent_pin=pin1, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin2, relative_position=(10, 0))
    
    # Set pin1 to HIGH, pin2 to FLOAT
    pin1.set_state(PinState.HIGH)
    pin2.set_state(PinState.FLOAT)
    
    # Create VNET with both tabs
    vnet = VNET(vnet_id="vnet001", page_id="page001")
    vnet.add_tab("tab001")
    vnet.add_tab("tab002")
    
    # Create evaluator
    all_vnets = {"vnet001": vnet}
    all_tabs = {"tab001": tab1, "tab002": tab2}
    all_bridges = {}
    evaluator = VnetEvaluator(all_vnets, all_tabs, all_bridges)
    
    # Evaluate
    result = evaluator.evaluate_vnet_state(vnet)
    
    # Verify
    assert result == PinState.HIGH, f"Expected HIGH, got {result}"
    print("  ✓ One HIGH tab → HIGH state (HIGH OR logic)")
    print()


def test_evaluator_multiple_high():
    """Test VNET evaluation with multiple HIGH tabs."""
    print("Test 3: Multiple tabs HIGH → VNET HIGH")
    
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
    
    # Set all pins to HIGH
    pin1.set_state(PinState.HIGH)
    pin2.set_state(PinState.HIGH)
    pin3.set_state(PinState.HIGH)
    
    # Create VNET
    vnet = VNET(vnet_id="vnet001", page_id="page001")
    vnet.add_tab("tab001")
    vnet.add_tab("tab002")
    vnet.add_tab("tab003")
    
    # Create evaluator
    all_vnets = {"vnet001": vnet}
    all_tabs = {"tab001": tab1, "tab002": tab2, "tab003": tab3}
    all_bridges = {}
    evaluator = VnetEvaluator(all_vnets, all_tabs, all_bridges)
    
    # Evaluate
    result = evaluator.evaluate_vnet_state(vnet)
    
    # Verify
    assert result == PinState.HIGH, f"Expected HIGH, got {result}"
    print("  ✓ Multiple HIGH tabs → HIGH state")
    print()


def test_evaluator_with_links():
    """Test VNET evaluation with cross-page links."""
    print("Test 4: Links connecting VNETs → State propagation")
    
    # Create components on different pages
    comp1 = MockComponent(component_id="comp001", page_id="page001")
    comp2 = MockComponent(component_id="comp002", page_id="page002")
    
    pin1 = Pin(pin_id="pin001", parent_component=comp1)
    pin2 = Pin(pin_id="pin002", parent_component=comp2)
    
    tab1 = Tab(tab_id="tab001", parent_pin=pin1, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin2, relative_position=(10, 0))
    
    # Set pin1 to FLOAT, pin2 to HIGH
    pin1.set_state(PinState.FLOAT)
    pin2.set_state(PinState.HIGH)
    
    # Create two VNETs on different pages with same link name
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet1.add_tab("tab001")
    vnet1.add_link("POWER")  # Link name
    
    vnet2 = VNET(vnet_id="vnet002", page_id="page002")
    vnet2.add_tab("tab002")
    vnet2.add_link("POWER")  # Same link name
    
    # Create evaluator
    all_vnets = {"vnet001": vnet1, "vnet002": vnet2}
    all_tabs = {"tab001": tab1, "tab002": tab2}
    all_bridges = {}
    evaluator = VnetEvaluator(all_vnets, all_tabs, all_bridges)
    
    # Evaluate vnet1 (FLOAT locally, but linked to HIGH vnet2)
    result1 = evaluator.evaluate_vnet_state(vnet1)
    
    # Evaluate vnet2 (HIGH locally)
    result2 = evaluator.evaluate_vnet_state(vnet2)
    
    # Verify both are HIGH (linked)
    assert result1 == PinState.HIGH, f"VNET1 expected HIGH (linked), got {result1}"
    assert result2 == PinState.HIGH, f"VNET2 expected HIGH (source), got {result2}"
    print("  ✓ Linked VNETs share state (HIGH propagates via link)")
    print()


def test_evaluator_with_bridges():
    """Test VNET evaluation with relay bridges."""
    print("Test 5: Bridges connecting VNETs → State propagation")
    
    # Create components
    comp1 = MockComponent(component_id="comp001", page_id="page001")
    comp2 = MockComponent(component_id="comp002", page_id="page001")
    comp3 = MockComponent(component_id="relay001", page_id="page001")
    
    pin1 = Pin(pin_id="pin001", parent_component=comp1)
    pin2 = Pin(pin_id="pin002", parent_component=comp2)
    
    tab1 = Tab(tab_id="tab001", parent_pin=pin1, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin2, relative_position=(10, 0))
    
    # Set pin1 to HIGH, pin2 to FLOAT
    pin1.set_state(PinState.HIGH)
    pin2.set_state(PinState.FLOAT)
    
    # Create two separate VNETs
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet1.add_tab("tab001")
    
    vnet2 = VNET(vnet_id="vnet002", page_id="page001")
    vnet2.add_tab("tab002")
    
    # Create bridge connecting the VNETs (simulating relay contact)
    bridge_mgr = BridgeManager()
    bridge = bridge_mgr.create_bridge("vnet001", "vnet002", "relay001")
    
    # Add bridge references to VNETs
    vnet1.add_bridge(bridge.bridge_id)
    vnet2.add_bridge(bridge.bridge_id)
    
    # Create evaluator
    all_vnets = {"vnet001": vnet1, "vnet002": vnet2}
    all_tabs = {"tab001": tab1, "tab002": tab2}
    all_bridges = {bridge.bridge_id: bridge}
    evaluator = VnetEvaluator(all_vnets, all_tabs, all_bridges)
    
    # Evaluate vnet2 (FLOAT locally, but bridged to HIGH vnet1)
    result2 = evaluator.evaluate_vnet_state(vnet2)
    
    # Verify vnet2 is HIGH (bridged to vnet1)
    assert result2 == PinState.HIGH, f"VNET2 expected HIGH (bridged), got {result2}"
    print("  ✓ Bridged VNETs share state (HIGH propagates via bridge)")
    print()


def test_evaluator_circular_links():
    """Test VNET evaluation with circular link connections."""
    print("Test 6: Circular link detection → No infinite loop")
    
    # Create three components with circular link connections
    # A links to B, B links to C, C links to A
    comp1 = MockComponent(component_id="comp001", page_id="page001")
    comp2 = MockComponent(component_id="comp002", page_id="page002")
    comp3 = MockComponent(component_id="comp003", page_id="page003")
    
    pin1 = Pin(pin_id="pin001", parent_component=comp1)
    pin2 = Pin(pin_id="pin002", parent_component=comp2)
    pin3 = Pin(pin_id="pin003", parent_component=comp3)
    
    tab1 = Tab(tab_id="tab001", parent_pin=pin1, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin2, relative_position=(10, 0))
    tab3 = Tab(tab_id="tab003", parent_pin=pin3, relative_position=(0, -10))
    
    # Set pin2 to HIGH, others to FLOAT
    pin1.set_state(PinState.FLOAT)
    pin2.set_state(PinState.HIGH)
    pin3.set_state(PinState.FLOAT)
    
    # Create VNETs with circular link structure
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet1.add_tab("tab001")
    vnet1.add_link("LINK_AB")
    vnet1.add_link("LINK_CA")  # Circular: C → A
    
    vnet2 = VNET(vnet_id="vnet002", page_id="page002")
    vnet2.add_tab("tab002")
    vnet2.add_link("LINK_AB")  # A ↔ B
    vnet2.add_link("LINK_BC")
    
    vnet3 = VNET(vnet_id="vnet003", page_id="page003")
    vnet3.add_tab("tab003")
    vnet3.add_link("LINK_BC")  # B ↔ C
    vnet3.add_link("LINK_CA")  # C → A (closes circle)
    
    # Create evaluator
    all_vnets = {"vnet001": vnet1, "vnet002": vnet2, "vnet003": vnet3}
    all_tabs = {"tab001": tab1, "tab002": tab2, "tab003": tab3}
    all_bridges = {}
    evaluator = VnetEvaluator(all_vnets, all_tabs, all_bridges)
    
    # Evaluate all VNETs (should not hang)
    result1 = evaluator.evaluate_vnet_state(vnet1)
    result2 = evaluator.evaluate_vnet_state(vnet2)
    result3 = evaluator.evaluate_vnet_state(vnet3)
    
    # Verify all are HIGH (circular propagation works)
    assert result1 == PinState.HIGH, f"VNET1 expected HIGH, got {result1}"
    assert result2 == PinState.HIGH, f"VNET2 expected HIGH, got {result2}"
    assert result3 == PinState.HIGH, f"VNET3 expected HIGH, got {result3}"
    print("  ✓ Circular links handled (no infinite loop)")
    print("  ✓ HIGH propagates through circular structure")
    print()


def test_evaluator_circular_bridges():
    """Test VNET evaluation with circular bridge connections."""
    print("Test 7: Circular bridge detection → No infinite loop")
    
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
    
    # Set pin1 to HIGH, others to FLOAT
    pin1.set_state(PinState.HIGH)
    pin2.set_state(PinState.FLOAT)
    pin3.set_state(PinState.FLOAT)
    
    # Create VNETs
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet1.add_tab("tab001")
    
    vnet2 = VNET(vnet_id="vnet002", page_id="page001")
    vnet2.add_tab("tab002")
    
    vnet3 = VNET(vnet_id="vnet003", page_id="page001")
    vnet3.add_tab("tab003")
    
    # Create circular bridges: 1→2, 2→3, 3→1
    bridge_mgr = BridgeManager()
    bridge1 = bridge_mgr.create_bridge("vnet001", "vnet002", "relay001")
    bridge2 = bridge_mgr.create_bridge("vnet002", "vnet003", "relay002")
    bridge3 = bridge_mgr.create_bridge("vnet003", "vnet001", "relay003")
    
    # Add bridge references
    vnet1.add_bridge(bridge1.bridge_id)
    vnet1.add_bridge(bridge3.bridge_id)
    vnet2.add_bridge(bridge1.bridge_id)
    vnet2.add_bridge(bridge2.bridge_id)
    vnet3.add_bridge(bridge2.bridge_id)
    vnet3.add_bridge(bridge3.bridge_id)
    
    # Create evaluator
    all_vnets = {"vnet001": vnet1, "vnet002": vnet2, "vnet003": vnet3}
    all_tabs = {"tab001": tab1, "tab002": tab2, "tab003": tab3}
    all_bridges = {
        bridge1.bridge_id: bridge1,
        bridge2.bridge_id: bridge2,
        bridge3.bridge_id: bridge3
    }
    evaluator = VnetEvaluator(all_vnets, all_tabs, all_bridges)
    
    # Evaluate all VNETs (should not hang)
    result1 = evaluator.evaluate_vnet_state(vnet1)
    result2 = evaluator.evaluate_vnet_state(vnet2)
    result3 = evaluator.evaluate_vnet_state(vnet3)
    
    # Verify all are HIGH (circular propagation works)
    assert result1 == PinState.HIGH, f"VNET1 expected HIGH, got {result1}"
    assert result2 == PinState.HIGH, f"VNET2 expected HIGH, got {result2}"
    assert result3 == PinState.HIGH, f"VNET3 expected HIGH, got {result3}"
    print("  ✓ Circular bridges handled (no infinite loop)")
    print("  ✓ HIGH propagates through circular bridge structure")
    print()


def test_evaluator_batch_evaluation():
    """Test evaluating multiple VNETs in batch."""
    print("Test 8: Batch evaluation of multiple VNETs")
    
    # Create several components
    components = []
    pins = []
    tabs = []
    vnets = []
    
    for i in range(5):
        comp = MockComponent(
            component_id=f"comp{i:03d}",
            page_id="page001"
        )
        pin = Pin(pin_id=f"pin{i:03d}", parent_component=comp)
        tab = Tab(
            tab_id=f"tab{i:03d}",
            parent_pin=pin,
            relative_position=(0, 10)
        )
        vnet = VNET(vnet_id=f"vnet{i:03d}", page_id="page001")
        vnet.add_tab(f"tab{i:03d}")
        
        components.append(comp)
        pins.append(pin)
        tabs.append(tab)
        vnets.append(vnet)
    
    # Set alternating states: HIGH, FLOAT, HIGH, FLOAT, HIGH
    pins[0].set_state(PinState.HIGH)
    pins[1].set_state(PinState.FLOAT)
    pins[2].set_state(PinState.HIGH)
    pins[3].set_state(PinState.FLOAT)
    pins[4].set_state(PinState.HIGH)
    
    # Create evaluator
    all_vnets = {vnet.vnet_id: vnet for vnet in vnets}
    all_tabs = {tab.tab_id: tab for tab in tabs}
    all_bridges = {}
    evaluator = VnetEvaluator(all_vnets, all_tabs, all_bridges)
    
    # Batch evaluate
    results = evaluator.evaluate_multiple_vnets(vnets)
    
    # Verify results
    assert results["vnet000"] == PinState.HIGH, "VNET0 should be HIGH"
    assert results["vnet001"] == PinState.FLOAT, "VNET1 should be FLOAT"
    assert results["vnet002"] == PinState.HIGH, "VNET2 should be HIGH"
    assert results["vnet003"] == PinState.FLOAT, "VNET3 should be FLOAT"
    assert results["vnet004"] == PinState.HIGH, "VNET4 should be HIGH"
    
    print("  ✓ Batch evaluation successful")
    print(f"  ✓ Evaluated {len(results)} VNETs")
    print()


def test_evaluator_get_connected_vnets():
    """Test getting all connected VNETs."""
    print("Test 9: Get all connected VNETs")
    
    # Create components
    comp1 = MockComponent(component_id="comp001", page_id="page001")
    comp2 = MockComponent(component_id="comp002", page_id="page002")
    comp3 = MockComponent(component_id="comp003", page_id="page001")
    
    pin1 = Pin(pin_id="pin001", parent_component=comp1)
    pin2 = Pin(pin_id="pin002", parent_component=comp2)
    pin3 = Pin(pin_id="pin003", parent_component=comp3)
    
    tab1 = Tab(tab_id="tab001", parent_pin=pin1, relative_position=(0, 10))
    tab2 = Tab(tab_id="tab002", parent_pin=pin2, relative_position=(10, 0))
    tab3 = Tab(tab_id="tab003", parent_pin=pin3, relative_position=(0, -10))
    
    pin1.set_state(PinState.HIGH)
    pin2.set_state(PinState.FLOAT)
    pin3.set_state(PinState.FLOAT)
    
    # Create VNETs: vnet1 linked to vnet2, vnet1 bridged to vnet3
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet1.add_tab("tab001")
    vnet1.add_link("POWER")
    
    vnet2 = VNET(vnet_id="vnet002", page_id="page002")
    vnet2.add_tab("tab002")
    vnet2.add_link("POWER")
    
    vnet3 = VNET(vnet_id="vnet003", page_id="page001")
    vnet3.add_tab("tab003")
    
    # Create bridge
    bridge_mgr = BridgeManager()
    bridge = bridge_mgr.create_bridge("vnet001", "vnet003", "relay001")
    vnet1.add_bridge(bridge.bridge_id)
    vnet3.add_bridge(bridge.bridge_id)
    
    # Create evaluator
    all_vnets = {"vnet001": vnet1, "vnet002": vnet2, "vnet003": vnet3}
    all_tabs = {"tab001": tab1, "tab002": tab2, "tab003": tab3}
    all_bridges = {bridge.bridge_id: bridge}
    evaluator = VnetEvaluator(all_vnets, all_tabs, all_bridges)
    
    # Get connected VNETs
    connected = evaluator.get_all_connected_vnets(vnet1)
    
    # Verify all three VNETs are connected
    assert "vnet001" in connected, "vnet001 should be in connected set"
    assert "vnet002" in connected, "vnet002 should be connected (via link)"
    assert "vnet003" in connected, "vnet003 should be connected (via bridge)"
    assert len(connected) == 3, f"Expected 3 connected VNETs, got {len(connected)}"
    
    print("  ✓ Found all connected VNETs")
    print(f"  ✓ Connected set: {sorted(connected)}")
    print()


def run_all_tests():
    """Run all VNET evaluator tests."""
    print("=" * 60)
    print("VNET STATE EVALUATOR TEST SUITE (Phase 4.1)")
    print("=" * 60)
    print()
    
    tests = [
        test_evaluator_all_float,
        test_evaluator_one_high,
        test_evaluator_multiple_high,
        test_evaluator_with_links,
        test_evaluator_with_bridges,
        test_evaluator_circular_links,
        test_evaluator_circular_bridges,
        test_evaluator_batch_evaluation,
        test_evaluator_get_connected_vnets,
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
        print("\nVNET State Evaluator implementation verified:")
        print("  ✓ EvaluateVnetState(vnet) - Main method")
        print("  ✓ Read all tab states in VNET")
        print("  ✓ Apply HIGH OR FLOAT logic")
        print("  ✓ Determine final VNET state")
        print("  ✓ Return computed state")
        print("  ✓ Get state from linked VNETs")
        print("  ✓ Include in OR evaluation")
        print("  ✓ Get state from bridged VNETs")
        print("  ✓ Include in OR evaluation")
        print("  ✓ Circular link/bridge detection")
        print("  ✓ Batch evaluation support")
        return 0
    else:
        print(f"\n✗ {failed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
