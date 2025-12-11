"""
Properties Panel - Right sidebar for editing component properties.

Displays properties of selected component(s) with grouped sections:
- Component section (id, type, position, rotation)
- Properties section (component-specific properties)
- Advanced section (additional settings)
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Callable
from gui.theme import VSCodeTheme


class PropertySection:
    """
    Collapsible section in properties panel.
    
    Features:
    - Header with expand/collapse arrow
    - Collapsible content frame
    - VS Code-style appearance
    """
    
    def __init__(self, parent: tk.Widget, title: str):
        """
        Initialize property section.
        
        Args:
            parent: Parent widget
            title: Section title
        """
        self.parent = parent
        self.title = title
        self.expanded = True
        
        # Container frame
        self.frame = tk.Frame(
            parent,
            bg=VSCodeTheme.BG_PRIMARY
        )
        self.frame.pack(fill=tk.X, pady=(0, 1))
        
        # Header (clickable to expand/collapse)
        self.header = tk.Frame(
            self.frame,
            bg=VSCodeTheme.BG_SECONDARY,
            cursor="hand2"
        )
        self.header.pack(fill=tk.X)
        self.header.bind('<Button-1>', self._toggle_expansion)
        
        # Arrow label
        self.arrow_label = tk.Label(
            self.header,
            text="▼",
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_PRIMARY,
            font=("Segoe UI", 8),
            width=2
        )
        self.arrow_label.pack(side=tk.LEFT, padx=(5, 0))
        self.arrow_label.bind('<Button-1>', self._toggle_expansion)
        
        # Title label
        self.title_label = tk.Label(
            self.header,
            text=title,
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_PRIMARY,
            font=("Segoe UI", 9, "bold"),
            anchor=tk.W
        )
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=3)
        self.title_label.bind('<Button-1>', self._toggle_expansion)
        
        # Content frame
        self.content = tk.Frame(
            self.frame,
            bg=VSCodeTheme.BG_PRIMARY
        )
        self.content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def _toggle_expansion(self, event=None):
        """Toggle section expansion."""
        self.expanded = not self.expanded
        
        if self.expanded:
            self.arrow_label.config(text="▼")
            self.content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        else:
            self.arrow_label.config(text="▶")
            self.content.pack_forget()
    
    def add_property(self, label: str, widget: tk.Widget) -> None:
        """
        Add a property editor to this section.
        
        Args:
            label: Property label
            widget: Editor widget
        """
        row = tk.Frame(self.content, bg=VSCodeTheme.BG_PRIMARY)
        row.pack(fill=tk.X, pady=2)
        
        label_widget = tk.Label(
            row,
            text=label,
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=("Segoe UI", 9),
            anchor=tk.W,
            width=12
        )
        label_widget.pack(side=tk.LEFT, padx=(0, 5))
        
        widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def clear(self):
        """Clear all properties from this section."""
        for widget in self.content.winfo_children():
            widget.destroy()


class PropertyEditor:
    """Base class for property editors."""
    
    def __init__(self, parent: tk.Widget):
        """
        Initialize property editor.
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.widget = None
        self.on_change_callback: Optional[Callable] = None
    
    def set_value(self, value: Any) -> None:
        """Set editor value."""
        raise NotImplementedError
    
    def get_value(self) -> Any:
        """Get editor value."""
        raise NotImplementedError
    
    def set_on_change(self, callback: Callable) -> None:
        """Set callback for value changes."""
        self.on_change_callback = callback


class TextPropertyEditor(PropertyEditor):
    """Text entry property editor."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize text editor."""
        super().__init__(parent)
        
        self.widget = tk.Entry(
            parent,
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_PRIMARY,
            insertbackground=VSCodeTheme.FG_PRIMARY,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=VSCodeTheme.BG_SECONDARY,
            highlightcolor=VSCodeTheme.ACCENT_BLUE,
            font=("Segoe UI", 9)
        )
        
        self.widget.bind('<Return>', lambda e: self._on_change())
        self.widget.bind('<FocusOut>', lambda e: self._on_change())
    
    def _on_change(self):
        """Handle value change."""
        if self.on_change_callback:
            self.on_change_callback(self.get_value())
    
    def set_value(self, value: Any) -> None:
        """Set text value."""
        self.widget.delete(0, tk.END)
        self.widget.insert(0, str(value))
    
    def get_value(self) -> str:
        """Get text value."""
        return self.widget.get()


