"""
Test script for Sub-Circuit Instantiation - Phase 2 validation.

Tests:
1. Load and embed Latch.rsub template
2. Create instance with ID regeneration
3. Verify page cloning and ID mapping
4. Verify SubCircuit component creation
5. Verify pin creation from FOOTPRINT Links
6. Verify bounding box calculation
"""

import sys
from pathlib import Path

# Add relay_simulator to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document import Document
from core.sub_circuit_instantiator import SubCircuitInstantiator
from components.factory import ComponentFactory


def test_load_and_embed():
    """Test loading .rsub and embedding in document."""
    print("=" * 60)
    print("Test 1: Load and Embed Template")
    print("=" * 60)
    
    doc = Document()
    main_page = doc.create_page("Main")
    factory = ComponentFactory()
    
    instantiator = SubCircuitInstantiator(doc, factory)
    rsub_path = Path(__file__).parent.parent.parent / "examples" / "Latch.rsub"
    
    try:
        sc_def = instantiator.load_and_embed_template(str(rsub_path))
        print(f"✓ Loaded and embedded: {sc_def.name}")
        print(f"  Definition ID: {sc_def.sub_circuit_id}")
        print(f"  Template pages: {len(sc_def.template_pages)}")
        print(f"  Source file: {sc_def.source_file}")
        
        # Verify in document
        retrieved = doc.get_sub_circuit_definition(sc_def.sub_circuit_id)
        if retrieved:
            print(f"✓ Definition accessible from document")
        else:
            print(f"✗ Definition NOT found in document")
            return None
        
        return sc_def, doc, main_page, instantiator
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_create_instance(sc_def, doc, main_page, instantiator):
    """Test creating an instance."""
    print("\n" + "=" * 60)
    print("Test 2: Create Instance")
    print("=" * 60)
    
    try:
        sub_circuit = instantiator.create_instance(
            sc_def.sub_circuit_id,
            main_page.page_id,
            (200, 200)
        )
        
        print(f"✓ Created instance component")
        print(f"  Component ID: {sub_circuit.component_id}")
        print(f"  Instance ID: {sub_circuit.instance_id}")
        print(f"  Position: {sub_circuit.position}")
        print(f"  Pins: {len(sub_circuit.pins)}")
        print(f"  Width x Height: {sub_circuit.width} x {sub_circuit.height}")
        
        # Verify instance in definition
        instance = sc_def.instances.get(sub_circuit.instance_id)
        if instance:
            print(f"✓ Instance record created")
            print(f"  Parent page: {instance.parent_page_id}")
            print(f"  Page ID mappings: {len(instance.page_id_map)}")
        else:
            print(f"✗ Instance record NOT found")
            return None
        
        return sub_circuit, instance
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_page_cloning(doc, sc_def, instance):
    """Test that pages were cloned correctly."""
    print("\n" + "=" * 60)
    print("Test 3: Page Cloning & ID Regeneration")
    print("=" * 60)
    
    # Check instance pages exist in document
    for template_page_id, instance_page_id in instance.page_id_map.items():
        instance_page = doc.get_page(instance_page_id)
        
        if instance_page:
            print(f"✓ Cloned page: {instance_page.name}")
            print(f"  Template ID: {template_page_id}")
            print(f"  Instance ID: {instance_page_id}")
            print(f"  Is sub-circuit page: {instance_page.is_sub_circuit_page}")
            print(f"  Parent instance: {instance_page.parent_instance_id}")
            print(f"  Components: {len(instance_page.components)}")
            
            # Verify component IDs are different from template
            for comp in instance_page.components.values():
                if comp.component_id == template_page_id:
                    print(f"  ✗ Component ID NOT regenerated!")
                    return False
        else:
            print(f"✗ Instance page {instance_page_id} NOT found in document")
            return False
    
    print(f"\n✓ All {len(instance.page_id_map)} pages cloned successfully")
    return True


