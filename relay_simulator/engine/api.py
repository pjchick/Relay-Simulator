"""
Public API for the simulation engine.
Thread-safe interface for designer and other local clients.
"""

from typing import Callable, Dict, Any, List, Optional
from threading import Lock


class SimulationEngine:
    """
    Public API for simulation engine.
    Provides thread-safe interface for controlling simulation and querying state.
    """
    
    def __init__(self):
        """Initialize the simulation engine"""
        self.document = None  # Will be Document instance
        self.sim_engine = None  # Will be SimEngine instance
        self.vnet_manager = None  # Will be VnetManager instance
        self._stable_callbacks: List[Callable] = []
        self._lock = Lock()
        self._running = False
    
    # === FILE OPERATIONS ===
    
    def load_file(self, filepath: str) -> Dict[str, Any]:
        """
        Load .rsim file.
        
        Args:
            filepath: Path to .rsim file
            
        Returns:
            {
                'success': bool,
                'message': str,
                'document_info': {...}
            }
        """
        # TODO: Implement file loading
        return {
            'success': False,
            'message': 'Not yet implemented',
            'document_info': {}
        }
    
    def save_file(self, filepath: str) -> Dict[str, Any]:
        """
        Save current document to .rsim file.
        
        Args:
            filepath: Path to save file
            
        Returns:
            {'success': bool, 'message': str}
        """
        # TODO: Implement file saving
        return {
            'success': False,
            'message': 'Not yet implemented'
        }
    
    # === SIMULATION CONTROL ===
    
    def start_simulation(self) -> Dict[str, Any]:
        """
        Start simulation.
        - Builds VNETs
        - Calls SimStart on components
        - Starts main loop
        
        Returns:
            {'success': bool, 'message': str}
        """
        # TODO: Implement simulation start
        with self._lock:
            self._running = True
        
        return {
            'success': False,
            'message': 'Not yet implemented'
        }
    
    def stop_simulation(self) -> Dict[str, Any]:
        """
        Stop simulation.
        - Stops main loop
        - Calls SimStop on components
        - Clears VNETs
        
        Returns:
            {'success': bool, 'message': str}
        """
        # TODO: Implement simulation stop
        with self._lock:
            self._running = False
        
        return {
            'success': False,
            'message': 'Not yet implemented'
        }
    
    def is_running(self) -> bool:
        """
        Check if simulation is running.
        
        Returns:
            bool: True if simulation is running
        """
        with self._lock:
            return self._running
    
    def is_stable(self) -> bool:
        """
        Check if simulation is in stable state (no dirty VNETs).
        
        Returns:
            bool: True if stable
        """
        # TODO: Implement stability check
        return True
    
    # === STATE QUERIES ===
    
    def get_component_states(self, page_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get visual states of all components (or specific page).
        
        Args:
            page_id: Optional page ID to filter components
            
        Returns:
            List of component visual state dicts
        """
        # TODO: Implement state retrieval
        return []
    
    def get_vnet_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all VNETs.
        
        Returns:
            List of VNET info dicts
        """
        # TODO: Implement VNET info retrieval
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get simulation statistics.
        
        Returns:
            {
                'iterations': int,
                'time_to_stable': float,
                'dirty_vnets': int,
                'total_vnets': int,
                'components': int
            }
        """
        # TODO: Implement statistics retrieval
        return {
            'iterations': 0,
            'time_to_stable': 0.0,
            'dirty_vnets': 0,
            'total_vnets': 0,
            'components': 0
        }
    
    # === COMPONENT INTERACTION ===
    
    def interact_with_component(self, component_id: str, 
                               action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Interact with a component (e.g., toggle switch).
        
        Args:
            component_id: Component ID
            action: Action name (e.g., "toggle")
            params: Optional parameters
        
        Returns:
            {'success': bool, 'message': str}
        """
        # TODO: Implement component interaction
        return {
            'success': False,
            'message': 'Not yet implemented'
        }
    
    # === CALLBACKS ===
    
    def register_stable_callback(self, callback: Callable[[Dict], None]):
        """
        Register callback for stable state notifications.
        
        Callback signature: callback(state_data: Dict)
        
        Called when simulation reaches stable state.
        State data includes component states for rendering.
        
        Args:
            callback: Function to call on stable state
        """
        with self._lock:
            if callback not in self._stable_callbacks:
                self._stable_callbacks.append(callback)
    
    def unregister_stable_callback(self, callback: Callable):
        """
        Unregister a stable callback.
        
        Args:
            callback: Function to unregister
        """
        with self._lock:
            if callback in self._stable_callbacks:
                self._stable_callbacks.remove(callback)
    
    def _notify_stable(self, state_data: Dict):
        """
        Internal: notify all registered callbacks of stable state.
        
        Args:
            state_data: State data to pass to callbacks
        """
        with self._lock:
            callbacks = self._stable_callbacks.copy()
        
        for callback in callbacks:
            try:
                callback(state_data)
            except Exception as e:
                print(f"Error in stable callback: {e}")
