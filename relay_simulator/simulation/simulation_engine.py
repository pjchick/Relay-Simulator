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
import os
from collections import defaultdict
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

        # Debug controls (off by default).
        # PowerShell:
        #   $env:RSIM_DEBUG_VNETS = "1"
        # Optional:
        #   $env:RSIM_DEBUG_VNETS_MODE = "all"   # or "dirty"
        #   $env:RSIM_DEBUG_VNETS_INCLUDE_TABS = "1"
        # CMD.exe:
        #   set RSIM_DEBUG_VNETS=1
        self._debug_vnets_enabled = self._read_env_bool("RSIM_DEBUG_VNETS")
        self._debug_vnets_mode = (os.getenv("RSIM_DEBUG_VNETS_MODE", "all") or "all").strip().lower()
        self._debug_vnets_include_tabs = self._read_env_bool("RSIM_DEBUG_VNETS_INCLUDE_TABS")

    @staticmethod
    def _read_env_bool(name: str, default: bool = False) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        value = str(value).strip().lower()
        return value in ("1", "true", "yes", "y", "on")

    def _debug_dump_vnets(self, *, iteration: int, phase: str, dirty_vnets: Optional[List[VNET]] = None) -> None:
        if not self._debug_vnets_enabled:
            return

        try:
            dirty_ids: Set[str] = set()
            if dirty_vnets is not None:
                dirty_ids = {v.vnet_id for v in dirty_vnets if v}
            else:
                # If caller didn't provide a snapshot, read current dirty set.
                try:
                    dirty_ids = set(self.dirty_manager.get_dirty_vnet_ids())
                except Exception:
                    dirty_ids = {v.vnet_id for v in self.vnets.values() if v and getattr(v, 'is_dirty', None) and v.is_dirty()}

            print("\n" + "=" * 80)
            print(f"[RSIM_DEBUG_VNETS] iter={iteration} phase={phase} dirty={len(dirty_ids)} total_vnets={len(self.vnets)}")

            # Stable ordering for diffing between runs
            vnets_sorted = sorted(self.vnets.values(), key=lambda v: v.vnet_id)

            if self._debug_vnets_mode == "dirty":
                vnets_sorted = [v for v in vnets_sorted if v and v.vnet_id in dirty_ids]

            for vnet in vnets_sorted:
                if not vnet:
                    continue

                page = vnet.page_id or "(none)"
                state = getattr(vnet, "state", None)
                links = sorted(list(getattr(vnet, "link_names", set()) or []))
                bridges = sorted(list(getattr(vnet, "bridge_ids", set()) or []))
                tabs = sorted(list(getattr(vnet, "tab_ids", set()) or []))

                dirty_mark = "*" if vnet.vnet_id in dirty_ids else " "
                print(
                    f"{dirty_mark} {vnet.vnet_id} page={page} state={state} tabs={len(tabs)} links={links} bridges={bridges}"
                )
                if self._debug_vnets_include_tabs and tabs:
                    for tab_id in tabs:
                        print(f"    tab={tab_id}")

            print("=" * 80 + "\n")
        except Exception as e:
            print(f"[RSIM_DEBUG_VNETS] dump failed: {e}")
    
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

            self._debug_dump_vnets(iteration=0, phase="after_initialize_mark_all_dirty")
            
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

        def evaluate_tabs_only(vnet: VNET) -> PinState:
            """Evaluate a VNET from tab/pin drives only.

            IMPORTANT: VNET.state is not a drive source. Only component pin states
            (via Tab.state -> Pin.state) can actively assert HIGH.
            """
            for tab_id in vnet.get_all_tabs():
                tab = self.tabs.get(tab_id)
                if tab and tab.state == PinState.HIGH:
                    return PinState.HIGH
            return PinState.FLOAT

        # Pre-index link_name -> {vnet_id} (links are static during a run)
        link_index: Dict[str, Set[str]] = defaultdict(set)
        for vnet_id, vnet in self.vnets.items():
            if not vnet:
                continue
            for link_name in getattr(vnet, 'link_names', set()) or set():
                if link_name:
                    link_index[link_name].add(vnet_id)

        def _union_find_groups() -> Dict[str, Set[str]]:
            """Build connected components across bridges + link names.

            Deterministic and order-independent. This replaces recursive link
            evaluation (which can become order-dependent in cyclic link graphs).
            """

            parent: Dict[str, str] = {}

            def find(x: str) -> str:
                # Path compression
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            def union(a: str, b: str) -> None:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[rb] = ra

            # Init parents
            for vnet_id in self.vnets.keys():
                parent[vnet_id] = vnet_id

            # Bridges (dynamic)
            for bridge in self.bridges.values():
                if not bridge:
                    continue
                v1 = getattr(bridge, 'vnet_id1', None)
                v2 = getattr(bridge, 'vnet_id2', None)
                if v1 in parent and v2 in parent:
                    union(v1, v2)

            # Links (static)
            for vnet_ids in link_index.values():
                vnet_ids_list = list(vnet_ids)
                if len(vnet_ids_list) < 2:
                    continue
                first = vnet_ids_list[0]
                for other in vnet_ids_list[1:]:
                    union(first, other)

            groups: Dict[str, Set[str]] = defaultdict(set)
            for vnet_id in self.vnets.keys():
                groups[find(vnet_id)].add(vnet_id)
            return groups
        
        try:
            while self._running and not self._stop_requested:
                iteration += 1
                
                # Update statistics
                with self._stats_lock:
                    self.statistics.iterations = iteration
                
                # Get dirty VNETs
                dirty_vnets = self.dirty_manager.get_dirty_vnets()

                self._debug_dump_vnets(iteration=iteration, phase="loop_start", dirty_vnets=dirty_vnets)
                
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
                    self._debug_dump_vnets(iteration=iteration, phase="stable_reached")
                    break

                # Deterministic recompute: build full connectivity groups (bridges + links),
                # compute group state from pin/tab drives only, then apply to all VNETs.
                # Only queue components when a VNET's state actually changes.
                groups = _union_find_groups()

                for group_ids in groups.values():
                    group_state = PinState.FLOAT
                    for vnet_id in group_ids:
                        gvnet = self.vnets.get(vnet_id)
                        if not gvnet:
                            continue
                        if evaluate_tabs_only(gvnet) == PinState.HIGH:
                            group_state = PinState.HIGH
                            break

                    for vnet_id in group_ids:
                        gvnet = self.vnets.get(vnet_id)
                        if not gvnet:
                            continue

                        old_state = gvnet.state
                        if old_state != group_state:
                            gvnet.state = group_state
                            self.coordinator.queue_components_for_vnet(gvnet)
                        # Consider this VNET evaluated for this iteration.
                        self.dirty_manager.clear_dirty(vnet_id)

                # If nothing changed electrically, we can still have pending component updates
                # from previous iteration; otherwise we are stable.
                self._debug_dump_vnets(iteration=iteration, phase="after_vnet_processing")
                
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
