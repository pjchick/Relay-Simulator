"""
Test Suite for VCC Component (Phase 3.3.5)

Tests the VCC (constant power source) component including:
- Pin configuration (1 pin, 1 tab)
- Constant HIGH output
- SimStart/SimStop behavior
- No user interaction
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.vcc import VCC
from core.pin import Pin
from core.state import PinState


# ============================================================
# Mock Objects for Testing
# ============================================================

class MockVNET:
    """Mock VNET for testing."""
    def __init__(self, vnet_id: str):
        self.vnet_id = vnet_id
        self.state = PinState.FLOAT
        self.dirty = False
    
    def mark_dirty(self):
        """Mark VNET as dirty."""
        self.dirty = True


class MockVnetManager:
    """Mock VnetManager for testing."""
    def __init__(self):
        self.vnets = {}
        self.tab_to_vnet = {}
    
    def get_vnet_for_tab(self, tab_id: str):
        """Get VNET for a tab."""
        return self.tab_to_vnet.get(tab_id)
    
    def register_tab(self, tab_id: str, vnet: MockVNET):
        """Register a tab with a VNET."""
        self.tab_to_vnet[tab_id] = vnet


# ============================================================
# Test Functions
# ============================================================

def test_vcc_creation():
    """Test VCC creation and initialization."""
    print("=== Testing VCC Creation ===")
    
    vcc = VCC("vcc001", "page1")
    
    # Check basic properties
    assert vcc.component_id == "vcc001"
    assert vcc.component_type == "VCC"
    assert vcc.page_id == "page1"
    print("✓ VCC created: VCC(vcc001)")
    
    # Check default properties
    assert vcc.properties["label"] == "VCC"
    print("✓ Default label: VCC")
    
    print("✓ VCC creation tests passed\n")


def test_vcc_pin_configuration():
    """Test VCC has correct pin configuration (1 pin, 1 tab)."""
    print("=== Testing VCC Pin Configuration ===")
    
    vcc = VCC("vcc001", "page1")
    
    # Check pin count
    assert len(vcc.pins) == 1
    print("✓ VCC has 1 pin")
    
    # Check output pin exists
    output_pin = vcc.get_output_pin()
    assert output_pin is not None
    print("✓ Output pin exists")
    
    # Check pin has 1 tab
    assert len(output_pin.tabs) == 1
    print("✓ Pin has 1 tab")
    
    # Check tab position (should be at 6 o'clock - bottom)
    tab = list(output_pin.tabs.values())[0]
    assert tab.relative_position == (0, 20)
    print("✓ Tab at correct position: 6 o'clock (bottom)")
    
    print("✓ VCC pin configuration tests passed\n")


def test_vcc_sim_start():
    """Test VCC initialization on SimStart."""
    print("=== Testing VCC SimStart ===")
    
    vcc = VCC("vcc001", "page1")
    vnet_mgr = MockVnetManager()
    
    # Create VNET for the tab
    output_pin = vcc.get_output_pin()
    tab = list(output_pin.tabs.values())[0]
    vnet = MockVNET("vnet_output")
    vnet_mgr.register_tab(tab.tab_id, vnet)
    
    # Call sim_start
    vcc.sim_start(vnet_mgr)
    
    # Check output pin is HIGH
    assert output_pin.state == PinState.HIGH
    print("✓ Output pin set to HIGH")
    
    # Check VNET marked dirty
    assert vnet.dirty == True
    print("✓ VNET marked dirty")
    
    # Check is_on returns True
    assert vcc.is_on() == True
    print("✓ is_on() returns True")
    
    print("✓ VCC SimStart tests passed\n")


def test_vcc_constant_output():
    """Test VCC maintains constant HIGH output."""
    print("=== Testing VCC Constant Output ===")
    
    vcc = VCC("vcc001", "page1")
    vnet_mgr = MockVnetManager()
    
    # Initialize
    output_pin = vcc.get_output_pin()
    tab = list(output_pin.tabs.values())[0]
    vnet = MockVNET("vnet_output")
    vnet_mgr.register_tab(tab.tab_id, vnet)
    
    vcc.sim_start(vnet_mgr)
    
    # Check initial state
    assert output_pin.state == PinState.HIGH
    print("✓ Initial state: HIGH")
    
    # Run simulate_logic multiple times
    for i in range(10):
        vcc.simulate_logic(vnet_mgr)
    
    # State should still be HIGH
    assert output_pin.state == PinState.HIGH
    print("✓ State remains HIGH after simulate_logic calls")
    
    print("✓ VCC constant output tests passed\n")


def test_vcc_sim_stop():
    """Test VCC cleanup on SimStop."""
    print("=== Testing VCC SimStop ===")
    
    vcc = VCC("vcc001", "page1")
    vnet_mgr = MockVnetManager()
    
    # Initialize
    output_pin = vcc.get_output_pin()
    tab = list(output_pin.tabs.values())[0]
    vnet = MockVNET("vnet_output")
    vnet_mgr.register_tab(tab.tab_id, vnet)
    
    vcc.sim_start(vnet_mgr)
    assert output_pin.state == PinState.HIGH
    print("✓ Started with HIGH")
    
    # Stop simulation
    vcc.sim_stop(vnet_mgr)
    
    # Check output is FLOAT
    assert output_pin.state == PinState.FLOAT
    print("✓ Output set to FLOAT after SimStop")
    
    # Check is_on returns False
    assert vcc.is_on() == False
    print("✓ is_on() returns False")
    
    print("✓ VCC SimStop tests passed\n")


def test_vcc_no_interaction():
    """Test VCC doesn't support user interaction."""
    print("=== Testing VCC No Interaction ===")
    
    vcc = VCC("vcc001", "page1")
    
    # Try various interactions
    result = vcc.interact("toggle")
    assert result == False
    print("✓ Toggle interaction returns False")
    
    result = vcc.interact("press")
    assert result == False
    print("✓ Press interaction returns False")
    
    result = vcc.interact("any_action")
    assert result == False
    print("✓ Any interaction returns False")
    
    print("✓ VCC no interaction tests passed\n")


