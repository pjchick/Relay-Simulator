"""
Test suite for Link Resolution System (Phase 2.4)

Comprehensive tests for LinkResolver including same-page links, cross-page links,
multiple components with same link name, and link validation.
"""

import sys
import os

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.link_resolver import LinkResolver, LinkValidator, LinkResolutionResult
from core.document import Document
from core.page import Page
from core.vnet import VNET
from core.vnet_builder import VnetBuilder
from core.wire import Wire
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


def test_link_resolver_creation():
    """Test LinkResolver class creation."""
    print("\n=== Testing LinkResolver Creation ===")
    
    resolver = LinkResolver()
    
    assert resolver is not None
    print(f"✓ LinkResolver created")
    
    print("✓ LinkResolver creation tests passed")


def test_no_links():
    """Test link resolution with no link names."""
    print("\n=== Testing No Links ===")
    
    doc = Document()
    page = doc.create_page("Test Page")
    
    # Create component without link name
    comp = TestComponent("comp001", page.page_id)
    pin = Pin("pin001", comp)
    tab = Tab("tab001", pin, (0, 0))
    pin.add_tab(tab)
    comp.add_pin(pin)
    page.add_component(comp)
    
    # Build VNETs
    builder = VnetBuilder()
    vnets = builder.build_vnets_for_page(page)
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, vnets)
    
    assert result.total_links == 0
    assert result.resolved_links == 0
    assert len(result.unresolved_links) == 0
    print(f"✓ No links to resolve: {result}")
    
    print("✓ No links tests passed")


def test_same_page_link():
    """Test link resolution on same page."""
    print("\n=== Testing Same-Page Link ===")
    
    doc = Document()
    page = doc.create_page("Test Page")
    
    # Create two components with same link name
    comp1 = TestComponent("comp001", page.page_id)
    comp1.link_name = "POWER"
    pin1 = Pin("pin001", comp1)
    tab1 = Tab("tab001", pin1, (0, 0))
    pin1.add_tab(tab1)
    comp1.add_pin(pin1)
    page.add_component(comp1)
    
    comp2 = TestComponent("comp002", page.page_id)
    comp2.link_name = "POWER"
    pin2 = Pin("pin002", comp2)
    tab2 = Tab("tab002", pin2, (0, 0))
    pin2.add_tab(tab2)
    comp2.add_pin(pin2)
    page.add_component(comp2)
    
    # Build VNETs (no wires, so 2 separate VNETs)
    builder = VnetBuilder()
    vnets = builder.build_vnets_for_page(page)
    
    assert len(vnets) == 2, f"Expected 2 VNETs, got {len(vnets)}"
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, vnets)
    
    assert result.total_links == 1
    assert result.resolved_links == 1
    assert result.same_page_links == 1
    assert result.cross_page_links == 0
    assert result.vnets_with_links == 2
    
    # Both VNETs should have "POWER" link
    for vnet in vnets:
        assert vnet.has_link("POWER")
    
    print(f"✓ Same-page link resolved: {result}")
    print(f"✓ Both VNETs have 'POWER' link")
    
    print("✓ Same-page link tests passed")


