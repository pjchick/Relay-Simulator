"""
Test suite for Document Class and FileIO (Phase 1.7)

Comprehensive tests for Document class, page management, document-wide operations,
ID validation, and file save/load functionality.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.document import Document
from core.page import Page
from core.file_io import FileIO
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
        comp.position = tuple(data.get('position', (0, 0)))
        comp.rotation = data.get('rotation', 0)
        comp.properties = data.get('properties', {}).copy()
        comp.link_name = data.get('link_name')
        
        # Reconstruct pins
        from core.pin import Pin
        for pin_data in data.get('pins', {}).values():
            pin = Pin.from_dict(pin_data, comp)
            comp.add_pin(pin)
        
        return comp


def test_document_creation():
    """Test Document class creation."""
    print("\n=== Testing Document Creation ===")
    
    doc = Document()
    
    # Verify metadata
    assert 'version' in doc.metadata
    assert 'author' in doc.metadata
    assert 'created' in doc.metadata
    assert 'modified' in doc.metadata
    assert 'description' in doc.metadata
    print(f"✓ Metadata initialized with all fields")
    
    # Verify collections
    assert isinstance(doc.pages, dict), "Pages should be dict"
    assert len(doc.pages) == 0, "Pages should start empty"
    print(f"✓ Pages collection initialized (empty)")
    
    # Verify ID manager
    assert doc.id_manager is not None
    print(f"✓ ID manager initialized")
    
    print("✓ Document creation tests passed")


def test_add_page():
    """Test adding pages to document."""
    print("\n=== Testing Add Page ===")
    
    doc = Document()
    
    # Create and add page
    page1 = Page("page001", "First Page")
    result = doc.add_page(page1)
    
    assert result == True, "Should return True when page added"
    assert len(doc.pages) == 1
    assert "page001" in doc.pages
    assert doc.pages["page001"] == page1
    print(f"✓ Added page: {len(doc.pages)} total")
    
    # Try to add duplicate page ID
    page_dup = Page("page001", "Duplicate")
    result = doc.add_page(page_dup)
    
    assert result == False, "Should return False for duplicate page ID"
    assert len(doc.pages) == 1, "Page count shouldn't change"
    print(f"✓ Duplicate page ID rejected")
    
    # Add more pages
    page2 = Page("page002", "Second Page")
    page3 = Page("page003", "Third Page")
    doc.add_page(page2)
    doc.add_page(page3)
    
    assert len(doc.pages) == 3
    print(f"✓ Added 3 pages total")
    
    print("✓ Add page tests passed")


def test_create_page():
    """Test creating pages with auto-generated IDs."""
    print("\n=== Testing Create Page ===")
    
    doc = Document()
    
    # Create page with auto ID
    page1 = doc.create_page("Auto Page 1")
    
    assert page1 is not None
    assert len(page1.page_id) == 8, "Generated ID should be 8 chars"
    assert page1.name == "Auto Page 1"
    assert page1.page_id in doc.pages
    print(f"✓ Created page with auto ID: {page1.page_id}")
    
    # Create another
    page2 = doc.create_page("Auto Page 2")
    
    assert page2.page_id != page1.page_id, "IDs should be unique"
    assert len(doc.pages) == 2
    print(f"✓ Created second page: {page2.page_id}")
    
    # Create with default name
    page3 = doc.create_page()
    assert page3.name == "Untitled"
    print(f"✓ Created page with default name: '{page3.name}'")
    
    print("✓ Create page tests passed")


def test_get_page():
    """Test getting pages from document."""
    print("\n=== Testing Get Page ===")
    
    doc = Document()
    
    page1 = Page("page001", "Page 1")
    page2 = Page("page002", "Page 2")
    doc.add_page(page1)
    doc.add_page(page2)
    
    # Get specific page
    retrieved = doc.get_page("page001")
    assert retrieved == page1, "Should retrieve correct page"
    print(f"✓ Retrieved page by ID: {retrieved.page_id}")
    
    # Get non-existent page
    retrieved = doc.get_page("nonexistent")
    assert retrieved is None, "Should return None for non-existent page"
    print(f"✓ Non-existent page returns None")
    
    print("✓ Get page tests passed")


def test_get_all_pages():
    """Test getting all pages."""
    print("\n=== Testing Get All Pages ===")
    
    doc = Document()
    
    page1 = Page("page001", "Page 1")
    page2 = Page("page002", "Page 2")
    page3 = Page("page003", "Page 3")
    doc.add_page(page1)
    doc.add_page(page2)
    doc.add_page(page3)
    
    # Get all pages
    all_pages = doc.get_all_pages()
    
    assert len(all_pages) == 3, "Should return all 3 pages"
    assert page1 in all_pages
    assert page2 in all_pages
    assert page3 in all_pages
    print(f"✓ Retrieved all pages: {len(all_pages)} pages")
    
    # Verify it's a list
    assert isinstance(all_pages, list), "Should return a list"
    print(f"✓ Returns list of pages")
    
    # Test page count
    count = doc.get_page_count()
    assert count == 3
    print(f"✓ Page count: {count}")
    
    print("✓ Get all pages tests passed")


def test_remove_page():
    """Test removing pages from document."""
    print("\n=== Testing Remove Page ===")
    
    doc = Document()
    
    page1 = Page("page001", "Page 1")
    page2 = Page("page002", "Page 2")
    doc.add_page(page1)
    doc.add_page(page2)
    
    # Remove existing page
    removed = doc.remove_page("page001")
    assert removed == page1, "Should return removed page"
    assert len(doc.pages) == 1, "Should have 1 page left"
    assert "page001" not in doc.pages
    print(f"✓ Removed page: {len(doc.pages)} remaining")
    
    # Try to remove non-existent page
    removed = doc.remove_page("nonexistent")
    assert removed is None, "Should return None for non-existent page"
    assert len(doc.pages) == 1, "Page count shouldn't change"
    print(f"✓ Remove non-existent page returns None")
    
    print("✓ Remove page tests passed")


def test_get_component_by_id():
    """Test getting components across pages."""
    print("\n=== Testing Get Component By ID ===")
    
    doc = Document()
    
    page1 = Page("page001", "Page 1")
    page2 = Page("page002", "Page 2")
    doc.add_page(page1)
    doc.add_page(page2)
    
    # Add components to different pages
    comp1 = TestComponent("page001.comp001", "page001")
    comp2 = TestComponent("page002.comp002", "page002")
    page1.add_component(comp1)
    page2.add_component(comp2)
    
    # Get component with page ID prefix
    retrieved = doc.get_component("page001.comp001")
    assert retrieved == comp1, "Should find component on correct page"
    print(f"✓ Found component: {retrieved.component_id}")
    
    # Get component from different page
    retrieved = doc.get_component("page002.comp002")
    assert retrieved == comp2
    print(f"✓ Found component on page 2: {retrieved.component_id}")
    
    # Get non-existent component
    retrieved = doc.get_component("nonexistent")
    assert retrieved is None
    print(f"✓ Non-existent component returns None")
    
    print("✓ Get component by ID tests passed")


def test_get_all_components():
    """Test getting all components across all pages."""
    print("\n=== Testing Get All Components ===")
    
    doc = Document()
    
    page1 = Page("page001", "Page 1")
    page2 = Page("page002", "Page 2")
    doc.add_page(page1)
    doc.add_page(page2)
    
    # Add components to different pages
    comp1 = TestComponent("page001.comp001", "page001")
    comp2 = TestComponent("page001.comp002", "page001")
    comp3 = TestComponent("page002.comp003", "page002")
    page1.add_component(comp1)
    page1.add_component(comp2)
    page2.add_component(comp3)
    
    # Get all components
    all_comps = doc.get_all_components()
    
    assert len(all_comps) == 3, "Should return all 3 components"
    assert comp1 in all_comps
    assert comp2 in all_comps
    assert comp3 in all_comps
    print(f"✓ Retrieved all components: {len(all_comps)} components across pages")
    
    print("✓ Get all components tests passed")


def test_get_components_with_link_name():
    """Test finding components by link name."""
    print("\n=== Testing Get Components With Link Name ===")
    
    doc = Document()
    
    page1 = Page("page001", "Page 1")
    page2 = Page("page002", "Page 2")
    doc.add_page(page1)
    doc.add_page(page2)
    
    # Add components with link names
    comp1 = TestComponent("page001.comp001", "page001")
    comp1.link_name = "POWER"
    comp2 = TestComponent("page001.comp002", "page001")
    comp2.link_name = "GROUND"
    comp3 = TestComponent("page002.comp003", "page002")
    comp3.link_name = "POWER"  # Same link name on different page
    
    page1.add_component(comp1)
    page1.add_component(comp2)
    page2.add_component(comp3)
    
    # Find components with "POWER" link
    power_comps = doc.get_components_with_link_name("POWER")
    
    assert len(power_comps) == 2, "Should find 2 components with POWER link"
    assert comp1 in power_comps
    assert comp3 in power_comps
    print(f"✓ Found {len(power_comps)} components with 'POWER' link")
    
    # Find components with "GROUND" link
    ground_comps = doc.get_components_with_link_name("GROUND")
    assert len(ground_comps) == 1
    assert comp2 in ground_comps
    print(f"✓ Found {len(ground_comps)} components with 'GROUND' link")
    
    # Find non-existent link
    none_comps = doc.get_components_with_link_name("NONEXISTENT")
    assert len(none_comps) == 0
    print(f"✓ Non-existent link returns empty list")
    
    print("✓ Get components with link name tests passed")


def test_validate_ids_success():
    """Test ID validation with unique IDs."""
    print("\n=== Testing Validate IDs (Success) ===")
    
    doc = Document()
    
    page1 = Page("page001", "Page 1")
    doc.add_page(page1)
    
    comp1 = TestComponent("page001.comp001", "page001")
    pin1 = Pin("page001.comp001.pin001", comp1)
    tab1 = Tab("page001.comp001.pin001.tab001", pin1, (0, 0))
    pin1.add_tab(tab1)
    comp1.add_pin(pin1)
    page1.add_component(comp1)
    
    # Validate
    is_valid, duplicates = doc.validate_ids()
    
    assert is_valid == True, "Should be valid with unique IDs"
    assert len(duplicates) == 0, "Should have no duplicates"
    print(f"✓ Validation passed with unique IDs")
    
    print("✓ Validate IDs success tests passed")


def test_validate_ids_failure():
    """Test ID validation with duplicate IDs."""
    print("\n=== Testing Validate IDs (Failure) ===")
    
    doc = Document()
    
    page1 = Page("page001", "Page 1")
    doc.add_page(page1)
    
    # Create components with duplicate IDs (manually bypass normal add)
    comp1 = TestComponent("page001.comp001", "page001")
    comp2 = TestComponent("page001.comp001", "page001")  # Duplicate!
    page1.components["comp001_a"] = comp1
    page1.components["comp001_b"] = comp2
    
    # Validate
    is_valid, duplicates = doc.validate_ids()
    
    assert is_valid == False, "Should be invalid with duplicate IDs"
    assert "page001.comp001" in duplicates, "Should detect duplicate component ID"
    print(f"✓ Validation detected duplicate: {duplicates}")
    
    print("✓ Validate IDs failure tests passed")


def test_document_serialization():
    """Test document serialization."""
    print("\n=== Testing Document Serialization ===")
    
    doc = Document()
    doc.metadata['author'] = "Test User"
    doc.metadata['description'] = "Test Document"
    
    page1 = Page("page001", "Main Page")
    doc.add_page(page1)
    
    comp1 = TestComponent("page001.comp001", "page001")
    comp1.position = (100, 200)
    page1.add_component(comp1)
    
    # Serialize
    data = doc.to_dict()
    
    assert 'metadata' in data
    assert 'pages' in data
    assert data['metadata']['author'] == "Test User"
    assert data['metadata']['description'] == "Test Document"
    assert len(data['pages']) == 1
    assert 'page001' in data['pages']
    
    print(f"✓ Serialization includes all fields")
    print(f"  Author: {data['metadata']['author']}")
    print(f"  Pages: {len(data['pages'])}")
    
    print("✓ Document serialization tests passed")


def test_document_deserialization():
    """Test document deserialization."""
    print("\n=== Testing Document Deserialization ===")
    
    # Create serialized data
    data = {
        'metadata': {
            'version': '1.0',
            'author': 'Test User',
            'description': 'Restored Document'
        },
        'pages': {
            'page001': {
                'page_id': 'page001',
                'name': 'Restored Page',
                'components': {},
                'wires': {}
            }
        }
    }
    
    # Deserialize
    doc = Document.from_dict(data)
    
    assert doc.metadata['author'] == "Test User"
    assert doc.metadata['description'] == "Restored Document"
    assert len(doc.pages) == 1
    assert "page001" in doc.pages
    assert doc.pages["page001"].name == "Restored Page"
    
    print(f"✓ Deserialized document")
    print(f"  Author: {doc.metadata['author']}")
    print(f"  Pages: {len(doc.pages)}")
    
    print("✓ Document deserialization tests passed")


def test_file_save():
    """Test saving document to .rsim file."""
    print("\n=== Testing File Save ===")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.rsim', delete=False) as tf:
        temp_path = tf.name
    
    try:
        # Create document
        doc = Document()
        doc.metadata['author'] = "File Test"
        page1 = doc.create_page("Test Page")
        
        comp1 = TestComponent("comp001", "page001")
        comp1.position = (50, 100)
        page1.add_component(comp1)
        
        # Save
        result = FileIO.save_document(doc, temp_path)
        
        assert result['success'] == True, f"Save failed: {result['message']}"
        print(f"✓ {result['message']}")
        
        # Verify file exists
        assert Path(temp_path).exists(), "File should exist"
        print(f"✓ File created: {temp_path}")
        
        # Verify file size
        file_size = Path(temp_path).stat().st_size
        assert file_size > 0, "File should not be empty"
        print(f"✓ File size: {file_size} bytes")
        
    finally:
        # Cleanup
        if Path(temp_path).exists():
            Path(temp_path).unlink()
    
    print("✓ File save tests passed")


def test_file_load():
    """Test loading document from .rsim file."""
    print("\n=== Testing File Load ===")
    
    # Create and save document
    with tempfile.NamedTemporaryFile(suffix='.rsim', delete=False) as tf:
        temp_path = tf.name
    
    try:
        # Create original document
        doc1 = Document()
        doc1.metadata['author'] = "Load Test"
        doc1.metadata['description'] = "Test loading"
        page1 = doc1.create_page("Original Page")
        
        comp1 = TestComponent("comp001", page1.page_id)
        comp1.position = (123, 456)
        comp1.set_property("test_prop", "test_value")
        page1.add_component(comp1)
        
        # Save
        FileIO.save_document(doc1, temp_path)
        
        # Load
        result = FileIO.load_document(temp_path)
        
        assert result['success'] == True, f"Load failed: {result['message']}"
        print(f"✓ {result['message']}")
        
        doc2 = result['document']
        assert doc2 is not None
        assert doc2.metadata['author'] == "Load Test"
        assert doc2.metadata['description'] == "Test loading"
        assert len(doc2.pages) == 1
        print(f"✓ Document loaded correctly")
        print(f"  Author: {doc2.metadata['author']}")
        print(f"  Pages: {len(doc2.pages)}")
        
    finally:
        # Cleanup
        if Path(temp_path).exists():
            Path(temp_path).unlink()
    
    print("✓ File load tests passed")


def test_file_save_load_roundtrip():
    """Test save → load → save produces consistent results."""
    print("\n=== Testing File Save/Load Roundtrip ===")
    
    with tempfile.NamedTemporaryFile(suffix='.rsim', delete=False) as tf:
        temp_path = tf.name
    
    try:
        # Create document
        doc1 = Document()
        doc1.metadata['author'] = "Roundtrip Test"
        page1 = doc1.create_page("Page 1")
        page2 = doc1.create_page("Page 2")
        
        # Save
        FileIO.save_document(doc1, temp_path)
        
        # Load
        result = FileIO.load_document(temp_path)
        doc2 = result['document']
        
        # Compare
        assert doc2.metadata['author'] == doc1.metadata['author']
        assert len(doc2.pages) == len(doc1.pages)
        print(f"✓ Roundtrip data matches")
        print(f"  Pages: {len(doc2.pages)}")
        
    finally:
        if Path(temp_path).exists():
            Path(temp_path).unlink()
    
    print("✓ Roundtrip tests passed")


def test_create_empty_document():
    """Test creating empty document helper."""
    print("\n=== Testing Create Empty Document ===")
    
    doc = FileIO.create_empty_document()
    
    assert doc is not None
    assert doc.metadata['version'] == '1.0'
    assert len(doc.pages) == 1, "Should have 1 default page"
    
    page = doc.get_all_pages()[0]
    assert page.name == "Page 1"
    print(f"✓ Created empty document with default page: '{page.name}'")
    
    print("✓ Create empty document tests passed")


def test_document_repr():
    """Test document string representation."""
    print("\n=== Testing Document Repr ===")
    
    doc = Document()
    page1 = doc.create_page("Page 1")
    
    comp1 = TestComponent("comp001", page1.page_id)
    comp2 = TestComponent("comp002", page1.page_id)
    page1.add_component(comp1)
    page1.add_component(comp2)
    
    repr_str = repr(doc)
    print(f"✓ Document repr: {repr_str}")
    
    assert "Document(" in repr_str
    assert "pages=1" in repr_str
    assert "components=2" in repr_str
    
    print("✓ Document repr tests passed")


def run_all_tests():
    """Run all Document and FileIO tests."""
    print("=" * 60)
    print("DOCUMENT CLASS & FILE I/O TEST SUITE (Phase 1.7)")
    print("=" * 60)
    
    try:
        test_document_creation()
        test_add_page()
        test_create_page()
        test_get_page()
        test_get_all_pages()
        test_remove_page()
        test_get_component_by_id()
        test_get_all_components()
        test_get_components_with_link_name()
        test_validate_ids_success()
        test_validate_ids_failure()
        test_document_serialization()
        test_document_deserialization()
        test_file_save()
        test_file_load()
        test_file_save_load_roundtrip()
        test_create_empty_document()
        test_document_repr()
        
        print("\n" + "=" * 60)
        print("✓ ALL DOCUMENT & FILE I/O TESTS PASSED")
        print("=" * 60)
        print("\nSection 1.7 Document Class Requirements:")
        print("✓ Define Document class")
        print("  ✓ Document metadata")
        print("  ✓ Collection of Pages")
        print("  ✓ ID Manager")
        print("✓ Implement page management")
        print("  ✓ add_page()")
        print("  ✓ create_page()")
        print("  ✓ remove_page()")
        print("  ✓ get_page()")
        print("  ✓ get_all_pages()")
        print("  ✓ get_page_count()")
        print("✓ Implement document-wide operations")
        print("  ✓ validate_ids()")
        print("  ✓ get_component()")
        print("  ✓ get_all_components()")
        print("  ✓ get_components_with_link_name()")
        print("✓ Add serialization support")
        print("  ✓ to_dict()")
        print("  ✓ from_dict()")
        print("  ✓ FileIO.save_document()")
        print("  ✓ FileIO.load_document()")
        print("  ✓ FileIO.create_empty_document()")
        print("✓ Tests")
        print("  ✓ Test document creation")
        print("  ✓ Test page management")
        print("  ✓ Test ID uniqueness validation")
        print("  ✓ Test file save/load")
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
