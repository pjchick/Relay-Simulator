"""
Main Window for Relay Simulator III

Provides the MainWindow class which manages the primary application window,
including initialization, lifecycle, and basic window operations.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional
from pathlib import Path

from gui.theme import VSCodeTheme, apply_theme
from gui.menu_bar import MenuBar
from gui.settings import Settings
from gui.settings_dialog import show_settings_dialog
from gui.file_tabs import FileTabBar
from gui.page_tabs import PageTabBar
from gui.canvas import DesignCanvas
from gui.toolbox import ToolboxPanel
from gui.properties_panel import PropertiesPanel
from core.document import Document
from fileio.document_loader import DocumentLoader


class MainWindow:
    """
    Main application window for Relay Simulator III.
    
    This class manages the primary application window, including:
    - Window initialization and configuration
    - Theme application
    - Menu bar placeholder
    - Status bar placeholder
    - Window lifecycle (open, close, exit confirmation)
    
    The window serves as the container for all other GUI components
    (canvas, toolbars, panels, etc.).
    """
    
    def __init__(self):
        """Initialize the main window."""
        # Create root window
        self.root = tk.Tk()
        self.root.title("Relay Simulator III")
        
        # Set window size and position
        self.default_width = 1280
        self.default_height = 720
        self._center_window()
        
        # Apply VS Code dark theme
        apply_theme(self.root)
        
        # Load settings
        self.settings = Settings()
        
        # Initialize document loader
        self.document_loader = DocumentLoader()
        
        # Track if there are unsaved changes
        self.has_unsaved_changes = False
        
        # Track simulation state
        self.is_simulation_running = False
        
        # Create menu bar (before setting up window close handler so Exit callback works)
        self.menu_bar = MenuBar(self.root)
        self._setup_menu_callbacks()
        
        # Sync recent documents from settings to menu
        for filepath in self.settings.get_recent_documents():
            self.menu_bar.add_recent_document(filepath)
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Create UI components
        self._create_widgets()
        
    def _center_window(self) -> None:
        """Center the window on the screen."""
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - self.default_width) // 2
        y = (screen_height - self.default_height) // 2
        
        # Set geometry
        self.root.geometry(f"{self.default_width}x{self.default_height}+{x}+{y}")
        
    def _setup_menu_callbacks(self) -> None:
        """Setup menu bar callbacks."""
        # File menu
        self.menu_bar.set_callback('new', self._menu_new)
        self.menu_bar.set_callback('open', self._menu_open)
        self.menu_bar.set_callback('save', self._menu_save)
        self.menu_bar.set_callback('save_as', self._menu_save_as)
        self.menu_bar.set_callback('settings', self._menu_settings)
        self.menu_bar.set_callback('exit', self._on_closing)
        
        # Edit menu
        self.menu_bar.set_callback('select_all', self._menu_select_all)
        self.menu_bar.set_callback('cut', self._menu_cut)
        self.menu_bar.set_callback('copy', self._menu_copy)
        self.menu_bar.set_callback('paste', self._menu_paste)
        
        # Simulation menu
        self.menu_bar.set_callback('start_simulation', self._menu_start_simulation)
        self.menu_bar.set_callback('stop_simulation', self._menu_stop_simulation)
        
        # View menu
        self.menu_bar.set_callback('zoom_in', self._menu_zoom_in)
        self.menu_bar.set_callback('zoom_out', self._menu_zoom_out)
        self.menu_bar.set_callback('reset_zoom', self._menu_reset_zoom)
        
        # Initialize menu states
        self.menu_bar.enable_edit_menu(has_selection=False)
        self.menu_bar.enable_simulation_controls(is_running=False)
        
    # Menu callback implementations
    
    def _menu_new(self) -> None:
        """Handle File > New."""
        # Create new untitled document
        new_doc = Document()
        new_doc.create_page("Page 1")
        tab_id = self.file_tabs.add_untitled_tab(new_doc)
        self.file_tabs.set_active_tab(tab_id)
        self.set_status("New document created")
        
    def _menu_open(self, filepath: Optional[str] = None) -> None:
        """
        Handle File > Open or opening a recent document.
        
        Args:
            filepath: Optional path to open (from recent documents)
        """
        # If no filepath provided, show file dialog
        if not filepath:
            filepath = filedialog.askopenfilename(
                parent=self.root,
                title="Open Relay Simulator File",
                filetypes=[("Relay Simulator Files", "*.rsim"), ("All Files", "*.*")],
                defaultextension=".rsim"
            )
            
            if not filepath:  # User cancelled
                return
        
        # Check if file is already open
        existing_tab = self.file_tabs.get_tab_by_filepath(filepath)
        if existing_tab:
            self.file_tabs.set_active_tab(existing_tab.tab_id)
            self.set_status(f"Switched to {Path(filepath).name}")
            return
        
        try:
            # Load document
            document = self.document_loader.load_from_file(filepath)
            
            # Create new tab
            filename = Path(filepath).name
            tab_id = self.file_tabs.add_tab(filename, filepath, document)
            self.file_tabs.set_active_tab(tab_id)
            
            # Restore canvas state from first page
            pages = document.get_all_pages()
            if pages:
                active_page = pages[0]
                self.design_canvas.restore_canvas_state(
                    active_page.canvas_x,
                    active_page.canvas_y,
                    active_page.canvas_zoom
                )
            
            # Add to recent documents
            self.settings.add_recent_document(filepath)
            self.menu_bar.add_recent_document(filepath)
            self.settings.save()
            
            self.set_status(f"Opened {filename}")
            
        except FileNotFoundError:
            messagebox.showerror(
                "File Not Found",
                f"File not found: {filepath}",
                parent=self.root
            )
            self.set_status("Failed to open file")
        except Exception as e:
            messagebox.showerror(
                "Error Opening File",
                f"Failed to open file: {str(e)}",
                parent=self.root
            )
            self.set_status("Failed to open file")
        
    def _menu_save(self) -> None:
        """Handle File > Save."""
        active_tab = self.file_tabs.get_active_tab()
        if not active_tab:
            return
        
        # If no filepath, do Save As
        if not active_tab.filepath:
            self._menu_save_as()
            return
        
        try:
            # Save current canvas state to document's active page
            if active_tab.document:
                active_page_id = self.page_tabs.get_active_page_id()
                if active_page_id:
                    active_page = active_tab.document.get_page(active_page_id)
                    if active_page:
                        canvas_x, canvas_y, zoom = self.design_canvas.save_canvas_state()
                        active_page.canvas_x = canvas_x
                        active_page.canvas_y = canvas_y
                        active_page.canvas_zoom = zoom
            
            # Save document
            self.document_loader.save_to_file(active_tab.document, active_tab.filepath)
            
            # Mark as not modified
            self.file_tabs.set_tab_modified(active_tab.tab_id, False)
            
            # Add to recent documents
            self.settings.add_recent_document(active_tab.filepath)
            self.menu_bar.add_recent_document(active_tab.filepath)
            self.settings.save()
            
            self.set_status(f"Saved {active_tab.filename}")
            
        except Exception as e:
            messagebox.showerror(
                "Error Saving File",
                f"Failed to save file: {str(e)}",
                parent=self.root
            )
            self.set_status("Failed to save file")
        
    def _menu_save_as(self) -> None:
        """Handle File > Save As."""
        active_tab = self.file_tabs.get_active_tab()
        if not active_tab:
            return
        
        # Show save dialog
        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save Relay Simulator File As",
            filetypes=[("Relay Simulator Files", "*.rsim"), ("All Files", "*.*")],
            defaultextension=".rsim",
            initialfile=active_tab.filename if not active_tab.filepath else Path(active_tab.filepath).name
        )
        
        if not filepath:  # User cancelled
            return
        
        try:
            # Save current canvas state to document's active page
            if active_tab.document:
                active_page_id = self.page_tabs.get_active_page_id()
                if active_page_id:
                    active_page = active_tab.document.get_page(active_page_id)
                    if active_page:
                        canvas_x, canvas_y, zoom = self.design_canvas.save_canvas_state()
                        active_page.canvas_x = canvas_x
                        active_page.canvas_y = canvas_y
                        active_page.canvas_zoom = zoom
            
            # Save document to new filepath
            self.document_loader.save_to_file(active_tab.document, filepath)
            
            # Update tab with new filepath
            filename = Path(filepath).name
            self.file_tabs.set_tab_filepath(active_tab.tab_id, filepath, filename)
            self.file_tabs.set_tab_modified(active_tab.tab_id, False)
            
            # Add to recent documents
            self.settings.add_recent_document(filepath)
            self.menu_bar.add_recent_document(filepath)
            self.settings.save()
            
            self.set_status(f"Saved as {filename}")
            
        except Exception as e:
            messagebox.showerror(
                "Error Saving File",
                f"Failed to save file: {str(e)}",
                parent=self.root
            )
            self.set_status("Failed to save file")
        
    def _menu_settings(self) -> None:
        """Handle File > Settings."""
        # Show settings dialog
        if show_settings_dialog(self.root, self.settings):
            self.set_status("Settings saved")
        else:
            self.set_status("Settings cancelled")
        
    def _menu_select_all(self) -> None:
        """Handle Edit > Select All."""
        # TODO: Implement in Phase 13.1
        self.set_status("Select All (not yet implemented)")
        
    def _menu_cut(self) -> None:
        """Handle Edit > Cut."""
        # TODO: Implement in Phase 13.3
        self.set_status("Cut (not yet implemented)")
        
    def _menu_copy(self) -> None:
        """Handle Edit > Copy."""
        # TODO: Implement in Phase 13.3
        self.set_status("Copy (not yet implemented)")
        
    def _menu_paste(self) -> None:
        """Handle Edit > Paste."""
        # TODO: Implement in Phase 13.3
        self.set_status("Paste (not yet implemented)")
        
    def _menu_start_simulation(self) -> None:
        """Handle Simulation > Start."""
        # TODO: Implement in Phase 15.2
        self.is_simulation_running = True
        self.file_tabs.set_simulation_running(True)
        self.menu_bar.enable_simulation_controls(is_running=True)
        self.set_status("Start Simulation (not yet implemented)")
        
    def _menu_stop_simulation(self) -> None:
        """Handle Simulation > Stop."""
        # TODO: Implement in Phase 15.2
        self.is_simulation_running = False
        self.file_tabs.set_simulation_running(False)
        self.menu_bar.enable_simulation_controls(is_running=False)
        self.set_status("Stop Simulation (not yet implemented)")
        
    def _menu_zoom_in(self) -> None:
        """Handle View > Zoom In."""
        self.design_canvas.zoom_in()
        zoom_pct = int(self.design_canvas.get_zoom_level() * 100)
        self.set_status(f"Zoom: {zoom_pct}%")
        
    def _menu_zoom_out(self) -> None:
        """Handle View > Zoom Out."""
        self.design_canvas.zoom_out()
        zoom_pct = int(self.design_canvas.get_zoom_level() * 100)
        self.set_status(f"Zoom: {zoom_pct}%")
        
    def _menu_reset_zoom(self) -> None:
        """Handle View > Reset Zoom."""
        self.design_canvas.reset_zoom()
        self.set_status("Zoom: 100%")
        
    def _create_widgets(self) -> None:
        """Create the main UI components."""
        # Create main container frame
        self.main_frame = tk.Frame(
            self.root,
            bg=VSCodeTheme.BG_PRIMARY
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status bar (create first so callbacks can use set_status)
        self.status_bar = tk.Frame(
            self.main_frame,
            bg=VSCodeTheme.BG_SECONDARY,
            height=VSCodeTheme.STATUSBAR_HEIGHT
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(
            self.status_bar,
            text="Ready",
            font=VSCodeTheme.get_font('small'),
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_SECONDARY,
            anchor=tk.W,
            padx=VSCodeTheme.PADDING_MEDIUM
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X)
        
        # File tab bar
        self.file_tabs = FileTabBar(self.main_frame)
        self.file_tabs.on_tab_switch = self._on_tab_switch
        self.file_tabs.on_tab_close = self._on_tab_close
        self.file_tabs.on_tab_modified = self._on_tab_modified
        
        # Page tab bar (for multi-page navigation within a document)
        self.page_tabs = PageTabBar(self.main_frame)
        self.page_tabs.on_page_switch = self._on_page_switch
        self.page_tabs.on_page_added = self._on_page_added
        self.page_tabs.on_page_deleted = self._on_page_deleted
        self.page_tabs.on_page_renamed = self._on_page_renamed
        self.page_tabs.pack(side=tk.TOP, fill=tk.X)
        
        # Content area (for canvas, toolbars, etc.)
        self.content_frame = tk.Frame(
            self.main_frame,
            bg=VSCodeTheme.BG_PRIMARY
        )
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Component toolbox (left sidebar)
        self.toolbox = ToolboxPanel(
            self.content_frame,
            on_component_select=self._on_component_selected
        )
        self.toolbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1))
        
        # Create design canvas
        canvas_width = self.settings.get('default_canvas_width', 3000)
        canvas_height = self.settings.get('default_canvas_height', 3000)
        grid_size = self.settings.get_grid_size()
        
        self.design_canvas = DesignCanvas(
            self.content_frame,
            width=canvas_width,
            height=canvas_height,
            grid_size=grid_size
        )
        self.design_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Properties panel (right sidebar)
        self.properties_panel = PropertiesPanel(self.content_frame)
        self.properties_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(1, 0))
        
        # Bind property change events to update canvas
        self.content_frame.bind('<<PropertyChanged>>', self._on_property_changed)
        
        # Track component placement mode
        self.placement_component = None  # Component type being placed
        self.placement_rotation = 0  # Rotation for placement (0, 90, 180, 270)
        
        # Track wire drawing mode
        self.wire_mode = False  # True when wire tool is active
        self.wire_start_tab = None  # Tab ID where wire starts
        self.wire_preview_line = None  # Canvas item for wire preview
        
        # Bind canvas click for component placement and wire drawing
        self.design_canvas.canvas.bind('<Button-1>', self._on_canvas_click)
        self.design_canvas.canvas.bind('<Motion>', self._on_canvas_motion)
        
        # Create initial untitled document (after canvas is created)
        initial_doc = Document()
        initial_doc.create_page("Page 1")
        self.file_tabs.add_untitled_tab(initial_doc)
        
    def _on_closing(self) -> None:
        """
        Handle window close event.
        
        If there are unsaved changes, prompts the user for confirmation
        before closing.
        """
        if self.has_unsaved_changes:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                parent=self.root
            )
            
            if response is None:  # Cancel
                return
            elif response:  # Yes - save all modified tabs
                # Save all modified tabs
                for tab in self.file_tabs.get_all_tabs():
                    if tab.is_modified:
                        # Temporarily set as active to save
                        old_active = self.file_tabs.active_tab_id
                        self.file_tabs.active_tab_id = tab.tab_id
                        self._menu_save()
                        self.file_tabs.active_tab_id = old_active
                        
                        # If save was cancelled, don't close
                        if tab.is_modified:
                            return
                
                self.quit()
            else:  # No - don't save
                self.quit()
        else:
            self.quit()
            
    def run(self) -> None:
        """Start the main event loop."""
        self.root.mainloop()
        
    def quit(self) -> None:
        """Quit the application."""
        self.root.quit()
        self.root.destroy()
        
    def set_unsaved_changes(self, has_changes: bool) -> None:
        """
        Set the unsaved changes flag.
        
        Args:
            has_changes: True if there are unsaved changes, False otherwise
        """
        self.has_unsaved_changes = has_changes
        
        # Update window title to show unsaved changes
        base_title = "Relay Simulator III"
        if has_changes:
            self.root.title(f"*{base_title}")
        else:
            self.root.title(base_title)
            
    def set_status(self, message: str) -> None:
        """
        Update the status bar message.
        
        Args:
            message: The status message to display
        """
        self.status_label.config(text=message)
    
    # File tab callbacks
    
    def _on_tab_switch(self, tab_id: str) -> None:
        """
        Handle file tab switch event.
        
        Args:
            tab_id: ID of newly active tab
        """
        tab = self.file_tabs.get_tab(tab_id)
        if tab and tab.document:
            # Save canvas state to previous document's active page
            old_tab = self.file_tabs.get_tab(self._last_active_tab_id) if hasattr(self, '_last_active_tab_id') and self._last_active_tab_id else None
            if old_tab and old_tab.document and self.page_tabs.get_active_page_id():
                active_page = old_tab.document.get_page(self.page_tabs.get_active_page_id())
                if active_page:
                    canvas_x, canvas_y, zoom = self.design_canvas.save_canvas_state()
                    active_page.canvas_x = canvas_x
                    active_page.canvas_y = canvas_y
                    active_page.canvas_zoom = zoom
            
            # Update page tabs for new document
            self.page_tabs.set_document(tab.document)
            
            # Restore canvas state from new document's active page
            active_page_id = self.page_tabs.get_active_page_id()
            if active_page_id:
                active_page = tab.document.get_page(active_page_id)
                if active_page:
                    # Set page on canvas (will render components)
                    self.design_canvas.set_page(active_page)
                    
                    # Restore canvas state
                    self.design_canvas.restore_canvas_state(
                        active_page.canvas_x,
                        active_page.canvas_y,
                        active_page.canvas_zoom
                    )
            
            # Update window title
            self._update_window_title()
            self.set_status(f"Switched to {tab.filename}")
            
            # Track last active tab for next switch
            self._last_active_tab_id = tab_id
    
    def _on_tab_close(self, tab_id: str) -> bool:
        """
        Handle tab close event.
        
        Args:
            tab_id: ID of tab to close
            
        Returns:
            bool: True if can close, False if user cancelled
        """
        tab = self.file_tabs.get_tab(tab_id)
        if not tab:
            return True
        
        # Check for unsaved changes
        if tab.is_modified:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"Save changes to {tab.filename} before closing?",
                parent=self.root
            )
            
            if response is None:  # Cancel
                return False
            elif response:  # Yes - save
                # Temporarily set as active to save
                old_active = self.file_tabs.active_tab_id
                self.file_tabs.active_tab_id = tab_id
                self._menu_save()
                self.file_tabs.active_tab_id = old_active
                
                # Check if save was successful (tab should no longer be modified)
                if tab.is_modified:
                    return False  # Save failed or was cancelled
            # else: No - don't save, allow close
        
        # Update window title after close
        self.root.after(10, self._update_window_title)
        return True
    
    def _on_tab_modified(self, tab_id: str, modified: bool) -> None:
        """
        Handle tab modified state change.
        
        Args:
            tab_id: Tab ID
            modified: Modified state
        """
        # Update window title and unsaved changes flag
        self._update_window_title()
    
    # Page tab callbacks
    
    def _on_page_switch(self, page_id: str) -> None:
        """
        Handle page switch event within current document.
        
        Args:
            page_id: ID of newly active page
        """
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
            
        # Get the page
        page = tab.document.get_page(page_id)
        if not page:
            return
            
        # Set page on canvas (will render components)
        self.design_canvas.set_page(page)
        
        # Restore canvas state for this page
        self.design_canvas.restore_canvas_state(
            page.canvas_x,
            page.canvas_y,
            page.canvas_zoom
        )
        
        self.set_status(f"Switched to page: {page.name}")
    
    def _on_page_added(self, page_id: str) -> None:
        """
        Handle page added event.
        
        Args:
            page_id: ID of newly added page
        """
        tab = self.file_tabs.get_active_tab()
        if tab:
            # Mark document as modified
            self.file_tabs.set_tab_modified(tab.tab_id, True)
            self.set_status("New page added")
    
    def _on_page_deleted(self, page_id: str) -> None:
        """
        Handle page deleted event.
        
        Args:
            page_id: ID of deleted page
        """
        tab = self.file_tabs.get_active_tab()
        if tab:
            # Mark document as modified
            self.file_tabs.set_tab_modified(tab.tab_id, True)
            self.set_status("Page deleted")
    
    def _on_page_renamed(self, page_id: str, new_name: str) -> None:
        """
        Handle page renamed event.
        
        Args:
            page_id: ID of renamed page
            new_name: New name of the page
        """
        tab = self.file_tabs.get_active_tab()
        if tab:
            # Mark document as modified
            self.file_tabs.set_tab_modified(tab.tab_id, True)
            self.set_status(f"Page renamed to: {new_name}")
    
    def _update_window_title(self) -> None:
        """Update window title with active document name and modified indicator."""
        active_tab = self.file_tabs.get_active_tab()
        
        if active_tab:
            base_title = f"{active_tab.filename} - Relay Simulator III"
            if active_tab.is_modified:
                self.root.title(f"*{base_title}")
            else:
                self.root.title(base_title)
            
            # Update global unsaved changes flag
            self.has_unsaved_changes = self.file_tabs.has_unsaved_changes()
        else:
            self.root.title("Relay Simulator III")
            self.has_unsaved_changes = False
    
    # === Component Placement ===
    
    def _on_component_selected(self, component_type: Optional[str]) -> None:
        """
        Handle component/tool selection from toolbox.
        
        Args:
            component_type: Type selected (None = Select, 'Wire' = Wire tool, or component type)
        """
        # Reset modes
        self.placement_component = None
        self.wire_mode = False
        self.placement_rotation = 0
        self._clear_wire_preview()
        
        if component_type == 'Wire':
            # Wire drawing mode
            self.wire_mode = True
            self.set_status("Click on a tab to start drawing a wire")
            self.design_canvas.canvas.config(cursor="crosshair")
        elif component_type:
            # Component placement mode
            self.placement_component = component_type
            self.set_status(f"Click on canvas to place {component_type}. Press R to rotate.")
            self.design_canvas.canvas.config(cursor="crosshair")
        else:
            # Select mode
            self.set_status("Select tool active")
            self.design_canvas.canvas.config(cursor="")
    
    def _on_canvas_click(self, event) -> None:
        """
        Handle canvas click for component placement and wire drawing.
        
        Args:
            event: Click event
        """
        # Handle wire drawing mode
        if self.wire_mode:
            self._handle_wire_click(event)
            return
        
        # Handle component placement mode
        if self.placement_component:
            self._handle_component_placement(event)
            return
        
        # Handle component selection (when not in placement or wire mode)
        self._handle_component_selection(event)
    
    def _handle_component_placement(self, event) -> None:
        """
        Handle component placement on canvas.
        
        Args:
            event: Click event
        """
        # Get active page
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return
        
        # Convert screen coordinates to canvas coordinates
        canvas_x = self.design_canvas.canvas.canvasx(event.x)
        canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Snap to grid
        grid_size = self.settings.get_grid_size()
        snap_size = grid_size // 2  # Snap to half-grid (10px for 20px grid)
        snapped_x = round(canvas_x / snap_size) * snap_size
        snapped_y = round(canvas_y / snap_size) * snap_size
        
        # Create component
        component_id = tab.document.id_manager.generate_id()
        
        # Import component classes
        from components.switch import Switch
        from components.indicator import Indicator
        from components.dpdt_relay import DPDTRelay
        from components.vcc import VCC
        
        # Create component instance based on type
        component = None
        if self.placement_component == 'Switch':
            component = Switch(component_id, page.page_id)
        elif self.placement_component == 'Indicator':
            component = Indicator(component_id, page.page_id)
        elif self.placement_component == 'DPDTRelay':
            component = DPDTRelay(component_id, page.page_id)
        elif self.placement_component == 'VCC':
            component = VCC(component_id, page.page_id)
        
        if component:
            # Set position and rotation
            component.position = (snapped_x, snapped_y)
            component.rotation = self.placement_rotation
            
            # Add to page
            page.add_component(component)
            
            # Mark document as modified
            self.file_tabs.set_tab_modified(tab.tab_id, True)
            
            # Re-render components on canvas
            self.design_canvas.set_page(page)
            
            # Return to select tool
            self.toolbox.select_tool()
            
            self.set_status(f"{self.placement_component} placed at ({int(snapped_x)}, {int(snapped_y)})")
    
    # === Wire Drawing ===
    
    def _on_canvas_motion(self, event) -> None:
        """
        Handle mouse motion for wire preview.
        
        Args:
            event: Motion event
        """
        if not self.wire_mode or not self.wire_start_tab:
            return
        
        # Get canvas coordinates
        canvas_x = self.design_canvas.canvas.canvasx(event.x)
        canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Update wire preview line
        if self.wire_preview_line:
            self.design_canvas.canvas.delete(self.wire_preview_line)
        
        # Get start position from tab
        start_pos = self._get_tab_canvas_position(self.wire_start_tab)
        if start_pos:
            self.wire_preview_line = self.design_canvas.canvas.create_line(
                start_pos[0], start_pos[1],
                canvas_x, canvas_y,
                fill=VSCodeTheme.WIRE_SELECTED,
                width=2,
                dash=(5, 5)  # Dashed line for preview
            )
    
    def _handle_wire_click(self, event) -> None:
        """
        Handle click in wire drawing mode.
        
        Args:
            event: Click event
        """
        # Get canvas coordinates
        canvas_x = self.design_canvas.canvas.canvasx(event.x)
        canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Find tab at click location
        tab_id = self._find_tab_at_position(canvas_x, canvas_y)
        
        if not tab_id:
            # Clicked on empty canvas - cancel wire
            if self.wire_start_tab:
                self._clear_wire_preview()
                self.wire_start_tab = None
                self.set_status("Wire cancelled. Click on a tab to start a new wire.")
            return
        
        if not self.wire_start_tab:
            # First click - start wire
            self.wire_start_tab = tab_id
            self.set_status(f"Wire started. Click on another tab to complete the wire.")
        else:
            # Second click - complete wire
            if tab_id == self.wire_start_tab:
                self.set_status("Cannot connect a tab to itself. Click on a different tab.")
                return
            
            self._create_wire(self.wire_start_tab, tab_id)
            self._clear_wire_preview()
            self.wire_start_tab = None
            self.set_status("Wire created. Click on a tab to start another wire.")
    
    def _find_tab_at_position(self, x: float, y: float) -> Optional[str]:
        """
        Find tab at the given canvas position.
        
        Args:
            x: Canvas X coordinate
            y: Canvas Y coordinate
            
        Returns:
            Tab ID if found, None otherwise
        """
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return None
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return None
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return None
        
        # Check all components and their tabs
        for component in page.components.values():
            comp_x, comp_y = component.position
            for pin in component.pins.values():
                for tab_obj in pin.tabs.values():
                    tab_dx, tab_dy = tab_obj.relative_position
                    tab_x = comp_x + tab_dx
                    tab_y = comp_y + tab_dy
                    
                    # Check if click is within tab area (use TAB_SIZE for hit detection)
                    hit_radius = VSCodeTheme.TAB_SIZE * 3  # More generous click area
                    if abs(x - tab_x) <= hit_radius and abs(y - tab_y) <= hit_radius:
                        return tab_obj.tab_id
        
        return None
    
    def _get_tab_canvas_position(self, tab_id: str) -> Optional[Tuple[float, float]]:
        """
        Get canvas position of a tab.
        
        Args:
            tab_id: Tab ID
            
        Returns:
            (x, y) position or None if not found
        """
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return None
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return None
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return None
        
        # Parse tab_id to find component
        # Format: {component_id}.{pin_name}.{tab_name}
        # Example: 7ab1d562.pin1.tab3
        parts = tab_id.split('.')
        if len(parts) < 3:
            return None
        
        component_id = parts[0]
        component = page.components.get(component_id)
        if not component:
            return None
        
        pin_name = parts[1]
        pin_id = f"{component_id}.{pin_name}"
        pin = component.pins.get(pin_id)
        if not pin:
            return None
        
        tab_obj = pin.tabs.get(tab_id)
        if not tab_obj:
            return None
        
        comp_x, comp_y = component.position
        tab_dx, tab_dy = tab_obj.relative_position
        return (comp_x + tab_dx, comp_y + tab_dy)
    
    def _create_wire(self, start_tab_id: str, end_tab_id: str) -> None:
        """
        Create a wire between two tabs.
        
        Args:
            start_tab_id: Starting tab ID
            end_tab_id: Ending tab ID
        """
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return
        
        # Import Wire class
        from core.wire import Wire
        
        # Generate wire ID
        wire_id = tab.document.id_manager.generate_id()
        
        # Create wire
        wire = Wire(wire_id, start_tab_id, end_tab_id)
        
        # Add to page
        page.add_wire(wire)
        
        # Mark document as modified
        self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        # Re-render page (including new wire)
        self.design_canvas.set_page(page)
    
    def _on_property_changed(self, event=None) -> None:
        """
        Handle property changes from properties panel.
        
        Re-renders the current page to reflect property changes.
        """
        # Get current page
        active_tab = self.file_tabs.get_active_tab()
        if not active_tab or not active_tab.document:
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return
        
        page = active_tab.document.get_page(active_page_id)
        if not page:
            return
        
        # Mark document as modified
        self.file_tabs.set_tab_modified(active_tab.tab_id, True)
        
        # Re-render the page
        self.design_canvas.set_page(page)
    
    def _handle_component_selection(self, event) -> None:
        """
        Handle clicking on a component to select it.
        
        Args:
            event: Click event
        """
        # Get canvas coordinates
        canvas_x = self.design_canvas.canvas.canvasx(event.x)
        canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Get active page
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            self.properties_panel.set_component(None)
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            self.properties_panel.set_component(None)
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            self.properties_panel.set_component(None)
            return
        
        # Find component at click position
        for component in page.components.values():
            comp_x, comp_y = component.position
            
            # Get component bounds (simplified - assumes components are roughly 100x100)
            # TODO: Get actual component bounds from renderer
            half_size = 50
            
            if (comp_x - half_size <= canvas_x <= comp_x + half_size and
                comp_y - half_size <= canvas_y <= comp_y + half_size):
                # Component clicked
                self.properties_panel.set_component(component)
                self.set_status(f"Selected {component.__class__.__name__} ({component.component_id})")
                return
        
        # No component clicked - deselect
        self.properties_panel.set_component(None)
        self.set_status("Ready")


    
    def _clear_wire_preview(self) -> None:
        """Clear wire preview line from canvas."""
        if self.wire_preview_line:
            self.design_canvas.canvas.delete(self.wire_preview_line)
            self.wire_preview_line = None

