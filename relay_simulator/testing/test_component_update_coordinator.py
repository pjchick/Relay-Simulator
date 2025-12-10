"""
Test Suite for Component Update Coordinator

Tests the ComponentUpdateCoordinator class including:
- Queue management (single and batch)
- Duplicate prevention
- Completion tracking and synchronization
- Timeout handling
- Thread-safety
- VNET-based queueing
- Statistics and monitoring

Author: Cascade AI
Date: 2025-12-10
"""

import sys
import threading
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.component_update_coordinator import ComponentUpdateCoordinator
from components.base import Component
from core.vnet import VNET
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class MockComponent(Component):
    """Mock component for testing."""
    
    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)
        self.logic_call_count = 0
        self.logic_delay = 0.0  # Delay in seconds for ComponentLogic
    
    def simulate_logic(self):
        """Mock simulate_logic (required abstract method)."""
        self.logic_call_count += 1
        if self.logic_delay > 0:
            time.sleep(self.logic_delay)
    
    def sim_start(self):
        """Mock sim_start (required abstract method)."""
        pass
    
    def render(self, page):
        """Mock render (required abstract method)."""
        pass


def test_basic_queueing():
    """Test basic component queueing."""
    print("Test 1: Basic component queueing")
    
    # Create components
    components = {
        'comp1': MockComponent('comp1', 'page1'),
        'comp2': MockComponent('comp2', 'page1'),
        'comp3': MockComponent('comp3', 'page1'),
    }
    
    coordinator = ComponentUpdateCoordinator(components, {})
    
    # Queue a component
    result = coordinator.queue_component_update('comp1')
    assert result == True, "Should successfully queue comp1"
    assert coordinator.get_queued_count() == 1, "Should have 1 queued"
    assert coordinator.has_pending_work() == True, "Should have pending work"
    
    # Try to queue same component again (duplicate prevention)
    result = coordinator.queue_component_update('comp1')
    assert result == False, "Should not queue duplicate"
    assert coordinator.get_queued_count() == 1, "Should still have 1 queued"
    
    # Queue invalid component
    result = coordinator.queue_component_update('invalid')
    assert result == False, "Should not queue invalid component"
    
    # Queue multiple components
    result = coordinator.queue_component_update('comp2')
    assert result == True, "Should queue comp2"
    result = coordinator.queue_component_update('comp3')
    assert result == True, "Should queue comp3"
    assert coordinator.get_queued_count() == 3, "Should have 3 queued"
    
    print("  ✓ Single component queueing works")
    print("  ✓ Duplicate prevention works")
    print("  ✓ Invalid component handling works")
    print()


def test_batch_queueing():
    """Test batch queueing operations."""
    print("Test 2: Batch queueing operations")
    
    components = {
        f'comp{i}': MockComponent(f'comp{i}', 'page1')
        for i in range(10)
    }
    
    coordinator = ComponentUpdateCoordinator(components, {})
    
    # Queue multiple at once
    component_ids = {'comp0', 'comp1', 'comp2', 'comp3', 'comp4'}
    count = coordinator.queue_multiple_updates(component_ids)
    assert count == 5, "Should queue 5 components"
    assert coordinator.get_queued_count() == 5, "Should have 5 queued"
    
    # Try to queue some duplicates
    component_ids = {'comp2', 'comp3', 'comp5', 'comp6'}  # comp2, comp3 already queued
    count = coordinator.queue_multiple_updates(component_ids)
    assert count == 2, "Should only queue 2 new components"
    assert coordinator.get_queued_count() == 7, "Should have 7 queued total"
    
    # Queue with invalid IDs
    component_ids = {'comp7', 'invalid1', 'invalid2'}
    count = coordinator.queue_multiple_updates(component_ids)
    assert count == 1, "Should only queue 1 valid component"
    
    print("  ✓ Batch queueing works")
    print("  ✓ Batch duplicate prevention works")
    print("  ✓ Batch with invalid IDs handled")
    print()


