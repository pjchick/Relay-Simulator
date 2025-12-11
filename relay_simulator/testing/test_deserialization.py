"""
Tests for deserialization and document loading.
Validates loading .rsim files with ComponentFactory integration.
"""

import unittest
import json
import tempfile
from pathlib import Path

from fileio.document_loader import DocumentLoader, load_document, save_document
from fileio.example_files import SIMPLE_SWITCH_LED, RELAY_CIRCUIT, CROSS_PAGE_LINKS
from fileio.example_files import WIRE_WITH_JUNCTION, INVALID_VERSION, INVALID_MISSING_REQUIRED
from components.factory import ComponentFactory
from core.document import Document
from core.page import Page
from components.switch import Switch
from components.indicator import Indicator


class TestDocumentLoader(unittest.TestCase):
    """Test DocumentLoader class"""
    
    def setUp(self):
        """Create loader with factory"""
        self.factory = ComponentFactory()
        self.loader = DocumentLoader(self.factory)
    
    def test_loader_creation(self):
        """Test creating loader"""
        loader = DocumentLoader()
        self.assertIsNotNone(loader.component_factory)
        
        # With custom factory
        factory = ComponentFactory()
        loader2 = DocumentLoader(factory)
        self.assertIs(loader2.component_factory, factory)
    
    def test_load_from_string_simple(self):
        """Test loading simple circuit from JSON string"""
        doc = self.loader.load_from_string(SIMPLE_SWITCH_LED)
        
        self.assertEqual(len(doc.pages), 1)
        page = list(doc.pages.values())[0]
        
        # Should have 2 components
        self.assertEqual(len(page.components), 2)
        
        # Should have 1 wire
        self.assertEqual(len(page.wires), 1)
    
    def test_load_from_string_relay_circuit(self):
        """Test loading relay circuit"""
        doc = self.loader.load_from_string(RELAY_CIRCUIT)
        
        self.assertEqual(len(doc.pages), 1)
        page = list(doc.pages.values())[0]
        
        # Should have 4 components (Switch, VCC, DPDTRelay, Indicator)
        self.assertEqual(len(page.components), 4)
        
        # Verify component types
        types = [comp.component_type for comp in page.components.values()]
        self.assertIn('Switch', types)
        self.assertIn('VCC', types)
        self.assertIn('DPDTRelay', types)
        self.assertIn('Indicator', types)
    
    def test_load_cross_page_links(self):
        """Test loading multi-page circuit with links"""
        doc = self.loader.load_from_string(CROSS_PAGE_LINKS)
        
        # Should have 2 pages
        self.assertEqual(len(doc.pages), 2)
        
        # Get components with link names
        linked_comps = doc.get_components_with_link_name('SIGNAL_A')
        self.assertEqual(len(linked_comps), 2)
        
        # Both should have link_name set
        for comp in linked_comps:
            self.assertEqual(comp.link_name, 'SIGNAL_A')
    
    def test_load_wire_with_junction(self):
        """Test loading wire with junction"""
        doc = self.loader.load_from_string(WIRE_WITH_JUNCTION)
        
        page = list(doc.pages.values())[0]
        
        # Should have 4 components (Switch + 3 Indicators)
        self.assertEqual(len(page.components), 4)
        
        # Should have wires with junction
        self.assertGreater(len(page.wires), 0)
        
        # Find wire with junction (junctions is a dict)
        wire_with_junction = None
        for wire in page.wires.values():
            if wire.junctions:
                wire_with_junction = wire
                break
        
        self.assertIsNotNone(wire_with_junction)
        self.assertEqual(len(wire_with_junction.junctions), 1)
        
        # Junction should have 3 child wires (to 3 LEDs)
        junction = list(wire_with_junction.junctions.values())[0]
        self.assertEqual(len(junction.child_wires), 3)
    
    def test_load_invalid_version(self):
        """Test loading file with invalid version"""
        with self.assertRaises(ValueError) as cm:
            self.loader.load_from_string(INVALID_VERSION)
        
        self.assertIn('Incompatible', str(cm.exception))
    
    def test_load_invalid_missing_required(self):
        """Test loading file with missing required fields"""
        # This should fail during Page.from_dict() with KeyError
        with self.assertRaises(KeyError):
            self.loader.load_from_string(INVALID_MISSING_REQUIRED)
    
    def test_load_invalid_json(self):
        """Test loading malformed JSON"""
        with self.assertRaises(json.JSONDecodeError):
            self.loader.load_from_string("{invalid json")
    
    def test_validate_structure_not_object(self):
        """Test validation rejects non-object"""
        with self.assertRaises(ValueError) as cm:
            self.loader._validate_structure([])
        
        self.assertIn('must be a JSON object', str(cm.exception))
    
    def test_validate_structure_missing_version(self):
        """Test validation rejects missing version"""
        with self.assertRaises(ValueError) as cm:
            self.loader._validate_structure({'pages': []})
        
        self.assertIn('version', str(cm.exception))
    
    def test_validate_structure_missing_pages(self):
        """Test validation rejects missing pages"""
        with self.assertRaises(ValueError) as cm:
            self.loader._validate_structure({'version': '1.0.0'})
        
        self.assertIn('pages', str(cm.exception))
    
    def test_validate_structure_pages_not_array(self):
        """Test validation rejects pages as non-array"""
        with self.assertRaises(ValueError) as cm:
            self.loader._validate_structure({
                'version': '1.0.0',
                'pages': {}
            })
        
        self.assertIn('array', str(cm.exception))
    
    def test_validate_structure_empty_pages(self):
        """Test validation rejects empty pages array"""
        with self.assertRaises(ValueError) as cm:
            self.loader._validate_structure({
                'version': '1.0.0',
                'pages': []
            })
        
        self.assertIn('at least one page', str(cm.exception))


