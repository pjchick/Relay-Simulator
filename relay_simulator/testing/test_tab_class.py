"""
Test suite for Tab Class (Phase 1.3)

Comprehensive tests for Tab class definition, state management, and serialization.
"""

import sys
import os

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.state import PinState
from core.tab import Tab
from core.pin import Pin


def test_tab_creation():
    """Test Tab class definition and creation."""
    print("\n=== Testing Tab Creation ===")
    
    # Create a parent pin
    pin = Pin("page001.comp001.pin001", None)
    
    # Create tab with all required properties
    tab = Tab(
        tab_id="page001.comp001.pin001.tab001",
        parent_pin=pin,
        relative_position=(10.0, 20.0)
    )
    
    # Verify properties
    assert tab.tab_id == "page001.comp001.pin001.tab001", "TabId not set correctly"
    print(f"✓ TabId: {tab.tab_id}")
    
    assert tab.parent_pin == pin, "Parent pin reference not set"
    print(f"✓ Parent pin reference set")
    
    assert tab.relative_position == (10.0, 20.0), "Position not set correctly"
    print(f"✓ Relative position: {tab.relative_position}")
    
    assert tab.state == PinState.FLOAT, "Initial state should be FLOAT"
    print(f"✓ Initial state: {tab.state}")
    
    print("✓ Tab creation tests passed")


def test_tab_state_get():
    """Test getting tab state (reflects parent pin)."""
    print("\n=== Testing Tab State Get ===")
    
    # Create pin and tab
    pin = Pin("page001.comp001.pin001", None)
    tab = Tab("page001.comp001.pin001.tab001", pin, (0, 0))
    pin.add_tab(tab)
    
    # Tab state should reflect pin state
    assert tab.state == PinState.FLOAT, "Tab should start with FLOAT"
    print(f"✓ Initial tab state: {tab.state}")
    
    # Change pin state
    pin.set_state(PinState.HIGH)
    assert tab.state == PinState.HIGH, "Tab state should reflect pin state"
    print(f"✓ Tab reflects pin HIGH state: {tab.state}")
    
    # Change pin back to FLOAT
    pin.set_state(PinState.FLOAT)
    assert tab.state == PinState.FLOAT, "Tab should reflect FLOAT"
    print(f"✓ Tab reflects pin FLOAT state: {tab.state}")
    
    print("✓ Tab state get tests passed")


def test_tab_state_set_propagation():
    """Test setting tab state (propagates to parent pin)."""
    print("\n=== Testing Tab State Set (Propagation) ===")
    
    # Create pin with one tab
    pin = Pin("page001.comp001.pin001", None)
    tab = Tab("page001.comp001.pin001.tab001", pin, (0, 0))
    pin.add_tab(tab)
    
    # Set tab state to HIGH
    tab.state = PinState.HIGH
    
    # Pin should now be HIGH
    assert pin.state == PinState.HIGH, "Setting tab state should propagate to pin"
    print(f"✓ Tab state HIGH propagated to pin: {pin.state}")
    
    # Set tab back to FLOAT
    tab.state = PinState.FLOAT
    assert pin.state == PinState.FLOAT, "Tab FLOAT should propagate"
    print(f"✓ Tab state FLOAT propagated to pin: {pin.state}")
    
    print("✓ Tab state set propagation tests passed")


def test_multiple_tabs_on_pin():
    """Test multiple tabs sharing one pin (like an indicator)."""
    print("\n=== Testing Multiple Tabs on One Pin ===")
    
    # Create pin with 4 tabs (like indicator at 12, 3, 6, 9 o'clock)
    pin = Pin("page001.comp001.pin001", None)
    
    tab1 = Tab("page001.comp001.pin001.tab001", pin, (0, -20))   # 12 o'clock
    tab2 = Tab("page001.comp001.pin001.tab002", pin, (20, 0))    # 3 o'clock
    tab3 = Tab("page001.comp001.pin001.tab003", pin, (0, 20))    # 6 o'clock
    tab4 = Tab("page001.comp001.pin001.tab004", pin, (-20, 0))   # 9 o'clock
    
    pin.add_tab(tab1)
    pin.add_tab(tab2)
    pin.add_tab(tab3)
    pin.add_tab(tab4)
    
    print(f"✓ Created {len(pin.tabs)} tabs")
    
    # All tabs should start FLOAT
    assert all(tab.state == PinState.FLOAT for tab in [tab1, tab2, tab3, tab4])
    print("✓ All tabs initially FLOAT")
    
    # Set pin to HIGH - all tabs should be HIGH
    pin.set_state(PinState.HIGH)
    assert all(tab.state == PinState.HIGH for tab in [tab1, tab2, tab3, tab4])
    print("✓ Pin HIGH propagates to all 4 tabs")
    
    # Set one tab to HIGH (via the tab, not pin)
    pin.set_state(PinState.FLOAT)  # Reset
    tab1.state = PinState.HIGH
    
    # Pin should be HIGH (due to OR logic)
    assert pin.state == PinState.HIGH
    print("✓ One tab HIGH makes pin HIGH (OR logic)")
    
    # All tabs should show HIGH (since they reflect pin)
    assert all(tab.state == PinState.HIGH for tab in [tab1, tab2, tab3, tab4])
    print("✓ All tabs show HIGH when pin is HIGH")
    
    print("✓ Multiple tabs tests passed")


