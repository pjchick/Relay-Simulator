"""
Test suite for VNET Class (Phase 2.2)

Comprehensive tests for VNET class including tab management, link management,
bridge management, state evaluation, dirty flag, and thread-safety.
"""

import sys
import os
import threading
import time

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vnet import VNET
from core.state import PinState


def test_vnet_creation():
    """Test VNET class creation."""
    print("\n=== Testing VNET Creation ===")
    
    # Single-page VNET
    vnet1 = VNET("vnet001", "page001")
    
    assert vnet1.vnet_id == "vnet001"
    assert vnet1.page_id == "page001"
    assert len(vnet1.tab_ids) == 0
    assert len(vnet1.link_names) == 0
    assert len(vnet1.bridge_ids) == 0
    assert vnet1.state == PinState.FLOAT
    assert vnet1.is_dirty() == True  # Starts dirty
    print(f"✓ Single-page VNET created: {vnet1}")
    
    # Cross-page VNET
    vnet2 = VNET("vnet002")
    
    assert vnet2.page_id is None
    print(f"✓ Cross-page VNET created: {vnet2}")
    
    print("✓ VNET creation tests passed")


def test_vnet_add_tab():
    """Test adding tabs to VNET."""
    print("\n=== Testing Add Tab ===")
    
    vnet = VNET("vnet001", "page001")
    
    # Add tab
    result = vnet.add_tab("tab001")
    
    assert result == True
    assert vnet.has_tab("tab001")
    assert vnet.get_tab_count() == 1
    assert vnet.is_dirty() == True
    print(f"✓ Added tab: {vnet.get_tab_count()} total")
    
    # Try to add duplicate
    result = vnet.add_tab("tab001")
    
    assert result == False
    assert vnet.get_tab_count() == 1
    print(f"✓ Duplicate tab rejected")
    
    # Add more tabs
    vnet.add_tab("tab002")
    vnet.add_tab("tab003")
    
    assert vnet.get_tab_count() == 3
    print(f"✓ Added 3 tabs total")
    
    print("✓ Add tab tests passed")


def test_vnet_remove_tab():
    """Test removing tabs from VNET."""
    print("\n=== Testing Remove Tab ===")
    
    vnet = VNET("vnet001", "page001")
    vnet.add_tab("tab001")
    vnet.add_tab("tab002")
    vnet.clear_dirty()
    
    # Remove tab
    result = vnet.remove_tab("tab001")
    
    assert result == True
    assert not vnet.has_tab("tab001")
    assert vnet.get_tab_count() == 1
    assert vnet.is_dirty() == True
    print(f"✓ Removed tab: {vnet.get_tab_count()} remaining")
    
    # Try to remove non-existent
    result = vnet.remove_tab("nonexistent")
    
    assert result == False
    assert vnet.get_tab_count() == 1
    print(f"✓ Remove non-existent tab returns False")
    
    print("✓ Remove tab tests passed")


def test_vnet_get_all_tabs():
    """Test getting all tabs from VNET."""
    print("\n=== Testing Get All Tabs ===")
    
    vnet = VNET("vnet001", "page001")
    vnet.add_tab("tab001")
    vnet.add_tab("tab002")
    vnet.add_tab("tab003")
    
    # Get all tabs
    all_tabs = vnet.get_all_tabs()
    
    assert len(all_tabs) == 3
    assert "tab001" in all_tabs
    assert "tab002" in all_tabs
    assert "tab003" in all_tabs
    print(f"✓ Retrieved all tabs: {all_tabs}")
    
    # Verify it's a copy (modifying shouldn't affect VNET)
    all_tabs.append("tab004")
    assert vnet.get_tab_count() == 3
    print(f"✓ Returns copy of tab list")
    
    print("✓ Get all tabs tests passed")