class TestIDValidation(unittest.TestCase):
    """Test ID uniqueness validation"""
    
    def setUp(self):
        """Create loader"""
        self.loader = DocumentLoader()
    
    def test_validate_unique_ids_valid_document(self):
        """Test validation passes for valid document"""
        doc = Document()
        page = Page('page001', 'Main')
        doc.add_page(page)
        
        sw = Switch('sw00001', 'page001')
        led = Indicator('led0001', 'page001')
        page.add_component(sw)
        page.add_component(led)
        
        # Should not raise
        self.loader._validate_unique_ids(doc)
    
    def test_validate_duplicate_page_ids(self):
        """Test validation catches duplicate page IDs"""
        doc = Document()
        page1 = Page('page001', 'Page 1')
        page2 = Page('page001', 'Page 2')  # Duplicate ID
        doc.add_page(page1)
        # Manually add to bypass Document's duplicate checking
        doc.pages['page001_dup'] = page2
        
        with self.assertRaises(ValueError) as cm:
            self.loader._validate_unique_ids(doc)
        
        self.assertIn('Duplicate IDs', str(cm.exception))
        self.assertIn('page001', str(cm.exception))
    
    def test_validate_duplicate_component_ids(self):
        """Test validation catches duplicate component IDs"""
        # Create document with duplicate manually
        doc = Document()
        page = Page('page001', 'Main')
        doc.add_page(page)
        
        sw1 = Switch('comp001', 'page001')
        sw2 = Switch('comp001', 'page001')  # Duplicate ID
        page.add_component(sw1)
        # Manually add to bypass Page's duplicate checking
        page.components['comp001_dup'] = sw2
        
        with self.assertRaises(ValueError) as cm:
            self.loader._validate_unique_ids(doc)
        
        self.assertIn('Duplicate IDs', str(cm.exception))
        self.assertIn('comp001', str(cm.exception))


class TestFileOperations(unittest.TestCase):
    """Test file save/load operations"""
    
    def setUp(self):
        """Create loader and temp directory"""
        self.loader = DocumentLoader()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up temp directory"""
        self.temp_dir.cleanup()
    
    def test_save_and_load_file(self):
        """Test saving and loading document from file"""
        # Create document
        doc = Document()
        doc.metadata = {
            'title': 'Test Circuit',
            'author': 'Test Author'
        }
        page = Page('page001', 'Main')
        doc.add_page(page)
        
        sw = Switch('sw00001', 'page001')
        sw.position = (100, 100)
        page.add_component(sw)
        
        # Save to file
        filepath = self.temp_path / 'test.rsim'
        self.loader.save_to_file(doc, str(filepath))
        
        # Verify file exists
        self.assertTrue(filepath.exists())
        
        # Load back
        loaded = self.loader.load_from_file(str(filepath))
        
        # Verify contents
        self.assertEqual(loaded.metadata['title'], 'Test Circuit')
        self.assertEqual(len(loaded.pages), 1)
        
        loaded_page = list(loaded.pages.values())[0]
        self.assertEqual(len(loaded_page.components), 1)
        
        loaded_sw = list(loaded_page.components.values())[0]
        self.assertEqual(loaded_sw.component_type, 'Switch')
        self.assertEqual(loaded_sw.position, (100, 100))
    
    def test_load_nonexistent_file(self):
        """Test loading file that doesn't exist"""
        with self.assertRaises(FileNotFoundError):
            self.loader.load_from_file('nonexistent.rsim')
    
    def test_convenience_functions(self):
        """Test convenience load/save functions"""
        # Create document
        doc = Document()
        page = Page('page001', 'Main')
        doc.add_page(page)
        
        # Save using convenience function
        filepath = self.temp_path / 'convenience.rsim'
        save_document(doc, str(filepath))
        
        self.assertTrue(filepath.exists())
        
        # Load using convenience function
        loaded = load_document(str(filepath))
        
        self.assertEqual(len(loaded.pages), 1)