def test_vnet_based_queueing():
    """Test queueing components connected to VNETs."""
    print("Test 3: VNET-based component queueing")
    
    # Create components
    components = {
        'comp1': MockComponent('comp1', 'page1'),
        'comp2': MockComponent('comp2', 'page1'),
        'comp3': MockComponent('comp3', 'page1'),
    }
    
    # Create pins and tabs
    pin1 = Pin('pin1', components['comp1'])
    pin2 = Pin('pin2', components['comp2'])
    pin3 = Pin('pin3', components['comp3'])
    
    tab1 = Tab('tab1', (0, 0), PinState.FLOAT)
    tab2 = Tab('tab2', (0, 0), PinState.FLOAT)
    tab3 = Tab('tab3', (0, 0), PinState.FLOAT)
    
    # Link tabs to pins
    tab1.parent_pin = pin1
    tab2.parent_pin = pin2
    tab3.parent_pin = pin3
    
    # Create tabs dictionary
    tabs = {
        'tab1': tab1,
        'tab2': tab2,
        'tab3': tab3,
    }
    
    # Create VNET with tabs from comp1 and comp2
    vnet1 = VNET('vnet1', 'page1')
    vnet1.add_tab('tab1')
    vnet1.add_tab('tab2')
    
    # Create second VNET with tab from comp3
    vnet2 = VNET('vnet2', 'page1')
    vnet2.add_tab('tab3')
    
    coordinator = ComponentUpdateCoordinator(components, tabs)
    
    # Queue components for vnet1
    count = coordinator.queue_components_for_vnet(vnet1)
    assert count == 2, "Should queue 2 components from vnet1"
    assert coordinator.get_queued_count() == 2, "Should have 2 queued"
    
    # Queue components for vnet2
    count = coordinator.queue_components_for_vnet(vnet2)
    assert count == 1, "Should queue 1 component from vnet2"
    assert coordinator.get_queued_count() == 3, "Should have 3 queued total"
    
    # Queue for vnet1 again (all duplicates)
    count = coordinator.queue_components_for_vnet(vnet1)
    assert count == 0, "Should not queue duplicates"
    
    # Reset and test batch VNET queueing
    coordinator.reset()
    count = coordinator.queue_components_for_vnets([vnet1, vnet2])
    assert count == 3, "Should queue 3 components from both VNETs"
    
    print("  ✓ Single VNET queueing works")
    print("  ✓ Multiple VNET queueing works")
    print("  ✓ Automatic deduplication works")
    print()


def test_pending_updates():
    """Test pending update tracking."""
    print("Test 4: Pending update tracking")
    
    components = {
        'comp1': MockComponent('comp1', 'page1'),
        'comp2': MockComponent('comp2', 'page1'),
        'comp3': MockComponent('comp3', 'page1'),
    }
    
    coordinator = ComponentUpdateCoordinator(components, {})
    
    # Initially should be complete
    assert coordinator.is_complete() == True, "Should be complete initially"
    assert coordinator.get_pending_count() == 0, "Should have 0 pending"
    
    # Queue some components
    coordinator.queue_component_update('comp1')
    coordinator.queue_component_update('comp2')
    coordinator.queue_component_update('comp3')
    
    assert coordinator.get_queued_count() == 3, "Should have 3 queued"
    assert coordinator.get_pending_count() == 0, "Should have 0 pending yet"
    assert coordinator.is_complete() == False, "Should not be complete"
    
    # Start updates (move queued to pending)
    count = coordinator.start_updates()
    assert count == 3, "Should start 3 updates"
    assert coordinator.get_queued_count() == 0, "Should have 0 queued"
    assert coordinator.get_pending_count() == 3, "Should have 3 pending"
    
    # Get pending components
    pending = coordinator.get_pending_components()
    assert len(pending) == 3, "Should have 3 pending components"
    
    # Mark updates complete
    result = coordinator.mark_update_complete('comp1')
    assert result == True, "Should mark comp1 complete"
    assert coordinator.get_pending_count() == 2, "Should have 2 pending"
    
    result = coordinator.mark_update_complete('comp1')
    assert result == False, "Should not mark same component twice"
    
    coordinator.mark_update_complete('comp2')
    assert coordinator.get_pending_count() == 1, "Should have 1 pending"
    assert coordinator.is_complete() == False, "Should not be complete yet"
    
    coordinator.mark_update_complete('comp3')
    assert coordinator.get_pending_count() == 0, "Should have 0 pending"
    assert coordinator.is_complete() == True, "Should be complete now"
    
    print("  ✓ Queued to pending transition works")
    print("  ✓ Pending count tracking works")
    print("  ✓ Completion detection works")
    print()


