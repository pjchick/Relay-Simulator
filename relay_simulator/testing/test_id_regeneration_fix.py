"""
Test ID Regeneration Fix - Verify hierarchical ID remapping preserves pin/tab names.

This test validates the fix for the bug where pin names and tab names were
being incorrectly remapped as UUIDs instead of being preserved.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.id_manager import IDManager
from core.id_regenerator import IDMapper


def test_hierarchical_id_remapping():
    """Test that only component IDs are remapped, pin/tab names are preserved."""
    id_manager = IDManager()
    id_mapper = IDMapper(id_manager)
    
    # Register component ID mapping
    old_comp_id = "afccd56d"
    new_comp_id = id_mapper.generate_new_id(old_comp_id)
    
    # Test cases: (input, expected_pattern)
    test_cases = [
        # Pin IDs - component.pin_name
        ("afccd56d.pin1", f"{new_comp_id}.pin1"),
        ("afccd56d.COIL", f"{new_comp_id}.COIL"),
        ("afccd56d.COM1", f"{new_comp_id}.COM1"),
        
        # Tab IDs - component.pin_name.tab_name
        ("afccd56d.pin1.tab1", f"{new_comp_id}.pin1.tab1"),
        ("afccd56d.COIL.tab0", f"{new_comp_id}.COIL.tab0"),
        ("afccd56d.COM1.tab0", f"{new_comp_id}.COM1.tab0"),
        
        # Complex pin names
        ("afccd56d.SUB_IN", f"{new_comp_id}.SUB_IN"),
        ("afccd56d.SUB_OUT", f"{new_comp_id}.SUB_OUT"),
    ]
    
    print("Testing hierarchical ID remapping...")
    print(f"Component ID mapping: {old_comp_id} → {new_comp_id}\n")
    
    all_passed = True
    for original_id, expected_pattern in test_cases:
        remapped = id_mapper.remap_hierarchical_id(original_id)
        
        # Check if remapped matches expected pattern
        if remapped == expected_pattern:
            print(f"✓ PASS: {original_id} → {remapped}")
        else:
            print(f"✗ FAIL: {original_id} → {remapped} (expected {expected_pattern})")
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED - ID remapping preserves pin/tab names")
    else:
        print("✗ SOME TESTS FAILED - Check implementation")
    print("="*60)
    
    return all_passed


def test_wire_tab_id_remapping():
    """Test realistic wire tab ID remapping scenario."""
    id_manager = IDManager()
    id_mapper = IDMapper(id_manager)
    
    # Simulate component ID mappings from template to instance
    template_ids = {
        "afccd56d": id_mapper.generate_new_id("afccd56d"),  # VCC
        "e2830e6e": id_mapper.generate_new_id("e2830e6e"),  # DPDTRelay
    }
    
    # Wire from template
    wire_start = "afccd56d.pin1.tab1"  # VCC tab
    wire_end = "e2830e6e.COM2.tab0"    # Relay COM2 tab
    
    # Remap wire endpoints
    remapped_start = id_mapper.remap_hierarchical_id(wire_start)
    remapped_end = id_mapper.remap_hierarchical_id(wire_end)
    
    print("\nTesting realistic wire remapping scenario...")
    print(f"Original wire: {wire_start} → {wire_end}")
    print(f"Remapped wire: {remapped_start} → {remapped_end}")
    
    # Validate format: should be {new_comp_id}.{original_pin_name}.{original_tab_name}
    start_parts = remapped_start.split('.')
    end_parts = remapped_end.split('.')
    
    # Check structure
    assert len(start_parts) == 3, f"Expected 3 parts, got {len(start_parts)}"
    assert len(end_parts) == 3, f"Expected 3 parts, got {len(end_parts)}"
    
    # Check component IDs were remapped
    assert start_parts[0] == template_ids["afccd56d"], "Component ID not remapped"
    assert end_parts[0] == template_ids["e2830e6e"], "Component ID not remapped"
    
    # Check pin/tab names were preserved
    assert start_parts[1] == "pin1", "Pin name was corrupted"
    assert start_parts[2] == "tab1", "Tab name was corrupted"
    assert end_parts[1] == "COM2", "Pin name was corrupted"
    assert end_parts[2] == "tab0", "Tab name was corrupted"
    
    print("✓ Wire tab IDs remapped correctly with preserved pin/tab names")
    return True


if __name__ == "__main__":
    test1_pass = test_hierarchical_id_remapping()
    test2_pass = test_wire_tab_id_remapping()
    
    if test1_pass and test2_pass:
        print("\n🎉 All ID regeneration tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed")
        exit(1)