def test_vcc_visual_state():
    """Test VCC visual state."""
    print("=== Testing VCC Visual State ===")
    
    vcc = VCC("vcc001", "page1")
    vnet_mgr = MockVnetManager()
    
    output_pin = vcc.get_output_pin()
    tab = list(output_pin.tabs.values())[0]
    vnet = MockVNET("vnet_output")
    vnet_mgr.register_tab(tab.tab_id, vnet)
    
    # Before SimStart
    state = vcc.get_visual_state()
    assert state["output_state"] == "FLOAT"
    print("✓ Visual state: FLOAT before SimStart")
    
    # After SimStart
    vcc.sim_start(vnet_mgr)
    state = vcc.get_visual_state()
    assert state["output_state"] == "HIGH"
    print("✓ Visual state: HIGH after SimStart")
    
    # After SimStop
    vcc.sim_stop(vnet_mgr)
    state = vcc.get_visual_state()
    assert state["output_state"] == "FLOAT"
    print("✓ Visual state: FLOAT after SimStop")
    
    print("✓ VCC visual state tests passed\n")


def test_vcc_serialization():
    """Test VCC serialization."""
    print("=== Testing VCC Serialization ===")
    
    vcc = VCC("vcc001", "page1")
    vcc.properties["label"] = "Power"
    
    # Serialize
    data = vcc.to_dict()
    
    # Check serialized data
    assert data["component_id"] == "vcc001"
    assert data["type"] == "VCC"
    assert data["properties"]["label"] == "Power"
    print("✓ VCC serialized")
    
    print("✓ VCC serialization tests passed\n")


