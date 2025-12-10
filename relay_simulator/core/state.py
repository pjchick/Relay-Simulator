"""
Signal state definitions for the simulator.
Uses HIGH and FLOAT (not HIGH and LOW).
"""

from enum import Enum


class PinState(Enum):
    """
    Pin state enumeration.
    
    FLOAT: No signal (default state, like a disconnected wire)
    HIGH: Active signal (powered)
    
    Note: We use HIGH and FLOAT (not HIGH and LOW) because:
    - HIGH always wins when multiple signals are present
    - FLOAT represents "no connection" or "unpowered"
    - This models real relay logic better
    """
    
    FLOAT = 0
    HIGH = 1
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"PinState.{self.name}"


def combine_states(*states: PinState) -> PinState:
    """
    Combine multiple pin states using OR logic.
    HIGH always wins.
    
    Args:
        *states: Variable number of PinState values
        
    Returns:
        PinState: Combined state (HIGH if any are HIGH, else FLOAT)
        
    Examples:
        >>> combine_states(PinState.FLOAT, PinState.FLOAT)
        PinState.FLOAT
        >>> combine_states(PinState.HIGH, PinState.FLOAT)
        PinState.HIGH
        >>> combine_states(PinState.HIGH, PinState.HIGH)
        PinState.HIGH
    """
    for state in states:
        if state == PinState.HIGH:
            return PinState.HIGH
    return PinState.FLOAT


def has_state_changed(old_state: PinState, new_state: PinState) -> bool:
    """
    Detect if a state has changed.
    
    Args:
        old_state: Previous PinState value
        new_state: Current PinState value
        
    Returns:
        bool: True if the state has changed, False otherwise
        
    Examples:
        >>> has_state_changed(PinState.FLOAT, PinState.HIGH)
        True
        >>> has_state_changed(PinState.HIGH, PinState.HIGH)
        False
    """
    return old_state != new_state


def states_equal(state1: PinState, state2: PinState) -> bool:
    """
    Check if two states are equal.
    
    Args:
        state1: First PinState value
        state2: Second PinState value
        
    Returns:
        bool: True if states are equal, False otherwise
        
    Examples:
        >>> states_equal(PinState.HIGH, PinState.HIGH)
        True
        >>> states_equal(PinState.HIGH, PinState.FLOAT)
        False
    """
    return state1 == state2
