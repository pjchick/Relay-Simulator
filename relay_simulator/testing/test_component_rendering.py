"""
Tests for Component Rendering System (Phase 10.3)

Tests component rendering including:
- Renderer factory
- Base renderer functionality
- Individual component renderers
- Canvas integration
- Zoom and rotation handling
- Selection and powered state
"""

import unittest
import tkinter as tk
from gui.canvas import DesignCanvas
from gui.renderers.renderer_factory import RendererFactory
from gui.renderers.base_renderer import ComponentRenderer
from gui.renderers.switch_renderer import SwitchRenderer
from gui.renderers.indicator_renderer import IndicatorRenderer
from gui.renderers.relay_renderer import RelayRenderer
from gui.renderers.vcc_renderer import VCCRenderer
from components.switch import Switch
from components.indicator import Indicator
from components.dpdt_relay import DPDTRelay
from components.vcc import VCC
from core.document import Document


class TestRendererFactory(unittest.TestCase):
    """Tests for RendererFactory."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_factory_creates_switch_renderer(self):
        """Test factory creates SwitchRenderer for Switch component."""
        switch = Switch("sw1", "page1")
        renderer = RendererFactory.create_renderer(self.canvas.canvas, switch)
        
        self.assertIsInstance(renderer, SwitchRenderer)
        self.assertEqual(renderer.component, switch)
    
    def test_factory_creates_indicator_renderer(self):
        """Test factory creates IndicatorRenderer for Indicator component."""
        indicator = Indicator("ind1", "page1")
        renderer = RendererFactory.create_renderer(self.canvas.canvas, indicator)
        
        self.assertIsInstance(renderer, IndicatorRenderer)
        self.assertEqual(renderer.component, indicator)
    
    def test_factory_creates_relay_renderer(self):
        """Test factory creates RelayRenderer for DPDTRelay component."""
        relay = DPDTRelay("relay1", "page1")
        renderer = RendererFactory.create_renderer(self.canvas.canvas, relay)
        
        self.assertIsInstance(renderer, RelayRenderer)
        self.assertEqual(renderer.component, relay)
    
    def test_factory_creates_vcc_renderer(self):
        """Test factory creates VCCRenderer for VCC component."""
        vcc = VCC("vcc1", "page1")
        renderer = RendererFactory.create_renderer(self.canvas.canvas, vcc)
        
        self.assertIsInstance(renderer, VCCRenderer)
        self.assertEqual(renderer.component, vcc)
    
    def test_factory_get_supported_types(self):
        """Test factory returns supported component types."""
        types = RendererFactory.get_supported_types()
        
        self.assertIn('Switch', types)
        self.assertIn('Indicator', types)
        self.assertIn('DPDTRelay', types)
        self.assertIn('VCC', types)


class TestBaseRenderer(unittest.TestCase):
    """Tests for ComponentRenderer base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        self.switch = Switch("sw1", "page1")
        self.switch.position = (100, 100)
        self.renderer = SwitchRenderer(self.canvas.canvas, self.switch)
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_renderer_initialization(self):
        """Test renderer initializes correctly."""
        self.assertEqual(self.renderer.component, self.switch)
        self.assertEqual(self.renderer.canvas, self.canvas.canvas)
        self.assertEqual(len(self.renderer.canvas_items), 0)
        self.assertFalse(self.renderer.selected)
        self.assertFalse(self.renderer.powered)
    
    def test_renderer_get_position(self):
        """Test renderer gets component position."""
        x, y = self.renderer.get_position()
        self.assertEqual(x, 100)
        self.assertEqual(y, 100)
    
    def test_renderer_set_selected(self):
        """Test renderer selection state."""
        self.assertFalse(self.renderer.selected)
        
        self.renderer.set_selected(True)
        self.assertTrue(self.renderer.selected)
        
        self.renderer.set_selected(False)
        self.assertFalse(self.renderer.selected)
    
    def test_renderer_set_powered(self):
        """Test renderer powered state."""
        self.assertFalse(self.renderer.powered)
        
        self.renderer.set_powered(True)
        self.assertTrue(self.renderer.powered)
        
        self.renderer.set_powered(False)
        self.assertFalse(self.renderer.powered)
    
    def test_renderer_rotate_point(self):
        """Test point rotation calculation."""
        # Rotate point (10, 0) around (0, 0) by 90 degrees
        x, y = self.renderer.rotate_point(10, 0, 0, 0, 90)
        self.assertAlmostEqual(x, 0, places=5)
        self.assertAlmostEqual(y, 10, places=5)
        
        # Rotate point (10, 0) around (0, 0) by 180 degrees
        x, y = self.renderer.rotate_point(10, 0, 0, 0, 180)
        self.assertAlmostEqual(x, -10, places=5)
        self.assertAlmostEqual(y, 0, places=5)


