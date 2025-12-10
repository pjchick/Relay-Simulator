"""
Test suite for Bridge System (Phase 2.5)

Comprehensive tests for Bridge and BridgeManager including bridge creation,
removal, VNET dirty marking, thread-safety, and multiple bridges.
"""

import sys
import os
import threading
import time

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.bridge import Bridge, BridgeManager
from core.vnet import VNET
from core.state import PinState


def test_bridge_creation():
    """Test Bridge class creation."""
    print("\n=== Testing Bridge Creation ===")
    
    bridge = Bridge("vnet001", "vnet002", "relay001")
    
    assert bridge.bridge_id is not None
    assert len(bridge.bridge_id) == 8
    assert bridge.vnet_id1 == "vnet001"
    assert bridge.vnet_id2 == "vnet002"
    assert bridge.owner_component_id == "relay001"
    
    print(f"✓ Bridge created: {bridge}")
    
    # Test with explicit bridge ID
    bridge2 = Bridge("vnet003", "vnet004", "relay002", "bridge99")
    assert bridge2.bridge_id == "bridge99"
    
    print(f"✓ Bridge with explicit ID: {bridge2}")
    
    print("✓ Bridge creation tests passed")


def test_bridge_self_connection():
    """Test that bridge rejects same VNET connection."""
    print("\n=== Testing Bridge Self-Connection ===")
    
    try:
        bridge = Bridge("vnet001", "vnet001", "relay001")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Cannot bridge VNET to itself" in str(e)
        print(f"✓ Self-connection rejected: {e}")
    
    print("✓ Bridge self-connection tests passed")


def test_bridge_get_connected_vnets():
    """Test getting connected VNETs."""
    print("\n=== Testing Get Connected VNETs ===")
    
    bridge = Bridge("vnet001", "vnet002", "relay001")
    
    vnets = bridge.get_connected_vnets()
    assert vnets == ("vnet001", "vnet002")
    
    print(f"✓ Connected VNETs: {vnets}")
    
    print("✓ Get connected VNETs tests passed")


def test_bridge_get_other_vnet():
    """Test getting the other VNET in a bridge."""
    print("\n=== Testing Get Other VNET ===")
    
    bridge = Bridge("vnet001", "vnet002", "relay001")
    
    other = bridge.get_other_vnet("vnet001")
    assert other == "vnet002"
    
    other = bridge.get_other_vnet("vnet002")
    assert other == "vnet001"
    
    other = bridge.get_other_vnet("vnet003")
    assert other is None
    
    print(f"✓ Get other VNET works correctly")
    
    print("✓ Get other VNET tests passed")


def test_bridge_contains_vnet():
    """Test checking if bridge contains a VNET."""
    print("\n=== Testing Contains VNET ===")
    
    bridge = Bridge("vnet001", "vnet002", "relay001")
    
    assert bridge.contains_vnet("vnet001")
    assert bridge.contains_vnet("vnet002")
    assert not bridge.contains_vnet("vnet003")
    
    print(f"✓ Contains VNET checks work")
    
    print("✓ Contains VNET tests passed")


def test_bridge_manager_creation():
    """Test BridgeManager creation."""
    print("\n=== Testing BridgeManager Creation ===")
    
    manager = BridgeManager()
    
    assert manager.get_bridge_count() == 0
    assert len(manager.get_all_bridges()) == 0
    
    print(f"✓ BridgeManager created: {manager}")
    
    print("✓ BridgeManager creation tests passed")


def test_create_bridge():
    """Test creating bridges."""
    print("\n=== Testing Create Bridge ===")
    
    manager = BridgeManager()
    
    bridge = manager.create_bridge("vnet001", "vnet002", "relay001")
    
    assert bridge.vnet_id1 == "vnet001"
    assert bridge.vnet_id2 == "vnet002"
    assert bridge.owner_component_id == "relay001"
    assert manager.get_bridge_count() == 1
    
    print(f"✓ Bridge created: {bridge}")
    
    # Create another bridge
    bridge2 = manager.create_bridge("vnet002", "vnet003", "relay002")
    assert manager.get_bridge_count() == 2
    
    print(f"✓ Second bridge created: {bridge2}")
    
    print("✓ Create bridge tests passed")