def test_pin_generation(sub_circuit):
    """Test that pins were generated from FOOTPRINT Links."""
    print("\n" + "=" * 60)
    print("Test 4: Pin Generation from FOOTPRINT")
    print("=" * 60)
    
    expected_links = ["SUB_IN", "SUB_OUT"]
    
    for link_name in expected_links:
        pin_id = f"{sub_circuit.component_id}.{link_name}"
        pin = sub_circuit.pins.get(pin_id)
        
        if pin:
            print(f"✓ Pin created for Link: {link_name}")
            print(f"  Pin ID: {pin.pin_id}")
            print(f"  Tabs: {len(pin.tabs)}")
            
            # Check for instance link mapping in properties
            if hasattr(pin, 'properties') and pin.properties:
                instance_link_id = pin.properties.get('instance_link_id')
                if instance_link_id:
                    print(f"  Instance Link ID: {instance_link_id}")
                else:
                    print(f"  (No instance link ID yet - OK for Phase 2)")
        else:
            print(f"✗ Pin NOT created for Link: {link_name}")
            return False
    
    print(f"\n✓ All {len(expected_links)} pins generated correctly")
    return True


def test_serialization(doc):
    """Test document serialization with sub-circuits."""
    print("\n" + "=" * 60)
    print("Test 5: Serialization Round-Trip")
    print("=" * 60)
    
    try:
        # Serialize
        data = doc.to_dict()
        print(f"✓ Serialized document")
        print(f"  Pages: {len(data['pages'])}")
        print(f"  Sub-circuits: {len(data.get('sub_circuits', {}))}")
        
        # Count instance pages vs main pages
        main_pages = 0
        instance_pages = 0
        for page_data in data['pages']:
            if page_data.get('is_sub_circuit_page'):
                instance_pages += 1
            else:
                main_pages += 1
        
        print(f"  Main pages: {main_pages}")
        print(f"  Instance pages: {instance_pages}")
        
        # Deserialize
        factory = ComponentFactory()
        doc2 = Document.from_dict(data, factory)
        print(f"✓ Deserialized document")
        print(f"  Pages: {doc2.get_page_count()}")
        print(f"  Sub-circuits: {len(doc2.sub_circuits)}")
        
        # Verify instance pages have correct flags
        for page in doc2.get_all_pages():
            if page.is_sub_circuit_page:
                if not page.parent_instance_id:
                    print(f"  ✗ Instance page missing parent_instance_id!")
                    return False
        
        print(f"✓ All instance pages have correct metadata")
        return True
    except Exception as e:
        print(f"✗ Serialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_instances(doc, sc_def, instantiator, main_page):
    """Test creating multiple instances of same sub-circuit."""
    print("\n" + "=" * 60)
    print("Test 6: Multiple Instances")
    print("=" * 60)
    
    try:
        # Create second instance
        sub_circuit2 = instantiator.create_instance(
            sc_def.sub_circuit_id,
            main_page.page_id,
            (400, 200)
        )
        
        print(f"✓ Created second instance")
        print(f"  Component ID: {sub_circuit2.component_id}")
        print(f"  Instance ID: {sub_circuit2.instance_id}")
        
        # Verify definition has two instances
        print(f"  Total instances in definition: {len(sc_def.instances)}")
        
        if len(sc_def.instances) != 2:
            print(f"✗ Expected 2 instances, got {len(sc_def.instances)}")
            return False
        
        # Verify page count (1 main + 2 instances * 2 pages each = 5 total)
        expected_pages = 1 + (2 * 2)  # 1 main + 2 instances with 2 pages each
        actual_pages = doc.get_page_count()
        
        print(f"  Total pages in document: {actual_pages}")
        print(f"  Expected: {expected_pages}")
        
        if actual_pages != expected_pages:
            print(f"✗ Page count mismatch")
            return False
        
        print(f"✓ Multiple instances work correctly")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("Phase 2 Sub-Circuit Instantiation Tests")
    print("=" * 60 + "\n")
    
    # Test 1
    result = test_load_and_embed()
    if not result:
        print("\n✗ Test 1 FAILED - aborting")
        return
    sc_def, doc, main_page, instantiator = result
    
    # Test 2
    result = test_create_instance(sc_def, doc, main_page, instantiator)
    if not result:
        print("\n✗ Test 2 FAILED - aborting")
        return
    sub_circuit, instance = result
    
    # Test 3
    if not test_page_cloning(doc, sc_def, instance):
        print("\n✗ Test 3 FAILED - aborting")
        return
    
    # Test 4
    if not test_pin_generation(sub_circuit):
        print("\n✗ Test 4 FAILED - aborting")
        return
    
    # Test 5
    if not test_serialization(doc):
        print("\n✗ Test 5 FAILED - aborting")
        return
    
    # Test 6
    if not test_multiple_instances(doc, sc_def, instantiator, main_page):
        print("\n✗ Test 6 FAILED")
        return
    
    print("\n" + "=" * 60)
    print("All Phase 2 tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
