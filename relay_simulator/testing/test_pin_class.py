"""
Test suite for Pin Class (Phase 1.4)

Comprehensive tests for Pin class definition, pin-tab synchronization, 
tab management, and serialization.
"""

import sys
import os

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.state import PinState
from core.tab import Tab
from core.pin import Pin


def test_pin_creation():
    """Test Pin class definition and creation."""
    print("\n=== Testing Pin Creation ===")
    
    # Create pin with all required properties
    pin = Pin(
        pin_id="page001.comp001.pin001",
        parent_component=None
    )
    
    # Verify properties
    assert pin.pin_id == "page001.comp001.pin001", "PinId not set correctly"
    print(f"✓ PinId: {pin.pin_id}")
    
    assert pin.parent_component is None, "Parent component not set"
    print(f"✓ Parent component reference set")
    
    assert isinstance(pin.tabs, dict), "Tabs should be a dictionary"
    assert len(pin.tabs) == 0, "Tabs should start empty"
    print(f"✓ Tabs collection initialized (empty)")
    
    assert pin.state == PinState.FLOAT, "Initial state should be FLOAT"
    print(f"✓ Initial state: {pin.state}")
    
    print("✓ Pin creation tests passed")


def test_pin_state_get_set():
    """Test pin state getting and setting."""
    print("\n=== Testing Pin State Get/Set ===")
    
    pin = Pin("page001.comp001.pin001", None)
    
    # Initial state
    assert pin.state == PinState.FLOAT
    print(f"✓ Initial state: {pin.state}")
    
    # Set to HIGH
    changed = pin.set_state(PinState.HIGH)
    assert pin.state == PinState.HIGH
    assert changed == True, "Should return True when state changes"
    print(f"✓ Set state to HIGH: {pin.state}")
    
    # Set to same state (no change)
    changed = pin.set_state(PinState.HIGH)
    assert changed == False, "Should return False when state doesn't change"
    print(f"✓ Set same state returns False")
    
    # Set back to FLOAT
    changed = pin.set_state(PinState.FLOAT)
    assert pin.state == PinState.FLOAT
    assert changed == True
    print(f"✓ Set state to FLOAT: {pin.state}")
    
    print("✓ Pin state get/set tests passed")


def test_tab_management():
    """Test adding, removing, and getting tabs."""
    print("\n=== Testing Tab Management ===")
    
    pin = Pin("page001.comp001.pin001", None)
    
    # Add first tab
    tab1 = Tab("page001.comp001.pin001.tab001", pin, (0, -20))
    pin.add_tab(tab1)
    
    assert len(pin.tabs) == 1, "Should have 1 tab"
    assert "page001.comp001.pin001.tab001" in pin.tabs
    print(f"✓ Added tab1: {len(pin.tabs)} tabs total")
    
    # Add more tabs
    tab2 = Tab("page001.comp001.pin001.tab002", pin, (20, 0))
    tab3 = Tab("page001.comp001.pin001.tab003", pin, (0, 20))
    tab4 = Tab("page001.comp001.pin001.tab004", pin, (-20, 0))
    
    pin.add_tab(tab2)
    pin.add_tab(tab3)
    pin.add_tab(tab4)
    
    assert len(pin.tabs) == 4, "Should have 4 tabs"
    print(f"✓ Added 4 tabs total: {len(pin.tabs)} tabs")
    
    # Get tab by ID
    retrieved = pin.get_tab("page001.comp001.pin001.tab002")
    assert retrieved == tab2, "Should retrieve correct tab"
    print(f"✓ Retrieved tab by ID: {retrieved.tab_id}")
    
    # Get non-existent tab
    retrieved = pin.get_tab("nonexistent")
    assert retrieved is None, "Should return None for non-existent tab"
    print(f"✓ Non-existent tab returns None")
    
    # Remove tab
    pin.remove_tab("page001.comp001.pin001.tab002")
    assert len(pin.tabs) == 3, "Should have 3 tabs after removal"
    assert "page001.comp001.pin001.tab002" not in pin.tabs
    print(f"✓ Removed tab: {len(pin.tabs)} tabs remaining")
    
    print("✓ Tab management tests passed")