def test_cross_page_link():
    """Test link resolution across pages."""
    print("\n=== Testing Cross-Page Link ===")
    
    doc = Document()
    page1 = doc.create_page("Page 1")
    page2 = doc.create_page("Page 2")
    
    # Component on page 1 with link name
    comp1 = TestComponent("comp001", page1.page_id)
    comp1.link_name = "SIGNAL_A"
    pin1 = Pin("pin001", comp1)
    tab1 = Tab("tab001", pin1, (0, 0))
    pin1.add_tab(tab1)
    comp1.add_pin(pin1)
    page1.add_component(comp1)
    
    # Component on page 2 with same link name
    comp2 = TestComponent("comp002", page2.page_id)
    comp2.link_name = "SIGNAL_A"
    pin2 = Pin("pin002", comp2)
    tab2 = Tab("tab002", pin2, (0, 0))
    pin2.add_tab(tab2)
    comp2.add_pin(pin2)
    page2.add_component(comp2)
    
    # Build VNETs for both pages
    builder = VnetBuilder()
    vnets1 = builder.build_vnets_for_page(page1)
    vnets2 = builder.build_vnets_for_page(page2)
    all_vnets = vnets1 + vnets2
    
    assert len(all_vnets) == 2
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, all_vnets)
    
    assert result.total_links == 1
    assert result.resolved_links == 1
    assert result.cross_page_links == 1
    assert result.same_page_links == 0
    assert result.vnets_with_links == 2
    
    # Both VNETs should have "SIGNAL_A" link
    for vnet in all_vnets:
        assert vnet.has_link("SIGNAL_A")
    
    print(f"✓ Cross-page link resolved: {result}")
    print(f"✓ VNETs on different pages both have 'SIGNAL_A' link")
    
    print("✓ Cross-page link tests passed")


def test_multiple_components_same_link():
    """Test multiple components with same link name."""
    print("\n=== Testing Multiple Components Same Link ===")
    
    doc = Document()
    page = doc.create_page("Test Page")
    
    # Create 3 components with same link name
    for i in range(3):
        comp = TestComponent(f"comp{i:03d}", page.page_id)
        comp.link_name = "GROUND"
        pin = Pin(f"pin{i:03d}", comp)
        tab = Tab(f"tab{i:03d}", pin, (0, 0))
        pin.add_tab(tab)
        comp.add_pin(pin)
        page.add_component(comp)
    
    # Build VNETs (3 separate VNETs)
    builder = VnetBuilder()
    vnets = builder.build_vnets_for_page(page)
    
    assert len(vnets) == 3
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, vnets)
    
    assert result.total_links == 1
    assert result.resolved_links == 1
    assert result.vnets_with_links == 3
    
    # All 3 VNETs should have "GROUND" link
    for vnet in vnets:
        assert vnet.has_link("GROUND")
    
    print(f"✓ Multiple components resolved: {result}")
    print(f"✓ All 3 VNETs have 'GROUND' link")
    
    print("✓ Multiple components same link tests passed")


def test_multiple_links():
    """Test multiple different link names."""
    print("\n=== Testing Multiple Links ===")
    
    doc = Document()
    page = doc.create_page("Test Page")
    
    # Create components with different link names
    comp1 = TestComponent("comp001", page.page_id)
    comp1.link_name = "POWER"
    pin1 = Pin("pin001", comp1)
    tab1 = Tab("tab001", pin1, (0, 0))
    pin1.add_tab(tab1)
    comp1.add_pin(pin1)
    page.add_component(comp1)
    
    comp2 = TestComponent("comp002", page.page_id)
    comp2.link_name = "POWER"
    pin2 = Pin("pin002", comp2)
    tab2 = Tab("tab002", pin2, (0, 0))
    pin2.add_tab(tab2)
    comp2.add_pin(pin2)
    page.add_component(comp2)
    
    comp3 = TestComponent("comp003", page.page_id)
    comp3.link_name = "GROUND"
    pin3 = Pin("pin003", comp3)
    tab3 = Tab("tab003", pin3, (0, 0))
    pin3.add_tab(tab3)
    comp3.add_pin(pin3)
    page.add_component(comp3)
    
    comp4 = TestComponent("comp004", page.page_id)
    comp4.link_name = "GROUND"
    pin4 = Pin("pin004", comp4)
    tab4 = Tab("tab004", pin4, (0, 0))
    pin4.add_tab(tab4)
    comp4.add_pin(pin4)
    page.add_component(comp4)
    
    # Build VNETs
    builder = VnetBuilder()
    vnets = builder.build_vnets_for_page(page)
    
    assert len(vnets) == 4
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, vnets)
    
    assert result.total_links == 2  # POWER and GROUND
    assert result.resolved_links == 2
    assert result.vnets_with_links == 4
    
    # Check which VNETs have which links
    power_vnets = [v for v in vnets if v.has_link("POWER")]
    ground_vnets = [v for v in vnets if v.has_link("GROUND")]
    
    assert len(power_vnets) == 2
    assert len(ground_vnets) == 2
    
    print(f"✓ Multiple links resolved: {result}")
    print(f"✓ 2 VNETs have 'POWER', 2 have 'GROUND'")
    
    print("✓ Multiple links tests passed")


