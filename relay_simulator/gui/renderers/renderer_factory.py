"""
Renderer factory for creating appropriate renderers for components.
"""

import tkinter as tk
from typing import Dict, Type
from components.base import Component
from gui.renderers.base_renderer import ComponentRenderer
from gui.renderers.switch_renderer import SwitchRenderer
from gui.renderers.indicator_renderer import IndicatorRenderer
from gui.renderers.relay_renderer import RelayRenderer
from gui.renderers.vcc_renderer import VCCRenderer
from gui.renderers.bus_renderer import BUSRenderer
from gui.renderers.seven_segment_display_renderer import SevenSegmentDisplayRenderer
from gui.renderers.thumbwheel_renderer import ThumbwheelRenderer
from gui.renderers.bus_display_renderer import BusDisplayRenderer
from gui.renderers.memory_renderer import MemoryRenderer
from gui.renderers.diode_renderer import DiodeRenderer
from gui.renderers.clock_renderer import ClockRenderer
from gui.renderers.link_renderer import LinkRenderer
from gui.renderers.text_renderer import TextRenderer


class RendererFactory:
    """
    Factory for creating component renderers.
    
    Maps component types to their renderer classes.
    """
    
    # Mapping of component type to renderer class
    _renderer_map: Dict[str, Type[ComponentRenderer]] = {
        'Switch': SwitchRenderer,
        'Indicator': IndicatorRenderer,
        'DPDTRelay': RelayRenderer,
        'VCC': VCCRenderer,
        'BUS': BUSRenderer,
        'SevenSegmentDisplay': SevenSegmentDisplayRenderer,
        'Thumbwheel': ThumbwheelRenderer,
        'BusDisplay': BusDisplayRenderer,
        'Memory': MemoryRenderer,
        'Diode': DiodeRenderer,
        'Clock': ClockRenderer,
        'Link': LinkRenderer,
        'Text': TextRenderer,
    }
    
    @classmethod
    def create_renderer(cls, canvas: tk.Canvas, component: Component) -> ComponentRenderer:
        """
        Create appropriate renderer for a component.
        
        Args:
            canvas: tkinter Canvas to draw on
            component: Component to create renderer for
            
        Returns:
            ComponentRenderer instance
            
        Raises:
            ValueError: If component type has no registered renderer
        """
        component_type = component.component_type
        
        if component_type not in cls._renderer_map:
            raise ValueError(f"No renderer registered for component type: {component_type}")
            
        renderer_class = cls._renderer_map[component_type]
        return renderer_class(canvas, component)
    
    @classmethod
    def register_renderer(cls, component_type: str, renderer_class: Type[ComponentRenderer]) -> None:
        """
        Register a custom renderer for a component type.
        
        Args:
            component_type: Component type string
            renderer_class: Renderer class to register
        """
        cls._renderer_map[component_type] = renderer_class
    
    @classmethod
    def get_supported_types(cls) -> list[str]:
        """
        Get list of supported component types.
        
        Returns:
            List of component type strings
        """
        return list(cls._renderer_map.keys())