def test_completion_waiting():
    """Test waiting for completion."""
    print("Test 5: Completion waiting and timeout")
    
    components = {
        'comp1': MockComponent('comp1', 'page1'),
        'comp2': MockComponent('comp2', 'page1'),
    }
    
    # Set delays to simulate slow components
    components['comp1'].logic_delay = 0.1
    components['comp2'].logic_delay = 0.1
    
    coordinator = ComponentUpdateCoordinator(components, {})
    
    # Test immediate completion (no work)
    result = coordinator.wait_for_completion(timeout=0.1)
    assert result == True, "Should complete immediately when no work"
    
    # Queue and start updates
    coordinator.queue_component_update('comp1')
    coordinator.queue_component_update('comp2')
    coordinator.start_updates()
    
    # Simulate component execution in separate thread
    def execute_components():
        time.sleep(0.05)  # Small delay before starting
        pending = coordinator.get_pending_components()
        for comp in pending:
            comp.simulate_logic()
            coordinator.mark_update_complete(comp.component_id)
    
    executor_thread = threading.Thread(target=execute_components)
    executor_thread.start()
    
    # Wait for completion with generous timeout
    result = coordinator.wait_for_completion(timeout=1.0)
    assert result == True, "Should complete within timeout"
    assert coordinator.is_complete() == True, "Should be complete"
    
    executor_thread.join()
    
    # Test timeout scenario
    coordinator.queue_component_update('comp1')
    coordinator.start_updates()
    # Don't execute the component, just wait
    result = coordinator.wait_for_completion(timeout=0.05)
    assert result == False, "Should timeout"
    assert coordinator.is_complete() == False, "Should not be complete"
    
    # Clean up
    coordinator.cancel_all_updates()
    
    print("  ✓ Immediate completion works")
    print("  ✓ Waiting for completion works")
    print("  ✓ Timeout handling works")
    print()


def test_thread_safety():
    """Test thread-safety of coordinator."""
    print("Test 6: Thread-safety")
    
    # Create many components
    components = {
        f'comp{i}': MockComponent(f'comp{i}', 'page1')
        for i in range(100)
    }
    
    coordinator = ComponentUpdateCoordinator(components, {})
    
    # Queue components from multiple threads
    def queue_worker(start_idx, count):
        for i in range(start_idx, start_idx + count):
            coordinator.queue_component_update(f'comp{i}')
            time.sleep(0.001)  # Small delay to interleave operations
    
    threads = []
    for i in range(5):
        t = threading.Thread(target=queue_worker, args=(i * 20, 20))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert coordinator.get_queued_count() == 100, "Should have all 100 queued"
    
    # Start updates
    coordinator.start_updates()
    assert coordinator.get_pending_count() == 100, "Should have all 100 pending"
    
    # Complete updates from multiple threads
    def complete_worker(start_idx, count):
        for i in range(start_idx, start_idx + count):
            coordinator.mark_update_complete(f'comp{i}')
            time.sleep(0.001)
    
    threads = []
    for i in range(5):
        t = threading.Thread(target=complete_worker, args=(i * 20, 20))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert coordinator.get_pending_count() == 0, "Should have 0 pending"
    assert coordinator.is_complete() == True, "Should be complete"
    
    print("  ✓ Concurrent queueing works")
    print("  ✓ Concurrent completion works")
    print("  ✓ No race conditions detected")
    print()


def test_cancel_updates():
    """Test canceling all updates."""
    print("Test 7: Cancel updates")
    
    components = {
        'comp1': MockComponent('comp1', 'page1'),
        'comp2': MockComponent('comp2', 'page1'),
        'comp3': MockComponent('comp3', 'page1'),
    }
    
    coordinator = ComponentUpdateCoordinator(components, {})
    
    # Queue some components
    coordinator.queue_component_update('comp1')
    coordinator.queue_component_update('comp2')
    
    # Start some updates
    coordinator.start_updates()
    coordinator.queue_component_update('comp3')
    
    assert coordinator.get_pending_count() == 2, "Should have 2 pending"
    assert coordinator.get_queued_count() == 1, "Should have 1 queued"
    
    # Cancel all
    coordinator.cancel_all_updates()
    
    assert coordinator.get_pending_count() == 0, "Should have 0 pending"
    assert coordinator.get_queued_count() == 0, "Should have 0 queued"
    assert coordinator.is_complete() == True, "Should be complete"
    
    print("  ✓ Cancel clears pending updates")
    print("  ✓ Cancel clears queued updates")
    print("  ✓ Cancel signals completion")
    print()


