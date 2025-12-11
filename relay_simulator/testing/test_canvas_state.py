"""
Tests for Canvas State Management (Phase 10.2)

Tests canvas state persistence including:
- Page canvas state fields
- Canvas state save/restore
- State persistence across file operations
- State switching between tabs
"""

import unittest
import tkinter as tk
import tempfile
import os
from pathlib import Path

from core.page import Page
from core.document import Document
from gui.canvas import DesignCanvas
from fileio.document_loader import DocumentLoader


class TestPageCanvasState(unittest.TestCase):
    """Tests for Page canvas state fields."""
    
    def test_page_has_canvas_state(self):
        """Test that Page has canvas state fields."""
        page = Page("page_001", "Test Page")
        
        self.assertTrue(hasattr(page, 'canvas_x'))
        self.assertTrue(hasattr(page, 'canvas_y'))
        self.assertTrue(hasattr(page, 'canvas_zoom'))
    
    def test_page_canvas_state_defaults(self):
        """Test canvas state default values."""
        page = Page("page_001", "Test Page")
        
        self.assertEqual(page.canvas_x, 0.0)
        self.assertEqual(page.canvas_y, 0.0)
        self.assertEqual(page.canvas_zoom, 1.0)
    
    def test_page_canvas_state_mutable(self):
        """Test that canvas state can be changed."""
        page = Page("page_001", "Test Page")
        
        page.canvas_x = 100.5
        page.canvas_y = 200.5
        page.canvas_zoom = 1.5
        
        self.assertEqual(page.canvas_x, 100.5)
        self.assertEqual(page.canvas_y, 200.5)
        self.assertEqual(page.canvas_zoom, 1.5)
    
    def test_page_to_dict_includes_canvas_state(self):
        """Test that to_dict includes canvas state."""
        page = Page("page_001", "Test Page")
        page.canvas_x = 150.0
        page.canvas_y = 250.0
        page.canvas_zoom = 2.0
        
        data = page.to_dict()
        
        self.assertIn('canvas_x', data)
        self.assertIn('canvas_y', data)
        self.assertIn('canvas_zoom', data)
        self.assertEqual(data['canvas_x'], 150.0)
        self.assertEqual(data['canvas_y'], 250.0)
        self.assertEqual(data['canvas_zoom'], 2.0)
    
    def test_page_from_dict_restores_canvas_state(self):
        """Test that from_dict restores canvas state."""
        data = {
            'page_id': 'page_001',
            'name': 'Test Page',
            'canvas_x': 300.0,
            'canvas_y': 400.0,
            'canvas_zoom': 1.5
        }
        
        page = Page.from_dict(data)
        
        self.assertEqual(page.canvas_x, 300.0)
        self.assertEqual(page.canvas_y, 400.0)
        self.assertEqual(page.canvas_zoom, 1.5)
    
    def test_page_from_dict_defaults_missing_canvas_state(self):
        """Test that from_dict uses defaults for missing canvas state."""
        # Simulates loading older files without canvas state
        data = {
            'page_id': 'page_001',
            'name': 'Test Page'
        }
        
        page = Page.from_dict(data)
        
        self.assertEqual(page.canvas_x, 0.0)
        self.assertEqual(page.canvas_y, 0.0)
        self.assertEqual(page.canvas_zoom, 1.0)