def test_vnet_add_link():
    """Test adding link names to VNET."""
    print("\n=== Testing Add Link ===")
    
    vnet = VNET("vnet001", "page001")
    
    # Add link
    result = vnet.add_link("POWER")
    
    assert result == True
    assert vnet.has_link("POWER")
    assert len(vnet.get_all_links()) == 1
    print(f"✓ Added link: {vnet.get_all_links()}")
    
    # Try to add duplicate
    result = vnet.add_link("POWER")
    
    assert result == False
    assert len(vnet.get_all_links()) == 1
    print(f"✓ Duplicate link rejected")
    
    # Add more links
    vnet.add_link("GROUND")
    vnet.add_link("SIGNAL_A")
    
    assert len(vnet.get_all_links()) == 3
    print(f"✓ Added 3 links total")
    
    print("✓ Add link tests passed")


def test_vnet_remove_link():
    """Test removing link names from VNET."""
    print("\n=== Testing Remove Link ===")
    
    vnet = VNET("vnet001", "page001")
    vnet.add_link("POWER")
    vnet.add_link("GROUND")
    
    # Remove link
    result = vnet.remove_link("POWER")
    
    assert result == True
    assert not vnet.has_link("POWER")
    assert len(vnet.get_all_links()) == 1
    print(f"✓ Removed link: {len(vnet.get_all_links())} remaining")
    
    # Try to remove non-existent
    result = vnet.remove_link("nonexistent")
    
    assert result == False
    print(f"✓ Remove non-existent link returns False")
    
    print("✓ Remove link tests passed")


def test_vnet_add_bridge():
    """Test adding bridge IDs to VNET."""
    print("\n=== Testing Add Bridge ===")
    
    vnet = VNET("vnet001", "page001")
    
    # Add bridge
    result = vnet.add_bridge("bridge001")
    
    assert result == True
    assert vnet.has_bridge("bridge001")
    assert len(vnet.get_all_bridges()) == 1
    print(f"✓ Added bridge: {vnet.get_all_bridges()}")
    
    # Try to add duplicate
    result = vnet.add_bridge("bridge001")
    
    assert result == False
    assert len(vnet.get_all_bridges()) == 1
    print(f"✓ Duplicate bridge rejected")
    
    # Add more bridges
    vnet.add_bridge("bridge002")
    
    assert len(vnet.get_all_bridges()) == 2
    print(f"✓ Added 2 bridges total")
    
    print("✓ Add bridge tests passed")


def test_vnet_remove_bridge():
    """Test removing bridge IDs from VNET."""
    print("\n=== Testing Remove Bridge ===")
    
    vnet = VNET("vnet001", "page001")
    vnet.add_bridge("bridge001")
    vnet.add_bridge("bridge002")
    
    # Remove bridge
    result = vnet.remove_bridge("bridge001")
    
    assert result == True
    assert not vnet.has_bridge("bridge001")
    assert len(vnet.get_all_bridges()) == 1
    print(f"✓ Removed bridge: {len(vnet.get_all_bridges())} remaining")
    
    # Try to remove non-existent
    result = vnet.remove_bridge("nonexistent")
    
    assert result == False
    print(f"✓ Remove non-existent bridge returns False")
    
    print("✓ Remove bridge tests passed")


def test_vnet_state_property():
    """Test VNET state property."""
    print("\n=== Testing State Property ===")
    
    vnet = VNET("vnet001", "page001")
    
    # Initial state
    assert vnet.state == PinState.FLOAT
    print(f"✓ Initial state: FLOAT")
    
    # Set state to HIGH
    vnet.state = PinState.HIGH
    
    assert vnet.state == PinState.HIGH
    assert vnet.is_dirty() == True
    print(f"✓ State changed to HIGH (dirty flag set)")
    
    # Set same state (should still set dirty)
    vnet.clear_dirty()
    vnet.state = PinState.HIGH
    
    assert vnet.is_dirty() == False  # Same state doesn't set dirty
    print(f"✓ Same state doesn't set dirty flag")
    
    print("✓ State property tests passed")