class TestSwitchRenderer(unittest.TestCase):
    """Tests for SwitchRenderer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        self.switch = Switch("sw1", "page1")
        self.switch.position = (100, 100)
        self.renderer = SwitchRenderer(self.canvas.canvas, self.switch)
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_switch_renderer_renders(self):
        """Test switch renderer creates canvas items."""
        self.renderer.render(zoom=1.0)
        
        # Should create canvas items (circle, label, tabs)
        self.assertGreater(len(self.renderer.canvas_items), 0)
    
    def test_switch_renderer_clears(self):
        """Test switch renderer clears canvas items."""
        self.renderer.render(zoom=1.0)
        item_count = len(self.renderer.canvas_items)
        self.assertGreater(item_count, 0)
        
        self.renderer.clear()
        self.assertEqual(len(self.renderer.canvas_items), 0)
    
    def test_switch_renderer_zoom(self):
        """Test switch renderer at different zoom levels."""
        # Render at 1.0 zoom
        self.renderer.render(zoom=1.0)
        items_1x = len(self.renderer.canvas_items)
        
        # Render at 2.0 zoom (should recreate items)
        self.renderer.render(zoom=2.0)
        items_2x = len(self.renderer.canvas_items)
        
        # Should have same number of items
        self.assertEqual(items_1x, items_2x)
    
    def test_switch_renderer_rotation(self):
        """Test switch renderer with rotation."""
        self.switch.rotation = 90
        self.renderer.render(zoom=1.0)
        
        # Should create items even with rotation
        self.assertGreater(len(self.renderer.canvas_items), 0)


class TestIndicatorRenderer(unittest.TestCase):
    """Tests for IndicatorRenderer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        self.indicator = Indicator("ind1", "page1")
        self.indicator.position = (200, 200)
        self.renderer = IndicatorRenderer(self.canvas.canvas, self.indicator)
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_indicator_renderer_renders(self):
        """Test indicator renderer creates canvas items."""
        self.renderer.render(zoom=1.0)
        
        # Should create canvas items (circle, label, tabs)
        self.assertGreater(len(self.renderer.canvas_items), 0)
    
    def test_indicator_renderer_powered_state(self):
        """Test indicator renderer with powered state."""
        # Render unpowered
        self.renderer.set_powered(False)
        self.renderer.render(zoom=1.0)
        unpowered_items = len(self.renderer.canvas_items)
        
        # Render powered
        self.renderer.set_powered(True)
        self.renderer.render(zoom=1.0)
        powered_items = len(self.renderer.canvas_items)
        
        # Should have same number of items (just different colors)
        self.assertEqual(unpowered_items, powered_items)


class TestRelayRenderer(unittest.TestCase):
    """Tests for RelayRenderer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        self.relay = DPDTRelay("relay1", "page1")
        self.relay.position = (300, 300)
        self.renderer = RelayRenderer(self.canvas.canvas, self.relay)
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_relay_renderer_renders(self):
        """Test relay renderer creates canvas items."""
        self.renderer.render(zoom=1.0)
        
        # Should create canvas items (body, coil, poles, tabs)
        self.assertGreater(len(self.renderer.canvas_items), 0)
    
    def test_relay_renderer_energized_state(self):
        """Test relay renderer with energized state."""
        # Test that renderer can handle energized relay
        self.relay._is_energized = True
        self.renderer.render(zoom=1.0)
        
        self.assertGreater(len(self.renderer.canvas_items), 0)


class TestVCCRenderer(unittest.TestCase):
    """Tests for VCCRenderer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        self.vcc = VCC("vcc1", "page1")
        self.vcc.position = (400, 400)
        self.renderer = VCCRenderer(self.canvas.canvas, self.vcc)
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_vcc_renderer_renders(self):
        """Test VCC renderer creates canvas items."""
        self.renderer.render(zoom=1.0)
        
        # Should create canvas items (circle, +, label, tabs)
        self.assertGreater(len(self.renderer.canvas_items), 0)
    
    def test_vcc_renderer_voltage_label(self):
        """Test VCC renderer with different voltages."""
        self.vcc.properties['voltage'] = 12
        self.renderer.render(zoom=1.0)
        
        self.assertGreater(len(self.renderer.canvas_items), 0)


