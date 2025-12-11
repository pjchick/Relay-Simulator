"""
Comprehensive tests for serialization/deserialization of all core classes.
Tests that to_dict() and from_dict() properly round-trip all data.
"""

import unittest
import json
from core.tab import Tab
from core.pin import Pin
from core.wire import Wire, Waypoint, Junction
from core.page import Page
from core.document import Document
from components.switch import Switch
from components.indicator import Indicator
from components.dpdt_relay import DPDTRelay
from components.vcc import VCC


class TestTabSerialization(unittest.TestCase):
    """Test Tab serialization/deserialization"""
    
    def test_tab_to_dict(self):
        """Test tab serialization to dict"""
        # Create a minimal pin for parent reference
        from components.switch import Switch
        comp = Switch('comp001', 'page001')
        pin = Pin('pin001', comp)
        
        tab = Tab('tab001', pin, (10.5, 20.3))
        
        data = tab.to_dict()
        
        self.assertEqual(data['tab_id'], 'tab001')
        self.assertIsInstance(data['position'], dict)
        self.assertEqual(data['position']['x'], 10.5)
        self.assertEqual(data['position']['y'], 20.3)
    
    def test_tab_from_dict(self):
        """Test tab deserialization from dict"""
        from components.switch import Switch
        comp = Switch('comp001', 'page001')
        pin = Pin('pin001', comp)
        
        data = {
            'tab_id': 'tab001',
            'position': {'x': 10.5, 'y': 20.3}
        }
        
        tab = Tab.from_dict(data, pin)
        
        self.assertEqual(tab.tab_id, 'tab001')
        self.assertEqual(tab.relative_position, (10.5, 20.3))
        self.assertEqual(tab.parent_pin, pin)
    
    def test_tab_round_trip(self):
        """Test tab serialization round trip"""
        from components.switch import Switch
        comp = Switch('comp001', 'page001')
        pin = Pin('pin001', comp)
        
        original = Tab('tab001', pin, (15.0, 25.0))
        data = original.to_dict()
        reconstructed = Tab.from_dict(data, pin)
        
        self.assertEqual(original.tab_id, reconstructed.tab_id)
        self.assertEqual(original.relative_position, reconstructed.relative_position)


class TestPinSerialization(unittest.TestCase):
    """Test Pin serialization/deserialization"""
    
    def test_pin_to_dict(self):
        """Test pin serialization to dict"""
        from components.switch import Switch
        comp = Switch('comp001', 'page001')
        pin = Pin('pin001', comp)
        
        # Add tabs
        tab1 = Tab('tab001', pin, (0.0, -20.0))
        tab2 = Tab('tab002', pin, (20.0, 0.0))
        pin.add_tab(tab1)
        pin.add_tab(tab2)
        
        data = pin.to_dict()
        
        self.assertEqual(data['pin_id'], 'pin001')
        self.assertIsInstance(data['tabs'], list)
        self.assertEqual(len(data['tabs']), 2)
    
    def test_pin_from_dict(self):
        """Test pin deserialization from dict"""
        from components.switch import Switch
        comp = Switch('comp001', 'page001')
        
        data = {
            'pin_id': 'pin001',
            'tabs': [
                {'tab_id': 'tab001', 'position': {'x': 0.0, 'y': -20.0}},
                {'tab_id': 'tab002', 'position': {'x': 20.0, 'y': 0.0}}
            ]
        }
        
        pin = Pin.from_dict(data, comp)
        
        self.assertEqual(pin.pin_id, 'pin001')
        self.assertEqual(len(pin.tabs), 2)
        self.assertIn('tab001', pin.tabs)
        self.assertIn('tab002', pin.tabs)
    
    def test_pin_round_trip(self):
        """Test pin serialization round trip"""
        from components.switch import Switch
        comp = Switch('comp001', 'page001')
        
        original = Pin('pin001', comp)
        original.add_tab(Tab('tab001', original, (0.0, -20.0)))
        original.add_tab(Tab('tab002', original, (20.0, 0.0)))
        
        data = original.to_dict()
        reconstructed = Pin.from_dict(data, comp)
        
        self.assertEqual(original.pin_id, reconstructed.pin_id)
        self.assertEqual(len(original.tabs), len(reconstructed.tabs))


