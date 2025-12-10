"""
Thread Pool Manager

Provides a wrapper around Python's built-in ThreadPoolExecutor for managing
concurrent work execution in the relay simulator. Handles work submission,
completion tracking, and graceful shutdown.

The thread pool is used to parallelize VNET evaluation and component logic
execution, improving simulation performance on multi-core systems.

Author: Cascade AI
Date: 2025-12-10
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import Callable, List, Any, Optional, Dict
from dataclasses import dataclass
from enum import Enum


class PoolState(Enum):
    """Thread pool state enumeration."""
    INITIALIZED = "initialized"
    RUNNING = "running"
    SHUTDOWN = "shutdown"
    ERROR = "error"


@dataclass
class WorkItem:
    """Represents a unit of work to be executed in the thread pool."""
    task_id: str
    function: Callable
    args: tuple = ()
    kwargs: dict = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


class ThreadPoolManager:
    """
    Thread pool manager for concurrent task execution.
    
    Wraps Python's ThreadPoolExecutor with additional features:
    - Automatic thread count determination based on CPU cores
    - Work submission with task IDs
    - Completion tracking
    - Error collection
    - Graceful shutdown
    - Statistics gathering
    
    Thread-safe: All operations use locks for coordination.
    
    Attributes:
        thread_count: Number of worker threads
        state: Current pool state
        executor: Underlying ThreadPoolExecutor
        pending_futures: Dictionary of task_id -> Future
        completed_tasks: Count of completed tasks
        failed_tasks: Count of failed tasks
        errors: List of (task_id, exception) tuples
    """
    
    def __init__(self, thread_count: Optional[int] = None, max_workers: Optional[int] = None):
        """
        Initialize the thread pool manager.
        
        Args:
            thread_count: Number of worker threads. If None, uses CPU count.
            max_workers: Deprecated alias for thread_count (for compatibility)
        """
        # Handle both parameter names
        if max_workers is not None and thread_count is None:
            thread_count = max_workers
        
        # Determine thread count
        if thread_count is None:
            thread_count = self._determine_optimal_thread_count()
        
        self.thread_count = max(1, thread_count)  # At least 1 thread
        
        # State management
        self.state = PoolState.INITIALIZED
        self._state_lock = threading.RLock()
        
        # Thread pool
        self.executor: Optional[ThreadPoolExecutor] = None
        
        # Work tracking
        self.pending_futures: Dict[str, Future] = {}
        self._futures_lock = threading.RLock()
        
        # Statistics
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.errors: List[tuple] = []
        self._stats_lock = threading.RLock()
    
    def _determine_optimal_thread_count(self) -> int:
        """
        Determine optimal thread count based on CPU cores.
        
        Strategy:
        - Use os.cpu_count() to get logical CPU count
        - For CPU-bound tasks: Use CPU count
        - For I/O-bound tasks: Could use more, but relay simulation is CPU-bound
        - Minimum of 1, maximum of 32 for safety
        
        Returns:
            Optimal thread count
        """
        try:
            cpu_count = os.cpu_count()
            if cpu_count is None:
                return 4  # Reasonable default
            
            # Use CPU count for CPU-bound simulation work
            # Cap at 32 to avoid excessive overhead
            return min(max(1, cpu_count), 32)
        except Exception:
            return 4  # Safe default
    
    def start(self) -> bool:
        """
        Start the thread pool.
        
        Creates the underlying ThreadPoolExecutor and transitions to RUNNING state.
        
        Returns:
            True if started successfully, False otherwise
        """
        with self._state_lock:
            if self.state == PoolState.RUNNING:
                return True  # Already running
            
            if self.state == PoolState.SHUTDOWN:
                return False  # Cannot restart after shutdown
            
            try:
                self.executor = ThreadPoolExecutor(max_workers=self.thread_count)
                self.state = PoolState.RUNNING
                return True
            except Exception as e:
                print(f"Error starting thread pool: {e}")
                self.state = PoolState.ERROR
                return False
    
    def submit(self, task_id: str, function: Callable, *args, **kwargs) -> bool:
        """
        Submit a task to the thread pool.
        
        Args:
            task_id: Unique identifier for this task
            function: Callable to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            True if submitted successfully, False otherwise
        """
        with self._state_lock:
            if self.state != PoolState.RUNNING:
                return False
            
            if self.executor is None:
                return False
        
        try:
            # Submit work to executor
            future = self.executor.submit(function, *args, **kwargs)
            
            # Track future
            with self._futures_lock:
                self.pending_futures[task_id] = future
            
            # Add completion callback
            future.add_done_callback(lambda f: self._on_task_complete(task_id, f))
            
            return True
            
        except Exception as e:
            print(f"Error submitting task {task_id}: {e}")
            return False
    
    def submit_batch(self, work_items: List[WorkItem]) -> int:
        """
        Submit multiple tasks at once.
        
        Args:
            work_items: List of WorkItem objects to submit
            
        Returns:
            Number of tasks successfully submitted
        """
        submitted = 0
        for item in work_items:
            if self.submit(item.task_id, item.function, *item.args, **item.kwargs):
                submitted += 1
        return submitted
    
    def _on_task_complete(self, task_id: str, future: Future):
        """
        Callback when a task completes.
        
        Args:
            task_id: ID of the completed task
            future: Completed Future object
        """
        # Remove from pending
        with self._futures_lock:
            self.pending_futures.pop(task_id, None)
        
        # Update statistics
        with self._stats_lock:
            try:
                # Check if task succeeded or failed
                exception = future.exception()
                if exception:
                    self.failed_tasks += 1
                    self.errors.append((task_id, exception))
                else:
                    self.completed_tasks += 1
            except Exception as e:
                self.failed_tasks += 1
                self.errors.append((task_id, e))
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all pending tasks to complete.
        
        Args:
            timeout: Maximum time to wait in seconds. None = wait forever.
            
        Returns:
            True if all tasks completed, False if timeout occurred
        """
        with self._futures_lock:
            pending = list(self.pending_futures.values())
        
        if not pending:
            return True
        
        try:
            # Wait for all futures to complete
            for future in as_completed(pending, timeout=timeout):
                pass  # Just need to wait
            return True
        except Exception:
            # Timeout or other error
            return False
    
    def get_pending_count(self) -> int:
        """
        Get the number of pending tasks.
        
        Returns:
            Count of tasks not yet completed
        """
        with self._futures_lock:
            return len(self.pending_futures)
    
    def is_idle(self) -> bool:
        """
        Check if the pool has no pending work.
        
        Returns:
            True if no pending tasks, False otherwise
        """
        return self.get_pending_count() == 0
    
    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Shutdown the thread pool.
        
        Args:
            wait: Whether to wait for pending tasks to complete
            timeout: Maximum time to wait for completion (if wait=True)
            
        Returns:
            True if shutdown successful, False otherwise
        """
        with self._state_lock:
            if self.state == PoolState.SHUTDOWN:
                return True  # Already shut down
            
            if self.executor is None:
                self.state = PoolState.SHUTDOWN
                return True
            
            try:
                # Wait for pending tasks if requested
                if wait and timeout is not None:
                    self.wait_for_completion(timeout)
                
                # Shutdown executor
                self.executor.shutdown(wait=wait)
                self.executor = None
                
                # Clear pending futures
                with self._futures_lock:
                    self.pending_futures.clear()
                
                self.state = PoolState.SHUTDOWN
                return True
                
            except Exception as e:
                print(f"Error shutting down thread pool: {e}")
                self.state = PoolState.ERROR
                return False
    
    def get_statistics(self) -> dict:
        """
        Get thread pool statistics.
        
        Returns:
            Dictionary containing:
                - thread_count: Number of worker threads
                - state: Current pool state
                - pending_tasks: Number of pending tasks
                - completed_tasks: Number of completed tasks
                - failed_tasks: Number of failed tasks
                - error_count: Number of errors encountered
        """
        with self._stats_lock:
            with self._futures_lock:
                return {
                    'thread_count': self.thread_count,
                    'state': self.state.value,
                    'pending_tasks': len(self.pending_futures),
                    'completed_tasks': self.completed_tasks,
                    'failed_tasks': self.failed_tasks,
                    'error_count': len(self.errors)
                }
    
    def get_errors(self) -> List[tuple]:
        """
        Get list of errors that occurred during task execution.
        
        Returns:
            List of (task_id, exception) tuples
        """
        with self._stats_lock:
            return list(self.errors)
    
    def clear_errors(self):
        """Clear the error list."""
        with self._stats_lock:
            self.errors.clear()
    
    def reset_statistics(self):
        """Reset statistics counters."""
        with self._stats_lock:
            self.completed_tasks = 0
            self.failed_tasks = 0
            self.errors.clear()
    
    def get_state(self) -> PoolState:
        """
        Get current pool state.
        
        Returns:
            Current PoolState
        """
        with self._state_lock:
            return self.state
    
    def __enter__(self):
        """Context manager entry - start the pool."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - shutdown the pool."""
        self.shutdown(wait=True)
        return False
