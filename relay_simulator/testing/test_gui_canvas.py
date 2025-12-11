"""
Tests for Design Canvas (Phase 10.1)

Tests DesignCanvas class including:
- Canvas creation and initialization
- Grid rendering
- Zoom functionality
- Pan functionality
- Coordinate conversion
"""

import unittest
import tkinter as tk
from gui.canvas import DesignCanvas


class TestDesignCanvasCreation(unittest.TestCase):
    """Tests for canvas creation and initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_create_canvas(self):
        """Test creating design canvas."""
        canvas = DesignCanvas(self.root)
        
        self.assertIsNotNone(canvas.canvas)
        self.assertIsNotNone(canvas.frame)
        self.assertEqual(canvas.canvas_width, 3000)
        self.assertEqual(canvas.canvas_height, 3000)
        self.assertEqual(canvas.grid_size, 20)
    
    def test_create_canvas_custom_size(self):
        """Test creating canvas with custom size."""
        canvas = DesignCanvas(self.root, width=5000, height=4000, grid_size=25)
        
        self.assertEqual(canvas.canvas_width, 5000)
        self.assertEqual(canvas.canvas_height, 4000)
        self.assertEqual(canvas.grid_size, 25)
    
    def test_canvas_has_scrollbars(self):
        """Test that canvas has scrollbars."""
        canvas = DesignCanvas(self.root)
        
        self.assertIsNotNone(canvas.h_scrollbar)
        self.assertIsNotNone(canvas.v_scrollbar)
    
    def test_initial_zoom_level(self):
        """Test initial zoom level is 1.0."""
        canvas = DesignCanvas(self.root)
        
        self.assertEqual(canvas.get_zoom_level(), 1.0)
    
    def test_grid_drawn(self):
        """Test that grid is drawn."""
        canvas = DesignCanvas(self.root)
        
        # Grid items should be created
        self.assertGreater(len(canvas.grid_items), 0)
        
        # Grid items should be tagged
        grid_tagged = canvas.canvas.find_withtag("grid")
        self.assertGreater(len(grid_tagged), 0)


class TestCanvasZoom(unittest.TestCase):
    """Tests for canvas zoom functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_zoom_in(self):
        """Test zoom in increases zoom level."""
        initial_zoom = self.canvas.get_zoom_level()
        
        self.canvas.zoom_in()
        
        self.assertGreater(self.canvas.get_zoom_level(), initial_zoom)
    
    def test_zoom_out(self):
        """Test zoom out decreases zoom level."""
        initial_zoom = self.canvas.get_zoom_level()
        
        self.canvas.zoom_out()
        
        self.assertLess(self.canvas.get_zoom_level(), initial_zoom)
    
    def test_reset_zoom(self):
        """Test reset zoom returns to 1.0."""
        self.canvas.zoom_in()
        self.canvas.zoom_in()
        
        self.canvas.reset_zoom()
        
        # Should be back to 1.0 (with small tolerance for floating point)
        self.assertAlmostEqual(self.canvas.get_zoom_level(), 1.0, places=2)
    
    def test_zoom_min_limit(self):
        """Test zoom cannot go below minimum."""
        # Zoom out many times
        for _ in range(20):
            self.canvas.zoom_out()
        
        # Should be at or above minimum
        self.assertGreaterEqual(self.canvas.get_zoom_level(), self.canvas.min_zoom)
    
    def test_zoom_max_limit(self):
        """Test zoom cannot exceed maximum."""
        # Zoom in many times
        for _ in range(20):
            self.canvas.zoom_in()
        
        # Should be at or below maximum
        self.assertLessEqual(self.canvas.get_zoom_level(), self.canvas.max_zoom)
    
    def test_zoom_updates_scroll_region(self):
        """Test that zooming updates scroll region."""
        initial_region = self.canvas.canvas.cget("scrollregion")
        
        self.canvas.zoom_in()
        
        new_region = self.canvas.canvas.cget("scrollregion")
        self.assertNotEqual(initial_region, new_region)
    
    def test_zoom_redraws_grid(self):
        """Test that zooming redraws grid."""
        initial_grid_count = len(self.canvas.grid_items)
        
        self.canvas.zoom_in()
        
        # Grid should still exist (might be same or different count)
        self.assertGreater(len(self.canvas.grid_items), 0)


