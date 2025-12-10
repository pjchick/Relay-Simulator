"""
Thread-Safe Component Wrapper

Provides thread-safety for component state access and pin operations
during parallel execution in the simulation engine.

This wrapper adds locking mechanisms to ensure that component state
remains consistent when accessed from multiple threads.

Author: Cascade AI
Date: 2025-12-10
"""

import threading
from typing import Any, Dict, Optional
from contextlib import contextmanager

from components.base import Component


class ThreadSafeComponent:
    """
    Thread-safe wrapper for Component instances.
    
    Provides locking mechanisms to protect:
    - Component state access during simulate_logic()
    - Pin state reads and writes
    - Property access
    
    The wrapper uses a RLock (reentrant lock) to allow the same thread
    to acquire the lock multiple times, which is necessary when
    component logic calls multiple methods that need the lock.
    
    Attributes:
        component: The wrapped Component instance
        _lock: RLock for thread-safe access
        _execution_errors: List of errors during parallel execution
    """
    
    def __init__(self, component: Component):
        """
        Initialize thread-safe wrapper.
        
        Args:
            component: Component instance to wrap
        """
        if not isinstance(component, Component):
            raise TypeError("component must be a Component instance")
        
        self._component = component
        self._lock = threading.RLock()
        self._execution_errors = []
    
    @property
    def component(self) -> Component:
        """Get the wrapped component."""
        return self._component
    
    @property
    def component_id(self) -> str:
        """Get component ID (thread-safe)."""
        return self._component.component_id
    
    @property
    def component_type(self) -> str:
        """Get component type (thread-safe)."""
        return self._component.component_type
    
    @contextmanager
    def lock(self):
        """
        Context manager for acquiring component lock.
        
        Usage:
            with thread_safe_comp.lock():
                # Thread-safe operations
                comp.simulate_logic()
        
        Yields:
            None
        """
        self._lock.acquire()
        try:
            yield
        finally:
            self._lock.release()
    
    def execute_logic_safe(self) -> tuple[bool, Optional[Exception]]:
        """
        Execute component logic with thread-safety.
        
        Acquires lock before calling simulate_logic() and releases
        after completion or error.
        
        Returns:
            Tuple of (success, exception)
            - success: True if logic executed without error
            - exception: Exception object if error occurred, None otherwise
        """
        with self._lock:
            try:
                self._component.simulate_logic()
                return (True, None)
            except Exception as e:
                self._execution_errors.append(e)
                return (False, e)
    
    def get_pin_state_safe(self, pin_id: str) -> Optional[Any]:
        """
        Get pin state with thread-safety.
        
        Args:
            pin_id: Pin ID to query
            
        Returns:
            Pin state or None if pin not found
        """
        with self._lock:
            pin = self._component.get_pin(pin_id)
            if pin is None:
                return None
            
            # Pin already has its own lock, so this is safe
            return pin.state
    
    def set_pin_state_safe(self, pin_id: str, state: Any) -> bool:
        """
        Set pin state with thread-safety.
        
        Args:
            pin_id: Pin ID to set
            state: New state value
            
        Returns:
            True if successful, False if pin not found
        """
        with self._lock:
            pin = self._component.get_pin(pin_id)
            if pin is None:
                return False
            
            # Pin already has its own lock, so this is safe
            pin.state = state
            return True
    
    def get_property_safe(self, key: str, default: Any = None) -> Any:
        """
        Get component property with thread-safety.
        
        Args:
            key: Property key
            default: Default value if key not found
            
        Returns:
            Property value or default
        """
        with self._lock:
            return self._component.properties.get(key, default)
    
    def set_property_safe(self, key: str, value: Any) -> None:
        """
        Set component property with thread-safety.
        
        Args:
            key: Property key
            value: Property value
        """
        with self._lock:
            self._component.properties[key] = value
    
    def get_execution_errors(self) -> list[Exception]:
        """
        Get list of execution errors.
        
        Returns:
            List of Exception objects from failed execute_logic_safe calls
        """
        with self._lock:
            return self._execution_errors.copy()
    
    def clear_execution_errors(self) -> None:
        """Clear execution error list."""
        with self._lock:
            self._execution_errors.clear()
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ThreadSafeComponent({self._component.component_id})"


