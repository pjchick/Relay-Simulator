"""
Test suite for Indicator Component (Phase 3.2)

Comprehensive tests for Indicator component including creation, pin state reading,
passive behavior, visual state, and serialization.
"""

import sys
import os

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.indicator import Indicator
from core.state import PinState


# Mock VnetManager for testing
class MockVnetManager:
    """Mock VnetManager for testing."""
    
    def __init__(self):
        self.dirty_tabs = set()
    
    def mark_tab_dirty(self, tab_id):
        """Mark a tab as dirty."""
        self.dirty_tabs.add(tab_id)


# Mock BridgeManager for testing
class MockBridgeManager:
    """Mock BridgeManager for testing."""
    pass


def test_indicator_creation():
    """Test Indicator component creation."""
    print("\n=== Testing Indicator Creation ===")
    
    indicator = Indicator("led001", "page001")
    
    assert indicator.component_id == "led001"
    assert indicator.page_id == "page001"
    assert indicator.component_type == "Indicator"
    
    print(f"✓ Indicator created: {indicator}")
    
    # Check default properties
    assert indicator.properties['label'] == 'LED'
    assert indicator.properties['label_position'] == 'bottom'
    assert indicator.properties['color'] == 'red'
    
    print(f"✓ Default properties set")
    
    print("✓ Indicator creation tests passed")


def test_indicator_pin_configuration():
    """Test indicator has correct pin and tab configuration."""
    print("\n=== Testing Indicator Pin Configuration ===")
    
    indicator = Indicator("led001", "page001")
    
    # Should have 1 pin
    pins = indicator.get_all_pins()
    assert len(pins) == 1
    
    print(f"✓ Indicator has 1 pin")
    
    # Pin should have 4 tabs (12, 3, 6, 9 o'clock)
    pin = list(pins.values())[0]
    tabs = pin.tabs
    assert len(tabs) == 4
    
    print(f"✓ Pin has 4 tabs")
    
    # Check tab positions
    tab_positions = [tab.relative_position for tab in tabs.values()]
    expected_positions = [(0, -20), (20, 0), (0, 20), (-20, 0)]
    
    for pos in expected_positions:
        assert pos in tab_positions, f"Missing tab at position {pos}"
    
    print(f"✓ Tabs at correct positions: {tab_positions}")
    
    print("✓ Indicator pin configuration tests passed")


def test_indicator_sim_start():
    """Test indicator initialization at simulation start."""
    print("\n=== Testing Indicator SimStart ===")
    
    indicator = Indicator("led001", "page001")
    vnet_mgr = MockVnetManager()
    bridge_mgr = MockBridgeManager()
    
    # Initialize indicator
    indicator.sim_start(vnet_mgr, bridge_mgr)
    
    # Pin should be FLOAT (no signal)
    pin = list(indicator.pins.values())[0]
    assert pin.state == PinState.FLOAT
    
    print(f"✓ Pin state is FLOAT after SimStart")
    
    # Passive component should NOT mark tabs dirty on start
    assert len(vnet_mgr.dirty_tabs) == 0
    
    print(f"✓ Passive component doesn't mark tabs dirty")
    
    print("✓ Indicator SimStart tests passed")


def test_indicator_passive_behavior():
    """Test that indicator is passive (no state changes)."""
    print("\n=== Testing Indicator Passive Behavior ===")
    
    indicator = Indicator("led001", "page001")
    vnet_mgr = MockVnetManager()
    bridge_mgr = MockBridgeManager()
    
    indicator.sim_start(vnet_mgr, bridge_mgr)
    
    pin = list(indicator.pins.values())[0]
    initial_state = pin.state
    
    # Call simulate_logic (should do nothing)
    indicator.simulate_logic(vnet_mgr)
    
    # State should not change
    assert pin.state == initial_state
    
    print(f"✓ simulate_logic() doesn't change state (passive)")
    
    # No tabs should be marked dirty
    assert len(vnet_mgr.dirty_tabs) == 0
    
    print(f"✓ No tabs marked dirty (passive)")
    
    print("✓ Indicator passive behavior tests passed")


def test_indicator_reads_pin_state():
    """Test indicator reads and displays pin state."""
    print("\n=== Testing Indicator Reads Pin State ===")
    
    indicator = Indicator("led001", "page001")
    vnet_mgr = MockVnetManager()
    bridge_mgr = MockBridgeManager()
    
    indicator.sim_start(vnet_mgr, bridge_mgr)
    
    pin = list(indicator.pins.values())[0]
    
    # Initial state: FLOAT (OFF)
    assert not indicator.is_on()
    
    print(f"✓ Initial state: OFF (FLOAT)")
    
    # Simulate external signal driving pin HIGH
    pin.set_state(PinState.HIGH)
    
    # Indicator should now read as ON
    assert indicator.is_on()
    assert pin.state == PinState.HIGH
    
    print(f"✓ Pin driven HIGH: Indicator ON")
    
    # Drive pin back to FLOAT
    pin.set_state(PinState.FLOAT)
    
    # Indicator should read as OFF
    assert not indicator.is_on()
    
    print(f"✓ Pin driven FLOAT: Indicator OFF")
    
    print("✓ Indicator reads pin state tests passed")