class TestCanvasIntegration(unittest.TestCase):
    """Tests for canvas integration with renderers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        self.document = Document()
        # Document starts with no pages, create one
        self.page = self.document.create_page("Test Page")
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_canvas_set_page(self):
        """Test setting page on canvas."""
        self.canvas.set_page(self.page)
        
        self.assertEqual(self.canvas.current_page, self.page)
    
    def test_canvas_render_empty_page(self):
        """Test rendering empty page."""
        self.canvas.set_page(self.page)
        
        # Should have no renderers for empty page
        self.assertEqual(len(self.canvas.renderers), 0)
    
    def test_canvas_render_page_with_components(self):
        """Test rendering page with components."""
        # Add components to page
        switch = Switch("sw1", self.page.page_id)
        switch.position = (100, 100)
        self.page.add_component(switch)
        
        indicator = Indicator("ind1", self.page.page_id)
        indicator.position = (200, 200)
        self.page.add_component(indicator)
        
        # Set page (should render components)
        self.canvas.set_page(self.page)
        
        # Should have renderers for both components
        self.assertEqual(len(self.canvas.renderers), 2)
        self.assertIn("sw1", self.canvas.renderers)
        self.assertIn("ind1", self.canvas.renderers)
    
    def test_canvas_clear_components(self):
        """Test clearing components from canvas."""
        # Add components
        switch = Switch("sw1", self.page.page_id)
        switch.position = (100, 100)
        self.page.add_component(switch)
        
        self.canvas.set_page(self.page)
        self.assertEqual(len(self.canvas.renderers), 1)
        
        # Clear components
        self.canvas.clear_components()
        self.assertEqual(len(self.canvas.renderers), 0)
    
    def test_canvas_update_component(self):
        """Test updating specific component."""
        # Add component
        switch = Switch("sw1", self.page.page_id)
        switch.position = (100, 100)
        self.page.add_component(switch)
        
        self.canvas.set_page(self.page)
        
        # Update component (should re-render)
        self.canvas.update_component("sw1")
        
        # Should still have renderer
        self.assertIn("sw1", self.canvas.renderers)
    
    def test_canvas_set_component_selected(self):
        """Test setting component selection state."""
        # Add component
        switch = Switch("sw1", self.page.page_id)
        switch.position = (100, 100)
        self.page.add_component(switch)
        
        self.canvas.set_page(self.page)
        
        # Set selected
        self.canvas.set_component_selected("sw1", True)
        self.assertTrue(self.canvas.renderers["sw1"].selected)
        
        # Clear selected
        self.canvas.set_component_selected("sw1", False)
        self.assertFalse(self.canvas.renderers["sw1"].selected)
    
    def test_canvas_set_component_powered(self):
        """Test setting component powered state."""
        # Add component
        indicator = Indicator("ind1", self.page.page_id)
        indicator.position = (200, 200)
        self.page.add_component(indicator)
        
        self.canvas.set_page(self.page)
        
        # Set powered
        self.canvas.set_component_powered("ind1", True)
        self.assertTrue(self.canvas.renderers["ind1"].powered)
        
        # Clear powered
        self.canvas.set_component_powered("ind1", False)
        self.assertFalse(self.canvas.renderers["ind1"].powered)


class TestZoomAndRotation(unittest.TestCase):
    """Tests for zoom and rotation handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = DesignCanvas(self.root)
        self.document = Document()
        # Document starts with no pages, create one
        self.page = self.document.create_page("Test Page")
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_components_render_at_zoom(self):
        """Test components render at different zoom levels."""
        # Add component
        switch = Switch("sw1", self.page.page_id)
        switch.position = (100, 100)
        self.page.add_component(switch)
        
        self.canvas.set_page(self.page)
        
        # Should render at current zoom
        self.assertGreater(len(self.canvas.renderers["sw1"].canvas_items), 0)
    
    def test_components_re_render_on_zoom(self):
        """Test components re-render when zoom changes."""
        # Add component
        switch = Switch("sw1", self.page.page_id)
        switch.position = (100, 100)
        self.page.add_component(switch)
        
        self.canvas.set_page(self.page)
        initial_items = len(self.canvas.renderers["sw1"].canvas_items)
        
        # Change zoom (should trigger re-render)
        self.canvas._apply_zoom(1.5, 500, 500)
        
        # Should still have items
        self.assertGreater(len(self.canvas.renderers["sw1"].canvas_items), 0)
    
    def test_rotated_components_render(self):
        """Test components with rotation render correctly."""
        # Add rotated component
        switch = Switch("sw1", self.page.page_id)
        switch.position = (100, 100)
        switch.rotation = 90
        self.page.add_component(switch)
        
        self.canvas.set_page(self.page)
        
        # Should create items even with rotation
        self.assertGreater(len(self.canvas.renderers["sw1"].canvas_items), 0)


if __name__ == '__main__':
    unittest.main()