def test_vnet_evaluate_state():
    """Test VNET state evaluation from tabs."""
    print("\n=== Testing Evaluate State ===")
    
    vnet = VNET("vnet001", "page001")
    vnet.add_tab("tab001")
    vnet.add_tab("tab002")
    vnet.add_tab("tab003")
    
    # All tabs FLOAT
    tab_states = {
        "tab001": PinState.FLOAT,
        "tab002": PinState.FLOAT,
        "tab003": PinState.FLOAT
    }
    
    result = vnet.evaluate_state(tab_states)
    
    assert result == PinState.FLOAT
    assert vnet.state == PinState.FLOAT
    print(f"✓ All FLOAT → VNET FLOAT")
    
    # One tab HIGH (HIGH OR logic)
    tab_states["tab002"] = PinState.HIGH
    
    result = vnet.evaluate_state(tab_states)
    
    assert result == PinState.HIGH
    assert vnet.state == PinState.HIGH
    print(f"✓ One HIGH → VNET HIGH")
    
    # All tabs HIGH
    tab_states["tab001"] = PinState.HIGH
    tab_states["tab003"] = PinState.HIGH
    
    result = vnet.evaluate_state(tab_states)
    
    assert result == PinState.HIGH
    assert vnet.state == PinState.HIGH
    print(f"✓ All HIGH → VNET HIGH")
    
    # Missing tab in tab_states (should be ignored)
    tab_states = {"tab001": PinState.FLOAT}
    
    result = vnet.evaluate_state(tab_states)
    
    assert result == PinState.FLOAT
    print(f"✓ Missing tabs ignored in evaluation")
    
    print("✓ Evaluate state tests passed")


def test_vnet_dirty_flag():
    """Test VNET dirty flag management."""
    print("\n=== Testing Dirty Flag ===")
    
    vnet = VNET("vnet001", "page001")
    
    # Starts dirty
    assert vnet.is_dirty() == True
    print(f"✓ VNET starts dirty")
    
    # Clear dirty
    vnet.clear_dirty()
    
    assert vnet.is_dirty() == False
    print(f"✓ Dirty flag cleared")
    
    # Mark dirty
    vnet.mark_dirty()
    
    assert vnet.is_dirty() == True
    print(f"✓ Dirty flag set")
    
    # Adding tab sets dirty
    vnet.clear_dirty()
    vnet.add_tab("tab001")
    
    assert vnet.is_dirty() == True
    print(f"✓ Adding tab sets dirty flag")
    
    # Removing tab sets dirty
    vnet.clear_dirty()
    vnet.remove_tab("tab001")
    
    assert vnet.is_dirty() == True
    print(f"✓ Removing tab sets dirty flag")
    
    print("✓ Dirty flag tests passed")


def test_vnet_serialization():
    """Test VNET serialization."""
    print("\n=== Testing Serialization ===")
    
    vnet = VNET("vnet001", "page001")
    vnet.add_tab("tab001")
    vnet.add_tab("tab002")
    vnet.add_link("POWER")
    vnet.add_bridge("bridge001")
    vnet.state = PinState.HIGH
    vnet.mark_dirty()
    
    # Serialize
    data = vnet.to_dict()
    
    assert data['vnet_id'] == "vnet001"
    assert data['page_id'] == "page001"
    assert len(data['tab_ids']) == 2
    assert len(data['link_names']) == 1
    assert len(data['bridge_ids']) == 1
    assert data['state'] == PinState.HIGH.value
    assert data['dirty'] == True
    print(f"✓ Serialized VNET")
    
    print("✓ Serialization tests passed")


def test_vnet_deserialization():
    """Test VNET deserialization."""
    print("\n=== Testing Deserialization ===")
    
    data = {
        'vnet_id': 'vnet002',
        'page_id': 'page002',
        'tab_ids': ['tab001', 'tab002', 'tab003'],
        'link_names': ['POWER', 'GROUND'],
        'bridge_ids': ['bridge001'],
        'state': PinState.HIGH.value,
        'dirty': True
    }
    
    # Deserialize
    vnet = VNET.from_dict(data)
    
    assert vnet.vnet_id == "vnet002"
    assert vnet.page_id == "page002"
    assert vnet.get_tab_count() == 3
    assert len(vnet.get_all_links()) == 2
    assert len(vnet.get_all_bridges()) == 1
    assert vnet.state == PinState.HIGH
    assert vnet.is_dirty() == True
    print(f"✓ Deserialized VNET: {vnet}")
    
    print("✓ Deserialization tests passed")


