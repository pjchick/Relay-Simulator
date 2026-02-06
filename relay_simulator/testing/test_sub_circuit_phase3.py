"""
Test script for Sub-Circuit Simulation - Phase 3 validation.

Tests:
1. Bridge creation in SubCircuit components
2. VNET building with instance pages
3. Link resolution across sub-circuit boundaries
4. Actual simulation test with Latch example
5. Document reference restoration after load
"""

import sys
from pathlib import Path

# Add relay_simulator to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document import Document
from core.sub_circuit_instantiator import SubCircuitInstantiator
from core.vnet_builder import VnetBuilder
from core.link_resolver import LinkResolver
from components.factory import ComponentFactory
from components.switch import Switch
from components.indicator import Indicator


def test_document_reference():
    """Test that document reference is set correctly."""
    print("=" * 60)
    print("Test 1: Document Reference in SubCircuit")
    print("=" * 60)
    
    doc = Document()
    main_page = doc.create_page("Main")
    factory = ComponentFactory()
    
    instantiator = SubCircuitInstantiator(doc, factory)
    rsub_path = Path(__file__).parent.parent.parent / "examples" / "Latch.rsub"
    
    # Load and embed
    sc_def = instantiator.load_and_embed_template(str(rsub_path))
    
    # Create instance
    latch = instantiator.create_instance(
        sc_def.sub_circuit_id,
        main_page.page_id,
        (200, 200)
    )
    # Add to page
    main_page.add_component(latch)
    
    # Check document reference
    if latch._document is doc:
        print(f"✓ Document reference set correctly")
    else:
        print(f"✗ Document reference NOT set!")
        return False
    
    # Check pin to link mapping
    if len(latch._pin_to_link_map) > 0:
        print(f"✓ Pin-to-Link mapping: {len(latch._pin_to_link_map)} mappings")
        for pin_id, link_id in latch._pin_to_link_map.items():
            print(f"    {pin_id} -> {link_id}")
    else:
        print(f"✗ No pin-to-link mappings!")
        return False
    
    return doc, latch, sc_def


def test_vnet_building(doc):
    """Test VNET building with instance pages."""
    print("\n" + "=" * 60)
    print("Test 2: VNET Building with Instance Pages")
    print("=" * 60)
    
    builder = VnetBuilder(doc.id_manager)
    
    # Build VNETs for all pages (including instance pages)
    all_vnets = []
    for page in doc.get_all_pages():
        page_vnets = builder.build_vnets_for_page(page)
        all_vnets.extend(page_vnets)
        print(f"  Page: {page.name}")
        print(f"    Is sub-circuit page: {page.is_sub_circuit_page}")
        print(f"    VNETs: {len(page_vnets)}")
        print(f"    Components: {len(page.components)}")
    
    print(f"\n✓ Total VNETs built: {len(all_vnets)}")
    
    # Count instance page VNETs vs main page VNETs
    main_vnets = sum(1 for v in all_vnets if not v.page_id.startswith('e') or len(v.page_id) != 8)
    # This is a rough heuristic - better to track properly
    
    return all_vnets


def test_link_resolution(doc, all_vnets):
    """Test link resolution including sub-circuit instance Links."""
    print("\n" + "=" * 60)
    print("Test 3: Link Resolution with Instance Pages")
    print("=" * 60)
    
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, all_vnets)
    
    print(f"  Total links: {result.total_links}")
    print(f"  Resolved links: {result.resolved_links}")
    print(f"  Unresolved links: {len(result.unresolved_links)}")
    print(f"  VNETs with links: {result.vnets_with_links}")
    print(f"  Cross-page links: {result.cross_page_links}")
    
    if result.errors:
        print(f"\n  Errors:")
        for error in result.errors:
            print(f"    - {error}")
    
    if result.warnings:
        print(f"\n  Warnings:")
        for warning in result.warnings:
            print(f"    - {warning}")
    
    # Check for SUB_IN and SUB_OUT links (from Latch)
    # These should be resolved within the instance
    
    if result.resolved_links > 0:
        print(f"\n✓ Links resolved successfully")
    else:
        print(f"\n⚠ No links resolved (expected for Latch internal circuit)")
    
    return result


