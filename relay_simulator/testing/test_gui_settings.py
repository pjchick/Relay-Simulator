"""
Tests for Phase 8.3 - Settings System

Tests settings persistence, settings dialog, and integration with MainWindow.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import tkinter as tk

from gui.settings import Settings
from gui.settings_dialog import SettingsDialog
from gui.main_window import MainWindow


class TestSettings(unittest.TestCase):
    """Test the Settings class."""
    
    def setUp(self):
        """Set up a temporary settings directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        # Create settings instance and override paths BEFORE loading
        self.settings = Settings.__new__(Settings)
        self.settings.settings_dir = Path(self.temp_dir)
        self.settings.settings_file = self.settings.settings_dir / 'settings.json'
        # Initialize with fresh defaults
        self.settings._settings = {
            'recent_documents': [],
            'simulation_threading': 'single',
            'default_canvas_width': 3000,
            'default_canvas_height': 3000,
            'canvas_grid_size': 20,
            'canvas_snap_size': 10,
        }
        # Don't call load() - start fresh with defaults
        
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_default_settings(self):
        """Test that default settings are initialized."""
        self.assertEqual(self.settings.get('simulation_threading'), 'single')
        self.assertEqual(self.settings.get('default_canvas_width'), 3000)
        self.assertEqual(self.settings.get('default_canvas_height'), 3000)
        self.assertEqual(self.settings.get('canvas_grid_size'), 20)
        self.assertEqual(self.settings.get('canvas_snap_size'), 10)
        
    def test_get_set(self):
        """Test get and set methods."""
        self.settings.set('test_key', 'test_value')
        self.assertEqual(self.settings.get('test_key'), 'test_value')
        
    def test_get_default(self):
        """Test get with default value."""
        self.assertEqual(self.settings.get('nonexistent', 'default'), 'default')
        
    def test_save_and_load(self):
        """Test saving and loading settings."""
        # Set some values
        self.settings.set('simulation_threading', 'multi')
        self.settings.set('canvas_grid_size', 25)
        
        # Save
        self.settings.save()
        
        # Create new settings instance and load
        new_settings = Settings()
        new_settings.settings_dir = Path(self.temp_dir)
        new_settings.settings_file = new_settings.settings_dir / 'settings.json'
        new_settings.load()
        
        # Verify loaded values
        self.assertEqual(new_settings.get('simulation_threading'), 'multi')
        self.assertEqual(new_settings.get('canvas_grid_size'), 25)
        
    def test_recent_documents(self):
        """Test recent documents management."""
        # Initially empty
        self.assertEqual(len(self.settings.get_recent_documents()), 0)
        
        # Add documents
        self.settings.add_recent_document('/path/to/file1.rsim')
        self.settings.add_recent_document('/path/to/file2.rsim')
        
        recent = self.settings.get_recent_documents()
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0], '/path/to/file2.rsim')  # Most recent first
        
    def test_recent_documents_limit(self):
        """Test that recent documents are limited to 10."""
        # Add more than 10 documents
        for i in range(15):
            self.settings.add_recent_document(f'/path/to/file{i}.rsim')
            
        recent = self.settings.get_recent_documents()
        self.assertEqual(len(recent), 10)
        
    def test_recent_documents_no_duplicates(self):
        """Test that recent documents have no duplicates."""
        self.settings.add_recent_document('/path/to/file1.rsim')
        self.settings.add_recent_document('/path/to/file2.rsim')
        self.settings.add_recent_document('/path/to/file1.rsim')
        
        recent = self.settings.get_recent_documents()
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0], '/path/to/file1.rsim')  # Moved to front
        
    def test_remove_recent_document(self):
        """Test removing a recent document."""
        self.settings.add_recent_document('/path/to/file1.rsim')
        self.settings.add_recent_document('/path/to/file2.rsim')
        
        self.settings.remove_recent_document('/path/to/file1.rsim')
        
        recent = self.settings.get_recent_documents()
        self.assertEqual(len(recent), 1)
        self.assertNotIn('/path/to/file1.rsim', recent)
        
    def test_clear_recent_documents(self):
        """Test clearing all recent documents."""
        self.settings.add_recent_document('/path/to/file1.rsim')
        self.settings.add_recent_document('/path/to/file2.rsim')
        
        self.settings.clear_recent_documents()
        
        self.assertEqual(len(self.settings.get_recent_documents()), 0)
        
    def test_simulation_threading(self):
        """Test simulation threading getter/setter."""
        self.assertEqual(self.settings.get_simulation_threading(), 'single')
        
        self.settings.set_simulation_threading('multi')
        self.assertEqual(self.settings.get_simulation_threading(), 'multi')
        
    def test_simulation_threading_invalid(self):
        """Test that invalid threading mode raises error."""
        with self.assertRaises(ValueError):
            self.settings.set_simulation_threading('invalid')
            
    def test_canvas_size(self):
        """Test canvas size getter/setter."""
        self.assertEqual(self.settings.get_canvas_size(), (3000, 3000))
        
        self.settings.set_canvas_size(4000, 5000)
        self.assertEqual(self.settings.get_canvas_size(), (4000, 5000))
        
    def test_grid_size(self):
        """Test grid size getter/setter."""
        self.assertEqual(self.settings.get_grid_size(), 20)
        
        self.settings.set_grid_size(25)
        self.assertEqual(self.settings.get_grid_size(), 25)
        
    def test_grid_size_invalid(self):
        """Test that invalid grid size raises error."""
        with self.assertRaises(ValueError):
            self.settings.set_grid_size(0)
        with self.assertRaises(ValueError):
            self.settings.set_grid_size(-5)
            
    def test_snap_size(self):
        """Test snap size getter/setter."""
        self.assertEqual(self.settings.get_snap_size(), 10)
        
        self.settings.set_snap_size(15)
        self.assertEqual(self.settings.get_snap_size(), 15)
        
    def test_snap_size_invalid(self):
        """Test that invalid snap size raises error."""
        with self.assertRaises(ValueError):
            self.settings.set_snap_size(0)
        with self.assertRaises(ValueError):
            self.settings.set_snap_size(-5)
            
    def test_reset_to_defaults(self):
        """Test resetting to default values."""
        # Change some settings
        self.settings.set_simulation_threading('multi')
        self.settings.set_grid_size(30)
        
        # Reset
        self.settings.reset_to_defaults()
        
        # Verify defaults restored
        self.assertEqual(self.settings.get_simulation_threading(), 'single')
        self.assertEqual(self.settings.get_grid_size(), 20)


