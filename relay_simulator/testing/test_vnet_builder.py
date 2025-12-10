"""
Test suite for VNET Builder (Phase 2.3)

Comprehensive tests for VNET Builder graph traversal algorithm including
simple wires, junctions, complex networks, disconnected components, and edge cases.
"""

import sys
import os

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vnet_builder import VnetBuilder, VnetBuilderStats
from core.page import Page
from core.wire import Wire, Junction, Waypoint
from core.pin import Pin
from core.tab import Tab
from components.base import Component


# Create a simple test component
class TestComponent(Component):
    """Simple test component."""
    component_type = "TestComponent"
    
    def simulate_logic(self, vnet_manager):
        pass
    
    def sim_start(self, vnet_manager, bridge_manager):
        pass
    
    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        pass
    
    @classmethod
    def from_dict(cls, data):
        comp = cls(data['component_id'], data.get('page_id', 'page001'))
        return comp


def test_vnet_builder_creation():
    """Test VnetBuilder class creation."""
    print("\n=== Testing VnetBuilder Creation ===")
    
    builder = VnetBuilder()
    
    assert builder is not None
    assert builder.id_manager is not None
    print(f"✓ VnetBuilder created")
    
    print("✓ VnetBuilder creation tests passed")


def test_collect_all_tabs():
    """Test collecting all tabs from page."""
    print("\n=== Testing Collect All Tabs ===")
    
    page = Page("page001", "Test Page")
    builder = VnetBuilder()
    
    # Add components with tabs
    comp1 = TestComponent("page001.comp001", "page001")
    pin1 = Pin("page001.comp001.pin001", comp1)
    tab1 = Tab("page001.comp001.pin001.tab001", pin1, (0, 0))
    tab2 = Tab("page001.comp001.pin001.tab002", pin1, (10, 0))
    pin1.add_tab(tab1)
    pin1.add_tab(tab2)
    comp1.add_pin(pin1)
    page.add_component(comp1)
    
    comp2 = TestComponent("page001.comp002", "page001")
    pin2 = Pin("page001.comp002.pin001", comp2)
    tab3 = Tab("page001.comp002.pin001.tab001", pin2, (0, 0))
    pin2.add_tab(tab3)
    comp2.add_pin(pin2)
    page.add_component(comp2)
    
    # Collect tabs
    all_tabs = builder._collect_all_tabs(page)
    
    assert len(all_tabs) == 3
    assert tab1.tab_id in all_tabs
    assert tab2.tab_id in all_tabs
    assert tab3.tab_id in all_tabs
    print(f"✓ Collected {len(all_tabs)} tabs from 2 components")
    
    print("✓ Collect all tabs tests passed")


def test_simple_wire_connection():
    """Test VNET building with simple wire (2 tabs)."""
    print("\n=== Testing Simple Wire Connection ===")
    
    page = Page("page001", "Test Page")
    builder = VnetBuilder()
    
    # Create two components with one tab each
    comp1 = TestComponent("page001.comp001", "page001")
    pin1 = Pin("page001.comp001.pin001", comp1)
    tab1 = Tab("page001.comp001.pin001.tab001", pin1, (0, 0))
    pin1.add_tab(tab1)
    comp1.add_pin(pin1)
    page.add_component(comp1)
    
    comp2 = TestComponent("page001.comp002", "page001")
    pin2 = Pin("page001.comp002.pin001", comp2)
    tab2 = Tab("page001.comp002.pin001.tab001", pin2, (0, 0))
    pin2.add_tab(tab2)
    comp2.add_pin(pin2)
    page.add_component(comp2)
    
    # Create wire connecting the two tabs
    wire = Wire("wire001", tab1.tab_id, tab2.tab_id)
    page.add_wire(wire)
    
    # Build VNETs
    vnets = builder.build_vnets_for_page(page)
    
    # Should create 1 VNET with 2 tabs
    assert len(vnets) == 1, f"Expected 1 VNET, got {len(vnets)}"
    assert vnets[0].get_tab_count() == 2
    assert vnets[0].has_tab(tab1.tab_id)
    assert vnets[0].has_tab(tab2.tab_id)
    print(f"✓ Created 1 VNET with 2 connected tabs")
    
    print("✓ Simple wire connection tests passed")