class TestCanvasStateSaveRestore(unittest.TestCase):
    """Tests for canvas state save/restore functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        # Let widgets render
        self.root.update()
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_save_canvas_state(self):
        """Test saving canvas state."""
        # Modify canvas state
        self.canvas.zoom_in()
        
        # Save state
        canvas_x, canvas_y, zoom = self.canvas.save_canvas_state()
        
        # Should return valid values
        self.assertIsInstance(canvas_x, float)
        self.assertIsInstance(canvas_y, float)
        self.assertIsInstance(zoom, float)
        self.assertGreater(zoom, 1.0)  # Zoomed in
    
    def test_restore_canvas_state(self):
        """Test restoring canvas state."""
        # Set a specific state
        target_zoom = 1.5
        
        # Restore state
        self.canvas.restore_canvas_state(100.0, 200.0, target_zoom)
        
        # Zoom should be restored
        self.assertAlmostEqual(self.canvas.get_zoom_level(), target_zoom, places=1)
    
    def test_save_restore_roundtrip(self):
        """Test save/restore roundtrip preserves state."""
        # Set canvas to known state
        self.canvas.zoom_in()
        self.canvas.zoom_in()
        
        # Save state
        saved_x, saved_y, saved_zoom = self.canvas.save_canvas_state()
        
        # Change state
        self.canvas.zoom_out()
        
        # Restore saved state
        self.canvas.restore_canvas_state(saved_x, saved_y, saved_zoom)
        
        # Should match saved zoom
        self.assertAlmostEqual(self.canvas.get_zoom_level(), saved_zoom, places=2)


class TestCanvasStatePersistence(unittest.TestCase):
    """Tests for canvas state persistence to files."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = DocumentLoader()
        
    def tearDown(self):
        """Clean up temp files."""
        # Clean up temp directory
        for file in Path(self.temp_dir).glob("*.rsim"):
            file.unlink()
        os.rmdir(self.temp_dir)
    
    def test_canvas_state_saved_to_file(self):
        """Test that canvas state is saved to .rsim file."""
        # Create document with custom canvas state
        doc = Document()
        page = doc.create_page("Test Page")
        page.canvas_x = 500.0
        page.canvas_y = 600.0
        page.canvas_zoom = 2.5
        
        # Save to file
        filepath = os.path.join(self.temp_dir, "test.rsim")
        self.loader.save_to_file(doc, filepath)
        
        # Load file and check state
        loaded_doc = self.loader.load_from_file(filepath)
        loaded_page = loaded_doc.get_all_pages()[0]
        
        self.assertEqual(loaded_page.canvas_x, 500.0)
        self.assertEqual(loaded_page.canvas_y, 600.0)
        self.assertEqual(loaded_page.canvas_zoom, 2.5)
    
    def test_canvas_state_preserved_across_save_load(self):
        """Test canvas state preserved across multiple save/load cycles."""
        # Create document
        doc = Document()
        page = doc.create_page("Test Page")
        page.canvas_x = 123.45
        page.canvas_y = 678.90
        page.canvas_zoom = 1.75
        
        filepath = os.path.join(self.temp_dir, "test.rsim")
        
        # Save and load multiple times
        for _ in range(3):
            self.loader.save_to_file(doc, filepath)
            doc = self.loader.load_from_file(filepath)
        
        # State should still match
        final_page = doc.get_all_pages()[0]
        self.assertAlmostEqual(final_page.canvas_x, 123.45, places=2)
        self.assertAlmostEqual(final_page.canvas_y, 678.90, places=2)
        self.assertAlmostEqual(final_page.canvas_zoom, 1.75, places=2)
    
    def test_multiple_pages_have_independent_canvas_state(self):
        """Test that each page has independent canvas state."""
        doc = Document()
        
        page1 = doc.create_page("Page 1")
        page1.canvas_x = 100.0
        page1.canvas_y = 200.0
        page1.canvas_zoom = 1.0
        
        page2 = doc.create_page("Page 2")
        page2.canvas_x = 300.0
        page2.canvas_y = 400.0
        page2.canvas_zoom = 2.0
        
        # Save and load
        filepath = os.path.join(self.temp_dir, "test.rsim")
        self.loader.save_to_file(doc, filepath)
        loaded_doc = self.loader.load_from_file(filepath)
        
        pages = loaded_doc.get_all_pages()
        self.assertEqual(len(pages), 2)
        
        # Each page should have its own state
        # Note: Order might not be preserved, so check both possibilities
        states = [(p.canvas_x, p.canvas_y, p.canvas_zoom) for p in pages]
        self.assertIn((100.0, 200.0, 1.0), states)
        self.assertIn((300.0, 400.0, 2.0), states)


class TestCanvasStateIntegration(unittest.TestCase):
    """Integration tests for canvas state in full workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = DocumentLoader()
        
    def tearDown(self):
        """Clean up temp files."""
        for file in Path(self.temp_dir).glob("*.rsim"):
            file.unlink()
        os.rmdir(self.temp_dir)
    
    def test_new_page_has_default_canvas_state(self):
        """Test that newly created pages have default canvas state."""
        doc = Document()
        page = doc.create_page("New Page")
        
        self.assertEqual(page.canvas_x, 0.0)
        self.assertEqual(page.canvas_y, 0.0)
        self.assertEqual(page.canvas_zoom, 1.0)
    
    def test_canvas_state_in_document_serialization(self):
        """Test canvas state included in full document serialization."""
        doc = Document()
        page = doc.create_page("Test Page")
        page.canvas_zoom = 3.0
        
        # Serialize document
        doc_dict = doc.to_dict()
        
        # Canvas state should be in page data (pages is a list)
        page_data = doc_dict['pages'][0]  # First page in list
        
        self.assertEqual(page_data['canvas_zoom'], 3.0)


if __name__ == '__main__':
    unittest.main()