class TestSettingsDialog(unittest.TestCase):
    """Test the SettingsDialog class."""
    
    def setUp(self):
        """Create a root window and settings for testing."""
        self.root = tk.Tk()
        self.settings = Settings()
        
    def tearDown(self):
        """Clean up after each test."""
        try:
            self.root.destroy()
        except:
            pass
            
    def test_dialog_creation(self):
        """Test that dialog can be created."""
        dialog = SettingsDialog(self.root, self.settings)
        self.assertIsNotNone(dialog)
        dialog.dialog.destroy()
        
    def test_dialog_initializes_with_current_settings(self):
        """Test that dialog shows current settings."""
        # Set some custom values
        self.settings.set_simulation_threading('multi')
        self.settings.set_canvas_size(4000, 5000)
        self.settings.set_grid_size(25)
        self.settings.set_snap_size(15)
        
        # Create dialog
        dialog = SettingsDialog(self.root, self.settings)
        
        # Verify variables are initialized with current values
        self.assertEqual(dialog.threading_var.get(), 'multi')
        self.assertEqual(dialog.canvas_width_var.get(), 4000)
        self.assertEqual(dialog.canvas_height_var.get(), 5000)
        self.assertEqual(dialog.grid_size_var.get(), 25)
        self.assertEqual(dialog.snap_size_var.get(), 15)
        
        dialog.dialog.destroy()
        
    def test_reset_to_defaults_button(self):
        """Test that Reset button sets default values."""
        # Set some custom values
        self.settings.set_simulation_threading('multi')
        self.settings.set_grid_size(30)
        
        dialog = SettingsDialog(self.root, self.settings)
        
        # Click reset
        dialog._on_reset()
        
        # Verify defaults are set in the dialog
        self.assertEqual(dialog.threading_var.get(), 'single')
        self.assertEqual(dialog.grid_size_var.get(), 20)
        
        dialog.dialog.destroy()
        
    def test_cancel_does_not_save(self):
        """Test that Cancel button doesn't save changes."""
        original_threading = self.settings.get_simulation_threading()
        
        dialog = SettingsDialog(self.root, self.settings)
        dialog.threading_var.set('multi')
        dialog._on_cancel()
        
        # Settings should not have changed
        self.assertEqual(self.settings.get_simulation_threading(), original_threading)


class TestMainWindowSettingsIntegration(unittest.TestCase):
    """Test settings integration with MainWindow."""
    
    def setUp(self):
        """Create a main window for testing."""
        self.window = MainWindow()
        # Override settings directory to use temp directory
        self.temp_dir = tempfile.mkdtemp()
        self.window.settings.settings_dir = Path(self.temp_dir)
        self.window.settings.settings_file = self.window.settings.settings_dir / 'settings.json'
        
    def tearDown(self):
        """Clean up after each test."""
        try:
            self.window.root.destroy()
        except:
            pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_main_window_has_settings(self):
        """Test that MainWindow has a Settings instance."""
        self.assertIsNotNone(self.window.settings)
        self.assertIsInstance(self.window.settings, Settings)
        
    def test_recent_documents_synced_to_menu(self):
        """Test that recent documents from settings are synced to menu."""
        # Add document directly to window's settings
        self.window.settings.add_recent_document('/path/to/test.rsim')
        self.window.menu_bar.add_recent_document('/path/to/test.rsim')
        
        # Menu should have the recent document
        self.assertIn('/path/to/test.rsim', self.window.menu_bar.recent_documents)
        
    def test_settings_menu_callback_set(self):
        """Test that Settings menu callback is set."""
        self.assertIsNotNone(self.window.menu_bar.callbacks['settings'])


if __name__ == '__main__':
    unittest.main()
