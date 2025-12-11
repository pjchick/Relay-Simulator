"""
Tests for Phase 8.1 - Application Window and Theme

Tests the main window, theme application, and basic window lifecycle.
"""

import unittest
import tkinter as tk
from gui.main_window import MainWindow
from gui.theme import VSCodeTheme, apply_theme


class TestVSCodeTheme(unittest.TestCase):
    """Test the VS Code theme configuration."""
    
    def test_color_constants_defined(self):
        """Test that all required color constants are defined."""
        # Background colors
        self.assertIsInstance(VSCodeTheme.BG_PRIMARY, str)
        self.assertIsInstance(VSCodeTheme.BG_SECONDARY, str)
        self.assertIsInstance(VSCodeTheme.BG_TERTIARY, str)
        
        # Foreground colors
        self.assertIsInstance(VSCodeTheme.FG_PRIMARY, str)
        self.assertIsInstance(VSCodeTheme.FG_SECONDARY, str)
        
        # Accent colors
        self.assertIsInstance(VSCodeTheme.ACCENT_BLUE, str)
        self.assertIsInstance(VSCodeTheme.ACCENT_GREEN, str)
        
        # Canvas colors
        self.assertIsInstance(VSCodeTheme.CANVAS_BG, str)
        self.assertIsInstance(VSCodeTheme.CANVAS_GRID, str)
        
        # Component colors
        self.assertIsInstance(VSCodeTheme.COMPONENT_FILL, str)
        self.assertIsInstance(VSCodeTheme.WIRE_POWERED, str)
        
    def test_font_sizes_defined(self):
        """Test that all font sizes are defined as integers."""
        self.assertIsInstance(VSCodeTheme.FONT_SIZE_SMALL, int)
        self.assertIsInstance(VSCodeTheme.FONT_SIZE_NORMAL, int)
        self.assertIsInstance(VSCodeTheme.FONT_SIZE_MEDIUM, int)
        self.assertIsInstance(VSCodeTheme.FONT_SIZE_LARGE, int)
        self.assertIsInstance(VSCodeTheme.FONT_SIZE_CANVAS_LABEL, int)
        
    def test_spacing_constants_defined(self):
        """Test that spacing constants are defined."""
        self.assertIsInstance(VSCodeTheme.PADDING_SMALL, int)
        self.assertIsInstance(VSCodeTheme.PADDING_MEDIUM, int)
        self.assertIsInstance(VSCodeTheme.PADDING_LARGE, int)
        self.assertIsInstance(VSCodeTheme.SPACING_SMALL, int)
        
    def test_widget_sizes_defined(self):
        """Test that widget size constants are defined."""
        self.assertIsInstance(VSCodeTheme.BUTTON_HEIGHT, int)
        self.assertIsInstance(VSCodeTheme.TOOLBAR_HEIGHT, int)
        self.assertIsInstance(VSCodeTheme.STATUSBAR_HEIGHT, int)
        self.assertIsInstance(VSCodeTheme.TOOLBOX_WIDTH, int)
        self.assertIsInstance(VSCodeTheme.PROPERTIES_WIDTH, int)
        
    def test_get_font_normal(self):
        """Test get_font with default parameters."""
        font = VSCodeTheme.get_font()
        self.assertIsInstance(font, tuple)
        self.assertEqual(len(font), 3)
        self.assertIsInstance(font[0], str)  # Font family
        self.assertIsInstance(font[1], int)  # Font size
        self.assertIsInstance(font[2], str)  # Font weight
        
    def test_get_font_sizes(self):
        """Test get_font with different size parameters."""
        small_font = VSCodeTheme.get_font('small')
        self.assertEqual(small_font[1], VSCodeTheme.FONT_SIZE_SMALL)
        
        normal_font = VSCodeTheme.get_font('normal')
        self.assertEqual(normal_font[1], VSCodeTheme.FONT_SIZE_NORMAL)
        
        medium_font = VSCodeTheme.get_font('medium')
        self.assertEqual(medium_font[1], VSCodeTheme.FONT_SIZE_MEDIUM)
        
        large_font = VSCodeTheme.get_font('large')
        self.assertEqual(large_font[1], VSCodeTheme.FONT_SIZE_LARGE)
        
    def test_get_font_bold(self):
        """Test get_font with bold parameter."""
        bold_font = VSCodeTheme.get_font(bold=True)
        self.assertEqual(bold_font[2], 'bold')
        
        normal_font = VSCodeTheme.get_font(bold=False)
        self.assertEqual(normal_font[2], 'normal')
        
    def test_get_font_mono(self):
        """Test get_font with monospace parameter."""
        mono_font = VSCodeTheme.get_font(mono=True)
        self.assertEqual(mono_font[0], VSCodeTheme.FONT_FAMILY_MONO)
        
        ui_font = VSCodeTheme.get_font(mono=False)
        self.assertEqual(ui_font[0], VSCodeTheme.FONT_FAMILY_UI)


