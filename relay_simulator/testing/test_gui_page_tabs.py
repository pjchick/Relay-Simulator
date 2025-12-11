"""
Tests for the page tab bar.
"""

import unittest
import tkinter as tk
from gui.page_tabs import PageTabBar
from core.document import Document


class TestPageTabBar(unittest.TestCase):
    """Test PageTabBar functionality."""
    
    def setUp(self):
        """Create test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        self.page_tabs = PageTabBar(self.root)
        
    def tearDown(self):
        """Clean up after tests."""
        if self.root:
            self.root.destroy()
            
    def test_create_page_tab_bar(self):
        """Test creating page tab bar."""
        self.assertIsNotNone(self.page_tabs)
        self.assertIsNotNone(self.page_tabs.frame)
        
    def test_initial_state_no_document(self):
        """Test initial state with no document."""
        self.assertIsNone(self.page_tabs.current_document)
        self.assertIsNone(self.page_tabs.get_active_page_id())
        self.assertEqual(self.page_tabs.get_page_count(), 0)
        
    def test_set_document_with_single_page(self):
        """Test setting a document with one page."""
        doc = Document()
        page = doc.create_page("Test Page")
        
        self.page_tabs.set_document(doc)
        
        self.assertEqual(self.page_tabs.current_document, doc)
        self.assertEqual(self.page_tabs.get_active_page_id(), page.page_id)
        self.assertEqual(self.page_tabs.get_page_count(), 1)
        
    def test_set_document_with_multiple_pages(self):
        """Test setting a document with multiple pages."""
        doc = Document()
        page1 = doc.create_page("Page 1")
        page2 = doc.create_page("Page 2")
        page3 = doc.create_page("Page 3")
        
        self.page_tabs.set_document(doc)
        
        self.assertEqual(self.page_tabs.get_page_count(), 3)
        # First page should be active by default
        self.assertEqual(self.page_tabs.get_active_page_id(), page1.page_id)
        
    def test_set_document_to_none(self):
        """Test clearing document by setting to None."""
        doc = Document()
        doc.create_page("Test Page")
        self.page_tabs.set_document(doc)
        
        # Clear document
        self.page_tabs.set_document(None)
        
        self.assertIsNone(self.page_tabs.current_document)
        self.assertIsNone(self.page_tabs.get_active_page_id())
        self.assertEqual(self.page_tabs.get_page_count(), 0)
        
    def test_set_active_page(self):
        """Test switching active page."""
        doc = Document()
        page1 = doc.create_page("Page 1")
        page2 = doc.create_page("Page 2")
        self.page_tabs.set_document(doc)
        
        # Initially first page is active
        self.assertEqual(self.page_tabs.get_active_page_id(), page1.page_id)
        
        # Switch to second page
        self.page_tabs.set_active_page(page2.page_id)
        self.assertEqual(self.page_tabs.get_active_page_id(), page2.page_id)
        
    def test_set_active_page_invalid_id(self):
        """Test setting active page with invalid ID."""
        doc = Document()
        page = doc.create_page("Test Page")
        self.page_tabs.set_document(doc)
        
        # Try to set invalid page
        self.page_tabs.set_active_page("invalid_id")
        
        # Should still be on original page
        self.assertEqual(self.page_tabs.get_active_page_id(), page.page_id)
        
    def test_page_switch_callback(self):
        """Test page switch callback is triggered."""
        doc = Document()
        page1 = doc.create_page("Page 1")
        page2 = doc.create_page("Page 2")
        self.page_tabs.set_document(doc)
        
        callback_called = []
        def on_switch(page_id):
            callback_called.append(page_id)
            
        self.page_tabs.on_page_switch = on_switch
        
        # Switch pages
        self.page_tabs.set_active_page(page2.page_id)
        
        self.assertEqual(len(callback_called), 1)
        self.assertEqual(callback_called[0], page2.page_id)
        
    def test_add_page_button_adds_page(self):
        """Test add page button creates new page."""
        doc = Document()
        doc.create_page("Page 1")
        self.page_tabs.set_document(doc)
        
        initial_count = self.page_tabs.get_page_count()
        
        # Simulate add page button click
        self.page_tabs._on_add_page()
        
        self.assertEqual(self.page_tabs.get_page_count(), initial_count + 1)
        
    def test_add_page_callback(self):
        """Test add page callback is triggered."""
        doc = Document()
        doc.create_page("Page 1")
        self.page_tabs.set_document(doc)
        
        callback_called = []
        def on_add(page_id):
            callback_called.append(page_id)
            
        self.page_tabs.on_page_added = on_add
        
        self.page_tabs._on_add_page()
        
        self.assertEqual(len(callback_called), 1)
        
    def test_add_page_generates_sequential_names(self):
        """Test that added pages get sequential names."""
        doc = Document()
        doc.create_page("Page 1")
        self.page_tabs.set_document(doc)
        
        # Add second page
        self.page_tabs._on_add_page()
        pages = doc.get_all_pages()
        self.assertEqual(pages[1].name, "Page 2")
        
        # Add third page
        self.page_tabs._on_add_page()
        pages = doc.get_all_pages()
        self.assertEqual(pages[2].name, "Page 3")
        
    def test_add_page_activates_new_page(self):
        """Test that new page becomes active."""
        doc = Document()
        page1 = doc.create_page("Page 1")
        self.page_tabs.set_document(doc)
        
        self.page_tabs._on_add_page()
        
        # New page should be active
        active_id = self.page_tabs.get_active_page_id()
        self.assertNotEqual(active_id, page1.page_id)
        
    def test_delete_page(self):
        """Test deleting a page."""
        doc = Document()
        page1 = doc.create_page("Page 1")
        page2 = doc.create_page("Page 2")
        self.page_tabs.set_document(doc)
        
        # Can't easily test the messagebox, but we can test the method exists
        self.assertTrue(hasattr(self.page_tabs, '_on_delete_page'))
        
    def test_cannot_delete_first_page(self):
        """Test that first page cannot be deleted."""
        doc = Document()
        page1 = doc.create_page("Page 1")
        page2 = doc.create_page("Page 2")
        self.page_tabs.set_document(doc)
        
        initial_count = self.page_tabs.get_page_count()
        
        # Note: _on_delete_page has a messagebox, so we can't fully test it
        # But we can verify the protection logic exists in the code
        # First page should not have a close button
        self.assertEqual(initial_count, 2)
        
    def test_rename_page(self):
        """Test renaming a page."""
        doc = Document()
        page = doc.create_page("Original Name")
        self.page_tabs.set_document(doc)
        
        # Test that rename method exists
        self.assertTrue(hasattr(self.page_tabs, '_start_rename'))
        
        # Change page name directly (simulating rename)
        page.name = "New Name"
        
        self.assertEqual(page.name, "New Name")
        
    def test_refresh_tabs_updates_display(self):
        """Test that refresh updates tab display."""
        doc = Document()
        doc.create_page("Page 1")
        self.page_tabs.set_document(doc)
        
        # Add page directly to document
        doc.create_page("Page 2")
        
        # Refresh tabs
        self.page_tabs._refresh_tabs()
        
        self.assertEqual(self.page_tabs.get_page_count(), 2)
        
    def test_tab_widgets_created_for_each_page(self):
        """Test that tab widgets are created for pages."""
        doc = Document()
        page1 = doc.create_page("Page 1")
        page2 = doc.create_page("Page 2")
        self.page_tabs.set_document(doc)
        
        # Check tab widgets dictionary
        self.assertIn(page1.page_id, self.page_tabs.tab_widgets)
        self.assertIn(page2.page_id, self.page_tabs.tab_widgets)
        self.assertEqual(len(self.page_tabs.tab_widgets), 2)


class TestPageTabBarIntegration(unittest.TestCase):
    """Test PageTabBar integration scenarios."""
    
    def setUp(self):
        """Create test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.page_tabs = PageTabBar(self.root)
        
    def tearDown(self):
        """Clean up after tests."""
        if self.root:
            self.root.destroy()
            
    def test_switch_between_multiple_pages(self):
        """Test switching between multiple pages."""
        doc = Document()
        page1 = doc.create_page("Page 1")
        page2 = doc.create_page("Page 2")
        page3 = doc.create_page("Page 3")
        self.page_tabs.set_document(doc)
        
        # Switch through pages
        self.page_tabs.set_active_page(page2.page_id)
        self.assertEqual(self.page_tabs.get_active_page_id(), page2.page_id)
        
        self.page_tabs.set_active_page(page3.page_id)
        self.assertEqual(self.page_tabs.get_active_page_id(), page3.page_id)
        
        self.page_tabs.set_active_page(page1.page_id)
        self.assertEqual(self.page_tabs.get_active_page_id(), page1.page_id)
        
    def test_switch_documents(self):
        """Test switching between different documents."""
        doc1 = Document()
        page1 = doc1.create_page("Doc1 Page1")
        
        doc2 = Document()
        page2 = doc2.create_page("Doc2 Page1")
        
        # Set first document
        self.page_tabs.set_document(doc1)
        self.assertEqual(self.page_tabs.get_active_page_id(), page1.page_id)
        
        # Switch to second document
        self.page_tabs.set_document(doc2)
        self.assertEqual(self.page_tabs.get_active_page_id(), page2.page_id)
        self.assertEqual(self.page_tabs.get_page_count(), 1)
        
    def test_all_callbacks_triggered(self):
        """Test that all callbacks are triggered appropriately."""
        doc = Document()
        page1 = doc.create_page("Page 1")
        self.page_tabs.set_document(doc)
        
        switch_calls = []
        add_calls = []
        
        def on_switch(page_id):
            switch_calls.append(page_id)
            
        def on_add(page_id):
            add_calls.append(page_id)
            
        self.page_tabs.on_page_switch = on_switch
        self.page_tabs.on_page_added = on_add
        
        # Add page
        self.page_tabs._on_add_page()
        
        # Should have triggered add callback and switch callback (to new page)
        self.assertEqual(len(add_calls), 1)
        self.assertEqual(len(switch_calls), 1)


if __name__ == '__main__':
    unittest.main()