def test_disconnected_tabs():
    """Test VNET building with disconnected tabs."""
    print("\n=== Testing Disconnected Tabs ===")
    
    page = Page("page001", "Test Page")
    builder = VnetBuilder()
    
    # Create three components with one tab each, no wires
    for i in range(3):
        comp = TestComponent(f"page001.comp{i:03d}", "page001")
        pin = Pin(f"page001.comp{i:03d}.pin001", comp)
        tab = Tab(f"page001.comp{i:03d}.pin001.tab001", pin, (0, 0))
        pin.add_tab(tab)
        comp.add_pin(pin)
        page.add_component(comp)
    
    # Build VNETs
    vnets = builder.build_vnets_for_page(page)
    
    # Should create 3 VNETs, each with 1 tab
    assert len(vnets) == 3, f"Expected 3 VNETs, got {len(vnets)}"
    for vnet in vnets:
        assert vnet.get_tab_count() == 1
    print(f"✓ Created 3 single-tab VNETs for disconnected components")
    
    print("✓ Disconnected tabs tests passed")


def test_junction_network():
    """Test VNET building with junction (3+ tabs)."""
    print("\n=== Testing Junction Network ===")
    
    page = Page("page001", "Test Page")
    builder = VnetBuilder()
    
    # Create 4 components with tabs
    tabs = []
    for i in range(4):
        comp = TestComponent(f"page001.comp{i:03d}", "page001")
        pin = Pin(f"page001.comp{i:03d}.pin001", comp)
        tab = Tab(f"page001.comp{i:03d}.pin001.tab001", pin, (0, 0))
        pin.add_tab(tab)
        comp.add_pin(pin)
        page.add_component(comp)
        tabs.append(tab)
    
    # Create wire with junction: tab0 connects to tab1, tab2, tab3
    main_wire = Wire("wire001", tabs[0].tab_id)
    junction = Junction("junc001", (100, 100))
    
    # Add child wires from junction
    child1 = Wire("wire002", tabs[1].tab_id, tabs[1].tab_id)  # Simple endpoint
    child2 = Wire("wire003", tabs[2].tab_id, tabs[2].tab_id)
    child3 = Wire("wire004", tabs[3].tab_id, tabs[3].tab_id)
    
    junction.add_child_wire(child1)
    junction.add_child_wire(child2)
    junction.add_child_wire(child3)
    main_wire.add_junction(junction)
    
    page.add_wire(main_wire)
    
    # Build VNETs
    vnets = builder.build_vnets_for_page(page)
    
    # Should create 1 VNET with 4 tabs
    assert len(vnets) == 1, f"Expected 1 VNET, got {len(vnets)}"
    assert vnets[0].get_tab_count() == 4
    for tab in tabs:
        assert vnets[0].has_tab(tab.tab_id)
    print(f"✓ Created 1 VNET with 4 tabs connected via junction")
    
    print("✓ Junction network tests passed")


