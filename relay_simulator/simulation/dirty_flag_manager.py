"""
Dirty Flag Manager for Relay Logic Simulator

This module implements the dirty flag management system that tracks which VNETs
need re-evaluation during simulation. The dirty flag optimization is a key
performance feature that prevents unnecessary computation.

The manager:
1. Tracks all VNETs in the simulation
2. Marks VNETs as dirty when their state may have changed
3. Clears dirty flags after evaluation
4. Provides queries for dirty VNETs (stability detection)
5. Ensures thread-safe dirty flag operations

A VNET becomes dirty when:
- A component changes a pin state connected to that VNET
- A linked or bridged VNET changes state
- The simulation first starts (all VNETs dirty initially)

The simulation reaches stability when no VNETs are dirty.
"""

from typing import Dict, Set, List, Optional
from threading import RLock
from core.vnet import VNET
from core.state import PinState


class DirtyFlagManager:
    """
    Manages dirty flags for all VNETs in the simulation.
    
    The dirty flag optimization prevents unnecessary work by tracking which
    VNETs need re-evaluation. Only dirty VNETs are processed in each
    simulation iteration.
    
    Thread-safe: All operations use locking to ensure correct behavior
    in multi-threaded simulation scenarios.
    
    Attributes:
        _vnets: Dictionary mapping vnet_id -> VNET object
        _lock: Reentrant lock for thread-safety
    """
    
    def __init__(self, vnets: Dict[str, VNET]):
        """
        Initialize the dirty flag manager.
        
        Args:
            vnets: Dictionary mapping vnet_id -> VNET object
        """
        self._vnets = vnets
        self._lock = RLock()  # Reentrant lock for nested calls
    
    def mark_dirty(self, vnet_id: str) -> bool:
        """
        Mark a VNET as dirty (needs re-evaluation).
        
        Thread-safe operation.
        
        Args:
            vnet_id: ID of VNET to mark dirty
            
        Returns:
            True if VNET was marked dirty, False if not found
        """
        with self._lock:
            vnet = self._vnets.get(vnet_id)
            if vnet:
                vnet.mark_dirty()
                return True
            return False
    
    def mark_multiple_dirty(self, vnet_ids: Set[str]) -> int:
        """
        Mark multiple VNETs as dirty in a single operation.
        
        Thread-safe operation.
        
        Args:
            vnet_ids: Set of VNET IDs to mark dirty
            
        Returns:
            Number of VNETs successfully marked dirty
        """
        with self._lock:
            count = 0
            for vnet_id in vnet_ids:
                if self.mark_dirty(vnet_id):
                    count += 1
            return count
    
    def clear_dirty(self, vnet_id: str) -> bool:
        """
        Clear a VNET's dirty flag (after evaluation).
        
        Thread-safe operation.
        
        Args:
            vnet_id: ID of VNET to clear
            
        Returns:
            True if VNET was cleared, False if not found
        """
        with self._lock:
            vnet = self._vnets.get(vnet_id)
            if vnet:
                vnet.clear_dirty()
                return True
            return False
    
    def clear_multiple_dirty(self, vnet_ids: Set[str]) -> int:
        """
        Clear dirty flags for multiple VNETs.
        
        Thread-safe operation.
        
        Args:
            vnet_ids: Set of VNET IDs to clear
            
        Returns:
            Number of VNETs successfully cleared
        """
        with self._lock:
            count = 0
            for vnet_id in vnet_ids:
                if self.clear_dirty(vnet_id):
                    count += 1
            return count
    
    def clear_all_dirty(self) -> int:
        """
        Clear dirty flags for all VNETs.
        
        Thread-safe operation.
        
        Returns:
            Number of VNETs cleared
        """
        with self._lock:
            count = 0
            for vnet in self._vnets.values():
                vnet.clear_dirty()
                count += 1
            return count
    
    def is_dirty(self, vnet_id: str) -> bool:
        """
        Check if a VNET is dirty.
        
        Thread-safe operation.
        
        Args:
            vnet_id: ID of VNET to check
            
        Returns:
            True if VNET is dirty, False otherwise (or if not found)
        """
        with self._lock:
            vnet = self._vnets.get(vnet_id)
            if vnet:
                return vnet.is_dirty()
            return False
    
    def get_dirty_vnets(self) -> List[VNET]:
        """
        Get all VNETs that are currently dirty.
        
        Thread-safe operation.
        
        Returns:
            List of dirty VNET objects
        """
        with self._lock:
            dirty_vnets = []
            for vnet in self._vnets.values():
                if vnet.is_dirty():
                    dirty_vnets.append(vnet)
            return dirty_vnets
    
    def get_dirty_vnet_ids(self) -> Set[str]:
        """
        Get IDs of all VNETs that are currently dirty.
        
        Thread-safe operation.
        
        Returns:
            Set of dirty VNET IDs
        """
        with self._lock:
            dirty_ids = set()
            for vnet_id, vnet in self._vnets.items():
                if vnet.is_dirty():
                    dirty_ids.add(vnet_id)
            return dirty_ids
    
    def has_dirty_vnets(self) -> bool:
        """
        Check if any VNETs are dirty (stability check).
        
        Thread-safe operation.
        
        Returns:
            True if at least one VNET is dirty, False if all clean (stable)
        """
        with self._lock:
            for vnet in self._vnets.values():
                if vnet.is_dirty():
                    return True
            return False
    
    def is_stable(self) -> bool:
        """
        Check if simulation is stable (no dirty VNETs).
        
        Thread-safe operation.
        
        Returns:
            True if stable (no dirty VNETs), False otherwise
        """
        return not self.has_dirty_vnets()
    
    def get_dirty_count(self) -> int:
        """
        Get count of dirty VNETs.
        
        Thread-safe operation.
        
        Returns:
            Number of dirty VNETs
        """
        with self._lock:
            count = 0
            for vnet in self._vnets.values():
                if vnet.is_dirty():
                    count += 1
            return count
    
    def mark_all_dirty(self) -> int:
        """
        Mark all VNETs as dirty.
        
        This is typically called at simulation start to force initial evaluation.
        
        Thread-safe operation.
        
        Returns:
            Number of VNETs marked dirty
        """
        with self._lock:
            count = 0
            for vnet in self._vnets.values():
                vnet.mark_dirty()
                count += 1
            return count
    
    def detect_state_change_and_mark_dirty(
        self,
        vnet_id: str,
        new_state: PinState
    ) -> bool:
        """
        Compare current VNET state with new state and mark dirty if different.
        
        This is the core dirty detection logic used by components when they
        want to change a pin state.
        
        Thread-safe operation.
        
        Args:
            vnet_id: ID of VNET to check
            new_state: New state to compare against
            
        Returns:
            True if state changed and VNET marked dirty, False otherwise
        """
        with self._lock:
            vnet = self._vnets.get(vnet_id)
            if not vnet:
                return False
            
            # Compare states
            if vnet.state != new_state:
                vnet.mark_dirty()
                return True
            
            return False
    
    def batch_detect_and_mark(
        self,
        vnet_states: Dict[str, PinState]
    ) -> Set[str]:
        """
        Batch version of detect_state_change_and_mark_dirty.
        
        Check multiple VNETs for state changes and mark dirty as needed.
        
        Thread-safe operation.
        
        Args:
            vnet_states: Dictionary mapping vnet_id -> desired new state
            
        Returns:
            Set of VNET IDs that were marked dirty (state changed)
        """
        with self._lock:
            marked_dirty = set()
            
            for vnet_id, new_state in vnet_states.items():
                if self.detect_state_change_and_mark_dirty(vnet_id, new_state):
                    marked_dirty.add(vnet_id)
            
            return marked_dirty
    
    def get_statistics(self) -> dict:
        """
        Get statistics about dirty flags.
        
        Useful for monitoring and debugging.
        
        Thread-safe operation.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            total = len(self._vnets)
            dirty = self.get_dirty_count()
            clean = total - dirty
            
            return {
                'total_vnets': total,
                'dirty_vnets': dirty,
                'clean_vnets': clean,
                'dirty_percentage': (dirty / total * 100) if total > 0 else 0,
                'is_stable': self.is_stable()
            }
    
    def reset(self):
        """
        Clear all dirty flags and reset state.
        
        Typically used when stopping simulation or resetting.
        
        Thread-safe operation.
        """
        with self._lock:
            for vnet in self._vnets.values():
                vnet.clear_dirty()