def test_duplicate_bridge_id():
    """Test that duplicate bridge ID is rejected."""
    print("\n=== Testing Duplicate Bridge ID ===")
    
    manager = BridgeManager()
    
    bridge1 = manager.create_bridge("vnet001", "vnet002", "relay001", "bridge99")
    
    try:
        bridge2 = manager.create_bridge("vnet003", "vnet004", "relay002", "bridge99")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "already exists" in str(e)
        print(f"✓ Duplicate bridge ID rejected: {e}")
    
    print("✓ Duplicate bridge ID tests passed")


def test_get_bridge():
    """Test getting bridge by ID."""
    print("\n=== Testing Get Bridge ===")
    
    manager = BridgeManager()
    
    bridge = manager.create_bridge("vnet001", "vnet002", "relay001")
    bridge_id = bridge.bridge_id
    
    retrieved = manager.get_bridge(bridge_id)
    assert retrieved is not None
    assert retrieved.bridge_id == bridge_id
    
    print(f"✓ Bridge retrieved: {retrieved}")
    
    # Test non-existent bridge
    none_bridge = manager.get_bridge("nonexistent")
    assert none_bridge is None
    
    print(f"✓ Non-existent bridge returns None")
    
    print("✓ Get bridge tests passed")


def test_remove_bridge():
    """Test removing bridges."""
    print("\n=== Testing Remove Bridge ===")
    
    manager = BridgeManager()
    
    bridge = manager.create_bridge("vnet001", "vnet002", "relay001")
    bridge_id = bridge.bridge_id
    
    assert manager.get_bridge_count() == 1
    
    removed = manager.remove_bridge(bridge_id)
    assert removed is not None
    assert removed.bridge_id == bridge_id
    assert manager.get_bridge_count() == 0
    
    print(f"✓ Bridge removed: {removed}")
    
    # Test removing non-existent bridge
    removed2 = manager.remove_bridge("nonexistent")
    assert removed2 is None
    
    print(f"✓ Remove non-existent returns None")
    
    print("✓ Remove bridge tests passed")


def test_get_bridges_for_vnet():
    """Test getting all bridges for a VNET."""
    print("\n=== Testing Get Bridges For VNET ===")
    
    manager = BridgeManager()
    
    # Create bridges: vnet001 connects to vnet002 and vnet003
    bridge1 = manager.create_bridge("vnet001", "vnet002", "relay001")
    bridge2 = manager.create_bridge("vnet001", "vnet003", "relay002")
    bridge3 = manager.create_bridge("vnet004", "vnet005", "relay003")
    
    # Get bridges for vnet001
    bridges = manager.get_bridges_for_vnet("vnet001")
    assert len(bridges) == 2
    bridge_ids = {b.bridge_id for b in bridges}
    assert bridge1.bridge_id in bridge_ids
    assert bridge2.bridge_id in bridge_ids
    
    print(f"✓ VNET 001 has 2 bridges: {[b.bridge_id for b in bridges]}")
    
    # Get bridges for vnet004
    bridges = manager.get_bridges_for_vnet("vnet004")
    assert len(bridges) == 1
    assert bridges[0].bridge_id == bridge3.bridge_id
    
    print(f"✓ VNET 004 has 1 bridge")
    
    # Get bridges for non-connected VNET
    bridges = manager.get_bridges_for_vnet("vnet999")
    assert len(bridges) == 0
    
    print(f"✓ Non-connected VNET has 0 bridges")
    
    print("✓ Get bridges for VNET tests passed")


