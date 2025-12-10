"""
Test suite for Component Base Class (Phase 1.5)

Comprehensive tests for Component base class definition, pin management, 
property management, and serialization interface.
"""

import sys
import os

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


# Create a concrete test component for testing
class TestComponent(Component):
    """Concrete component for testing base class functionality."""
    
    component_type = "TestComponent"
    
    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)
        self.logic_called = False
        self.start_called = False
        self.stop_called = False
    
    def simulate_logic(self, vnet_manager):
        """Test implementation of simulate_logic."""
        self.logic_called = True
    
    def sim_start(self, vnet_manager, bridge_manager):
        """Test implementation of sim_start."""
        self.start_called = True
    
    def sim_stop(self):
        """Test implementation of sim_stop."""
        self.stop_called = True
    
    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        """Test implementation of render."""
        pass
    
    @classmethod
    def from_dict(cls, data):
        """Test implementation of from_dict."""
        comp = cls(data['component_id'], data.get('page_id', 'page001'))
        comp.position = tuple(data.get('position', (0, 0)))
        comp.rotation = data.get('rotation', 0)
        comp.properties = data.get('properties', {}).copy()
        comp.link_name = data.get('link_name')
        
        # Reconstruct pins
        from core.pin import Pin
        for pin_data in data.get('pins', {}).values():
            pin = Pin.from_dict(pin_data, comp)
            comp.add_pin(pin)
        
        return comp


def test_component_creation():
    """Test Component base class instantiation."""
    print("\n=== Testing Component Creation ===")
    
    comp = TestComponent("comp001", "page001")
    
    # Verify basic properties
    assert comp.component_id == "comp001", "ComponentId not set"
    print(f"✓ ComponentId: {comp.component_id}")
    
    assert comp.page_id == "page001", "PageId not set"
    print(f"✓ PageId: {comp.page_id}")
    
    assert comp.component_type == "TestComponent", "ComponentType not set"
    print(f"✓ ComponentType: {comp.component_type}")
    
    assert comp.position == (0, 0), "Position not initialized"
    print(f"✓ Position: {comp.position}")
    
    assert comp.rotation == 0, "Rotation not initialized"
    print(f"✓ Rotation: {comp.rotation}")
    
    assert comp.link_name is None, "LinkName should be None initially"
    print(f"✓ LinkName: {comp.link_name}")
    
    assert isinstance(comp.pins, dict), "Pins should be a dict"
    assert len(comp.pins) == 0, "Pins should start empty"
    print(f"✓ Pins collection initialized (empty)")
    
    assert isinstance(comp.properties, dict), "Properties should be a dict"
    assert len(comp.properties) == 0, "Properties should start empty"
    print(f"✓ Properties dictionary initialized (empty)")
    
    print("✓ Component creation tests passed")


def test_pin_management_add():
    """Test adding pins to component."""
    print("\n=== Testing Pin Management - Add ===")
    
    comp = TestComponent("comp001", "page001")
    
    # Create and add pin
    pin1 = Pin("page001.comp001.pin001", comp)
    comp.add_pin(pin1)
    
    assert len(comp.pins) == 1, "Should have 1 pin"
    assert "page001.comp001.pin001" in comp.pins
    assert comp.pins["page001.comp001.pin001"] == pin1
    assert pin1.parent_component == comp
    print(f"✓ Added pin1: {len(comp.pins)} pins total")
    
    # Add more pins
    pin2 = Pin("page001.comp001.pin002", comp)
    pin3 = Pin("page001.comp001.pin003", comp)
    comp.add_pin(pin2)
    comp.add_pin(pin3)
    
    assert len(comp.pins) == 3, "Should have 3 pins"
    print(f"✓ Added 3 pins total")
    
    print("✓ Pin add tests passed")


def test_pin_management_get():
    """Test getting pins from component."""
    print("\n=== Testing Pin Management - Get ===")
    
    comp = TestComponent("comp001", "page001")
    
    pin1 = Pin("page001.comp001.pin001", comp)
    pin2 = Pin("page001.comp001.pin002", comp)
    comp.add_pin(pin1)
    comp.add_pin(pin2)
    
    # Get specific pin
    retrieved = comp.get_pin("page001.comp001.pin001")
    assert retrieved == pin1, "Should retrieve correct pin"
    print(f"✓ Retrieved pin by ID: {retrieved.pin_id}")
    
    # Get non-existent pin
    retrieved = comp.get_pin("nonexistent")
    assert retrieved is None, "Should return None for non-existent pin"
    print(f"✓ Non-existent pin returns None")
    
    # Get all pins
    all_pins = comp.get_all_pins()
    assert len(all_pins) == 2, "Should return all pins"
    assert "page001.comp001.pin001" in all_pins
    assert "page001.comp001.pin002" in all_pins
    print(f"✓ Retrieved all pins: {len(all_pins)} pins")
    
    # Verify it's a copy (modification doesn't affect original)
    all_pins["new_pin"] = Pin("page001.comp001.pin999", comp)
    assert len(comp.pins) == 2, "Modifying returned dict shouldn't affect component"
    print(f"✓ get_all_pins returns copy")
    
    print("✓ Pin get tests passed")