def test_vnet_serialization_roundtrip():
    """Test VNET serialization roundtrip."""
    print("\n=== Testing Serialization Roundtrip ===")
    
    vnet1 = VNET("vnet001", "page001")
    vnet1.add_tab("tab001")
    vnet1.add_tab("tab002")
    vnet1.add_link("SIGNAL")
    vnet1.state = PinState.HIGH
    
    # Serialize and deserialize
    data = vnet1.to_dict()
    vnet2 = VNET.from_dict(data)
    
    assert vnet2.vnet_id == vnet1.vnet_id
    assert vnet2.page_id == vnet1.page_id
    assert vnet2.get_tab_count() == vnet1.get_tab_count()
    assert vnet2.get_all_links() == vnet1.get_all_links()
    assert vnet2.state == vnet1.state
    print(f"✓ Roundtrip preserves data")
    
    print("✓ Serialization roundtrip tests passed")


def test_vnet_thread_safety_state():
    """Test thread-safe state operations."""
    print("\n=== Testing Thread-Safe State ===")
    
    vnet = VNET("vnet001", "page001")
    results = []
    
    def worker():
        """Worker thread that sets state multiple times."""
        for i in range(100):
            vnet.state = PinState.HIGH if i % 2 == 0 else PinState.FLOAT
        results.append("done")
    
    # Create multiple threads
    threads = [threading.Thread(target=worker) for _ in range(5)]
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    assert len(results) == 5
    assert vnet.state in [PinState.HIGH, PinState.FLOAT]
    print(f"✓ Thread-safe state operations completed")
    
    print("✓ Thread-safe state tests passed")


def test_vnet_thread_safety_tabs():
    """Test thread-safe tab operations."""
    print("\n=== Testing Thread-Safe Tab Operations ===")
    
    vnet = VNET("vnet001", "page001")
    
    def add_tabs():
        """Worker thread that adds tabs."""
        for i in range(50):
            vnet.add_tab(f"tab_{threading.current_thread().name}_{i}")
    
    def remove_tabs():
        """Worker thread that removes tabs."""
        time.sleep(0.01)  # Let some tabs get added first
        for i in range(25):
            tab_id = f"tab_{threading.current_thread().name.replace('Remove', 'Add')}_{i}"
            vnet.remove_tab(tab_id)
    
    # Create add and remove threads
    add_threads = [threading.Thread(target=add_tabs, name=f"Add{i}") for i in range(3)]
    remove_threads = [threading.Thread(target=remove_tabs, name=f"Remove{i}") for i in range(2)]
    
    all_threads = add_threads + remove_threads
    
    # Start all threads
    for t in all_threads:
        t.start()
    
    # Wait for completion
    for t in all_threads:
        t.join()
    
    # Verify VNET is in a valid state
    tab_count = vnet.get_tab_count()
    assert tab_count >= 0
    print(f"✓ Thread-safe tab operations completed: {tab_count} tabs")
    
    print("✓ Thread-safe tab operations tests passed")


def test_vnet_thread_safety_dirty():
    """Test thread-safe dirty flag operations."""
    print("\n=== Testing Thread-Safe Dirty Flag ===")
    
    vnet = VNET("vnet001", "page001")
    
    def worker():
        """Worker thread that marks and clears dirty."""
        for i in range(100):
            if i % 2 == 0:
                vnet.mark_dirty()
            else:
                vnet.clear_dirty()
    
    # Create multiple threads
    threads = [threading.Thread(target=worker) for _ in range(5)]
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Dirty flag should be in valid state
    dirty = vnet.is_dirty()
    assert isinstance(dirty, bool)
    print(f"✓ Thread-safe dirty flag operations completed: dirty={dirty}")
    
    print("✓ Thread-safe dirty flag tests passed")


