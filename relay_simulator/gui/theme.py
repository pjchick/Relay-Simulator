"""
Theme Configuration for Relay Simulator III

Provides VS Code-style dark theme colors, fonts, and spacing constants
for a consistent, modern appearance across the GUI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Tuple


class VSCodeTheme:
    """
    VS Code dark theme color palette and styling constants.
    
    This class provides color constants matching Visual Studio Code's dark theme,
    along with font definitions, spacing, and ttk.Style configuration methods.
    """
    
    # Background Colors
    BG_PRIMARY = "#1e1e1e"          # Main background (editor background)
    BG_SECONDARY = "#252526"        # Secondary background (sidebar)
    BG_TERTIARY = "#2d2d30"         # Tertiary background (panels)
    BG_HOVER = "#2a2d2e"            # Hover state
    BG_SELECTED = "#094771"         # Selected item background
    BG_ACTIVE = "#0e639c"           # Active element background
    
    # Foreground Colors
    FG_PRIMARY = "#cccccc"          # Primary text
    FG_SECONDARY = "#969696"        # Secondary text (dimmed)
    FG_DISABLED = "#656565"         # Disabled text
    FG_BRIGHT = "#ffffff"           # Bright text (emphasis)
    
    # Accent Colors
    ACCENT_BLUE = "#007acc"         # Primary accent (links, buttons)
    ACCENT_GREEN = "#4ec9b0"        # Success, powered components
    ACCENT_ORANGE = "#ce9178"       # Warning
    ACCENT_RED = "#f48771"          # Error, unpowered components
    ACCENT_PURPLE = "#c586c0"       # Special elements
    
    # Border Colors
    BORDER_DEFAULT = "#3e3e42"      # Default border
    BORDER_FOCUS = "#007acc"        # Focused element border
    BORDER_SUBTLE = "#2d2d30"       # Subtle separator
    
    # Canvas Colors
    CANVAS_BG = "#1e1e1e"           # Canvas background
    CANVAS_GRID = "#2d2d2d"         # Grid lines
    CANVAS_GRID_MAJOR = "#3e3e3e"   # Major grid lines (every 5th line)
    
    # Component Colors
    COMPONENT_FILL = "#2d2d30"      # Component body fill
    COMPONENT_STROKE = "#cccccc"    # Component outline
    COMPONENT_SELECTED = "#007acc"  # Selected component highlight
    COMPONENT_LABEL = "#cccccc"     # Component label text
    
    # Wire Colors
    WIRE_UNPOWERED = "#656565"      # Unpowered wire
    WIRE_POWERED = "#4ec9b0"        # Powered wire
    WIRE_SELECTED = "#007acc"       # Selected wire
    WIRE_WAYPOINT = "#cccccc"       # Waypoint marker
    WIRE_JUNCTION = "#ce9178"       # Junction marker
    
    # Font Sizes
    FONT_SIZE_SMALL = 9             # Small text (status bar)
    FONT_SIZE_NORMAL = 10           # Normal text (UI elements)
    FONT_SIZE_MEDIUM = 11           # Medium text (headers)
    FONT_SIZE_LARGE = 12            # Large text (titles)
    FONT_SIZE_CANVAS_LABEL = 10     # Component labels on canvas
    
    # Font Families
    FONT_FAMILY_UI = "Segoe UI"     # UI elements
    FONT_FAMILY_MONO = "Consolas"   # Monospace (IDs, technical text)
    
    # Spacing
    PADDING_SMALL = 4               # Small padding
    PADDING_MEDIUM = 8              # Medium padding
    PADDING_LARGE = 12              # Large padding
    SPACING_SMALL = 4               # Small spacing between elements
    SPACING_MEDIUM = 8              # Medium spacing
    SPACING_LARGE = 12              # Large spacing
    
    # Widget Sizes
    BUTTON_HEIGHT = 24              # Standard button height
    TOOLBAR_HEIGHT = 32             # Toolbar height
    STATUSBAR_HEIGHT = 24           # Status bar height
    TOOLBOX_WIDTH = 200             # Toolbox panel width
    PROPERTIES_WIDTH = 250          # Properties panel width
    
    # Component Rendering
    COMPONENT_OUTLINE = '#505050'   # Component outline color
    COMPONENT_FILL = '#2d2d2d'      # Component fill color
    COMPONENT_SELECTED = ACCENT_BLUE  # Selected component highlight
    COMPONENT_TEXT = FG_PRIMARY     # Component label text
    
    # Component-specific colors
    SWITCH_ON = '#ff0000'           # Switch ON color (red)
    SWITCH_OFF = '#800000'          # Switch OFF color (dark red)
    INDICATOR_ON = '#00ff00'        # Indicator ON color (green)
    INDICATOR_OFF = '#004000'       # Indicator OFF color (dark green)
    RELAY_COIL = '#c0c0c0'          # Relay coil color (silver)
    RELAY_CONTACT = '#ffa500'       # Relay contact color (orange)
    VCC_COLOR = '#ff0000'           # VCC symbol color (red)
    
    # Wire colors
    WIRE_UNPOWERED = '#505050'      # Unpowered wire (gray)
    WIRE_POWERED = '#00ff00'        # Powered wire (green)
    WIRE_SELECTED = ACCENT_BLUE     # Selected wire
    WIRE_WIDTH = 2                  # Wire line width
    
    # Tab/Pin rendering
    TAB_SIZE = 6                    # Tab indicator size (pixels)
    TAB_COLOR = '#808080'           # Tab color (gray)
    TAB_HOVER = ACCENT_BLUE         # Tab hover color
    
    @staticmethod
    def configure_styles(root: tk.Tk) -> None:
        """
        Configure ttk.Style for all themed widgets.
        
        This method sets up the ttk.Style object with custom styling for all
        ttk widgets used in the application, ensuring a consistent VS Code
        dark theme appearance.
        
        Args:
            root: The root Tk window
        """
        style = ttk.Style(root)
        
        # Use 'clam' theme as base (works well for dark themes)
        style.theme_use('clam')
        
        # Configure root window colors
        root.configure(bg=VSCodeTheme.BG_PRIMARY)
        
        # Frame styles
        style.configure(
            'TFrame',
            background=VSCodeTheme.BG_PRIMARY
        )
        
        style.configure(
            'Secondary.TFrame',
            background=VSCodeTheme.BG_SECONDARY
        )
        
        style.configure(
            'Tertiary.TFrame',
            background=VSCodeTheme.BG_TERTIARY
        )
        
        # Label styles
        style.configure(
            'TLabel',
            background=VSCodeTheme.BG_PRIMARY,
            foreground=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL)
        )
        
        style.configure(
            'Secondary.TLabel',
            background=VSCodeTheme.BG_SECONDARY,
            foreground=VSCodeTheme.FG_SECONDARY
        )
        
        style.configure(
            'Header.TLabel',
            background=VSCodeTheme.BG_PRIMARY,
            foreground=VSCodeTheme.FG_BRIGHT,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_MEDIUM, 'bold')
        )
        
        # Button styles
        style.configure(
            'TButton',
            background=VSCodeTheme.BG_TERTIARY,
            foreground=VSCodeTheme.FG_PRIMARY,
            bordercolor=VSCodeTheme.BORDER_DEFAULT,
            focuscolor=VSCodeTheme.BORDER_FOCUS,
            lightcolor=VSCodeTheme.BG_TERTIARY,
            darkcolor=VSCodeTheme.BG_TERTIARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL)
        )
        
        style.map(
            'TButton',
            background=[('active', VSCodeTheme.BG_HOVER), ('pressed', VSCodeTheme.BG_SELECTED)],
            foreground=[('disabled', VSCodeTheme.FG_DISABLED)]
        )
        
        # Accent button (for primary actions)
        style.configure(
            'Accent.TButton',
            background=VSCodeTheme.ACCENT_BLUE,
            foreground=VSCodeTheme.FG_BRIGHT
        )
        
        style.map(
            'Accent.TButton',
            background=[('active', VSCodeTheme.BG_ACTIVE)]
        )
        
        # Entry styles
        style.configure(
            'TEntry',
            fieldbackground=VSCodeTheme.BG_TERTIARY,
            foreground=VSCodeTheme.FG_PRIMARY,
            bordercolor=VSCodeTheme.BORDER_DEFAULT,
            insertcolor=VSCodeTheme.FG_PRIMARY
        )
        
        style.map(
            'TEntry',
            fieldbackground=[('focus', VSCodeTheme.BG_PRIMARY)],
            bordercolor=[('focus', VSCodeTheme.BORDER_FOCUS)]
        )
        
        # Notebook (tabs) styles
        style.configure(
            'TNotebook',
            background=VSCodeTheme.BG_SECONDARY,
            bordercolor=VSCodeTheme.BORDER_DEFAULT,
            tabmargins=[0, 0, 0, 0]
        )
        
        style.configure(
            'TNotebook.Tab',
            background=VSCodeTheme.BG_TERTIARY,
            foreground=VSCodeTheme.FG_SECONDARY,
            padding=[12, 4],
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL)
        )
        
        style.map(
            'TNotebook.Tab',
            background=[('selected', VSCodeTheme.BG_PRIMARY)],
            foreground=[('selected', VSCodeTheme.FG_BRIGHT)],
            expand=[('selected', [1, 1, 1, 0])]
        )
        
        # Separator styles
        style.configure(
            'TSeparator',
            background=VSCodeTheme.BORDER_SUBTLE
        )
        
    @staticmethod
    def get_font(size: str = 'normal', bold: bool = False, mono: bool = False) -> Tuple[str, int, str]:
        """
        Get a font tuple for the specified size and style.
        
        Args:
            size: Font size ('small', 'normal', 'medium', 'large', or 'canvas')
            bold: Whether the font should be bold
            mono: Whether to use monospace font
            
        Returns:
            Tuple of (font_family, font_size, font_weight)
        """
        size_map = {
            'small': VSCodeTheme.FONT_SIZE_SMALL,
            'normal': VSCodeTheme.FONT_SIZE_NORMAL,
            'medium': VSCodeTheme.FONT_SIZE_MEDIUM,
            'large': VSCodeTheme.FONT_SIZE_LARGE,
            'canvas': VSCodeTheme.FONT_SIZE_CANVAS_LABEL
        }
        
        font_family = VSCodeTheme.FONT_FAMILY_MONO if mono else VSCodeTheme.FONT_FAMILY_UI
        font_size = size_map.get(size, VSCodeTheme.FONT_SIZE_NORMAL)
        font_weight = 'bold' if bold else 'normal'
        
        return (font_family, font_size, font_weight)


# Convenience function for quick access
def apply_theme(root: tk.Tk) -> None:
    """
    Apply the VS Code dark theme to the application.
    
    Args:
        root: The root Tk window
    """
    VSCodeTheme.configure_styles(root)
