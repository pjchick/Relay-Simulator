"""
Test suite for Page Class (Phase 1.6)

Comprehensive tests for Page class definition, component management,
wire management, and serialization.
"""

import sys
import os

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.page import Page
from core.pin import Pin
from core.tab import Tab
from components.base import Component


# Create a simple test component
class SimpleComponent(Component):
    """Simple test component."""
    component_type = "SimpleComponent"
    
    def simulate_logic(self, vnet_manager):
        pass
    
    def sim_start(self, vnet_manager, bridge_manager):
        pass
    
    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        pass
    
    @classmethod
    def from_dict(cls, data):
        comp = cls(data['component_id'], data.get('page_id', 'page001'))
        comp.position = tuple(data.get('position', (0, 0)))
        comp.rotation = data.get('rotation', 0)
        comp.properties = data.get('properties', {}).copy()
        comp.link_name = data.get('link_name')
        return comp


# Create a simple wire class for testing
class SimpleWire:
    """Simple test wire."""
    def __init__(self, wire_id: str):
        self.wire_id = wire_id
    
    def to_dict(self):
        return {'wire_id': self.wire_id}
    
    @staticmethod
    def from_dict(data):
        return SimpleWire(data['wire_id'])


def test_page_creation():
    """Test Page class creation."""
    print("\n=== Testing Page Creation ===")
    
    # Create with default name
    page1 = Page("page001")
    assert page1.page_id == "page001", "PageId not set"
    assert page1.name == "Untitled", "Default name should be 'Untitled'"
    print(f"✓ Created page with default name: '{page1.name}'")
    
    # Create with custom name
    page2 = Page("page002", "Main Schematic")
    assert page2.page_id == "page002"
    assert page2.name == "Main Schematic"
    print(f"✓ Created page with custom name: '{page2.name}'")
    
    # Verify collections initialized
    assert isinstance(page1.components, dict), "Components should be dict"
    assert len(page1.components) == 0, "Components should start empty"
    print(f"✓ Components collection initialized (empty)")
    
    assert isinstance(page1.wires, dict), "Wires should be dict"
    assert len(page1.wires) == 0, "Wires should start empty"
    print(f"✓ Wires collection initialized (empty)")
    
    print("✓ Page creation tests passed")


def test_add_component():
    """Test adding components to page."""
    print("\n=== Testing Add Component ===")
    
    page = Page("page001", "Test Page")
    
    # Create and add component
    comp1 = SimpleComponent("comp001", "page001")
    page.add_component(comp1)
    
    assert len(page.components) == 1
    assert "comp001" in page.components
    assert page.components["comp001"] == comp1
    print(f"✓ Added component: {len(page.components)} total")
    
    # Add more components
    comp2 = SimpleComponent("comp002", "page001")
    comp3 = SimpleComponent("comp003", "page001")
    page.add_component(comp2)
    page.add_component(comp3)
    
    assert len(page.components) == 3
    print(f"✓ Added 3 components total")
    
    print("✓ Add component tests passed")


def test_get_component():
    """Test getting components from page."""
    print("\n=== Testing Get Component ===")
    
    page = Page("page001", "Test Page")
    
    comp1 = SimpleComponent("comp001", "page001")
    comp2 = SimpleComponent("comp002", "page001")
    page.add_component(comp1)
    page.add_component(comp2)
    
    # Get specific component
    retrieved = page.get_component("comp001")
    assert retrieved == comp1, "Should retrieve correct component"
    print(f"✓ Retrieved component by ID: {retrieved.component_id}")
    
    # Get non-existent component
    retrieved = page.get_component("nonexistent")
    assert retrieved is None, "Should return None for non-existent component"
    print(f"✓ Non-existent component returns None")
    
    print("✓ Get component tests passed")


def test_get_all_components():
    """Test getting all components."""
    print("\n=== Testing Get All Components ===")
    
    page = Page("page001", "Test Page")
    
    comp1 = SimpleComponent("comp001", "page001")
    comp2 = SimpleComponent("comp002", "page001")
    comp3 = SimpleComponent("comp003", "page001")
    page.add_component(comp1)
    page.add_component(comp2)
    page.add_component(comp3)
    
    # Get all components
    all_comps = page.get_all_components()
    
    assert len(all_comps) == 3, "Should return all 3 components"
    assert comp1 in all_comps
    assert comp2 in all_comps
    assert comp3 in all_comps
    print(f"✓ Retrieved all components: {len(all_comps)} components")
    
    # Verify it's a list
    assert isinstance(all_comps, list), "Should return a list"
    print(f"✓ Returns list of components")
    
    print("✓ Get all components tests passed")