def test_component_with_no_tabs():
    """Test component with link name but no tabs (edge case)."""
    print("\n=== Testing Component With No Tabs ===")
    
    doc = Document()
    page = doc.create_page("Test Page")
    
    # Create component with link name but no tabs
    comp = TestComponent("comp001", page.page_id)
    comp.link_name = "ORPHAN"
    # No pins/tabs added
    page.add_component(comp)
    
    # Build VNETs (empty)
    builder = VnetBuilder()
    vnets = builder.build_vnets_for_page(page)
    
    assert len(vnets) == 0
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, vnets)
    
    assert result.total_links == 1
    assert result.resolved_links == 0
    assert len(result.unresolved_links) == 1
    assert "ORPHAN" in result.unresolved_links
    assert len(result.errors) > 0
    
    print(f"✓ Component with no tabs detected: {result}")
    print(f"✓ Error: {result.errors[0]}")
    
    print("✓ Component with no tabs tests passed")


def test_single_component_link_warning():
    """Test warning for link with only one component."""
    print("\n=== Testing Single Component Link Warning ===")
    
    doc = Document()
    page = doc.create_page("Test Page")
    
    # Create single component with link name
    comp = TestComponent("comp001", page.page_id)
    comp.link_name = "LONELY"
    pin = Pin("pin001", comp)
    tab = Tab("tab001", pin, (0, 0))
    pin.add_tab(tab)
    comp.add_pin(pin)
    page.add_component(comp)
    
    # Build VNETs
    builder = VnetBuilder()
    vnets = builder.build_vnets_for_page(page)
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, vnets)
    
    assert result.total_links == 1
    assert result.resolved_links == 1
    assert len(result.warnings) > 0
    
    # Check for single-component warning
    assert any("only one component" in w for w in result.warnings)
    
    print(f"✓ Single component link warning: {result}")
    print(f"✓ Warning: {result.warnings[0]}")
    
    print("✓ Single component link warning tests passed")


def test_linked_components_with_wire():
    """Test link resolution when linked components are also wired together."""
    print("\n=== Testing Linked Components With Wire ===")
    
    doc = Document()
    page = doc.create_page("Test Page")
    
    # Create two components with same link name AND wire them together
    comp1 = TestComponent("comp001", page.page_id)
    comp1.link_name = "SHARED"
    pin1 = Pin("pin001", comp1)
    tab1 = Tab("tab001", pin1, (0, 0))
    pin1.add_tab(tab1)
    comp1.add_pin(pin1)
    page.add_component(comp1)
    
    comp2 = TestComponent("comp002", page.page_id)
    comp2.link_name = "SHARED"
    pin2 = Pin("pin002", comp2)
    tab2 = Tab("tab002", pin2, (0, 0))
    pin2.add_tab(tab2)
    comp2.add_pin(pin2)
    page.add_component(comp2)
    
    # Wire them together
    wire = Wire("wire001", tab1.tab_id, tab2.tab_id)
    page.add_wire(wire)
    
    # Build VNETs (should be 1 VNET with both tabs)
    builder = VnetBuilder()
    vnets = builder.build_vnets_for_page(page)
    
    assert len(vnets) == 1
    assert vnets[0].get_tab_count() == 2
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, vnets)
    
    assert result.total_links == 1
    assert result.resolved_links == 1
    assert result.vnets_with_links == 1
    
    # The single VNET should have "SHARED" link
    assert vnets[0].has_link("SHARED")
    
    print(f"✓ Wired linked components resolved: {result}")
    print(f"✓ Single VNET has both tabs and 'SHARED' link")
    
    print("✓ Linked components with wire tests passed")