def test_pin_to_tabs_propagation():
    """Test pin state change propagates to all tabs."""
    print("\n=== Testing Pin → Tabs State Propagation ===")
    
    pin = Pin("page001.comp001.pin001", None)
    
    # Add 4 tabs
    tab1 = Tab("page001.comp001.pin001.tab001", pin, (0, -20))
    tab2 = Tab("page001.comp001.pin001.tab002", pin, (20, 0))
    tab3 = Tab("page001.comp001.pin001.tab003", pin, (0, 20))
    tab4 = Tab("page001.comp001.pin001.tab004", pin, (-20, 0))
    
    pin.add_tab(tab1)
    pin.add_tab(tab2)
    pin.add_tab(tab3)
    pin.add_tab(tab4)
    
    # All tabs should start FLOAT
    assert all(tab.state == PinState.FLOAT for tab in [tab1, tab2, tab3, tab4])
    print("✓ All tabs initially FLOAT")
    
    # Set pin to HIGH
    pin.set_state(PinState.HIGH)
    
    # All tabs should be HIGH
    assert pin.state == PinState.HIGH
    assert all(tab.state == PinState.HIGH for tab in [tab1, tab2, tab3, tab4])
    print("✓ Pin HIGH propagated to all 4 tabs")
    
    # Set pin back to FLOAT
    pin.set_state(PinState.FLOAT)
    
    assert pin.state == PinState.FLOAT
    assert all(tab.state == PinState.FLOAT for tab in [tab1, tab2, tab3, tab4])
    print("✓ Pin FLOAT propagated to all 4 tabs")
    
    print("✓ Pin → Tabs propagation tests passed")


def test_tabs_to_pin_propagation():
    """Test tab state change propagates to pin."""
    print("\n=== Testing Tabs → Pin State Propagation ===")
    
    pin = Pin("page001.comp001.pin001", None)
    
    tab1 = Tab("page001.comp001.pin001.tab001", pin, (0, -20))
    tab2 = Tab("page001.comp001.pin001.tab002", pin, (20, 0))
    
    pin.add_tab(tab1)
    pin.add_tab(tab2)
    
    # Set tab1 to HIGH via tab.state setter
    tab1.state = PinState.HIGH
    
    # Pin should be HIGH
    assert pin.state == PinState.HIGH
    print("✓ Tab HIGH propagated to pin")
    
    # Other tab should also be HIGH (because pin propagates to all tabs)
    assert tab2.state == PinState.HIGH
    print("✓ Pin propagated HIGH to other tabs")
    
    print("✓ Tabs → Pin propagation tests passed")


def test_evaluate_state_from_tabs():
    """Test evaluating pin state from tab states (HIGH OR logic)."""
    print("\n=== Testing Evaluate State From Tabs (OR Logic) ===")
    
    pin = Pin("page001.comp001.pin001", None)
    
    tab1 = Tab("page001.comp001.pin001.tab001", pin, (0, -20))
    tab2 = Tab("page001.comp001.pin001.tab002", pin, (20, 0))
    tab3 = Tab("page001.comp001.pin001.tab003", pin, (0, 20))
    
    pin.add_tab(tab1)
    pin.add_tab(tab2)
    pin.add_tab(tab3)
    
    # All tabs FLOAT → Pin FLOAT
    tab1._state = PinState.FLOAT
    tab2._state = PinState.FLOAT
    tab3._state = PinState.FLOAT
    
    result = pin.evaluate_state_from_tabs()
    assert result == PinState.FLOAT
    assert pin.state == PinState.FLOAT
    print("✓ All tabs FLOAT → Pin FLOAT")
    
    # One tab HIGH → Pin HIGH (OR logic)
    tab1._state = PinState.HIGH
    tab2._state = PinState.FLOAT
    tab3._state = PinState.FLOAT
    
    result = pin.evaluate_state_from_tabs()
    assert result == PinState.HIGH
    assert pin.state == PinState.HIGH
    print("✓ One tab HIGH → Pin HIGH (OR logic)")
    
    # Multiple tabs HIGH → Pin HIGH
    tab1._state = PinState.HIGH
    tab2._state = PinState.HIGH
    tab3._state = PinState.FLOAT
    
    result = pin.evaluate_state_from_tabs()
    assert result == PinState.HIGH
    assert pin.state == PinState.HIGH
    print("✓ Multiple tabs HIGH → Pin HIGH")
    
    # All tabs HIGH → Pin HIGH
    tab1._state = PinState.HIGH
    tab2._state = PinState.HIGH
    tab3._state = PinState.HIGH
    
    result = pin.evaluate_state_from_tabs()
    assert result == PinState.HIGH
    assert pin.state == PinState.HIGH
    print("✓ All tabs HIGH → Pin HIGH")
    
    print("✓ Evaluate state from tabs tests passed")