class ComponentExecutionCoordinator:
    """
    Coordinates parallel component execution with error tracking.
    
    Manages:
    - Thread-safe component wrappers
    - Error collection from parallel execution
    - Execution statistics
    
    This extends the basic ComponentUpdateCoordinator with thread-safety
    and error handling specifically for parallel execution.
    
    Attributes:
        _components: Dict of component_id -> ThreadSafeComponent
        _lock: RLock for thread-safe access to coordinator state
        _execution_stats: Statistics about parallel execution
    """
    
    def __init__(self):
        """Initialize coordinator."""
        self._components: Dict[str, ThreadSafeComponent] = {}
        self._lock = threading.RLock()
        self._execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'errors': []
        }
    
    def register_component(self, component: Component) -> None:
        """
        Register a component for thread-safe execution.
        
        Args:
            component: Component to register
        """
        with self._lock:
            thread_safe = ThreadSafeComponent(component)
            self._components[component.component_id] = thread_safe
    
    def unregister_component(self, component_id: str) -> None:
        """
        Unregister a component.
        
        Args:
            component_id: Component ID to unregister
        """
        with self._lock:
            if component_id in self._components:
                del self._components[component_id]
    
    def get_thread_safe_component(self, component_id: str) -> Optional[ThreadSafeComponent]:
        """
        Get thread-safe wrapper for component.
        
        Args:
            component_id: Component ID
            
        Returns:
            ThreadSafeComponent or None if not found
        """
        with self._lock:
            return self._components.get(component_id)
    
    def execute_component_parallel(self, component_id: str) -> tuple[bool, Optional[Exception]]:
        """
        Execute component logic with thread-safety.
        
        Args:
            component_id: Component ID to execute
            
        Returns:
            Tuple of (success, exception)
        """
        with self._lock:
            ts_comp = self._components.get(component_id)
            if ts_comp is None:
                return (False, ValueError(f"Component {component_id} not registered"))
            
            self._execution_stats['total_executions'] += 1
        
        # Execute outside the coordinator lock (component has its own lock)
        success, exception = ts_comp.execute_logic_safe()
        
        with self._lock:
            if success:
                self._execution_stats['successful_executions'] += 1
            else:
                self._execution_stats['failed_executions'] += 1
                self._execution_stats['errors'].append({
                    'component_id': component_id,
                    'exception': exception
                })
        
        return (success, exception)
    
    def execute_batch_parallel(self, component_ids: list[str]) -> Dict[str, tuple[bool, Optional[Exception]]]:
        """
        Execute multiple components in parallel.
        
        This is called by the simulation engine's thread pool.
        Each component executes with its own lock.
        
        Args:
            component_ids: List of component IDs to execute
            
        Returns:
            Dict of component_id -> (success, exception)
        """
        results = {}
        
        for comp_id in component_ids:
            results[comp_id] = self.execute_component_parallel(comp_id)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Dict with total, successful, failed counts and errors
        """
        with self._lock:
            return {
                'total_executions': self._execution_stats['total_executions'],
                'successful_executions': self._execution_stats['successful_executions'],
                'failed_executions': self._execution_stats['failed_executions'],
                'error_count': len(self._execution_stats['errors']),
                'errors': self._execution_stats['errors'].copy()
            }
    
    def reset_statistics(self) -> None:
        """Reset execution statistics."""
        with self._lock:
            self._execution_stats = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'errors': []
            }
    
    def get_all_errors(self) -> list[Dict[str, Any]]:
        """
        Get all execution errors.
        
        Returns:
            List of error dicts with component_id and exception
        """
        with self._lock:
            return self._execution_stats['errors'].copy()
    
    def clear_errors(self) -> None:
        """Clear all execution errors."""
        with self._lock:
            self._execution_stats['errors'].clear()
    
    def has_errors(self) -> bool:
        """Check if any execution errors occurred."""
        with self._lock:
            return len(self._execution_stats['errors']) > 0