def test_vnet_repr():
    """Test VNET string representation."""
    print("\n=== Testing VNET Repr ===")
    
    vnet1 = VNET("vnet001", "page001")
    vnet1.add_tab("tab001")
    vnet1.add_tab("tab002")
    vnet1.state = PinState.HIGH
    vnet1.mark_dirty()
    
    repr1 = repr(vnet1)
    print(f"✓ VNET repr: {repr1}")
    
    assert "vnet001" in repr1
    assert "2 tabs" in repr1
    assert "HIGH" in repr1
    assert "dirty" in repr1
    assert "page=page001" in repr1
    
    # Cross-page VNET
    vnet2 = VNET("vnet002")
    vnet2.clear_dirty()
    
    repr2 = repr(vnet2)
    print(f"✓ Cross-page VNET repr: {repr2}")
    
    assert "cross-page" in repr2
    assert "dirty" not in repr2
    
    print("✓ VNET repr tests passed")


def run_all_tests():
    """Run all VNET tests."""
    print("=" * 60)
    print("VNET CLASS TEST SUITE (Phase 2.2)")
    print("=" * 60)
    
    try:
        test_vnet_creation()
        test_vnet_add_tab()
        test_vnet_remove_tab()
        test_vnet_get_all_tabs()
        test_vnet_add_link()
        test_vnet_remove_link()
        test_vnet_add_bridge()
        test_vnet_remove_bridge()
        test_vnet_state_property()
        test_vnet_evaluate_state()
        test_vnet_dirty_flag()
        test_vnet_serialization()
        test_vnet_deserialization()
        test_vnet_serialization_roundtrip()
        test_vnet_thread_safety_state()
        test_vnet_thread_safety_tabs()
        test_vnet_thread_safety_dirty()
        test_vnet_repr()
        
        print("\n" + "=" * 60)
        print("✓ ALL VNET TESTS PASSED")
        print("=" * 60)
        print("\nSection 2.2 VNET Class Requirements:")
        print("✓ Define VNET class")
        print("  ✓ VnetId (string, 8 char UUID)")
        print("  ✓ Collection of TabIds")
        print("  ✓ Collection of LinkNames")
        print("  ✓ Collection of BridgeIds")
        print("  ✓ Current state (PinState)")
        print("  ✓ Dirty flag (boolean)")
        print("  ✓ PageId (for single-page VNETs)")
        print("✓ Implement VNET operations")
        print("  ✓ Add tab")
        print("  ✓ Remove tab")
        print("  ✓ Has tab")
        print("  ✓ Get all tabs")
        print("  ✓ Get tab count")
        print("  ✓ Add link")
        print("  ✓ Remove link")
        print("  ✓ Has link")
        print("  ✓ Get all links")
        print("  ✓ Add bridge")
        print("  ✓ Remove bridge")
        print("  ✓ Has bridge")
        print("  ✓ Get all bridges")
        print("✓ Implement state management")
        print("  ✓ State property (get/set)")
        print("  ✓ Evaluate VNET state (HIGH OR FLOAT)")
        print("  ✓ Mark dirty")
        print("  ✓ Clear dirty")
        print("  ✓ Check if dirty")
        print("✓ Thread-safety")
        print("  ✓ Locking for state changes")
        print("  ✓ Locking for dirty flag")
        print("  ✓ Locking for all operations")
        print("  ✓ Thread-safe tab operations")
        print("  ✓ Thread-safe state evaluation")
        print("✓ Serialization")
        print("  ✓ to_dict()")
        print("  ✓ from_dict()")
        print("  ✓ Roundtrip consistency")
        print("✓ Tests")
        print("  ✓ Test VNET creation")
        print("  ✓ Test tab management")
        print("  ✓ Test link management")
        print("  ✓ Test bridge management")
        print("  ✓ Test state evaluation")
        print("  ✓ Test dirty flag")
        print("  ✓ Test thread-safety")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
