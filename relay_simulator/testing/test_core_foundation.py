"""
Test script for core foundation classes.
Tests ID generation, Pin/Tab relationships, and document structure.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import PinState, IDManager, Tab, Pin, Document, FileIO


def test_id_manager():
    """Test ID manager functionality"""
    print("=" * 60)
    print("Testing ID Manager")
    print("=" * 60)
    
    id_mgr = IDManager()
    
    # Generate some IDs
    id1 = id_mgr.generate_id()
    id2 = id_mgr.generate_id()
    id3 = id_mgr.generate_id()
    
    print(f"Generated IDs: {id1}, {id2}, {id3}")
    print(f"All IDs are 8 chars: {len(id1) == 8 and len(id2) == 8 and len(id3) == 8}")
    print(f"All IDs are unique: {len({id1, id2, id3}) == 3}")
    print(f"Used ID count: {id_mgr.get_used_count()}")
    
    # Test hierarchical IDs
    comp_id = IDManager.build_hierarchical_id(id1, id2)
    pin_id = IDManager.build_hierarchical_id(id1, id2, id3)
    print(f"\nHierarchical IDs:")
    print(f"  Component: {comp_id}")
    print(f"  Pin: {pin_id}")
    print(f"  Extracted page ID: {IDManager.get_page_id(pin_id)}")
    
    # Test page ID replacement
    new_id = IDManager.replace_page_id(pin_id, "aaaaaaaa")
    print(f"  Replaced page ID: {new_id}")
    
    print("\n✓ ID Manager tests passed\n")


def test_pin_tab_system():
    """Test Pin and Tab relationships"""
    print("=" * 60)
    print("Testing Pin/Tab System")
    print("=" * 60)
    
    # Create a pin with multiple tabs
    pin = Pin("12345678.abcdef12.pin00001", None)
    
    # Add 4 tabs (like an indicator)
    tab1 = Tab("12345678.abcdef12.pin00001.tab00001", pin, (0, -20))   # 12 o'clock
    tab2 = Tab("12345678.abcdef12.pin00001.tab00002", pin, (20, 0))    # 3 o'clock
    tab3 = Tab("12345678.abcdef12.pin00001.tab00003", pin, (0, 20))    # 6 o'clock
    tab4 = Tab("12345678.abcdef12.pin00001.tab00004", pin, (-20, 0))   # 9 o'clock
    
    pin.add_tab(tab1)
    pin.add_tab(tab2)
    pin.add_tab(tab3)
    pin.add_tab(tab4)
    
    print(f"Created pin with {len(pin.tabs)} tabs")
    print(f"Initial pin state: {pin.state}")
    print(f"All tabs FLOAT: {all(tab.state == PinState.FLOAT for tab in pin.tabs.values())}")
    
    # Set pin state to HIGH
    pin.set_state(PinState.HIGH)
    print(f"\nSet pin to HIGH")
    print(f"Pin state: {pin.state}")
    print(f"All tabs HIGH: {all(tab.state == PinState.HIGH for tab in pin.tabs.values())}")
    
    # Set one tab to FLOAT (should not affect pin since others are HIGH)
    tab1._state = PinState.FLOAT
    combined = pin.evaluate_state_from_tabs()
    print(f"\nSet one tab to FLOAT, evaluated state: {combined}")
    print(f"Pin still HIGH (OR logic): {pin.state == PinState.HIGH}")
    
    # Set all tabs to FLOAT
    for tab in pin.tabs.values():
        tab._state = PinState.FLOAT
    combined = pin.evaluate_state_from_tabs()
    print(f"\nSet all tabs to FLOAT, evaluated state: {combined}")
    print(f"Pin now FLOAT: {pin.state == PinState.FLOAT}")
    
    print("\n✓ Pin/Tab tests passed\n")


def test_document_structure():
    """Test Document, Page, and hierarchy"""
    print("=" * 60)
    print("Testing Document Structure")
    print("=" * 60)
    
    # Create document
    doc = Document()
    print(f"Created empty document")
    print(f"Initial page count: {doc.get_page_count()}")
    
    # Add pages
    page1 = doc.create_page("Main Circuit")
    page2 = doc.create_page("Sub-circuit")
    
    print(f"\nAdded 2 pages")
    print(f"Page count: {doc.get_page_count()}")
    print(f"Page 1: {page1}")
    print(f"Page 2: {page2}")
    
    # Validate IDs
    is_valid, duplicates = doc.validate_ids()
    print(f"\nID validation: {'PASS' if is_valid else 'FAIL'}")
    if not is_valid:
        print(f"Duplicates: {duplicates}")
    
    print("\n✓ Document structure tests passed\n")


def test_file_io():
    """Test saving and loading documents"""
    print("=" * 60)
    print("Testing File I/O")
    print("=" * 60)
    
    # Create a document
    doc = FileIO.create_empty_document()
    page = doc.get_all_pages()[0]
    page.name = "Test Page"
    
    print(f"Created document: {doc}")
    
    # Save to file
    test_file = Path(__file__).parent / "test_output" / "test.rsim"
    result = FileIO.save_document(doc, str(test_file))
    print(f"\nSave result: {result['success']}")
    print(f"Message: {result['message']}")
    
    if result['success']:
        print(f"File exists: {test_file.exists()}")
        print(f"File size: {test_file.stat().st_size} bytes")
        
        # Load it back
        result = FileIO.load_document(str(test_file))
        print(f"\nLoad result: {result['success']}")
        print(f"Message: {result['message']}")
        
        if result['success']:
            loaded_doc = result['document']
            print(f"Loaded document: {loaded_doc}")
            print(f"Pages match: {loaded_doc.get_page_count() == doc.get_page_count()}")
            print(f"Page name matches: {loaded_doc.get_all_pages()[0].name == page.name}")
    
    print("\n✓ File I/O tests passed\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CORE FOUNDATION CLASSES TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_id_manager()
        test_pin_tab_system()
        test_document_structure()
        test_file_io()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
