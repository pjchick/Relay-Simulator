"""
Test Logic Analyser Configuration Persistence

Verify that logic analyser configurations are correctly saved to and loaded from .rsim files.
"""

import os
import tempfile
from pathlib import Path

from core.document import Document
from fileio.document_loader import DocumentLoader


def test_logic_analyser_config_save_load():
    """Test saving and loading logic analyser configurations."""
    print("Testing logic analyser configuration persistence...")
    
    # Create a document
    doc = Document()
    page = doc.create_page("Test Page")
    
    # Add logic analyser configurations
    config1_id = doc.id_manager.generate_id()
    channel1 = {
        'name': 'Channel 1',
        'link_name': 'CLK',
        'color': '#4ec9b0'
    }
    channel2 = {
        'name': 'Channel 2',
        'link_name': 'DATA',
        'color': '#ce9178'
    }
    
    success = doc.add_logic_analyser_config(
        config1_id,
        "Main Circuit Monitor",
        [channel1, channel2]
    )
    assert success, "Failed to add first config"
    print(f"✓ Added config 1 with ID: {config1_id}")
    
    # Add a second configuration
    config2_id = doc.id_manager.generate_id()
    channel3 = {
        'name': 'Channel A',
        'link_name': 'ADDR0',
        'color': '#c586c0'
    }
    
    success = doc.add_logic_analyser_config(
        config2_id,
        "Address Bus Monitor",
        [channel3]
    )
    assert success, "Failed to add second config"
    print(f"✓ Added config 2 with ID: {config2_id}")
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rsim', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        loader = DocumentLoader()
        loader.save_to_file(doc, tmp_path)
        print(f"✓ Saved document to: {tmp_path}")
        
        # Load from file
        loaded_doc = loader.load_from_file(tmp_path)
        print("✓ Loaded document from file")
        
        # Verify configurations were loaded
        configs = loaded_doc.get_all_logic_analyser_configs()
        assert len(configs) == 2, f"Expected 2 configs, got {len(configs)}"
        print(f"✓ Loaded {len(configs)} configurations")
        
        # Verify first config
        config1 = loaded_doc.get_logic_analyser_config(config1_id)
        assert config1 is not None, "Config 1 not found"
        assert config1['name'] == "Main Circuit Monitor", f"Config 1 name mismatch: {config1['name']}"
        assert len(config1['channels']) == 2, f"Config 1 should have 2 channels, got {len(config1['channels'])}"
        assert config1['channels'][0]['link_name'] == 'CLK', "Channel 1 link_name mismatch"
        assert config1['channels'][1]['link_name'] == 'DATA', "Channel 2 link_name mismatch"
        print(f"✓ Config 1 verified: {config1['name']}")
        
        # Verify second config
        config2 = loaded_doc.get_logic_analyser_config(config2_id)
        assert config2 is not None, "Config 2 not found"
        assert config2['name'] == "Address Bus Monitor", f"Config 2 name mismatch: {config2['name']}"
        assert len(config2['channels']) == 1, f"Config 2 should have 1 channel, got {len(config2['channels'])}"
        assert config2['channels'][0]['link_name'] == 'ADDR0', "Channel A link_name mismatch"
        print(f"✓ Config 2 verified: {config2['name']}")
        
        # Test updating a config
        loaded_doc.update_logic_analyser_config(
            config1_id,
            name="Updated Monitor Name"
        )
        
        # Save and reload again
        loader.save_to_file(loaded_doc, tmp_path)
        reloaded_doc = loader.load_from_file(tmp_path)
        
        updated_config = reloaded_doc.get_logic_analyser_config(config1_id)
        assert updated_config['name'] == "Updated Monitor Name", "Config update failed to persist"
        print("✓ Config update persisted correctly")
        
        # Test removing a config
        removed = reloaded_doc.remove_logic_analyser_config(config2_id)
        assert removed, "Failed to remove config 2"
        
        loader.save_to_file(reloaded_doc, tmp_path)
        final_doc = loader.load_from_file(tmp_path)
        
        final_configs = final_doc.get_all_logic_analyser_configs()
        assert len(final_configs) == 1, f"Expected 1 config after removal, got {len(final_configs)}"
        assert final_doc.get_logic_analyser_config(config2_id) is None, "Removed config should not exist"
        print("✓ Config removal persisted correctly")
        
        print("\n✅ ALL TESTS PASSED!")
        
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            print(f"✓ Cleaned up temporary file")


def test_empty_logic_analyser_configs():
    """Test document with no logic analyser configurations."""
    print("\nTesting document with no logic analyser configs...")
    
    # Create a document without configs
    doc = Document()
    page = doc.create_page("Test Page")
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rsim', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        loader = DocumentLoader()
        loader.save_to_file(doc, tmp_path)
        
        # Load from file
        loaded_doc = loader.load_from_file(tmp_path)
        
        # Verify no configs
        configs = loaded_doc.get_all_logic_analyser_configs()
        assert len(configs) == 0, f"Expected 0 configs, got {len(configs)}"
        print("✓ Document with no configs loads correctly")
        
        print("✅ TEST PASSED!")
        
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == '__main__':
    test_logic_analyser_config_save_load()
    test_empty_logic_analyser_configs()
    print("\n🎉 All logic analyser persistence tests completed successfully!")