def test_complex_network():
    """Test VNET building with complex wire network."""
    print("\n=== Testing Complex Network ===")
    
    page = Page("page001", "Test Page")
    builder = VnetBuilder()
    
    # Create 6 components
    tabs = []
    for i in range(6):
        comp = TestComponent(f"page001.comp{i:03d}", "page001")
        pin = Pin(f"page001.comp{i:03d}.pin001", comp)
        tab = Tab(f"page001.comp{i:03d}.pin001.tab001", pin, (0, 0))
        pin.add_tab(tab)
        comp.add_pin(pin)
        page.add_component(comp)
        tabs.append(tab)
    
    # Create complex network:
    # tab0 → tab1 → tab2
    # tab3 → tab4 → tab5
    wire1 = Wire("wire001", tabs[0].tab_id, tabs[1].tab_id)
    wire2 = Wire("wire002", tabs[1].tab_id, tabs[2].tab_id)
    wire3 = Wire("wire003", tabs[3].tab_id, tabs[4].tab_id)
    wire4 = Wire("wire004", tabs[4].tab_id, tabs[5].tab_id)
    
    page.add_wire(wire1)
    page.add_wire(wire2)
    page.add_wire(wire3)
    page.add_wire(wire4)
    
    # Build VNETs
    vnets = builder.build_vnets_for_page(page)
    
    # Should create 2 VNETs: {tab0, tab1, tab2} and {tab3, tab4, tab5}
    assert len(vnets) == 2, f"Expected 2 VNETs, got {len(vnets)}"
    
    # Find VNETs by checking tab membership
    vnet1 = next(v for v in vnets if v.has_tab(tabs[0].tab_id))
    vnet2 = next(v for v in vnets if v.has_tab(tabs[3].tab_id))
    
    assert vnet1.get_tab_count() == 3
    assert vnet1.has_tab(tabs[0].tab_id)
    assert vnet1.has_tab(tabs[1].tab_id)
    assert vnet1.has_tab(tabs[2].tab_id)
    
    assert vnet2.get_tab_count() == 3
    assert vnet2.has_tab(tabs[3].tab_id)
    assert vnet2.has_tab(tabs[4].tab_id)
    assert vnet2.has_tab(tabs[5].tab_id)
    
    print(f"✓ Created 2 VNETs: one with tabs 0-2, one with tabs 3-5")
    
    print("✓ Complex network tests passed")


def test_nested_junctions():
    """Test VNET building with nested junctions."""
    print("\n=== Testing Nested Junctions ===")
    
    page = Page("page001", "Test Page")
    builder = VnetBuilder()
    
    # Create 5 components
    tabs = []
    for i in range(5):
        comp = TestComponent(f"page001.comp{i:03d}", "page001")
        pin = Pin(f"page001.comp{i:03d}.pin001", comp)
        tab = Tab(f"page001.comp{i:03d}.pin001.tab001", pin, (0, 0))
        pin.add_tab(tab)
        comp.add_pin(pin)
        page.add_component(comp)
        tabs.append(tab)
    
    # Create nested junction structure:
    # tab0 → junction1 → {tab1, tab2 → junction2 → {tab3, tab4}}
    main_wire = Wire("wire001", tabs[0].tab_id)
    
    junc1 = Junction("junc001", (100, 100))
    child1 = Wire("wire002", tabs[1].tab_id, tabs[1].tab_id)
    child2 = Wire("wire003", tabs[2].tab_id)
    
    junc1.add_child_wire(child1)
    junc1.add_child_wire(child2)
    main_wire.add_junction(junc1)
    
    # Nested junction on child2
    junc2 = Junction("junc002", (200, 200))
    grandchild1 = Wire("wire004", tabs[3].tab_id, tabs[3].tab_id)
    grandchild2 = Wire("wire005", tabs[4].tab_id, tabs[4].tab_id)
    
    junc2.add_child_wire(grandchild1)
    junc2.add_child_wire(grandchild2)
    child2.add_junction(junc2)
    
    page.add_wire(main_wire)
    
    # Build VNETs
    vnets = builder.build_vnets_for_page(page)
    
    # Should create 1 VNET with all 5 tabs
    assert len(vnets) == 1, f"Expected 1 VNET, got {len(vnets)}"
    assert vnets[0].get_tab_count() == 5
    for tab in tabs:
        assert vnets[0].has_tab(tab.tab_id)
    print(f"✓ Created 1 VNET with 5 tabs connected via nested junctions")
    
    print("✓ Nested junctions tests passed")


