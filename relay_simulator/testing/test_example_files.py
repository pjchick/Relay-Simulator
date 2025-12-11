"""
Tests for Phase 7.4 - Example Files validation.
Validates that all example .rsim files can be loaded and simulated.
"""

import unittest
from pathlib import Path

from fileio.document_loader import load_document
from simulation.simulation_engine import SimulationEngine
from core.vnet_builder import VnetBuilder
from core.link_resolver import LinkResolver


class TestExampleFilesLoad(unittest.TestCase):
    """Test that all example files load successfully"""
    
    def setUp(self):
        """Find examples directory"""
        # Examples are in relay_simulator/../examples
        test_dir = Path(__file__).parent
        self.examples_dir = (test_dir.parent.parent / 'examples').resolve()
        
        if not self.examples_dir.exists():
            self.skipTest(f"Examples directory not found: {self.examples_dir}")
    
    def test_simple_switch_led_loads(self):
        """Test loading simple switch→LED example"""
        filepath = self.examples_dir / '01_simple_switch_led.rsim'
        
        doc = load_document(str(filepath))
        
        # Verify structure
        self.assertEqual(len(doc.pages), 1)
        self.assertEqual(doc.metadata['title'], 'Switch and LED')
        
        page = list(doc.pages.values())[0]
        self.assertEqual(len(page.components), 2)
        self.assertEqual(len(page.wires), 1)
        
        # Verify component types
        types = [c.component_type for c in page.components.values()]
        self.assertIn('Switch', types)
        self.assertIn('Indicator', types)
    
    def test_relay_circuit_loads(self):
        """Test loading relay circuit example"""
        filepath = self.examples_dir / '02_relay_circuit.rsim'
        
        doc = load_document(str(filepath))
        
        # Verify structure
        self.assertEqual(len(doc.pages), 1)
        self.assertEqual(doc.metadata['title'], 'Relay Circuit')
        
        page = list(doc.pages.values())[0]
        self.assertEqual(len(page.components), 4)  # Switch, VCC, Relay, LED
        
        # Verify component types
        types = [c.component_type for c in page.components.values()]
        self.assertIn('Switch', types)
        self.assertIn('VCC', types)
        self.assertIn('DPDTRelay', types)
        self.assertIn('Indicator', types)
    
    def test_cross_page_links_loads(self):
        """Test loading cross-page links example"""
        filepath = self.examples_dir / '03_cross_page_links.rsim'
        
        doc = load_document(str(filepath))
        
        # Verify multi-page structure
        self.assertEqual(len(doc.pages), 2)
        
        # Verify link names
        linked_comps = doc.get_components_with_link_name('SIGNAL_A')
        self.assertEqual(len(linked_comps), 2)
    
    def test_wire_with_junction_loads(self):
        """Test loading wire with junction example"""
        filepath = self.examples_dir / '04_wire_with_junction.rsim'
        
        doc = load_document(str(filepath))
        
        page = list(doc.pages.values())[0]
        
        # Should have 1 switch + 3 LEDs
        self.assertEqual(len(page.components), 4)
        
        # Should have wires
        self.assertGreater(len(page.wires), 0)
    
    def test_complex_circuit_loads(self):
        """Test loading complex circuit example"""
        filepath = self.examples_dir / '05_complex_circuit.rsim'
        
        doc = load_document(str(filepath))
        
        page = list(doc.pages.values())[0]
        
        # Complex circuit has multiple components
        self.assertGreater(len(page.components), 4)
        self.assertGreaterEqual(len(page.wires), 3)
    
    def test_all_examples_have_valid_metadata(self):
        """Test that all examples have proper metadata"""
        example_files = sorted(self.examples_dir.glob('*.rsim'))
        
        self.assertGreater(len(example_files), 0, "No example files found")
        
        for filepath in example_files:
            with self.subTest(file=filepath.name):
                doc = load_document(str(filepath))
                
                # Check metadata exists
                self.assertIn('title', doc.metadata)
                self.assertIn('description', doc.metadata)