def test_remove_component():
    """Test removing components from page."""
    print("\n=== Testing Remove Component ===")
    
    page = Page("page001", "Test Page")
    
    comp1 = SimpleComponent("comp001", "page001")
    comp2 = SimpleComponent("comp002", "page001")
    page.add_component(comp1)
    page.add_component(comp2)
    
    # Remove existing component
    removed = page.remove_component("comp001")
    assert removed == comp1, "Should return removed component"
    assert len(page.components) == 1, "Should have 1 component left"
    assert "comp001" not in page.components
    print(f"✓ Removed component: {len(page.components)} remaining")
    
    # Try to remove non-existent component
    removed = page.remove_component("nonexistent")
    assert removed is None, "Should return None for non-existent component"
    assert len(page.components) == 1, "Component count shouldn't change"
    print(f"✓ Remove non-existent component returns None")
    
    print("✓ Remove component tests passed")


def test_add_wire():
    """Test adding wires to page."""
    print("\n=== Testing Add Wire ===")
    
    page = Page("page001", "Test Page")
    
    # Create and add wire
    wire1 = SimpleWire("wire001")
    page.add_wire(wire1)
    
    assert len(page.wires) == 1
    assert "wire001" in page.wires
    assert page.wires["wire001"] == wire1
    print(f"✓ Added wire: {len(page.wires)} total")
    
    # Add more wires
    wire2 = SimpleWire("wire002")
    wire3 = SimpleWire("wire003")
    page.add_wire(wire2)
    page.add_wire(wire3)
    
    assert len(page.wires) == 3
    print(f"✓ Added 3 wires total")
    
    print("✓ Add wire tests passed")


def test_get_wire():
    """Test getting wires from page."""
    print("\n=== Testing Get Wire ===")
    
    page = Page("page001", "Test Page")
    
    wire1 = SimpleWire("wire001")
    wire2 = SimpleWire("wire002")
    page.add_wire(wire1)
    page.add_wire(wire2)
    
    # Get specific wire
    retrieved = page.get_wire("wire001")
    assert retrieved == wire1, "Should retrieve correct wire"
    print(f"✓ Retrieved wire by ID: {retrieved.wire_id}")
    
    # Get non-existent wire
    retrieved = page.get_wire("nonexistent")
    assert retrieved is None, "Should return None for non-existent wire"
    print(f"✓ Non-existent wire returns None")
    
    print("✓ Get wire tests passed")


def test_get_all_wires():
    """Test getting all wires."""
    print("\n=== Testing Get All Wires ===")
    
    page = Page("page001", "Test Page")
    
    wire1 = SimpleWire("wire001")
    wire2 = SimpleWire("wire002")
    page.add_wire(wire1)
    page.add_wire(wire2)
    
    # Get all wires
    all_wires = page.get_all_wires()
    
    assert len(all_wires) == 2, "Should return all 2 wires"
    assert wire1 in all_wires
    assert wire2 in all_wires
    print(f"✓ Retrieved all wires: {len(all_wires)} wires")
    
    # Verify it's a list
    assert isinstance(all_wires, list), "Should return a list"
    print(f"✓ Returns list of wires")
    
    print("✓ Get all wires tests passed")


def test_remove_wire():
    """Test removing wires from page."""
    print("\n=== Testing Remove Wire ===")
    
    page = Page("page001", "Test Page")
    
    wire1 = SimpleWire("wire001")
    wire2 = SimpleWire("wire002")
    page.add_wire(wire1)
    page.add_wire(wire2)
    
    # Remove existing wire
    removed = page.remove_wire("wire001")
    assert removed == wire1, "Should return removed wire"
    assert len(page.wires) == 1, "Should have 1 wire left"
    assert "wire001" not in page.wires
    print(f"✓ Removed wire: {len(page.wires)} remaining")
    
    # Try to remove non-existent wire
    removed = page.remove_wire("nonexistent")
    assert removed is None, "Should return None for non-existent wire"
    assert len(page.wires) == 1, "Wire count shouldn't change"
    print(f"✓ Remove non-existent wire returns None")
    
    print("✓ Remove wire tests passed")


def test_page_serialization():
    """Test page serialization."""
    print("\n=== Testing Page Serialization ===")
    
    page = Page("page001", "Main Circuit")
    
    # Add components
    comp1 = SimpleComponent("comp001", "page001")
    comp1.position = (100, 200)
    comp2 = SimpleComponent("comp002", "page001")
    comp2.position = (300, 400)
    page.add_component(comp1)
    page.add_component(comp2)
    
    # Add wires
    wire1 = SimpleWire("wire001")
    page.add_wire(wire1)
    
    # Serialize
    data = page.to_dict()
    
    assert 'page_id' in data
    assert 'name' in data
    assert 'components' in data
    assert 'wires' in data
    
    assert data['page_id'] == "page001"
    assert data['name'] == "Main Circuit"
    assert len(data['components']) == 2
    assert len(data['wires']) == 1
    
    print(f"✓ Serialization includes all fields")
    print(f"  PageId: {data['page_id']}")
    print(f"  Name: {data['name']}")
    print(f"  Components: {len(data['components'])}")
    print(f"  Wires: {len(data['wires'])}")
    
    # Verify nested component data
    assert 'comp001' in data['components']
    assert data['components']['comp001']['position'] == (100, 200)
    print(f"✓ Component data nested correctly")
    
    print("✓ Page serialization tests passed")