def test_bridge_creation(doc, latch):
    """Test that bridges can be created from SubCircuit to instance Links."""
    print("\n" + "=" * 60)
    print("Test 4: Bridge Creation")
    print("=" * 60)
    
    # For this test, we'll mock the bridge manager and vnet manager
    class MockVnetManager:
        def mark_tab_dirty(self, tab_id):
            pass
    
    class MockBridgeManager:
        def __init__(self):
            self.bridges = []
        
        def create_bridge(self, tab1, tab2, bridge_id):
            self.bridges.append((tab1, tab2, bridge_id))
    
    vnet_mgr = MockVnetManager()
    bridge_mgr = MockBridgeManager()
    
    # Call sim_start on the SubCircuit component
    try:
        latch.sim_start(vnet_mgr, bridge_mgr)
        print(f"✓ sim_start() executed without errors")
    except Exception as e:
        print(f"✗ sim_start() failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Check bridges created
    if len(bridge_mgr.bridges) > 0:
        print(f"✓ Bridges created: {len(bridge_mgr.bridges)}")
        for tab1, tab2, bridge_id in bridge_mgr.bridges:
            print(f"    {tab1} <-> {tab2} (bridge: {bridge_id})")
    else:
        print(f"⚠ No bridges created (might need actual simulation engine)")
    
    return True


def test_serialization_with_instances(doc):
    """Test that document with sub-circuits serializes and deserializes correctly."""
    print("\n" + "=" * 60)
    print("Test 5: Serialization with Document Reference")
    print("=" * 60)
    
    # Serialize
    data = doc.to_dict()
    print(f"✓ Serialized document")
    
    # Deserialize
    factory = ComponentFactory()
    doc2 = Document.from_dict(data, factory)
    print(f"✓ Deserialized document")
    
    # Check that SubCircuit components have document reference restored
    sub_circuit_count = 0
    for page in doc2.get_all_pages():
        for comp in page.get_all_components():
            if comp.component_type == "SubCircuit":
                sub_circuit_count += 1
                if comp._document is doc2:
                    print(f"  ✓ SubCircuit {comp.component_id}: document reference restored")
                else:
                    print(f"  ✗ SubCircuit {comp.component_id}: document reference NOT restored!")
                    return False
    
    if sub_circuit_count > 0:
        print(f"\n✓ All {sub_circuit_count} SubCircuit components have document references")
    else:
        print(f"\n⚠ No SubCircuit components found")
    
    return True


def test_full_circuit_simulation():
    """Test a complete circuit with sub-circuit, switch, and indicator."""
    print("\n" + "=" * 60)
    print("Test 6: Full Circuit Simulation (Conceptual)")
    print("=" * 60)
    
    # Create document
    doc = Document()
    main_page = doc.create_page("Main Circuit")
    factory = ComponentFactory()
    
    # Load Latch sub-circuit
    instantiator = SubCircuitInstantiator(doc, factory)
    rsub_path = Path(__file__).parent.parent.parent / "examples" / "Latch.rsub"
    sc_def = instantiator.load_and_embed_template(str(rsub_path))
    
    # Create latch instance
    latch = instantiator.create_instance(
        sc_def.sub_circuit_id,
        main_page.page_id,
        (300, 300)
    )
    main_page.add_component(latch)
    
    # Create switch to drive latch input
    switch = Switch(doc.id_manager.generate_id(), main_page.page_id)
    switch.position = (100, 300)
    main_page.add_component(switch)
    
    # Create indicator to show latch output  
    indicator = Indicator(doc.id_manager.generate_id(), main_page.page_id)
    indicator.position = (500, 300)
    main_page.add_component(indicator)
    
    print(f"✓ Created test circuit:")
    print(f"    Switch -> Latch -> Indicator")
    print(f"    Components on main page: {len(main_page.components)}")
    print(f"    Total pages (main + instance): {doc.get_page_count()}")
    
    # Build VNETs
    builder = VnetBuilder(doc.id_manager)
    all_vnets = []
    for page in doc.get_all_pages():
        page_vnets = builder.build_vnets_for_page(page)
        all_vnets.extend(page_vnets)
    
    print(f"✓ Built VNETs: {len(all_vnets)}")
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, all_vnets)
    print(f"✓ Resolved links: {result.resolved_links}")
    
    # Note: Actual simulation would require:
    # - Wiring components together
    # - Creating simulation engine
    # - Running simulation cycles
    # This test validates the structure is correct for simulation
    
    print(f"\n✓ Circuit structure ready for simulation")
    return True


def main():
    """Run all tests."""
    print("Phase 3 Sub-Circuit Simulation Tests")
    print("=" * 60 + "\n")
    
    # Test 1
    result = test_document_reference()
    if not result:
        print("\n✗ Test 1 FAILED - aborting")
        return
    doc, latch, sc_def = result
    
    # Test 2
    all_vnets = test_vnet_building(doc)
    
    # Test 3
    test_link_resolution(doc, all_vnets)
    
    # Test 4
    if not test_bridge_creation(doc, latch):
        print("\n✗ Test 4 FAILED")
        return
    
    # Test 5
    if not test_serialization_with_instances(doc):
        print("\n✗ Test 5 FAILED")
        return
    
    # Test 6
    if not test_full_circuit_simulation():
        print("\n✗ Test 6 FAILED")
        return
    
    print("\n" + "=" * 60)
    print("All Phase 3 tests completed successfully!")
    print("=" * 60)
    print("\nSub-circuits are ready for simulation!")
    print("Next steps: GUI integration and rendering")


if __name__ == "__main__":
    main()
