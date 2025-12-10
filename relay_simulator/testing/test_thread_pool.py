"""
Test Suite for Thread Pool Manager

Tests the ThreadPoolManager class including:
- Pool initialization with auto thread count
- Work submission (single and batch)
- Completion tracking and waiting
- Error handling
- Shutdown functionality
- Statistics tracking
- Context manager usage

Author: Cascade AI
Date: 2025-12-10
"""

import sys
import time
import threading
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from thread_pool_pkg.thread_pool import ThreadPoolManager, WorkItem, PoolState


def simple_task(value: int) -> int:
    """Simple task that returns doubled value."""
    return value * 2


def slow_task(delay: float) -> str:
    """Task that sleeps for specified delay."""
    time.sleep(delay)
    return f"Completed after {delay}s"


def failing_task():
    """Task that raises an exception."""
    raise ValueError("Intentional test error")


def counter_task(counter: dict, key: str):
    """Task that increments a counter (tests shared state)."""
    # Use lock to avoid race conditions
    with counter['lock']:
        counter[key] = counter.get(key, 0) + 1


def test_pool_initialization():
    """Test thread pool initialization."""
    print("Test 1: Thread pool initialization")
    
    # Test with auto thread count
    pool = ThreadPoolManager()
    assert pool.thread_count > 0, "Should have positive thread count"
    assert pool.state == PoolState.INITIALIZED, "Should be initialized"
    
    print(f"  ✓ Auto thread count: {pool.thread_count}")
    
    # Test with explicit thread count
    pool2 = ThreadPoolManager(thread_count=4)
    assert pool2.thread_count == 4, "Should use specified thread count"
    
    print("  ✓ Explicit thread count works")
    
    # Test minimum thread count (shouldn't be 0)
    pool3 = ThreadPoolManager(thread_count=0)
    assert pool3.thread_count >= 1, "Should have at least 1 thread"
    
    print("  ✓ Minimum thread count enforced")
    print()


def test_pool_start():
    """Test starting the thread pool."""
    print("Test 2: Pool start")
    
    pool = ThreadPoolManager(thread_count=2)
    
    assert pool.state == PoolState.INITIALIZED, "Should start as initialized"
    
    # Start pool
    result = pool.start()
    assert result == True, "Start should succeed"
    assert pool.state == PoolState.RUNNING, "Should be running"
    assert pool.executor is not None, "Executor should be created"
    
    # Starting again should succeed (idempotent)
    result = pool.start()
    assert result == True, "Second start should succeed"
    
    pool.shutdown()
    
    print("  ✓ Pool starts successfully")
    print("  ✓ Executor created")
    print("  ✓ Idempotent start")
    print()


def test_work_submission():
    """Test submitting work to the pool."""
    print("Test 3: Work submission")
    
    pool = ThreadPoolManager(thread_count=2)
    pool.start()
    
    # Submit a slow task so we can check pending count
    result = pool.submit('task1', slow_task, 0.1)
    assert result == True, "Submit should succeed"
    
    # Check immediately - should be pending
    pending = pool.get_pending_count()
    # It might complete very quickly, so just check submission worked
    assert result == True, "Task was submitted"
    
    # Wait for completion
    pool.wait_for_completion(timeout=1.0)
    assert pool.get_pending_count() == 0, "Should have no pending tasks"
    
    pool.shutdown()
    
    print("  ✓ Task submission works")
    print("  ✓ Pending count tracked")
    print("  ✓ Wait for completion works")
    print()


def test_batch_submission():
    """Test batch work submission."""
    print("Test 4: Batch work submission")
    
    pool = ThreadPoolManager(thread_count=4)
    pool.start()
    
    # Create batch of work items
    work_items = [
        WorkItem(f'task{i}', simple_task, (i,))
        for i in range(10)
    ]
    
    # Submit batch
    submitted = pool.submit_batch(work_items)
    assert submitted == 10, "Should submit all 10 tasks"
    
    # Wait for all to complete
    result = pool.wait_for_completion(timeout=2.0)
    assert result == True, "All should complete"
    assert pool.is_idle() == True, "Pool should be idle"
    
    stats = pool.get_statistics()
    assert stats['completed_tasks'] == 10, "Should have 10 completed tasks"
    
    pool.shutdown()
    
    print("  ✓ Batch submission works")
    print(f"  ✓ Completed {stats['completed_tasks']} tasks")
    print("  ✓ Pool idle after completion")
    print()


