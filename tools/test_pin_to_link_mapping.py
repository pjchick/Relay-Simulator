"""
Test pin-to-link mapping restoration from file.

This verifies that SubCircuit components can find their internal Link components
after loading from a .rsim file.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'relay_simulator'))

from fileio.document_loader import DocumentLoader
from components.factory import get_factory

def test_pin_to_link_mapping():
    """Test that pin-to-link mapping is restored when loading SubTest1.rsim."""
    
    print("Loading SubTest1.rsim...")
    factory = get_factory()
    loader = DocumentLoader(factory)
    
    doc = loader.load_from_file('examples/SubTest1.rsim')
    print(f"✓ Loaded document with {len(doc.pages)} pages")
    print()
    
    # Find SubCircuit component
    main_page = doc.get_all_pages()[0]
    subcircuit = None
    
    for comp in main_page.components.values():
        if comp.component_type == "SubCircuit":
            subcircuit = comp
            break
    
    if not subcircuit:
        print("❌ No SubCircuit found!")
        return False
    
    print(f"SubCircuit: {subcircuit.component_id}")
    print(f"  Name: {subcircuit.sub_circuit_name}")
    print(f"  Instance ID: {subcircuit.instance_id}")
    print(f"  Sub-circuit ID: {subcircuit.sub_circuit_id}")
    print(f"  Document ref: {'SET' if subcircuit._document else 'NOT SET'}")
    print()
    
    # Check pins
    print(f"Pins ({len(subcircuit.pins)}):")
    for pin_id, pin in subcircuit.pins.items():
        print(f"  {pin_id} ({len(pin.tabs)} tabs)")
    print()
    
    # Check pin-to-link mapping
    print("Pin-to-Link Mapping:")
    if not subcircuit._pin_to_link_map:
        print("  ❌ EMPTY - mapping not restored!")
        return False
    
    all_valid = True
    for pin_id, link_id in subcircuit._pin_to_link_map.items():
        # Verify the Link component exists
        link_comp = doc.get_component(link_id)
        if link_comp:
            link_name = getattr(link_comp, 'link_name', 'UNKNOWN')
            print(f"  ✓ {pin_id} → {link_id} (Link: {link_name})")
        else:
            print(f"  ❌ {pin_id} → {link_id} (NOT FOUND!)")
            all_valid = False
    
    print()
    return all_valid


if __name__ == "__main__":
    print("="*70)
    print("SubCircuit Pin-to-Link Mapping Test")
    print("="*70)
    print()
    
    try:
        success = test_pin_to_link_mapping()
        
        print("="*70)
        if success:
            print("✓ Pin-to-link mapping successfully restored")
            print("  SubCircuit should now work in simulation")
        else:
            print("❌ Pin-to-link mapping failed")
        print("="*70)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
