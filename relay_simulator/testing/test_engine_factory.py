"""
Tests for Simulation Engine Factory

Tests the factory's ability to select the appropriate engine based on
configuration and component count.

Author: Cascade AI
Date: 2025-12-10
"""

import unittest
from typing import Dict

from core.vnet import VNET
from core.tab import Tab
from core.pin import Pin
from core.bridge import Bridge
from components.base import Component
from components.vcc import VCC
from components.switch import Switch
from simulation.simulation_engine import SimulationEngine
from simulation.threaded_simulation_engine import ThreadedSimulationEngine
from simulation.engine_factory import (
    SimulationEngineFactory,
    EngineConfig,
    EngineMode,
    create_engine
)


class TestEngineConfig(unittest.TestCase):
    """Test EngineConfig class."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = EngineConfig()
        
        self.assertEqual(config.mode, EngineMode.AUTO)
        self.assertIsNone(config.thread_count)
        self.assertEqual(config.auto_threshold, 2000)
        self.assertEqual(config.max_iterations, 10000)
        self.assertEqual(config.timeout_seconds, 30.0)
    
    def test_string_mode_conversion(self):
        """Test string to EngineMode conversion."""
        config1 = EngineConfig(mode='single')
        self.assertEqual(config1.mode, EngineMode.SINGLE_THREADED)
        
        config2 = EngineConfig(mode='multi')
        self.assertEqual(config2.mode, EngineMode.MULTI_THREADED)
        
        config3 = EngineConfig(mode='auto')
        self.assertEqual(config3.mode, EngineMode.AUTO)
    
    def test_custom_threshold(self):
        """Test custom auto threshold."""
        config = EngineConfig(auto_threshold=5000)
        self.assertEqual(config.auto_threshold, 5000)
    
    def test_custom_thread_count(self):
        """Test custom thread count."""
        config = EngineConfig(mode='multi', thread_count=8)
        self.assertEqual(config.thread_count, 8)


class TestSimulationEngineFactory(unittest.TestCase):
    """Test SimulationEngineFactory class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create minimal data structures
        self.vnets: Dict[str, VNET] = {}
        self.tabs: Dict[str, Tab] = {}
        self.bridges: Dict[str, Bridge] = {}
        self.components: Dict[str, Component] = {}
    
    def _create_components(self, count: int):
        """Helper to create test components."""
        for i in range(count):
            comp = VCC(f"VCC_{i:04d}", "PAGE_01")
            self.components[comp.component_id] = comp
            
            # Create pin and tab
            pin = comp.get_pin("P0")
            if pin and pin.tabs:
                for tab in pin.tabs.values():
                    self.tabs[tab.tab_id] = tab
    
    def test_create_single_threaded_explicit(self):
        """Test explicit single-threaded engine creation."""
        self._create_components(100)
        
        config = EngineConfig(mode=EngineMode.SINGLE_THREADED)
        engine = SimulationEngineFactory.create_engine(
            self.vnets, self.tabs, self.bridges, self.components, config
        )
        
        self.assertIsInstance(engine, SimulationEngine)
        self.assertNotIsInstance(engine, ThreadedSimulationEngine)
    
    def test_create_multi_threaded_explicit(self):
        """Test explicit multi-threaded engine creation."""
        self._create_components(100)
        
        config = EngineConfig(mode=EngineMode.MULTI_THREADED)
        engine = SimulationEngineFactory.create_engine(
            self.vnets, self.tabs, self.bridges, self.components, config
        )
        
        self.assertIsInstance(engine, ThreadedSimulationEngine)
    
    def test_auto_mode_small_circuit(self):
        """Test auto mode selects single-threaded for small circuits."""
        self._create_components(100)  # < 2000
        
        config = EngineConfig(mode=EngineMode.AUTO)
        engine = SimulationEngineFactory.create_engine(
            self.vnets, self.tabs, self.bridges, self.components, config
        )
        
        self.assertIsInstance(engine, SimulationEngine)
        self.assertNotIsInstance(engine, ThreadedSimulationEngine)
    
    def test_auto_mode_large_circuit(self):
        """Test auto mode selects multi-threaded for large circuits."""
        self._create_components(2500)  # > 2000
        
        config = EngineConfig(mode=EngineMode.AUTO)
        engine = SimulationEngineFactory.create_engine(
            self.vnets, self.tabs, self.bridges, self.components, config
        )
        
        self.assertIsInstance(engine, ThreadedSimulationEngine)
    
    def test_auto_mode_threshold_boundary(self):
        """Test auto mode at threshold boundary."""
        self._create_components(2000)  # Exactly at threshold
        
        config = EngineConfig(mode=EngineMode.AUTO)
        engine = SimulationEngineFactory.create_engine(
            self.vnets, self.tabs, self.bridges, self.components, config
        )
        
        # At threshold, should use multi-threaded
        self.assertIsInstance(engine, ThreadedSimulationEngine)
    
    def test_custom_threshold(self):
        """Test custom auto threshold."""
        self._create_components(3000)
        
        # High threshold - should use single-threaded
        config = EngineConfig(mode=EngineMode.AUTO, auto_threshold=5000)
        engine = SimulationEngineFactory.create_engine(
            self.vnets, self.tabs, self.bridges, self.components, config
        )
        
        self.assertIsInstance(engine, SimulationEngine)
        self.assertNotIsInstance(engine, ThreadedSimulationEngine)
    
    def test_default_config(self):
        """Test using default configuration."""
        self._create_components(100)
        
        engine = SimulationEngineFactory.create_engine(
            self.vnets, self.tabs, self.bridges, self.components
        )
        
        # Default is auto mode, <2000 components = single-threaded
        self.assertIsInstance(engine, SimulationEngine)
        self.assertNotIsInstance(engine, ThreadedSimulationEngine)
    
    def test_convenience_method_single_threaded(self):
        """Test convenience method for single-threaded."""
        self._create_components(100)
        
        engine = SimulationEngineFactory.create_single_threaded(
            self.vnets, self.tabs, self.bridges, self.components
        )
        
        self.assertIsInstance(engine, SimulationEngine)
        self.assertNotIsInstance(engine, ThreadedSimulationEngine)
    
    def test_convenience_method_multi_threaded(self):
        """Test convenience method for multi-threaded."""
        self._create_components(100)
        
        engine = SimulationEngineFactory.create_multi_threaded(
            self.vnets, self.tabs, self.bridges, self.components,
            thread_count=4
        )
        
        self.assertIsInstance(engine, ThreadedSimulationEngine)
        self.assertEqual(engine.thread_pool.thread_count, 4)
    
    def test_get_recommended_mode_small(self):
        """Test recommendation for small circuits."""
        mode = SimulationEngineFactory.get_recommended_mode(500)
        self.assertEqual(mode, EngineMode.SINGLE_THREADED)
    
    def test_get_recommended_mode_large(self):
        """Test recommendation for large circuits."""
        mode = SimulationEngineFactory.get_recommended_mode(3000)
        self.assertEqual(mode, EngineMode.MULTI_THREADED)
    
    def test_thread_count_propagation(self):
        """Test thread count is propagated to engine."""
        self._create_components(100)
        
        config = EngineConfig(mode=EngineMode.MULTI_THREADED, thread_count=8)
        engine = SimulationEngineFactory.create_engine(
            self.vnets, self.tabs, self.bridges, self.components, config
        )
        
        self.assertEqual(engine.thread_pool.thread_count, 8)
    
    def test_max_iterations_propagation(self):
        """Test max_iterations is propagated to engine."""
        self._create_components(100)
        
        config = EngineConfig(mode=EngineMode.SINGLE_THREADED, max_iterations=5000)
        engine = SimulationEngineFactory.create_engine(
            self.vnets, self.tabs, self.bridges, self.components, config
        )
        
        self.assertEqual(engine.max_iterations, 5000)
    
    def test_timeout_propagation(self):
        """Test timeout_seconds is propagated to engine."""
        self._create_components(100)
        
        config = EngineConfig(mode=EngineMode.SINGLE_THREADED, timeout_seconds=60.0)
        engine = SimulationEngineFactory.create_engine(
            self.vnets, self.tabs, self.bridges, self.components, config
        )
        
        self.assertEqual(engine.timeout_seconds, 60.0)


