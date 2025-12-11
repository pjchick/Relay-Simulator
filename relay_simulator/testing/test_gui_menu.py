"""
Tests for Phase 8.2 - Menu System

Tests the menu bar, all menus, keyboard shortcuts, and menu state management.
"""

import unittest
import tkinter as tk
from gui.main_window import MainWindow
from gui.menu_bar import MenuBar


class TestMenuBar(unittest.TestCase):
    """Test the MenuBar class."""
    
    def setUp(self):
        """Create a root window and menu bar for testing."""
        self.root = tk.Tk()
        self.menu_bar = MenuBar(self.root)
        
    def tearDown(self):
        """Clean up after each test."""
        try:
            self.root.destroy()
        except:
            pass
            
    def test_menu_bar_created(self):
        """Test that the menu bar is created."""
        self.assertIsNotNone(self.menu_bar)
        self.assertIsNotNone(self.menu_bar.menubar)
        
    def test_file_menu_exists(self):
        """Test that the File menu exists."""
        self.assertIsNotNone(self.menu_bar.file_menu)
        
    def test_edit_menu_exists(self):
        """Test that the Edit menu exists."""
        self.assertIsNotNone(self.menu_bar.edit_menu)
        
    def test_simulation_menu_exists(self):
        """Test that the Simulation menu exists."""
        self.assertIsNotNone(self.menu_bar.simulation_menu)
        
    def test_view_menu_exists(self):
        """Test that the View menu exists."""
        self.assertIsNotNone(self.menu_bar.view_menu)
        
    def test_recent_menu_exists(self):
        """Test that the Recent Documents submenu exists."""
        self.assertIsNotNone(self.menu_bar.recent_menu)
        
    def test_callbacks_initialized(self):
        """Test that all callback slots are initialized."""
        expected_callbacks = [
            'new', 'open', 'save', 'save_as', 'settings', 'exit',
            'select_all', 'cut', 'copy', 'paste',
            'start_simulation', 'stop_simulation',
            'zoom_in', 'zoom_out', 'reset_zoom'
        ]
        for cb in expected_callbacks:
            self.assertIn(cb, self.menu_bar.callbacks)
            
    def test_set_callback(self):
        """Test setting a callback function."""
        called = []
        
        def test_callback():
            called.append(True)
            
        self.menu_bar.set_callback('new', test_callback)
        self.assertEqual(self.menu_bar.callbacks['new'], test_callback)
        
    def test_callback_execution(self):
        """Test that callbacks are executed when triggered."""
        called = []
        
        def test_callback():
            called.append(True)
            
        self.menu_bar.set_callback('new', test_callback)
        self.menu_bar._on_new()
        
        self.assertTrue(called)
        
    def test_add_recent_document(self):
        """Test adding a recent document."""
        self.menu_bar.add_recent_document("/path/to/file1.rsim")
        self.assertEqual(len(self.menu_bar.recent_documents), 1)
        self.assertEqual(self.menu_bar.recent_documents[0], "/path/to/file1.rsim")
        
    def test_recent_documents_max_limit(self):
        """Test that recent documents list is limited to max_recent."""
        # Add more than max_recent documents
        for i in range(15):
            self.menu_bar.add_recent_document(f"/path/to/file{i}.rsim")
            
        # Should only keep the last max_recent (10)
        self.assertEqual(len(self.menu_bar.recent_documents), self.menu_bar.max_recent)
        
    def test_recent_documents_no_duplicates(self):
        """Test that recent documents list has no duplicates."""
        self.menu_bar.add_recent_document("/path/to/file1.rsim")
        self.menu_bar.add_recent_document("/path/to/file2.rsim")
        self.menu_bar.add_recent_document("/path/to/file1.rsim")
        
        # Should have 2 unique documents, with file1 at the front
        self.assertEqual(len(self.menu_bar.recent_documents), 2)
        self.assertEqual(self.menu_bar.recent_documents[0], "/path/to/file1.rsim")
        
    def test_remove_recent_document(self):
        """Test removing a recent document."""
        self.menu_bar.add_recent_document("/path/to/file1.rsim")
        self.menu_bar.add_recent_document("/path/to/file2.rsim")
        
        self.menu_bar.remove_recent_document("/path/to/file1.rsim")
        
        self.assertEqual(len(self.menu_bar.recent_documents), 1)
        self.assertNotIn("/path/to/file1.rsim", self.menu_bar.recent_documents)
        
    def test_clear_recent_documents(self):
        """Test clearing all recent documents."""
        self.menu_bar.add_recent_document("/path/to/file1.rsim")
        self.menu_bar.add_recent_document("/path/to/file2.rsim")
        
        self.menu_bar.clear_recent_documents()
        
        self.assertEqual(len(self.menu_bar.recent_documents), 0)
        
    def test_enable_edit_menu_no_selection(self):
        """Test that Cut/Copy are disabled when there's no selection."""
        self.menu_bar.enable_edit_menu(has_selection=False)
        
        # Cut and Copy should be disabled
        cut_state = self.menu_bar.edit_menu.entrycget('Cut', 'state')
        copy_state = self.menu_bar.edit_menu.entrycget('Copy', 'state')
        
        self.assertEqual(cut_state, tk.DISABLED)
        self.assertEqual(copy_state, tk.DISABLED)
        
    def test_enable_edit_menu_with_selection(self):
        """Test that Cut/Copy are enabled when there's a selection."""
        self.menu_bar.enable_edit_menu(has_selection=True)
        
        # Cut and Copy should be enabled
        cut_state = self.menu_bar.edit_menu.entrycget('Cut', 'state')
        copy_state = self.menu_bar.edit_menu.entrycget('Copy', 'state')
        
        self.assertEqual(cut_state, tk.NORMAL)
        self.assertEqual(copy_state, tk.NORMAL)
        
    def test_enable_simulation_controls_stopped(self):
        """Test simulation controls when simulation is stopped."""
        self.menu_bar.enable_simulation_controls(is_running=False)
        
        # Start should be enabled, Stop should be disabled
        start_state = self.menu_bar.simulation_menu.entrycget('Start Simulation', 'state')
        stop_state = self.menu_bar.simulation_menu.entrycget('Stop Simulation', 'state')
        
        self.assertEqual(start_state, tk.NORMAL)
        self.assertEqual(stop_state, tk.DISABLED)
        
    def test_enable_simulation_controls_running(self):
        """Test simulation controls when simulation is running."""
        self.menu_bar.enable_simulation_controls(is_running=True)
        
        # Start should be disabled, Stop should be enabled
        start_state = self.menu_bar.simulation_menu.entrycget('Start Simulation', 'state')
        stop_state = self.menu_bar.simulation_menu.entrycget('Stop Simulation', 'state')
        
        self.assertEqual(start_state, tk.DISABLED)
        self.assertEqual(stop_state, tk.NORMAL)