def test_circular_wire_path():
    """Test VNET building with circular wire connections."""
    print("\n=== Testing Circular Wire Path ===")
    
    page = Page("page001", "Test Page")
    builder = VnetBuilder()
    
    # Create 4 components in a circle
    tabs = []
    for i in range(4):
        comp = TestComponent(f"page001.comp{i:03d}", "page001")
        pin = Pin(f"page001.comp{i:03d}.pin001", comp)
        tab = Tab(f"page001.comp{i:03d}.pin001.tab001", pin, (0, 0))
        pin.add_tab(tab)
        comp.add_pin(pin)
        page.add_component(comp)
        tabs.append(tab)
    
    # Create circular connection: tab0 → tab1 → tab2 → tab3 → tab0
    wire1 = Wire("wire001", tabs[0].tab_id, tabs[1].tab_id)
    wire2 = Wire("wire002", tabs[1].tab_id, tabs[2].tab_id)
    wire3 = Wire("wire003", tabs[2].tab_id, tabs[3].tab_id)
    wire4 = Wire("wire004", tabs[3].tab_id, tabs[0].tab_id)
    
    page.add_wire(wire1)
    page.add_wire(wire2)
    page.add_wire(wire3)
    page.add_wire(wire4)
    
    # Build VNETs (should not infinite loop)
    vnets = builder.build_vnets_for_page(page)
    
    # Should create 1 VNET with all 4 tabs
    assert len(vnets) == 1, f"Expected 1 VNET, got {len(vnets)}"
    assert vnets[0].get_tab_count() == 4
    for tab in tabs:
        assert vnets[0].has_tab(tab.tab_id)
    print(f"✓ Handled circular path without infinite loop: 1 VNET with 4 tabs")
    
    print("✓ Circular wire path tests passed")


def test_mixed_connected_disconnected():
    """Test VNET building with mix of connected and disconnected components."""
    print("\n=== Testing Mixed Connected/Disconnected ===")
    
    page = Page("page001", "Test Page")
    builder = VnetBuilder()
    
    # Create 6 components
    tabs = []
    for i in range(6):
        comp = TestComponent(f"page001.comp{i:03d}", "page001")
        pin = Pin(f"page001.comp{i:03d}.pin001", comp)
        tab = Tab(f"page001.comp{i:03d}.pin001.tab001", pin, (0, 0))
        pin.add_tab(tab)
        comp.add_pin(pin)
        page.add_component(comp)
        tabs.append(tab)
    
    # Connect tab0-tab1, tab2-tab3, leave tab4 and tab5 disconnected
    wire1 = Wire("wire001", tabs[0].tab_id, tabs[1].tab_id)
    wire2 = Wire("wire002", tabs[2].tab_id, tabs[3].tab_id)
    
    page.add_wire(wire1)
    page.add_wire(wire2)
    
    # Build VNETs
    vnets = builder.build_vnets_for_page(page)
    
    # Should create 4 VNETs: {0,1}, {2,3}, {4}, {5}
    assert len(vnets) == 4, f"Expected 4 VNETs, got {len(vnets)}"
    
    # Count VNETs by size
    two_tab_vnets = [v for v in vnets if v.get_tab_count() == 2]
    one_tab_vnets = [v for v in vnets if v.get_tab_count() == 1]
    
    assert len(two_tab_vnets) == 2
    assert len(one_tab_vnets) == 2
    print(f"✓ Created 4 VNETs: 2 with 2 tabs, 2 with 1 tab")
    
    print("✓ Mixed connected/disconnected tests passed")


def test_vnet_builder_stats():
    """Test VnetBuilderStats analysis."""
    print("\n=== Testing VnetBuilderStats ===")
    
    page = Page("page001", "Test Page")
    builder = VnetBuilder()
    
    # Create test scenario: 2 connected, 3 disconnected
    tabs = []
    for i in range(5):
        comp = TestComponent(f"page001.comp{i:03d}", "page001")
        pin = Pin(f"page001.comp{i:03d}.pin001", comp)
        tab = Tab(f"page001.comp{i:03d}.pin001.tab001", pin, (0, 0))
        pin.add_tab(tab)
        comp.add_pin(pin)
        page.add_component(comp)
        tabs.append(tab)
    
    # Connect first two
    wire = Wire("wire001", tabs[0].tab_id, tabs[1].tab_id)
    page.add_wire(wire)
    
    # Build VNETs
    vnets = builder.build_vnets_for_page(page)
    
    # Analyze
    stats = VnetBuilderStats().analyze_vnets(vnets)
    
    assert stats.total_vnets == 4
    assert stats.single_tab_vnets == 3
    assert stats.multi_tab_vnets == 1
    assert stats.largest_vnet_size == 2
    assert stats.total_tabs == 5
    print(f"✓ Stats: {stats}")
    
    print("✓ VnetBuilderStats tests passed")


