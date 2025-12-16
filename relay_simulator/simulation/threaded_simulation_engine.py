"""
Threaded Simulation Engine

A multi-threaded variant of the SimulationEngine that uses a thread pool
to parallelize VNET evaluation and component logic execution.

This improves performance on multi-core systems by processing multiple
VNETs and components concurrently, while maintaining thread-safety through
proper locking strategies.

Author: Cascade AI
Date: 2025-12-10
"""

import time
import threading
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from core.vnet import VNET
from core.tab import Tab
from core.bridge import Bridge
from components.base import Component
from simulation.vnet_evaluator import VnetEvaluator
from simulation.state_propagator import StatePropagator
from simulation.dirty_flag_manager import DirtyFlagManager
from simulation.component_update_coordinator import ComponentUpdateCoordinator
from thread_pool_pkg.thread_pool import ThreadPoolManager, WorkItem
from components.thread_safe_component import ThreadSafeComponent, ComponentExecutionCoordinator


class SimulationState(Enum):
    """Simulation state enumeration."""
    STOPPED = "stopped"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STABLE = "stable"
    OSCILLATING = "oscillating"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class SimulationStatistics:
    """Statistics gathered during simulation."""
    iterations: int = 0
    components_updated: int = 0
    time_to_stability: float = 0.0
    total_time: float = 0.0
    max_iterations_reached: bool = False
    timeout_reached: bool = False
    stable: bool = False
    vnets_processed_parallel: int = 0
    components_processed_parallel: int = 0
    component_errors: int = 0
    successful_components: int = 0