class TestConvenienceFunction(unittest.TestCase):
    """Test the create_engine convenience function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.vnets: Dict[str, VNET] = {}
        self.tabs: Dict[str, Tab] = {}
        self.bridges: Dict[str, Bridge] = {}
        self.components: Dict[str, Component] = {}
    
    def _create_components(self, count: int):
        """Helper to create test components."""
        for i in range(count):
            comp = VCC(f"VCC_{i:04d}", "PAGE_01")
            self.components[comp.component_id] = comp
    
    def test_auto_mode_default(self):
        """Test default auto mode."""
        self._create_components(100)
        
        engine = create_engine(
            self.vnets, self.tabs, self.bridges, self.components
        )
        
        self.assertIsInstance(engine, SimulationEngine)
    
    def test_explicit_single(self):
        """Test explicit single mode."""
        self._create_components(100)
        
        engine = create_engine(
            self.vnets, self.tabs, self.bridges, self.components,
            mode='single'
        )
        
        self.assertIsInstance(engine, SimulationEngine)
        self.assertNotIsInstance(engine, ThreadedSimulationEngine)
    
    def test_explicit_multi(self):
        """Test explicit multi mode."""
        self._create_components(100)
        
        engine = create_engine(
            self.vnets, self.tabs, self.bridges, self.components,
            mode='multi'
        )
        
        self.assertIsInstance(engine, ThreadedSimulationEngine)
    
    def test_with_thread_count(self):
        """Test with custom thread count."""
        self._create_components(100)
        
        engine = create_engine(
            self.vnets, self.tabs, self.bridges, self.components,
            mode='multi',
            thread_count=6
        )
        
        self.assertEqual(engine.thread_pool.thread_count, 6)
    
    def test_with_custom_params(self):
        """Test with custom parameters."""
        self._create_components(100)
        
        engine = create_engine(
            self.vnets, self.tabs, self.bridges, self.components,
            mode='single',
            max_iterations=5000,
            timeout_seconds=45.0
        )
        
        self.assertEqual(engine.max_iterations, 5000)
        self.assertEqual(engine.timeout_seconds, 45.0)


class TestEngineSelection(unittest.TestCase):
    """Integration tests for engine selection logic."""
    
    def test_small_circuit_performance_hint(self):
        """Test that small circuits get single-threaded engine."""
        vnets = {}
        tabs = {}
        bridges = {}
        components = {}
        
        # Create 500 component circuit
        for i in range(500):
            comp = VCC(f"VCC_{i:04d}", "PAGE_01")
            components[comp.component_id] = comp
        
        # Should automatically select single-threaded
        engine = create_engine(vnets, tabs, bridges, components)
        
        self.assertIsInstance(engine, SimulationEngine)
        self.assertNotIsInstance(engine, ThreadedSimulationEngine)
    
    def test_large_circuit_performance_hint(self):
        """Test that large circuits get multi-threaded engine."""
        vnets = {}
        tabs = {}
        bridges = {}
        components = {}
        
        # Create 3000 component circuit
        for i in range(3000):
            comp = VCC(f"VCC_{i:04d}", "PAGE_01")
            components[comp.component_id] = comp
        
        # Should automatically select multi-threaded
        engine = create_engine(vnets, tabs, bridges, components)
        
        self.assertIsInstance(engine, ThreadedSimulationEngine)
    
    def test_override_recommendation(self):
        """Test overriding automatic recommendation."""
        vnets = {}
        tabs = {}
        bridges = {}
        components = {}
        
        # Create small circuit (would normally be single-threaded)
        for i in range(100):
            comp = VCC(f"VCC_{i:04d}", "PAGE_01")
            components[comp.component_id] = comp
        
        # Force multi-threaded
        engine = create_engine(vnets, tabs, bridges, components, mode='multi')
        
        self.assertIsInstance(engine, ThreadedSimulationEngine)


if __name__ == '__main__':
    unittest.main()