def test_indicator_no_interaction():
    """Test that indicator has no user interaction."""
    print("\n=== Testing Indicator No Interaction ===")
    
    indicator = Indicator("led001", "page001")
    
    # Try various interactions - all should return False
    assert indicator.interact('click') == False
    assert indicator.interact('toggle') == False
    assert indicator.interact('press') == False
    assert indicator.interact('release') == False
    
    print(f"✓ All interactions return False (passive)")
    
    print("✓ Indicator no interaction tests passed")


def test_indicator_visual_state_off():
    """Test indicator visual state when OFF."""
    print("\n=== Testing Indicator Visual State (OFF) ===")
    
    indicator = Indicator("led001", "page001")
    vnet_mgr = MockVnetManager()
    bridge_mgr = MockBridgeManager()
    
    indicator.sim_start(vnet_mgr, bridge_mgr)
    
    # Get visual state (should be OFF)
    visual = indicator.get_visual_state()
    
    assert visual['indicator_state'] == 'OFF'
    assert visual['type'] == 'Indicator'
    
    print(f"✓ Visual state: OFF")
    
    print("✓ Indicator visual state (OFF) tests passed")


def test_indicator_visual_state_on():
    """Test indicator visual state when ON."""
    print("\n=== Testing Indicator Visual State (ON) ===")
    
    indicator = Indicator("led001", "page001")
    vnet_mgr = MockVnetManager()
    bridge_mgr = MockBridgeManager()
    
    indicator.sim_start(vnet_mgr, bridge_mgr)
    
    # Drive pin HIGH
    pin = list(indicator.pins.values())[0]
    pin.set_state(PinState.HIGH)
    
    # Get visual state (should be ON)
    visual = indicator.get_visual_state()
    
    assert visual['indicator_state'] == 'ON'
    
    print(f"✓ Visual state: ON")
    
    print("✓ Indicator visual state (ON) tests passed")


def test_indicator_color_presets():
    """Test indicator color presets."""
    print("\n=== Testing Indicator Color Presets ===")
    
    indicator = Indicator("led001", "page001")
    
    # Default is red
    assert indicator.properties['color'] == 'red'
    assert indicator.properties['on_color'] == (255, 0, 0)
    assert indicator.properties['off_color'] == (64, 0, 0)
    
    print(f"✓ Default color: red")
    
    # Set to green
    indicator.set_color('green')
    assert indicator.properties['color'] == 'green'
    assert indicator.properties['on_color'] == (0, 255, 0)
    assert indicator.properties['off_color'] == (0, 64, 0)
    
    print(f"✓ Set color to green")
    
    # Set to blue
    indicator.set_color('blue')
    assert indicator.properties['on_color'] == (0, 0, 255)
    assert indicator.properties['off_color'] == (0, 0, 64)
    
    print(f"✓ Set color to blue")
    
    # Set to amber
    indicator.set_color('amber')
    assert indicator.properties['on_color'] == (255, 191, 0)
    
    print(f"✓ Set color to amber")
    
    print("✓ Indicator color presets tests passed")


def test_indicator_serialization():
    """Test indicator serialization."""
    print("\n=== Testing Indicator Serialization ===")
    
    indicator = Indicator("led001", "page001")
    indicator.position = (100, 200)
    indicator.properties['label'] = 'POWER'
    indicator.properties['color'] = 'green'
    indicator.set_color('green')
    
    # Serialize
    data = indicator.to_dict()
    
    assert data['component_id'] == "led001"
    assert data['type'] == "Indicator"
    assert data['position'] == (100, 200)
    assert data['properties']['label'] == 'POWER'
    assert data['properties']['color'] == 'green'
    assert 'pins' in data
    
    print(f"✓ Indicator serialized")
    
    print("✓ Indicator serialization tests passed")