class TestCanvasPan(unittest.TestCase):
    """Tests for canvas pan functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_pan_state_initial(self):
        """Test initial pan state."""
        self.assertFalse(self.canvas.is_panning)
    
    def test_pan_start(self):
        """Test pan start sets state."""
        # Create mock event
        event = type('Event', (), {})()
        event.x = 100
        event.y = 100
        
        self.canvas._on_pan_start(event)
        
        self.assertTrue(self.canvas.is_panning)
        self.assertEqual(self.canvas.pan_start_x, 100)
        self.assertEqual(self.canvas.pan_start_y, 100)
    
    def test_pan_end(self):
        """Test pan end clears state."""
        # Start pan
        event = type('Event', (), {})()
        event.x = 100
        event.y = 100
        self.canvas._on_pan_start(event)
        
        # End pan
        self.canvas._on_pan_end(event)
        
        self.assertFalse(self.canvas.is_panning)


class TestCanvasGridManagement(unittest.TestCase):
    """Tests for grid management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_set_grid_size(self):
        """Test changing grid size."""
        self.canvas.set_grid_size(30)
        
        self.assertEqual(self.canvas.grid_size, 30)
        # Grid should be redrawn
        self.assertGreater(len(self.canvas.grid_items), 0)
    
    def test_set_canvas_size(self):
        """Test changing canvas size."""
        self.canvas.set_canvas_size(4000, 3500)
        
        self.assertEqual(self.canvas.canvas_width, 4000)
        self.assertEqual(self.canvas.canvas_height, 3500)
        
        # Scroll region should update
        region = self.canvas.canvas.cget("scrollregion")
        self.assertIn("4000", region)
        self.assertIn("3500", region)


class TestCanvasCoordinateConversion(unittest.TestCase):
    """Tests for coordinate conversion."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_screen_to_canvas(self):
        """Test screen to canvas coordinate conversion."""
        # At zoom 1.0, should be approximately the same
        canvas_x, canvas_y = self.canvas.screen_to_canvas(100, 200)
        
        # Should return valid coordinates
        self.assertIsInstance(canvas_x, float)
        self.assertIsInstance(canvas_y, float)
    
    def test_canvas_to_screen(self):
        """Test canvas to screen coordinate conversion."""
        # At zoom 1.0, should be approximately the same
        screen_x, screen_y = self.canvas.canvas_to_screen(100, 200)
        
        # Should return valid coordinates
        self.assertIsInstance(screen_x, float)
        self.assertIsInstance(screen_y, float)


class TestCanvasClear(unittest.TestCase):
    """Tests for canvas clearing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_clear_preserves_grid(self):
        """Test that clear preserves grid."""
        # Add some items
        self.canvas.canvas.create_rectangle(100, 100, 200, 200, fill="red")
        self.canvas.canvas.create_line(50, 50, 150, 150)
        
        grid_count_before = len(self.canvas.grid_items)
        
        # Clear canvas
        self.canvas.clear()
        
        # Grid should still exist
        grid_count_after = len(self.canvas.grid_items)
        self.assertEqual(grid_count_before, grid_count_after)
        
        # Grid items should still be on canvas
        grid_tagged = self.canvas.canvas.find_withtag("grid")
        self.assertGreater(len(grid_tagged), 0)
    
    def test_clear_removes_non_grid_items(self):
        """Test that clear removes non-grid items."""
        # Add some items
        rect_id = self.canvas.canvas.create_rectangle(100, 100, 200, 200, fill="red")
        line_id = self.canvas.canvas.create_line(50, 50, 150, 150)
        
        # Clear canvas
        self.canvas.clear()
        
        # Non-grid items should be gone
        # find_withtag returns empty tuple if item doesn't exist
        all_items = self.canvas.canvas.find_all()
        self.assertNotIn(rect_id, all_items)
        self.assertNotIn(line_id, all_items)


class TestCanvasIntegration(unittest.TestCase):
    """Integration tests for canvas."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_pack_canvas(self):
        """Test that canvas can be packed."""
        canvas = DesignCanvas(self.root)
        
        # Should not raise exception
        canvas.pack(fill=tk.BOTH, expand=True)
    
    def test_grid_canvas(self):
        """Test that canvas can be gridded."""
        canvas = DesignCanvas(self.root)
        
        # Should not raise exception
        canvas.grid(row=0, column=0, sticky="nsew")
    
    def test_multiple_zoom_operations(self):
        """Test multiple zoom operations in sequence."""
        canvas = DesignCanvas(self.root)
        
        canvas.zoom_in()
        canvas.zoom_in()
        canvas.zoom_out()
        canvas.reset_zoom()
        
        # Should be back to 1.0
        self.assertAlmostEqual(canvas.get_zoom_level(), 1.0, places=2)


if __name__ == '__main__':
    unittest.main()