class ThreadedSimulationEngine:
    """
    Multi-threaded simulation engine for relay logic simulator.
    
    Extends the single-threaded SimulationEngine with parallel processing:
    - Parallel VNET evaluation using thread pool
    - Parallel component logic execution
    - Thread-safe state management
    - Performance optimizations for multi-core systems
    
    All VNETs and components already have thread-safe locks (RLock),
    so we can safely process them in parallel.
    
    Attributes:
        state: Current simulation state
        vnets: Dictionary of all VNETs by ID
        tabs: Dictionary of all tabs by ID
        bridges: Dictionary of all bridges by ID
        components: Dictionary of all components by ID
        evaluator: VNET state evaluator
        propagator: State propagation system
        dirty_manager: Dirty flag manager
        coordinator: Component update coordinator
        thread_pool: Thread pool for parallel execution
        execution_coordinator: Thread-safe component execution coordinator
        statistics: Simulation statistics
    """
    
    def __init__(
        self,
        vnets: Dict[str, VNET],
        tabs: Dict[str, Tab],
        bridges: Dict[str, Bridge],
        components: Dict[str, Component],
        max_iterations: int = 10000,
        timeout_seconds: float = 30.0,
        thread_count: Optional[int] = None
    ):
        """
        Initialize the threaded simulation engine.
        
        Args:
            vnets: Dictionary of all VNETs by ID
            tabs: Dictionary of all tabs by ID
            bridges: Dictionary of all bridges by ID
            components: Dictionary of all components by ID
            max_iterations: Maximum iterations before oscillation detection
            timeout_seconds: Maximum time before timeout
            thread_count: Number of worker threads (None = auto-detect)
        """
        # Core data structures
        self.vnets = vnets
        self.tabs = tabs
        self.bridges = bridges
        self.components = components
        
        # Simulation parameters
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds
        
        # State management
        self.state = SimulationState.STOPPED
        self._state_lock = threading.RLock()
        
        # Phase 4 components
        self.evaluator = VnetEvaluator(vnets, tabs, bridges)
        self.propagator = StatePropagator(vnets, tabs, bridges)
        self.dirty_manager = DirtyFlagManager(vnets)
        self.coordinator = ComponentUpdateCoordinator(components, tabs)
        
        # Phase 5 - Thread pool
        self.thread_pool = ThreadPoolManager(thread_count=thread_count)
        
        # Phase 5.3 - Thread-safe component execution coordinator
        self.execution_coordinator = ComponentExecutionCoordinator()
        
        # Register all components for thread-safe execution
        for component in components.values():
            self.execution_coordinator.register_component(component)
        
        # Statistics
        self.statistics = SimulationStatistics()
        self._stats_lock = threading.RLock()
        
        # Control flags
        self._running = False
        self._stop_requested = False
    
    def initialize(self) -> bool:
        """
        Initialize the simulation.
        
        Steps:
        1. Set state to INITIALIZING
        2. Start thread pool
        3. Call sim_start() on all components
        4. Mark all VNETs dirty (force initial evaluation)
        5. Reset statistics
        
        Returns:
            True if initialization successful, False otherwise
        """
        with self._state_lock:
            if self.state != SimulationState.STOPPED:
                return False
            
            self.state = SimulationState.INITIALIZING
        
        try:
            # Start thread pool
            if not self.thread_pool.start():
                raise Exception("Failed to start thread pool")
            
            # Reset statistics
            with self._stats_lock:
                self.statistics = SimulationStatistics()
            
            # Call sim_start on all components
            for component in self.components.values():
                try:
                    component.sim_start()
                except Exception as e:
                    print(f"Error in sim_start for {component.component_id}: {e}")
            
            # Mark all VNETs dirty
            self.dirty_manager.mark_all_dirty()
            
            # Reset control flags
            self._running = False
            self._stop_requested = False
            
            with self._state_lock:
                self.state = SimulationState.STOPPED
            
            return True
            
        except Exception as e:
            print(f"Initialization error: {e}")
            with self._state_lock:
                self.state = SimulationState.ERROR
            return False
    
    def _evaluate_vnet_task(self, vnet: VNET) -> tuple:
        """
        Task to evaluate a single VNET.
        
        Args:
            vnet: VNET to evaluate
            
        Returns:
            Tuple of (vnet_id, old_state, new_state)
        """
        old_state = vnet.state
        new_state = self.evaluator.evaluate_vnet_state(vnet)
        return (vnet.vnet_id, old_state, new_state)
    
    def _propagate_vnet_task(self, vnet: VNET, new_state) -> Set[str]:
        """
        Task to propagate a VNET state change.
        
        Args:
            vnet: VNET to propagate
            new_state: New state to propagate
            
        Returns:
            Set of affected VNET IDs
        """
        return self.propagator.propagate_vnet_state(vnet, new_state)
    
    def _execute_component_task(self, component: Component) -> tuple[bool, Optional[Exception]]:
        """
        Task to execute component logic with thread-safety.
        
        Uses the ComponentExecutionCoordinator to execute component logic
        with proper locking and error handling.
        
        Args:
            component: Component to execute
            
        Returns:
            Tuple of (success, exception)
        """
        return self.execution_coordinator.execute_component_parallel(component.component_id)
    
    def run(self) -> SimulationStatistics:
        """
        Run the main simulation loop with parallel processing.
        
        Main loop:
        1. Get all dirty VNETs
        2. Evaluate VNETs in parallel using thread pool
        3. Propagate state changes in parallel
        4. Queue affected components
        5. Execute component logic in parallel
        6. Check for stability, oscillation, timeout
        
        Returns:
            SimulationStatistics object with results
        """
        with self._state_lock:
            if self.state not in (SimulationState.STOPPED, SimulationState.STABLE):
                return self.statistics
            
            self.state = SimulationState.RUNNING
            self._running = True
            self._stop_requested = False
        
        start_time = time.time()
        iteration = 0
        
        try:
            while self._running and not self._stop_requested:
                iteration += 1
                
                # Update statistics
                with self._stats_lock:
                    self.statistics.iterations = iteration
                
                # Get dirty VNETs
                dirty_vnets = self.dirty_manager.get_dirty_vnets()
                
                # If no dirty VNETs, we've reached stability
                if not dirty_vnets:
                    elapsed = time.time() - start_time
                    with self._stats_lock:
                        self.statistics.stable = True
                        self.statistics.time_to_stability = elapsed
                        self.statistics.total_time = elapsed
                    
                    with self._state_lock:
                        self.state = SimulationState.STABLE
                    
                    self._running = False
                    break
                
                # === PARALLEL VNET EVALUATION ===
                # Submit all VNET evaluations to thread pool
                eval_tasks = [
                    WorkItem(f'eval_{vnet.vnet_id}', self._evaluate_vnet_task, (vnet,))
                    for vnet in dirty_vnets
                ]
                
                self.thread_pool.submit_batch(eval_tasks)
                self.thread_pool.wait_for_completion(timeout=10.0)
                
                with self._stats_lock:
                    self.statistics.vnets_processed_parallel += len(dirty_vnets)
                
                # Collect results and propagate changes
                affected_vnets: Set[str] = set()
                vnets_to_propagate = []
                
                for vnet in dirty_vnets:
                    new_state = self.evaluator.evaluate_vnet_state(vnet)
                    
                    if new_state != vnet.state:
                        vnets_to_propagate.append((vnet, new_state))
                    
                    # Clear dirty flag
                    self.dirty_manager.clear_dirty(vnet.vnet_id)
                    
                    # Queue components
                    self.coordinator.queue_components_for_vnet(vnet)
                
                # === PARALLEL STATE PROPAGATION ===
                # Propagate state changes in parallel
                if vnets_to_propagate:
                    prop_tasks = [
                        WorkItem(f'prop_{vnet.vnet_id}', self._propagate_vnet_task, (vnet, new_state))
                        for vnet, new_state in vnets_to_propagate
                    ]
                    
                    self.thread_pool.submit_batch(prop_tasks)
                    self.thread_pool.wait_for_completion(timeout=10.0)
                    
                    # Collect affected VNETs
                    for vnet, new_state in vnets_to_propagate:
                        propagated = self.propagator.propagate_vnet_state(vnet, new_state)
                        affected_vnets.update(propagated)
                
                # NOTE: We no longer re-mark all propagated VNETs dirty here.
                # Propagation applies the resolved state; forcing re-evaluation can create oscillation
                # when certain connectivity (e.g., bridges) is resolved outside the evaluator.
                
                # === PARALLEL COMPONENT EXECUTION ===
                # Start component updates
                num_pending = self.coordinator.start_updates()
                
                if num_pending > 0:
                    pending_components = self.coordinator.get_pending_components()
                    
                    # Submit component logic to thread pool
                    comp_tasks = [
                        WorkItem(f'comp_{comp.component_id}', self._execute_component_task, (comp,))
                        for comp in pending_components
                    ]
                    
                    self.thread_pool.submit_batch(comp_tasks)
                    self.thread_pool.wait_for_completion(timeout=10.0)
                    
                    # Collect execution results and update statistics
                    exec_stats = self.execution_coordinator.get_statistics()
                    
                    with self._stats_lock:
                        self.statistics.components_updated += num_pending
                        self.statistics.components_processed_parallel += num_pending
                        self.statistics.component_errors = exec_stats['failed_executions']
                        self.statistics.successful_components = exec_stats['successful_executions']
                    
                    # Log any errors
                    if exec_stats['error_count'] > 0:
                        for error_info in exec_stats['errors']:
                            comp_id = error_info['component_id']
                            exc = error_info['exception']
                            print(f"Component {comp_id} error: {exc}")
                    
                    # Mark all components complete
                    for comp in pending_components:
                        self.coordinator.mark_update_complete(comp.component_id)
                    
                    # No global post-component VNET scan here.
                    # Components must mark affected VNETs dirty via VnetManager, and bridge changes
                    # already mark VNETs dirty.
                
                # Check for oscillation
                if iteration >= self.max_iterations:
                    elapsed = time.time() - start_time
                    with self._stats_lock:
                        self.statistics.max_iterations_reached = True
                        self.statistics.total_time = elapsed
                    
                    with self._state_lock:
                        self.state = SimulationState.OSCILLATING
                    
                    self._running = False
                    break
                
                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed >= self.timeout_seconds:
                    with self._stats_lock:
                        self.statistics.timeout_reached = True
                        self.statistics.total_time = elapsed
                    
                    with self._state_lock:
                        self.state = SimulationState.TIMEOUT
                    
                    self._running = False
                    break
            
            # If stopped by request
            if self._stop_requested:
                elapsed = time.time() - start_time
                with self._stats_lock:
                    self.statistics.total_time = elapsed
                
                with self._state_lock:
                    self.state = SimulationState.STOPPED
            
            return self.statistics
            
        except Exception as e:
            print(f"Simulation error: {e}")
            elapsed = time.time() - start_time
            with self._stats_lock:
                self.statistics.total_time = elapsed
            
            with self._state_lock:
                self.state = SimulationState.ERROR
            
            self._running = False
            return self.statistics
    
    def stop(self):
        """Request simulation to stop."""
        self._stop_requested = True
    
    def shutdown(self) -> bool:
        """
        Shutdown the simulation and cleanup.
        
        Steps:
        1. Stop the simulation if running
        2. Call sim_stop() on all components
        3. Clear dirty flags
        4. Cancel pending component updates
        5. Shutdown thread pool
        
        Returns:
            True if shutdown successful, False otherwise
        """
        # Stop if running
        if self._running:
            self.stop()
            timeout = 2.0
            start = time.time()
            while self._running and (time.time() - start) < timeout:
                time.sleep(0.01)
        
        try:
            # Call sim_stop on all components
            for component in self.components.values():
                try:
                    component.sim_stop()
                except Exception as e:
                    print(f"Error in sim_stop for {component.component_id}: {e}")
            
            # Clear dirty flags
            self.dirty_manager.reset()
            
            # Cancel pending updates
            self.coordinator.cancel_all_updates()
            
            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True, timeout=2.0)
            
            with self._state_lock:
                self.state = SimulationState.STOPPED
            
            return True
            
        except Exception as e:
            print(f"Shutdown error: {e}")
            with self._state_lock:
                self.state = SimulationState.ERROR
            return False
    
    def get_state(self) -> SimulationState:
        """Get current simulation state (thread-safe)."""
        with self._state_lock:
            return self.state
    
    def get_statistics(self) -> SimulationStatistics:
        """Get current simulation statistics (thread-safe)."""
        with self._stats_lock:
            return SimulationStatistics(
                iterations=self.statistics.iterations,
                components_updated=self.statistics.components_updated,
                time_to_stability=self.statistics.time_to_stability,
                total_time=self.statistics.total_time,
                max_iterations_reached=self.statistics.max_iterations_reached,
                timeout_reached=self.statistics.timeout_reached,
                stable=self.statistics.stable,
                vnets_processed_parallel=self.statistics.vnets_processed_parallel,
                components_processed_parallel=self.statistics.components_processed_parallel,
                component_errors=self.statistics.component_errors,
                successful_components=self.statistics.successful_components
            )
    
    def is_running(self) -> bool:
        """Check if simulation is currently running."""
        return self._running
    
    def is_stable(self) -> bool:
        """Check if simulation has reached stable state."""
        with self._state_lock:
            return self.state == SimulationState.STABLE
    
    def reset_statistics(self):
        """Reset simulation statistics to initial state."""
        with self._stats_lock:
            self.statistics = SimulationStatistics()
        
        # Also reset execution coordinator statistics
        self.execution_coordinator.reset_statistics()
    
    def get_thread_pool_stats(self) -> dict:
        """Get thread pool statistics."""
        return self.thread_pool.get_statistics()
    
    def get_execution_coordinator_stats(self) -> dict:
        """
        Get component execution coordinator statistics.
        
        Returns execution statistics including successful/failed counts
        and any errors that occurred during parallel component execution.
        """
        return self.execution_coordinator.get_statistics()
        return self.thread_pool.get_statistics()