def test_pin_management_remove():
    """Test removing pins from component."""
    print("\n=== Testing Pin Management - Remove ===")
    
    comp = TestComponent("comp001", "page001")
    
    pin1 = Pin("page001.comp001.pin001", comp)
    pin2 = Pin("page001.comp001.pin002", comp)
    comp.add_pin(pin1)
    comp.add_pin(pin2)
    
    # Remove existing pin
    result = comp.remove_pin("page001.comp001.pin001")
    assert result == True, "Should return True when pin removed"
    assert len(comp.pins) == 1, "Should have 1 pin remaining"
    assert "page001.comp001.pin001" not in comp.pins
    print(f"✓ Removed pin: {len(comp.pins)} remaining")
    
    # Try to remove non-existent pin
    result = comp.remove_pin("nonexistent")
    assert result == False, "Should return False when pin not found"
    assert len(comp.pins) == 1, "Pin count shouldn't change"
    print(f"✓ Remove non-existent pin returns False")
    
    print("✓ Pin remove tests passed")


def test_property_management():
    """Test property get/set operations."""
    print("\n=== Testing Property Management ===")
    
    comp = TestComponent("comp001", "page001")
    
    # Set properties
    comp.set_property("label", "My Component")
    comp.set_property("enabled", True)
    comp.set_property("value", 42)
    
    assert len(comp.properties) == 3, "Should have 3 properties"
    print(f"✓ Set 3 properties")
    
    # Get properties
    label = comp.get_property("label")
    assert label == "My Component", f"Expected 'My Component', got {label}"
    print(f"✓ Get property 'label': {label}")
    
    enabled = comp.get_property("enabled")
    assert enabled == True
    print(f"✓ Get property 'enabled': {enabled}")
    
    # Get non-existent property with default
    missing = comp.get_property("missing", "default_value")
    assert missing == "default_value", "Should return default for missing property"
    print(f"✓ Get missing property returns default: {missing}")
    
    # Get non-existent property without default
    missing = comp.get_property("missing")
    assert missing is None, "Should return None for missing property"
    print(f"✓ Get missing property without default returns None")
    
    print("✓ Property management tests passed")


def test_property_clone():
    """Test property cloning for copy operations."""
    print("\n=== Testing Property Clone ===")
    
    comp = TestComponent("comp001", "page001")
    
    # Set properties including nested structures
    comp.set_property("label", "Original")
    comp.set_property("config", {"setting1": "value1", "setting2": "value2"})
    comp.set_property("values", [1, 2, 3])
    
    # Clone properties
    cloned = comp.clone_properties()
    
    assert len(cloned) == 3, "Should have 3 cloned properties"
    assert cloned["label"] == "Original"
    print(f"✓ Cloned {len(cloned)} properties")
    
    # Modify clone - original should not change
    cloned["label"] = "Modified"
    cloned["config"]["setting1"] = "modified_value"
    cloned["values"].append(4)
    
    assert comp.get_property("label") == "Original", "Original should not change"
    assert comp.get_property("config")["setting1"] == "value1", "Nested dict should not change"
    assert len(comp.get_property("values")) == 3, "Nested list should not change"
    print(f"✓ Clone is deep copy (modifications don't affect original)")
    
    print("✓ Property clone tests passed")


def test_position_and_rotation():
    """Test position and rotation properties."""
    print("\n=== Testing Position and Rotation ===")
    
    comp = TestComponent("comp001", "page001")
    
    # Set position
    comp.position = (100, 200)
    assert comp.position == (100, 200), "Position not set correctly"
    print(f"✓ Position: {comp.position}")
    
    # Set rotation
    comp.rotation = 90
    assert comp.rotation == 90, "Rotation not set correctly"
    print(f"✓ Rotation: {comp.rotation}")
    
    print("✓ Position and rotation tests passed")