class TestMainWindow(unittest.TestCase):
    """Test the MainWindow class."""
    
    def setUp(self):
        """Create a main window for testing."""
        self.window = MainWindow()
        
    def tearDown(self):
        """Clean up the window after each test."""
        try:
            self.window.root.destroy()
        except:
            pass
        
    def test_window_created(self):
        """Test that the window is created successfully."""
        self.assertIsNotNone(self.window.root)
        self.assertIsInstance(self.window.root, tk.Tk)
        
    def test_window_title(self):
        """Test that the window has the correct title."""
        # Window title now includes active tab name (Phase 9.1)
        title = self.window.root.title()
        self.assertIn("Relay Simulator III", title)
        
    def test_window_size(self):
        """Test that the window has the correct default size."""
        self.assertEqual(self.window.default_width, 1280)
        self.assertEqual(self.window.default_height, 720)
        
    def test_unsaved_changes_flag(self):
        """Test the unsaved changes flag."""
        # Initially no unsaved changes
        self.assertFalse(self.window.has_unsaved_changes)
        
        # Set unsaved changes
        self.window.set_unsaved_changes(True)
        self.assertTrue(self.window.has_unsaved_changes)
        
        # Clear unsaved changes
        self.window.set_unsaved_changes(False)
        self.assertFalse(self.window.has_unsaved_changes)
        
    def test_unsaved_changes_updates_title(self):
        """Test that unsaved changes updates the window title."""
        base_title = "Relay Simulator III"
        
        # No unsaved changes
        self.window.set_unsaved_changes(False)
        self.assertEqual(self.window.root.title(), base_title)
        
        # With unsaved changes
        self.window.set_unsaved_changes(True)
        self.assertEqual(self.window.root.title(), f"*{base_title}")
        
    def test_status_bar_exists(self):
        """Test that the status bar is created."""
        self.assertIsNotNone(self.window.status_bar)
        self.assertIsNotNone(self.window.status_label)
        
    def test_set_status(self):
        """Test setting the status bar message."""
        test_message = "Test Status Message"
        self.window.set_status(test_message)
        self.assertEqual(self.window.status_label.cget('text'), test_message)
        
    def test_main_frame_created(self):
        """Test that the main frame is created."""
        self.assertIsNotNone(self.window.main_frame)
        
    def test_content_frame_created(self):
        """Test that the content frame is created."""
        self.assertIsNotNone(self.window.content_frame)
        
    def test_theme_applied(self):
        """Test that the theme is applied to the window."""
        # Check that the root background color is set
        self.assertEqual(self.window.root.cget('bg'), VSCodeTheme.BG_PRIMARY)


class TestThemeApplication(unittest.TestCase):
    """Test theme application to widgets."""
    
    def setUp(self):
        """Create a root window for testing."""
        self.root = tk.Tk()
        apply_theme(self.root)
        
    def tearDown(self):
        """Clean up after each test."""
        try:
            self.root.destroy()
        except:
            pass
        
    def test_apply_theme_to_root(self):
        """Test that apply_theme configures the root window."""
        self.assertEqual(self.root.cget('bg'), VSCodeTheme.BG_PRIMARY)
        
    def test_theme_configures_styles(self):
        """Test that apply_theme creates ttk styles."""
        from tkinter import ttk
        style = ttk.Style(self.root)
        
        # Check that some styles are configured
        # Note: We can't directly check all styles, but we can verify theme is set
        self.assertIsNotNone(style.theme_use())


if __name__ == '__main__':
    unittest.main()
