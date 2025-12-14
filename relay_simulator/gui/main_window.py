"""
Main Window for Relay Simulator III

Provides the MainWindow class which manages the primary application window,
including initialization, lifecycle, and basic window operations.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional, Dict
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
from core.vnet_builder import VnetBuilder
from core.vnet import VNET
from core.tab import Tab
from core.bridge import Bridge
from fileio.document_loader import DocumentLoader
from simulation.simulation_engine import SimulationEngine
from components.base import Component


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
        
        # Track simulation mode (False = Design Mode, True = Simulation Mode)
        self.simulation_mode = False
        self.simulation_engine = None  # Will hold SimulationEngine instance when running
        
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
        
        # Clear current selection
        self._clear_selection()
        
        # Select all components on the page
        for component_id in page.components.keys():
            self.selected_components.add(component_id)
            self.design_canvas.set_component_selected(component_id, True)
        
        # Update properties panel (don't show individual component if multiple selected)
        if len(self.selected_components) > 0:
            self.properties_panel.set_component(None)
            self.menu_bar.enable_edit_menu(has_selection=True)
            self.set_status(f"Selected all {len(self.selected_components)} component(s)")
        else:
            self.menu_bar.enable_edit_menu(has_selection=False)
            self.set_status("No components to select")
        
    def _menu_cut(self) -> None:
        """Handle Edit > Cut."""
        if self.simulation_mode:
            return
        self._cut_selected()
        
    def _menu_copy(self) -> None:
        """Handle Edit > Copy."""
        if self.simulation_mode:
            return
        self._copy_selected()
        
    def _menu_paste(self) -> None:
        """Handle Edit > Paste."""
        if self.simulation_mode:
            return
        self._paste_clipboard()
        
    def _menu_start_simulation(self) -> None:
        """Handle Simulation > Start Simulation (F5)."""
        if self.simulation_mode:
            return  # Already in simulation mode
        
        # Get active document
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            self.set_status("No document open to simulate")
            return
        
        # Build simulation data structures
        try:
            vnets, tabs, bridges, components = self._build_simulation_structures(tab.document)
        except Exception as e:
            messagebox.showerror("Simulation Error", f"Failed to build simulation:\n{e}")
            return
        
        # Create and initialize simulation engine
        try:
            self.simulation_engine = SimulationEngine(
                vnets=vnets,
                tabs=tabs,
                bridges=bridges,
                components=components,
                max_iterations=10000,
                timeout_seconds=30.0
            )
            
            if not self.simulation_engine.initialize():
                messagebox.showerror("Simulation Error", "Failed to initialize simulation")
                self.simulation_engine = None
                return
            
        except Exception as e:
            messagebox.showerror("Simulation Error", f"Failed to create simulation:\n{e}")
            self.simulation_engine = None
            return
        
        # Switch to Simulation Mode
        self.simulation_mode = True
        
        # Update UI for simulation mode
        self.toolbox.pack_forget()  # Hide toolbox
        self.file_tabs.set_simulation_running(True)
        self.menu_bar.enable_simulation_controls(is_running=True)
        self.set_status("Simulation Mode - Click switches to toggle. Press Shift+F5 to stop.")
        
        # Clear any active editing states
        self.placement_component = None
        self.wire_start_tab = None
        self.wire_temp_waypoints = []
        self._clear_wire_preview()
        self.selected_components.clear()
        
        # Disable canvas cursor
        self.design_canvas.canvas.config(cursor="")
        
        # Start simulation in background
        self.root.after(10, self._run_simulation_step)
        
    def _menu_stop_simulation(self) -> None:
        """Handle Simulation > Stop Simulation (Shift+F5)."""
        if not self.simulation_mode:
            return  # Already in design mode
        
        # Stop and shutdown simulation engine
        if self.simulation_engine:
            try:
                self.simulation_engine.shutdown()
                stats = self.simulation_engine.get_statistics()
                print(f"Simulation Statistics:")
                print(f"  Iterations: {stats.iterations}")
                print(f"  Components Updated: {stats.components_updated}")
                print(f"  Time to Stability: {stats.time_to_stability:.3f}s")
                print(f"  Total Time: {stats.total_time:.3f}s")
                print(f"  Stable: {stats.stable}")
            except Exception as e:
                print(f"Error shutting down simulation: {e}")
            finally:
                self.simulation_engine = None
        
        # Switch back to Design Mode
        self.simulation_mode = False
        
        # Restore UI for design mode - pack before design_canvas.frame
        self.toolbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1), before=self.design_canvas.frame)
        self.file_tabs.set_simulation_running(False)
        self.menu_bar.enable_simulation_controls(is_running=False)
        self.set_status("Design Mode - Ready")
        
        # Redraw canvas to clear powered state visual feedback
        self._redraw_canvas()
    
    def _build_simulation_structures(self, document: Document):
        """
        Build simulation data structures from document.
        
        Args:
            document: Document to build from
            
        Returns:
            Tuple of (vnets, tabs, bridges, components) dictionaries
        """
        vnets: Dict[str, VNET] = {}
        tabs: Dict[str, Tab] = {}
        bridges: Dict[str, Bridge] = {}
        components: Dict[str, Component] = {}
        
        # Collect all components from all pages
        for page in document.get_all_pages():
            for component in page.get_all_components():
                components[component.component_id] = component
                
                # Collect all tabs from component pins
                for pin in component.get_all_pins().values():
                    for tab in pin.tabs.values():
                        tabs[tab.tab_id] = tab
        
        # Build VNETs for each page
        vnet_builder = VnetBuilder(document.id_manager)
        for page in document.get_all_pages():
            page_vnets = vnet_builder.build_vnets_for_page(page)
            for vnet in page_vnets:
                vnets[vnet.vnet_id] = vnet
        
        # TODO: Build bridges for cross-page connections
        # This would require scanning for components with matching link_names
        # For Phase 15.2, we'll skip this (bridges remain empty for single-page circuits)
        
        return vnets, tabs, bridges, components
    
    def _run_simulation_step(self):
        """
        Run one simulation step and schedule the next.
        This keeps the simulation running in the background.
        """
        if not self.simulation_mode or not self.simulation_engine:
            print("DEBUG: _run_simulation_step but not in simulation mode")
            return
        
        print("DEBUG: Running simulation step...")
        
        # Run one iteration of simulation
        try:
            stats = self.simulation_engine.run()
            
            print(f"DEBUG: Simulation complete - stable={stats.stable}, iterations={stats.iterations}")
            
            # Update visual feedback
            self._update_simulation_visuals()
            
            # Check if simulation is stable
            if stats.stable:
                self.set_status(f"Simulation Stable - {stats.iterations} iterations in {stats.time_to_stability:.3f}s")
            elif stats.max_iterations_reached:
                self.set_status(f"Simulation Oscillating - Max iterations reached")
            elif stats.timeout_reached:
                self.set_status(f"Simulation Timeout - {stats.total_time:.3f}s")
            else:
                # Continue simulation
                self.root.after(100, self._run_simulation_step)
                
        except Exception as e:
            print(f"Simulation error: {e}")
            import traceback
            traceback.print_exc()
            self.set_status(f"Simulation Error: {e}")
    
    def _update_simulation_visuals(self):
        """Update visual feedback for powered components and wires."""
        print("DEBUG: _update_simulation_visuals called")
        
        # Get active page
        tab = self.file_tabs.get_active_tab()
        if tab and tab.document:
            active_page_id = self.page_tabs.get_active_page_id()
            if active_page_id:
                page = tab.document.get_page(active_page_id)
                if page:
                    # Re-render the entire page with simulation engine
                    self._set_canvas_page(page)
        
        print("DEBUG: Canvas redrawn")
    
    def _handle_switch_toggle(self, canvas_x: float, canvas_y: float):
        """
        Handle switch toggling in simulation mode.
        
        Args:
            canvas_x: Canvas X coordinate of click
            canvas_y: Canvas Y coordinate of click
        """
        print(f"DEBUG: _handle_switch_toggle called at ({canvas_x}, {canvas_y})")
        
        # Get active page
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            print("DEBUG: No active tab or document")
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            print("DEBUG: No active page")
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            print("DEBUG: Page not found")
            return
        
        # Find component at click position
        clicked_component = None
        print(f"DEBUG: Checking {len(page.get_all_components())} components")
        for component in page.get_all_components():
            x, y = component.position
            distance = ((canvas_x - x)**2 + (canvas_y - y)**2)**0.5
            print(f"DEBUG: Component {component.component_type} at ({x}, {y}), distance={distance:.1f}")
            # Simple bounding box check (assuming components are roughly 40x40)
            if abs(canvas_x - x) <= 20 and abs(canvas_y - y) <= 20:
                clicked_component = component
                print(f"DEBUG: MATCHED component {component.component_type}")
                break
        
        if not clicked_component:
            print("DEBUG: No component clicked")
            return
        
        # Check if it's a switch component
        print(f"DEBUG: Clicked component type: '{clicked_component.component_type}'")
        if clicked_component.component_type != "Switch":
            print(f"DEBUG: Not a Switch, it's a {clicked_component.component_type}")
            return
        
        print(f"DEBUG: About to toggle switch, current state: {clicked_component._is_on}")
        
        # Toggle the switch
        try:
            # Switch component has a toggle_switch() method
            if hasattr(clicked_component, 'toggle_switch'):
                clicked_component.toggle_switch()
                print(f"DEBUG: Toggled! New state: {clicked_component._is_on}")
                self.set_status(f"Switch toggled")
                
                # Update the component's logic to propagate the state change
                if self.simulation_engine:
                    print("DEBUG: Calling simulate_logic")
                    clicked_component.simulate_logic(self.simulation_engine.vnet_manager)
                    
                    # Mark all VNETs dirty to force re-evaluation
                    self.simulation_engine.dirty_manager.mark_all_dirty()
                    
                    # Update visuals immediately
                    self._update_simulation_visuals()
                    
                    # Re-run simulation to propagate change
                    self.root.after(10, self._run_simulation_step)
                    print("DEBUG: Simulation restart scheduled")
                else:
                    print("DEBUG: No simulation engine!")
            else:
                print("DEBUG: No toggle_switch method")
                self.set_status(f"Component {clicked_component.component_type} is not interactive")
        except Exception as e:
            print(f"Error toggling switch: {e}")
            import traceback
            traceback.print_exc()
            self.set_status(f"Error toggling switch: {e}")
        
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
    
    # === Context Menu ===
    
    def _create_context_menu(self) -> None:
        """Create right-click context menu for canvas."""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        
        # Add menu items
        self.context_menu.add_command(
            label="Cut",
            accelerator="Ctrl+X",
            command=self._cut_selected
        )
        self.context_menu.add_command(
            label="Copy",
            accelerator="Ctrl+C",
            command=self._copy_selected
        )
        self.context_menu.add_command(
            label="Paste",
            accelerator="Ctrl+V",
            command=self._paste_clipboard
        )
        
        self.context_menu.add_separator()
        
        self.context_menu.add_command(
            label="Delete",
            accelerator="Delete",
            command=self._delete_selected
        )
        
        self.context_menu.add_separator()
        
        self.context_menu.add_command(
            label="Select All",
            accelerator="Ctrl+A",
            command=self._menu_select_all
        )
    
    def _show_context_menu(self, event) -> None:
        """
        Show context menu at cursor position.
        
        Args:
            event: Right-click event
        """
        # Get canvas coordinates
        canvas_x = self.design_canvas.canvas.canvasx(event.x)
        canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Check if right-clicked on a waypoint
        waypoint_info = self._find_waypoint_at_position(canvas_x, canvas_y)
        if waypoint_info:
            self._show_waypoint_context_menu(event, waypoint_info)
            return
        
        # Update menu item states based on selection
        has_selection = len(self.selected_components) > 0
        has_clipboard = len(self.clipboard) > 0
        
        # Enable/disable menu items
        cut_index = 0
        copy_index = 1
        paste_index = 2
        delete_index = 4  # After separator
        
        self.context_menu.entryconfig(cut_index, state=tk.NORMAL if has_selection else tk.DISABLED)
        self.context_menu.entryconfig(copy_index, state=tk.NORMAL if has_selection else tk.DISABLED)
        self.context_menu.entryconfig(paste_index, state=tk.NORMAL if has_clipboard else tk.DISABLED)
        self.context_menu.entryconfig(delete_index, state=tk.NORMAL if has_selection else tk.DISABLED)
        
        # Show menu at cursor position
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def _on_right_click(self, event) -> None:
        """
        Handle right mouse button press - track position for context menu vs pan.
        
        Args:
            event: Right-click event
        """
        # Record the position where right-click started
        self.right_click_start = (event.x, event.y)
        
        # Let canvas handle pan start
        self.design_canvas._on_pan_start(event)
    
    def _on_right_release(self, event) -> None:
        """
        Handle right mouse button release - show context menu if no drag occurred.
        
        Args:
            event: Button release event
        """
        # Let canvas handle pan end first
        self.design_canvas._on_pan_end(event)
        
        # Check if this was a drag or just a click
        if self.right_click_start:
            start_x, start_y = self.right_click_start
            # If mouse moved less than 5 pixels, treat as click (show context menu)
            distance = ((event.x - start_x) ** 2 + (event.y - start_y) ** 2) ** 0.5
            if distance < 5:
                self._show_context_menu(event)
            
            self.right_click_start = None
    
    def _show_waypoint_context_menu(self, event, waypoint_info: Tuple[str, str]) -> None:
        """
        Show context menu for waypoint operations.
        
        Args:
            event: Right-click event
            waypoint_info: Tuple of (wire_id, waypoint_id)
        """
        # Create a simple menu for waypoint
        waypoint_menu = tk.Menu(self.root, tearoff=0)
        waypoint_menu.add_command(
            label="Delete Waypoint",
            command=lambda: self._delete_waypoint(waypoint_info)
        )
        
        try:
            waypoint_menu.tk_popup(event.x_root, event.y_root)
        finally:
            waypoint_menu.grab_release()
    
    def _delete_waypoint(self, waypoint_info: Tuple[str, str]) -> None:
        """
        Delete a waypoint from a wire.
        
        Args:
            waypoint_info: Tuple of (wire_id, waypoint_id)
        """
        wire_id, waypoint_id = waypoint_info
        
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return
        
        wire = page.wires.get(wire_id)
        if not wire:
            return
        
        # Remove waypoint
        waypoint = wire.remove_waypoint(waypoint_id)
        if waypoint:
            # Mark document as modified
            self.file_tabs.set_tab_modified(tab.tab_id, True)
            
            # Re-render page
            self.design_canvas.set_page(page)
            
            self.set_status("Waypoint deleted")
    
    # === Widget Creation ===
        
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
        
        # Track wire drawing state
        self.wire_start_tab = None  # Tab ID where wire starts
        self.wire_preview_lines = []  # Canvas items for wire preview (multiple segments with waypoints)
        self.wire_temp_waypoints = []  # Temporary waypoints during wire creation [(x, y), ...]
        
        # Track selected components
        self.selected_components = set()  # Set of selected component IDs
        self.selection_box = None  # Rectangle for bounding box selection
        self.selection_start = None  # Start position for bounding box
        
        # Track component dragging
        self.drag_start = None  # (canvas_x, canvas_y) where drag started
        self.drag_components = {}  # {component_id: (original_x, original_y)}
        self.is_dragging = False  # True when actively dragging components
        
        # Track waypoint editing
        self.selected_wire = None  # Wire ID currently selected
        self.dragging_waypoint = None  # Waypoint being dragged (waypoint_id, wire_id)
        self.waypoint_drag_start = None  # Original position of waypoint being dragged
        self.hovered_waypoint = None  # Waypoint being hovered (waypoint_id, wire_id)
        
        # Track junction editing
        self.dragging_junction = None  # Junction ID being dragged
        self.junction_drag_start = None  # Original position of junction being dragged
        
        # Track right-click for context menu vs pan
        self.right_click_start = None  # Position where right-click started
        
        # Clipboard for copy/paste
        self.clipboard = []  # List of serialized components
        
        # Create context menu
        self._create_context_menu()
        
        # Bind canvas click for component placement and wire drawing
        self.design_canvas.canvas.bind('<Button-1>', self._on_canvas_click)
        self.design_canvas.canvas.bind('<Motion>', self._on_canvas_motion)
        self.design_canvas.canvas.bind('<ButtonRelease-1>', self._on_canvas_release)
        self.design_canvas.canvas.bind('<Button-3>', self._on_right_click)  # Right-click
        self.design_canvas.canvas.bind('<ButtonRelease-3>', self._on_right_release)  # Right-click release
        
        # Bind keyboard events for component movement
        self.root.bind('<KeyPress>', self._on_key_press)
        
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
        Handle component selection from toolbox.
        
        Args:
            component_type: Type selected (None = normal mode, or component type for placement)
        """
        # Reset placement mode
        self.placement_component = None
        self.placement_rotation = 0
        self._clear_wire_preview()
        self.wire_temp_waypoints = []
        
        if component_type:
            # Component placement mode
            self.placement_component = component_type
            self.set_status(f"Click on canvas to place {component_type}. Press R to rotate.")
            self.design_canvas.canvas.config(cursor="crosshair")
        else:
            # Normal interaction mode
            self.set_status("Ready")
            self.design_canvas.canvas.config(cursor="")
    
    def _on_canvas_click(self, event) -> None:
        """
        Handle canvas click for component placement, wire drawing, and waypoint editing.
        In simulation mode, handles switch toggling.
        
        Args:
            event: Click event
        """
        # Convert screen coordinates to canvas coordinates (needed for all modes)
        canvas_x = self.design_canvas.canvas.canvasx(event.x)
        canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        print(f"DEBUG: Canvas click at screen ({event.x}, {event.y}) -> canvas ({canvas_x}, {canvas_y})")
        print(f"DEBUG: simulation_mode = {self.simulation_mode}")
        
        # In simulation mode, only allow switch toggling
        if self.simulation_mode:
            print("DEBUG: In simulation mode, calling _handle_switch_toggle")
            self._handle_switch_toggle(canvas_x, canvas_y)
            return
        
        # Design mode only - handle component placement mode
        if self.placement_component:
            self._handle_component_placement(event)
            return
        
        # Check if clicked on a junction
        junction_id = self._find_junction_at_position(canvas_x, canvas_y)
        if junction_id:
            # If drawing a wire, complete it at the junction
            if self.wire_start_tab:
                self._complete_wire_to_junction(junction_id)
                return
            else:
                # Not drawing a wire - start dragging the junction
                self._start_junction_drag(junction_id, canvas_x, canvas_y)
                return
        
        # Check if clicked on a waypoint (for dragging)
        waypoint_info = self._find_waypoint_at_position(canvas_x, canvas_y)
        if waypoint_info:
            self._start_waypoint_drag(waypoint_info, canvas_x, canvas_y)
            return
        
        # Check if clicked on a tab (for wire creation)
        tab_id = self._find_tab_at_position(canvas_x, canvas_y)
        if tab_id:
            # Clicked on a tab - handle wire creation
            self._handle_wire_click(event)
            return
        
        # Check if clicked on a wire (for adding waypoints or creating junctions)
        if self.wire_start_tab:
            # If we're in the middle of drawing a wire, check for wire clicks to create junctions
            wire_id = self._find_wire_at_position(canvas_x, canvas_y)
            if wire_id:
                self._create_junction_and_complete_wire(canvas_x, canvas_y, wire_id)
                return
            else:
                # Clicked on empty canvas - add waypoint
                snap_size = self.settings.get_snap_size()
                snapped_x = round(canvas_x / snap_size) * snap_size
                snapped_y = round(canvas_y / snap_size) * snap_size
                self.wire_temp_waypoints.append((int(snapped_x), int(snapped_y)))
                self.set_status(f"Waypoint added. Click a tab to complete or click canvas for more waypoints.")
            return
        else:
            # Not drawing a wire - check for wire segment click to add waypoint
            wire_clicked = self._find_wire_at_position(canvas_x, canvas_y)
            if wire_clicked:
                self._handle_wire_segment_click(event, wire_clicked)
                return
        
        # Handle component selection and dragging
        self._handle_component_selection(event)
    
    def _handle_component_placement(self, event) -> None:
        """
        Handle component placement on canvas.
        
        Args:
            event: Click event
        """
        # Block placement in simulation mode
        if self.simulation_mode:
            return
        
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
            
            # Return to normal mode
            self.toolbox.deselect_all()
            self.placement_component = None
            self.design_canvas.canvas.config(cursor="")
            
            self.set_status(f"Component placed at ({int(snapped_x)}, {int(snapped_y)})")
    
    # === Wire Drawing ===
    
    def _on_canvas_motion(self, event) -> None:
        """
        Handle mouse motion for wire preview, bounding box selection, waypoint dragging, junction dragging, and component dragging.
        
        Args:
            event: Motion event
        """
        # Get canvas coordinates
        canvas_x = self.design_canvas.canvas.canvasx(event.x)
        canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Update waypoint hover state (always check, even while dragging/drawing)
        # This allows waypoint markers to appear when hovering
        if not self.dragging_waypoint and not self.dragging_junction:  # Don't update hover while actively dragging
            waypoint_info = self._find_waypoint_at_position(canvas_x, canvas_y)
            if waypoint_info != self.hovered_waypoint:
                self.hovered_waypoint = waypoint_info
                self._redraw_canvas()  # Redraw to show/hide waypoint markers
        
        # Handle junction dragging
        if self.dragging_junction:
            self._update_junction_drag(canvas_x, canvas_y)
            return
        
        # Handle waypoint dragging
        if self.dragging_waypoint:
            self._update_waypoint_drag(canvas_x, canvas_y)
            return
        
        # Handle component dragging (check drag_start, not is_dragging)
        if self.drag_start:
            self._update_drag(canvas_x, canvas_y)
            return
        
        # Handle bounding box selection drawing
        if self.selection_start:
            canvas_x = self.design_canvas.canvas.canvasx(event.x)
            canvas_y = self.design_canvas.canvas.canvasy(event.y)
            
            # Update or create selection box
            if self.selection_box:
                self.design_canvas.canvas.delete(self.selection_box)
            
            start_x, start_y = self.selection_start
            self.selection_box = self.design_canvas.canvas.create_rectangle(
                start_x, start_y, canvas_x, canvas_y,
                outline=VSCodeTheme.ACCENT_BLUE,
                width=2,
                dash=(5, 5)
            )
            return
        
        # Handle wire preview
        if not self.wire_start_tab:
            return
        
        # Get canvas coordinates
        canvas_x = self.design_canvas.canvas.canvasx(event.x)
        canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Clear old preview lines
        for line in self.wire_preview_lines:
            self.design_canvas.canvas.delete(line)
        self.wire_preview_lines = []
        
        # Get start position from tab
        start_pos = self._get_tab_canvas_position(self.wire_start_tab)
        if start_pos:
            # Build path: start -> waypoints -> cursor
            path_points = [start_pos] + self.wire_temp_waypoints + [(canvas_x, canvas_y)]
            
            # Draw segments
            for i in range(len(path_points) - 1):
                x1, y1 = path_points[i]
                x2, y2 = path_points[i + 1]
                line = self.design_canvas.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=VSCodeTheme.WIRE_SELECTED,
                    width=2,
                    dash=(5, 5)  # Dashed line for preview
                )
                self.wire_preview_lines.append(line)
            
            # Draw waypoint markers
            for wx, wy in self.wire_temp_waypoints:
                marker = self.design_canvas.canvas.create_oval(
                    wx - 3, wy - 3, wx + 3, wy + 3,
                    fill=VSCodeTheme.WIRE_SELECTED,
                    outline=VSCodeTheme.WIRE_SELECTED
                )
                self.wire_preview_lines.append(marker)
    
    def _redraw_canvas(self) -> None:
        """
        Redraw the canvas (used when waypoint hover state changes or simulation updates).
        """
        # Update hovered waypoint on canvas
        self.design_canvas.hovered_waypoint = self.hovered_waypoint
        
        # Re-render wires to show/hide waypoint markers and powered state
        self.design_canvas.render_wires(self.simulation_engine if self.simulation_mode else None)
    
    def _set_canvas_page(self, page) -> None:
        """
        Set the canvas page with simulation engine if in simulation mode.
        
        Args:
            page: Page to set
        """
        self.design_canvas.set_page(page, self.simulation_engine if self.simulation_mode else None)
    
    def _handle_wire_click(self, event) -> None:
        """
        Handle click in wire drawing mode.
        
        Args:
            event: Click event
        """
        # Block wire drawing in simulation mode
        if self.simulation_mode:
            return
        
        # Get canvas coordinates
        canvas_x = self.design_canvas.canvas.canvasx(event.x)
        canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Find tab at click location
        tab_id = self._find_tab_at_position(canvas_x, canvas_y)
        
        if not tab_id:
            # Check if clicked on a wire (for junction creation)
            if self.wire_start_tab:
                wire_id = self._find_wire_at_position(canvas_x, canvas_y)
                if wire_id:
                    # Create junction at click position
                    self._create_junction_and_complete_wire(canvas_x, canvas_y, wire_id)
                    return
                else:
                    # Clicked on empty canvas - add waypoint to wire being drawn
                    snap_size = self.settings.get_snap_size()
                    snapped_x = round(canvas_x / snap_size) * snap_size
                    snapped_y = round(canvas_y / snap_size) * snap_size
                    self.wire_temp_waypoints.append((int(snapped_x), int(snapped_y)))
                    self.set_status(f"Waypoint added. Click another position, a tab, or a wire to complete.")
            return
        
        if not self.wire_start_tab:
            # First click - start wire
            self.wire_start_tab = tab_id
            self.set_status(f"Wire started. Click on a tab or wire to complete the wire.")
        else:
            # Second click - complete wire
            if tab_id == self.wire_start_tab:
                self.set_status("Cannot connect a tab to itself. Click on a different tab.")
                return
            
            self._create_wire(self.wire_start_tab, tab_id, self.wire_temp_waypoints)
            self._clear_wire_preview()
            self.wire_start_tab = None
            self.wire_temp_waypoints = []
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
        
        # Get current zoom level for accurate hit detection
        zoom = self.design_canvas.zoom_level
        
        # Check all components and their tabs
        for component in page.components.values():
            comp_x, comp_y = component.position
            for pin in component.pins.values():
                for tab_obj in pin.tabs.values():
                    tab_dx, tab_dy = tab_obj.relative_position
                    tab_x = comp_x + tab_dx
                    tab_y = comp_y + tab_dy
                    
                    # Check if click is within tab area (scale hit radius with zoom)
                    hit_radius = VSCodeTheme.TAB_SIZE * 1.5 * zoom  # Smaller radius for easier component selection
                    if abs(x - tab_x) <= hit_radius and abs(y - tab_y) <= hit_radius:
                        return tab_obj.tab_id
        
        return None
    
    def _get_tab_canvas_position(self, tab_id: str) -> Optional[Tuple[float, float]]:
        """
        Get canvas position of a tab or junction.
        
        Args:
            tab_id: Tab ID or Junction ID
            
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
        
        # Check if this is a junction ID first
        junction = page.get_junction(tab_id)
        if junction:
            return junction.position
        
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
    
    def _complete_wire_to_junction(self, junction_id: str) -> None:
        """
        Complete the wire being drawn to an existing junction.
        
        Args:
            junction_id: ID of the junction to connect to
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
        
        # Verify junction exists
        junction = page.get_junction(junction_id)
        if not junction:
            return
        
        # Create wire from start tab to junction
        from core.wire import Wire, Waypoint
        new_wire_id = tab.document.id_manager.generate_id()
        new_wire = Wire(new_wire_id, self.wire_start_tab, junction_id)
        
        # Add waypoints from temporary wire drawing if provided
        if self.wire_temp_waypoints:
            for pos in self.wire_temp_waypoints:
                waypoint_id = tab.document.id_manager.generate_id()
                waypoint = Waypoint(waypoint_id, pos)
                new_wire.add_waypoint(waypoint)
        
        # Add new wire to page
        page.add_wire(new_wire)
        
        # Mark document as modified
        self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        # Clear wire creation state
        self._clear_wire_preview()
        self.wire_start_tab = None
        self.wire_temp_waypoints = []
        
        # Re-render page
        self.design_canvas.set_page(page)
        
        self.set_status(f"Wire connected to existing junction.")

    def _create_junction_and_complete_wire(self, canvas_x: float, canvas_y: float, wire_id: str) -> None:
        """
        Create a junction at the click position and complete the wire to it.
        Also splits the clicked wire at the junction point.
        
        Args:
            canvas_x: Canvas X coordinate where wire was clicked
            canvas_y: Canvas Y coordinate where wire was clicked
            wire_id: ID of the wire that was clicked
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
        
        # Get the wire that was clicked
        clicked_wire = page.get_wire(wire_id)
        if not clicked_wire:
            return
        
        # Snap junction position to grid
        snap_size = self.settings.get_snap_size()
        junction_x = round(canvas_x / snap_size) * snap_size
        junction_y = round(canvas_y / snap_size) * snap_size
        junction_pos = (int(junction_x), int(junction_y))
        
        # Generate junction ID
        junction_id = tab.document.id_manager.generate_id()
        
        # Create junction
        from core.wire import Junction, Wire, Waypoint
        junction = Junction(junction_id, junction_pos)
        
        # Add junction to page
        page.add_junction(junction)
        
        # Create wire from drawing start tab to junction (using junction_id as end_tab_id)
        new_wire_id = tab.document.id_manager.generate_id()
        new_wire = Wire(new_wire_id, self.wire_start_tab, junction_id)
        
        # Add waypoints from temporary wire drawing if provided
        if self.wire_temp_waypoints:
            for pos in self.wire_temp_waypoints:
                waypoint_id = tab.document.id_manager.generate_id()
                waypoint = Waypoint(waypoint_id, pos)
                new_wire.add_waypoint(waypoint)
        
        # Add new wire to page
        page.add_wire(new_wire)
        
        # Now split the clicked wire at the junction point
        # Store the original end point of the clicked wire
        original_end = clicked_wire.end_tab_id
        
        # Modify the clicked wire to end at the junction instead
        clicked_wire.end_tab_id = junction_id
        
        # Create a new wire from the junction to the original end point
        if original_end:
            continuation_wire_id = tab.document.id_manager.generate_id()
            continuation_wire = Wire(continuation_wire_id, junction_id, original_end)
            page.add_wire(continuation_wire)
        
        # Mark document as modified
        self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        # Clear wire creation state
        self._clear_wire_preview()
        self.wire_start_tab = None
        self.wire_temp_waypoints = []
        
        # Re-render page (including new junction and wires)
        self.design_canvas.set_page(page)
        
        self.set_status(f"Junction created at wire intersection. Three wires now connected.")
    
    def _create_wire(self, start_tab_id: str, end_tab_id: str, waypoints: list = None) -> None:
        """
        Create a wire between two tabs.
        
        Args:
            start_tab_id: Starting tab ID
            end_tab_id: Ending tab ID
            waypoints: Optional list of waypoint positions [(x, y), ...]
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
        
        # Add waypoints if provided
        if waypoints:
            from core.wire import Waypoint
            for pos in waypoints:
                waypoint_id = tab.document.id_manager.generate_id()
                waypoint = Waypoint(waypoint_id, pos)
                wire.add_waypoint(waypoint)
        
        # Add to page
        page.add_wire(wire)
        
        # Mark document as modified
        self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        # Re-render page (including new wire)
        self.design_canvas.set_page(page)
    
    def _find_wire_at_position(self, x: float, y: float) -> Optional[str]:
        """
        Find wire at the given canvas position.
        
        Args:
            x: Canvas X coordinate
            y: Canvas Y coordinate
            
        Returns:
            Wire ID if found, None otherwise
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
        
        # Check all wires
        hit_distance = 8.0  # Pixels from wire line to be considered a click (increased for easier clicking)
        
        for wire in page.wires.values():
            # Get wire path segments
            start_pos = self._get_tab_canvas_position(wire.start_tab_id)
            if not start_pos:
                continue
            
            end_pos = None
            if wire.end_tab_id:
                end_pos = self._get_tab_canvas_position(wire.end_tab_id)
            
            if not end_pos and not wire.waypoints:
                continue
            
            # Build path: start -> waypoints -> end
            path_points = [start_pos]
            
            # Add waypoints (sorted by... actually we need to maintain order)
            # For now, just add them in dict order (should maintain insertion order in Python 3.7+)
            for waypoint in wire.waypoints.values():
                path_points.append(waypoint.position)
            
            if end_pos:
                path_points.append(end_pos)
            
            # Check if click is near any segment
            for i in range(len(path_points) - 1):
                x1, y1 = path_points[i]
                x2, y2 = path_points[i + 1]
                
                # Calculate distance from point to line segment
                dist = self._point_to_segment_distance(x, y, x1, y1, x2, y2)
                
                if dist <= hit_distance:
                    return wire.wire_id
        
        return None
    
    def _point_to_segment_distance(self, px: float, py: float, 
                                   x1: float, y1: float, x2: float, y2: float) -> float:
        """
        Calculate distance from point to line segment.
        
        Args:
            px, py: Point coordinates
            x1, y1: Line segment start
            x2, y2: Line segment end
            
        Returns:
            Distance from point to segment
        """
        # Vector from p1 to p2
        dx = x2 - x1
        dy = y2 - y1
        
        # If segment is a point
        if dx == 0 and dy == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        
        # Parameter t of closest point on line
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        
        # Closest point on segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance from point to closest point
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
    
    def _handle_wire_segment_click(self, event, wire_id: str) -> None:
        """
        Handle click on a wire segment to add a waypoint.
        
        Args:
            event: Click event
            wire_id: ID of clicked wire
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
        
        wire = page.wires.get(wire_id)
        if not wire:
            return
        
        # Get canvas coordinates
        canvas_x = self.design_canvas.canvas.canvasx(event.x)
        canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Snap to grid
        snap_size = self.settings.get_snap_size()
        snapped_x = round(canvas_x / snap_size) * snap_size
        snapped_y = round(canvas_y / snap_size) * snap_size
        
        # Create waypoint
        from core.wire import Waypoint
        waypoint_id = tab.document.id_manager.generate_id()
        waypoint = Waypoint(waypoint_id, (int(snapped_x), int(snapped_y)))
        
        # Add waypoint to wire
        wire.add_waypoint(waypoint)
        
        # Mark document as modified
        self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        # Re-render page
        self.design_canvas.set_page(page)
        
        self.set_status(f"Added waypoint to wire. Right-click waypoint to delete.")
    
    def _find_waypoint_at_position(self, x: float, y: float) -> Optional[Tuple[str, str]]:
        """
        Find waypoint at the given canvas position.
        
        Args:
            x: Canvas X coordinate
            y: Canvas Y coordinate
            
        Returns:
            Tuple of (wire_id, waypoint_id) if found, None otherwise
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
        
        hit_radius = 6.0  # Pixels from waypoint center to be considered a click
        
        for wire in page.wires.values():
            for waypoint in wire.waypoints.values():
                wx, wy = waypoint.position
                distance = ((x - wx) ** 2 + (y - wy) ** 2) ** 0.5
                
                if distance <= hit_radius:
                    return (wire.wire_id, waypoint.waypoint_id)
        
        return None
    
    def _find_junction_at_position(self, x: float, y: float) -> Optional[str]:
        """
        Find junction at the given canvas position.
        
        Args:
            x: Canvas X coordinate
            y: Canvas Y coordinate
            
        Returns:
            Junction ID if found, None otherwise
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
        
        hit_radius = 8.0  # Pixels from junction center to be considered a click
        
        for junction in page.junctions.values():
            jx, jy = junction.position
            distance = ((x - jx) ** 2 + (y - jy) ** 2) ** 0.5
            
            if distance <= hit_radius:
                return junction.junction_id
        
        return None
    
    def _start_waypoint_drag(self, waypoint_info: Tuple[str, str], x: float, y: float) -> None:
        """
        Start dragging a waypoint.
        
        Args:
            waypoint_info: Tuple of (wire_id, waypoint_id)
            x: Starting canvas X coordinate
            y: Starting canvas Y coordinate
        """
        # Block waypoint dragging in simulation mode
        if self.simulation_mode:
            return
        
        wire_id, waypoint_id = waypoint_info
        
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return
        
        wire = page.wires.get(wire_id)
        if not wire:
            return
        
        waypoint = wire.waypoints.get(waypoint_id)
        if not waypoint:
            return
        
        # Start dragging
        self.dragging_waypoint = (wire_id, waypoint_id)
        self.waypoint_drag_start = waypoint.position
        self.set_status("Dragging waypoint. Press Escape to cancel.")
    
    def _update_waypoint_drag(self, x: float, y: float) -> None:
        """
        Update waypoint position during drag.
        
        Args:
            x: Current canvas X coordinate
            y: Current canvas Y coordinate
        """
        if not self.dragging_waypoint:
            return
        
        wire_id, waypoint_id = self.dragging_waypoint
        
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return
        
        wire = page.wires.get(wire_id)
        if not wire:
            return
        
        waypoint = wire.waypoints.get(waypoint_id)
        if not waypoint:
            return
        
        # Snap to grid
        snap_size = self.settings.get_snap_size()
        snapped_x = round(x / snap_size) * snap_size
        snapped_y = round(y / snap_size) * snap_size
        
        # Update waypoint position
        waypoint.position = (int(snapped_x), int(snapped_y))
        
        # Re-render page
        self.design_canvas.set_page(page)
    
    def _end_waypoint_drag(self) -> None:
        """End waypoint dragging and mark document as modified."""
        if not self.dragging_waypoint:
            return
        
        tab = self.file_tabs.get_active_tab()
        if tab:
            self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        self.dragging_waypoint = None
        self.waypoint_drag_start = None
        self.set_status("Waypoint moved")
    
    def _cancel_waypoint_drag(self) -> None:
        """Cancel waypoint dragging and restore original position."""
        if not self.dragging_waypoint or not self.waypoint_drag_start:
            return
        
        wire_id, waypoint_id = self.dragging_waypoint
        
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return
        
        wire = page.wires.get(wire_id)
        if wire:
            waypoint = wire.waypoints.get(waypoint_id)
            if waypoint:
                waypoint.position = self.waypoint_drag_start
        
        # Re-render page
        self.design_canvas.set_page(page)
        
        self.dragging_waypoint = None
        self.waypoint_drag_start = None
        self.set_status("Waypoint drag cancelled")
    
    def _start_junction_drag(self, junction_id: str, canvas_x: float, canvas_y: float) -> None:
        """
        Start dragging a junction.
        
        Args:
            junction_id: ID of junction to drag
            canvas_x: Canvas X coordinate
            canvas_y: Canvas Y coordinate
        """
        # Block junction dragging in simulation mode
        if self.simulation_mode:
            return
        
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return
        
        junction = page.get_junction(junction_id)
        if not junction:
            return
        
        # Start dragging
        self.dragging_junction = junction_id
        self.junction_drag_start = junction.position
        self.set_status("Dragging junction. Press Escape to cancel.")
    
    def _update_junction_drag(self, canvas_x: float, canvas_y: float) -> None:
        """
        Update junction position during drag.
        
        Args:
            canvas_x: Current canvas X coordinate
            canvas_y: Current canvas Y coordinate
        """
        if not self.dragging_junction:
            return
        
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return
        
        junction = page.get_junction(self.dragging_junction)
        if not junction:
            return
        
        # Snap to grid
        snap_size = self.settings.get_snap_size()
        snapped_x = round(canvas_x / snap_size) * snap_size
        snapped_y = round(canvas_y / snap_size) * snap_size
        
        # Update junction position
        junction.position = (int(snapped_x), int(snapped_y))
        
        # Re-render page
        self.design_canvas.set_page(page)
    
    def _end_junction_drag(self) -> None:
        """End junction dragging and mark document as modified."""
        if not self.dragging_junction:
            return
        
        tab = self.file_tabs.get_active_tab()
        if tab:
            self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        self.dragging_junction = None
        self.junction_drag_start = None
        self.set_status("Junction moved")
    
    def _cancel_junction_drag(self) -> None:
        """Cancel junction dragging and restore original position."""
        if not self.dragging_junction or not self.junction_drag_start:
            return
        
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return
        
        junction = page.get_junction(self.dragging_junction)
        if not junction:
            return
        
        # Restore original position
        junction.position = self.junction_drag_start
        
        # Re-render page
        self.design_canvas.set_page(page)
        
        self.dragging_junction = None
        self.junction_drag_start = None
        self.set_status("Junction drag cancelled")
    
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
        # Block selection in simulation mode
        if self.simulation_mode:
            return
        
        # Get canvas coordinates
        canvas_x = self.design_canvas.canvas.canvasx(event.x)
        canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Check if Ctrl is held for multi-selection
        ctrl_held = (event.state & 0x0004) != 0
        
        # Get active page
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            self._clear_selection()
            return
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            self._clear_selection()
            return
        
        page = tab.document.get_page(active_page_id)
        if not page:
            self._clear_selection()
            return
        
        # Find component at click position
        clicked_component = None
        for component in page.components.values():
            comp_x, comp_y = component.position
            
            # Get component bounds (simplified - assumes components are roughly 100x100)
            # TODO: Get actual component bounds from renderer
            half_size = 50
            
            if (comp_x - half_size <= canvas_x <= comp_x + half_size and
                comp_y - half_size <= canvas_y <= comp_y + half_size):
                clicked_component = component
                break
        
        if clicked_component:
            # Component clicked
            if ctrl_held:
                # Ctrl+Click: Toggle selection (don't start drag)
                if clicked_component.component_id in self.selected_components:
                    self.selected_components.remove(clicked_component.component_id)
                    self.design_canvas.set_component_selected(clicked_component.component_id, False)
                else:
                    self.selected_components.add(clicked_component.component_id)
                    self.design_canvas.set_component_selected(clicked_component.component_id, True)
            else:
                # Regular click: Select component if not already selected
                if clicked_component.component_id not in self.selected_components:
                    self._clear_selection()
                    self.selected_components.add(clicked_component.component_id)
                    self.design_canvas.set_component_selected(clicked_component.component_id, True)
                
                # Always start drag operation for selected components on regular click
                self._start_drag(canvas_x, canvas_y, page)
            
            # Update properties panel and menu
            if len(self.selected_components) == 1:
                self.properties_panel.set_component(clicked_component)
                self.menu_bar.enable_edit_menu(has_selection=True)
                self.set_status(f"Selected {clicked_component.__class__.__name__} ({clicked_component.component_id})")
            elif len(self.selected_components) > 1:
                self.properties_panel.set_component(None)
                self.menu_bar.enable_edit_menu(has_selection=True)
                self.set_status(f"Selected {len(self.selected_components)} components")
            else:
                self.properties_panel.set_component(None)
                self.menu_bar.enable_edit_menu(has_selection=False)
                self.set_status("Ready")
        else:
            # No component clicked
            if not ctrl_held:
                # Start bounding box selection
                self.selection_start = (canvas_x, canvas_y)
            else:
                # Ctrl held but no component - do nothing
                pass
    
    def _clear_selection(self):
        """Clear all selected components."""
        for component_id in self.selected_components:
            self.design_canvas.set_component_selected(component_id, False)
        self.selected_components.clear()
        self.properties_panel.set_component(None)
        self.menu_bar.enable_edit_menu(has_selection=False)
        self.set_status("Ready")
    
    def _on_canvas_release(self, event) -> None:
        """
        Handle mouse button release for bounding box selection, junction drag end, waypoint drag end, and component drag end.
        
        Args:
            event: Mouse release event
        """
        # Handle junction drag end
        if self.dragging_junction:
            self._end_junction_drag()
            return
        
        # Handle waypoint drag end
        if self.dragging_waypoint:
            self._end_waypoint_drag()
            return
        
        # Handle component drag end
        if self.is_dragging:
            self._end_drag()
            return
        
        # Handle bounding box selection completion
        if self.selection_start and self.selection_box:
            # Get all components in selection box
            self._finalize_box_selection()
            
        # Clean up selection box
        if self.selection_box:
            self.design_canvas.canvas.delete(self.selection_box)
            self.selection_box = None
        self.selection_start = None
    
    def _finalize_box_selection(self):
        """Finalize bounding box selection by selecting all components in the box."""
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
        
        # Get bounding box coordinates
        bbox = self.design_canvas.canvas.coords(self.selection_box)
        if len(bbox) != 4:
            return
        
        x1, y1, x2, y2 = bbox
        # Normalize coordinates
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        # Clear previous selection
        self._clear_selection()
        
        # Select all components inside the box
        for component in page.components.values():
            comp_x, comp_y = component.position
            
            # Check if component center is inside selection box
            if min_x <= comp_x <= max_x and min_y <= comp_y <= max_y:
                self.selected_components.add(component.component_id)
                self.design_canvas.set_component_selected(component.component_id, True)
        
        # Update status and menu
        if len(self.selected_components) > 0:
            self.menu_bar.enable_edit_menu(has_selection=True)
            self.set_status(f"Selected {len(self.selected_components)} components")
        else:
            self.menu_bar.enable_edit_menu(has_selection=False)
            self.set_status("No components selected")
    
    # === Component Movement ===
    
    def _start_drag(self, canvas_x: float, canvas_y: float, page) -> None:
        """
        Start dragging selected components.
        
        Args:
            canvas_x: Starting canvas X coordinate
            canvas_y: Starting canvas Y coordinate
            page: Active page
        """
        # Block dragging in simulation mode
        if self.simulation_mode:
            return
        
        self.drag_start = (canvas_x, canvas_y)
        self.drag_components = {}
        
        # Store original positions of all selected components
        for component_id in self.selected_components:
            component = page.components.get(component_id)
            if component:
                self.drag_components[component_id] = component.position
    
    def _update_drag(self, canvas_x: float, canvas_y: float) -> None:
        """
        Update component positions during drag.
        
        Args:
            canvas_x: Current canvas X coordinate
            canvas_y: Current canvas Y coordinate
        """
        if not self.drag_start or not self.drag_components:
            return
        
        # Calculate drag delta
        start_x, start_y = self.drag_start
        delta_x = canvas_x - start_x
        delta_y = canvas_y - start_y
        
        # Only start dragging after minimum movement threshold
        if not self.is_dragging:
            if abs(delta_x) < 3 and abs(delta_y) < 3:
                return  # Not enough movement yet
            self.is_dragging = True
            self.set_status("Dragging... (Press Escape to cancel)")
        
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
        
        # Get grid size for snapping
        grid_size = self.settings.get_grid_size()
        snap_size = grid_size // 2  # Snap to half-grid (10px for 20px grid)
        
        # Update all dragged components
        for component_id, original_pos in self.drag_components.items():
            component = page.components.get(component_id)
            if component:
                # Calculate new position
                new_x = original_pos[0] + delta_x
                new_y = original_pos[1] + delta_y
                
                # Snap to grid
                snapped_x = round(new_x / snap_size) * snap_size
                snapped_y = round(new_y / snap_size) * snap_size
                
                # Update component position
                component.position = (snapped_x, snapped_y)
        
        # Re-render page to show updated positions
        self.design_canvas.set_page(page)
    
    def _end_drag(self) -> None:
        """End dragging operation."""
        if self.is_dragging:
            # Mark document as modified
            tab = self.file_tabs.get_active_tab()
            if tab:
                self.file_tabs.set_tab_modified(tab.tab_id, True)
            
            # Update properties panel if single component selected
            if len(self.selected_components) == 1:
                active_page_id = self.page_tabs.get_active_page_id()
                if active_page_id and tab and tab.document:
                    page = tab.document.get_page(active_page_id)
                    if page:
                        component_id = next(iter(self.selected_components))
                        component = page.components.get(component_id)
                        if component:
                            self.properties_panel.set_component(component)
            
            self.set_status(f"Moved {len(self.selected_components)} component(s)")
        
        # Reset drag state
        self.drag_start = None
        self.drag_components = {}
        self.is_dragging = False
    
    def _cancel_drag(self) -> None:
        """Cancel drag operation and restore original positions."""
        if not self.is_dragging:
            return
        
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
        
        # Restore original positions
        for component_id, original_pos in self.drag_components.items():
            component = page.components.get(component_id)
            if component:
                component.position = original_pos
        
        # Re-render page
        self.design_canvas.set_page(page)
        
        # Reset drag state
        self.drag_start = None
        self.drag_components = {}
        self.is_dragging = False
        
        self.set_status("Drag cancelled")
    
    def _move_selected_components(self, dx: int, dy: int) -> None:
        """
        Move selected components by specified delta.
        
        Args:
            dx: Delta X (pixels)
            dy: Delta Y (pixels)
        """
        if not self.selected_components:
            return
        
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
        
        # Move all selected components
        for component_id in self.selected_components:
            component = page.components.get(component_id)
            if component:
                current_x, current_y = component.position
                component.position = (current_x + dx, current_y + dy)
        
        # Mark as modified
        self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        # Re-render page
        self.design_canvas.set_page(page)
        
        # Update properties panel if single component selected
        if len(self.selected_components) == 1:
            component_id = next(iter(self.selected_components))
            component = page.components.get(component_id)
            if component:
                self.properties_panel.set_component(component)
    
    def _on_key_press(self, event) -> None:
        """
        Handle keyboard events for component movement, deletion, and wire/waypoint cancellation.
        
        Args:
            event: Key press event
        """
        # Cancel drag, wire, junction, or waypoint on Escape
        if event.keysym == 'Escape':
            if self.dragging_junction:
                self._cancel_junction_drag()
            elif self.dragging_waypoint:
                self._cancel_waypoint_drag()
            elif self.is_dragging:
                self._cancel_drag()
            elif self.wire_start_tab:
                # Cancel wire creation
                self._clear_wire_preview()
                self.wire_start_tab = None
                self.wire_temp_waypoints = []
                self.set_status("Wire cancelled.")
            return
        
        # Check if focus is in a text entry widget
        focused = self.root.focus_get()
        is_text_widget = focused and isinstance(focused, (tk.Entry, tk.Text))
        
        # Delete key (only when not in text entry)
        if event.keysym in ('Delete', 'BackSpace') and not is_text_widget:
            self._delete_selected()
            return 'break'
        
        # Arrow key movement (only when not in text entry)
        if event.keysym in ('Up', 'Down', 'Left', 'Right'):
            if is_text_widget:
                return
            
            # Get grid size
            grid_size = self.settings.get_grid_size()
            
            # Check if Shift is held for fine movement
            shift_held = (event.state & 0x0001) != 0
            move_amount = 1 if shift_held else grid_size
            
            # Calculate movement delta
            dx, dy = 0, 0
            if event.keysym == 'Up':
                dy = -move_amount
            elif event.keysym == 'Down':
                dy = move_amount
            elif event.keysym == 'Left':
                dx = -move_amount
            elif event.keysym == 'Right':
                dx = move_amount
            
            # Move selected components
            self._move_selected_components(dx, dy)
            
            return 'break'  # Prevent default behavior
    
    # === Clipboard Operations ===
    
    def _copy_selected(self) -> None:
        """
        Copy selected components to clipboard.
        """
        if not self.selected_components:
            self.set_status("No components selected to copy")
            return
        
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
        
        # Serialize selected components
        self.clipboard = []
        for component_id in self.selected_components:
            component = page.components.get(component_id)
            if component:
                # Serialize component to dictionary
                component_data = component.to_dict()
                self.clipboard.append(component_data)
        
        self.set_status(f"Copied {len(self.clipboard)} component(s) to clipboard")
    
    def _cut_selected(self) -> None:
        """
        Cut selected components (copy + delete).
        """
        if not self.selected_components:
            self.set_status("No components selected to cut")
            return
        
        # Copy first
        self._copy_selected()
        
        # Then delete
        self._delete_selected()
        
        self.set_status(f"Cut {len(self.clipboard)} component(s)")
    
    def _paste_clipboard(self) -> None:
        """
        Paste components from clipboard with new IDs and offset position.
        """
        if not self.clipboard:
            self.set_status("Clipboard is empty")
            return
        
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
        
        # Import component classes
        from components.switch import Switch
        from components.indicator import Indicator
        from components.dpdt_relay import DPDTRelay
        from components.vcc import VCC
        
        # Clear current selection
        self._clear_selection()
        
        # Paste offset (20px right and down from original)
        paste_offset = 20
        
        # Paste each component
        pasted_count = 0
        for component_data in self.clipboard:
            # Generate new unique ID
            new_id = tab.document.id_manager.generate_id()
            
            # Get component type (key is 'component_type' from to_dict())
            component_type = component_data.get('component_type', '')
            
            # Create new component based on type (all components need component_id and page_id)
            component = None
            if component_type == 'Switch':
                component = Switch(new_id, active_page_id)
            elif component_type == 'Indicator':
                component = Indicator(new_id, active_page_id)
            elif component_type == 'DPDTRelay':
                component = DPDTRelay(new_id, active_page_id)
            elif component_type == 'VCC':
                component = VCC(new_id, active_page_id)
            
            if component:
                # Restore properties from clipboard data
                if 'properties' in component_data:
                    component.properties = component_data['properties'].copy()
                
                # Apply offset to position
                # Position is stored as {'x': float, 'y': float} in to_dict()
                position_data = component_data.get('position', {'x': 0, 'y': 0})
                if isinstance(position_data, dict):
                    original_x = position_data.get('x', 0)
                    original_y = position_data.get('y', 0)
                else:
                    # Fallback for tuple format
                    original_x, original_y = position_data
                component.position = (original_x + paste_offset, original_y + paste_offset)
                
                # Restore rotation
                if 'rotation' in component_data:
                    component.rotation = component_data['rotation']
                
                # Add to page
                page.add_component(component)
                
                # Select pasted component
                self.selected_components.add(new_id)
                self.design_canvas.set_component_selected(new_id, True)
                
                pasted_count += 1
        
        # Mark document as modified
        self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        # Re-render page
        self.design_canvas.set_page(page)
        
        # Update properties panel and menu
        if len(self.selected_components) == 1:
            component_id = next(iter(self.selected_components))
            component = page.components.get(component_id)
            if component:
                self.properties_panel.set_component(component)
        else:
            self.properties_panel.set_component(None)
        
        self.menu_bar.enable_edit_menu(has_selection=len(self.selected_components) > 0)
        self.set_status(f"Pasted {pasted_count} component(s)")
    
    def _delete_selected(self) -> None:
        """
        Delete selected components and connected wires.
        Shows confirmation dialog before deletion.
        """
        # Block delete in simulation mode
        if self.simulation_mode:
            return
        
        if not self.selected_components:
            self.set_status("No components selected to delete")
            return
        
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
        
        # Count components to delete
        delete_count = len(self.selected_components)
        
        # Show confirmation dialog
        component_word = "component" if delete_count == 1 else "components"
        message = f"Delete {delete_count} {component_word}?"
        if delete_count == 1:
            # For single component, show the component type
            component_id = next(iter(self.selected_components))
            component = page.components.get(component_id)
            if component:
                message = f"Delete {component.__class__.__name__} ({component_id})?"
        
        result = messagebox.askyesno(
            "Confirm Deletion",
            message,
            icon=messagebox.WARNING
        )
        
        if not result:
            self.set_status("Deletion cancelled")
            return
        
        # Find wires connected to deleted components
        wires_to_delete = []
        for wire in page.wires.values():
            # Parse tab IDs to get component IDs
            # Tab ID format: {component_id}.{pin_name}.{tab_name}
            start_component_id = wire.start_tab_id.split('.')[0]
            end_component_id = wire.end_tab_id.split('.')[0]
            
            # If either end is connected to a deleted component, delete wire
            if start_component_id in self.selected_components or end_component_id in self.selected_components:
                wires_to_delete.append(wire.wire_id)
        
        # Delete wires
        for wire_id in wires_to_delete:
            page.remove_wire(wire_id)
        
        # Delete components
        for component_id in list(self.selected_components):
            page.remove_component(component_id)
        
        # Clear selection
        self._clear_selection()
        
        # Mark document as modified
        self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        # Re-render page
        self.design_canvas.set_page(page)
        
        self.set_status(f"Deleted {delete_count} component(s) and {len(wires_to_delete)} wire(s)")

    
    def _clear_wire_preview(self) -> None:
        """Clear wire preview lines from canvas."""
        for line in self.wire_preview_lines:
            self.design_canvas.canvas.delete(line)
        self.wire_preview_lines = []