def test_tab_absolute_position():
    """Test absolute position calculation."""
    print("\n=== Testing Tab Absolute Position ===")
    
    pin = Pin("page001.comp001.pin001", None)
    tab = Tab("page001.comp001.pin001.tab001", pin, (10, 20))
    
    # Component at (100, 200)
    abs_x, abs_y = tab.get_absolute_position(100, 200)
    
    assert abs_x == 110, f"Expected X=110, got {abs_x}"
    assert abs_y == 220, f"Expected Y=220, got {abs_y}"
    print(f"✓ Absolute position: ({abs_x}, {abs_y})")
    
    # Component at origin
    abs_x, abs_y = tab.get_absolute_position(0, 0)
    assert abs_x == 10 and abs_y == 20
    print(f"✓ Position from origin: ({abs_x}, {abs_y})")
    
    print("✓ Absolute position tests passed")


def test_tab_serialization():
    """Test tab serialization to dict."""
    print("\n=== Testing Tab Serialization ===")
    
    pin = Pin("page001.comp001.pin001", None)
    tab = Tab("page001.comp001.pin001.tab001", pin, (15.5, -25.0))
    
    # Serialize
    data = tab.to_dict()
    
    assert 'tab_id' in data, "Missing tab_id in serialization"
    assert 'relative_position' in data, "Missing relative_position in serialization"
    
    assert data['tab_id'] == "page001.comp001.pin001.tab001"
    assert data['relative_position'] == (15.5, -25.0)
    
    print(f"✓ Serialized data: {data}")
    print("✓ Tab serialization tests passed")


def test_tab_deserialization():
    """Test tab deserialization from dict."""
    print("\n=== Testing Tab Deserialization ===")
    
    # Create serialized data
    data = {
        'tab_id': 'page001.comp001.pin001.tab001',
        'relative_position': [30.0, -40.0]  # Lists are also supported
    }
    
    pin = Pin("page001.comp001.pin001", None)
    
    # Deserialize
    tab = Tab.from_dict(data, pin)
    
    assert tab.tab_id == "page001.comp001.pin001.tab001"
    assert tab.relative_position == (30.0, -40.0)  # Converted to tuple
    assert tab.parent_pin == pin
    
    print(f"✓ Deserialized tab: {tab.tab_id}")
    print(f"✓ Position: {tab.relative_position}")
    print("✓ Tab deserialization tests passed")


def test_tab_serialization_roundtrip():
    """Test serialize -> deserialize -> serialize produces same data."""
    print("\n=== Testing Tab Serialization Roundtrip ===")
    
    pin = Pin("page001.comp001.pin001", None)
    original_tab = Tab("page001.comp001.pin001.tab001", pin, (12.5, -8.25))
    
    # Serialize
    data1 = original_tab.to_dict()
    
    # Deserialize
    restored_tab = Tab.from_dict(data1, pin)
    
    # Serialize again
    data2 = restored_tab.to_dict()
    
    # Compare
    assert data1 == data2, "Roundtrip serialization data mismatch"
    print(f"✓ Original data: {data1}")
    print(f"✓ Roundtrip data: {data2}")
    print("✓ Roundtrip serialization tests passed")


def test_tab_without_parent_pin():
    """Test tab behavior without parent pin (edge case)."""
    print("\n=== Testing Tab Without Parent Pin ===")
    
    # Create orphan tab
    tab = Tab("page001.comp001.pin001.tab001", None, (0, 0))
    
    # Should still work but use internal state
    assert tab.state == PinState.FLOAT
    print(f"✓ Orphan tab state: {tab.state}")
    
    # Set state directly
    tab.state = PinState.HIGH
    assert tab._state == PinState.HIGH
    assert tab.state == PinState.HIGH
    print(f"✓ Orphan tab state set: {tab.state}")
    
    print("✓ Orphan tab tests passed")


def test_tab_repr():
    """Test tab string representation."""
    print("\n=== Testing Tab Repr ===")
    
    pin = Pin("page001.comp001.pin001", None)
    tab = Tab("page001.comp001.pin001.tab001", pin, (10, 20))
    
    repr_str = repr(tab)
    print(f"✓ Tab repr: {repr_str}")
    
    assert "Tab(" in repr_str
    assert "page001.comp001.pin001.tab001" in repr_str
    assert "pos=" in repr_str
    assert "state=" in repr_str
    
    print("✓ Tab repr tests passed")


def run_all_tests():
    """Run all Tab class tests."""
    print("=" * 60)
    print("TAB CLASS TEST SUITE (Phase 1.3)")
    print("=" * 60)
    
    try:
        test_tab_creation()
        test_tab_state_get()
        test_tab_state_set_propagation()
        test_multiple_tabs_on_pin()
        test_tab_absolute_position()
        test_tab_serialization()
        test_tab_deserialization()
        test_tab_serialization_roundtrip()
        test_tab_without_parent_pin()
        test_tab_repr()
        
        print("\n" + "=" * 60)
        print("✓ ALL TAB CLASS TESTS PASSED")
        print("=" * 60)
        print("\nSection 1.3 Tab Class Requirements:")
        print("✓ Define Tab class")
        print("  ✓ TabId (string, 8 char UUID)")
        print("  ✓ Position (relative to component)")
        print("  ✓ Current state (PinState)")
        print("  ✓ Parent pin reference")
        print("✓ Implement tab state management")
        print("  ✓ Get state")
        print("  ✓ Set state (propagate to pin)")
        print("✓ Add serialization support")
        print("  ✓ Serialize to file format")
        print("  ✓ Deserialize from file format")
        print("✓ Tests")
        print("  ✓ Test tab creation")
        print("  ✓ Test state management")
        print("  ✓ Test serialization/deserialization")
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
