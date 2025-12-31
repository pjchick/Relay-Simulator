"""
Test to verify the Text component is properly integrated.
"""

import sys
import os

# Add relay_simulator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'relay_simulator'))

from components.text import Text
from components.factory import ComponentFactory
from gui.renderers.renderer_factory import RendererFactory


def test_text_component():
    """Test Text component creation and properties."""
    print("Testing Text component...")
    
    # Create Text component
    text = Text("test_text", "test_page")
    
    # Verify type
    assert text.component_type == "Text", "Component type should be 'Text'"
    print(f"  ✓ Component type: {text.component_type}")
    
    # Verify default properties
    assert text.properties['text'] == 'Text', "Default text should be 'Text'"
    assert text.properties['font_size'] == 12, "Default font size should be 12"
    assert text.properties['color'] == '#FFFFFF', "Default color should be white"
    assert text.properties['multiline'] == False, "Default multiline should be False"
    assert text.properties['justify'] == 'left', "Default justify should be 'left'"
    assert text.properties['width'] == 200, "Default width should be 200"
    print("  ✓ Default properties correct")
    
    # Test property modification
    text.properties['text'] = 'Hello World!'
    text.properties['font_size'] = 16
    text.properties['color'] = '#FF0000'
    text.properties['multiline'] = True
    text.properties['justify'] = 'right'
    
    assert text.properties['text'] == 'Hello World!'
    assert text.properties['font_size'] == 16
    assert text.properties['color'] == '#FF0000'
    assert text.properties['multiline'] == True
    assert text.properties['justify'] == 'right'
    print("  ✓ Property modification works")
    
    # Verify no pins
    assert len(text.pins) == 0, "Text component should have no pins"
    print("  ✓ No pins (passive component)")
    
    # Test simulation methods (should all be no-ops)
    text.sim_start(None, None)
    text.simulate_logic(None, None)
    text.sim_stop()
    print("  ✓ Simulation methods (no-ops)")
    
    return True


def test_factory_registration():
    """Test that Text component is registered in factory."""
    print("\nTesting Factory registration...")
    
    factory = ComponentFactory()
    
    # Create Text component via factory
    text = factory.create_component("Text", "factory_text", "test_page")
    
    assert text is not None, "Factory should create Text component"
    assert text.component_type == "Text", "Created component should be Text type"
    assert isinstance(text, Text), "Created component should be Text instance"
    print("  ✓ Text component registered in factory")
    
    return True


def test_renderer_registration():
    """Test that TextRenderer is registered."""
    print("\nTesting Renderer registration...")
    
    # Check that Text is in supported types
    supported_types = RendererFactory.get_supported_types()
    assert "Text" in supported_types, "Text should be in supported renderer types"
    print(f"  ✓ Text renderer registered")
    print(f"  Supported types: {len(supported_types)} component types")
    
    return True


def test_serialization():
    """Test Text component serialization/deserialization."""
    print("\nTesting Serialization...")
    
    # Create Text component with custom properties
    text = Text("serial_test", "page001")
    text.position = (100, 200)
    text.properties['text'] = 'Test Annotation'
    text.properties['font_size'] = 18
    text.properties['color'] = '#00FF00'
    text.properties['multiline'] = True
    text.properties['justify'] = 'right'
    
    # Serialize to dict
    data = text.to_dict()
    
    assert data['component_id'] == 'serial_test'
    assert data['component_type'] == 'Text'
    assert data['position']['x'] == 100
    assert data['position']['y'] == 200
    assert data['properties']['text'] == 'Test Annotation'
    assert data['properties']['font_size'] == 18
    print("  ✓ Serialization to dict works")
    
    # Deserialize from dict
    text2 = Text.from_dict(data)
    
    assert text2.component_id == 'serial_test'
    assert text2.position == (100, 200)
    assert text2.properties['text'] == 'Test Annotation'
    assert text2.properties['font_size'] == 18
    assert text2.properties['color'] == '#00FF00'
    assert text2.properties['multiline'] == True
    assert text2.properties['justify'] == 'right'
    print("  ✓ Deserialization from dict works")
    
    return True


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Testing Text Component Integration")
        print("=" * 60)
        
        test_text_component()
        test_factory_registration()
        test_renderer_registration()
        test_serialization()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("Text component is ready to use!")
        print("\nFeatures:")
        print("  • Multi-line text support")
        print("  • Adjustable font size (6-72)")
        print("  • 10 color options")
        print("  • Left/Right justification")
        print("  • Fixed-width console font (Consolas/Courier)")
        print("  • No pins (passive annotation only)")
        
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