class TestWaypointSerialization(unittest.TestCase):
    """Test Waypoint serialization/deserialization"""
    
    def test_waypoint_to_dict(self):
        """Test waypoint serialization"""
        wp = Waypoint('wp001', (100, 200))
        data = wp.to_dict()
        
        self.assertEqual(data['waypoint_id'], 'wp001')
        self.assertIsInstance(data['position'], dict)
        self.assertEqual(data['position']['x'], 100)
        self.assertEqual(data['position']['y'], 200)
    
    def test_waypoint_from_dict(self):
        """Test waypoint deserialization"""
        data = {
            'waypoint_id': 'wp001',
            'position': {'x': 100, 'y': 200}
        }
        
        wp = Waypoint.from_dict(data)
        
        self.assertEqual(wp.waypoint_id, 'wp001')
        self.assertEqual(wp.position, (100, 200))
    
    def test_waypoint_round_trip(self):
        """Test waypoint serialization round trip"""
        original = Waypoint('wp001', (150, 250))
        data = original.to_dict()
        reconstructed = Waypoint.from_dict(data)
        
        self.assertEqual(original.waypoint_id, reconstructed.waypoint_id)
        self.assertEqual(original.position, reconstructed.position)


class TestJunctionSerialization(unittest.TestCase):
    """Test Junction serialization/deserialization"""
    
    def test_junction_to_dict_no_children(self):
        """Test junction serialization without child wires"""
        junction = Junction('junc001', (200, 300))
        data = junction.to_dict()
        
        self.assertEqual(data['junction_id'], 'junc001')
        self.assertIsInstance(data['position'], dict)
        self.assertEqual(data['position']['x'], 200)
        self.assertEqual(data['position']['y'], 300)
        self.assertIsInstance(data['child_wires'], list)
        self.assertEqual(len(data['child_wires']), 0)
    
    def test_junction_to_dict_with_children(self):
        """Test junction serialization with child wires"""
        junction = Junction('junc001', (200, 300))
        
        wire1 = Wire('wire002', 'junc001', 'tab002')
        wire2 = Wire('wire003', 'junc001', 'tab003')
        junction.add_child_wire(wire1)
        junction.add_child_wire(wire2)
        
        data = junction.to_dict()
        
        self.assertEqual(len(data['child_wires']), 2)
        self.assertIsInstance(data['child_wires'], list)
    
    def test_junction_from_dict(self):
        """Test junction deserialization"""
        data = {
            'junction_id': 'junc001',
            'position': {'x': 200, 'y': 300},
            'child_wires': [
                {
                    'wire_id': 'wire002',
                    'start_tab_id': 'junc001',
                    'end_tab_id': 'tab002'
                }
            ]
        }
        
        junction = Junction.from_dict(data)
        
        self.assertEqual(junction.junction_id, 'junc001')
        self.assertEqual(junction.position, (200, 300))
        self.assertEqual(len(junction.child_wires), 1)
    
    def test_junction_round_trip(self):
        """Test junction serialization round trip"""
        original = Junction('junc001', (250, 350))
        wire = Wire('wire002', 'junc001', 'tab002')
        original.add_child_wire(wire)
        
        data = original.to_dict()
        reconstructed = Junction.from_dict(data)
        
        self.assertEqual(original.junction_id, reconstructed.junction_id)
        self.assertEqual(original.position, reconstructed.position)
        self.assertEqual(len(original.child_wires), len(reconstructed.child_wires))