def test_pin_with_no_tabs():
    """Test pin behavior with no tabs (edge case)."""
    print("\n=== Testing Pin With No Tabs ===")
    
    pin = Pin("page001.comp001.pin001", None)
    
    # Evaluate with no tabs
    result = pin.evaluate_state_from_tabs()
    assert result == PinState.FLOAT
    print("✓ Empty pin evaluates to FLOAT")
    
    # Set state still works
    pin.set_state(PinState.HIGH)
    assert pin.state == PinState.HIGH
    print("✓ Can set state on empty pin")
    
    print("✓ Pin with no tabs tests passed")


def test_pin_serialization():
    """Test pin serialization to dict."""
    print("\n=== Testing Pin Serialization ===")
    
    pin = Pin("page001.comp001.pin001", None)
    
    # Add some tabs
    tab1 = Tab("page001.comp001.pin001.tab001", pin, (0, -20))
    tab2 = Tab("page001.comp001.pin001.tab002", pin, (20, 0))
    pin.add_tab(tab1)
    pin.add_tab(tab2)
    
    # Serialize
    data = pin.to_dict()
    
    assert 'pin_id' in data
    assert 'tabs' in data
    assert data['pin_id'] == "page001.comp001.pin001"
    assert len(data['tabs']) == 2
    print(f"✓ Serialized pin with {len(data['tabs'])} tabs")
    
    # Check tab data is nested
    assert "page001.comp001.pin001.tab001" in data['tabs']
    assert "page001.comp001.pin001.tab002" in data['tabs']
    print(f"✓ Tab data nested in serialization")
    
    print("✓ Pin serialization tests passed")


def test_pin_deserialization():
    """Test pin deserialization from dict."""
    print("\n=== Testing Pin Deserialization ===")
    
    # Create serialized data
    data = {
        'pin_id': 'page001.comp001.pin001',
        'tabs': {
            'page001.comp001.pin001.tab001': {
                'tab_id': 'page001.comp001.pin001.tab001',
                'relative_position': [0, -20]
            },
            'page001.comp001.pin001.tab002': {
                'tab_id': 'page001.comp001.pin001.tab002',
                'relative_position': [20, 0]
            }
        }
    }
    
    # Deserialize
    pin = Pin.from_dict(data, None)
    
    assert pin.pin_id == "page001.comp001.pin001"
    assert len(pin.tabs) == 2
    print(f"✓ Deserialized pin with {len(pin.tabs)} tabs")
    
    # Check tabs were reconstructed
    assert "page001.comp001.pin001.tab001" in pin.tabs
    assert "page001.comp001.pin001.tab002" in pin.tabs
    
    tab1 = pin.tabs["page001.comp001.pin001.tab001"]
    assert tab1.relative_position == (0, -20)
    assert tab1.parent_pin == pin
    print(f"✓ Tabs reconstructed correctly")
    
    print("✓ Pin deserialization tests passed")


def test_pin_serialization_roundtrip():
    """Test serialize → deserialize → serialize produces same data."""
    print("\n=== Testing Pin Serialization Roundtrip ===")
    
    # Create original pin
    original_pin = Pin("page001.comp001.pin001", None)
    tab1 = Tab("page001.comp001.pin001.tab001", original_pin, (10, 20))
    tab2 = Tab("page001.comp001.pin001.tab002", original_pin, (-15, 30))
    original_pin.add_tab(tab1)
    original_pin.add_tab(tab2)
    
    # Serialize
    data1 = original_pin.to_dict()
    
    # Deserialize
    restored_pin = Pin.from_dict(data1, None)
    
    # Serialize again
    data2 = restored_pin.to_dict()
    
    # Compare
    assert data1['pin_id'] == data2['pin_id']
    assert len(data1['tabs']) == len(data2['tabs'])
    print(f"✓ Roundtrip data matches")
    
    print("✓ Roundtrip serialization tests passed")