def test_link_validator_statistics():
    """Test LinkValidator statistics."""
    print("\n=== Testing LinkValidator Statistics ===")
    
    doc = Document()
    page = doc.create_page("Test Page")
    
    # Create components with link names
    for i in range(3):
        comp = TestComponent(f"comp{i:03d}", page.page_id)
        comp.link_name = "POWER" if i < 2 else "GROUND"
        pin = Pin(f"pin{i:03d}", comp)
        tab = Tab(f"tab{i:03d}", pin, (0, 0))
        pin.add_tab(tab)
        comp.add_pin(pin)
        page.add_component(comp)
    
    # Get statistics
    stats = LinkValidator.get_link_statistics(doc)
    
    assert stats['total_components_with_links'] == 3
    assert stats['unique_link_names'] == 2
    assert stats['link_usage']['POWER'] == 2
    assert stats['link_usage']['GROUND'] == 1
    
    print(f"✓ Link statistics: {stats}")
    
    print("✓ LinkValidator statistics tests passed")


def test_link_validator_unconnected():
    """Test LinkValidator finding unconnected links."""
    print("\n=== Testing LinkValidator Unconnected Links ===")
    
    doc = Document()
    page = doc.create_page("Test Page")
    
    # Create component with link name but no tabs
    comp = TestComponent("comp001", page.page_id)
    comp.link_name = "ORPHAN"
    page.add_component(comp)
    
    # Build VNETs
    builder = VnetBuilder()
    vnets = builder.build_vnets_for_page(page)
    
    # Find unconnected links
    unconnected = LinkValidator.find_unconnected_links(doc, vnets)
    
    assert len(unconnected) == 1
    assert "ORPHAN" in unconnected
    
    print(f"✓ Unconnected links: {unconnected}")
    
    print("✓ LinkValidator unconnected links tests passed")