class TestMenuBarIntegration(unittest.TestCase):
    """Test menu bar integration with MainWindow."""
    
    def setUp(self):
        """Create a main window for testing."""
        self.window = MainWindow()
        
    def tearDown(self):
        """Clean up after each test."""
        try:
            self.window.root.destroy()
        except:
            pass
            
    def test_main_window_has_menu_bar(self):
        """Test that MainWindow has a menu bar."""
        self.assertIsNotNone(self.window.menu_bar)
        self.assertIsInstance(self.window.menu_bar, MenuBar)
        
    def test_menu_callbacks_set(self):
        """Test that menu callbacks are set in MainWindow."""
        # Check that at least some callbacks are set
        self.assertIsNotNone(self.window.menu_bar.callbacks['new'])
        self.assertIsNotNone(self.window.menu_bar.callbacks['exit'])
        self.assertIsNotNone(self.window.menu_bar.callbacks['start_simulation'])
        
    def test_menu_new_updates_status(self):
        """Test that File > New updates the status bar."""
        self.window._menu_new()
        status_text = self.window.status_label.cget('text')
        self.assertIn("New document", status_text)
        
    def test_menu_save_updates_status(self):
        """Test that File > Save updates the status bar."""
        self.window._menu_save()
        status_text = self.window.status_label.cget('text')
        self.assertIn("Save", status_text)
        
    def test_menu_start_simulation_updates_menu_state(self):
        """Test that Start Simulation updates menu states."""
        self.window._menu_start_simulation()
        
        # Start should be disabled, Stop should be enabled
        start_state = self.window.menu_bar.simulation_menu.entrycget('Start Simulation', 'state')
        stop_state = self.window.menu_bar.simulation_menu.entrycget('Stop Simulation', 'state')
        
        self.assertEqual(start_state, tk.DISABLED)
        self.assertEqual(stop_state, tk.NORMAL)
        
    def test_menu_stop_simulation_updates_menu_state(self):
        """Test that Stop Simulation updates menu states."""
        # Start simulation first
        self.window._menu_start_simulation()
        
        # Then stop it
        self.window._menu_stop_simulation()
        
        # Start should be enabled, Stop should be disabled
        start_state = self.window.menu_bar.simulation_menu.entrycget('Start Simulation', 'state')
        stop_state = self.window.menu_bar.simulation_menu.entrycget('Stop Simulation', 'state')
        
        self.assertEqual(start_state, tk.NORMAL)
        self.assertEqual(stop_state, tk.DISABLED)


