"""
Core package - Core simulation classes and algorithms.
"""

# Import key classes for easier access
from .state import PinState, combine_states, has_state_changed, states_equal
from .id_manager import IDManager
from .tab import Tab
from .pin import Pin
from .page import Page
from .document import Document
from .file_io import FileIO

__all__ = [
    'PinState',
    'combine_states',
    'has_state_changed',
    'states_equal',
    'IDManager',
    'Tab',
    'Pin',
    'Page',
    'Document',
    'FileIO'
]