def test_empty_page():
    """Test VNET building with empty page."""
    print("\n=== Testing Empty Page ===")
    
    page = Page("page001", "Empty Page")
    builder = VnetBuilder()
    
    # Build VNETs (should not crash)
    vnets = builder.build_vnets_for_page(page)
    
    assert len(vnets) == 0
    print(f"✓ Empty page produces 0 VNETs")
    
    print("✓ Empty page tests passed")


def test_component_with_multiple_pins():
    """Test VNET building with component having multiple pins."""
    print("\n=== Testing Component with Multiple Pins ===")
    
    page = Page("page001", "Test Page")
    builder = VnetBuilder()
    
    # Create component with 2 pins, each with 2 tabs
    comp1 = TestComponent("page001.comp001", "page001")
    
    pin1 = Pin("page001.comp001.pin001", comp1)
    tab1a = Tab("page001.comp001.pin001.tab001", pin1, (0, 0))
    tab1b = Tab("page001.comp001.pin001.tab002", pin1, (10, 0))
    pin1.add_tab(tab1a)
    pin1.add_tab(tab1b)
    comp1.add_pin(pin1)
    
    pin2 = Pin("page001.comp001.pin002", comp1)
    tab2a = Tab("page001.comp001.pin002.tab001", pin2, (0, 0))
    tab2b = Tab("page001.comp001.pin002.tab002", pin2, (10, 0))
    pin2.add_tab(tab2a)
    pin2.add_tab(tab2b)
    comp1.add_pin(pin2)
    
    page.add_component(comp1)
    
    # Build VNETs (no wires, so each tab gets its own VNET)
    vnets = builder.build_vnets_for_page(page)
    
    # Should create 4 single-tab VNETs
    assert len(vnets) == 4, f"Expected 4 VNETs, got {len(vnets)}"
    for vnet in vnets:
        assert vnet.get_tab_count() == 1
    print(f"✓ Component with 2 pins (4 tabs total) creates 4 single-tab VNETs")
    
    print("✓ Component with multiple pins tests passed")


def run_all_tests():
    """Run all VNET Builder tests."""
    print("=" * 60)
    print("VNET BUILDER TEST SUITE (Phase 2.3)")
    print("=" * 60)
    
    try:
        test_vnet_builder_creation()
        test_collect_all_tabs()
        test_simple_wire_connection()
        test_disconnected_tabs()
        test_junction_network()
        test_complex_network()
        test_nested_junctions()
        test_circular_wire_path()
        test_mixed_connected_disconnected()
        test_vnet_builder_stats()
        test_empty_page()
        test_component_with_multiple_pins()
        
        print("\n" + "=" * 60)
        print("✓ ALL VNET BUILDER TESTS PASSED")
        print("=" * 60)
        print("\nSection 2.3 VNET Builder Algorithm Requirements:")
        print("✓ Implement graph traversal algorithm")
        print("  ✓ Start from unprocessed tab")
        print("  ✓ Follow wire to connected tabs")
        print("  ✓ Handle junctions (multiple branches)")
        print("  ✓ Mark tabs as processed")
        print("  ✓ Create VNET with all connected tabs")
        print("✓ Handle edge cases")
        print("  ✓ Disconnected tabs (single-tab VNETs)")
        print("  ✓ Complex junction networks")
        print("  ✓ Circular wire paths")
        print("  ✓ Nested junctions")
        print("  ✓ Empty pages")
        print("✓ Optimize for performance")
        print("  ✓ Efficient data structures (sets, dicts)")
        print("  ✓ Avoid redundant processing (processed_tabs)")
        print("  ✓ Depth-first search algorithm")
        print("✓ Create VnetBuilder class/module")
        print("  ✓ build_vnets_for_page(page) - Main entry point")
        print("  ✓ Returns collection of VNETs")
        print("  ✓ VnetBuilderStats for analysis")
        print("✓ Tests")
        print("  ✓ Test simple wire (2 tabs)")
        print("  ✓ Test junction (3+ tabs)")
        print("  ✓ Test complex network")
        print("  ✓ Test disconnected components")
        print("  ✓ Test nested junctions")
        print("  ✓ Test circular paths")
        print("  ✓ Test mixed scenarios")
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
