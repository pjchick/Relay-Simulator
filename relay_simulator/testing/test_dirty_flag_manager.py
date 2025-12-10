"""
Test Suite for Dirty Flag Manager (Phase 4.3)

This test suite validates the dirty flag management system that tracks which
VNETs need re-evaluation during simulation.

Tests cover:
1. Marking VNETs dirty
2. Clearing dirty flags
3. Getting dirty VNETs
4. Stability detection
5. Thread-safety
6. State change detection
7. Batch operations
8. Statistics
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import threading
import time
from core.state import PinState
from core.vnet import VNET
from simulation.dirty_flag_manager import DirtyFlagManager


def test_marking_dirty():
    """Test marking VNETs as dirty."""
    print("Test 1: Marking VNETs dirty")
    
    # Create VNETs
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet2 = VNET(vnet_id="vnet002", page_id="page001")
    vnet3 = VNET(vnet_id="vnet003", page_id="page001")
    
    # Clear dirty flags (VNETs start dirty)
    vnet1.clear_dirty()
    vnet2.clear_dirty()
    vnet3.clear_dirty()
    
    # Create manager
    vnets = {"vnet001": vnet1, "vnet002": vnet2, "vnet003": vnet3}
    manager = DirtyFlagManager(vnets)
    
    # Mark vnet1 dirty
    result = manager.mark_dirty("vnet001")
    
    # Verify
    assert result == True, "Should return True when marking dirty"
    assert vnet1.is_dirty() == True, "VNET1 should be dirty"
    assert vnet2.is_dirty() == False, "VNET2 should be clean"
    assert vnet3.is_dirty() == False, "VNET3 should be clean"
    
    # Mark invalid VNET
    result = manager.mark_dirty("invalid_id")
    assert result == False, "Should return False for invalid ID"
    
    print("  ✓ Single VNET marked dirty")
    print("  ✓ Invalid ID handled correctly")
    print()


def test_clearing_dirty():
    """Test clearing dirty flags."""
    print("Test 2: Clearing dirty flags")
    
    # Create VNETs (start dirty by default)
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet2 = VNET(vnet_id="vnet002", page_id="page001")
    vnet3 = VNET(vnet_id="vnet003", page_id="page001")
    
    # Create manager
    vnets = {"vnet001": vnet1, "vnet002": vnet2, "vnet003": vnet3}
    manager = DirtyFlagManager(vnets)
    
    # Verify all start dirty
    assert vnet1.is_dirty() == True, "VNET1 should start dirty"
    
    # Clear vnet1
    result = manager.clear_dirty("vnet001")
    
    # Verify
    assert result == True, "Should return True when clearing"
    assert vnet1.is_dirty() == False, "VNET1 should be clean"
    assert vnet2.is_dirty() == True, "VNET2 should still be dirty"
    
    # Clear all
    count = manager.clear_all_dirty()
    
    assert count == 3, f"Should clear 3 VNETs, got {count}"
    assert vnet1.is_dirty() == False, "VNET1 should be clean"
    assert vnet2.is_dirty() == False, "VNET2 should be clean"
    assert vnet3.is_dirty() == False, "VNET3 should be clean"
    
    print("  ✓ Single VNET cleared")
    print("  ✓ All VNETs cleared")
    print()


def test_getting_dirty_vnets():
    """Test getting lists of dirty VNETs."""
    print("Test 3: Getting dirty VNETs")
    
    # Create VNETs
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet2 = VNET(vnet_id="vnet002", page_id="page001")
    vnet3 = VNET(vnet_id="vnet003", page_id="page001")
    
    # Clear all
    vnet1.clear_dirty()
    vnet2.clear_dirty()
    vnet3.clear_dirty()
    
    # Mark vnet1 and vnet3 dirty
    vnet1.mark_dirty()
    vnet3.mark_dirty()
    
    # Create manager
    vnets = {"vnet001": vnet1, "vnet002": vnet2, "vnet003": vnet3}
    manager = DirtyFlagManager(vnets)
    
    # Get dirty VNETs
    dirty_vnets = manager.get_dirty_vnets()
    dirty_ids = manager.get_dirty_vnet_ids()
    dirty_count = manager.get_dirty_count()
    
    # Verify
    assert len(dirty_vnets) == 2, f"Should have 2 dirty VNETs, got {len(dirty_vnets)}"
    assert len(dirty_ids) == 2, f"Should have 2 dirty IDs, got {len(dirty_ids)}"
    assert dirty_count == 2, f"Should count 2 dirty VNETs, got {dirty_count}"
    assert "vnet001" in dirty_ids, "vnet001 should be in dirty set"
    assert "vnet003" in dirty_ids, "vnet003 should be in dirty set"
    assert "vnet002" not in dirty_ids, "vnet002 should not be in dirty set"
    
    # Check specific VNET
    assert manager.is_dirty("vnet001") == True, "vnet001 should be dirty"
    assert manager.is_dirty("vnet002") == False, "vnet002 should be clean"
    
    print("  ✓ Get dirty VNETs list")
    print("  ✓ Get dirty VNET IDs")
    print("  ✓ Get dirty count")
    print("  ✓ Check specific VNET")
    print()


def test_stability_detection():
    """Test stability detection (no dirty VNETs)."""
    print("Test 4: Stability detection")
    
    # Create VNETs
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet2 = VNET(vnet_id="vnet002", page_id="page001")
    
    # Create manager
    vnets = {"vnet001": vnet1, "vnet002": vnet2}
    manager = DirtyFlagManager(vnets)
    
    # Initially dirty (VNETs start dirty)
    assert manager.is_stable() == False, "Should not be stable (VNETs start dirty)"
    assert manager.has_dirty_vnets() == True, "Should have dirty VNETs"
    
    # Clear all
    manager.clear_all_dirty()
    
    # Now stable
    assert manager.is_stable() == True, "Should be stable (all clean)"
    assert manager.has_dirty_vnets() == False, "Should have no dirty VNETs"
    
    # Mark one dirty
    manager.mark_dirty("vnet001")
    
    # Not stable anymore
    assert manager.is_stable() == False, "Should not be stable (one dirty)"
    assert manager.has_dirty_vnets() == True, "Should have dirty VNETs"
    
    print("  ✓ Stability detection working")
    print("  ✓ has_dirty_vnets() working")
    print()


def test_thread_safety():
    """Test thread-safe operations."""
    print("Test 5: Thread-safety")
    
    # Create VNETs
    vnets = {}
    for i in range(100):
        vnet = VNET(vnet_id=f"vnet{i:03d}", page_id="page001")
        vnet.clear_dirty()  # Start clean
        vnets[f"vnet{i:03d}"] = vnet
    
    # Create manager
    manager = DirtyFlagManager(vnets)
    
    # Thread function: mark VNETs dirty
    def mark_worker(start, end):
        for i in range(start, end):
            manager.mark_dirty(f"vnet{i:03d}")
    
    # Thread function: clear VNETs
    def clear_worker(start, end):
        for i in range(start, end):
            manager.clear_dirty(f"vnet{i:03d}")
    
    # Create threads
    threads = []
    
    # Mark threads
    for i in range(5):
        t = threading.Thread(target=mark_worker, args=(i*20, (i+1)*20))
        threads.append(t)
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Verify all marked
    assert manager.get_dirty_count() == 100, "All VNETs should be dirty"
    
    # Now clear with threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=clear_worker, args=(i*20, (i+1)*20))
        threads.append(t)
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    # Verify all cleared
    assert manager.get_dirty_count() == 0, "All VNETs should be clean"
    assert manager.is_stable() == True, "Should be stable"
    
    print("  ✓ Thread-safe marking")
    print("  ✓ Thread-safe clearing")
    print("  ✓ No race conditions detected")
    print()


def test_state_change_detection():
    """Test detecting state changes and marking dirty."""
    print("Test 6: State change detection")
    
    # Create VNETs with states
    vnet1 = VNET(vnet_id="vnet001", page_id="page001")
    vnet1.state = PinState.FLOAT
    vnet1.clear_dirty()
    
    vnet2 = VNET(vnet_id="vnet002", page_id="page001")
    vnet2.state = PinState.HIGH
    vnet2.clear_dirty()
    
    # Create manager
    vnets = {"vnet001": vnet1, "vnet002": vnet2}
    manager = DirtyFlagManager(vnets)
    
    # Detect state change: FLOAT → HIGH (should mark dirty)
    changed = manager.detect_state_change_and_mark_dirty("vnet001", PinState.HIGH)
    
    assert changed == True, "Should detect state change"
    assert vnet1.is_dirty() == True, "VNET1 should be marked dirty"
    
    # Detect no change: HIGH → HIGH (should not mark dirty)
    vnet2.clear_dirty()
    changed = manager.detect_state_change_and_mark_dirty("vnet002", PinState.HIGH)
    
    assert changed == False, "Should not detect change (same state)"
    assert vnet2.is_dirty() == False, "VNET2 should stay clean"
    
    print("  ✓ State change detected and marked dirty")
    print("  ✓ No change detected when state same")
    print()


def test_batch_operations():
    """Test batch marking and clearing operations."""
    print("Test 7: Batch operations")
    
    # Create VNETs
    vnets = {}
    for i in range(10):
        vnet = VNET(vnet_id=f"vnet{i:03d}", page_id="page001")
        vnet.clear_dirty()
        vnets[f"vnet{i:03d}"] = vnet
    
    # Create manager
    manager = DirtyFlagManager(vnets)
    
    # Batch mark
    ids_to_mark = {"vnet000", "vnet002", "vnet004", "vnet006", "vnet008"}
    count = manager.mark_multiple_dirty(ids_to_mark)
    
    assert count == 5, f"Should mark 5 VNETs, got {count}"
    assert manager.get_dirty_count() == 5, "Should have 5 dirty VNETs"
    
    # Batch clear
    ids_to_clear = {"vnet000", "vnet002"}
    count = manager.clear_multiple_dirty(ids_to_clear)
    
    assert count == 2, f"Should clear 2 VNETs, got {count}"
    assert manager.get_dirty_count() == 3, "Should have 3 dirty VNETs remaining"
    
    # Batch detect and mark
    manager.clear_all_dirty()
    vnets["vnet001"].state = PinState.FLOAT
    vnets["vnet003"].state = PinState.HIGH
    
    vnet_states = {
        "vnet001": PinState.HIGH,  # Change: FLOAT → HIGH
        "vnet003": PinState.HIGH,  # No change: HIGH → HIGH
        "vnet005": PinState.FLOAT  # No change: FLOAT → FLOAT
    }
    
    marked = manager.batch_detect_and_mark(vnet_states)
    
    assert "vnet001" in marked, "vnet001 should be marked (state changed)"
    assert "vnet003" not in marked, "vnet003 should not be marked (no change)"
    assert "vnet005" not in marked, "vnet005 should not be marked (no change)"
    assert len(marked) == 1, f"Should mark 1 VNET, got {len(marked)}"
    
    print("  ✓ Batch mark multiple VNETs")
    print("  ✓ Batch clear multiple VNETs")
    print("  ✓ Batch detect and mark")
    print()


def test_mark_all_dirty():
    """Test marking all VNETs dirty (simulation start)."""
    print("Test 8: Mark all dirty (simulation start)")
    
    # Create VNETs
    vnets = {}
    for i in range(5):
        vnet = VNET(vnet_id=f"vnet{i:03d}", page_id="page001")
        vnet.clear_dirty()  # Start clean
        vnets[f"vnet{i:03d}"] = vnet
    
    # Create manager
    manager = DirtyFlagManager(vnets)
    
    # Verify all clean
    assert manager.is_stable() == True, "Should be stable initially"
    
    # Mark all dirty (simulation start)
    count = manager.mark_all_dirty()
    
    assert count == 5, f"Should mark 5 VNETs, got {count}"
    assert manager.get_dirty_count() == 5, "All VNETs should be dirty"
    assert manager.is_stable() == False, "Should not be stable"
    
    print("  ✓ All VNETs marked dirty")
    print("  ✓ Typical simulation start scenario")
    print()


def test_statistics():
    """Test statistics gathering."""
    print("Test 9: Statistics")
    
    # Create VNETs
    vnets = {}
    for i in range(10):
        vnet = VNET(vnet_id=f"vnet{i:03d}", page_id="page001")
        vnet.clear_dirty()
        vnets[f"vnet{i:03d}"] = vnet
    
    # Create manager
    manager = DirtyFlagManager(vnets)
    
    # Mark 3 dirty
    manager.mark_dirty("vnet001")
    manager.mark_dirty("vnet003")
    manager.mark_dirty("vnet007")
    
    # Get statistics
    stats = manager.get_statistics()
    
    assert stats['total_vnets'] == 10, "Should have 10 total VNETs"
    assert stats['dirty_vnets'] == 3, "Should have 3 dirty VNETs"
    assert stats['clean_vnets'] == 7, "Should have 7 clean VNETs"
    assert stats['dirty_percentage'] == 30.0, f"Should be 30%, got {stats['dirty_percentage']}"
    assert stats['is_stable'] == False, "Should not be stable"
    
    # Clear all and check again
    manager.clear_all_dirty()
    stats = manager.get_statistics()
    
    assert stats['dirty_vnets'] == 0, "Should have 0 dirty VNETs"
    assert stats['is_stable'] == True, "Should be stable"
    assert stats['dirty_percentage'] == 0.0, "Should be 0%"
    
    print("  ✓ Statistics calculated correctly")
    print(f"  ✓ Total: {stats['total_vnets']}, Dirty: {stats['dirty_vnets']}, Clean: {stats['clean_vnets']}")
    print()


def test_reset():
    """Test resetting dirty flags."""
    print("Test 10: Reset")
    
    # Create VNETs (all start dirty)
    vnets = {}
    for i in range(5):
        vnet = VNET(vnet_id=f"vnet{i:03d}", page_id="page001")
        vnets[f"vnet{i:03d}"] = vnet
    
    # Create manager
    manager = DirtyFlagManager(vnets)
    
    # Verify all dirty initially
    assert manager.get_dirty_count() == 5, "All should start dirty"
    
    # Reset
    manager.reset()
    
    # Verify all clean
    assert manager.get_dirty_count() == 0, "All should be clean after reset"
    assert manager.is_stable() == True, "Should be stable after reset"
    
    print("  ✓ Reset clears all dirty flags")
    print()


def run_all_tests():
    """Run all dirty flag manager tests."""
    print("=" * 60)
    print("DIRTY FLAG MANAGER TEST SUITE (Phase 4.3)")
    print("=" * 60)
    print()
    
    tests = [
        test_marking_dirty,
        test_clearing_dirty,
        test_getting_dirty_vnets,
        test_stability_detection,
        test_thread_safety,
        test_state_change_detection,
        test_batch_operations,
        test_mark_all_dirty,
        test_statistics,
        test_reset,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All tests PASSED!")
        print("\nDirty Flag Manager implementation verified:")
        print("  ✓ Track all VNETs")
        print("  ✓ Mark VNET dirty")
        print("  ✓ Clear VNET dirty")
        print("  ✓ Get all dirty VNETs")
        print("  ✓ Check if any VNETs dirty")
        print("  ✓ Component requests pin state change")
        print("  ✓ Compare with current VNET state")
        print("  ✓ If different → mark dirty")
        print("  ✓ Lock when marking/clearing dirty")
        print("  ✓ Atomic dirty flag operations")
        print("  ✓ Batch operations support")
        print("  ✓ Statistics and monitoring")
        return 0
    else:
        print(f"\n✗ {failed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