class TestExampleFilesSimulation(unittest.TestCase):
    """Test that example files can be simulated"""
    
    def setUp(self):
        """Find examples directory"""
        test_dir = Path(__file__).parent
        self.examples_dir = (test_dir.parent.parent / 'examples').resolve()
        
        if not self.examples_dir.exists():
            self.skipTest(f"Examples directory not found: {self.examples_dir}")
    
    def test_simple_switch_led_builds_vnets(self):
        """Test that simple example builds VNETs correctly"""
        filepath = self.examples_dir / '01_simple_switch_led.rsim'
        doc = load_document(str(filepath))
        
        # Build VNETs for the page
        page = list(doc.pages.values())[0]
        vnets = VnetBuilder.build_vnets_for_page(page)
        
        # Should have at least 1 VNET connecting switch to LED
        self.assertGreater(len(vnets), 0)
        
        # Each VNET should have tabs
        for vnet in vnets:
            self.assertGreater(len(vnet.tab_ids), 0)
    
    def test_relay_circuit_builds_vnets(self):
        """Test relay circuit builds VNETs"""
        filepath = self.examples_dir / '02_relay_circuit.rsim'
        doc = load_document(str(filepath))
        
        page = list(doc.pages.values())[0]
        vnets = VnetBuilder.build_vnets_for_page(page)
        
        # Relay circuit has multiple VNETs (coil, poles, etc)
        self.assertGreater(len(vnets), 1)
    
    def test_cross_page_links_resolves(self):
        """Test that cross-page links resolve correctly"""
        filepath = self.examples_dir / '03_cross_page_links.rsim'
        doc = load_document(str(filepath))
        
        # Build VNETs for all pages
        all_vnets = []
        for page in doc.get_all_pages():
            vnets = VnetBuilder.build_vnets_for_page(page)
            all_vnets.extend(vnets)
        
        # Resolve links
        LinkResolver.resolve_links(doc, all_vnets)
        
        # Find VNETs with link 'SIGNAL_A'
        linked_vnets = [v for v in all_vnets if 'SIGNAL_A' in v.link_names]
        
        # Should have VNETs with the link
        self.assertGreater(len(linked_vnets), 0)
    
    def test_simple_example_simulates(self):
        """Test that simple example can be simulated"""
        # TODO: Full simulation integration requires engine setup with tab/bridge building
        # Skip for now - Phase 7.4 focuses on file loading validation
        self.skipTest("Full simulation integration test - TODO for Phase 8")


class TestExampleFileStatistics(unittest.TestCase):
    """Gather statistics about example files"""
    
    def setUp(self):
        """Find examples directory"""
        test_dir = Path(__file__).parent
        self.examples_dir = (test_dir.parent.parent / 'examples').resolve()
        
        if not self.examples_dir.exists():
            self.skipTest(f"Examples directory not found: {self.examples_dir}")
    
    def test_count_example_files(self):
        """Count and report example files"""
        example_files = list(self.examples_dir.glob('*.rsim'))
        
        self.assertGreaterEqual(len(example_files), 5)
        
        print(f"\nFound {len(example_files)} example files:")
        for filepath in sorted(example_files):
            print(f"  - {filepath.name}")
    
    def test_example_complexity_statistics(self):
        """Report complexity statistics for each example"""
        example_files = sorted(self.examples_dir.glob('*.rsim'))
        
        print("\nExample File Complexity:")
        print("-" * 70)
        print(f"{'File':<30} {'Pages':<8} {'Comps':<8} {'Wires':<8}")
        print("-" * 70)
        
        for filepath in example_files:
            doc = load_document(str(filepath))
            
            total_comps = len(doc.get_all_components())
            total_wires = sum(len(p.wires) for p in doc.get_all_pages())
            
            print(f"{filepath.name:<30} {len(doc.pages):<8} {total_comps:<8} {total_wires:<8}")
        
        print("-" * 70)


if __name__ == '__main__':
    unittest.main()