class TestWireSerialization(unittest.TestCase):
    """Test Wire serialization/deserialization"""
    
    def test_wire_simple_to_dict(self):
        """Test simple wire serialization (no waypoints/junctions)"""
        wire = Wire('wire001', 'tab001', 'tab002')
        data = wire.to_dict()
        
        self.assertEqual(data['wire_id'], 'wire001')
        self.assertEqual(data['start_tab_id'], 'tab001')
        self.assertEqual(data['end_tab_id'], 'tab002')
        self.assertNotIn('waypoints', data)  # Optional, shouldn't be present if empty
        self.assertNotIn('junctions', data)
    
    def test_wire_with_waypoints_to_dict(self):
        """Test wire with waypoints serialization"""
        wire = Wire('wire001', 'tab001', 'tab002')
        wire.add_waypoint(Waypoint('wp001', (100, 150)))
        wire.add_waypoint(Waypoint('wp002', (200, 250)))
        
        data = wire.to_dict()
        
        self.assertIn('waypoints', data)
        self.assertIsInstance(data['waypoints'], list)
        self.assertEqual(len(data['waypoints']), 2)
    
    def test_wire_with_junction_to_dict(self):
        """Test wire with junction serialization"""
        wire = Wire('wire001', 'tab001', None)
        junction = Junction('junc001', (150, 200))
        wire.add_junction(junction)
        
        data = wire.to_dict()
        
        self.assertIn('junctions', data)
        self.assertIsInstance(data['junctions'], list)
        self.assertEqual(len(data['junctions']), 1)
        self.assertNotIn('end_tab_id', data)  # None, shouldn't be present
    
    def test_wire_from_dict(self):
        """Test wire deserialization"""
        data = {
            'wire_id': 'wire001',
            'start_tab_id': 'tab001',
            'end_tab_id': 'tab002',
            'waypoints': [
                {'waypoint_id': 'wp001', 'position': {'x': 100, 'y': 150}}
            ]
        }
        
        wire = Wire.from_dict(data)
        
        self.assertEqual(wire.wire_id, 'wire001')
        self.assertEqual(wire.start_tab_id, 'tab001')
        self.assertEqual(wire.end_tab_id, 'tab002')
        self.assertEqual(len(wire.waypoints), 1)
    
    def test_wire_round_trip(self):
        """Test wire serialization round trip"""
        original = Wire('wire001', 'tab001', 'tab002')
        original.add_waypoint(Waypoint('wp001', (100, 150)))
        
        data = original.to_dict()
        reconstructed = Wire.from_dict(data)
        
        self.assertEqual(original.wire_id, reconstructed.wire_id)
        self.assertEqual(original.start_tab_id, reconstructed.start_tab_id)
        self.assertEqual(original.end_tab_id, reconstructed.end_tab_id)
        self.assertEqual(len(original.waypoints), len(reconstructed.waypoints))


class TestComponentSerialization(unittest.TestCase):
    """Test Component serialization/deserialization"""
    
    def test_toggle_switch_to_dict(self):
        """Test Switch serialization"""
        switch = Switch('sw001', 'page001')
        switch.position = (100, 200)
        switch.rotation = 90
        switch.set_property('label', 'SW1')
        switch.set_property('mode', 'toggle')
        
        data = switch.to_dict()
        
        self.assertEqual(data['component_id'], 'sw001')
        self.assertEqual(data['component_type'], 'Switch')
        self.assertIsInstance(data['position'], dict)
        self.assertEqual(data['position']['x'], 100)
        self.assertEqual(data['position']['y'], 200)
        self.assertEqual(data['rotation'], 90)
        self.assertIsInstance(data['pins'], list)
        self.assertIn('properties', data)
        self.assertEqual(data['properties']['label'], 'SW1')
    
    def test_indicator_to_dict(self):
        """Test Indicator serialization"""
        led = Indicator('led001', 'page001')
        led.position = (300, 400)
        led.set_property('label', 'LED1')
        led.set_property('color', 'red')
        
        data = led.to_dict()
        
        self.assertEqual(data['component_id'], 'led001')
        self.assertEqual(data['component_type'], 'Indicator')
        self.assertEqual(data['position']['x'], 300)
        self.assertEqual(data['position']['y'], 400)
        self.assertEqual(len(data['pins']), 1)
    
    def test_dpdt_relay_to_dict(self):
        """Test DPDTRelay serialization"""
        relay = DPDTRelay('rly001', 'page001')
        relay.position = (500, 600)
        relay.rotation = 180
        relay.set_property('label', 'K1')
        
        data = relay.to_dict()
        
        self.assertEqual(data['component_id'], 'rly001')
        self.assertEqual(data['component_type'], 'DPDTRelay')
        self.assertEqual(data['rotation'], 180)
        self.assertEqual(len(data['pins']), 7)  # Coil + 2 poles × 3
    
    def test_vcc_to_dict(self):
        """Test VCC serialization"""
        vcc = VCC('vcc001', 'page001')
        vcc.position = (50, 50)
        
        data = vcc.to_dict()
        
        self.assertEqual(data['component_id'], 'vcc001')
        self.assertEqual(data['component_type'], 'VCC')
        self.assertEqual(len(data['pins']), 1)
    
    def test_component_with_link_name(self):
        """Test component serialization with link name"""
        switch = Switch('sw001', 'page001')
        switch.link_name = 'SIGNAL_A'
        
        data = switch.to_dict()
        
        self.assertIn('link_name', data)
        self.assertEqual(data['link_name'], 'SIGNAL_A')
    
    def test_component_optional_fields(self):
        """Test that optional fields are only included when non-default"""
        switch = Switch('sw001', 'page001')
        # rotation defaults to 0, link_name to None, properties to {}
        
        data = switch.to_dict()
        
        # rotation = 0 should not be included
        self.assertNotIn('rotation', data)
        # link_name = None should not be included
        self.assertNotIn('link_name', data)
        # properties = {} may or may not be included (component sets defaults)