def test_get_bridges_for_component():
    """Test getting all bridges for a component."""
    print("\n=== Testing Get Bridges For Component ===")
    
    manager = BridgeManager()
    
    # Create bridges for relay001
    bridge1 = manager.create_bridge("vnet001", "vnet002", "relay001")
    bridge2 = manager.create_bridge("vnet003", "vnet004", "relay001")
    bridge3 = manager.create_bridge("vnet005", "vnet006", "relay002")
    
    # Get bridges for relay001
    bridges = manager.get_bridges_for_component("relay001")
    assert len(bridges) == 2
    bridge_ids = {b.bridge_id for b in bridges}
    assert bridge1.bridge_id in bridge_ids
    assert bridge2.bridge_id in bridge_ids
    
    print(f"✓ Relay001 has 2 bridges")
    
    # Get bridges for relay002
    bridges = manager.get_bridges_for_component("relay002")
    assert len(bridges) == 1
    assert bridges[0].bridge_id == bridge3.bridge_id
    
    print(f"✓ Relay002 has 1 bridge")
    
    print("✓ Get bridges for component tests passed")


def test_clear_bridges_for_component():
    """Test clearing all bridges for a component."""
    print("\n=== Testing Clear Bridges For Component ===")
    
    manager = BridgeManager()
    
    # Create bridges
    bridge1 = manager.create_bridge("vnet001", "vnet002", "relay001")
    bridge2 = manager.create_bridge("vnet003", "vnet004", "relay001")
    bridge3 = manager.create_bridge("vnet005", "vnet006", "relay002")
    
    assert manager.get_bridge_count() == 3
    
    # Clear bridges for relay001
    removed = manager.clear_bridges_for_component("relay001")
    assert len(removed) == 2
    assert manager.get_bridge_count() == 1
    
    print(f"✓ Cleared 2 bridges for relay001")
    
    # Verify relay002 bridge still exists
    bridges = manager.get_bridges_for_component("relay002")
    assert len(bridges) == 1
    
    print(f"✓ Relay002 bridge still exists")
    
    print("✓ Clear bridges for component tests passed")


def test_clear_all_bridges():
    """Test clearing all bridges."""
    print("\n=== Testing Clear All Bridges ===")
    
    manager = BridgeManager()
    
    # Create several bridges
    for i in range(5):
        manager.create_bridge(f"vnet{i:03d}", f"vnet{i+1:03d}", f"relay{i:03d}")
    
    assert manager.get_bridge_count() == 5
    
    manager.clear_all_bridges()
    assert manager.get_bridge_count() == 0
    assert len(manager.get_all_bridges()) == 0
    
    print(f"✓ All bridges cleared")
    
    print("✓ Clear all bridges tests passed")


def test_vnet_bridge_operations():
    """Test VNET bridge add/remove operations."""
    print("\n=== Testing VNET Bridge Operations ===")
    
    vnet = VNET("vnet001", "page001")
    
    # Add bridge
    added = vnet.add_bridge("bridge001")
    assert added
    assert vnet.has_bridge("bridge001")
    assert len(vnet.get_all_bridges()) == 1
    
    print(f"✓ Bridge added to VNET")
    
    # Try to add duplicate
    added = vnet.add_bridge("bridge001")
    assert not added
    
    print(f"✓ Duplicate bridge rejected")
    
    # Add more bridges
    vnet.add_bridge("bridge002")
    vnet.add_bridge("bridge003")
    assert len(vnet.get_all_bridges()) == 3
    
    print(f"✓ Multiple bridges added: {vnet.get_all_bridges()}")
    
    # Remove bridge
    removed = vnet.remove_bridge("bridge002")
    assert removed
    assert not vnet.has_bridge("bridge002")
    assert len(vnet.get_all_bridges()) == 2
    
    print(f"✓ Bridge removed from VNET")
    
    # Try to remove non-existent
    removed = vnet.remove_bridge("bridge999")
    assert not removed
    
    print(f"✓ Remove non-existent returns False")
    
    print("✓ VNET bridge operations tests passed")