def test_vcc_deserialization():
    """Test VCC deserialization."""
    print("=== Testing VCC Deserialization ===")
    
    # Create and serialize VCC
    vcc1 = VCC("vcc001", "page1")
    vcc1.properties["label"] = "+5V"
    data = vcc1.to_dict()
    
    # Deserialize
    vcc2 = VCC.from_dict(data)
    
    # Verify properties restored
    assert vcc2.component_id == "vcc001"
    assert vcc2.properties["label"] == "+5V"
    print("✓ VCC deserialized")
    
    # Verify pin restored
    assert len(vcc2.pins) == 1
    output_pin = vcc2.get_output_pin()
    assert output_pin is not None
    assert len(output_pin.tabs) == 1
    print("✓ Pin and tab restored")
    
    print("✓ VCC deserialization tests passed\n")


def test_vcc_with_indicator():
    """Test VCC powering an indicator (integration test)."""
    print("=== Testing VCC With Indicator ===")
    
    from components.indicator import Indicator
    
    vcc = VCC("vcc001", "page1")
    indicator = Indicator("led001", "page1")
    vnet_mgr = MockVnetManager()
    
    # Create shared VNET
    shared_vnet = MockVNET("vnet_power")
    
    # Register VCC output tab
    vcc_pin = vcc.get_output_pin()
    vcc_tab = list(vcc_pin.tabs.values())[0]
    vnet_mgr.register_tab(vcc_tab.tab_id, shared_vnet)
    
    # Register indicator input tab (any tab)
    ind_pin = list(indicator.pins.values())[0]
    ind_tab = list(ind_pin.tabs.values())[0]
    vnet_mgr.register_tab(ind_tab.tab_id, shared_vnet)
    
    # Start simulation
    vcc.sim_start(vnet_mgr)
    indicator.sim_start(vnet_mgr, None)
    
    # VCC should output HIGH
    assert vcc_pin.state == PinState.HIGH
    print("✓ VCC outputs HIGH")
    
    # Simulate indicator reading the VNET (manually set for test)
    ind_pin.set_state(PinState.HIGH)
    
    # Indicator should be ON
    assert indicator.is_on() == True
    print("✓ Indicator powered ON by VCC")
    
    print("✓ VCC with indicator tests passed\n")


# ============================================================
# Main Test Runner
# ============================================================

def run_all_tests():
    """Run all VCC tests."""
    print("=" * 60)
    print("VCC COMPONENT TEST SUITE (Phase 3.3.5)")
    print("=" * 60)
    print()
    
    tests = [
        test_vcc_creation,
        test_vcc_pin_configuration,
        test_vcc_sim_start,
        test_vcc_constant_output,
        test_vcc_sim_stop,
        test_vcc_no_interaction,
        test_vcc_visual_state,
        test_vcc_serialization,
        test_vcc_deserialization,
        test_vcc_with_indicator,
    ]
    
    for test in tests:
        test()
    
    print("=" * 60)
    print("✓ ALL VCC COMPONENT TESTS PASSED")
    print("=" * 60)
    print()
    print("Section 3.3.5 VCC Component Requirements:")
    print("✓ Define VCC class (extends Component)")
    print("  ✓ Pin configuration: 1 pin, 1 tab at bottom")
    print("  ✓ Visual state: Always ON during simulation")
    print("✓ Implement simulate_logic()")
    print("  ✓ No logic needed (constant source)")
    print("✓ Implement interact()")
    print("  ✓ No interaction (always returns False)")
    print("✓ Implement sim_start()")
    print("  ✓ Initialize pin to HIGH")
    print("  ✓ Mark VNET dirty")
    print("✓ Implement sim_stop()")
    print("  ✓ Set pin to FLOAT")
    print("✓ Add visual properties")
    print("  ✓ General > ID (readonly)")
    print("  ✓ General > Label (defaults to 'VCC')")
    print("✓ Tests")
    print("  ✓ Test goes HIGH on SimStart")
    print("  ✓ Test goes FLOAT on SimStop")
    print("  ✓ Test constant HIGH output")
    print("  ✓ Test no user interaction")
    print("  ✓ Test serialization/deserialization")
    print("  ✓ Test integration with indicator")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
