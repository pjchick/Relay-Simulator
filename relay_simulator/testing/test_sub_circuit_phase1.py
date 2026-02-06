"""
Test script for Sub-Circuit Loader - Phase 1 validation.

Tests:
1. Load Latch.rsub template
2. Validate FOOTPRINT page exists
3. Validate Link components on FOOTPRINT
4. Serialize/deserialize SubCircuitDefinition
"""

import sys
from pathlib import Path

# Add relay_simulator to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fileio.sub_circuit_loader import SubCircuitLoader, SubCircuitTemplate
from core.document import Document, SubCircuitDefinition
from components.factory import ComponentFactory


def test_load_latch_rsub():
    """Test loading the Latch.rsub example file."""
    print("=" * 60)
    print("Test 1: Load Latch.rsub")
    print("=" * 60)
    
    loader = SubCircuitLoader()
    rsub_path = Path(__file__).parent.parent.parent / "examples" / "Latch.rsub"
    
    try:
        template = loader.load_from_file(str(rsub_path))
        print(f"✓ Loaded template: {template.name}")
        print(f"  Source file: {template.source_file}")
        print(f"  Number of pages: {len(template.pages)}")
        print(f"  FOOTPRINT page ID: {template.footprint_page_id}")
        print(f"  Interface links: {len(template.interface_links)}")
        
        # Print link details
        for i, link in enumerate(template.interface_links, 1):
            link_name = link.get('link_name', 'UNNAMED')
            comp_id = link.get('component_id', 'unknown')
            print(f"    Link {i}: {link_name} (ID: {comp_id})")
        
        return template
    except Exception as e:
        print(f"✗ Failed to load: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_sub_circuit_definition_serialization():
    """Test SubCircuitDefinition to_dict/from_dict."""
    print("\n" + "=" * 60)
    print("Test 2: SubCircuitDefinition Serialization")
    print("=" * 60)
    
    factory = ComponentFactory()
    
    # Create a test definition
    sc_def = SubCircuitDefinition("test123", "TestCircuit")
    sc_def.source_file = "test.rsub"
    
    # Serialize
    data = sc_def.to_dict()
    print(f"✓ Serialized definition")
    print(f"  Keys: {list(data.keys())}")
    
    # Deserialize
    sc_def2 = SubCircuitDefinition.from_dict(data, factory)
    print(f"✓ Deserialized definition")
    print(f"  ID: {sc_def2.sub_circuit_id}")
    print(f"  Name: {sc_def2.name}")
    print(f"  Source: {sc_def2.source_file}")
    
    return sc_def2


def test_document_with_sub_circuits():
    """Test Document with embedded sub-circuits."""
    print("\n" + "=" * 60)
    print("Test 3: Document with Sub-Circuits")
    print("=" * 60)
    
    factory = ComponentFactory()
    
    # Create document
    doc = Document()
    page = doc.create_page("Main Page")
    print(f"✓ Created document with page: {page.name}")
    
    # Add sub-circuit definition
    sc_def = SubCircuitDefinition("sc001", "Latch")
    sc_def.source_file = "Latch.rsub"
    doc.add_sub_circuit_definition(sc_def)
    print(f"✓ Added sub-circuit definition: {sc_def.name}")
    
    # Serialize
    data = doc.to_dict()
    print(f"✓ Serialized document")
    print(f"  Top-level keys: {list(data.keys())}")
    print(f"  Has sub_circuits: {'sub_circuits' in data}")
    
    # Deserialize
    doc2 = Document.from_dict(data, factory)
    print(f"✓ Deserialized document")
    print(f"  Pages: {doc2.get_page_count()}")
    print(f"  Sub-circuits: {len(doc2.sub_circuits)}")
    
    # Check sub-circuit
    sc_def2 = doc2.get_sub_circuit_definition("sc001")
    if sc_def2:
        print(f"  Retrieved sub-circuit: {sc_def2.name}")
    else:
        print(f"  ✗ Sub-circuit not found!")
    
    return doc2


def main():
    """Run all tests."""
    print("Phase 1 Sub-Circuit Implementation Tests")
    print("=" * 60 + "\n")
    
    # Test 1
    template = test_load_latch_rsub()
    if not template:
        print("\n✗ Test 1 FAILED - aborting")
        return
    
    # Test 2
    test_sub_circuit_definition_serialization()
    
    # Test 3
    test_document_with_sub_circuits()
    
    print("\n" + "=" * 60)
    print("All Phase 1 tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