class TestPageSerialization(unittest.TestCase):
    """Test Page serialization/deserialization"""
    
    def test_page_to_dict_empty(self):
        """Test empty page serialization"""
        page = Page('page001', 'Test Page')
        data = page.to_dict()
        
        self.assertEqual(data['page_id'], 'page001')
        self.assertEqual(data['name'], 'Test Page')
        # Empty components/wires should not be included
        self.assertNotIn('components', data)
        self.assertNotIn('wires', data)
    
    def test_page_to_dict_with_components(self):
        """Test page serialization with components"""
        page = Page('page001', 'Test Page')
        
        switch = Switch('sw001', 'page001')
        led = Indicator('led001', 'page001')
        page.add_component(switch)
        page.add_component(led)
        
        data = page.to_dict()
        
        self.assertIn('components', data)
        self.assertIsInstance(data['components'], list)
        self.assertEqual(len(data['components']), 2)
    
    def test_page_to_dict_with_wires(self):
        """Test page serialization with wires"""
        page = Page('page001', 'Test Page')
        
        wire = Wire('wire001', 'tab001', 'tab002')
        page.add_wire(wire)
        
        data = page.to_dict()
        
        self.assertIn('wires', data)
        self.assertIsInstance(data['wires'], list)
        self.assertEqual(len(data['wires']), 1)
    
    def test_page_from_dict(self):
        """Test page deserialization"""
        data = {
            'page_id': 'page001',
            'name': 'Test Page',
            'wires': [
                {
                    'wire_id': 'wire001',
                    'start_tab_id': 'tab001',
                    'end_tab_id': 'tab002'
                }
            ]
        }
        
        page = Page.from_dict(data)
        
        self.assertEqual(page.page_id, 'page001')
        self.assertEqual(page.name, 'Test Page')
        self.assertEqual(len(page.wires), 1)
    
    def test_page_round_trip(self):
        """Test page serialization round trip"""
        original = Page('page001', 'Test Page')
        wire = Wire('wire001', 'tab001', 'tab002')
        original.add_wire(wire)
        
        data = original.to_dict()
        reconstructed = Page.from_dict(data)
        
        self.assertEqual(original.page_id, reconstructed.page_id)
        self.assertEqual(original.name, reconstructed.name)
        self.assertEqual(len(original.wires), len(reconstructed.wires))


class TestDocumentSerialization(unittest.TestCase):
    """Test Document serialization/deserialization"""
    
    def test_document_to_dict_minimal(self):
        """Test minimal document serialization"""
        doc = Document()
        page = Page('page001', 'Main')
        doc.add_page(page)
        
        data = doc.to_dict()
        
        self.assertIn('version', data)
        self.assertEqual(data['version'], '1.0.0')
        self.assertIn('pages', data)
        self.assertIsInstance(data['pages'], list)
        self.assertEqual(len(data['pages']), 1)
    
    def test_document_to_dict_with_metadata(self):
        """Test document serialization with metadata"""
        doc = Document()
        doc.metadata = {
            'title': 'Test Circuit',
            'author': 'Test User',
            'description': 'Test description'
        }
        page = Page('page001', 'Main')
        doc.add_page(page)
        
        data = doc.to_dict()
        
        self.assertIn('metadata', data)
        self.assertEqual(data['metadata']['title'], 'Test Circuit')
        self.assertEqual(data['metadata']['author'], 'Test User')
    
    def test_document_from_dict(self):
        """Test document deserialization"""
        data = {
            'version': '1.0.0',
            'metadata': {
                'title': 'Test Circuit'
            },
            'pages': [
                {
                    'page_id': 'page001',
                    'name': 'Main'
                }
            ]
        }
        
        doc = Document.from_dict(data)
        
        self.assertEqual(doc.metadata['title'], 'Test Circuit')
        self.assertEqual(len(doc.pages), 1)
        self.assertIn('page001', doc.pages)
    
    def test_document_version_validation(self):
        """Test document version compatibility validation"""
        data = {
            'version': '2.0.0',  # Incompatible major version
            'pages': []
        }
        
        with self.assertRaises(ValueError) as context:
            Document.from_dict(data)
        
        self.assertIn('Incompatible', str(context.exception))
    
    def test_document_round_trip(self):
        """Test document serialization round trip"""
        original = Document()
        original.metadata = {'title': 'Test', 'author': 'User'}
        page = Page('page001', 'Main')
        original.add_page(page)
        
        data = original.to_dict()
        reconstructed = Document.from_dict(data)
        
        self.assertEqual(original.metadata['title'], reconstructed.metadata['title'])
        self.assertEqual(len(original.pages), len(reconstructed.pages))


