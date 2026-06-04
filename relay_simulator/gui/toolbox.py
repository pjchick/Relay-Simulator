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
            padx=2,
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


class ComponentGroup(tk.Frame):
    """
    Collapsible group header for component categories.
    """
    
    def __init__(self, parent, group_name: str, is_expanded: bool = True, on_toggle: Optional[Callable] = None):
        """
        Initialize component group header.
        
        Args:
            parent: Parent widget
            group_name: Name of the group
            is_expanded: Whether group starts expanded
            on_toggle: Callback when group is toggled
        """
        super().__init__(parent, bg=VSCodeTheme.BG_SECONDARY)
        
        self.group_name = group_name
        self.is_expanded = is_expanded
        self.content_frame = None
        self.on_toggle = on_toggle
        
        # Create header button
        self.header = tk.Button(
            self,
            text=f"▼ {group_name}" if is_expanded else f"▶ {group_name}",
            font=VSCodeTheme.get_font('normal'),
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_PRIMARY,
            activebackground=VSCodeTheme.BG_HOVER,
            activeforeground=VSCodeTheme.FG_PRIMARY,
            relief=tk.FLAT,
            borderwidth=0,
            padx=2,
            pady=4,
            anchor=tk.W,
            command=self.toggle
        )
        self.header.pack(fill=tk.X)
        
        # Hover effects
        self.header.bind('<Enter>', lambda e: self.header.config(bg=VSCodeTheme.BG_HOVER))
        self.header.bind('<Leave>', lambda e: self.header.config(bg=VSCodeTheme.BG_TERTIARY))
    
    def toggle(self):
        """Toggle group expansion."""
        self.is_expanded = not self.is_expanded
        self.header.config(text=f"▼ {self.group_name}" if self.is_expanded else f"▶ {self.group_name}")
        
        # Show/hide content
        if self.content_frame:
            if self.is_expanded:
                self.content_frame.pack(fill=tk.X, after=self.header)
            else:
                self.content_frame.pack_forget()
        
        # Notify parent of toggle
        if self.on_toggle:
            self.on_toggle()
    
    def set_content_frame(self, frame):
        """Set the content frame for this group."""
        self.content_frame = frame
        if self.is_expanded:
            self.content_frame.pack(fill=tk.X, after=self.header)