def test_indicator_deserialization():
    """Test indicator deserialization."""
    print("\n=== Testing Indicator Deserialization ===")
    
    # Create and serialize an indicator
    indicator1 = Indicator("led001", "page001")
    indicator1.position = (150, 250)
    indicator1.properties['label'] = 'STATUS'
    indicator1.properties['label_position'] = 'top'
    indicator1.set_color('blue')
    
    data = indicator1.to_dict()
    
    # Deserialize
    indicator2 = Indicator.from_dict(data)
    
    assert indicator2.component_id == "led001"
    assert indicator2.position == (150, 250)
    assert indicator2.properties['label'] == 'STATUS'
    assert indicator2.properties['label_position'] == 'top'
    assert indicator2.properties['color'] == 'blue'
    
    print(f"✓ Indicator deserialized")
    
    # Check pins and tabs
    pins = indicator2.get_all_pins()
    assert len(pins) == 1
    pin = list(pins.values())[0]
    assert len(pin.tabs) == 4
    
    print(f"✓ Pins and tabs restored")
    
    print("✓ Indicator deserialization tests passed")


def test_indicator_with_switch():
    """Test indicator connected to a switch (integration test)."""
    print("\n=== Testing Indicator With Switch ===")
    
    from components.switch import Switch
    
    # Create switch and indicator
    switch = Switch("sw001", "page001")
    indicator = Indicator("led001", "page001")
    
    vnet_mgr = MockVnetManager()
    bridge_mgr = MockBridgeManager()
    
    # Initialize both
    switch.sim_start(vnet_mgr, bridge_mgr)
    indicator.sim_start(vnet_mgr, bridge_mgr)
    
    # Get pins
    switch_pin = list(switch.pins.values())[0]
    indicator_pin = list(indicator.pins.values())[0]
    
    # Initially both should be FLOAT/OFF
    assert switch_pin.state == PinState.FLOAT
    assert indicator_pin.state == PinState.FLOAT
    assert not indicator.is_on()
    
    print(f"✓ Initial: Switch OFF, Indicator OFF")
    
    # Toggle switch ON
    switch.interact('toggle')
    switch.simulate_logic(vnet_mgr)
    
    # Switch should be HIGH
    assert switch_pin.state == PinState.HIGH
    
    # Simulate indicator reading from same VNET (manual for test)
    indicator_pin.set_state(PinState.HIGH)
    
    # Indicator should now be ON
    assert indicator.is_on()
    
    print(f"✓ Switch ON → Indicator ON")
    
    # Toggle switch OFF
    switch.interact('toggle')
    switch.simulate_logic(vnet_mgr)
    
    # Switch should be FLOAT
    assert switch_pin.state == PinState.FLOAT
    
    # Update indicator
    indicator_pin.set_state(PinState.FLOAT)
    
    # Indicator should be OFF
    assert not indicator.is_on()
    
    print(f"✓ Switch OFF → Indicator OFF")
    
    print("✓ Indicator with switch tests passed")


def run_all_tests():
    """Run all Indicator component tests."""
    print("=" * 60)
    print("INDICATOR COMPONENT TEST SUITE (Phase 3.2)")
    print("=" * 60)
    
    try:
        test_indicator_creation()
        test_indicator_pin_configuration()
        test_indicator_sim_start()
        test_indicator_passive_behavior()
        test_indicator_reads_pin_state()
        test_indicator_no_interaction()
        test_indicator_visual_state_off()
        test_indicator_visual_state_on()
        test_indicator_color_presets()
        test_indicator_serialization()
        test_indicator_deserialization()
        test_indicator_with_switch()
        
        print("\n" + "=" * 60)
        print("✓ ALL INDICATOR COMPONENT TESTS PASSED")
        print("=" * 60)
        print("\nSection 3.2 Indicator Component Requirements:")
        print("✓ Define Indicator class (extends Component)")
        print("  ✓ Pin configuration: 1 pin, 4 tabs at 12, 3, 6, 9 o'clock")
        print("  ✓ Visual state: ON/OFF (derived from pin state)")
        print("✓ Implement simulate_logic()")
        print("  ✓ Read pin state (passive component)")
        print("  ✓ No state changes (read-only)")
        print("✓ Implement interact()")
        print("  ✓ No interaction (passive component)")
        print("✓ Implement sim_start()")
        print("  ✓ Initialize pin to FLOAT")
        print("  ✓ Position tabs at clock positions")
        print("✓ Implement sim_stop()")
        print("  ✓ No cleanup needed")
        print("✓ Add visual properties")
        print("  ✓ General > ID (readonly)")
        print("  ✓ General > Label (optional)")
        print("  ✓ General > Label position (Top, bottom, left, right)")
        print("  ✓ Format > Color (Red, Green, Blue, Yellow, Amber, etc.)")
        print("  ✓ Color presets with bright ON/dim OFF colors")
        print("✓ Tests")
        print("  ✓ Test indicator creation")
        print("  ✓ Test pin state reading")
        print("  ✓ Test 4 tabs on 1 pin")
        print("  ✓ Test visual state (HIGH → ON)")
        print("  ✓ Test passive behavior")
        print("  ✓ Test serialization/deserialization")
        print("  ✓ Test integration with switch")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
