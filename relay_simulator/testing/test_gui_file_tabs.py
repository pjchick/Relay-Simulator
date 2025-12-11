"""
Tests for File Tab System (Phase 9.1)

Tests FileTabBar class for multi-document support including:
- Tab creation and management
- Tab switching and activation
- Modified state tracking
- Tab closing with confirmation
- Simulation state blocking
"""

import unittest
import tkinter as tk
from gui.file_tabs import FileTabBar, FileTab
from core.document import Document


class TestFileTab(unittest.TestCase):
    """Tests for FileTab class."""
    
    def test_file_tab_creation(self):
        """Test creating a file tab."""
        tab = FileTab("tab1", "test.rsim", "/path/to/test.rsim")
        self.assertEqual(tab.tab_id, "tab1")
        self.assertEqual(tab.filename, "test.rsim")
        self.assertEqual(tab.filepath, "/path/to/test.rsim")
        self.assertFalse(tab.is_modified)
        self.assertIsNone(tab.document)
    
    def test_file_tab_untitled(self):
        """Test creating untitled tab."""
        tab = FileTab("tab1", "Untitled-1", None)
        self.assertEqual(tab.filename, "Untitled-1")
        self.assertIsNone(tab.filepath)
    
    def test_display_name_unmodified(self):
        """Test display name without modifications."""
        tab = FileTab("tab1", "test.rsim")
        self.assertEqual(tab.get_display_name(), "test.rsim")
    
    def test_display_name_modified(self):
        """Test display name with modifications."""
        tab = FileTab("tab1", "test.rsim")
        tab.set_modified(True)
        self.assertEqual(tab.get_display_name(), "test.rsim *")
    
    def test_set_modified(self):
        """Test setting modified state."""
        tab = FileTab("tab1", "test.rsim")
        self.assertFalse(tab.is_modified)
        
        tab.set_modified(True)
        self.assertTrue(tab.is_modified)
        
        tab.set_modified(False)
        self.assertFalse(tab.is_modified)