class ToolboxPanel(tk.Frame):
    """
    Component toolbox panel - left sidebar with component palette.
    
    Displays available component types that can be selected for placement.
    Supports collapsible groups for organizing components.
    """
    
    # Component groups - add/edit groups here
    # Format: 'Group Name': [('ComponentType', 'Display Name'), ...]
    COMPONENT_GROUPS = {
        'Basic': [
            ('Switch', 'Powered Switch'),
            ('SPSTSwitch', 'SPST Switch'),
            ('SPDTSwitch', 'SPDT Switch'),
            ('Clock', 'Clock'),
            ('Indicator', 'Indicator'),
            ('Link', 'Link'),
            ('Diode', 'Diode'),
        ],
        'Relays': [
            ('DPDTRelay', 'DPDT Relay'),
            ('GroundDPDTRelay', 'Ground DPDT Relay'),
            ('LatchingRelay', 'Latching Relay'),
            ('GroundLatchingRelay', 'Ground Latching Relay'),
        ],
        'Power': [
            ('VCC', 'VCC Source'),
            ('GND', 'Relay GND'),
        ],
        'Data': [
            ('BUS', 'BUS'),
            ('SevenSegmentDisplay', '7-Segment Display'),
            ('Thumbwheel', 'Thumbwheel'),
            ('BusDisplay', 'Bus Display'),
            ('Memory', 'Memory'),
        ],
        'Annotation': [
            ('Text', 'Text'),
            ('Box', 'Box'),
        ],
    }
    
    # Ungrouped components (appear at bottom)
    UNGROUPED_COMPONENTS = [

    ]
    
    
    def __init__(self, parent, on_component_select: Optional[Callable[[Optional[str]], None]] = None):
        """
        Initialize toolbox panel.
        
        Args:
            parent: Parent widget
            on_component_select: Callback when component is selected (None = select tool)
        """
        super().__init__(parent, bg=VSCodeTheme.BG_SECONDARY, width=VSCodeTheme.TOOLBOX_WIDTH)
        
        self.on_component_select = on_component_select
        self.component_buttons = {}
        self.selected_component = None  # None = Select tool active
        
        # Prevent expansion beyond configured width
        self.pack_propagate(False)
        
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
        title.pack(fill=tk.X, padx=1)
        
        # Separator
        separator = tk.Frame(self, bg=VSCodeTheme.BG_TERTIARY, height=1)
        separator.pack(fill=tk.X, padx=1, pady=VSCodeTheme.PADDING_SMALL)
        
        # Expand/Collapse All buttons
        button_frame = tk.Frame(self, bg=VSCodeTheme.BG_SECONDARY)
        button_frame.pack(fill=tk.X, padx=1, pady=(0, VSCodeTheme.PADDING_SMALL))
        
        expand_all_btn = tk.Button(
            button_frame,
            text="Expand All",
            font=VSCodeTheme.get_font('small'),
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_PRIMARY,
            activebackground=VSCodeTheme.BG_HOVER,
            activeforeground=VSCodeTheme.FG_PRIMARY,
            relief=tk.FLAT,
            borderwidth=0,
            padx=1,
            pady=3,
            command=self.expand_all
        )
        expand_all_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 1))
        expand_all_btn.bind('<Enter>', lambda e: expand_all_btn.config(bg=VSCodeTheme.BG_HOVER))
        expand_all_btn.bind('<Leave>', lambda e: expand_all_btn.config(bg=VSCodeTheme.BG_TERTIARY))
        
        collapse_all_btn = tk.Button(
            button_frame,
            text="Collapse All",
            font=VSCodeTheme.get_font('small'),
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_PRIMARY,
            activebackground=VSCodeTheme.BG_HOVER,
            activeforeground=VSCodeTheme.FG_PRIMARY,
            relief=tk.FLAT,
            borderwidth=0,
            padx=1,
            pady=3,
            command=self.collapse_all
        )
        collapse_all_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(1, 0))
        collapse_all_btn.bind('<Enter>', lambda e: collapse_all_btn.config(bg=VSCodeTheme.BG_HOVER))
        collapse_all_btn.bind('<Leave>', lambda e: collapse_all_btn.config(bg=VSCodeTheme.BG_TERTIARY))
        
        # Create scrollable container for component buttons
        # Container frame holds canvas + scrollbar
        container = tk.Frame(self, bg=VSCodeTheme.BG_SECONDARY)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = tk.Canvas(
            container,
            bg=VSCodeTheme.BG_SECONDARY,
            highlightthickness=0,
            borderwidth=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(
            container,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            bg=VSCodeTheme.BG_TERTIARY,
            troughcolor=VSCodeTheme.BG_SECONDARY,
            activebackground=VSCodeTheme.BG_HOVER
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure canvas to use scrollbar
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create frame inside canvas to hold buttons
        self.button_frame = tk.Frame(self.canvas, bg=VSCodeTheme.BG_SECONDARY)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.button_frame,
            anchor=tk.NW
        )
        
        # Add grouped components
        self.groups = {}
        for group_name, components in self.COMPONENT_GROUPS.items():
            # Create group header
            group = ComponentGroup(self.button_frame, group_name, is_expanded=True, on_toggle=self._on_group_toggle)
            group.pack(fill=tk.X, padx=1, pady=2)
            self.groups[group_name] = group
            
            # Create content frame for group
            content_frame = tk.Frame(self.button_frame, bg=VSCodeTheme.BG_SECONDARY)
            group.set_content_frame(content_frame)
            
            # Add component buttons to group
            for component_type, display_name in components:
                button = ComponentButton(
                    content_frame,
                    component_type,
                    display_name,
                    self._on_component_selected
                )
                button.pack(fill=tk.X, padx=2, pady=1)  # Extra left padding for hierarchy
                self.component_buttons[component_type] = button
        
        # Add separator before ungrouped components if there are any
        if self.UNGROUPED_COMPONENTS:
            separator = tk.Frame(self.button_frame, bg=VSCodeTheme.BG_TERTIARY, height=1)
            separator.pack(fill=tk.X, padx=1, pady=8)
        
        # Add ungrouped components at the bottom
        for component_type, display_name in self.UNGROUPED_COMPONENTS:
            button = ComponentButton(
                self.button_frame,
                component_type,
                display_name,
                self._on_component_selected
            )
            button.pack(fill=tk.X, padx=2, pady=1)
            self.component_buttons[component_type] = button
        
        # Update scroll region after buttons are added
        self.button_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Bind mousewheel for scrolling
        self.canvas.bind('<Enter>', self._on_canvas_enter)
        self.canvas.bind('<Leave>', self._on_canvas_leave)
        
        # Bind frame resize to update canvas window width
        self.button_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
    
    def _on_frame_configure(self, event):
        """Update scroll region when frame size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Update canvas window width to match canvas width."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def _on_canvas_enter(self, event):
        """Bind mousewheel when mouse enters canvas."""
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind_all('<Button-4>', self._on_mousewheel)  # Linux scroll up
        self.canvas.bind_all('<Button-5>', self._on_mousewheel)  # Linux scroll down
    
    def _on_canvas_leave(self, event):
        """Unbind mousewheel when mouse leaves canvas."""
        self.canvas.unbind_all('<MouseWheel>')
        self.canvas.unbind_all('<Button-4>')
        self.canvas.unbind_all('<Button-5>')
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scroll."""
        # Windows/MacOS
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
    
    def _on_group_toggle(self):
        """Handle group expand/collapse - update scroll region."""
        self.button_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def expand_all(self):
        """Expand all component groups."""
        for group in self.groups.values():
            if not group.is_expanded:
                group.toggle()
    
    def collapse_all(self):
        """Collapse all component groups."""
        for group in self.groups.values():
            if group.is_expanded:
                group.toggle()
    
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
        # Combine all grouped and ungrouped components
        all_components = []
        for components in self.COMPONENT_GROUPS.values():
            all_components.extend(components)
        all_components.extend(self.UNGROUPED_COMPONENTS)
        return all_components
