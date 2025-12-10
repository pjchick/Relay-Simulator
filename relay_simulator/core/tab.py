"""
Tab class - Physical connection point on a component pin.
Multiple tabs can belong to one pin.
"""

from typing import Tuple, TYPE_CHECKING
from core.state import PinState

if TYPE_CHECKING:
    from core.pin import Pin


class Tab:
    """
    Tab represents a physical connection point on a component.
    Multiple tabs can share the same Pin (electrical connection).
    
    Example: An indicator has 4 tabs at different positions (12, 3, 6, 9 o'clock)
    all connected to the same pin.
    """
    
    def __init__(self, tab_id: str, parent_pin: 'Pin', relative_position: Tuple[float, float]):
        """
        Initialize tab.
        
        Args:
            tab_id: Unique tab ID (hierarchical: PageId.CompId.PinId.TabId)
            parent_pin: Pin this tab belongs to
            relative_position: (dx, dy) position relative to component center
        """
        self.tab_id = tab_id
        self.parent_pin = parent_pin
        self.relative_position = relative_position  # (dx, dy) from component center
        self._state = PinState.FLOAT
    
    @property
    def state(self) -> PinState:
        """
        Get tab state (reflects parent pin state).
        
        Returns:
            PinState: Current state
        """
        # Tab state always reflects pin state
        if self.parent_pin:
            return self.parent_pin.state
        return self._state
    
    @state.setter
    def state(self, new_state: PinState):
        """
        Set tab state (propagates to parent pin).
        
        Args:
            new_state: New state to set
        """
        if self.parent_pin:
            self.parent_pin.set_state(new_state, source_tab=self)
        else:
            self._state = new_state
    
    def get_absolute_position(self, component_x: float, component_y: float) -> Tuple[float, float]:
        """
        Get absolute position on canvas.
        
        Args:
            component_x: Component X position
            component_y: Component Y position
            
        Returns:
            tuple: (absolute_x, absolute_y)
        """
        return (
            component_x + self.relative_position[0],
            component_y + self.relative_position[1]
        )
    
    def to_dict(self) -> dict:
        """
        Serialize tab to dict.
        
        Returns:
            dict: Tab data
        """
        return {
            'tab_id': self.tab_id,
            'relative_position': self.relative_position
        }
    
    @staticmethod
    def from_dict(data: dict, parent_pin: 'Pin') -> 'Tab':
        """
        Deserialize tab from dict.
        
        Args:
            data: Tab data dict
            parent_pin: Parent pin reference
            
        Returns:
            Tab: Reconstructed tab
        """
        return Tab(
            tab_id=data['tab_id'],
            parent_pin=parent_pin,
            relative_position=tuple(data['relative_position'])
        )
    
    def __repr__(self):
        return f"Tab({self.tab_id}, pos={self.relative_position}, state={self.state})"