class NumberPropertyEditor(PropertyEditor):
    """Numeric entry property editor."""
    
    def __init__(self, parent: tk.Widget, min_val: float = None, max_val: float = None):
        """
        Initialize number editor.
        
        Args:
            parent: Parent widget
            min_val: Minimum allowed value
            max_val: Maximum allowed value
        """
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        
        self.widget = tk.Entry(
            parent,
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_PRIMARY,
            insertbackground=VSCodeTheme.FG_PRIMARY,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=VSCodeTheme.BG_SECONDARY,
            highlightcolor=VSCodeTheme.ACCENT_BLUE,
            font=("Segoe UI", 9),
            width=10
        )
        
        self.widget.bind('<Return>', lambda e: self._on_change())
        self.widget.bind('<FocusOut>', lambda e: self._on_change())
    
    def _on_change(self):
        """Handle value change."""
        if self.on_change_callback:
            try:
                value = self.get_value()
                self.on_change_callback(value)
            except ValueError:
                # Invalid number, revert to previous value
                pass
    
    def set_value(self, value: Any) -> None:
        """Set numeric value."""
        self.widget.delete(0, tk.END)
        self.widget.insert(0, str(value))
    
    def get_value(self) -> float:
        """Get numeric value."""
        value = float(self.widget.get())
        if self.min_val is not None:
            value = max(value, self.min_val)
        if self.max_val is not None:
            value = min(value, self.max_val)
        return value


class DropdownPropertyEditor(PropertyEditor):
    """Dropdown property editor."""
    
    def __init__(self, parent: tk.Widget, options: list):
        """
        Initialize dropdown editor.
        
        Args:
            parent: Parent widget
            options: List of available options
        """
        super().__init__(parent)
        self.options = options
        
        self.var = tk.StringVar()
        self.widget = ttk.Combobox(
            parent,
            textvariable=self.var,
            values=options,
            state="readonly",
            font=("Segoe UI", 9),
            width=12
        )
        
        self.widget.bind('<<ComboboxSelected>>', lambda e: self._on_change())
    
    def _on_change(self):
        """Handle value change."""
        if self.on_change_callback:
            self.on_change_callback(self.get_value())
    
    def set_value(self, value: Any) -> None:
        """Set dropdown value."""
        self.var.set(str(value))
    
    def get_value(self) -> str:
        """Get dropdown value."""
        return self.var.get()


class CheckboxPropertyEditor(PropertyEditor):
    """Checkbox property editor."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize checkbox editor."""
        super().__init__(parent)
        
        self.var = tk.BooleanVar()
        self.widget = tk.Checkbutton(
            parent,
            variable=self.var,
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            selectcolor=VSCodeTheme.BG_TERTIARY,
            activebackground=VSCodeTheme.BG_PRIMARY,
            activeforeground=VSCodeTheme.FG_PRIMARY,
            command=self._on_change
        )
    
    def _on_change(self):
        """Handle value change."""
        if self.on_change_callback:
            self.on_change_callback(self.get_value())
    
    def set_value(self, value: Any) -> None:
        """Set checkbox value."""
        self.var.set(bool(value))
    
    def get_value(self) -> bool:
        """Get checkbox value."""
        return self.var.get()