def test_statistics():
    """Test statistics gathering."""
    print("Test 8: Statistics")
    
    components = {
        'comp1': MockComponent('comp1', 'page1'),
        'comp2': MockComponent('comp2', 'page1'),
        'comp3': MockComponent('comp3', 'page1'),
        'comp4': MockComponent('comp4', 'page1'),
        'comp5': MockComponent('comp5', 'page1'),
    }
    
    coordinator = ComponentUpdateCoordinator(components, {})
    
    # Initial statistics
    stats = coordinator.get_statistics()
    assert stats['total_components'] == 5, "Should have 5 total components"
    assert stats['queued'] == 0, "Should have 0 queued"
    assert stats['pending'] == 0, "Should have 0 pending"
    assert stats['complete'] == True, "Should be complete"
    
    # Queue some components
    coordinator.queue_component_update('comp1')
    coordinator.queue_component_update('comp2')
    coordinator.queue_component_update('comp3')
    
    stats = coordinator.get_statistics()
    assert stats['queued'] == 3, "Should have 3 queued"
    assert stats['pending'] == 0, "Should have 0 pending"
    assert stats['complete'] == False, "Should not be complete"
    
    # Start updates
    coordinator.start_updates()
    
    stats = coordinator.get_statistics()
    assert stats['queued'] == 0, "Should have 0 queued"
    assert stats['pending'] == 3, "Should have 3 pending"
    assert stats['complete'] == False, "Should not be complete"
    
    # Complete some
    coordinator.mark_update_complete('comp1')
    coordinator.mark_update_complete('comp2')
    
    stats = coordinator.get_statistics()
    assert stats['pending'] == 1, "Should have 1 pending"
    assert stats['complete'] == False, "Should not be complete"
    
    # Complete all
    coordinator.mark_update_complete('comp3')
    
    stats = coordinator.get_statistics()
    assert stats['pending'] == 0, "Should have 0 pending"
    assert stats['complete'] == True, "Should be complete"
    
    print("  ✓ Total components counted")
    print("  ✓ Queued count tracked")
    print("  ✓ Pending count tracked")
    print("  ✓ Completion status tracked")
    print()


def test_reset():
    """Test resetting the coordinator."""
    print("Test 9: Reset functionality")
    
    components = {
        'comp1': MockComponent('comp1', 'page1'),
        'comp2': MockComponent('comp2', 'page1'),
    }
    
    coordinator = ComponentUpdateCoordinator(components, {})
    
    # Queue and start updates
    coordinator.queue_component_update('comp1')
    coordinator.start_updates()
    coordinator.queue_component_update('comp2')
    
    assert coordinator.has_pending_work() == True, "Should have pending work"
    
    # Reset
    coordinator.reset()
    
    assert coordinator.get_pending_count() == 0, "Should have 0 pending"
    assert coordinator.get_queued_count() == 0, "Should have 0 queued"
    assert coordinator.is_complete() == True, "Should be complete"
    assert coordinator.has_pending_work() == False, "Should have no pending work"
    
    # Should be able to queue again after reset
    result = coordinator.queue_component_update('comp1')
    assert result == True, "Should queue after reset"
    
    print("  ✓ Reset clears pending")
    print("  ✓ Reset clears queued")
    print("  ✓ Reset signals completion")
    print("  ✓ Can queue after reset")
    print()


def run_all_tests():
    """Run all test functions."""
    print("=" * 60)
    print("COMPONENT UPDATE COORDINATOR TEST SUITE (Phase 4.4)")
    print("=" * 60)
    print()
    
    test_basic_queueing()
    test_batch_queueing()
    test_vnet_based_queueing()
    test_pending_updates()
    test_completion_waiting()
    test_thread_safety()
    test_cancel_updates()
    test_statistics()
    test_reset()
    
    print("=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)
    print()
    print("Component Update Coordinator Requirements Met:")
    print("✓ Queue component logic updates")
    print("✓ Track pending updates")
    print("✓ Wait for completion")
    print("✓ Get all components connected to dirty VNET")
    print("✓ Queue their ComponentLogic() calls")
    print("✓ Avoid duplicate queues")
    print("✓ Count pending updates")
    print("✓ Wait for all to complete")
    print("✓ Timeout handling")
    print("✓ Thread-safe operations")
    print("✓ Batch operations")
    print("✓ Statistics and monitoring")
    print()


if __name__ == '__main__':
    run_all_tests()