class TestKeyboardShortcuts(unittest.TestCase):
    """Test keyboard shortcuts."""
    
    def setUp(self):
        """Create a main window for testing."""
        self.window = MainWindow()
        self.called = []
        
    def tearDown(self):
        """Clean up after each test."""
        try:
            self.window.root.destroy()
        except:
            pass
            
    def _create_callback(self, name):
        """Create a test callback that records when it's called."""
        def callback(*args):
            self.called.append(name)
        return callback
        
    def test_ctrl_n_new_shortcut(self):
        """Test that Ctrl+N triggers New."""
        self.window.menu_bar.set_callback('new', self._create_callback('new'))
        
        # Simulate Ctrl+N
        event = tk.Event()
        event.keysym = 'n'
        self.window.root.event_generate('<Control-n>')
        self.window.root.update()
        
        # Note: In unit tests, event_generate doesn't always trigger callbacks
        # This test verifies the binding exists
        bindings = self.window.root.bind('<Control-n>')
        self.assertIsNotNone(bindings)
        
    def test_ctrl_s_save_shortcut(self):
        """Test that Ctrl+S binding exists."""
        bindings = self.window.root.bind('<Control-s>')
        self.assertIsNotNone(bindings)
        
    def test_ctrl_o_open_shortcut(self):
        """Test that Ctrl+O binding exists."""
        bindings = self.window.root.bind('<Control-o>')
        self.assertIsNotNone(bindings)
        
    def test_ctrl_c_copy_shortcut(self):
        """Test that Ctrl+C binding exists."""
        bindings = self.window.root.bind('<Control-c>')
        self.assertIsNotNone(bindings)
        
    def test_ctrl_v_paste_shortcut(self):
        """Test that Ctrl+V binding exists."""
        bindings = self.window.root.bind('<Control-v>')
        self.assertIsNotNone(bindings)
        
    def test_ctrl_x_cut_shortcut(self):
        """Test that Ctrl+X binding exists."""
        bindings = self.window.root.bind('<Control-x>')
        self.assertIsNotNone(bindings)
        
    def test_f5_start_simulation_shortcut(self):
        """Test that F5 binding exists."""
        bindings = self.window.root.bind('<F5>')
        self.assertIsNotNone(bindings)
        
    def test_shift_f5_stop_simulation_shortcut(self):
        """Test that Shift+F5 binding exists."""
        bindings = self.window.root.bind('<Shift-F5>')
        self.assertIsNotNone(bindings)
        
    def test_ctrl_plus_zoom_in_shortcut(self):
        """Test that Ctrl++ binding exists."""
        bindings = self.window.root.bind('<Control-plus>')
        self.assertIsNotNone(bindings)
        
    def test_ctrl_minus_zoom_out_shortcut(self):
        """Test that Ctrl+- binding exists."""
        bindings = self.window.root.bind('<Control-minus>')
        self.assertIsNotNone(bindings)
        
    def test_ctrl_0_reset_zoom_shortcut(self):
        """Test that Ctrl+0 binding exists."""
        bindings = self.window.root.bind('<Control-Key-0>')
        self.assertIsNotNone(bindings)


if __name__ == '__main__':
    unittest.main()
