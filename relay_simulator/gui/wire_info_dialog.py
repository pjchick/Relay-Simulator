"""
Wire Information Dialog

Shows all components connected to a wire (VNET) when clicked in simulation mode.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional


class WireInfoDialog:
    """
    Dialog showing all components connected to a wire's VNET.
    
    Displays:
    - Component Page
    - Component ID
    - Component Label
    - Whether the component is driving the wire
    """
    
    def __init__(self, parent: tk.Widget, wire_id: str, vnet_info: Dict[str, Any]):
        """
        Initialize wire info dialog.
        
        Args:
            parent: Parent widget
            wire_id: Wire ID that was clicked
            vnet_info: Dictionary containing VNET information with keys:
                - vnet_id: str
                - state: bool (True if HIGH, False if FLOAT)
                - components: List[Dict] with keys:
                    - page_id: str
                    - page_name: str
                    - component_id: str
                    - component_type: str
                    - label: str
                    - is_driving: bool
        """
        self.parent = parent
        self.wire_id = wire_id
        self.vnet_info = vnet_info
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Wire VNET Information - {wire_id[:8]}")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        
        # Make dialog modal
        self.dialog.grab_set()
        
        # Center dialog on parent
        self._center_dialog()
        
        # Create UI
        self._create_ui()
        
    def _center_dialog(self):
        """Center dialog on parent window."""
        self.dialog.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
        
    def _create_ui(self):
        """Create dialog UI."""
        # Header frame
        header_frame = ttk.Frame(self.dialog, padding="10")
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # VNET info
        vnet_id = self.vnet_info.get('vnet_id', 'Unknown')
        state = self.vnet_info.get('state', False)
        state_str = "HIGH" if state else "FLOAT"
        state_color = "#00ff00" if state else "#808080"
        
        ttk.Label(
            header_frame, 
            text=f"VNET: {vnet_id}",
            font=("Consolas", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        state_label = ttk.Label(
            header_frame,
            text=f"State: {state_str}",
            font=("Consolas", 10, "bold"),
            foreground=state_color
        )
        state_label.pack(side=tk.LEFT, padx=5)
        
        # Component count
        components = self.vnet_info.get('components', [])
        count_label = ttk.Label(
            header_frame,
            text=f"({len(components)} component{'s' if len(components) != 1 else ''})",
            font=("Consolas", 9)
        )
        count_label.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)
        
        # Components table frame
        table_frame = ttk.Frame(self.dialog)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview
        columns = ("page", "component_id", "type", "label", "driving")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.tree.heading("page", text="Page")
        self.tree.heading("component_id", text="Component ID")
        self.tree.heading("type", text="Type")
        self.tree.heading("label", text="Label")
        self.tree.heading("driving", text="Driving")
        
        self.tree.column("page", width=120, minwidth=80)
        self.tree.column("component_id", width=150, minwidth=100)
        self.tree.column("type", width=100, minwidth=80)
        self.tree.column("label", width=150, minwidth=80)
        self.tree.column("driving", width=80, minwidth=60)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Populate table
        self._populate_table()
        
        # Button frame
        button_frame = ttk.Frame(self.dialog, padding="10")
        button_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # Close button
        close_btn = ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy
        )
        close_btn.pack(side=tk.RIGHT)
        
        # Bind escape key to close
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())
        
    def _populate_table(self):
        """Populate the components table."""
        components = self.vnet_info.get('components', [])
        
        # Sort components: driving first, then by page name, then by component ID
        components_sorted = sorted(
            components,
            key=lambda c: (
                not c.get('is_driving', False),  # Driving components first
                c.get('page_name', ''),
                c.get('component_id', '')
            )
        )
        
        for comp in components_sorted:
            page_name = comp.get('page_name', 'Unknown')
            component_id = comp.get('component_id', 'Unknown')
            component_type = comp.get('component_type', 'Unknown')
            label = comp.get('label', '')
            is_driving = comp.get('is_driving', False)
            
            # Format driving status
            driving_str = "YES" if is_driving else "NO"
            
            # Insert row
            item_id = self.tree.insert(
                "",
                tk.END,
                values=(page_name, component_id, component_type, label, driving_str)
            )
            
            # Tag driving components for highlighting
            if is_driving:
                self.tree.item(item_id, tags=("driving",))
        
        # Configure tag colors - make driving components stand out more
        self.tree.tag_configure("driving", background="#4CAF50", foreground="#ffffff", font=("Consolas", 9, "bold"))
