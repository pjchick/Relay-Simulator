"""
Properties Panel - Right sidebar for editing component properties.

Displays properties of selected component(s) with grouped sections:
- Component section (id, type, position, rotation)
- Properties section (component-specific properties)
- Advanced section (additional settings)
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Callable, List
from gui.theme import VSCodeTheme

# Schema-driven property registry. Edit here to add/change component properties.
# Sections: Component, Label, Format, Advanced.
# Fields: section, key, label, type (text, text-readonly, dropdown, boolean, number),
#         target ('prop' for component.properties, 'attr' for attribute),
#         default, options (for dropdown), min/max (number), coerce (callable type like int/float).
BASE_PROPERTY_SCHEMA: List[Dict[str, Any]] = [
    {
        'section': 'Label',
        'key': 'label',
        'label': 'Label',
        'type': 'text',
        'target': 'prop',
        'default': ''
    },
    {
        'section': 'Label',
        'key': 'label_position',
        'label': 'Label Position',
        'type': 'dropdown',
        'options': [
            {'label': 'Top', 'value': 'top'},
            {'label': 'Bottom', 'value': 'bottom'},
            {'label': 'Left', 'value': 'left'},
            {'label': 'Right', 'value': 'right'},
        ],
        'default': 'bottom',
        'target': 'prop'
    }
]

PROPERTY_SCHEMAS: Dict[str, List[Dict[str, Any]]] = {
    'Switch': [
        {
            'section': 'Format',
            'key': 'color',
            'label': 'Color',
            'type': 'dropdown',
            'options': [
                {'label': 'Red', 'value': 'red'},
                {'label': 'Green', 'value': 'green'},
                {'label': 'Blue', 'value': 'blue'},
                {'label': 'Yellow', 'value': 'yellow'},
                {'label': 'Orange', 'value': 'orange'},
                {'label': 'White', 'value': 'white'},
                {'label': 'Amber', 'value': 'amber'},
            ],
            'default': 'red',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'mode',
            'label': 'Mode',
            'type': 'dropdown',
            'options': ['toggle', 'pushbutton'],
            'default': 'toggle',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'link_name',
            'label': 'Link Name',
            'type': 'text',
            'default': '',
            'target': 'attr',
        },
    ],
    'Clock': [
        {
            'section': 'Format',
            'key': 'color',
            'label': 'Color',
            'type': 'dropdown',
            'options': [
                {'label': 'Red', 'value': 'red'},
                {'label': 'Green', 'value': 'green'},
                {'label': 'Blue', 'value': 'blue'},
                {'label': 'Yellow', 'value': 'yellow'},
                {'label': 'Orange', 'value': 'orange'},
                {'label': 'White', 'value': 'white'},
                {'label': 'Amber', 'value': 'amber'},
                {'label': 'Gray', 'value': 'gray'},
            ],
            'default': 'red',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'frequency',
            'label': 'Frequency',
            'type': 'dropdown',
            'options': ['4Hz', '2Hz', '1Hz', '2 sec', '4 sec', '8 sec'],
            'default': '1Hz',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'enable_on_sim_start',
            'label': 'Enable on Sim Start',
            'type': 'boolean',
            'default': False,
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'link_name',
            'label': 'Link Name',
            'type': 'text',
            'default': '',
            'target': 'attr',
        },
    ],
    'Indicator': [ 
        {
            'section': 'Format',
            'key': 'color',
            'label': 'Color',
            'type': 'dropdown',
            'options': [
                {'label': 'Red', 'value': 'red'},
                {'label': 'Green', 'value': 'green'},
                {'label': 'Blue', 'value': 'blue'},
                {'label': 'Yellow', 'value': 'yellow'},
                {'label': 'Orange', 'value': 'orange'},
                {'label': 'White', 'value': 'white'},
                {'label': 'Amber', 'value': 'amber'},
            ],
            'default': 'red',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'link_name',
            'label': 'Link Name',
            'type': 'text',
            'default': '',
            'target': 'attr',
        },
    ],
    'DPDTRelay': [
        {
            'section': 'Format',
            'key': 'rotation',
            'label': 'Rotation',
            'type': 'dropdown',
            'options': ['0', '90', '180', '270'],
            'default': 0,
            'target': 'attr',
            'coerce': int,
        },
        {
            'section': 'Format',
            'key': 'flip_horizontal',
            'label': 'Flip Horizontal',
            'type': 'boolean',
            'default': False,
            'target': 'prop',
        },
                {
            'section': 'Format',
            'key': 'flip_vertical',
            'label': 'Flip Vertical',
            'type': 'boolean',
            'default': False,
            'target': 'prop',
        }
    ],
    'VCC': [
    ],
    'Link': [
        {
            'section': 'Format',
            'key': 'rotation',
            'label': 'Rotation',
            'type': 'dropdown',
            'options': ['0', '90', '180', '270'],
            'default': 0,
            'target': 'attr',
            'coerce': int,
        },
        {
            'section': 'Advanced',
            'key': 'link_name',
            'label': 'Link Name',
            'type': 'text',
            'default': '',
            'target': 'attr',
        },
    ],
    'BUS': [
        {
            'section': 'Format',
            'key': 'rotation',
            'label': 'Rotation',
            'type': 'dropdown',
            'options': ['0', '90', '180', '270'],
            'default': 0,
            'target': 'attr',
            'coerce': int,
        },
        {
            'section': 'Advanced',
            'key': 'bus_name',
            'label': 'Bus Name',
            'type': 'text',
            'default': 'Bus',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'link_ids',
            'label': "Link ID's",
            'type': 'text-readonly',
            'default': '',
            'target': 'attr',
        },
        {
            'section': 'Advanced',
            'key': 'start_pin',
            'label': 'Start Pin',
            'type': 'number',
            'default': 0,
            'min': -999999,
            'max': 999999,
            'target': 'prop',
            'coerce': int,
        },
        {
            'section': 'Advanced',
            'key': 'number_of_pins',
            'label': 'Number of Pins',
            'type': 'number',
            'default': 8,
            'min': 1,
            'max': 256,
            'target': 'prop',
            'coerce': int,
        },
        {
            'section': 'Advanced',
            'key': 'pin_spacing',
            'label': 'Pin Spacing',
            'type': 'number',
            'default': 1,
            'min': 1,
            'max': 20,
            'target': 'prop',
            'coerce': int,
        },
    ],

    'SevenSegmentDisplay': [
        {
            'section': 'Format',
            'key': 'color',
            'label': 'Color',
            'type': 'dropdown',
            'options': [
                {'label': 'Red', 'value': 'red'},
                {'label': 'Green', 'value': 'green'},
                {'label': 'Blue', 'value': 'blue'},
                {'label': 'Yellow', 'value': 'yellow'},
                {'label': 'Orange', 'value': 'orange'},
                {'label': 'White', 'value': 'white'},
                {'label': 'Amber', 'value': 'amber'},
            ],
            'default': 'green',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'bus_name',
            'label': 'Bus Name',
            'type': 'text',
            'default': 'Data',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'link_ids',
            'label': "Link ID's",
            'type': 'text-readonly',
            'default': '',
            'target': 'attr',
        },
        {
            'section': 'Advanced',
            'key': 'start_pin',
            'label': 'Start Pin',
            'type': 'number',
            'default': 0,
            'min': -999999,
            'max': 999999,
            'target': 'prop',
            'coerce': int,
        },
    ],

    'Thumbwheel': [
        {
            'section': 'Advanced',
            'key': 'bus_name',
            'label': 'Bus Name',
            'type': 'text',
            'default': 'Data',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'link_ids',
            'label': "Link ID's",
            'type': 'text-readonly',
            'default': '',
            'target': 'attr',
        },
        {
            'section': 'Advanced',
            'key': 'start_pin',
            'label': 'Start Pin',
            'type': 'number',
            'default': 0,
            'min': -999999,
            'max': 999999,
            'target': 'prop',
            'coerce': int,
        },
    ],

    'BusDisplay': [
        {
            'section': 'Format',
            'key': 'rotation',
            'label': 'Rotation',
            'type': 'dropdown',
            'options': ['0', '90', '180', '270'],
            'default': 0,
            'target': 'attr',
            'coerce': int,
        },
        {
            'section': 'Advanced',
            'key': 'bus_name',
            'label': 'Bus Name',
            'type': 'text',
            'default': 'Bus',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'link_ids',
            'label': "Link ID's",
            'type': 'text-readonly',
            'default': '',
            'target': 'attr',
        },
        {
            'section': 'Advanced',
            'key': 'start_pin',
            'label': 'Start Pin',
            'type': 'number',
            'default': 0,
            'min': -999999,
            'max': 999999,
            'target': 'prop',
            'coerce': int,
        },
        {
            'section': 'Advanced',
            'key': 'number_of_pins',
            'label': 'Number of Pins',
            'type': 'number',
            'default': 8,
            'min': 1,
            'max': 256,
            'target': 'prop',
            'coerce': int,
        },
        {
            'section': 'Advanced',
            'key': 'pin_spacing',
            'label': 'Pin Spacing',
            'type': 'number',
            'default': 1,
            'min': 1,
            'max': 20,
            'target': 'prop',
            'coerce': int,
        },
    ],

    'Memory': [
        {
            'section': 'Advanced',
            'key': 'address_bits',
            'label': 'Address Bits',
            'type': 'number',
            'default': 8,
            'min': 3,
            'max': 16,
            'target': 'prop',
            'coerce': int,
        },
        {
            'section': 'Advanced',
            'key': 'data_bits',
            'label': 'Data Bits',
            'type': 'number',
            'default': 8,
            'min': 1,
            'max': 16,
            'target': 'prop',
            'coerce': int,
        },
        {
            'section': 'Advanced',
            'key': 'address_bus_name',
            'label': 'Address Bus',
            'type': 'text',
            'default': 'ADDR',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'data_bus_name',
            'label': 'Data Bus',
            'type': 'text',
            'default': 'DATA',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'default_memory_file',
            'label': 'Default File',
            'type': 'text',
            'default': '',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'is_volatile',
            'label': 'Is Volatile',
            'type': 'boolean',
            'default': False,
            'target': 'prop',
        },
        {
            'section': 'Format',
            'key': 'visible_rows',
            'label': 'Visible Rows',
            'type': 'number',
            'default': 16,
            'min': 1,
            'max': 256,
            'target': 'prop',
            'coerce': int,
        },
    ],

    'Diode': [
        {
            'section': 'Format',
            'key': 'rotation',
            'label': 'Rotation',
            'type': 'dropdown',
            'options': ['0', '90', '180', '270'],
            'default': 0,
            'target': 'attr',
            'coerce': int,
        },
    ],
    
    'Text': [
        {
            'section': 'Format',
            'key': 'text',
            'label': 'Text Content',
            'type': 'text',
            'default': 'Text',
            'target': 'prop',
        },
        {
            'section': 'Format',
            'key': 'font_size',
            'label': 'Font Size',
            'type': 'number',
            'default': 12,
            'min': 6,
            'max': 72,
            'target': 'prop',
            'coerce': int,
        },
        {
            'section': 'Format',
            'key': 'color',
            'label': 'Text Color',
            'type': 'dropdown',
            'options': [
                {'label': 'White', 'value': '#FFFFFF'},
                {'label': 'Light Gray', 'value': '#CCCCCC'},
                {'label': 'Gray', 'value': '#888888'},
                {'label': 'Red', 'value': '#FF0000'},
                {'label': 'Green', 'value': '#00FF00'},
                {'label': 'Blue', 'value': '#0000FF'},
                {'label': 'Yellow', 'value': '#FFFF00'},
                {'label': 'Orange', 'value': '#FFA500'},
                {'label': 'Cyan', 'value': '#00FFFF'},
                {'label': 'Magenta', 'value': '#FF00FF'},
            ],
            'default': '#FFFFFF',
            'target': 'prop',
        },
        {
            'section': 'Format',
            'key': 'justify',
            'label': 'Justification',
            'type': 'dropdown',
            'options': [
                {'label': 'Left', 'value': 'left'},
                {'label': 'Right', 'value': 'right'},
            ],
            'default': 'left',
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'multiline',
            'label': 'Multi-line',
            'type': 'boolean',
            'default': False,
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'border',
            'label': 'Show Border',
            'type': 'boolean',
            'default': False,
            'target': 'prop',
        },
        {
            'section': 'Advanced',
            'key': 'width',
            'label': 'Width (px)',
            'type': 'number',
            'default': 200,
            'min': 50,
            'max': 1000,
            'target': 'prop',
            'coerce': int,
        },
        {
            'section': 'Advanced',
            'key': 'height',
            'label': 'Height (px)',
            'type': 'number',
            'default': 40,
            'min': 20,
            'max': 500,
            'target': 'prop',
            'coerce': int,
        },
    ],
}


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
    
    def add_property_row(self, label: str) -> tk.Frame:
        """Create and return a single property row frame (label left, value right)."""
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
        return row

    def add_property(self, label: str, widget: tk.Widget) -> None:
        """Add a property row with a pre-built widget (widget must be created with the row as parent)."""
        row = self.add_property_row(label)
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


class LabelPropertyEditor(PropertyEditor):
    """Read-only label property editor (non-editable)."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent)
        self.widget = tk.Label(
            parent,
            text="",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            font=("Segoe UI", 9),
            anchor=tk.W
        )

    def set_value(self, value: Any) -> None:
        self.widget.config(text=str(value) if value is not None else "")

    def get_value(self) -> str:
        return str(self.widget.cget('text'))


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
        # Options can be:
        # - list[str] (display==value)
        # - list[{'label': str, 'value': Any}] (display label, store value)
        self.options = options
        self._label_to_value: Dict[str, Any] = {}
        self._value_to_label: Dict[str, str] = {}

        display_values: List[str] = []
        for opt in options:
            if isinstance(opt, dict) and 'label' in opt and 'value' in opt:
                label = str(opt['label'])
                value = opt['value']
            else:
                label = str(opt)
                value = opt
            display_values.append(label)
            self._label_to_value[label] = value
            # Store first label for a given value
            if value not in self._value_to_label:
                self._value_to_label[value] = label

        self.var = tk.StringVar()
        self.widget = ttk.Combobox(
            parent,
            textvariable=self.var,
            values=display_values,
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
        # Prefer mapping stored value -> display label
        if value in self._value_to_label:
            self.var.set(self._value_to_label[value])
        else:
            # Fall back: if caller passes a display label
            self.var.set(str(value))
    
    def get_value(self) -> str:
        """Get dropdown value."""
        label = self.var.get()
        return self._label_to_value.get(label, label)


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
        self._active_definition_by_key: Dict[str, Dict[str, Any]] = {}
        
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
        
        # Create sections (fixed set for consistency)
        self.sections: Dict[str, PropertySection] = {
            'Component': PropertySection(self.content, "Component"),
            'Label': PropertySection(self.content, "Label"),
            'Format': PropertySection(self.content, "Format"),
            'Advanced': PropertySection(self.content, "Advanced"),
        }
        
        # Show "No selection" message initially
        self._show_no_selection()
    
    def _show_no_selection(self):
        """Show message when no component is selected."""
        for section in self.sections.values():
            section.clear()
        message = tk.Label(
            self.sections['Component'].content,
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
        for section in self.sections.values():
            section.clear()
        
        if not component:
            self._show_no_selection()
            return
        
        self._add_component_header_and_id()
        self._render_schema_properties()
    
    def _add_component_header_and_id(self):
        """Add the component header (with type) and ID field."""
        if not self.current_component:
            return

        # Update header with component type
        try:
            comp_type_name = self.current_component.__class__.__name__
            self.sections['Component'].title_label.config(
                text=f"Component — {comp_type_name}"
            )
        except Exception:
            pass

        # ID (editable with validation) — single line: label left, value right
        id_row = self.sections['Component'].add_property_row("ID:")
        id_editor = TextPropertyEditor(id_row)
        id_editor.set_value(self.current_component.component_id)
        id_editor.set_on_change(lambda v: self._update_component_id(v))
        id_editor.widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.property_editors['id'] = id_editor

    def _render_schema_properties(self):
        """Render properties based on the registry for the current component type."""
        if not self.current_component:
            return

        comp_type = self.current_component.__class__.__name__
        
        # Text components don't need label fields
        if comp_type == 'Text':
            definitions = PROPERTY_SCHEMAS.get(comp_type, [])
        else:
            definitions = BASE_PROPERTY_SCHEMA + PROPERTY_SCHEMAS.get(comp_type, [])

        self._active_definition_by_key = {
            d.get('key'): d for d in definitions if isinstance(d, dict) and d.get('key')
        }

        for definition in definitions:
            section_name = definition.get('section', 'Advanced')
            section = self.sections.get(section_name)
            if not section:
                continue

            row = section.add_property_row(f"{definition.get('label', definition['key'])}:")
            editor = self._create_editor_for_definition(row, definition)
            if not editor:
                continue

            # Pack the control into the row (label already present)
            editor.widget.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Store editor for future reference
            self.property_editors[definition['key']] = editor

        # Add custom controls for Memory component
        if comp_type == 'Memory':
            self._add_memory_actions()

    def _create_editor_for_definition(self, parent: tk.Widget, definition: Dict[str, Any]) -> Optional[PropertyEditor]:
        """Create and wire a property editor based on a schema definition."""
        ptype = definition.get('type', 'text').lower()
        key = definition['key']
        target = definition.get('target', 'prop')
        default = definition.get('default')
        coerce_fn = definition.get('coerce')
        value = self._get_property_value(key, target, default)

        # Apply optional coercion on read
        if coerce_fn:
            try:
                value = coerce_fn(value)
            except Exception:
                value = default

        if ptype == 'text-readonly':
            editor = LabelPropertyEditor(parent)
            editor.set_value(value if value is not None else '')
            return editor

        if ptype == 'text':
            editor = TextPropertyEditor(parent)
            editor.set_value(value if value is not None else '')
            editor.set_on_change(lambda v, k=key, t=target, c=coerce_fn: self._set_property_value(k, t, v, c))
            return editor

        if ptype == 'dropdown':
            options = definition.get('options', [])
            editor = DropdownPropertyEditor(parent, options)
            editor.set_value(str(value) if value is not None else '')
            editor.set_on_change(lambda v, k=key, t=target, c=coerce_fn: self._set_property_value(k, t, v, c))
            return editor

        if ptype == 'boolean':
            editor = CheckboxPropertyEditor(parent)
            editor.set_value(bool(value))
            editor.set_on_change(lambda v, k=key, t=target, c=coerce_fn: self._set_property_value(k, t, v, c))
            return editor

        if ptype == 'number':
            editor = NumberPropertyEditor(parent, min_val=definition.get('min'), max_val=definition.get('max'))
            editor.set_value(value if value is not None else 0)
            editor.set_on_change(lambda v, k=key, t=target, c=coerce_fn: self._set_property_value(k, t, v, c))
            return editor

        # Fallback to text editor
        editor = TextPropertyEditor(parent)
        editor.set_value(value if value is not None else '')
        editor.set_on_change(lambda v, k=key, t=target, c=coerce_fn: self._set_property_value(k, t, v, c))
        return editor
    
    def _get_property_value(self, key: str, target: str, default: Any):
        if not self.current_component:
            return default
        if target == 'attr':
            return getattr(self.current_component, key, default)
        # default to properties dict
        props = getattr(self.current_component, 'properties', None)
        if isinstance(props, dict):
            return props.get(key, default)
        return default

    def _set_property_value(self, key: str, target: str, value: Any, coerce_fn=None):
        if not self.current_component:
            return

        # Allow the main window to snapshot state before a mutation.
        try:
            self.parent.event_generate('<<UndoCheckpoint>>')
        except Exception:
            pass

        if coerce_fn:
            try:
                value = coerce_fn(value)
            except Exception:
                pass

        # Normalize common string enums to match component expectations
        if isinstance(value, str) and key in ('color', 'label_position'):
            value = value.strip().lower()

        if target == 'attr':
            setattr(self.current_component, key, value)
        else:
            if not hasattr(self.current_component, 'properties') or not isinstance(self.current_component.properties, dict):
                self.current_component.properties = {}

            # Special-case: changing a component's "color" should also update
            # its derived on/off shades when the component supports presets.
            if key == 'color' and hasattr(self.current_component, 'set_color') and callable(getattr(self.current_component, 'set_color')):
                try:
                    self.current_component.set_color(str(value))
                except Exception:
                    self.current_component.properties[key] = value
            else:
                self.current_component.properties[key] = value

        # Optional hook for components that need to respond to property changes
        # (e.g., dynamic pin layouts).
        if hasattr(self.current_component, 'on_property_changed') and callable(getattr(self.current_component, 'on_property_changed')):
            try:
                self.current_component.on_property_changed(key)
            except Exception:
                pass

        self._refresh_readonly_fields()

        self._notify_change()

    def _refresh_readonly_fields(self) -> None:
        """Recompute and refresh any read-only fields (e.g. computed attrs like BUS link_ids)."""
        if not self.current_component:
            return

        for key, definition in self._active_definition_by_key.items():
            ptype = str(definition.get('type', 'text')).lower()
            if ptype != 'text-readonly':
                continue

            editor = self.property_editors.get(key)
            if not editor:
                continue

            target = definition.get('target', 'prop')
            default = definition.get('default')
            coerce_fn = definition.get('coerce')
            value = self._get_property_value(key, target, default)
            if coerce_fn:
                try:
                    value = coerce_fn(value)
                except Exception:
                    value = default

            editor.set_value(value if value is not None else '')
    
    def _update_component_id(self, new_id: str):
        """
        Update component ID with validation.
        
        Args:
            new_id: New component ID
        """
        if not self.current_component:
            return

        # Allow the main window to snapshot state before a mutation.
        try:
            self.parent.event_generate('<<UndoCheckpoint>>')
        except Exception:
            pass
        
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
    
    def _notify_change(self):
        """Notify that a property has changed (trigger canvas redraw)."""
        # This will be connected to canvas refresh
        self.parent.event_generate('<<PropertyChanged>>')

    def _add_memory_actions(self):
        """Add Load/Save/Clear buttons for Memory component."""
        if not self.current_component or self.current_component.__class__.__name__ != 'Memory':
            return

        section = self.sections.get('Advanced')
        if not section:
            return

        # Add button row
        button_frame = tk.Frame(section.content, bg=VSCodeTheme.BG_PRIMARY)
        button_frame.pack(fill=tk.X, pady=5, padx=5)

        # Load button
        load_btn = tk.Button(
            button_frame,
            text="Load File",
            command=self._memory_load_file,
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_PRIMARY,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor='hand2'
        )
        load_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Save button
        save_btn = tk.Button(
            button_frame,
            text="Save File",
            command=self._memory_save_file,
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_PRIMARY,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor='hand2'
        )
        save_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Clear button
        clear_btn = tk.Button(
            button_frame,
            text="Clear",
            command=self._memory_clear,
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_PRIMARY,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor='hand2'
        )
        clear_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

    def _memory_load_file(self):
        """Load memory contents from file."""
        if not self.current_component or self.current_component.__class__.__name__ != 'Memory':
            return

        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="Load Memory File",
            filetypes=[
                ("Memory files", "*.mem"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if filepath:
            # Snapshot before mutating the memory contents.
            try:
                self.parent.event_generate('<<UndoCheckpoint>>')
            except Exception:
                pass
            if self.current_component.load_from_file(filepath):
                self._notify_change()
                print(f"Memory loaded from {filepath}")
            else:
                print(f"Failed to load memory from {filepath}")

    def _memory_save_file(self):
        """Save memory contents to file."""
        if not self.current_component or self.current_component.__class__.__name__ != 'Memory':
            return

        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            title="Save Memory File",
            defaultextension=".mem",
            filetypes=[
                ("Memory files", "*.mem"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if filepath:
            if self.current_component.save_to_file(filepath):
                print(f"Memory saved to {filepath}")
            else:
                print(f"Failed to save memory to {filepath}")

    def _memory_clear(self):
        """Clear memory contents."""
        if not self.current_component or self.current_component.__class__.__name__ != 'Memory':
            return

        from tkinter import messagebox
        if messagebox.askyesno("Clear Memory", "Clear all memory contents?"):
            # Snapshot before mutating the memory contents.
            try:
                self.parent.event_generate('<<UndoCheckpoint>>')
            except Exception:
                pass
            self.current_component.clear_memory()
            self._notify_change()
            print("Memory cleared")
    
    def pack(self, **kwargs):
        """Pack the panel."""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the panel."""
        self.frame.grid(**kwargs)
