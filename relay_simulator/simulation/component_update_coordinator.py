"""
Component Update Coordinator

Manages the queuing and execution of component logic updates during simulation.
Coordinates component updates, tracks pending operations, and provides completion
synchronization with timeout handling.

Author: Cascade AI
Date: 2025-12-10
"""

import threading
from typing import Dict, Set, List, Optional
from threading import Event, RLock
from components.base import Component
from core.vnet import VNET
from core.tab import Tab


class ComponentUpdateCoordinator:
    """
    Coordinates component logic updates during simulation.
    
    Manages a queue of components that need to execute their ComponentLogic(),
    tracks which updates are pending, and provides synchronization to wait
    for all updates to complete. Prevents duplicate queueing and supports
    timeout handling.
    
    Thread-safe: Uses RLock for all operations involving shared state.
    
    Attributes:
        _components: Dictionary of all components by ID
        _tabs: Dictionary of all tabs by ID (needed to resolve VNET connections)
        _lock: Reentrant lock for thread-safety
        _pending_updates: Set of component IDs with pending updates
        _completion_event: Event signaled when all updates complete
        _queued_components: Set of component IDs currently queued
    """
    
    def __init__(self, components: Dict[str, Component], tabs: Dict[str, Tab]):
        """
        Initialize the component update coordinator.
        
        Args:
            components: Dictionary mapping component IDs to Component instances
            tabs: Dictionary mapping tab IDs to Tab instances
        """
        self._components = components
        self._tabs = tabs
        self._lock = RLock()
        self._pending_updates: Set[str] = set()
        self._completion_event = Event()
        self._queued_components: Set[str] = set()
        
        # Initially, nothing is pending, so we're in "completed" state
        self._completion_event.set()
    
    def queue_component_update(self, component_id: str) -> bool:
        """
        Queue a component for logic update.
        
        If the component is already queued or pending, this is a no-op.
        This prevents duplicate executions of the same component's logic.
        
        Args:
            component_id: ID of the component to update
            
        Returns:
            True if component was queued, False if already queued or invalid ID
        """
        with self._lock:
            # Validate component exists
            if component_id not in self._components:
                return False
            
            # Check if already queued or pending
            if component_id in self._queued_components or component_id in self._pending_updates:
                return False
            
            # Mark as queued
            self._queued_components.add(component_id)
            
            # Clear completion event since we now have work to do
            self._completion_event.clear()
            
            return True
    
    def queue_multiple_updates(self, component_ids: Set[str]) -> int:
        """
        Queue multiple components for logic updates.
        
        Batch operation for efficiency. Avoids duplicates.
        
        Args:
            component_ids: Set of component IDs to queue
            
        Returns:
            Number of components successfully queued
        """
        count = 0
        for component_id in component_ids:
            if self.queue_component_update(component_id):
                count += 1
        return count
    
    def queue_components_for_vnet(self, vnet: VNET) -> int:
        """
        Queue all components connected to a VNET for updates.
        
        Finds all components that have tabs in the given VNET and queues
        them for logic updates. This is typically called after a VNET's
        state changes.
        
        Args:
            vnet: The VNET whose connected components should be queued
            
        Returns:
            Number of components successfully queued
        """
        with self._lock:
            # Find all unique components connected to this VNET
            connected_component_ids = set()
            
            # Get all tab IDs from the VNET
            for tab_id in vnet.get_all_tabs():
                tab = self._tabs.get(tab_id)
                if tab and tab.parent_pin and tab.parent_pin.parent_component:
                    component_id = tab.parent_pin.parent_component.component_id
                    connected_component_ids.add(component_id)
            
            # Queue all connected components
            return self.queue_multiple_updates(connected_component_ids)
    
    def queue_components_for_vnets(self, vnets: List[VNET]) -> int:
        """
        Queue all components connected to multiple VNETs.
        
        Batch operation for efficiency. Automatically deduplicates components.
        
        Args:
            vnets: List of VNETs whose connected components should be queued
            
        Returns:
            Number of components successfully queued
        """
        with self._lock:
            all_component_ids = set()
            
            for vnet in vnets:
                for tab_id in vnet.get_all_tabs():
                    tab = self._tabs.get(tab_id)
                    if tab and tab.parent_pin and tab.parent_pin.parent_component:
                        component_id = tab.parent_pin.parent_component.component_id
                        all_component_ids.add(component_id)
            
            return self.queue_multiple_updates(all_component_ids)
    
    def start_updates(self) -> int:
        """
        Move all queued components to pending state and return them for execution.
        
        This transfers components from the queued set to the pending set,
        preparing them for execution. The caller is responsible for actually
        executing the component logic.
        
        Returns:
            Number of components moved to pending state
        """
        with self._lock:
            # Move queued to pending
            self._pending_updates.update(self._queued_components)
            count = len(self._queued_components)
            self._queued_components.clear()
            
            return count
    
    def get_pending_components(self) -> List[Component]:
        """
        Get all components that have pending updates.
        
        Returns a copy of the pending components list for safe iteration.
        
        Returns:
            List of Component instances with pending updates
        """
        with self._lock:
            pending_components = []
            for component_id in self._pending_updates:
                if component_id in self._components:
                    pending_components.append(self._components[component_id])
            return pending_components
    
    def mark_update_complete(self, component_id: str) -> bool:
        """
        Mark a component's update as complete.
        
        Removes the component from the pending set. If this was the last
        pending update and there are no queued updates, signals the
        completion event.
        
        Args:
            component_id: ID of the component that completed
            
        Returns:
            True if component was pending, False otherwise
        """
        with self._lock:
            if component_id not in self._pending_updates:
                return False
            
            self._pending_updates.remove(component_id)
            
            # If no more pending and no more queued, signal completion
            if not self._pending_updates and not self._queued_components:
                self._completion_event.set()
            
            return True
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all pending component updates to complete.
        
        Blocks until all components have finished their logic updates,
        or until the timeout expires.
        
        Args:
            timeout: Maximum time to wait in seconds. None = wait forever.
            
        Returns:
            True if all updates completed, False if timeout occurred
        """
        return self._completion_event.wait(timeout)
    
    def get_pending_count(self) -> int:
        """
        Get the number of components with pending updates.
        
        Returns:
            Count of pending component updates
        """
        with self._lock:
            return len(self._pending_updates)
    
    def get_queued_count(self) -> int:
        """
        Get the number of components queued for updates.
        
        Returns:
            Count of queued components
        """
        with self._lock:
            return len(self._queued_components)
    
    def has_pending_work(self) -> bool:
        """
        Check if there are any pending or queued updates.
        
        Returns:
            True if updates are pending or queued, False if all complete
        """
        with self._lock:
            return bool(self._pending_updates or self._queued_components)
    
    def is_complete(self) -> bool:
        """
        Check if all updates are complete.
        
        Returns:
            True if no pending or queued work, False otherwise
        """
        return not self.has_pending_work()
    
    def cancel_all_updates(self):
        """
        Cancel all pending and queued updates.
        
        Clears both the pending and queued sets, and signals completion.
        This is typically used during simulation shutdown or reset.
        """
        with self._lock:
            self._pending_updates.clear()
            self._queued_components.clear()
            self._completion_event.set()
    
    def get_statistics(self) -> dict:
        """
        Get statistics about the coordinator's current state.
        
        Returns:
            Dictionary containing:
                - total_components: Total number of components
                - queued: Number of components queued
                - pending: Number of components with pending updates
                - complete: Whether all updates are complete
        """
        with self._lock:
            return {
                'total_components': len(self._components),
                'queued': len(self._queued_components),
                'pending': len(self._pending_updates),
                'complete': self.is_complete()
            }
    
    def reset(self):
        """
        Reset the coordinator to initial state.
        
        Clears all queued and pending updates, resets the completion event.
        """
        with self._lock:
            self._pending_updates.clear()
            self._queued_components.clear()
            self._completion_event.set()
