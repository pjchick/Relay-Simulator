"""
Test Suite for Component Factory/Registry (Phase 3.4)

Tests the ComponentFactory including:
- Component type registration
- Component creation by type string
- Deserialization from file data
- Component type listing
- Error handling
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.factory import ComponentFactory, get_factory, reset_factory
from components.base import Component
from components.switch import Switch
from components.indicator import Indicator
from components.dpdt_relay import DPDTRelay
from components.vcc import VCC


# ============================================================
# Test Functions
# ============================================================

def test_factory_creation():
    """Test factory creation and initialization."""
    print("=== Testing Factory Creation ===")
    
    factory = ComponentFactory()
    
    # Check factory created
    assert factory is not None
    print("✓ Factory created")
    
    # Check built-in components registered
    assert factory.is_registered("Switch")
    assert factory.is_registered("Indicator")
    assert factory.is_registered("DPDTRelay")
    assert factory.is_registered("VCC")
    print("✓ Built-in components registered")
    
    print("✓ Factory creation tests passed\n")


def test_list_component_types():
    """Test listing all registered component types."""
    print("=== Testing List Component Types ===")
    
    factory = ComponentFactory()
    
    # Get list of types
    types = factory.list_component_types()
    
    # Check all expected types present
    assert "Switch" in types
    assert "Indicator" in types
    assert "DPDTRelay" in types
    assert "VCC" in types
    print(f"✓ Component types: {types}")
    
    # Check list is sorted
    assert types == sorted(types)
    print("✓ List is sorted")
    
    print("✓ List component types tests passed\n")


def test_create_switch():
    """Test creating a Switch component."""
    print("=== Testing Create Switch ===")
    
    factory = ComponentFactory()
    
    # Create switch
    switch = factory.create_component("Switch", "sw001", "page1")
    
    # Verify it's a Switch
    assert isinstance(switch, Switch)
    assert switch.component_type == "Switch"
    assert switch.component_id == "sw001"
    assert switch.page_id == "page1"
    print("✓ Switch created successfully")
    
    print("✓ Create switch tests passed\n")


def test_create_indicator():
    """Test creating an Indicator component."""
    print("=== Testing Create Indicator ===")
    
    factory = ComponentFactory()
    
    # Create indicator
    indicator = factory.create_component("Indicator", "led001", "page1")
    
    # Verify it's an Indicator
    assert isinstance(indicator, Indicator)
    assert indicator.component_type == "Indicator"
    assert indicator.component_id == "led001"
    assert indicator.page_id == "page1"
    print("✓ Indicator created successfully")
    
    print("✓ Create indicator tests passed\n")


def test_create_dpdt_relay():
    """Test creating a DPDT Relay component."""
    print("=== Testing Create DPDT Relay ===")
    
    factory = ComponentFactory()
    
    # Create relay
    relay = factory.create_component("DPDTRelay", "relay001", "page1")
    
    # Verify it's a DPDTRelay
    assert isinstance(relay, DPDTRelay)
    assert relay.component_type == "DPDTRelay"
    assert relay.component_id == "relay001"
    assert relay.page_id == "page1"
    print("✓ DPDT Relay created successfully")
    
    print("✓ Create DPDT relay tests passed\n")


def test_create_vcc():
    """Test creating a VCC component."""
    print("=== Testing Create VCC ===")
    
    factory = ComponentFactory()
    
    # Create VCC
    vcc = factory.create_component("VCC", "vcc001", "page1")
    
    # Verify it's a VCC
    assert isinstance(vcc, VCC)
    assert vcc.component_type == "VCC"
    assert vcc.component_id == "vcc001"
    assert vcc.page_id == "page1"
    print("✓ VCC created successfully")
    
    print("✓ Create VCC tests passed\n")


def test_create_unknown_type():
    """Test error handling for unknown component type."""
    print("=== Testing Create Unknown Type ===")
    
    factory = ComponentFactory()
    
    # Try to create unknown type
    try:
        factory.create_component("UnknownType", "comp001", "page1")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown component type" in str(e)
        print("✓ ValueError raised for unknown type")
    
    print("✓ Create unknown type tests passed\n")


def test_deserialize_switch():
    """Test deserializing a Switch from data."""
    print("=== Testing Deserialize Switch ===")
    
    factory = ComponentFactory()
    
    # Create and serialize a switch
    switch1 = Switch("sw001", "page1")
    switch1.properties["label"] = "Power Switch"
    switch1.set_color("green")
    data = switch1.to_dict()
    
    # Deserialize
    switch2 = factory.create_from_dict(data)
    
    # Verify restored
    assert isinstance(switch2, Switch)
    assert switch2.component_id == "sw001"
    assert switch2.properties["label"] == "Power Switch"
    assert switch2.properties["color"] == "green"
    print("✓ Switch deserialized successfully")
    
    print("✓ Deserialize switch tests passed\n")


def test_deserialize_indicator():
    """Test deserializing an Indicator from data."""
    print("=== Testing Deserialize Indicator ===")
    
    factory = ComponentFactory()
    
    # Create and serialize an indicator
    ind1 = Indicator("led001", "page1")
    ind1.properties["label"] = "Status LED"
    ind1.set_color("blue")
    data = ind1.to_dict()
    
    # Deserialize
    ind2 = factory.create_from_dict(data)
    
    # Verify restored
    assert isinstance(ind2, Indicator)
    assert ind2.component_id == "led001"
    assert ind2.properties["label"] == "Status LED"
    assert ind2.properties["color"] == "blue"
    print("✓ Indicator deserialized successfully")
    
    print("✓ Deserialize indicator tests passed\n")


def test_deserialize_dpdt_relay():
    """Test deserializing a DPDT Relay from data."""
    print("=== Testing Deserialize DPDT Relay ===")
    
    factory = ComponentFactory()
    
    # Create and serialize a relay
    relay1 = DPDTRelay("relay001", "page1")
    relay1.properties["label"] = "Main Relay"
    relay1.set_color("red")
    data = relay1.to_dict()
    
    # Deserialize
    relay2 = factory.create_from_dict(data)
    
    # Verify restored
    assert isinstance(relay2, DPDTRelay)
    assert relay2.component_id == "relay001"
    assert relay2.properties["label"] == "Main Relay"
    assert relay2.properties["color"] == "red"
    print("✓ DPDT Relay deserialized successfully")
    
    print("✓ Deserialize DPDT relay tests passed\n")


def test_deserialize_vcc():
    """Test deserializing a VCC from data."""
    print("=== Testing Deserialize VCC ===")
    
    factory = ComponentFactory()
    
    # Create and serialize a VCC
    vcc1 = VCC("vcc001", "page1")
    vcc1.properties["label"] = "+5V"
    data = vcc1.to_dict()
    
    # Deserialize
    vcc2 = factory.create_from_dict(data)
    
    # Verify restored
    assert isinstance(vcc2, VCC)
    assert vcc2.component_id == "vcc001"
    assert vcc2.properties["label"] == "+5V"
    print("✓ VCC deserialized successfully")
    
    print("✓ Deserialize VCC tests passed\n")


def test_deserialize_missing_type():
    """Test error handling for data missing type field."""
    print("=== Testing Deserialize Missing Type ===")
    
    factory = ComponentFactory()
    
    # Data without type field
    data = {
        "component_id": "comp001",
        "properties": {}
    }
    
    # Try to deserialize
    try:
        factory.create_from_dict(data)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "missing 'type' field" in str(e)
        print("✓ ValueError raised for missing type")
    
    print("✓ Deserialize missing type tests passed\n")


def test_deserialize_unknown_type():
    """Test error handling for unknown component type in data."""
    print("=== Testing Deserialize Unknown Type ===")
    
    factory = ComponentFactory()
    
    # Data with unknown type
    data = {
        "type": "UnknownComponent",
        "component_id": "comp001",
        "properties": {}
    }
    
    # Try to deserialize
    try:
        factory.create_from_dict(data)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown component type" in str(e)
        print("✓ ValueError raised for unknown type")
    
    print("✓ Deserialize unknown type tests passed\n")


def test_custom_component_registration():
    """Test registering a custom component type."""
    print("=== Testing Custom Component Registration ===")
    
    # Create a custom component class
    class CustomComponent(Component):
        component_type = "Custom"
        
        def __init__(self, component_id: str, page_id: str):
            super().__init__(component_id, page_id)
        
        def simulate_logic(self, vnet_manager):
            pass
        
        def sim_start(self, vnet_manager, bridge_manager=None):
            pass
        
        def sim_stop(self, vnet_manager=None, bridge_manager=None):
            pass
        
        def interact(self, action: str, params=None) -> bool:
            return False
        
        def render(self, canvas_adapter, x_offset=0, y_offset=0):
            pass
    
    factory = ComponentFactory()
    
    # Register custom component
    factory.register_component("Custom", CustomComponent)
    print("✓ Custom component registered")
    
    # Check it's registered
    assert factory.is_registered("Custom")
    print("✓ Custom component found in registry")
    
    # Create instance
    custom = factory.create_component("Custom", "custom001", "page1")
    assert isinstance(custom, CustomComponent)
    assert custom.component_type == "Custom"
    print("✓ Custom component created")
    
    print("✓ Custom component registration tests passed\n")


def test_duplicate_registration():
    """Test error handling for duplicate type registration."""
    print("=== Testing Duplicate Registration ===")
    
    factory = ComponentFactory()
    
    # Try to register Switch again
    try:
        factory.register_component("Switch", Switch)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "already registered" in str(e)
        print("✓ ValueError raised for duplicate registration")
    
    print("✓ Duplicate registration tests passed\n")


def test_get_component_class():
    """Test getting component class by type."""
    print("=== Testing Get Component Class ===")
    
    factory = ComponentFactory()
    
    # Get Switch class
    switch_class = factory.get_component_class("Switch")
    assert switch_class == Switch
    print("✓ Switch class retrieved")
    
    # Get Indicator class
    indicator_class = factory.get_component_class("Indicator")
    assert indicator_class == Indicator
    print("✓ Indicator class retrieved")
    
    # Try unknown type
    try:
        factory.get_component_class("Unknown")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✓ ValueError raised for unknown type")
    
    print("✓ Get component class tests passed\n")


def test_registry_info():
    """Test getting registry information."""
    print("=== Testing Registry Info ===")
    
    factory = ComponentFactory()
    
    # Get registry info
    info = factory.get_registry_info()
    
    # Check info structure
    assert "Switch" in info
    assert "Indicator" in info
    assert "DPDTRelay" in info
    assert "VCC" in info
    print("✓ Registry info contains all components")
    
    # Check Switch info
    switch_info = info["Switch"]
    assert switch_info["type"] == "Switch"
    assert switch_info["class_name"] == "Switch"
    assert "module" in switch_info
    print("✓ Component info has correct structure")
    
    print("✓ Registry info tests passed\n")


def test_global_factory():
    """Test global factory singleton."""
    print("=== Testing Global Factory ===")
    
    # Reset factory
    reset_factory()
    
    # Get factory twice
    factory1 = get_factory()
    factory2 = get_factory()
    
    # Should be same instance
    assert factory1 is factory2
    print("✓ Global factory is singleton")
    
    # Should have built-in components
    assert factory1.is_registered("Switch")
    assert factory1.is_registered("Indicator")
    print("✓ Global factory has built-in components")
    
    # Reset factory
    reset_factory()
    factory3 = get_factory()
    
    # Should be new instance
    assert factory3 is not factory1
    print("✓ Reset factory creates new instance")
    
    print("✓ Global factory tests passed\n")


# ============================================================
# Main Test Runner
# ============================================================

def run_all_tests():
    """Run all component factory tests."""
    print("=" * 60)
    print("COMPONENT FACTORY/REGISTRY TEST SUITE (Phase 3.4)")
    print("=" * 60)
    print()
    
    tests = [
        test_factory_creation,
        test_list_component_types,
        test_create_switch,
        test_create_indicator,
        test_create_dpdt_relay,
        test_create_vcc,
        test_create_unknown_type,
        test_deserialize_switch,
        test_deserialize_indicator,
        test_deserialize_dpdt_relay,
        test_deserialize_vcc,
        test_deserialize_missing_type,
        test_deserialize_unknown_type,
        test_custom_component_registration,
        test_duplicate_registration,
        test_get_component_class,
        test_registry_info,
        test_global_factory,
    ]
    
    for test in tests:
        test()
    
    print("=" * 60)
    print("✓ ALL COMPONENT FACTORY TESTS PASSED")
    print("=" * 60)
    print()
    print("Section 3.4 Component Factory/Registry Requirements:")
    print("✓ Create ComponentFactory class")
    print("  ✓ Register component types")
    print("  ✓ Create component by type string")
    print("  ✓ List available component types")
    print("  ✓ Get component class by type")
    print("  ✓ Get registry information")
    print("✓ Register all components")
    print("  ✓ Switch")
    print("  ✓ Indicator")
    print("  ✓ DPDTRelay")
    print("  ✓ VCC")
    print("✓ Support deserialization")
    print("  ✓ Create component from file data")
    print("  ✓ Restore all properties")
    print("  ✓ Handle missing type field")
    print("  ✓ Handle unknown types")
    print("✓ Additional features")
    print("  ✓ Custom component registration")
    print("  ✓ Duplicate registration prevention")
    print("  ✓ Global factory singleton")
    print("✓ Tests")
    print("  ✓ Test component creation by type")
    print("  ✓ Test component registration")
    print("  ✓ Test deserialization")
    print("  ✓ Test error handling")
    print("  ✓ Test all component types")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