class PropertiesPanel:
    """
    Properties panel for editing component properties.
    
    Right sidebar with grouped property sections.
    Updates selected component properties in real-time.
    """
    
    def __init__(self, parent: tk.Widget):
        """
        Initialize properties panel.
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.current_component = None
        self.property_editors: Dict[str, PropertyEditor] = {}
        
        # Main container
        self.frame = tk.Frame(
            parent,
            bg=VSCodeTheme.BG_PRIMARY,
            width=250
        )
        
        # Title
        title = tk.Label(
            self.frame,
            text="PROPERTIES",
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=("Segoe UI", 9, "bold"),
            anchor=tk.W,
            padx=10,
            pady=5
        )
        title.pack(fill=tk.X)
        
        # Scrollable content
        canvas = tk.Canvas(
            self.frame,
            bg=VSCodeTheme.BG_PRIMARY,
            highlightthickness=0
        )
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(
            self.frame,
            orient=tk.VERTICAL,
            command=canvas.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Content frame inside canvas
        self.content = tk.Frame(canvas, bg=VSCodeTheme.BG_PRIMARY)
        canvas_window = canvas.create_window((0, 0), window=self.content, anchor=tk.NW)
        
        # Update scroll region when content changes
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Make content frame fill canvas width
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        self.content.bind('<Configure>', on_configure)
        canvas.bind('<Configure>', on_configure)
        
        # Create sections
        self.component_section = PropertySection(self.content, "Component")
        self.properties_section = PropertySection(self.content, "Properties")
        self.advanced_section = PropertySection(self.content, "Advanced")
        
        # Show "No selection" message initially
        self._show_no_selection()
    
    def _show_no_selection(self):
        """Show message when no component is selected."""
        self.component_section.clear()
        self.properties_section.clear()
        self.advanced_section.clear()
        
        message = tk.Label(
            self.component_section.content,
            text="No component selected",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=("Segoe UI", 9, "italic")
        )
        message.pack(pady=20)
    
    def set_component(self, component) -> None:
        """
        Display properties for a component.
        
        Args:
            component: Component to display properties for
        """
        self.current_component = component
        self.property_editors.clear()
        
        # Clear all sections
        self.component_section.clear()
        self.properties_section.clear()
        self.advanced_section.clear()
        
        if not component:
            self._show_no_selection()
            return
        
        # Component section - basic info
        self._add_component_properties()
        
        # Properties section - component-specific
        self._add_component_specific_properties()
        
        # Advanced section - extra settings
        self._add_advanced_properties()
    
    def _add_component_properties(self):
        """Add basic component properties (id, type, position, rotation)."""
        if not self.current_component:
            return
        
        # ID (editable with validation)
        id_frame = tk.Frame(self.component_section.content, bg=VSCodeTheme.BG_PRIMARY)
        id_frame.pack(fill=tk.X, pady=2)
        
        id_label = tk.Label(
            id_frame,
            text="ID:",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=("Segoe UI", 9),
            anchor=tk.W,
            width=12
        )
        id_label.pack(side=tk.LEFT, padx=(0, 5))
        
        id_editor = TextPropertyEditor(id_frame)
        id_editor.set_value(self.current_component.component_id)
        id_editor.set_on_change(lambda v: self._update_component_id(v))
        id_editor.widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.property_editors['id'] = id_editor
        
        # Type (read-only)
        type_editor = TextPropertyEditor(self.component_section.content)
        type_editor.set_value(self.current_component.__class__.__name__)
        type_editor.widget.config(state='readonly')
        self.component_section.add_property("Type:", type_editor.widget)
        
        # Position X with snap-to-grid button
        x_frame = tk.Frame(self.component_section.content, bg=VSCodeTheme.BG_PRIMARY)
        x_frame.pack(fill=tk.X, pady=2)
        
        x_label = tk.Label(
            x_frame,
            text="X:",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=("Segoe UI", 9),
            anchor=tk.W,
            width=12
        )
        x_label.pack(side=tk.LEFT, padx=(0, 5))
        
        x_editor = NumberPropertyEditor(x_frame)
        x_editor.set_value(self.current_component.position[0])
        x_editor.set_on_change(lambda v: self._update_position_x(v))
        x_editor.widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.property_editors['x'] = x_editor
        
        # Position Y with snap-to-grid button
        y_frame = tk.Frame(self.component_section.content, bg=VSCodeTheme.BG_PRIMARY)
        y_frame.pack(fill=tk.X, pady=2)
        
        y_label = tk.Label(
            y_frame,
            text="Y:",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=("Segoe UI", 9),
            anchor=tk.W,
            width=12
        )
        y_label.pack(side=tk.LEFT, padx=(0, 5))
        
        y_editor = NumberPropertyEditor(y_frame)
        y_editor.set_value(self.current_component.position[1])
        y_editor.set_on_change(lambda v: self._update_position_y(v))
        y_editor.widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.property_editors['y'] = y_editor
        
        # Snap to grid button (below X/Y)
        snap_button = tk.Button(
            self.component_section.content,
            text="📐 Snap to Grid",
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_PRIMARY,
            activebackground=VSCodeTheme.BG_HOVER,
            activeforeground=VSCodeTheme.FG_PRIMARY,
            relief=tk.FLAT,
            font=("Segoe UI", 9),
            cursor="hand2",
            command=self._snap_to_grid
        )
        snap_button.pack(fill=tk.X, pady=(2, 5))
        
        # Rotation
        rotation_editor = DropdownPropertyEditor(
            self.component_section.content,
            ["0", "90", "180", "270"]
        )
        rotation_editor.set_value(self.current_component.rotation)
        rotation_editor.set_on_change(lambda v: self._update_rotation(v))
        self.component_section.add_property("Rotation:", rotation_editor.widget)
        self.property_editors['rotation'] = rotation_editor
    
    def _add_component_specific_properties(self):
        """Add component-specific properties."""
        if not self.current_component:
            return
        
        component_type = self.current_component.__class__.__name__
        
        if component_type == "Switch":
            # Switch mode property (toggle or pushbutton)
            mode_editor = DropdownPropertyEditor(
                self.properties_section.content,
                ["toggle", "pushbutton"]
            )
            current_mode = self.current_component.properties.get('mode', 'toggle')
            mode_editor.set_value(current_mode)
            mode_editor.set_on_change(lambda v: self._update_switch_mode(v))
            self.properties_section.add_property("Mode:", mode_editor.widget)
            self.property_editors['mode'] = mode_editor
        
        elif component_type == "Indicator":
            # Color property
            color_editor = DropdownPropertyEditor(
                self.properties_section.content,
                ["red", "green", "blue", "yellow", "orange", "white", "amber"]
            )
            current_color = self.current_component.properties.get('color', 'red')
            color_editor.set_value(current_color)
            color_editor.set_on_change(lambda v: self._update_indicator_color(v))
            self.properties_section.add_property("Color:", color_editor.widget)
            self.property_editors['color'] = color_editor
        
        elif component_type == "DPDTRelay":
            # Coil resistance
            resistance_editor = NumberPropertyEditor(
                self.properties_section.content,
                min_val=0.0
            )
            resistance_editor.set_value(getattr(self.current_component, 'coil_resistance', 100.0))
            resistance_editor.set_on_change(lambda v: self._update_property('coil_resistance', v))
            self.properties_section.add_property("Coil Resistance:", resistance_editor.widget)
            self.property_editors['coil_resistance'] = resistance_editor
        
        elif component_type == "VCC":
            # Voltage
            voltage_editor = NumberPropertyEditor(
                self.properties_section.content,
                min_val=0.0
            )
            voltage_editor.set_value(getattr(self.current_component, 'voltage', 5.0))
            voltage_editor.set_on_change(lambda v: self._update_property('voltage', v))
            self.properties_section.add_property("Voltage:", voltage_editor.widget)
            self.property_editors['voltage'] = voltage_editor
    
    def _add_advanced_properties(self):
        """Add advanced properties (future enhancement)."""
        pass
    
    def _update_component_id(self, new_id: str):
        """
        Update component ID with validation.
        
        Args:
            new_id: New component ID
        """
        if not self.current_component:
            return
        
        # Validate ID is not empty
        if not new_id or not new_id.strip():
            self.property_editors['id'].set_value(self.current_component.component_id)
            return
        
        # Get the parent (MainWindow) to access document
        # We need to check uniqueness across the page
        # For now, just update the ID (uniqueness validation would require page access)
        old_id = self.current_component.component_id
        
        # TODO: Add proper uniqueness validation when we have page access
        # For now, just update the ID
        self.current_component.component_id = new_id
        self._notify_change()
    
    def _snap_to_grid(self):
        """Snap component position to grid."""
        if not self.current_component:
            return
        
        # Default grid size is 20px, snap to 10px increments
        grid_snap = 10
        
        current_x, current_y = self.current_component.position
        snapped_x = round(current_x / grid_snap) * grid_snap
        snapped_y = round(current_y / grid_snap) * grid_snap
        
        self.current_component.position = (snapped_x, snapped_y)
        
        # Update editor displays
        if 'x' in self.property_editors:
            self.property_editors['x'].set_value(snapped_x)
        if 'y' in self.property_editors:
            self.property_editors['y'].set_value(snapped_y)
        
        self._notify_change()
    
    def _update_position_x(self, value: float):
        """Update component X position."""
        if self.current_component:
            self.current_component.position = (value, self.current_component.position[1])
            self._notify_change()
    
    def _update_position_y(self, value: float):
        """Update component Y position."""
        if self.current_component:
            self.current_component.position = (self.current_component.position[0], value)
            self._notify_change()
    
    def _update_rotation(self, value: str):
        """Update component rotation."""
        if self.current_component:
            self.current_component.rotation = int(value)
            self._notify_change()
    
    def _update_indicator_color(self, color: str):
        """
        Update indicator color and on/off colors.
        
        Args:
            color: Color name from COLOR_PRESETS
        """
        if not self.current_component:
            return
        
        # Import Indicator to access COLOR_PRESETS
        from components.indicator import Indicator
        
        if color in Indicator.COLOR_PRESETS:
            self.current_component.properties['color'] = color
            self.current_component.properties['on_color'] = Indicator.COLOR_PRESETS[color]['on']
            self.current_component.properties['off_color'] = Indicator.COLOR_PRESETS[color]['off']
            self._notify_change()
    
    def _update_switch_mode(self, mode: str):
        """
        Update switch mode (toggle or pushbutton).
        
        Args:
            mode: "toggle" or "pushbutton"
        """
        if not self.current_component:
            return
        
        self.current_component.properties['mode'] = mode
        self._notify_change()
    
    def _update_property(self, name: str, value: Any):
        """Update a component property."""
        if self.current_component:
            setattr(self.current_component, name, value)
            self._notify_change()
    
    def _notify_change(self):
        """Notify that a property has changed (trigger canvas redraw)."""
        # This will be connected to canvas refresh
        self.parent.event_generate('<<PropertyChanged>>')
    
    def pack(self, **kwargs):
        """Pack the panel."""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the panel."""
        self.frame.grid(**kwargs)