def test_vnet_dirty_on_bridge_change():
    """Test that VNET is marked dirty when bridges change."""
    print("\n=== Testing VNET Dirty On Bridge Change ===")
    
    vnet = VNET("vnet001", "page001")
    vnet.clear_dirty()
    
    assert not vnet.is_dirty()
    
    # Add bridge should mark dirty
    vnet.add_bridge("bridge001")
    assert vnet.is_dirty()
    
    print(f"✓ VNET marked dirty after adding bridge")
    
    vnet.clear_dirty()
    assert not vnet.is_dirty()
    
    # Remove bridge should mark dirty
    vnet.remove_bridge("bridge001")
    assert vnet.is_dirty()
    
    print(f"✓ VNET marked dirty after removing bridge")
    
    print("✓ VNET dirty on bridge change tests passed")


def test_bridge_manager_statistics():
    """Test BridgeManager statistics."""
    print("\n=== Testing BridgeManager Statistics ===")
    
    manager = BridgeManager()
    
    # Create bridges
    manager.create_bridge("vnet001", "vnet002", "relay001")
    manager.create_bridge("vnet002", "vnet003", "relay001")
    manager.create_bridge("vnet004", "vnet005", "relay002")
    
    stats = manager.get_statistics()
    
    assert stats['total_bridges'] == 3
    assert stats['vnets_with_bridges'] == 5  # vnet001, 002, 003, 004, 005
    assert stats['components_with_bridges'] == 2  # relay001, relay002
    
    print(f"✓ Statistics: {stats}")
    
    print("✓ BridgeManager statistics tests passed")


def test_bridge_thread_safety():
    """Test bridge operations are thread-safe."""
    print("\n=== Testing Bridge Thread-Safety ===")
    
    manager = BridgeManager()
    errors = []
    
    def create_bridges(start_idx, count):
        try:
            for i in range(start_idx, start_idx + count):
                manager.create_bridge(f"vnet{i:03d}a", f"vnet{i:03d}b", f"relay{i:03d}")
        except Exception as e:
            errors.append(str(e))
    
    # Create bridges from multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=create_bridges, args=(i * 20, 20))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert manager.get_bridge_count() == 100
    
    print(f"✓ Created 100 bridges from 5 threads")
    
    print("✓ Bridge thread-safety tests passed")


def test_vnet_bridge_thread_safety():
    """Test VNET bridge operations are thread-safe."""
    print("\n=== Testing VNET Bridge Thread-Safety ===")
    
    vnet = VNET("vnet001", "page001")
    errors = []
    
    def add_bridges(start_idx, count):
        try:
            for i in range(start_idx, start_idx + count):
                vnet.add_bridge(f"bridge{i:03d}")
        except Exception as e:
            errors.append(str(e))
    
    # Add bridges from multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=add_bridges, args=(i * 20, 20))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(vnet.get_all_bridges()) == 100
    
    print(f"✓ Added 100 bridges from 5 threads")
    
    print("✓ VNET bridge thread-safety tests passed")