class TestCompleteCircuitSerialization(unittest.TestCase):
    """Test complete circuit serialization (integration)"""
    
    def test_simple_switch_Indicator_circuit(self):
        """Test serialization of complete switch→Indicator circuit"""
        # Create document
        doc = Document()
        doc.metadata = {
            'title': 'Switch and Indicator Test',
            'description': 'Simple test circuit'
        }
        
        # Create page
        page = Page('page001', 'Main')
        doc.add_page(page)
        
        # Create switch
        switch = Switch('sw000001', 'page001')
        switch.position = (100, 100)
        switch.set_property('label', 'SW1')
        switch.set_property('mode', 'toggle')
        page.add_component(switch)
        
        # Create Indicator
        led = Indicator('led00001', 'page001')
        led.position = (300, 100)
        led.set_property('label', 'LED1')
        led.set_property('color', 'green')
        page.add_component(led)
        
        # Create wire
        # Get tab IDs from components (need to access first pin's tabs)
        switch_pin = list(switch.pins.values())[0]
        switch_tab = list(switch_pin.tabs.values())[0]
        led_pin = list(led.pins.values())[0]
        led_tab = list(led_pin.tabs.values())[0]
        
        wire = Wire('wire0001', switch_tab.tab_id, led_tab.tab_id)
        page.add_wire(wire)
        
        # Serialize
        data = doc.to_dict()
        
        # Verify structure
        self.assertEqual(data['version'], '1.0.0')
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(len(data['pages'][0]['components']), 2)
        self.assertEqual(len(data['pages'][0]['wires']), 1)
        
        # Verify it's valid JSON
        json_str = json.dumps(data, indent=2)
        self.assertIsInstance(json_str, str)
        
        # Round trip
        reconstructed = Document.from_dict(data)
        self.assertEqual(len(reconstructed.pages), 1)
    
    def test_cross_page_links(self):
        """Test serialization of cross-page linked components"""
        doc = Document()
        
        # Page 1: Input
        page1 = Page('page001', 'Input')
        doc.add_page(page1)
        
        switch = Switch('sw000001', 'page001')
        switch.link_name = 'SIGNAL_A'
        switch.set_property('label', 'Input A')
        page1.add_component(switch)
        
        # Page 2: Output
        page2 = Page('page002', 'Output')
        doc.add_page(page2)
        
        led = Indicator('led00001', 'page002')
        led.link_name = 'SIGNAL_A'
        led.set_property('label', 'Output A')
        page2.add_component(led)
        
        # Serialize
        data = doc.to_dict()
        
        # Verify both components have link_name
        comp_data = []
        for page_data in data['pages']:
            for comp_data_item in page_data.get('components', []):
                comp_data.append(comp_data_item)
        
        self.assertEqual(len(comp_data), 2)
        self.assertEqual(comp_data[0]['link_name'], 'SIGNAL_A')
        self.assertEqual(comp_data[1]['link_name'], 'SIGNAL_A')
    
    def test_json_serialization_compatibility(self):
        """Test that serialized data is valid JSON"""
        doc = Document()
        page = Page('page001', 'Main')
        doc.add_page(page)
        
        switch = Switch('sw001', 'page001')
        page.add_component(switch)
        
        # Serialize to dict
        data = doc.to_dict()
        
        # Convert to JSON string and back
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        
        # Verify structure preserved
        self.assertEqual(parsed['version'], data['version'])
        self.assertEqual(len(parsed['pages']), len(data['pages']))


if __name__ == '__main__':
    unittest.main()