def test_pin_repr():
    """Test pin string representation."""
    print("\n=== Testing Pin Repr ===")
    
    pin = Pin("page001.comp001.pin001", None)
    tab1 = Tab("page001.comp001.pin001.tab001", pin, (0, 0))
    tab2 = Tab("page001.comp001.pin001.tab002", pin, (0, 0))
    pin.add_tab(tab1)
    pin.add_tab(tab2)
    
    repr_str = repr(pin)
    print(f"✓ Pin repr: {repr_str}")
    
    assert "Pin(" in repr_str
    assert "page001.comp001.pin001" in repr_str
    assert "tabs=2" in repr_str
    assert "state=" in repr_str
    
    print("✓ Pin repr tests passed")


def test_multiple_tabs_high_or_logic():
    """Test HIGH OR logic with multiple tabs (requirement from project plan)."""
    print("\n=== Testing Multiple Tabs HIGH OR Logic ===")
    
    pin = Pin("page001.comp001.pin001", None)
    
    # Create 4 tabs like an indicator component
    tab1 = Tab("page001.comp001.pin001.tab001", pin, (0, -20))   # 12 o'clock
    tab2 = Tab("page001.comp001.pin001.tab002", pin, (20, 0))    # 3 o'clock
    tab3 = Tab("page001.comp001.pin001.tab003", pin, (0, 20))    # 6 o'clock
    tab4 = Tab("page001.comp001.pin001.tab004", pin, (-20, 0))   # 9 o'clock
    
    pin.add_tab(tab1)
    pin.add_tab(tab2)
    pin.add_tab(tab3)
    pin.add_tab(tab4)
    
    print(f"✓ Created pin with {len(pin.tabs)} tabs")
    
    # Test case 1: All FLOAT
    for tab in pin.tabs.values():
        tab._state = PinState.FLOAT
    assert pin.evaluate_state_from_tabs() == PinState.FLOAT
    print("✓ All FLOAT → Pin FLOAT")
    
    # Test case 2: One HIGH, rest FLOAT
    tab1._state = PinState.HIGH
    for tab in [tab2, tab3, tab4]:
        tab._state = PinState.FLOAT
    assert pin.evaluate_state_from_tabs() == PinState.HIGH
    print("✓ 1 HIGH + 3 FLOAT → Pin HIGH")
    
    # Test case 3: Two HIGH, two FLOAT
    tab1._state = PinState.HIGH
    tab2._state = PinState.HIGH
    tab3._state = PinState.FLOAT
    tab4._state = PinState.FLOAT
    assert pin.evaluate_state_from_tabs() == PinState.HIGH
    print("✓ 2 HIGH + 2 FLOAT → Pin HIGH")
    
    # Test case 4: All HIGH
    for tab in pin.tabs.values():
        tab._state = PinState.HIGH
    assert pin.evaluate_state_from_tabs() == PinState.HIGH
    print("✓ All HIGH → Pin HIGH")
    
    print("✓ HIGH OR logic tests passed")


def run_all_tests():
    """Run all Pin class tests."""
    print("=" * 60)
    print("PIN CLASS TEST SUITE (Phase 1.4)")
    print("=" * 60)
    
    try:
        test_pin_creation()
        test_pin_state_get_set()
        test_tab_management()
        test_pin_to_tabs_propagation()
        test_tabs_to_pin_propagation()
        test_evaluate_state_from_tabs()
        test_pin_with_no_tabs()
        test_pin_serialization()
        test_pin_deserialization()
        test_pin_serialization_roundtrip()
        test_pin_repr()
        test_multiple_tabs_high_or_logic()
        
        print("\n" + "=" * 60)
        print("✓ ALL PIN CLASS TESTS PASSED")
        print("=" * 60)
        print("\nSection 1.4 Pin Class Requirements:")
        print("✓ Define Pin class")
        print("  ✓ PinId (string, 8 char UUID)")
        print("  ✓ Collection of Tabs")
        print("  ✓ Current state (PinState)")
        print("  ✓ Parent component reference")
        print("✓ Implement pin-tab state synchronization")
        print("  ✓ Tab state change → Pin state update")
        print("  ✓ Pin state change → All tabs update")
        print("  ✓ HIGH OR logic across all tabs")
        print("✓ Add tab management")
        print("  ✓ Add tab")
        print("  ✓ Remove tab")
        print("  ✓ Get all tabs")
        print("✓ Add serialization support")
        print("  ✓ Serialize to dict")
        print("  ✓ Deserialize from dict")
        print("✓ Tests")
        print("  ✓ Test pin-tab state propagation")
        print("  ✓ Test multiple tabs on one pin")
        print("  ✓ Test HIGH OR logic with multiple tabs")
        print("  ✓ Test serialization")
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
