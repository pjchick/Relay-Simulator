"""
Simulation Engine - Main Simulation Loop

The SimulationEngine is the core orchestrator of the relay logic simulation.
It integrates all Phase 4 components (VnetEvaluator, StatePropagator, 
DirtyFlagManager, ComponentUpdateCoordinator) into a cohesive simulation loop.

The engine:
1. Initializes all components and VNETs
2. Runs the main simulation loop until stable
3. Detects oscillations and timeouts
4. Tracks statistics
5. Manages component lifecycle (SimStart/SimStop)

Author: Cascade AI
Date: 2025-12-10
"""

import time
import threading
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from core.vnet import VNET
from core.state import PinState
from core.tab import Tab
from core.bridge import Bridge
from components.base import Component
from simulation.vnet_evaluator import VnetEvaluator
from simulation.state_propagator import StatePropagator
from simulation.dirty_flag_manager import DirtyFlagManager
from simulation.component_update_coordinator import ComponentUpdateCoordinator
from simulation.vnet_manager import VnetManager
from simulation.bridge_manager import BridgeManager


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


class SimulationEngine:
    """
    Main simulation engine for relay logic simulator.
    
    Orchestrates the complete simulation lifecycle:
    - Initialization: Call SimStart on all components, mark all VNETs dirty
    - Main Loop: Evaluate dirty VNETs, propagate states, update components
    - Stability Detection: Detect when simulation reaches stable state
    - Oscillation Detection: Detect infinite loops via max iterations or timeout
    - Shutdown: Call SimStop on all components, cleanup
    
    Thread-safe: Uses locks for state changes and statistics updates.
    
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
        statistics: Simulation statistics
    """
    
    def __init__(
        self,
        vnets: Dict[str, VNET],
        tabs: Dict[str, Tab],
        bridges: Dict[str, Bridge],
        components: Dict[str, Component],
        max_iterations: int = 10000,
        timeout_seconds: float = 30.0
    ):
        """
        Initialize the simulation engine.
        
        Args:
            vnets: Dictionary of all VNETs by ID
            tabs: Dictionary of all tabs by ID
            bridges: Dictionary of all bridges by ID
            components: Dictionary of all components by ID
            max_iterations: Maximum iterations before oscillation detection
            timeout_seconds: Maximum time before timeout
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
        
        # Create managers for component interface
        from core.id_manager import IDManager
        self.id_manager = IDManager()  # For generating bridge IDs
        self.vnet_manager = VnetManager(vnets, tabs, self.dirty_manager)
        self.bridge_manager = BridgeManager(bridges, self.id_manager, vnets)
        
        # Statistics
        self.statistics = SimulationStatistics()
        self._stats_lock = threading.RLock()
        
        # Control flags
        self._running = False
        self._stop_requested = False
        
        # GUI callback for async updates (e.g., relay timer completion)
        self._gui_restart_callback = None
    
    def initialize(self) -> bool:
        """
        Initialize the simulation.
        
        Steps:
        1. Set state to INITIALIZING
        2. Call sim_start() on all components
        3. Mark all VNETs dirty (force initial evaluation)
        4. Reset statistics
        
        Returns:
            True if initialization successful, False otherwise
        """
        with self._state_lock:
            if self.state != SimulationState.STOPPED:
                return False
            
            self.state = SimulationState.INITIALIZING
        
        try:
            # Reset statistics
            with self._stats_lock:
                self.statistics = SimulationStatistics()
            
            # Call sim_start on all components
            for component in self.components.values():
                try:
                    component.sim_start(self.vnet_manager, self.bridge_manager)
                    
                    # Set callback for DPDT relays to trigger simulation restart when timer completes
                    if hasattr(component, 'set_on_contacts_switched_callback'):
                        component.set_on_contacts_switched_callback(self._on_relay_contacts_switched)
                except Exception as e:
                    print(f"Error in sim_start for {component.component_id}: {e}")
                    # Continue with other components
            
            # Mark all VNETs dirty to force initial evaluation
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
    
    def _on_relay_contacts_switched(self):
        """
        Callback for when a relay switches its contacts.
        
        Marks all VNETs dirty and requests the GUI to restart simulation.
        This is called from the relay's timer thread.
        """
        self.dirty_manager.mark_all_dirty()
        
        # Trigger GUI to restart simulation
        if self._gui_restart_callback:
            self._gui_restart_callback()
        else:
            pass
    
    def set_gui_restart_callback(self, callback):
        """
        Set callback to trigger GUI simulation restart.
        
        This is called by relays when their timers complete and contacts switch.
        
        Args:
            callback: Function to call to restart simulation (no arguments)
        """
        self._gui_restart_callback = callback
    
    def run(self) -> SimulationStatistics:
        """
        Run the main simulation loop until stable or max iterations/timeout.
        
        Main loop:
        1. Get all dirty VNETs
        2. For each dirty VNET:
           a. Evaluate new state
           b. If state changed, propagate to connected VNETs
           c. Queue affected components for update
        3. Execute component updates (simulate_logic)
        4. Check if stable (no dirty VNETs)
        5. Check for oscillation (max iterations or timeout)
        6. Repeat until stable or oscillation detected
        
        Returns:
            SimulationStatistics object with results
        """
        with self._state_lock:
            if self.state not in (SimulationState.STOPPED, SimulationState.STABLE):
                return self.statistics
            
            self.state = SimulationState.RUNNING
            self._running = True
            self._stop_requested = False
        
        # (debug logging removed)
        
        start_time = time.time()
        iteration = 0

        def collect_bridge_group(start_vnet: VNET) -> Set[str]:
            """Return all VNET IDs connected to start_vnet via active bridges."""
            group: Set[str] = set()
            stack = [start_vnet.vnet_id]
            while stack:
                current_id = stack.pop()
                if current_id in group:
                    continue
                group.add(current_id)

                current_vnet = self.vnets.get(current_id)
                if not current_vnet:
                    continue

                for bridge_id in current_vnet.bridge_ids.copy():
                    bridge = self.bridges.get(bridge_id)
                    if not bridge:
                        continue
                    other_id = bridge.get_other_vnet(current_id)
                    if other_id and other_id not in group:
                        stack.append(other_id)

            return group
        
        try:
            while self._running and not self._stop_requested:
                iteration += 1
                
                # Update statistics
                with self._stats_lock:
                    self.statistics.iterations = iteration
                
                # Get dirty VNETs
                dirty_vnets = self.dirty_manager.get_dirty_vnets()
                
                # (debug logging removed)
                
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
                
                # Process dirty VNETs in bridge-connected groups.
                # This avoids oscillation when the evaluator intentionally ignores bridges.
                processed: Set[str] = set()
                for vnet in dirty_vnets:
                    if vnet.vnet_id in processed:
                        continue

                    group_ids = collect_bridge_group(vnet)
                    processed.update(group_ids)

                    # Evaluate base (tabs+links) for each VNET in the group, then OR to get group state.
                    group_state = PinState.FLOAT
                    for vnet_id in group_ids:
                        gvnet = self.vnets.get(vnet_id)
                        if not gvnet:
                            continue
                        base_state = self.evaluator.evaluate_vnet_state(gvnet)
                        if base_state == PinState.HIGH:
                            group_state = PinState.HIGH
                            break

                    # Apply group_state to all VNETs in the group.
                    # Propagate across LINKS only (bridges are already handled by grouping).
                    for vnet_id in group_ids:
                        gvnet = self.vnets.get(vnet_id)
                        if not gvnet:
                            continue

                        old_state = gvnet.state
                        if old_state != group_state:
                            # Let the propagator update gvnet.state; it also propagates across LINKS.
                            # If we set gvnet.state first, the propagator would early-return and skip propagation.
                            propagated = self.propagator.propagate_vnet_state(gvnet, group_state, include_bridges=False)
                            # Clear dirty for anything propagation touched so we don't re-evaluate it back to base.
                            for affected_id in propagated:
                                self.dirty_manager.clear_dirty(affected_id)
                                affected_vnet = self.vnets.get(affected_id)
                                if affected_vnet:
                                    self.coordinator.queue_components_for_vnet(affected_vnet)

                        # Clear dirty and queue components for the group VNET regardless.
                        self.dirty_manager.clear_dirty(vnet_id)
                        self.coordinator.queue_components_for_vnet(gvnet)
                
                # Start component updates
                num_pending = self.coordinator.start_updates()
                
                # Execute component logic
                if num_pending > 0:
                    pending_components = self.coordinator.get_pending_components()
                    
                    for component in pending_components:
                        try:
                            component.simulate_logic(self.vnet_manager, self.bridge_manager)
                            with self._stats_lock:
                                self.statistics.components_updated += 1
                        except Exception as e:
                            print(f"Error in simulate_logic for {component.component_id}: {e}")
                            import traceback
                            traceback.print_exc()
                        finally:
                            self.coordinator.mark_update_complete(component.component_id)
                    
                    # Wait for all updates to complete
                    self.coordinator.wait_for_completion(timeout=1.0)
                    # No global post-component VNET scan here.
                    # Components are responsible for marking affected VNETs dirty via VnetManager,
                    # and bridge changes (add/remove) already mark VNETs dirty.
                
                # Check for oscillation (max iterations)
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
        """
        Request simulation to stop.
        
        Sets the stop flag, which will cause the simulation loop to exit
        after the current iteration completes.
        """
        self._stop_requested = True
    
    def shutdown(self) -> bool:
        """
        Shutdown the simulation and cleanup.
        
        Steps:
        1. Stop the simulation if running
        2. Call sim_stop() on all components
        3. Clear dirty flags
        4. Cancel any pending component updates
        
        Returns:
            True if shutdown successful, False otherwise
        """
        # Stop if running
        if self._running:
            self.stop()
            # Wait a bit for loop to exit
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
            
            with self._state_lock:
                self.state = SimulationState.STOPPED
            
            return True
            
        except Exception as e:
            print(f"Shutdown error: {e}")
            with self._state_lock:
                self.state = SimulationState.ERROR
            return False
    
    def get_state(self) -> SimulationState:
        """
        Get current simulation state (thread-safe).
        
        Returns:
            Current SimulationState
        """
        with self._state_lock:
            return self.state
    
    def get_statistics(self) -> SimulationStatistics:
        """
        Get current simulation statistics (thread-safe).
        
        Returns:
            Copy of current SimulationStatistics
        """
        with self._stats_lock:
            # Return a copy
            return SimulationStatistics(
                iterations=self.statistics.iterations,
                components_updated=self.statistics.components_updated,
                time_to_stability=self.statistics.time_to_stability,
                total_time=self.statistics.total_time,
                max_iterations_reached=self.statistics.max_iterations_reached,
                timeout_reached=self.statistics.timeout_reached,
                stable=self.statistics.stable
            )
    
    def is_running(self) -> bool:
        """
        Check if simulation is currently running.
        
        Returns:
            True if running, False otherwise
        """
        return self._running
    
    def is_stable(self) -> bool:
        """
        Check if simulation has reached stable state.
        
        Returns:
            True if stable, False otherwise
        """
        with self._state_lock:
            return self.state == SimulationState.STABLE
    
    def reset_statistics(self):
        """Reset simulation statistics to initial state."""
        with self._stats_lock:
            self.statistics = SimulationStatistics()