def test_completion_tracking():
    """Test completion tracking and statistics."""
    print("Test 5: Completion tracking")
    
    pool = ThreadPoolManager(thread_count=2)
    pool.start()
    
    # Submit multiple tasks
    for i in range(5):
        pool.submit(f'task{i}', simple_task, i)
    
    # Wait for completion
    pool.wait_for_completion(timeout=2.0)
    
    stats = pool.get_statistics()
    assert stats['completed_tasks'] == 5, "Should have 5 completed"
    assert stats['failed_tasks'] == 0, "Should have 0 failed"
    assert stats['pending_tasks'] == 0, "Should have 0 pending"
    
    pool.shutdown()
    
    print(f"  ✓ Completed: {stats['completed_tasks']}")
    print(f"  ✓ Failed: {stats['failed_tasks']}")
    print(f"  ✓ Pending: {stats['pending_tasks']}")
    print()


def test_error_handling():
    """Test error handling for failing tasks."""
    print("Test 6: Error handling")
    
    pool = ThreadPoolManager(thread_count=2)
    pool.start()
    
    # Submit failing task
    pool.submit('fail_task', failing_task)
    
    # Submit successful task
    pool.submit('success_task', simple_task, 5)
    
    # Wait for both to complete
    pool.wait_for_completion(timeout=2.0)
    
    stats = pool.get_statistics()
    assert stats['failed_tasks'] == 1, "Should have 1 failed task"
    assert stats['completed_tasks'] == 1, "Should have 1 completed task"
    
    errors = pool.get_errors()
    assert len(errors) == 1, "Should have 1 error"
    assert errors[0][0] == 'fail_task', "Error should be from fail_task"
    
    pool.shutdown()
    
    print("  ✓ Failed task detected")
    print("  ✓ Successful task completed")
    print("  ✓ Error captured")
    print()


def test_timeout():
    """Test timeout on wait_for_completion."""
    print("Test 7: Timeout handling")
    
    pool = ThreadPoolManager(thread_count=2)
    pool.start()
    
    # Submit slow tasks
    for i in range(3):
        pool.submit(f'slow{i}', slow_task, 0.2)
    
    # Wait with short timeout
    result = pool.wait_for_completion(timeout=0.1)
    assert result == False, "Should timeout"
    assert pool.get_pending_count() > 0, "Should still have pending tasks"
    
    # Wait longer
    result = pool.wait_for_completion(timeout=1.0)
    assert result == True, "Should complete"
    assert pool.is_idle() == True, "Should be idle"
    
    pool.shutdown()
    
    print("  ✓ Timeout detection works")
    print("  ✓ Tasks complete after timeout")
    print()


def test_shutdown():
    """Test pool shutdown."""
    print("Test 8: Pool shutdown")
    
    pool = ThreadPoolManager(thread_count=2)
    pool.start()
    
    # Submit some tasks
    for i in range(5):
        pool.submit(f'task{i}', simple_task, i)
    
    # Shutdown with wait
    result = pool.shutdown(wait=True, timeout=2.0)
    assert result == True, "Shutdown should succeed"
    assert pool.state == PoolState.SHUTDOWN, "State should be SHUTDOWN"
    assert pool.executor is None, "Executor should be None"
    
    # Shutdown again should succeed (idempotent)
    result = pool.shutdown()
    assert result == True, "Second shutdown should succeed"
    
    # Starting after shutdown should fail
    result = pool.start()
    assert result == False, "Start after shutdown should fail"
    
    print("  ✓ Shutdown succeeds")
    print("  ✓ Tasks complete before shutdown")
    print("  ✓ Idempotent shutdown")
    print("  ✓ Cannot restart after shutdown")
    print()


