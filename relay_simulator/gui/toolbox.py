"""
Component Toolbox Panel - Left sidebar with component selection.

Provides a palette of components that can be selected and placed on the canvas.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from gui.theme import VSCodeTheme


class ComponentButton(tk.Frame):
    """
    Button representing a component type in the toolbox.
    Shows component name and can be selected.
    """
    
    def __init__(self, parent, component_type: str, display_name: str, 
                 on_select: Callable[[str], None]):
        """
        Initialize component button.
        
        Args:
            parent: Parent widget
            component_type: Component type identifier (e.g., 'Switch')
            display_name: Human-readable name to display
            on_select: Callback when button is clicked
        """
        super().__init__(parent, bg=VSCodeTheme.BG_PRIMARY)
        
        self.component_type = component_type
        self.display_name = display_name
        self.on_select = on_select
        self.selected = False
        
        # Create button
        self.button = tk.Button(
            self,
            text=display_name,
            font=VSCodeTheme.get_font('normal'),
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_PRIMARY,
            activebackground=VSCodeTheme.BG_HOVER,
            activeforeground=VSCodeTheme.FG_PRIMARY,
            relief=tk.FLAT,
            borderwidth=0,
            padx=8,
            pady=4,
            anchor=tk.W,
            command=self._on_click
        )
        self.button.pack(fill=tk.X, padx=2, pady=1)
        
        # Hover effects
        self.button.bind('<Enter>', self._on_enter)
        self.button.bind('<Leave>', self._on_leave)
    
    def _on_click(self):
        """Handle button click."""
        self.on_select(self.component_type)
    
    def _on_enter(self, event):
        """Handle mouse enter."""
        if not self.selected:
            self.button.config(bg=VSCodeTheme.BG_HOVER)
    
    def _on_leave(self, event):
        """Handle mouse leave."""
        if not self.selected:
            self.button.config(bg=VSCodeTheme.BG_SECONDARY)
    
    def set_selected(self, selected: bool):
        """
        Set selection state.
        
        Args:
            selected: True if selected, False otherwise
        """
        self.selected = selected
        if selected:
            self.button.config(bg=VSCodeTheme.BG_SELECTED, relief=tk.SUNKEN)
        else:
            self.button.config(bg=VSCodeTheme.BG_SECONDARY, relief=tk.FLAT)


class ToolboxPanel(tk.Frame):
    """
    Component toolbox panel - left sidebar with component palette.
    
    Displays available component types that can be selected for placement.
    """
    
    # Component types with display names
    COMPONENTS = [
        ('Switch', 'Switch'),
        ('Indicator', 'Indicator'),
        ('DPDTRelay', 'DPDT Relay'),
        ('VCC', 'VCC Source'),
        ('BUS', 'BUS'),
        ('SevenSegmentDisplay', '7-Segment Display'),
        ('Thumbwheel', 'Thumbwheel'),
        ('BusDisplay', 'Bus Display'),
        ('Memory', 'Memory'),
        ('Diode', 'Diode'),
    ]
    
    def __init__(self, parent, on_component_select: Optional[Callable[[Optional[str]], None]] = None):
        """
        Initialize toolbox panel.
        
        Args:
            parent: Parent widget
            on_component_select: Callback when component is selected (None = select tool)
        """
        super().__init__(parent, bg=VSCodeTheme.BG_SECONDARY)
        
        self.on_component_select = on_component_select
        self.component_buttons = {}
        self.selected_component = None  # None = Select tool active
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create toolbox widgets."""
        # Title
        title = tk.Label(
            self,
            text="Components",
            font=VSCodeTheme.get_font('large'),
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_PRIMARY,
            pady=VSCodeTheme.PADDING_MEDIUM
        )
        title.pack(fill=tk.X, padx=2)
        
        # Separator
        separator = tk.Frame(self, bg=VSCodeTheme.BG_TERTIARY, height=1)
        separator.pack(fill=tk.X, padx=2, pady=VSCodeTheme.PADDING_SMALL)
        
        # Container frame for component buttons
        button_frame = tk.Frame(self, bg=VSCodeTheme.BG_SECONDARY)
        button_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add component buttons
        for component_type, display_name in self.COMPONENTS:
            button = ComponentButton(
                button_frame,
                component_type,
                display_name,
                self._on_component_selected
            )
            button.pack(fill=tk.X, padx=2, pady=1)
            self.component_buttons[component_type] = button
    
    def _on_component_selected(self, component_type: Optional[str]):
        """
        Handle component selection.
        
        Args:
            component_type: Type of component selected (None = Select tool)
        """
        # Update selection state
        if self.selected_component is not None:
            self.component_buttons[self.selected_component].set_selected(False)
        
        self.selected_component = component_type
        self.component_buttons[component_type].set_selected(True)
        
        # Notify callback
        if self.on_component_select:
            self.on_component_select(component_type)
    
    def get_selected_component(self) -> Optional[str]:
        """
        Get currently selected component type.
        
        Returns:
            str or None: Selected component type, or None if Select tool active
        """
        return self.selected_component
    
    def select_tool(self):
        """Reset to Select tool (deselect component placement mode)."""
        self._on_component_selected(None)
    
    def deselect_all(self):
        """Deselect all components (return to normal interaction mode)."""
        for button in self.component_buttons.values():
            button.set_selected(False)
        self.selected_component = None
        if self.on_component_select:
            self.on_component_select(None)
    
    def get_component_types(self) -> list:
        """
        Get list of available component types.
        
        Returns:
            list: List of (component_type, display_name) tuples
        """
        return self.COMPONENTS.copy()