class TestRoundTripSerialization(unittest.TestCase):
    """Test complete round-trip: create → save → load → verify"""
    
    def setUp(self):
        """Create temp directory"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up"""
        self.temp_dir.cleanup()
    
    def test_round_trip_simple_circuit(self):
        """Test round trip for simple switch→LED circuit"""
        from core.wire import Wire
        
        # Create document
        doc = Document()
        doc.metadata = {
            'title': 'Simple Circuit',
            'description': 'Switch and LED test'
        }
        
        page = Page('page001', 'Main')
        doc.add_page(page)
        
        # Create switch
        sw = Switch('sw00001', 'page001')
        sw.position = (100, 200)
        sw.set_property('label', 'SW1')
        sw.set_property('mode', 'toggle')
        page.add_component(sw)
        
        # Create LED
        led = Indicator('led0001', 'page001')
        led.position = (300, 200)
        led.set_property('label', 'LED1')
        led.set_property('color', 'red')
        page.add_component(led)
        
        # Create wire
        sw_tab = list(list(sw.pins.values())[0].tabs.values())[0]
        led_tab = list(list(led.pins.values())[0].tabs.values())[0]
        wire = Wire('wire001', sw_tab.tab_id, led_tab.tab_id)
        page.add_wire(wire)
        
        # Save
        filepath = self.temp_path / 'simple.rsim'
        save_document(doc, str(filepath))
        
        # Load
        loaded = load_document(str(filepath))
        
        # Verify metadata
        self.assertEqual(loaded.metadata['title'], 'Simple Circuit')
        self.assertEqual(loaded.metadata['description'], 'Switch and LED test')
        
        # Verify structure
        self.assertEqual(len(loaded.pages), 1)
        loaded_page = list(loaded.pages.values())[0]
        self.assertEqual(loaded_page.page_id, 'page001')
        self.assertEqual(loaded_page.name, 'Main')
        
        # Verify components
        self.assertEqual(len(loaded_page.components), 2)
        
        loaded_sw = loaded_page.get_component('sw00001')
        self.assertIsNotNone(loaded_sw)
        self.assertEqual(loaded_sw.component_type, 'Switch')
        self.assertEqual(loaded_sw.position, (100, 200))
        self.assertEqual(loaded_sw.get_property('label'), 'SW1')
        self.assertEqual(loaded_sw.get_property('mode'), 'toggle')
        
        loaded_led = loaded_page.get_component('led0001')
        self.assertIsNotNone(loaded_led)
        self.assertEqual(loaded_led.component_type, 'Indicator')
        self.assertEqual(loaded_led.position, (300, 200))
        self.assertEqual(loaded_led.get_property('label'), 'LED1')
        self.assertEqual(loaded_led.get_property('color'), 'red')
        
        # Verify wires
        self.assertEqual(len(loaded_page.wires), 1)
        loaded_wire = list(loaded_page.wires.values())[0]
        self.assertEqual(loaded_wire.wire_id, 'wire001')
    
    def test_round_trip_with_metadata(self):
        """Test round trip preserves all metadata"""
        doc = Document()
        doc.metadata = {
            'title': 'Test Title',
            'author': 'Test Author',
            'description': 'Test Description',
            'created': '2024-01-15T10:30:00Z',
            'modified': '2024-01-16T15:45:00Z',
            'custom_field': 'Custom Value'
        }
        
        page = Page('page001', 'Main')
        doc.add_page(page)
        
        # Save and load
        filepath = self.temp_path / 'metadata.rsim'
        save_document(doc, str(filepath))
        loaded = load_document(str(filepath))
        
        # Verify all metadata preserved
        self.assertEqual(loaded.metadata['title'], 'Test Title')
        self.assertEqual(loaded.metadata['author'], 'Test Author')
        self.assertEqual(loaded.metadata['description'], 'Test Description')
        self.assertEqual(loaded.metadata['created'], '2024-01-15T10:30:00Z')
        self.assertEqual(loaded.metadata['modified'], '2024-01-16T15:45:00Z')
        self.assertEqual(loaded.metadata['custom_field'], 'Custom Value')


class TestExampleFilesLoading(unittest.TestCase):
    """Test loading all example files"""
    
    def setUp(self):
        """Create loader"""
        self.loader = DocumentLoader()
    
    def test_load_all_valid_examples(self):
        """Test that all valid example files load successfully"""
        examples = [
            ('SIMPLE_SWITCH_LED', SIMPLE_SWITCH_LED),
            ('RELAY_CIRCUIT', RELAY_CIRCUIT),
            ('CROSS_PAGE_LINKS', CROSS_PAGE_LINKS),
            ('WIRE_WITH_JUNCTION', WIRE_WITH_JUNCTION)
        ]
        
        for name, json_str in examples:
            with self.subTest(example=name):
                doc = self.loader.load_from_string(json_str)
                self.assertIsNotNone(doc)
                self.assertGreater(len(doc.pages), 0)


if __name__ == '__main__':
    unittest.main()