def test_complex_cross_page_scenario():
    """Test complex scenario with multiple pages and link names."""
    print("\n=== Testing Complex Cross-Page Scenario ===")
    
    doc = Document()
    page1 = doc.create_page("Page 1")
    page2 = doc.create_page("Page 2")
    page3 = doc.create_page("Page 3")
    
    # Page 1: POWER and GROUND
    comp1a = TestComponent("comp1a", page1.page_id)
    comp1a.link_name = "POWER"
    pin1a = Pin("pin1a", comp1a)
    tab1a = Tab("tab1a", pin1a, (0, 0))
    pin1a.add_tab(tab1a)
    comp1a.add_pin(pin1a)
    page1.add_component(comp1a)
    
    comp1b = TestComponent("comp1b", page1.page_id)
    comp1b.link_name = "GROUND"
    pin1b = Pin("pin1b", comp1b)
    tab1b = Tab("tab1b", pin1b, (0, 0))
    pin1b.add_tab(tab1b)
    comp1b.add_pin(pin1b)
    page1.add_component(comp1b)
    
    # Page 2: POWER and SIGNAL
    comp2a = TestComponent("comp2a", page2.page_id)
    comp2a.link_name = "POWER"
    pin2a = Pin("pin2a", comp2a)
    tab2a = Tab("tab2a", pin2a, (0, 0))
    pin2a.add_tab(tab2a)
    comp2a.add_pin(pin2a)
    page2.add_component(comp2a)
    
    comp2b = TestComponent("comp2b", page2.page_id)
    comp2b.link_name = "SIGNAL"
    pin2b = Pin("pin2b", comp2b)
    tab2b = Tab("tab2b", pin2b, (0, 0))
    pin2b.add_tab(tab2b)
    comp2b.add_pin(pin2b)
    page2.add_component(comp2b)
    
    # Page 3: GROUND and SIGNAL
    comp3a = TestComponent("comp3a", page3.page_id)
    comp3a.link_name = "GROUND"
    pin3a = Pin("pin3a", comp3a)
    tab3a = Tab("tab3a", pin3a, (0, 0))
    pin3a.add_tab(tab3a)
    comp3a.add_pin(pin3a)
    page3.add_component(comp3a)
    
    comp3b = TestComponent("comp3b", page3.page_id)
    comp3b.link_name = "SIGNAL"
    pin3b = Pin("pin3b", comp3b)
    tab3b = Tab("tab3b", pin3b, (0, 0))
    pin3b.add_tab(tab3b)
    comp3b.add_pin(pin3b)
    page3.add_component(comp3b)
    
    # Build VNETs for all pages
    builder = VnetBuilder()
    vnets1 = builder.build_vnets_for_page(page1)
    vnets2 = builder.build_vnets_for_page(page2)
    vnets3 = builder.build_vnets_for_page(page3)
    all_vnets = vnets1 + vnets2 + vnets3
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, all_vnets)
    
    assert result.total_links == 3  # POWER, GROUND, SIGNAL
    assert result.resolved_links == 3
    assert result.cross_page_links == 3
    assert result.vnets_with_links == 6
    
    # Check link distribution
    power_vnets = [v for v in all_vnets if v.has_link("POWER")]
    ground_vnets = [v for v in all_vnets if v.has_link("GROUND")]
    signal_vnets = [v for v in all_vnets if v.has_link("SIGNAL")]
    
    assert len(power_vnets) == 2  # page1 and page2
    assert len(ground_vnets) == 2  # page1 and page3
    assert len(signal_vnets) == 2  # page2 and page3
    
    print(f"✓ Complex cross-page scenario: {result}")
    print(f"✓ POWER: 2 VNETs, GROUND: 2 VNETs, SIGNAL: 2 VNETs")
    
    print("✓ Complex cross-page scenario tests passed")


def run_all_tests():
    """Run all Link Resolver tests."""
    print("=" * 60)
    print("LINK RESOLUTION SYSTEM TEST SUITE (Phase 2.4)")
    print("=" * 60)
    
    try:
        test_link_resolver_creation()
        test_no_links()
        test_same_page_link()
        test_cross_page_link()
        test_multiple_components_same_link()
        test_multiple_links()
        test_component_with_no_tabs()
        test_single_component_link_warning()
        test_linked_components_with_wire()
        test_link_validator_statistics()
        test_link_validator_unconnected()
        test_complex_cross_page_scenario()
        
        print("\n" + "=" * 60)
        print("✓ ALL LINK RESOLVER TESTS PASSED")
        print("=" * 60)
        print("\nSection 2.4 Link Resolution System Requirements:")
        print("✓ Implement link resolver")
        print("  ✓ Scan all components for LinkName property")
        print("  ✓ Build link name → components map")
        print("  ✓ Find VNETs containing linked component tabs")
        print("  ✓ Add link name to those VNETs")
        print("✓ Create LinkResolver class")
        print("  ✓ resolve_links(document, vnets) - Main entry point")
        print("  ✓ Returns LinkResolutionResult with statistics")
        print("✓ Handle cross-page links")
        print("  ✓ Link VNETs from different pages")
        print("  ✓ Track cross-page vs same-page links")
        print("✓ Validate links")
        print("  ✓ Warn about unconnected links")
        print("  ✓ Warn about single-component links")
        print("  ✓ Error on links with no VNETs")
        print("✓ LinkValidator utilities")
        print("  ✓ get_link_statistics()")
        print("  ✓ find_unconnected_links()")
        print("✓ Tests")
        print("  ✓ Test same-page links")
        print("  ✓ Test cross-page links")
        print("  ✓ Test multiple components same link name")
        print("  ✓ Test unconnected links")
        print("  ✓ Test validation warnings/errors")
        print("  ✓ Test complex multi-page scenarios")
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
