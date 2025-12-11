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
            # Save document
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
        # TODO: Implement in Phase 10.1
        self.set_status("Zoom In (not yet implemented)")
        
    def _menu_zoom_out(self) -> None:
        """Handle View > Zoom Out."""
        # TODO: Implement in Phase 10.1
        self.set_status("Zoom Out (not yet implemented)")
        
    def _menu_reset_zoom(self) -> None:
        """Handle View > Reset Zoom."""
        # TODO: Implement in Phase 10.1
        self.set_status("Reset Zoom (not yet implemented)")
        
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
        
        # Create initial untitled document
        initial_doc = Document()
        initial_doc.create_page("Page 1")
        self.file_tabs.add_untitled_tab(initial_doc)
        
        # Content area (for canvas, toolbars, etc.)
        self.content_frame = tk.Frame(
            self.main_frame,
            bg=VSCodeTheme.BG_PRIMARY
        )
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Add a centered label to show window is working
        welcome_label = tk.Label(
            self.content_frame,
            text="Relay Simulator III\n\nPhase 9.1: File Tab System",
            font=VSCodeTheme.get_font('large', bold=True),
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            justify=tk.CENTER
        )
        welcome_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
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
        Handle tab switch event.
        
        Args:
            tab_id: ID of newly active tab
        """
        tab = self.file_tabs.get_tab(tab_id)
        if tab:
            # Update window title
            self._update_window_title()
            # TODO: Switch canvas to new document/page in Phase 10
            self.set_status(f"Switched to {tab.filename}")
    
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