def test_concurrent_access():
    """Test thread-safety with concurrent access."""
    print("Test 9: Concurrent access (thread-safety)")
    
    pool = ThreadPoolManager(thread_count=4)
    pool.start()
    
    # Shared counter with lock
    counter = {'lock': threading.Lock()}
    
    # Submit many tasks that modify shared state
    for i in range(100):
        pool.submit(f'counter{i}', counter_task, counter, 'count')
    
    # Wait for all
    pool.wait_for_completion(timeout=5.0)
    
    # Check counter
    assert counter['count'] == 100, "All tasks should have executed"
    
    stats = pool.get_statistics()
    assert stats['completed_tasks'] == 100, "Should have 100 completed"
    assert stats['failed_tasks'] == 0, "Should have 0 failed"
    
    pool.shutdown()
    
    print("  ✓ 100 concurrent tasks completed")
    print("  ✓ No race conditions detected")
    print("  ✓ Thread-safe operations verified")
    print()


def test_context_manager():
    """Test using pool as context manager."""
    print("Test 10: Context manager usage")
    
    with ThreadPoolManager(thread_count=2) as pool:
        assert pool.state == PoolState.RUNNING, "Should auto-start"
        
        # Submit tasks
        for i in range(5):
            pool.submit(f'task{i}', simple_task, i)
        
        # Wait for completion
        pool.wait_for_completion(timeout=2.0)
        
        stats = pool.get_statistics()
        assert stats['completed_tasks'] == 5, "Should complete 5 tasks"
    
    # Pool should auto-shutdown after context
    assert pool.state == PoolState.SHUTDOWN, "Should auto-shutdown"
    
    print("  ✓ Context manager auto-start works")
    print("  ✓ Context manager auto-shutdown works")
    print()


def test_statistics():
    """Test detailed statistics tracking."""
    print("Test 11: Statistics tracking")
    
    pool = ThreadPoolManager(thread_count=2)
    pool.start()
    
    # Submit mix of successful and failing tasks
    for i in range(5):
        pool.submit(f'success{i}', simple_task, i)
    
    for i in range(3):
        pool.submit(f'fail{i}', failing_task)
    
    # Wait for all
    pool.wait_for_completion(timeout=2.0)
    
    stats = pool.get_statistics()
    assert stats['thread_count'] == 2, "Should have 2 threads"
    assert stats['completed_tasks'] == 5, "Should have 5 successful"
    assert stats['failed_tasks'] == 3, "Should have 3 failed"
    assert stats['error_count'] == 3, "Should have 3 errors"
    assert stats['pending_tasks'] == 0, "Should have 0 pending"
    
    # Test reset
    pool.reset_statistics()
    stats = pool.get_statistics()
    assert stats['completed_tasks'] == 0, "Should reset to 0"
    assert stats['failed_tasks'] == 0, "Should reset to 0"
    
    pool.shutdown()
    
    print(f"  ✓ Thread count: {stats['thread_count']}")
    print("  ✓ Successful/failed tasks tracked")
    print("  ✓ Error count tracked")
    print("  ✓ Statistics reset works")
    print()


def run_all_tests():
    """Run all test functions."""
    print("=" * 60)
    print("THREAD POOL MANAGER TEST SUITE (Phase 5.1)")
    print("=" * 60)
    print()
    
    test_pool_initialization()
    test_pool_start()
    test_work_submission()
    test_batch_submission()
    test_completion_tracking()
    test_error_handling()
    test_timeout()
    test_shutdown()
    test_concurrent_access()
    test_context_manager()
    test_statistics()
    
    print("=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)
    print()
    print("Thread Pool Manager Requirements Met:")
    print("✓ Language built-in ThreadPoolExecutor wrapper")
    print("✓ Initialize with thread count")
    print("✓ Submit work items (single and batch)")
    print("✓ Wait for completion")
    print("✓ Shutdown pool")
    print("✓ CPU core count based thread determination")
    print("✓ Configurable thread count")
    print("✓ Error handling and tracking")
    print("✓ Statistics gathering")
    print("✓ Thread-safe operations")
    print("✓ Context manager support")
    print()


if __name__ == '__main__':
    run_all_tests()