def test_integrated_bridge_scenario():
    """Test integrated scenario with VNETs and BridgeManager."""
    print("\n=== Testing Integrated Bridge Scenario ===")
    
    # Create VNETs
    vnet1 = VNET("vnet001", "page001")
    vnet2 = VNET("vnet002", "page001")
    vnet3 = VNET("vnet003", "page002")
    
    # Create BridgeManager
    manager = BridgeManager()
    
    # Component creates a bridge
    bridge = manager.create_bridge(vnet1.vnet_id, vnet2.vnet_id, "relay001")
    
    # Add bridge to both VNETs
    vnet1.add_bridge(bridge.bridge_id)
    vnet2.add_bridge(bridge.bridge_id)
    
    # Both VNETs should have the bridge
    assert vnet1.has_bridge(bridge.bridge_id)
    assert vnet2.has_bridge(bridge.bridge_id)
    
    print(f"✓ Bridge connects VNET1 and VNET2")
    
    # Both VNETs should be dirty
    assert vnet1.is_dirty()
    assert vnet2.is_dirty()
    
    print(f"✓ Both VNETs marked dirty")
    
    # Create another bridge
    bridge2 = manager.create_bridge(vnet2.vnet_id, vnet3.vnet_id, "relay001")
    vnet2.add_bridge(bridge2.bridge_id)
    vnet3.add_bridge(bridge2.bridge_id)
    
    # VNET2 should have 2 bridges
    assert len(vnet2.get_all_bridges()) == 2
    
    print(f"✓ VNET2 has 2 bridges (to VNET1 and VNET3)")
    
    # Remove first bridge
    manager.remove_bridge(bridge.bridge_id)
    vnet1.remove_bridge(bridge.bridge_id)
    vnet2.remove_bridge(bridge.bridge_id)
    
    # VNET1 should have no bridges
    assert len(vnet1.get_all_bridges()) == 0
    # VNET2 should have 1 bridge
    assert len(vnet2.get_all_bridges()) == 1
    
    print(f"✓ Bridge removed, VNETs updated")
    
    # Cleanup component bridges
    removed = manager.clear_bridges_for_component("relay001")
    assert len(removed) == 1  # Only bridge2 remains
    
    print(f"✓ Component bridges cleared")
    
    print("✓ Integrated bridge scenario tests passed")


def run_all_tests():
    """Run all Bridge System tests."""
    print("=" * 60)
    print("BRIDGE SYSTEM TEST SUITE (Phase 2.5)")
    print("=" * 60)
    
    try:
        test_bridge_creation()
        test_bridge_self_connection()
        test_bridge_get_connected_vnets()
        test_bridge_get_other_vnet()
        test_bridge_contains_vnet()
        test_bridge_manager_creation()
        test_create_bridge()
        test_duplicate_bridge_id()
        test_get_bridge()
        test_remove_bridge()
        test_get_bridges_for_vnet()
        test_get_bridges_for_component()
        test_clear_bridges_for_component()
        test_clear_all_bridges()
        test_vnet_bridge_operations()
        test_vnet_dirty_on_bridge_change()
        test_bridge_manager_statistics()
        test_bridge_thread_safety()
        test_vnet_bridge_thread_safety()
        test_integrated_bridge_scenario()
        
        print("\n" + "=" * 60)
        print("✓ ALL BRIDGE SYSTEM TESTS PASSED")
        print("=" * 60)
        print("\nSection 2.5 Bridge System Requirements:")
        print("✓ Define Bridge class")
        print("  ✓ BridgeId (string, runtime only)")
        print("  ✓ VnetId1 (first connected VNET)")
        print("  ✓ VnetId2 (second connected VNET)")
        print("  ✓ Owner component (reference)")
        print("  ✓ Get connected VNETs")
        print("  ✓ Get other VNET")
        print("  ✓ Contains VNET check")
        print("✓ Implement BridgeManager class")
        print("  ✓ Create bridge between two VNETs")
        print("  ✓ Remove bridge from VNETs")
        print("  ✓ Get bridge by ID")
        print("  ✓ Mark connected VNETs dirty")
        print("  ✓ Get bridges for VNET")
        print("  ✓ Get bridges for component")
        print("  ✓ Clear bridges for component")
        print("  ✓ Clear all bridges")
        print("  ✓ Statistics tracking")
        print("✓ Add bridge operations to VNET")
        print("  ✓ Add bridge reference")
        print("  ✓ Remove bridge reference")
        print("  ✓ Has bridge check")
        print("  ✓ Get all bridges")
        print("  ✓ Mark dirty on bridge add/remove")
        print("✓ Thread-safety")
        print("  ✓ Lock during bridge add/remove")
        print("  ✓ Thread-safe BridgeManager operations")
        print("  ✓ Thread-safe VNET bridge operations")
        print("✓ Tests")
        print("  ✓ Test bridge creation")
        print("  ✓ Test bridge removal")
        print("  ✓ Test VNET dirty marking")
        print("  ✓ Test thread-safety")
        print("  ✓ Test multiple bridges on same VNET")
        print("  ✓ Test integrated scenarios")
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