def test_link_name():
    """Test link name property for cross-page connections."""
    print("\n=== Testing Link Name ===")
    
    comp = TestComponent("comp001", "page001")
    
    # Initially None
    assert comp.link_name is None
    print(f"✓ Initial link_name: {comp.link_name}")
    
    # Set link name
    comp.link_name = "POWER_BUS"
    assert comp.link_name == "POWER_BUS"
    print(f"✓ Set link_name: {comp.link_name}")
    
    print("✓ Link name tests passed")


def test_simulation_lifecycle():
    """Test simulation lifecycle methods."""
    print("\n=== Testing Simulation Lifecycle ===")
    
    comp = TestComponent("comp001", "page001")
    
    # sim_start
    comp.sim_start(None, None)
    assert comp.start_called == True, "sim_start should be called"
    print(f"✓ sim_start() called")
    
    # simulate_logic
    comp.simulate_logic(None)
    assert comp.logic_called == True, "simulate_logic should be called"
    print(f"✓ simulate_logic() called")
    
    # sim_stop
    comp.sim_stop()
    assert comp.stop_called == True, "sim_stop should be called"
    print(f"✓ sim_stop() called")
    
    print("✓ Simulation lifecycle tests passed")


def test_interact_method():
    """Test interaction handling."""
    print("\n=== Testing Interaction Method ===")
    
    comp = TestComponent("comp001", "page001")
    
    # Default interact returns False
    result = comp.interact("toggle")
    assert result == False, "Default interact should return False"
    print(f"✓ Default interact returns False")
    
    # With parameters
    result = comp.interact("set_value", {"value": 100})
    assert result == False
    print(f"✓ Interact with params returns False")
    
    print("✓ Interaction tests passed")


def test_get_visual_state():
    """Test visual state retrieval."""
    print("\n=== Testing Get Visual State ===")
    
    comp = TestComponent("comp001", "page001")
    comp.position = (150, 250)
    comp.rotation = 45
    comp.set_property("color", "red")
    
    # Add a pin
    pin1 = Pin("page001.comp001.pin001", comp)
    pin1.set_state(PinState.HIGH)
    comp.add_pin(pin1)
    
    # Get visual state
    visual = comp.get_visual_state()
    
    assert visual['type'] == "TestComponent"
    assert visual['component_id'] == "comp001"
    assert visual['position'] == (150, 250)
    assert visual['rotation'] == 45
    assert 'properties' in visual
    assert visual['properties']['color'] == "red"
    assert 'pin_states' in visual
    assert visual['pin_states']['page001.comp001.pin001'] == "HIGH"
    
    print(f"✓ Visual state contains all fields")
    print(f"  Type: {visual['type']}")
    print(f"  Position: {visual['position']}")
    print(f"  Pin states: {visual['pin_states']}")
    
    print("✓ Visual state tests passed")


def test_serialization():
    """Test component serialization."""
    print("\n=== Testing Serialization ===")
    
    comp = TestComponent("comp001", "page001")
    comp.position = (100, 200)
    comp.rotation = 90
    comp.link_name = "POWER"
    comp.set_property("label", "Test Component")
    
    # Add pins with tabs
    pin1 = Pin("page001.comp001.pin001", comp)
    tab1 = Tab("page001.comp001.pin001.tab001", pin1, (0, -10))
    pin1.add_tab(tab1)
    comp.add_pin(pin1)
    
    # Serialize
    data = comp.to_dict()
    
    assert 'component_id' in data
    assert 'type' in data
    assert 'position' in data
    assert 'rotation' in data
    assert 'properties' in data
    assert 'link_name' in data
    assert 'pins' in data
    
    assert data['component_id'] == "comp001"
    assert data['type'] == "TestComponent"
    assert data['position'] == (100, 200)
    assert data['rotation'] == 90
    assert data['link_name'] == "POWER"
    assert data['properties']['label'] == "Test Component"
    assert len(data['pins']) == 1
    
    print(f"✓ Serialization includes all fields")
    print(f"  Component: {data['component_id']}")
    print(f"  Type: {data['type']}")
    print(f"  Pins: {len(data['pins'])}")
    
    print("✓ Serialization tests passed")


