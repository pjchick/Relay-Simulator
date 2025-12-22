"""
Menu Bar for Relay Simulator III

Provides the MenuBar class which manages all application menus including
File, Edit, Simulation, and View menus with keyboard shortcuts.
"""

import tkinter as tk
from typing import Callable, Optional, Dict, List


class MenuBar:
    """
    Application menu bar with all menus and keyboard shortcuts.
    
    This class manages:
    - File menu (New, Open, Save, Save As, Settings, Recent Documents, Exit)
    - Edit menu (Select All, Cut, Copy, Paste)
    - Simulation menu (Start, Stop)
    - View menu (Zoom In, Zoom Out, Reset Zoom)
    - Keyboard accelerators
    - Menu item state management (enable/disable)
    """
    
    def __init__(self, parent: tk.Tk):
        """
        Initialize the menu bar.
        
        Args:
            parent: The parent window (root Tk window)
        """
        self.parent = parent
        self.menubar = tk.Menu(parent)
        parent.config(menu=self.menubar)
        
        # Recent documents list (max 10)
        self.recent_documents: List[str] = []
        self.max_recent = 10
        
        # Menu references for state management
        self.file_menu: Optional[tk.Menu] = None
        self.edit_menu: Optional[tk.Menu] = None
        self.simulation_menu: Optional[tk.Menu] = None
        self.view_menu: Optional[tk.Menu] = None
        self.recent_menu: Optional[tk.Menu] = None
        
        # Callback references (to be set by main window)
        self.callbacks: Dict[str, Optional[Callable]] = {
            'new': None,
            'open': None,
            'save': None,
            'save_as': None,
            'settings': None,
            'exit': None,
            'select_all': None,
            'undo': None,
            'redo': None,
            'cut': None,
            'copy': None,
            'paste': None,
            'start_simulation': None,
            'stop_simulation': None,
            'zoom_in': None,
            'zoom_out': None,
            'reset_zoom': None,
            'toggle_properties': None,
        }
        
        # Create all menus
        self._create_file_menu()
        self._create_edit_menu()
        self._create_simulation_menu()
        self._create_view_menu()
        
    def _create_file_menu(self) -> None:
        """Create the File menu."""
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        
        self.file_menu.add_command(
            label="New",
            accelerator="Ctrl+N",
            command=self._on_new
        )
        
        self.file_menu.add_command(
            label="Open...",
            accelerator="Ctrl+O",
            command=self._on_open
        )
        
        self.file_menu.add_separator()
        
        self.file_menu.add_command(
            label="Save",
            accelerator="Ctrl+S",
            command=self._on_save
        )
        
        self.file_menu.add_command(
            label="Save As...",
            accelerator="Ctrl+Shift+S",
            command=self._on_save_as
        )
        
        self.file_menu.add_separator()
        
        # Recent Documents submenu
        self.recent_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Recent Documents", menu=self.recent_menu)
        self._update_recent_menu()
        
        self.file_menu.add_separator()
        
        self.file_menu.add_command(
            label="Settings...",
            command=self._on_settings
        )
        
        self.file_menu.add_separator()
        
        self.file_menu.add_command(
            label="Exit",
            accelerator="Ctrl+Q",
            command=self._on_exit
        )
        
        # Bind keyboard shortcuts
        self.parent.bind('<Control-n>', lambda e: self._on_new())
        self.parent.bind('<Control-N>', lambda e: self._on_new())
        self.parent.bind('<Control-o>', lambda e: self._on_open())
        self.parent.bind('<Control-O>', lambda e: self._on_open())
        self.parent.bind('<Control-s>', lambda e: self._on_save())
        self.parent.bind('<Control-S>', lambda e: self._on_save())
        self.parent.bind('<Control-Shift-S>', lambda e: self._on_save_as())
        self.parent.bind('<Control-Shift-s>', lambda e: self._on_save_as())
        
    def _create_edit_menu(self) -> None:
        """Create the Edit menu."""
        self.edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=self.edit_menu)

        self.edit_menu.add_command(
            label="Undo",
            accelerator="Ctrl+Z",
            command=self._on_undo
        )

        self.edit_menu.add_command(
            label="Redo",
            accelerator="Ctrl+Y",
            command=self._on_redo
        )

        self.edit_menu.add_separator()
        
        self.edit_menu.add_command(
            label="Select All",
            accelerator="Ctrl+A",
            command=self._on_select_all
        )
        
        self.edit_menu.add_separator()
        
        self.edit_menu.add_command(
            label="Cut",
            accelerator="Ctrl+X",
            command=self._on_cut
        )
        
        self.edit_menu.add_command(
            label="Copy",
            accelerator="Ctrl+C",
            command=self._on_copy
        )
        
        self.edit_menu.add_command(
            label="Paste",
            accelerator="Ctrl+V",
            command=self._on_paste
        )
        
        # Bind keyboard shortcuts
        self.parent.bind('<Control-z>', lambda e: self._on_undo() or 'break')
        self.parent.bind('<Control-Z>', lambda e: self._on_undo() or 'break')
        self.parent.bind('<Control-y>', lambda e: self._on_redo() or 'break')
        self.parent.bind('<Control-Y>', lambda e: self._on_redo() or 'break')
        self.parent.bind('<Control-a>', lambda e: self._on_select_all() or 'break')
        self.parent.bind('<Control-A>', lambda e: self._on_select_all() or 'break')
        self.parent.bind('<Control-x>', lambda e: self._on_cut() or 'break')
        self.parent.bind('<Control-X>', lambda e: self._on_cut() or 'break')
        self.parent.bind('<Control-c>', lambda e: self._on_copy() or 'break')
        self.parent.bind('<Control-C>', lambda e: self._on_copy() or 'break')
        self.parent.bind('<Control-v>', lambda e: self._on_paste() or 'break')
        self.parent.bind('<Control-V>', lambda e: self._on_paste() or 'break')
        
    def _create_simulation_menu(self) -> None:
        """Create the Simulation menu."""
        self.simulation_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Simulation", menu=self.simulation_menu)
        
        self.simulation_menu.add_command(
            label="Start Simulation",
            accelerator="F5",
            command=self._on_start_simulation
        )
        
        self.simulation_menu.add_command(
            label="Stop Simulation",
            accelerator="Shift+F5",
            command=self._on_stop_simulation
        )
        
        # Bind keyboard shortcuts
        self.parent.bind('<F5>', lambda e: self._on_start_simulation())
        self.parent.bind('<Shift-F5>', lambda e: self._on_stop_simulation())
        
    def _create_view_menu(self) -> None:
        """Create the View menu."""
        self.view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=self.view_menu)
        
        # Properties Panel toggle with checkbutton
        self.properties_visible = tk.BooleanVar(master=self.parent, value=True)
        self.view_menu.add_checkbutton(
            label="Properties Panel",
            variable=self.properties_visible,
            command=self._on_toggle_properties
        )
        
        self.view_menu.add_separator()
        
        self.view_menu.add_command(
            label="Zoom In",
            accelerator="Ctrl++",
            command=self._on_zoom_in
        )
        
        self.view_menu.add_command(
            label="Zoom Out",
            accelerator="Ctrl+-",
            command=self._on_zoom_out
        )
        
        self.view_menu.add_command(
            label="Reset Zoom",
            accelerator="Ctrl+0",
            command=self._on_reset_zoom
        )
        
        # Bind keyboard shortcuts
        # Note: Ctrl++ and Ctrl+= both zoom in (= is same key as + without shift)
        self.parent.bind('<Control-plus>', lambda e: self._on_zoom_in())
        self.parent.bind('<Control-equal>', lambda e: self._on_zoom_in())
        self.parent.bind('<Control-minus>', lambda e: self._on_zoom_out())
        self.parent.bind('<Control-Key-0>', lambda e: self._on_reset_zoom())
        
    # Callback wrappers
    def _on_new(self) -> None:
        """Handle New command."""
        if self.callbacks['new']:
            self.callbacks['new']()
            
    def _on_open(self) -> None:
        """Handle Open command."""
        if self.callbacks['open']:
            self.callbacks['open']()
            
    def _on_save(self) -> None:
        """Handle Save command."""
        if self.callbacks['save']:
            self.callbacks['save']()
            
    def _on_save_as(self) -> None:
        """Handle Save As command."""
        if self.callbacks['save_as']:
            self.callbacks['save_as']()
            
    def _on_settings(self) -> None:
        """Handle Settings command."""
        if self.callbacks['settings']:
            self.callbacks['settings']()
            
    def _on_exit(self) -> None:
        """Handle Exit command."""
        if self.callbacks['exit']:
            self.callbacks['exit']()
            
    def _on_select_all(self) -> None:
        """Handle Select All command."""
        if self.callbacks['select_all']:
            self.callbacks['select_all']()

    def _on_undo(self) -> None:
        """Handle Undo command."""
        if self.callbacks.get('undo'):
            self.callbacks['undo']()

    def _on_redo(self) -> None:
        """Handle Redo command."""
        if self.callbacks.get('redo'):
            self.callbacks['redo']()
            
    def _on_cut(self) -> None:
        """Handle Cut command."""
        if self.callbacks['cut']:
            self.callbacks['cut']()
            
    def _on_copy(self) -> None:
        """Handle Copy command."""
        if self.callbacks['copy']:
            self.callbacks['copy']()
            
    def _on_paste(self) -> None:
        """Handle Paste command."""
        if self.callbacks['paste']:
            self.callbacks['paste']()
            
    def _on_start_simulation(self) -> None:
        """Handle Start Simulation command."""
        if self.callbacks['start_simulation']:
            self.callbacks['start_simulation']()
            
    def _on_stop_simulation(self) -> None:
        """Handle Stop Simulation command."""
        if self.callbacks['stop_simulation']:
            self.callbacks['stop_simulation']()
            
    def _on_zoom_in(self) -> None:
        """Handle Zoom In command."""
        if self.callbacks['zoom_in']:
            self.callbacks['zoom_in']()
            
    def _on_zoom_out(self) -> None:
        """Handle Zoom Out command."""
        if self.callbacks['zoom_out']:
            self.callbacks['zoom_out']()
            
    def _on_reset_zoom(self) -> None:
        """Handle Reset Zoom command."""
        if self.callbacks['reset_zoom']:
            self.callbacks['reset_zoom']()
    
    def _on_toggle_properties(self) -> None:
        """Handle Toggle Properties Panel command."""
        if self.callbacks['toggle_properties']:
            self.callbacks['toggle_properties'](self.properties_visible.get())
            
    def _on_recent_document(self, filepath: str) -> None:
        """
        Handle opening a recent document.
        
        Args:
            filepath: Path to the recent document
        """
        if self.callbacks['open']:
            # Call open callback with the filepath
            # The callback should handle the actual file opening
            self.callbacks['open'](filepath)
            
    # Public API methods
    
    def set_callback(self, action: str, callback: Callable) -> None:
        """
        Set a callback for a menu action.
        
        Args:
            action: The action name (e.g., 'new', 'save', 'cut')
            callback: The callback function to execute
        """
        if action in self.callbacks:
            self.callbacks[action] = callback
            
    def add_recent_document(self, filepath: str) -> None:
        """
        Add a document to the recent documents list.
        
        Args:
            filepath: Full path to the document
        """
        # Remove if already in list
        if filepath in self.recent_documents:
            self.recent_documents.remove(filepath)
            
        # Add to front of list
        self.recent_documents.insert(0, filepath)
        
        # Trim to max size
        self.recent_documents = self.recent_documents[:self.max_recent]
        
        # Update menu
        self._update_recent_menu()
        
    def remove_recent_document(self, filepath: str) -> None:
        """
        Remove a document from the recent documents list.
        
        Args:
            filepath: Path to remove
        """
        if filepath in self.recent_documents:
            self.recent_documents.remove(filepath)
            self._update_recent_menu()
            
    def clear_recent_documents(self) -> None:
        """Clear all recent documents."""
        self.recent_documents.clear()
        self._update_recent_menu()
        
    def _update_recent_menu(self) -> None:
        """Update the Recent Documents submenu."""
        if not self.recent_menu:
            return
            
        # Clear existing items
        self.recent_menu.delete(0, tk.END)
        
        if not self.recent_documents:
            # No recent documents
            self.recent_menu.add_command(
                label="(No Recent Documents)",
                state=tk.DISABLED
            )
        else:
            # Add recent documents
            import os
            for filepath in self.recent_documents:
                # Show just the filename in the menu
                filename = os.path.basename(filepath)
                self.recent_menu.add_command(
                    label=filename,
                    command=lambda p=filepath: self._on_recent_document(p)
                )
                
            # Add separator and Clear option
            self.recent_menu.add_separator()
            self.recent_menu.add_command(
                label="Clear Recent Documents",
                command=self.clear_recent_documents
            )
            
    def set_menu_state(self, menu: str, item: str, enabled: bool) -> None:
        """
        Enable or disable a menu item.
        
        Args:
            menu: Menu name ('file', 'edit', 'simulation', 'view')
            item: Item label (e.g., 'Save', 'Copy', 'Start Simulation')
            enabled: True to enable, False to disable
        """
        menu_map = {
            'file': self.file_menu,
            'edit': self.edit_menu,
            'simulation': self.simulation_menu,
            'view': self.view_menu
        }
        
        target_menu = menu_map.get(menu.lower())
        if not target_menu:
            return
            
        # Find the menu item by label
        try:
            index = None
            for i in range(target_menu.index(tk.END) + 1):
                try:
                    if target_menu.entrycget(i, 'label') == item:
                        index = i
                        break
                except tk.TclError:
                    # Separator or other non-command item
                    continue
                    
            if index is not None:
                state = tk.NORMAL if enabled else tk.DISABLED
                target_menu.entryconfig(index, state=state)
        except tk.TclError:
            # Menu item not found
            pass
            
    def enable_edit_menu(self, has_selection: bool = False) -> None:
        """
        Update Edit menu state based on selection.
        
        Args:
            has_selection: True if there is a selection (enables Cut/Copy)
        """
        self.set_menu_state('edit', 'Cut', has_selection)
        self.set_menu_state('edit', 'Copy', has_selection)

    def enable_undo_redo(self, can_undo: bool, can_redo: bool) -> None:
        """Enable/disable Undo/Redo menu items."""
        self.set_menu_state('edit', 'Undo', can_undo)
        self.set_menu_state('edit', 'Redo', can_redo)
        
    def enable_simulation_controls(self, is_running: bool) -> None:
        """
        Update Simulation menu state based on simulation state.
        
        Args:
            is_running: True if simulation is running
        """
        # When running: disable Start, enable Stop
        # When stopped: enable Start, disable Stop
        self.set_menu_state('simulation', 'Start Simulation', not is_running)
        self.set_menu_state('simulation', 'Stop Simulation', is_running)
