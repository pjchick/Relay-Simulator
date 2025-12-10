"""
Abstract canvas adapter for component rendering.
Provides platform-independent drawing interface.
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Optional


class CanvasAdapter(ABC):
    """
    Abstract interface for drawing operations.
    Allows components to render without depending on specific GUI toolkit.
    
    Designer provides concrete implementation (TkinterCanvasAdapter).
    """
    
    @abstractmethod
    def draw_circle(self, x: float, y: float, radius: float, 
                   fill: Optional[str] = None, 
                   outline: Optional[str] = None, 
                   width: int = 1) -> Any:
        """
        Draw a circle.
        
        Args:
            x: Center X coordinate
            y: Center Y coordinate
            radius: Circle radius
            fill: Fill color (hex string or color name)
            outline: Outline color
            width: Outline width
            
        Returns:
            Platform-specific item ID
        """
        pass
    
    @abstractmethod
    def draw_rectangle(self, x1: float, y1: float, x2: float, y2: float,
                      fill: Optional[str] = None, 
                      outline: Optional[str] = None, 
                      width: int = 1) -> Any:
        """
        Draw a rectangle.
        
        Args:
            x1: Top-left X
            y1: Top-left Y
            x2: Bottom-right X
            y2: Bottom-right Y
            fill: Fill color
            outline: Outline color
            width: Outline width
            
        Returns:
            Platform-specific item ID
        """
        pass
    
    @abstractmethod
    def draw_line(self, x1: float, y1: float, x2: float, y2: float,
                 fill: Optional[str] = None, 
                 width: int = 1) -> Any:
        """
        Draw a line.
        
        Args:
            x1: Start X
            y1: Start Y
            x2: End X
            y2: End Y
            fill: Line color
            width: Line width
            
        Returns:
            Platform-specific item ID
        """
        pass
    
    @abstractmethod
    def draw_polygon(self, points: List[Tuple[float, float]], 
                    fill: Optional[str] = None, 
                    outline: Optional[str] = None, 
                    width: int = 1) -> Any:
        """
        Draw a polygon.
        
        Args:
            points: List of (x, y) coordinate tuples
            fill: Fill color
            outline: Outline color
            width: Outline width
            
        Returns:
            Platform-specific item ID
        """
        pass
    
    @abstractmethod
    def draw_text(self, x: float, y: float, text: str, 
                 font: Optional[Tuple] = None, 
                 fill: Optional[str] = None, 
                 anchor: str = 'center') -> Any:
        """
        Draw text.
        
        Args:
            x: X coordinate
            y: Y coordinate
            text: Text string
            font: Font tuple (family, size, style)
            fill: Text color
            anchor: Text anchor ('center', 'nw', 'ne', 'sw', 'se', etc.)
            
        Returns:
            Platform-specific item ID
        """
        pass
    
    @abstractmethod
    def clear(self):
        """Clear all drawn items from canvas"""
        pass