class TestFileTabBar(unittest.TestCase):
    """Tests for FileTabBar class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_create_file_tab_bar(self):
        """Test creating file tab bar."""
        tab_bar = FileTabBar(self.root)
        self.assertIsNotNone(tab_bar.frame)
        self.assertEqual(tab_bar.get_tab_count(), 0)
        self.assertIsNone(tab_bar.get_active_tab())
    
    def test_add_tab(self):
        """Test adding a tab."""
        tab_bar = FileTabBar(self.root)
        doc = Document()
        
        tab_id = tab_bar.add_tab("test.rsim", "/path/to/test.rsim", doc)
        
        self.assertEqual(tab_bar.get_tab_count(), 1)
        self.assertIsNotNone(tab_bar.get_tab(tab_id))
        
        tab = tab_bar.get_tab(tab_id)
        self.assertEqual(tab.filename, "test.rsim")
        self.assertEqual(tab.filepath, "/path/to/test.rsim")
        self.assertIs(tab.document, doc)
    
    def test_add_untitled_tab(self):
        """Test adding untitled tab."""
        tab_bar = FileTabBar(self.root)
        
        tab_id1 = tab_bar.add_untitled_tab()
        tab_id2 = tab_bar.add_untitled_tab()
        
        tab1 = tab_bar.get_tab(tab_id1)
        tab2 = tab_bar.get_tab(tab_id2)
        
        self.assertEqual(tab1.filename, "Untitled-1")
        self.assertEqual(tab2.filename, "Untitled-2")
        self.assertIsNone(tab1.filepath)
        self.assertIsNone(tab2.filepath)
    
    def test_first_tab_becomes_active(self):
        """Test that first tab becomes active automatically."""
        tab_bar = FileTabBar(self.root)
        
        tab_id = tab_bar.add_tab("test.rsim")
        
        active_tab = tab_bar.get_active_tab()
        self.assertIsNotNone(active_tab)
        self.assertEqual(active_tab.tab_id, tab_id)
    
    def test_set_active_tab(self):
        """Test setting active tab."""
        tab_bar = FileTabBar(self.root)
        
        tab_id1 = tab_bar.add_tab("file1.rsim")
        tab_id2 = tab_bar.add_tab("file2.rsim")
        
        # First tab is active
        self.assertEqual(tab_bar.get_active_tab().tab_id, tab_id1)
        
        # Switch to second tab
        tab_bar.set_active_tab(tab_id2)
        self.assertEqual(tab_bar.get_active_tab().tab_id, tab_id2)
    
    def test_tab_switch_callback(self):
        """Test tab switch callback."""
        tab_bar = FileTabBar(self.root)
        
        switched_to = []
        tab_bar.on_tab_switch = lambda tid: switched_to.append(tid)
        
        tab_id1 = tab_bar.add_tab("file1.rsim")
        tab_id2 = tab_bar.add_tab("file2.rsim")
        
        # Switch should trigger callback
        tab_bar.set_active_tab(tab_id2)
        
        self.assertIn(tab_id2, switched_to)
    
    def test_tab_switch_blocked_during_simulation(self):
        """Test that tab switching is blocked during simulation."""
        tab_bar = FileTabBar(self.root)
        
        tab_id1 = tab_bar.add_tab("file1.rsim")
        tab_id2 = tab_bar.add_tab("file2.rsim")
        
        # Start simulation
        tab_bar.set_simulation_running(True)
        
        # Try to switch (should be blocked)
        tab_bar.set_active_tab(tab_id2)
        
        # Should still be on tab1
        self.assertEqual(tab_bar.get_active_tab().tab_id, tab_id1)
        
        # Stop simulation and try again
        tab_bar.set_simulation_running(False)
        tab_bar.set_active_tab(tab_id2)
        
        # Now should switch
        self.assertEqual(tab_bar.get_active_tab().tab_id, tab_id2)
    
    def test_close_tab(self):
        """Test closing a tab."""
        tab_bar = FileTabBar(self.root)
        
        tab_id1 = tab_bar.add_tab("file1.rsim")
        tab_id2 = tab_bar.add_tab("file2.rsim")
        
        self.assertEqual(tab_bar.get_tab_count(), 2)
        
        # Close first tab
        result = tab_bar.close_tab(tab_id1)
        
        self.assertTrue(result)
        self.assertEqual(tab_bar.get_tab_count(), 1)
        self.assertIsNone(tab_bar.get_tab(tab_id1))
        self.assertIsNotNone(tab_bar.get_tab(tab_id2))
    
    def test_close_tab_callback(self):
        """Test tab close callback."""
        tab_bar = FileTabBar(self.root)
        
        closed_tabs = []
        tab_bar.on_tab_close = lambda tid: (closed_tabs.append(tid), True)[1]
        
        tab_id = tab_bar.add_tab("file1.rsim")
        tab_bar.close_tab(tab_id)
        
        self.assertIn(tab_id, closed_tabs)
    
    def test_close_tab_callback_cancel(self):
        """Test cancelling tab close via callback."""
        tab_bar = FileTabBar(self.root)
        
        # Callback returns False (cancel close)
        tab_bar.on_tab_close = lambda tid: False
        
        tab_id = tab_bar.add_tab("file1.rsim")
        result = tab_bar.close_tab(tab_id)
        
        self.assertFalse(result)
        self.assertEqual(tab_bar.get_tab_count(), 1)  # Tab still there
    
    def test_close_active_tab_activates_another(self):
        """Test that closing active tab activates another tab."""
        tab_bar = FileTabBar(self.root)
        
        tab_id1 = tab_bar.add_tab("file1.rsim")
        tab_id2 = tab_bar.add_tab("file2.rsim")
        tab_id3 = tab_bar.add_tab("file3.rsim")
        
        # Make tab2 active
        tab_bar.set_active_tab(tab_id2)
        
        # Close active tab
        tab_bar.close_tab(tab_id2)
        
        # Should activate another tab
        active = tab_bar.get_active_tab()
        self.assertIsNotNone(active)
        self.assertIn(active.tab_id, [tab_id1, tab_id3])
    
    def test_close_all_tabs(self):
        """Test closing all tabs."""
        tab_bar = FileTabBar(self.root)
        
        tab_bar.add_tab("file1.rsim")
        tab_bar.add_tab("file2.rsim")
        
        # Close all tabs
        for tab in tab_bar.get_all_tabs().copy():
            tab_bar.close_tab(tab.tab_id)
        
        self.assertEqual(tab_bar.get_tab_count(), 0)
        self.assertIsNone(tab_bar.get_active_tab())
    
    def test_set_tab_modified(self):
        """Test setting tab modified state."""
        tab_bar = FileTabBar(self.root)
        
        tab_id = tab_bar.add_tab("test.rsim")
        tab = tab_bar.get_tab(tab_id)
        
        self.assertFalse(tab.is_modified)
        
        tab_bar.set_tab_modified(tab_id, True)
        self.assertTrue(tab.is_modified)
        
        tab_bar.set_tab_modified(tab_id, False)
        self.assertFalse(tab.is_modified)
    
    def test_tab_modified_callback(self):
        """Test tab modified callback."""
        tab_bar = FileTabBar(self.root)
        
        modified_events = []
        tab_bar.on_tab_modified = lambda tid, mod: modified_events.append((tid, mod))
        
        tab_id = tab_bar.add_tab("test.rsim")
        
        tab_bar.set_tab_modified(tab_id, True)
        tab_bar.set_tab_modified(tab_id, False)
        
        self.assertEqual(len(modified_events), 2)
        self.assertEqual(modified_events[0], (tab_id, True))
        self.assertEqual(modified_events[1], (tab_id, False))
    
    def test_set_tab_filepath(self):
        """Test setting tab filepath (Save As)."""
        tab_bar = FileTabBar(self.root)
        
        tab_id = tab_bar.add_untitled_tab()
        tab = tab_bar.get_tab(tab_id)
        
        self.assertEqual(tab.filename, "Untitled-1")
        self.assertIsNone(tab.filepath)
        
        tab_bar.set_tab_filepath(tab_id, "/path/to/saved.rsim", "saved.rsim")
        
        self.assertEqual(tab.filename, "saved.rsim")
        self.assertEqual(tab.filepath, "/path/to/saved.rsim")
    
    def test_get_tab_by_filepath(self):
        """Test finding tab by filepath."""
        tab_bar = FileTabBar(self.root)
        
        tab_id1 = tab_bar.add_tab("file1.rsim", "/path/to/file1.rsim")
        tab_id2 = tab_bar.add_tab("file2.rsim", "/path/to/file2.rsim")
        
        tab = tab_bar.get_tab_by_filepath("/path/to/file1.rsim")
        self.assertIsNotNone(tab)
        self.assertEqual(tab.tab_id, tab_id1)
        
        tab = tab_bar.get_tab_by_filepath("/nonexistent.rsim")
        self.assertIsNone(tab)
    
    def test_has_unsaved_changes(self):
        """Test checking for unsaved changes across all tabs."""
        tab_bar = FileTabBar(self.root)
        
        tab_id1 = tab_bar.add_tab("file1.rsim")
        tab_id2 = tab_bar.add_tab("file2.rsim")
        
        self.assertFalse(tab_bar.has_unsaved_changes())
        
        # Modify one tab
        tab_bar.set_tab_modified(tab_id1, True)
        self.assertTrue(tab_bar.has_unsaved_changes())
        
        # Modify second tab too
        tab_bar.set_tab_modified(tab_id2, True)
        self.assertTrue(tab_bar.has_unsaved_changes())
        
        # Unmodify first tab
        tab_bar.set_tab_modified(tab_id1, False)
        self.assertTrue(tab_bar.has_unsaved_changes())  # Still true (tab2 modified)
        
        # Unmodify all
        tab_bar.set_tab_modified(tab_id2, False)
        self.assertFalse(tab_bar.has_unsaved_changes())
    
    def test_get_all_tabs(self):
        """Test getting all tabs in order."""
        tab_bar = FileTabBar(self.root)
        
        tab_id1 = tab_bar.add_tab("file1.rsim")
        tab_id2 = tab_bar.add_tab("file2.rsim")
        tab_id3 = tab_bar.add_tab("file3.rsim")
        
        all_tabs = tab_bar.get_all_tabs()
        
        self.assertEqual(len(all_tabs), 3)
        self.assertEqual(all_tabs[0].tab_id, tab_id1)
        self.assertEqual(all_tabs[1].tab_id, tab_id2)
        self.assertEqual(all_tabs[2].tab_id, tab_id3)


class TestFileTabBarIntegration(unittest.TestCase):
    """Integration tests for FileTabBar with Document."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_tab_with_document(self):
        """Test tab with associated document."""
        tab_bar = FileTabBar(self.root)
        doc = Document()
        doc.create_page("Page 1")
        
        tab_id = tab_bar.add_tab("test.rsim", document=doc)
        tab = tab_bar.get_tab(tab_id)
        
        self.assertIs(tab.document, doc)
        self.assertEqual(tab.document.get_page_count(), 1)
    
    def test_multiple_documents(self):
        """Test multiple tabs with different documents."""
        tab_bar = FileTabBar(self.root)
        
        doc1 = Document()
        doc1.create_page("Doc1 Page1")
        
        doc2 = Document()
        doc2.create_page("Doc2 Page1")
        doc2.create_page("Doc2 Page2")
        
        tab_id1 = tab_bar.add_tab("doc1.rsim", document=doc1)
        tab_id2 = tab_bar.add_tab("doc2.rsim", document=doc2)
        
        # Check documents are separate
        tab1 = tab_bar.get_tab(tab_id1)
        tab2 = tab_bar.get_tab(tab_id2)
        
        self.assertEqual(tab1.document.get_page_count(), 1)
        self.assertEqual(tab2.document.get_page_count(), 2)


if __name__ == '__main__':
    unittest.main()