def test_deserialization():
    """Test component deserialization."""
    print("\n=== Testing Deserialization ===")
    
    # Create serialized data
    data = {
        'component_id': 'comp002',
        'page_id': 'page002',
        'type': 'TestComponent',
        'position': [200, 300],
        'rotation': 180,
        'link_name': 'GND',
        'properties': {'label': 'Restored Component'},
        'pins': {
            'page002.comp002.pin001': {
                'pin_id': 'page002.comp002.pin001',
                'tabs': {
                    'page002.comp002.pin001.tab001': {
                        'tab_id': 'page002.comp002.pin001.tab001',
                        'relative_position': [5, -5]
                    }
                }
            }
        }
    }
    
    # Deserialize
    comp = TestComponent.from_dict(data)
    
    assert comp.component_id == "comp002"
    assert comp.page_id == "page002"
    assert comp.position == (200, 300)
    assert comp.rotation == 180
    assert comp.link_name == "GND"
    assert comp.get_property("label") == "Restored Component"
    assert len(comp.pins) == 1
    
    print(f"✓ Deserialized component: {comp.component_id}")
    print(f"  Position: {comp.position}")
    print(f"  Pins: {len(comp.pins)}")
    
    print("✓ Deserialization tests passed")


def test_serialization_roundtrip():
    """Test serialize → deserialize → serialize produces same data."""
    print("\n=== Testing Serialization Roundtrip ===")
    
    # Create original component
    comp1 = TestComponent("comp001", "page001")
    comp1.position = (123, 456)
    comp1.rotation = 270
    comp1.link_name = "TEST_LINK"
    comp1.set_property("value", 99)
    
    pin1 = Pin("page001.comp001.pin001", comp1)
    tab1 = Tab("page001.comp001.pin001.tab001", pin1, (10, 20))
    pin1.add_tab(tab1)
    comp1.add_pin(pin1)
    
    # Serialize
    data1 = comp1.to_dict()
    
    # Deserialize
    comp2 = TestComponent.from_dict(data1)
    
    # Serialize again
    data2 = comp2.to_dict()
    
    # Compare key fields
    assert data1['component_id'] == data2['component_id']
    assert data1['type'] == data2['type']
    assert data1['position'] == data2['position']
    assert data1['rotation'] == data2['rotation']
    assert data1['link_name'] == data2['link_name']
    assert len(data1['pins']) == len(data2['pins'])
    
    print(f"✓ Roundtrip data matches")
    
    print("✓ Roundtrip tests passed")


def test_component_repr():
    """Test component string representation."""
    print("\n=== Testing Component Repr ===")
    
    comp = TestComponent("comp001", "page001")
    
    repr_str = repr(comp)
    print(f"✓ Component repr: {repr_str}")
    
    assert "TestComponent" in repr_str
    assert "comp001" in repr_str
    
    print("✓ Component repr tests passed")


def run_all_tests():
    """Run all Component base class tests."""
    print("=" * 60)
    print("COMPONENT BASE CLASS TEST SUITE (Phase 1.5)")
    print("=" * 60)
    
    try:
        test_component_creation()
        test_pin_management_add()
        test_pin_management_get()
        test_pin_management_remove()
        test_property_management()
        test_property_clone()
        test_position_and_rotation()
        test_link_name()
        test_simulation_lifecycle()
        test_interact_method()
        test_get_visual_state()
        test_serialization()
        test_deserialization()
        test_serialization_roundtrip()
        test_component_repr()
        
        print("\n" + "=" * 60)
        print("✓ ALL COMPONENT BASE CLASS TESTS PASSED")
        print("=" * 60)
        print("\nSection 1.5 Component Base Class Requirements:")
        print("✓ Define Component base class")
        print("  ✓ ComponentId (string)")
        print("  ✓ ComponentType (string)")
        print("  ✓ Position (X, Y)")
        print("  ✓ Rotation")
        print("  ✓ LinkName (optional string)")
        print("  ✓ Collection of Pins")
        print("  ✓ Custom properties dictionary")
        print("✓ Define required methods")
        print("  ✓ simulate_logic() - Abstract")
        print("  ✓ render() - Abstract")
        print("  ✓ interact() - Default implementation")
        print("  ✓ sim_start() - Abstract")
        print("  ✓ sim_stop() - Default implementation")
        print("✓ Add pin management")
        print("  ✓ add_pin()")
        print("  ✓ get_pin()")
        print("  ✓ get_all_pins()")
        print("  ✓ remove_pin()")
        print("✓ Add property management")
        print("  ✓ get_property()")
        print("  ✓ set_property()")
        print("  ✓ clone_properties()")
        print("✓ Add serialization support")
        print("  ✓ to_dict()")
        print("  ✓ from_dict() - Abstract")
        print("✓ Tests")
        print("  ✓ Test component creation")
        print("  ✓ Test pin management")
        print("  ✓ Test property management")
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