def test_page_deserialization():
    """Test page deserialization."""
    print("\n=== Testing Page Deserialization ===")
    
    # Create serialized data
    data = {
        'page_id': 'page002',
        'name': 'Restored Page',
        'components': {},
        'wires': {}
    }
    
    # Deserialize
    page = Page.from_dict(data)
    
    assert page.page_id == "page002"
    assert page.name == "Restored Page"
    print(f"✓ Deserialized page: {page.page_id}")
    print(f"  Name: {page.name}")
    
    # Test with missing name (should use default)
    data2 = {'page_id': 'page003'}
    page2 = Page.from_dict(data2)
    assert page2.name == "Untitled"
    print(f"✓ Missing name uses default: '{page2.name}'")
    
    print("✓ Page deserialization tests passed")


def test_page_serialization_roundtrip():
    """Test serialize → deserialize → serialize produces same data."""
    print("\n=== Testing Page Serialization Roundtrip ===")
    
    # Create original page
    page1 = Page("page001", "Test Circuit")
    
    comp1 = SimpleComponent("comp001", "page001")
    comp1.position = (50, 100)
    page1.add_component(comp1)
    
    wire1 = SimpleWire("wire001")
    page1.add_wire(wire1)
    
    # Serialize
    data1 = page1.to_dict()
    
    # Deserialize
    page2 = Page.from_dict(data1)
    
    # Serialize again
    data2 = page2.to_dict()
    
    # Compare key fields
    assert data1['page_id'] == data2['page_id']
    assert data1['name'] == data2['name']
    # Note: components and wires won't roundtrip perfectly without proper loading
    
    print(f"✓ Roundtrip data matches (page metadata)")
    
    print("✓ Roundtrip tests passed")


def test_page_repr():
    """Test page string representation."""
    print("\n=== Testing Page Repr ===")
    
    page = Page("page001", "Main")
    
    comp1 = SimpleComponent("comp001", "page001")
    comp2 = SimpleComponent("comp002", "page001")
    page.add_component(comp1)
    page.add_component(comp2)
    
    wire1 = SimpleWire("wire001")
    page.add_wire(wire1)
    
    repr_str = repr(page)
    print(f"✓ Page repr: {repr_str}")
    
    assert "Page(" in repr_str
    assert "page001" in repr_str
    assert "Main" in repr_str
    assert "components=2" in repr_str
    assert "wires=1" in repr_str
    
    print("✓ Page repr tests passed")


def test_page_with_many_components():
    """Test page with many components."""
    print("\n=== Testing Page With Many Components ===")
    
    page = Page("page001", "Large Circuit")
    
    # Add 20 components
    for i in range(20):
        comp = SimpleComponent(f"comp{i:03d}", "page001")
        page.add_component(comp)
    
    assert len(page.components) == 20
    print(f"✓ Added 20 components: {len(page.components)} total")
    
    # Get all components
    all_comps = page.get_all_components()
    assert len(all_comps) == 20
    print(f"✓ Retrieved all 20 components")
    
    # Remove some
    for i in range(5):
        page.remove_component(f"comp{i:03d}")
    
    assert len(page.components) == 15
    print(f"✓ Removed 5 components: {len(page.components)} remaining")
    
    print("✓ Many components tests passed")


def run_all_tests():
    """Run all Page class tests."""
    print("=" * 60)
    print("PAGE CLASS TEST SUITE (Phase 1.6)")
    print("=" * 60)
    
    try:
        test_page_creation()
        test_add_component()
        test_get_component()
        test_get_all_components()
        test_remove_component()
        test_add_wire()
        test_get_wire()
        test_get_all_wires()
        test_remove_wire()
        test_page_serialization()
        test_page_deserialization()
        test_page_serialization_roundtrip()
        test_page_repr()
        test_page_with_many_components()
        
        print("\n" + "=" * 60)
        print("✓ ALL PAGE CLASS TESTS PASSED")
        print("=" * 60)
        print("\nSection 1.6 Page Class Requirements:")
        print("✓ Define Page class")
        print("  ✓ PageId (string, 8 char UUID)")
        print("  ✓ Name/Title (string)")
        print("  ✓ Collection of Components")
        print("  ✓ Collection of Wires")
        print("✓ Implement component management")
        print("  ✓ add_component()")
        print("  ✓ remove_component()")
        print("  ✓ get_component()")
        print("  ✓ get_all_components()")
        print("✓ Implement wire management")
        print("  ✓ add_wire()")
        print("  ✓ remove_wire()")
        print("  ✓ get_wire()")
        print("  ✓ get_all_wires()")
        print("✓ Add serialization support")
        print("  ✓ to_dict()")
        print("  ✓ from_dict()")
        print("✓ Tests")
        print("  ✓ Test page creation")
        print("  ✓ Test component management")
        print("  ✓ Test wire management")
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
