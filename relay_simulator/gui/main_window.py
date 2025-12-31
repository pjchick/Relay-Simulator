"""
Main Window for Relay Simulator III

Provides the MainWindow class which manages the primary application window,
including initialization, lifecycle, and basic window operations.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional, Dict, Tuple, Any
from pathlib import Path
import os
import tempfile
import math
import threading
import time
import traceback
import copy

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
from core.state import PinState
from fileio.document_loader import DocumentLoader
from simulation.simulation_engine import SimulationEngine
from components.base import Component
from diagnostics import UiWatchdog, get_logger


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

        # Single-step undo/redo (per tab): store one undo snapshot and one redo snapshot.
        self._undo_redo_state: Dict[str, Dict[str, Optional[Dict[str, Any]]]] = {}
        self._restoring_undo_redo = False

        # Track simulation mode (False = Design Mode, True = Simulation Mode)
        self.simulation_mode = False
        self.simulation_engine = None  # Will hold SimulationEngine instance when running

        # Simulation threading (prevents GUI "Not Responding" during long runs)
        self._simulation_stopping = False
        self._sim_run_lock = threading.Lock()
        self._sim_run_inflight = False
        self._sim_run_requested = False
        self._sim_thread: Optional[threading.Thread] = None
        
        # Track wire info dialog
        self._wire_info_dialog = None

        # Diagnostics
        self._logger = get_logger()
        self._ui_watchdog = UiWatchdog(self.root)
        self._ui_watchdog.start()

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

    def _rotate_point(self, x: float, y: float, cx: float, cy: float, angle_deg: float) -> Tuple[float, float]:
        """Rotate (x,y) around (cx,cy) by angle degrees."""
        if not angle_deg:
            return (x, y)
        angle_deg = angle_deg % 360
        if angle_deg == 0:
            return (x, y)

        rad = math.radians(angle_deg)
        tx = x - cx
        ty = y - cy
        rx = (tx * math.cos(rad)) - (ty * math.sin(rad))
        ry = (tx * math.sin(rad)) + (ty * math.cos(rad))
        return (rx + cx, ry + cy)
        
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
        self.menu_bar.set_callback('export_png', self._menu_export_canvas_png)
        self.menu_bar.set_callback('export_full_png', self._menu_export_full_canvas_png)
        self.menu_bar.set_callback('print_canvas', self._menu_print_canvas)
        self.menu_bar.set_callback('settings', self._menu_settings)
        self.menu_bar.set_callback('exit', self._on_closing)
        
        # Edit menu
        self.menu_bar.set_callback('undo', self._menu_undo)
        self.menu_bar.set_callback('redo', self._menu_redo)
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
        self.menu_bar.set_callback('toggle_properties', self._menu_toggle_properties)
        self.menu_bar.set_callback('toggle_properties', self._menu_toggle_properties)
        
        # Initialize menu states
        self.menu_bar.enable_edit_menu(has_selection=False)
        self.menu_bar.enable_undo_redo(can_undo=False, can_redo=False)
        self.menu_bar.enable_simulation_controls(is_running=False)

    def _ensure_undo_state_for_tab(self, tab_id: str) -> None:
        if tab_id not in self._undo_redo_state:
            self._undo_redo_state[tab_id] = {'undo': None, 'redo': None}

    def _get_active_tab_undo_state(self) -> Optional[Dict[str, Optional[Dict[str, Any]]]]:
        tab = self.file_tabs.get_active_tab()
        if not tab:
            return None
        self._ensure_undo_state_for_tab(tab.tab_id)
        return self._undo_redo_state.get(tab.tab_id)

    def _make_snapshot_for_tab(self, tab) -> Dict[str, Any]:
        active_page_id = None
        try:
            active_page_id = self.page_tabs.get_active_page_id()
        except Exception:
            active_page_id = None

        return {
            'document': copy.deepcopy(tab.document.to_dict()) if tab and tab.document else None,
            'active_page_id': active_page_id,
            'is_modified': bool(getattr(tab, 'is_modified', False)),
        }

    def _update_undo_redo_menu_state(self) -> None:
        if self.simulation_mode:
            self.menu_bar.enable_undo_redo(can_undo=False, can_redo=False)
            return
        state = self._get_active_tab_undo_state()
        if not state:
            self.menu_bar.enable_undo_redo(can_undo=False, can_redo=False)
            return
        can_undo = state.get('undo') is not None
        can_redo = state.get('redo') is not None
        self.menu_bar.enable_undo_redo(can_undo=can_undo, can_redo=can_redo)

    def _capture_undo_checkpoint(self) -> None:
        """Capture a pre-change snapshot for the active tab and clear redo."""
        if self.simulation_mode or self._restoring_undo_redo:
            return

        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return

        self._ensure_undo_state_for_tab(tab.tab_id)
        state = self._undo_redo_state[tab.tab_id]
        state['undo'] = self._make_snapshot_for_tab(tab)
        state['redo'] = None
        self._update_undo_redo_menu_state()

    def _restore_snapshot_to_active_tab(self, snapshot: Dict[str, Any]) -> None:
        """Restore a document snapshot into the currently active tab and refresh UI."""
        tab = self.file_tabs.get_active_tab()
        if not tab:
            return

        doc_dict = snapshot.get('document')
        if not isinstance(doc_dict, dict):
            return

        from components.factory import get_factory

        self._restoring_undo_redo = True
        try:
            restored_doc = Document.from_dict(doc_dict, component_factory=get_factory())
            tab.document = restored_doc

            # Rebind page tabs and restore active page if possible
            self.page_tabs.set_document(restored_doc)
            preferred_page_id = snapshot.get('active_page_id')
            if preferred_page_id and restored_doc.get_page(preferred_page_id):
                self.page_tabs.set_active_page(preferred_page_id)

            active_page_id = self.page_tabs.get_active_page_id()
            if active_page_id:
                page = restored_doc.get_page(active_page_id)
                if page:
                    self._set_canvas_page(page)
                    self.design_canvas.restore_canvas_state(page.canvas_x, page.canvas_y, page.canvas_zoom)

            # Restore modified marker
            if 'is_modified' in snapshot:
                self.file_tabs.set_tab_modified(tab.tab_id, bool(snapshot.get('is_modified')))

            # Clear selection/properties (selection ids may not exist after restore)
            self._clear_selection()
            self.properties_panel.set_component(None)
            self.menu_bar.enable_edit_menu(has_selection=False)

        finally:
            self._restoring_undo_redo = False

    def _on_undo_checkpoint_event(self, event=None) -> None:
        self._capture_undo_checkpoint()

    def _menu_undo(self) -> None:
        if self.simulation_mode:
            return

        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return

        self._ensure_undo_state_for_tab(tab.tab_id)
        state = self._undo_redo_state[tab.tab_id]
        snapshot = state.get('undo')
        if not snapshot:
            return

        # Save redo snapshot from current state
        state['redo'] = self._make_snapshot_for_tab(tab)

        # Restore undo snapshot
        self._restore_snapshot_to_active_tab(snapshot)

        # Single-step: undo is now consumed
        state['undo'] = None
        self._update_undo_redo_menu_state()
        self.set_status("Undo")

    def _menu_redo(self) -> None:
        if self.simulation_mode:
            return

        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return

        self._ensure_undo_state_for_tab(tab.tab_id)
        state = self._undo_redo_state[tab.tab_id]
        snapshot = state.get('redo')
        if not snapshot:
            return

        # Save undo snapshot from current state
        state['undo'] = self._make_snapshot_for_tab(tab)

        # Restore redo snapshot
        self._restore_snapshot_to_active_tab(snapshot)

        # Single-step: redo is now consumed
        state['redo'] = None
        self._update_undo_redo_menu_state()
        self.set_status("Redo")
        
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

    def _capture_visible_canvas_image(self):
        """Capture the currently visible canvas viewport as an image.

        Uses Pillow's ImageGrab, which is available on Windows/macOS.
        """
        try:
            from PIL import ImageGrab  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "Export/Print requires Pillow. Install it with: pip install Pillow"
            ) from e

        canvas = self.design_canvas.canvas
        
        # Ensure the window is fully updated and rendered
        try:
            # Force complete window update (not just idle tasks)
            self.root.update()
            canvas.update()
        except Exception:
            pass

        # Get canvas position on screen
        x0 = canvas.winfo_rootx()
        y0 = canvas.winfo_rooty()
        x1 = x0 + canvas.winfo_width()
        y1 = y0 + canvas.winfo_height()
        
        # Validate coordinates
        if x1 <= x0 or y1 <= y0:
            raise RuntimeError(
                f"Invalid canvas dimensions: width={x1-x0}, height={y1-y0}. "
                f"Canvas may not be visible or properly initialized."
            )
        
        # Capture the screen region
        image = ImageGrab.grab(bbox=(x0, y0, x1, y1))
        
        # Validate that we didn't capture a blank/black image
        # Sample pixels to check average brightness
        pixels = list(image.getdata())
        if pixels:
            # Sample every nth pixel for efficiency
            sample_step = max(1, len(pixels) // 100)
            sample_pixels = pixels[::sample_step]
            
            # Calculate average brightness
            total_brightness = 0
            for pixel in sample_pixels:
                if isinstance(pixel, tuple):
                    # RGB or RGBA
                    total_brightness += sum(pixel[:3]) / 3
                else:
                    # Grayscale
                    total_brightness += pixel
            
            avg_brightness = total_brightness / len(sample_pixels)
            
            # If image is very dark, it's likely a capture issue
            if avg_brightness < 5:
                raise RuntimeError(
                    "Captured image appears to be blank or black.\n\n"
                    "Possible causes:\n"
                    "- Canvas window is minimized or hidden\n"
                    "- Another window is covering the canvas\n"
                    "- Graphics driver issue\n\n"
                    "Try:\n"
                    "- Ensure the canvas is visible and not obscured\n"
                    "- Maximize the window\n"
                    "- Try exporting again"
                )
        
        return image

    def _menu_export_canvas_png(self) -> None:
        """Handle File > Export Canvas as PNG..."""
        active_tab = self.file_tabs.get_active_tab()

        suggested = "canvas"
        if active_tab and getattr(active_tab, 'filename', None):
            try:
                suggested = Path(active_tab.filename).stem
            except Exception:
                suggested = "canvas"

        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Canvas as PNG",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            defaultextension=".png",
            initialfile=f"{suggested}.png",
        )
        if not filepath:
            return

        try:
            image = self._capture_visible_canvas_image()
            image.save(filepath, format="PNG")
            self.set_status(f"Exported PNG: {Path(filepath).name}")
        except Exception as e:
            messagebox.showerror(
                "Export Failed",
                str(e),
                parent=self.root,
            )
            self.set_status("Export failed")

    def _menu_export_full_canvas_png(self) -> None:
        """Handle File > Export Full Canvas as PNG (1:1)..."""
        active_tab = self.file_tabs.get_active_tab()
        if not active_tab or not hasattr(active_tab, 'document'):
            messagebox.showinfo(
                "No Document",
                "No document is open to export.",
                parent=self.root,
            )
            return

        current_page = self.design_canvas.current_page
        if not current_page:
            messagebox.showinfo(
                "No Page",
                "No page is active to export.",
                parent=self.root,
            )
            return

        suggested = "canvas"
        if active_tab and getattr(active_tab, 'filename', None):
            try:
                suggested = Path(active_tab.filename).stem
            except Exception:
                suggested = "canvas"

        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Full Canvas as PNG (1:1 Scale)",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            defaultextension=".png",
            initialfile=f"{suggested}_full.png",
        )
        if not filepath:
            return

        try:
            image = self._render_full_canvas_image()
            image.save(filepath, format="PNG")
            self.set_status(f"Exported full canvas PNG: {Path(filepath).name}")
        except Exception as e:
            messagebox.showerror(
                "Export Failed",
                str(e),
                parent=self.root,
            )
            self.set_status("Export failed")

    def _get_canvas_bounds(self, padding=40):
        """Calculate the bounding box of all canvas items.
        
        Args:
            padding: Padding around content in pixels
            
        Returns:
            Tuple of (min_x, min_y, width, height) or None if no content
        """
        import math
        
        # Get bounding box of all canvas items
        # Tags used by renderers: component IDs, wire IDs, etc.
        bbox = self.design_canvas.canvas.bbox('all')
        if not bbox:
            return None
        
        min_x, min_y, max_x, max_y = bbox
        min_x = min_x - padding
        min_y = min_y - padding
        max_x += padding
        max_y += padding
        
        width = max(1, int(math.ceil(max_x - min_x)))
        height = max(1, int(math.ceil(max_y - min_y)))
        
        return (int(math.floor(min_x)), int(math.floor(min_y)), width, height)
    
    def _prepare_export_state(self):
        """Snapshot canvas state so it can be restored after exporting."""
        state = {
            "zoom": self.design_canvas.zoom_level,
            "xview": self.design_canvas.canvas.xview(),
            "yview": self.design_canvas.canvas.yview(),
            "scrollregion": self.design_canvas.canvas.cget('scrollregion'),
            "grid_items_state": [],
            "label_colors": []
        }
        
        # Hide grid items for export
        for item in self.design_canvas.grid_items:
            item_state = self.design_canvas.canvas.itemcget(item, 'state')
            state["grid_items_state"].append((item, item_state))
            self.design_canvas.canvas.itemconfig(item, state='hidden')
        
        # Change all label colors to black for export
        label_items = self.design_canvas.canvas.find_withtag('component_label')
        for item in label_items:
            original_fill = self.design_canvas.canvas.itemcget(item, 'fill')
            state["label_colors"].append((item, original_fill))
            self.design_canvas.canvas.itemconfig(item, fill='black')
        
        # Set to zoom 1.0 for export
        self.design_canvas.zoom_level = 1.0
        self.design_canvas.render_components()
        self.design_canvas.render_wires()
        self.design_canvas.render_junctions()
        self.design_canvas.canvas.xview_moveto(0)
        self.design_canvas.canvas.yview_moveto(0)
        
        return state
    
    def _restore_export_state(self, state):
        """Restore canvas state after an export attempt."""
        # Restore grid items visibility
        for item, item_state in state.get("grid_items_state", []):
            try:
                self.design_canvas.canvas.itemconfig(item, state=item_state)
            except:
                pass
        
        # Restore label colors
        for item, original_fill in state.get("label_colors", []):
            try:
                self.design_canvas.canvas.itemconfig(item, fill=original_fill)
            except:
                pass
        
        self.design_canvas.zoom_level = state.get("zoom", 1.0)
        
        xview = state.get("xview", (0, 1))
        yview = state.get("yview", (0, 1))
        self.design_canvas.canvas.xview_moveto(xview[0])
        self.design_canvas.canvas.yview_moveto(yview[0])
        
        scrollregion = state.get("scrollregion")
        if scrollregion:
            self.design_canvas.canvas.config(scrollregion=scrollregion)
        
        # Re-render at original zoom
        self.design_canvas.render_components()
        self.design_canvas.render_wires()
        self.design_canvas.render_junctions()
        
        self.root.update_idletasks()
    
    def _normalize_png_path(self, filename):
        """Ensure the output path ends with .png and directory exists."""
        path = Path(filename).expanduser()
        if path.suffix.lower() != '.png':
            path = path.with_suffix('.png')
        
        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        
        return str(path)
    
    def _extract_ps_bbox(self, ps_content):
        """Extract BoundingBox from PostScript content."""
        import re
        match = re.search(r"%%BoundingBox:\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)", ps_content)
        if match:
            return tuple(int(part) for part in match.groups())
        return None
    
    def _normalize_postscript_bbox(self, ps_content, bbox):
        """Translate PostScript so bounding box starts at (0,0).
        
        Returns:
            Tuple of (modified_ps_content, (shift_x, shift_y) or None)
        """
        import re
        
        min_x, min_y, max_x, max_y = bbox
        shift_x = -min(0, min_x)
        shift_y = -min(0, min_y)
        
        if shift_x == 0 and shift_y == 0:
            return ps_content, None
        
        # Inject translate command after %%EndProlog
        injection = f"{shift_x} {shift_y} translate\n"
        marker = "%%EndProlog\n"
        idx = ps_content.find(marker)
        if idx != -1:
            idx += len(marker)
            ps_content = ps_content[:idx] + injection + ps_content[idx:]
        else:
            ps_content = injection + ps_content
        
        # Update BoundingBox
        new_bbox = (min_x + shift_x, min_y + shift_y, max_x + shift_x, max_y + shift_y)
        ps_content = re.sub(
            r"%%BoundingBox:\s*-?\d+\s+-?\d+\s+-?\d+\s+-?\d+",
            f"%%BoundingBox: {new_bbox[0]} {new_bbox[1]} {new_bbox[2]} {new_bbox[3]}",
            ps_content,
            count=1
        )
        ps_content = re.sub(
            r"%%HiResBoundingBox:\s*-?[\d\.]+\s+-?[\d\.]+\s+-?[\d\.]+\s+-?[\d\.]+",
            f"%%HiResBoundingBox: {float(new_bbox[0]):.3f} {float(new_bbox[1]):.3f} {float(new_bbox[2]):.3f} {float(new_bbox[3]):.3f}",
            ps_content,
            count=1
        )
        
        return ps_content, (shift_x, shift_y)
    
    def _postscript_to_png(self, ps_data, output_path, width, height, ghostscript_hint=None):
        """Convert PostScript data to PNG using Ghostscript."""
        import subprocess
        
        ghostscript_executable = self._find_ghostscript_executable(ghostscript_hint)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ps', mode='w', encoding='utf-8') as temp_ps:
            temp_ps.write(ps_data)
            ps_path = temp_ps.name
        
        try:
            cmd = [
                ghostscript_executable,
                '-dSAFER',
                '-dBATCH',
                '-dNOPAUSE',
                '-sDEVICE=pngalpha',
                '-dGraphicsAlphaBits=4',
                '-dTextAlphaBits=4',
                '-r72',
                f'-g{width}x{height}',
                f'-sOutputFile={output_path}',
                ps_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode('utf-8', errors='ignore') if exc.stderr else ''
            raise RuntimeError(
                f"Ghostscript conversion failed.\n\n"
                f"Error: {stderr.strip()}\n\n"
                f"Please ensure Ghostscript is properly installed."
            ) from exc
        finally:
            if os.path.exists(ps_path):
                os.remove(ps_path)
    
    def _find_ghostscript_executable(self, user_hint=None):
        """Locate a Ghostscript executable using several strategies."""
        import shutil
        
        candidates = []
        seen = set()
        
        def add_candidate(path_like):
            if not path_like:
                return
            resolved = Path(path_like)
            if resolved.is_file():
                seen_key = resolved.resolve()
                if seen_key not in seen:
                    candidates.append(resolved)
                    seen.add(seen_key)
        
        def add_directory(directory):
            if not directory:
                return
            dir_path = Path(directory)
            if dir_path.is_dir():
                for exe_name in ('gswin64c.exe', 'gswin32c.exe', 'gs.exe'):
                    add_candidate(dir_path / 'bin' / exe_name)
                    add_candidate(dir_path / exe_name)
        
        # Try user hint first
        add_directory(user_hint)
        
        # Try environment variables
        add_directory(os.environ.get('GHOSTSCRIPT_PATH'))
        add_directory(os.environ.get('GHOSTSCRIPT_HOME'))
        
        # Try PATH
        for exe_name in ('gswin64c', 'gswin32c', 'gs'):
            which_path = shutil.which(exe_name)
            if which_path:
                add_candidate(which_path)
        
        # Try common installation directories
        possible_roots = [
            Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'gs',
            Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'gs'
        ]
        
        for root in possible_roots:
            if root.exists():
                for version_dir in sorted(root.iterdir(), reverse=True):
                    add_directory(version_dir)
        
        # Return first valid candidate
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        
        raise FileNotFoundError(
            "Ghostscript executable not found.\n\n"
            "Please install Ghostscript from:\n"
            "https://www.ghostscript.com/releases/gsdnld.html\n\n"
            "After installation, ensure the executable is in your PATH,\n"
            "or set the GHOSTSCRIPT_PATH environment variable."
        )
    
    def _render_full_canvas_image(self):
        """Render the full canvas content at 1:1 scale as an image.
        
        Exports the current canvas to PNG using PostScript conversion.
        """
        try:
            from PIL import Image
        except Exception as e:
            raise RuntimeError(
                "Export requires Pillow. Install it with: pip install Pillow"
            ) from e
        
        current_page = self.design_canvas.current_page
        if not current_page:
            raise RuntimeError("No active page to export")
        
        # Save current state
        export_state = self._prepare_export_state()
        
        bg_id = None
        try:
            # Update canvas
            self.root.update_idletasks()
            
            # Get bounds of all content
            bounds = self._get_canvas_bounds(padding=20)
            if not bounds:
                raise RuntimeError("No content found on current page to export")
            
            min_x, min_y, width, height = bounds
            
            # Limit size
            max_dimension = 10000
            if width > max_dimension or height > max_dimension:
                raise RuntimeError(
                    f"Canvas is too large to export: {width}x{height}\n"
                    f"Maximum dimension is {max_dimension} pixels."
                )
            
            # Add white background for export
            bg_id = self.design_canvas.canvas.create_rectangle(
                min_x, min_y,
                min_x + width, min_y + height,
                fill='white',
                outline='',
                tags='export_bg'
            )
            self.design_canvas.canvas.tag_lower(bg_id)
            self.design_canvas.canvas.update_idletasks()
            
            # Generate PostScript
            ps_data = self.design_canvas.canvas.postscript(
                colormode='color',
                x=min_x,
                y=min_y,
                width=width,
                height=height,
                pagewidth=f"{width}p",
                pageheight=f"{height}p"
            )
            
            # Normalize PostScript bounding box
            bbox = self._extract_ps_bbox(ps_data)
            if bbox:
                ps_data, adjusted = self._normalize_postscript_bbox(ps_data, bbox)
            
        finally:
            # Clean up
            if bg_id is not None:
                self.design_canvas.canvas.delete(bg_id)
            self._restore_export_state(export_state)
        
        # Convert to PNG
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_png:
            png_path = temp_png.name
        
        try:
            self._postscript_to_png(ps_data, png_path, width, height)
            image = Image.open(png_path)
            image_copy = image.copy()
            image.close()
            return image_copy
        finally:
            try:
                os.unlink(png_path)
            except:
                pass

    def _calculate_content_bounds(self):
        """Calculate the bounding box of all content on the current page.
        
        Returns:
            Tuple of (min_x, min_y, max_x, max_y) or (None, None, None, None) if no content
        """
        current_page = self.design_canvas.current_page
        if not current_page:
            return None, None, None, None

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        found_content = False

        # Check all components
        for component in current_page.components.values():
            found_content = True
            comp_x, comp_y = component.position
            
            # Get component dimensions (approximate)
            # Most components are around 40x40, but we'll use renderer if available
            width = height = 40
            renderer = self.design_canvas.renderers.get(component.component_id)
            if renderer and hasattr(renderer, 'get_bounds'):
                try:
                    bounds = renderer.get_bounds()
                    if bounds:
                        width, height = bounds
                except:
                    pass
            
            min_x = min(min_x, comp_x)
            min_y = min(min_y, comp_y)
            max_x = max(max_x, comp_x + width)
            max_y = max(max_y, comp_y + height)

        # Check all wires
        for wire in current_page.wires.values():
            found_content = True
            
            # Check waypoints
            if hasattr(wire, 'waypoints') and wire.waypoints:
                for waypoint in wire.waypoints.values():
                    wp_x, wp_y = waypoint.position
                    min_x = min(min_x, wp_x)
                    min_y = min(min_y, wp_y)
                    max_x = max(max_x, wp_x)
                    max_y = max(max_y, wp_y)
            
            # Check junctions
            if hasattr(wire, 'junctions') and wire.junctions:
                for junction in wire.junctions.values():
                    junc_x, junc_y = junction.position
                    min_x = min(min_x, junc_x)
                    min_y = min(min_y, junc_y)
                    max_x = max(max_x, junc_x)
                    max_y = max(max_y, junc_y)
            
            # Check start and end tab positions
            # We need to get the actual component positions for the tabs
            if hasattr(wire, 'start_tab_id') and wire.start_tab_id:
                # Find component that owns this tab
                for component in current_page.components.values():
                    if hasattr(component, 'pins'):
                        for pin in component.pins.values():
                            if hasattr(pin, 'tab_id') and pin.tab_id == wire.start_tab_id:
                                comp_x, comp_y = component.position
                                min_x = min(min_x, comp_x)
                                min_y = min(min_y, comp_y)
                                max_x = max(max_x, comp_x)
                                max_y = max(max_y, comp_y)
                                break
            
            if hasattr(wire, 'end_tab_id') and wire.end_tab_id:
                # Find component that owns this tab
                for component in current_page.components.values():
                    if hasattr(component, 'pins'):
                        for pin in component.pins.values():
                            if hasattr(pin, 'tab_id') and pin.tab_id == wire.end_tab_id:
                                comp_x, comp_y = component.position
                                min_x = min(min_x, comp_x)
                                min_y = min(min_y, comp_y)
                                max_x = max(max_x, comp_x)
                                max_y = max(max_y, comp_y)
                                break

        if not found_content:
            return None, None, None, None

        return min_x, min_y, max_x, max_y

    def _menu_print_canvas(self) -> None:
        """Handle File > Print Canvas..."""
        if os.name != 'nt':
            messagebox.showinfo(
                "Print Not Supported",
                "Printing is currently implemented for Windows only.\n\n"
                "You can still use File > Export Canvas as PNG... and print the image file.",
                parent=self.root,
            )
            return

        try:
            # Use the same rendering approach as full canvas export
            # This ensures white background, hidden grid, and black labels
            image = self._render_full_canvas_image()
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tmp_path = tmp.name
            tmp.close()

            image.save(tmp_path, format="PNG")

            # Ask the default associated app to print the image.
            os.startfile(tmp_path, "print")
            self.set_status("Sent canvas to printer")
        except Exception as e:
            messagebox.showerror(
                "Print Failed",
                str(e),
                parent=self.root,
            )
            self.set_status("Print failed")
        
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

        # Select all wires on the page
        for wire_id in page.wires.keys():
            self.selected_wires.add(wire_id)
            self.design_canvas.set_wire_selected(wire_id, True)

        # Select all junctions on the page
        for junction_id in page.junctions.keys():
            self.selected_junctions.add(junction_id)

        # Select all waypoints on the page
        for wire in page.wires.values():
            for waypoint_id in wire.waypoints.keys():
                self.selected_waypoints.add((wire.wire_id, waypoint_id))

        # Redraw so junction/waypoint selection is visible
        self._redraw_canvas()
        
        # Update properties panel (don't show individual component if multiple selected)
        total_selected = (
            len(self.selected_components)
            + len(self.selected_wires)
            + len(self.selected_junctions)
            + len(self.selected_waypoints)
        )
        if total_selected > 0:
            self.properties_panel.set_component(None)
            self.menu_bar.enable_edit_menu(has_selection=True)
            self.set_status(
                f"Selected all: {len(self.selected_components)} component(s), {len(self.selected_wires)} wire(s), "
                f"{len(self.selected_junctions)} junction(s), {len(self.selected_waypoints)} waypoint(s)"
            )
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
            
            # Set callback for relay timers to trigger simulation restart
            self.simulation_engine.set_gui_restart_callback(self._on_relay_timer_complete)
            
        except Exception as e:
            messagebox.showerror("Simulation Error", f"Failed to create simulation:\n{e}")
            self.simulation_engine = None
            return
        
        # Switch to Simulation Mode
        self.simulation_mode = True
        self._simulation_stopping = False
        
        # Update UI for simulation mode
        self.toolbox.pack_forget()  # Hide toolbox
        self.file_tabs.set_simulation_running(True)
        self.menu_bar.enable_simulation_controls(is_running=True)
        self._update_undo_redo_menu_state()
        self.set_status("Simulation Mode - Click switches to toggle. Press Shift+F5 to stop.")
        
        # Clear any active editing states
        self.placement_component = None
        self.wire_start_tab = None
        self.wire_temp_waypoints = []
        self._clear_wire_preview()
        self.selected_components.clear()
        
        # Disable canvas cursor
        self.design_canvas.canvas.config(cursor="")
        
        # Start simulation without blocking the Tk event loop
        self._run_simulation_step()
        
    def _menu_stop_simulation(self) -> None:
        """Handle Simulation > Stop Simulation (Shift+F5)."""
        if not self.simulation_mode or self._simulation_stopping:
            return

        self._simulation_stopping = True
        self.set_status("Stopping simulation...")

        # Request stop; do NOT block the UI thread waiting for completion.
        if self.simulation_engine:
            try:
                self.simulation_engine.stop()
            except Exception:
                pass

        self.root.after(50, self._poll_simulation_stopped)
    
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
                
                # Collect all tabs from component pins and RESET THEIR STATE
                # This ensures no state persists from previous simulation runs
                for pin in component.get_all_pins().values():
                    # Reset pin state to FLOAT
                    pin._state = PinState.FLOAT
                    for tab in pin.tabs.values():
                        # Reset tab state to FLOAT
                        tab._state = PinState.FLOAT
                        tabs[tab.tab_id] = tab
        
        # Build VNETs for each page
        vnet_builder = VnetBuilder(document.id_manager)
        for page in document.get_all_pages():
            page_vnets = vnet_builder.build_vnets_for_page(page)
            for vnet in page_vnets:
                vnets[vnet.vnet_id] = vnet

        # Resolve cross-page links (adds link_names onto the appropriate VNETs)
        try:
            from core.link_resolver import LinkResolver
            resolver = LinkResolver()
            resolver.resolve_links(document, list(vnets.values()))
        except Exception:
            # Links are optional; continue without failing simulation build
            pass
        
        # TODO: Build bridges for cross-page connections
        # This would require scanning for components with matching link_names
        # For Phase 15.2, we'll skip this (bridges remain empty for single-page circuits)
        
        return vnets, tabs, bridges, components
    
    def _on_relay_timer_complete(self):
        """
        Callback when a relay timer completes and switches contacts.
        
        This is called from the relay's timer thread, so we need to schedule
        the simulation restart on the GUI thread.
        """
        # Schedule simulation restart on GUI thread
        self.root.after(10, self._run_simulation_step)
    
    def _run_simulation_step(self):
        """
        Run one simulation step and schedule the next.
        This keeps the simulation running in the background.
        """
        if not self.simulation_mode or not self.simulation_engine or self._simulation_stopping:
            return

        self._schedule_simulation_run()

    def _schedule_simulation_run(self) -> None:
        """Run SimulationEngine.run() off the Tk thread, serializing invocations."""
        if not self.simulation_mode or not self.simulation_engine or self._simulation_stopping:
            return

        with self._sim_run_lock:
            if self._sim_run_inflight:
                self._sim_run_requested = True
                return
            self._sim_run_inflight = True
            self._sim_run_requested = False

        def worker():
            engine = self.simulation_engine
            if not engine:
                self.root.after(0, self._on_simulation_run_complete, None, "engine missing")
                return

            start = time.perf_counter()
            try:
                stats = engine.run()
                duration = time.perf_counter() - start
                self._logger.info(
                    "Simulation run complete: stable=%s iterations=%s total=%.3fs wall=%.3fs",
                    getattr(stats, 'stable', None),
                    getattr(stats, 'iterations', None),
                    getattr(stats, 'total_time', None),
                    duration,
                )
                self.root.after(0, self._on_simulation_run_complete, stats, None)
            except Exception as e:
                duration = time.perf_counter() - start
                self._logger.error("Simulation run crashed after %.3fs: %s", duration, e)
                self._logger.error("%s", traceback.format_exc())
                self.root.after(0, self._on_simulation_run_complete, None, str(e))

        self._sim_thread = threading.Thread(target=worker, name="SimulationRun", daemon=True)
        self._sim_thread.start()

    def _on_simulation_run_complete(self, stats, error: Optional[str]) -> None:
        with self._sim_run_lock:
            self._sim_run_inflight = False
            run_again = self._sim_run_requested
            self._sim_run_requested = False

        if not self.simulation_mode or self._simulation_stopping:
            return

        if error:
            self.set_status(f"Simulation Error: {error}")
            return

        if stats is None:
            self.set_status("Simulation Error: no statistics")
            return

        # Update visual feedback (GUI thread)
        try:
            self._update_simulation_visuals()
        except Exception as e:
            self._logger.error("Failed to update simulation visuals: %s", e)

        # Status
        try:
            if getattr(stats, 'stable', False):
                self.set_status(
                    f"Simulation Stable - {stats.iterations} iterations in {stats.time_to_stability:.3f}s"
                )
            elif getattr(stats, 'max_iterations_reached', False):
                self.set_status("Simulation Oscillating - Max iterations reached")
            elif getattr(stats, 'timeout_reached', False):
                self.set_status(f"Simulation Timeout - {stats.total_time:.3f}s")
            else:
                self.set_status("Simulation Running")
        except Exception:
            pass

        if run_again:
            self.root.after(10, self._run_simulation_step)

    def _poll_simulation_stopped(self) -> None:
        """Wait (without blocking the UI thread) for any in-flight simulation run to stop."""
        engine = self.simulation_engine
        if not engine:
            self._finalize_simulation_stop()
            return

        with self._sim_run_lock:
            inflight = self._sim_run_inflight

        # If the background thread is still running, keep polling.
        if inflight:
            self.root.after(50, self._poll_simulation_stopped)
            return

        self._finalize_simulation_stop()

    def _finalize_simulation_stop(self) -> None:
        engine = self.simulation_engine
        if engine:
            try:
                engine.shutdown()
                stats = engine.get_statistics()
                self._logger.info(
                    "Simulation stopped: iterations=%s components=%s stable=%s total=%.3fs",
                    stats.iterations,
                    stats.components_updated,
                    stats.stable,
                    stats.total_time,
                )
                print("Simulation Statistics:")
                print(f"  Iterations: {stats.iterations}")
                print(f"  Components Updated: {stats.components_updated}")
                print(f"  Time to Stability: {stats.time_to_stability:.3f}s")
                print(f"  Total Time: {stats.total_time:.3f}s")
                print(f"  Stable: {stats.stable}")
            except Exception as e:
                self._logger.error("Error shutting down simulation: %s", e)
            finally:
                self.simulation_engine = None

        # Switch back to Design Mode
        self.simulation_mode = False
        self._simulation_stopping = False

        # Restore UI for design mode - pack before design_canvas.frame
        self.toolbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1), before=self.design_canvas.frame)
        self.file_tabs.set_simulation_running(False)
        self.menu_bar.enable_simulation_controls(is_running=False)
        self._update_undo_redo_menu_state()
        self.set_status("Design Mode - Ready")

        # Redraw canvas to clear powered state visual feedback
        self._redraw_canvas()
    
    def _update_simulation_visuals(self):
        """Update visual feedback for powered components and wires."""
        
        # Get active page
        tab = self.file_tabs.get_active_tab()
        if tab and tab.document:
            active_page_id = self.page_tabs.get_active_page_id()
            if active_page_id:
                page = tab.document.get_page(active_page_id)
                if page:
                    # Re-render the entire page with simulation engine
                    start = time.perf_counter()
                    self._set_canvas_page(page)
                    elapsed = time.perf_counter() - start
                    if elapsed >= 0.25:
                        self._logger.warning(
                            "Slow simulation render: page=%s elapsed=%.3fs components=%s",
                            getattr(page, 'name', None),
                            elapsed,
                            len(page.get_all_components()) if hasattr(page, 'get_all_components') else None,
                        )
        
        # (debug logging removed)
    
    def _handle_switch_toggle(self, canvas_x: float, canvas_y: float):
        """Backward-compatible wrapper for simulation switch click handling."""
        self._handle_switch_interaction(canvas_x, canvas_y, action='press')

    def _handle_thumbwheel_interaction(self, canvas_x: float, canvas_y: float) -> bool:
        """Handle Thumbwheel button clicks in simulation mode.

        Returns True if a thumbwheel was clicked and handled.
        """
        # Get active page
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return False

        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return False

        page = tab.document.get_page(active_page_id)
        if not page:
            return False

        # Find a thumbwheel at click position
        clicked_component = None
        for component in page.get_all_components():
            if getattr(component, 'component_type', None) != 'Thumbwheel':
                continue

            x, y = component.position
            # Thumbwheel is 3x3 grid squares -> 60x60, so half-size is 30px
            if abs(canvas_x - x) <= 30 and abs(canvas_y - y) <= 30:
                clicked_component = component
                break

        if not clicked_component:
            return False

        # Determine which button row was clicked
        rel_y = canvas_y - clicked_component.position[1]
        if rel_y < -10:
            action = 'inc'
        elif rel_y > 10:
            action = 'dec'
        else:
            action = 'clear'

        try:
            changed = False
            if hasattr(clicked_component, 'interact') and callable(getattr(clicked_component, 'interact')):
                changed = bool(clicked_component.interact(action))

            if changed and self.simulation_engine:
                self.set_status("Thumbwheel updated")

                clicked_component.simulate_logic(
                    self.simulation_engine.vnet_manager,
                    self.simulation_engine.bridge_manager
                )

                self.simulation_engine.dirty_manager.mark_all_dirty()
                self._update_simulation_visuals()
                self.root.after(10, self._run_simulation_step)

        except Exception as e:
            print(f"Error interacting with thumbwheel: {e}")
            import traceback
            traceback.print_exc()
            self.set_status(f"Error interacting with thumbwheel: {e}")

        return True

    def _handle_memory_cell_interaction(self, canvas_x: float, canvas_y: float) -> bool:
        """Handle memory cell editing in design mode and simulation mode.
        
        Returns True if a memory cell was clicked and handled.
        """
        # Get active page
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return False
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return False
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return False
        
        # Check each Memory component
        for component in page.get_all_components():
            if component.component_type != "Memory":
                continue
            
            # Get renderer for this component
            renderer = self.design_canvas.renderers.get(component.component_id)
            if not renderer:
                continue
            
            # Check if click is on a memory cell
            try:
                from gui.renderers.memory_renderer import MemoryRenderer
                if isinstance(renderer, MemoryRenderer):
                    zoom = getattr(self.design_canvas, 'zoom_level', 1.0)
                    address = renderer.get_cell_at_position(canvas_x * zoom, canvas_y * zoom, zoom)
                    
                    if address is not None:
                        # Cell was clicked - prompt for new value
                        current_value = component.read_memory(address)
                        data_bits = component._get_data_bits()
                        addr_bits = component._get_address_bits()
                        
                        # Format current value as hex
                        hex_digits = (data_bits + 3) // 4
                        current_hex = f"{current_value:0{hex_digits}X}"
                        
                        # Prompt user for new value
                        from tkinter import simpledialog
                        addr_hex = f"{address:0{(addr_bits + 3) // 4}X}"
                        new_value_str = simpledialog.askstring(
                            "Edit Memory Cell",
                            f"Enter hex value for address 0x{addr_hex}\n"
                            f"(Current: 0x{current_hex}, Max: {(1 << data_bits) - 1:#X})",
                            initialvalue=current_hex
                        )
                        
                        if new_value_str is not None:
                            try:
                                # Parse hex value
                                new_value = int(new_value_str.strip(), 16)
                                
                                # Validate range
                                max_value = (1 << data_bits) - 1
                                if 0 <= new_value <= max_value:
                                    # In design mode, capture an undo checkpoint.
                                    self._capture_undo_checkpoint()

                                    # Update memory
                                    component.write_memory(address, new_value)

                                    # Update display / propagate
                                    if self.simulation_mode and self.simulation_engine:
                                        try:
                                            component.simulate_logic(
                                                self.simulation_engine.vnet_manager,
                                                self.simulation_engine.bridge_manager
                                            )
                                        except Exception:
                                            pass
                                        try:
                                            self.simulation_engine.dirty_manager.mark_all_dirty()
                                        except Exception:
                                            pass
                                        self._update_simulation_visuals()
                                        self.root.after(10, self._run_simulation_step)
                                    else:
                                        # Design mode: mark document modified and redraw.
                                        try:
                                            self.file_tabs.set_tab_modified(tab.tab_id, True)
                                        except Exception:
                                            pass
                                        self.design_canvas.set_page(page)
                                    self.set_status(f"Memory[0x{addr_hex}] = 0x{new_value:0{hex_digits}X}")
                                else:
                                    self.set_status(f"Error: Value must be 0-{max_value:#X}")
                            except ValueError:
                                self.set_status("Error: Invalid hex value")
                        
                        return True
            except Exception as e:
                print(f"Error editing memory cell: {e}")
                import traceback
                traceback.print_exc()
        
        return False

    def _handle_switch_interaction(self, canvas_x: float, canvas_y: float, action: str) -> None:
        """Handle switch press/toggle in simulation mode."""
        # Clear any previous press tracking; we only track the current mouse-down.
        self._pressed_switch_component = None

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
        
        # Find component at click position
        clicked_component = None
        for component in page.get_all_components():
            x, y = component.position
            distance = ((canvas_x - x)**2 + (canvas_y - y)**2)**0.5
            # Simple bounding box check (assuming components are roughly 40x40)
            if abs(canvas_x - x) <= 20 and abs(canvas_y - y) <= 20:
                clicked_component = component
                break
        
        if not clicked_component:
            return
        
        # Check if it's an interactive simulation component (Switch/Clock)
        if clicked_component.component_type not in ("Switch", "Clock"):
            return

        # Remember the pressed component so we can release it for pushbutton switches.
        # (Clock is toggle-only; release is a no-op.)
        try:
            self._pressed_switch_component = clicked_component
        except Exception:
            self._pressed_switch_component = None

        # Dispatch interaction based on the switch's mode
        try:
            changed = False
            if hasattr(clicked_component, 'interact') and callable(getattr(clicked_component, 'interact')):
                changed = bool(clicked_component.interact(action))
            elif hasattr(clicked_component, 'toggle_switch') and action in ('press', 'toggle', 'click'):
                # Fallback to legacy API
                clicked_component.toggle_switch()
                changed = True

            if changed:
                if clicked_component.component_type == 'Clock':
                    self.set_status("Clock updated")
                else:
                    self.set_status("Switch updated")

                if self.simulation_engine:
                    # Propagate switch output changes
                    clicked_component.simulate_logic(
                        self.simulation_engine.vnet_manager,
                        self.simulation_engine.bridge_manager
                    )

                    # Force re-evaluation
                    self.simulation_engine.dirty_manager.mark_all_dirty()

                    # Update visuals immediately
                    self._update_simulation_visuals()

                    # Re-run simulation to propagate change
                    self.root.after(10, self._run_simulation_step)
        except Exception as e:
            print(f"Error interacting with switch: {e}")
            import traceback
            traceback.print_exc()
            self.set_status(f"Error interacting with switch: {e}")

    def _handle_switch_release(self) -> None:
        """Handle mouse release for pushbutton switches in simulation mode."""
        clicked_component = getattr(self, '_pressed_switch_component', None)
        self._pressed_switch_component = None
        if not clicked_component:
            return

        if getattr(clicked_component, 'component_type', None) != "Switch":
            return

        try:
            changed = False
            if hasattr(clicked_component, 'interact') and callable(getattr(clicked_component, 'interact')):
                changed = bool(clicked_component.interact('release'))

            if changed and self.simulation_engine:
                clicked_component.simulate_logic(
                    self.simulation_engine.vnet_manager,
                    self.simulation_engine.bridge_manager
                )
                self.simulation_engine.dirty_manager.mark_all_dirty()
                self._update_simulation_visuals()
                self.root.after(10, self._run_simulation_step)
        except Exception as e:
            print(f"Error releasing switch: {e}")
            import traceback
            traceback.print_exc()
            self.set_status(f"Error releasing switch: {e}")
        
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
    
    def _menu_toggle_properties(self, visible: bool) -> None:
        """Handle View > Properties Panel toggle."""
        if visible:
            self.properties_panel.frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(1, 0))
        else:
            self.properties_panel.frame.pack_forget()
    
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
            command=self._paste_clipboard_from_context_menu
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
        
        self.context_menu.add_command(
            label="Select None",
            command=self._clear_selection
        )
    
    def _show_context_menu(self, event) -> None:
        """
        Show context menu at cursor position.
        
        Args:
            event: Right-click event
        """
        # Get world coordinates
        canvas_x, canvas_y = self.design_canvas.screen_to_world(event.x, event.y)

        # Remember where the context menu was opened, so "Paste" can anchor to the mouse.
        self._last_context_menu_world = (float(canvas_x), float(canvas_y))
        
        # Check if right-clicked on a waypoint
        waypoint_info = self._find_waypoint_at_position(canvas_x, canvas_y)
        if waypoint_info:
            self._show_waypoint_context_menu(event, waypoint_info)
            return
        
        # Update menu item states based on selection
        has_any_selection = (
            len(self.selected_components) > 0
            or len(self.selected_wires) > 0
            or len(self.selected_junctions) > 0
            or len(self.selected_waypoints) > 0
        )
        has_clipboard = self._clipboard_has_items()
        
        # Enable/disable menu items
        cut_index = 0
        copy_index = 1
        paste_index = 2
        delete_index = 4  # After separator
        
        self.context_menu.entryconfig(cut_index, state=tk.NORMAL if has_any_selection else tk.DISABLED)
        self.context_menu.entryconfig(copy_index, state=tk.NORMAL if has_any_selection else tk.DISABLED)
        self.context_menu.entryconfig(paste_index, state=tk.NORMAL if has_clipboard else tk.DISABLED)
        self.context_menu.entryconfig(delete_index, state=tk.NORMAL if has_any_selection else tk.DISABLED)
        
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

    def _paste_clipboard_from_context_menu(self) -> None:
        """Paste using the last context-menu mouse location as the anchor."""
        anchor = getattr(self, '_last_context_menu_world', None)
        try:
            self._paste_clipboard(anchor_world=anchor)
        finally:
            # Avoid stale anchors being accidentally reused elsewhere.
            self._last_context_menu_world = None
    
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
        self.page_tabs.on_pages_reordered = self._on_pages_reordered
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

        # Bind undo checkpoint events (emitted by editors before mutations)
        self.content_frame.bind('<<UndoCheckpoint>>', self._on_undo_checkpoint_event)
        self.root.bind('<<UndoCheckpoint>>', self._on_undo_checkpoint_event)
        
        # Track component placement mode
        self.placement_component = None  # Component type being placed
        self.placement_rotation = 0  # Rotation for placement (0, 90, 180, 270)
        
        # Track wire drawing state
        self.wire_start_tab = None  # Tab ID where wire starts
        self.wire_preview_lines = []  # Canvas items for wire preview (multiple segments with waypoints)
        self.wire_temp_waypoints = []  # Temporary waypoints during wire creation [(x, y), ...]
        
        # Track selected components
        self.selected_components = set()  # Set of selected component IDs
        self.selected_wires = set()  # Set of selected wire IDs
        self.selected_junctions = set()  # Set of selected junction IDs
        self.selected_waypoints = set()  # Set of (wire_id, waypoint_id)
        self.selection_box = None  # Rectangle for bounding box selection
        self.selection_start = None  # Start position for bounding box

        # Provide selection references to the canvas so redraws preserve highlight state
        self.design_canvas.selected_wires = self.selected_wires
        self.design_canvas.selected_junctions = self.selected_junctions
        self.design_canvas.selected_waypoints = self.selected_waypoints
        
        # Track component dragging
        self.drag_start = None  # (canvas_x, canvas_y) where drag started
        self.drag_components = {}  # {component_id: (original_x, original_y)}
        self.is_dragging = False  # True when actively dragging components
        self._pending_drag_start = None  # (canvas_x, canvas_y) click start for potential drag
        self._pending_drag_page = None  # Active page snapshot at mouse-down

        # Track Memory scrollbar dragging in simulation mode
        self._memory_scrollbar_renderer = None
        self._memory_scrollbar_zoom = 1.0
        
        # Track waypoint editing
        self.dragging_waypoint = None  # Waypoint being dragged (waypoint_id, wire_id)
        self.waypoint_drag_start = None  # Original position of waypoint being dragged
        self.hovered_waypoint = None  # Waypoint being hovered (wire_id, waypoint_id)
        
        # Track junction editing
        self.dragging_junction = None  # Junction ID being dragged
        self.junction_drag_start = None  # Original position of junction being dragged
        self._pending_junction_drag = None  # (junction_id, start_x, start_y) for click-vs-drag handling
        
        # Track right-click for context menu vs pan
        self.right_click_start = None  # Position where right-click started
        
        # Clipboard for copy/paste
        # Structured clipboard payload; see _copy_selected/_paste_clipboard.
        # (Backward compatible with older list-only clipboard.)
        self.clipboard = None
        
        # Inline text editor state
        self._inline_text_editor = None
        self._inline_text_editor_frame = None
        self._inline_text_component = None
        self._pending_text_click = None  # (component, canvas_x, canvas_y) for click vs drag detection
        
        # Text and Box component resize state
        self._resizing_component = None  # Can be Text or Box
        self._resize_corner = None
        self._resize_start_pos = None
        self._resize_original_size = None
        self._resize_border = None  # Canvas rectangle ID for alignment border
        self._drag_border = None  # Canvas rectangle ID for alignment border during drag
        
        # Create context menu
        self._create_context_menu()
        
        # Bind canvas click for component placement and wire drawing
        self.design_canvas.canvas.bind('<Button-1>', self._on_canvas_click)
        self.design_canvas.canvas.bind('<Double-Button-1>', self._on_canvas_double_click)
        self.design_canvas.canvas.bind('<Motion>', self._on_canvas_motion)
        self.design_canvas.canvas.bind('<ButtonRelease-1>', self._on_canvas_release)
        self.design_canvas.canvas.bind('<Button-3>', self._on_right_click)  # Right-click
        self.design_canvas.canvas.bind('<ButtonRelease-3>', self._on_right_release)  # Right-click release
        
        # Bind keyboard events for component movement
        self.root.bind('<KeyPress>', self._on_key_press)
        
        # Create initial untitled document (after canvas is created)
        initial_doc = Document()
        initial_doc.create_page("Page 1")
        initial_tab_id = self.file_tabs.add_untitled_tab(initial_doc)
        self._ensure_undo_state_for_tab(initial_tab_id)
        self._update_undo_redo_menu_state()
        
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
        try:
            if getattr(self, '_ui_watchdog', None):
                self._ui_watchdog.stop()
        except Exception:
            pass

        # Best-effort stop simulation without blocking exit.
        try:
            if getattr(self, 'simulation_engine', None):
                self.simulation_engine.stop()
        except Exception:
            pass

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
                    self._set_canvas_page(active_page)
                    
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

        # Update undo/redo enabled state for the new active tab
        self._ensure_undo_state_for_tab(tab_id)
        self._update_undo_redo_menu_state()
    
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

        # Drop undo/redo state for closed tab
        if tab_id in self._undo_redo_state:
            try:
                del self._undo_redo_state[tab_id]
            except Exception:
                pass
        self._update_undo_redo_menu_state()
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

        # Save current canvas state to the outgoing page before switching.
        # This lets each page remember its own zoom + scroll position.
        outgoing_page = getattr(self.design_canvas, 'current_page', None)
        if outgoing_page is not None and getattr(outgoing_page, 'page_id', None) and outgoing_page.page_id != page_id:
            canvas_x, canvas_y, zoom = self.design_canvas.save_canvas_state()
            outgoing_page.canvas_x = canvas_x
            outgoing_page.canvas_y = canvas_y
            outgoing_page.canvas_zoom = zoom
            
        # Get the page
        page = tab.document.get_page(page_id)
        if not page:
            return
            
        # Set page on canvas (will render components). In simulation mode we must
        # keep the simulation engine attached so powered/dim visuals are correct.
        self._set_canvas_page(page)
        
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

    def _on_pages_reordered(self, page_ids: list[str]) -> None:
        """Handle drag-reorder of pages in the tab bar."""
        tab = self.file_tabs.get_active_tab()
        if tab:
            self.file_tabs.set_tab_modified(tab.tab_id, True)
        self.set_status("Pages reordered")
    
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
        # Convert widget coordinates to world/model coordinates (unzoomed)
        canvas_x, canvas_y = self.design_canvas.screen_to_world(event.x, event.y)
        
        # In simulation mode, only allow switch toggling
        if self.simulation_mode:
            # Mouse-down: handle Thumbwheel buttons or Switch press/toggle.
            if self._handle_thumbwheel_interaction(canvas_x, canvas_y):
                return
            # Handle memory scrollbar interaction
            if self._handle_memory_scrollbar_interaction(canvas_x, canvas_y):
                return
            # Handle memory cell editing
            if self._handle_memory_cell_interaction(canvas_x, canvas_y):
                return
            
            # Check if clicked on a wire
            wire_clicked = self._find_wire_at_position(canvas_x, canvas_y)
            if wire_clicked:
                self._handle_wire_selection(event, wire_clicked)
                return
            
            self._handle_switch_interaction(canvas_x, canvas_y, action='press')
            return
        
        # Design mode only - handle component placement mode
        if self.placement_component:
            self._handle_component_placement(event)
            return
        
        # Check if clicked on a Text component resize handle
        if self._check_text_resize_handle_click(event):
            return

        # Design mode: allow editing Memory cells by clicking in the grid.
        # Do this before selection/wiring hit-testing so the cell click isn't stolen.
        if self._handle_memory_cell_interaction(canvas_x, canvas_y):
            return
        
        # Check if clicked on a junction
        junction_id = self._find_junction_at_position(canvas_x, canvas_y)
        if junction_id:
            # If drawing a wire, complete it at the junction
            if self.wire_start_tab:
                self._complete_wire_to_junction(junction_id)
                return
            else:
                # Not drawing a wire - allow either drag-to-move or click-to-start-wire.
                # We defer the decision until motion/release so a simple click can start a wire.
                self._pending_junction_drag = (junction_id, canvas_x, canvas_y)
                self.set_status("Junction: drag to move, release to start wire.")
                return
        
        # Check if clicked on a waypoint
        waypoint_info = self._find_waypoint_at_position(canvas_x, canvas_y)
        if waypoint_info:
            if self.wire_start_tab:
                # While drawing a wire: convert waypoint to a junction and complete to it
                self._convert_waypoint_to_junction_and_complete_wire(waypoint_info)
                return
            else:
                # Not drawing: begin waypoint drag
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
            wire_hit = self._find_wire_hit_at_position(canvas_x, canvas_y)
            if wire_hit:
                wire_id, segment_index, closest_point = wire_hit
                self._create_junction_and_complete_wire(closest_point[0], closest_point[1], wire_id, segment_index)
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
            # Not drawing a wire - wire click selects the wire
            wire_clicked = self._find_wire_at_position(canvas_x, canvas_y)
            if wire_clicked:
                self._handle_wire_selection(event, wire_clicked)
                return
        
        # Handle component selection and dragging
        self._handle_component_selection(event)
    
    def _on_canvas_double_click(self, event) -> None:
        """
        Handle canvas double-click for editing Text components.
        
        Args:
            event: Double-click event
        """
        # Don't handle in simulation mode
        if self.simulation_mode:
            return
        
        # Get canvas coordinates for hit-testing
        hit_canvas_x = self.design_canvas.canvas.canvasx(event.x)
        hit_canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
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
        
        # Find component at click position using canvas items
        clicked_component = None
        try:
            items = self.design_canvas.canvas.find_overlapping(
                hit_canvas_x, hit_canvas_y, hit_canvas_x, hit_canvas_y
            )
        except Exception:
            items = ()

        if items:
            # Prefer the top-most rendered item
            for item_id in reversed(items):
                try:
                    tags = set(self.design_canvas.canvas.gettags(item_id))
                except Exception:
                    continue

                # Only treat clicks on actual component body graphics
                if 'component' not in tags:
                    continue

                comp_tag = next((t for t in tags if isinstance(t, str) and t.startswith('component_')), None)
                if not comp_tag:
                    continue

                comp_id = comp_tag[len('component_'):]
                candidate = page.components.get(comp_id)
                if candidate:
                    clicked_component = candidate
                    break
        
        # Check if it's a Text component
        if clicked_component and clicked_component.component_type == 'Text':
            # Close any existing inline editor
            self._close_inline_text_editor()
            
            # Open inline editor for this Text component
            self._open_inline_text_editor(clicked_component, event.x, event.y)
    
    def _check_text_component_click(self, event) -> bool:
        """
        Check if a Text component was clicked and set up pending click state.
        This allows distinguishing between click (edit) and drag (move).
        
        Args:
            event: Click event
        
        Returns:
            True if a Text component was clicked
        """
        # Get canvas coordinates for hit-testing
        hit_canvas_x = self.design_canvas.canvas.canvasx(event.x)
        hit_canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Get world coordinates
        canvas_x, canvas_y = self.design_canvas.screen_to_world(event.x, event.y)
        
        # Get active page
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return False
        
        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return False
        
        page = tab.document.get_page(active_page_id)
        if not page:
            return False
        
        # Find component at click position using canvas items
        clicked_component = None
        try:
            items = self.design_canvas.canvas.find_overlapping(
                hit_canvas_x, hit_canvas_y, hit_canvas_x, hit_canvas_y
            )
        except Exception:
            items = ()

        if items:
            # Prefer the top-most rendered item
            for item_id in reversed(items):
                try:
                    tags = set(self.design_canvas.canvas.gettags(item_id))
                except Exception:
                    continue

                # Only treat clicks on actual component body graphics
                if 'component' not in tags:
                    continue

                comp_tag = next((t for t in tags if isinstance(t, str) and t.startswith('component_')), None)
                if not comp_tag:
                    continue

                comp_id = comp_tag[len('component_'):]
                candidate = page.components.get(comp_id)
                if candidate:
                    clicked_component = candidate
                    break
        
        # Check if it's a Text component
        if clicked_component and clicked_component.component_type == 'Text':
            # Store pending click - will open editor on release if not dragged
            self._pending_text_click = (clicked_component, canvas_x, canvas_y)
            return True
        
        return False
    
    def _open_inline_text_editor(self, component, screen_x: int, screen_y: int) -> None:
        """
        Open an inline text editor on the canvas for editing Text component.
        The editor is styled to match the component exactly.
        
        Args:
            component: Text component to edit
            screen_x: Screen X coordinate for editor position
            screen_y: Screen Y coordinate for editor position
        """
        from components.text import Text
        
        if not isinstance(component, Text):
            return
        
        # Store reference to component being edited
        self._inline_text_component = component
        
        # Get current text and properties
        current_text = component.properties.get('text', '')
        multiline = component.properties.get('multiline', False)
        font_size = component.properties.get('font_size', 12)
        width = component.properties.get('width', 200)
        height = component.properties.get('height', 40)
        color = component.properties.get('color', 'white')
        justify = component.properties.get('justify', 'left')
        has_border = component.properties.get('border', False)
        
        # Color mapping
        color_map = {
            'white': '#FFFFFF', 'gray': '#AAAAAA', 'red': '#FF6B6B',
            'green': '#4ECB71', 'blue': '#64B5F6', 'yellow': '#FFD93D',
            'orange': '#FF9F43', 'purple': '#A569BD', 'cyan': '#48C9B0',
            'pink': '#FD79A8'
        }
        fg_color = color_map.get(color, '#FFFFFF')
        
        # Calculate zoom for sizing
        zoom = self.design_canvas.zoom_level
        
        # Convert world coordinates to canvas coordinates
        comp_x, comp_y = component.position
        canvas_comp_x, canvas_comp_y = self.design_canvas.world_to_canvas(comp_x, comp_y)
        
        # Calculate scaled width and height
        scaled_width = width * zoom
        scaled_height = height * zoom
        
        # Calculate text position to match renderer positioning
        # The renderer centers the box at (comp_x, comp_y), then positions text with padding
        padding = 5 * zoom
        
        # Calculate the exact box boundaries
        box_x1 = canvas_comp_x - (scaled_width / 2)
        box_y1 = canvas_comp_y - (scaled_height / 2)
        box_x2 = canvas_comp_x + (scaled_width / 2)
        box_y2 = canvas_comp_y + (scaled_height / 2)
        
        if justify == 'left':
            # Text aligns to left edge of box with padding
            text_x = box_x1 + padding
            text_y = box_y1
            justify_anchor = tk.NW
        elif justify == 'right':
            # Text aligns to right edge of box with padding
            text_x = box_x2 - padding
            text_y = box_y1
            justify_anchor = tk.NE
        else:
            # Center alignment
            text_x = canvas_comp_x
            text_y = canvas_comp_y
            justify_anchor = tk.CENTER
        
        # Create a frame to hold the editor with exact pixel dimensions
        editor_frame = tk.Frame(
            self.design_canvas.canvas,
            bg=VSCodeTheme.BG_PRIMARY,
            width=int(scaled_width - 2 * padding),
            height=int(scaled_height),
            highlightthickness=0,
            borderwidth=0
        )
        editor_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Create text widget inside the frame
        if multiline:
            self._inline_text_editor = tk.Text(
                editor_frame,
                font=('Consolas', int(font_size * zoom)),
                bg=VSCodeTheme.BG_PRIMARY,
                fg=fg_color,
                insertbackground=fg_color,
                relief=tk.FLAT,
                borderwidth=0,
                highlightthickness=0,
                wrap=tk.WORD
            )
            self._inline_text_editor.pack(fill=tk.BOTH, expand=True)
            self._inline_text_editor.insert('1.0', current_text)
            self._inline_text_editor.focus_set()
            
            # Bind events
            self._inline_text_editor.bind('<Escape>', lambda e: self._close_inline_text_editor(save=False))
            self._inline_text_editor.bind('<FocusOut>', lambda e: self._close_inline_text_editor(save=True))
            # Return to save and close (Ctrl+Return for new lines in multiline mode)
            self._inline_text_editor.bind('<Return>', lambda e: self._close_inline_text_editor(save=True))
            # Ctrl+Return inserts a newline
            def insert_newline(e):
                self._inline_text_editor.insert(tk.INSERT, '\n')
                return 'break'
            self._inline_text_editor.bind('<Control-Return>', insert_newline)
        else:
            self._inline_text_editor = tk.Entry(
                editor_frame,
                font=('Consolas', int(font_size * zoom)),
                bg=VSCodeTheme.BG_PRIMARY,
                fg=fg_color,
                insertbackground=fg_color,
                relief=tk.FLAT,
                borderwidth=0,
                highlightthickness=0,
                justify=justify
            )
            self._inline_text_editor.pack(fill=tk.BOTH, expand=True, pady=int(scaled_height / 2 - font_size * zoom / 2))
            self._inline_text_editor.insert(0, current_text)
            self._inline_text_editor.select_range(0, tk.END)
            self._inline_text_editor.focus_set()
            
            # Bind events
            self._inline_text_editor.bind('<Return>', lambda e: self._close_inline_text_editor(save=True))
            self._inline_text_editor.bind('<Escape>', lambda e: self._close_inline_text_editor(save=False))
            self._inline_text_editor.bind('<FocusOut>', lambda e: self._close_inline_text_editor(save=True))
        
        # Store frame reference for cleanup
        self._inline_text_editor_frame = editor_frame
        
        # Position the frame to match the text rendering position exactly
        self.design_canvas.canvas.create_window(
            text_x, text_y,
            window=editor_frame,
            anchor=justify_anchor,
            tags=('inline_editor',)
        )
    
    def _close_inline_text_editor(self, save: bool = True) -> None:
        """
        Close the inline text editor and optionally save changes.
        
        Args:
            save: Whether to save the changes to the component
        """
        # Prevent double-close
        if not self._inline_text_editor or not self._inline_text_component:
            return
        
        # Store references before clearing
        editor = self._inline_text_editor
        component = self._inline_text_component
        frame = self._inline_text_editor_frame
        
        # Clear references immediately to prevent re-entry
        self._inline_text_editor = None
        self._inline_text_editor_frame = None
        self._inline_text_component = None
        
        # Get the edited text if saving
        if save:
            try:
                if isinstance(editor, tk.Text):
                    new_text = editor.get('1.0', 'end-1c')
                else:
                    new_text = editor.get()
                
                # Update component property
                old_text = component.properties.get('text', '')
                if new_text != old_text:
                    # Capture undo checkpoint before changing
                    self._capture_undo_checkpoint()
                    
                    component.properties['text'] = new_text
                    
                    # Mark document as modified
                    tab = self.file_tabs.get_active_tab()
                    if tab:
                        self.file_tabs.set_tab_modified(tab.tab_id, True)
                    
                    # Refresh the canvas to show updated text
                    if self.design_canvas.current_page:
                        self.design_canvas.set_page(self.design_canvas.current_page)
                    
                    self.set_status(f"Updated text: {new_text[:30]}...")
            except tk.TclError:
                # Widget already destroyed
                pass
        
        # Destroy the editor widget and frame
        try:
            if editor:
                editor.destroy()
        except tk.TclError:
            pass
        
        try:
            if frame:
                frame.destroy()
        except tk.TclError:
            pass
        
        # Remove the canvas window
        try:
            self.design_canvas.canvas.delete('inline_editor')
        except tk.TclError:
            pass
    
    def _check_text_resize_handle_click(self, event) -> bool:
        """
        Check if click is on a Text component resize handle and start resize if so.
        
        Args:
            event: Click event
            
        Returns:
            True if resize started, False otherwise
        """
        # Get canvas coordinates
        hit_canvas_x = self.design_canvas.canvas.canvasx(event.x)
        hit_canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
        # Find items at click position
        try:
            items = self.design_canvas.canvas.find_overlapping(
                hit_canvas_x, hit_canvas_y, hit_canvas_x, hit_canvas_y
            )
        except Exception:
            return False
        
        # Check if any item is a resize handle
        for item_id in reversed(items):
            try:
                tags = set(self.design_canvas.canvas.gettags(item_id))
            except Exception:
                continue
            
            if 'resize_handle' not in tags:
                continue
            
            # Found a resize handle - extract component ID and corner
            comp_tag = next((t for t in tags if t.startswith('resize_handle_')), None)
            corner_tag = next((t for t in tags if t.startswith('corner_')), None)
            
            if not comp_tag or not corner_tag:
                continue
            
            comp_id = comp_tag[len('resize_handle_'):]
            corner = corner_tag[len('corner_'):]
            
            # Get the component
            tab = self.file_tabs.get_active_tab()
            if not tab or not tab.document:
                return False
            
            active_page_id = self.page_tabs.get_active_page_id()
            if not active_page_id:
                return False
            
            page = tab.document.get_page(active_page_id)
            if not page:
                return False
            
            component = page.components.get(comp_id)
            if not component or component.component_type not in ('Text', 'Box'):
                return False
            
            # Start resizing
            canvas_x, canvas_y = self.design_canvas.screen_to_world(event.x, event.y)
            self._resizing_component = component
            self._resize_corner = corner
            self._resize_start_pos = (canvas_x, canvas_y)
            self._resize_original_size = (
                component.properties.get('width', 200),
                component.properties.get('height', 40)
            )
            self._resize_original_position = component.position
            
            # Calculate opposite corner position (world coordinates) - this stays fixed
            comp_x, comp_y = component.position
            width = component.properties.get('width', 200)
            height = component.properties.get('height', 40)
            half_w = width / 2
            half_h = height / 2
            
            # Get opposite corner coordinates
            opposite_corners = {
                'nw': (comp_x + half_w, comp_y + half_h),  # opposite is SE
                'ne': (comp_x - half_w, comp_y + half_h),  # opposite is SW
                'sw': (comp_x + half_w, comp_y - half_h),  # opposite is NE
                'se': (comp_x - half_w, comp_y - half_h),  # opposite is NW
            }
            self._resize_opposite_corner = opposite_corners.get(corner, component.position)
            
            # Set appropriate cursor
            cursor_map = {
                'nw': 'top_left_corner',
                'ne': 'top_right_corner',
                'sw': 'bottom_left_corner',
                'se': 'bottom_right_corner'
            }
            self.design_canvas.canvas.config(cursor=cursor_map.get(corner, 'cross'))
            
            return True
        
        return False
    
    def _update_text_component_resize(self, event) -> None:
        """
        Update Text component size during resize drag.
        
        Args:
            event: Motion event
        """
        if not self._resizing_component:
            return
        
        # Get current mouse position
        canvas_x, canvas_y = self.design_canvas.screen_to_world(event.x, event.y)
        
        # Calculate delta from start
        dx = canvas_x - self._resize_start_pos[0]
        dy = canvas_y - self._resize_start_pos[1]
        
        # Get original size
        orig_width, orig_height = self._resize_original_size
        
        # Calculate new size based on corner being dragged
        new_width = orig_width
        new_height = orig_height
        
        if self._resize_corner in ('ne', 'se'):
            new_width = orig_width + dx
        elif self._resize_corner in ('nw', 'sw'):
            new_width = orig_width - dx
        
        if self._resize_corner in ('sw', 'se'):
            new_height = orig_height + dy
        elif self._resize_corner in ('nw', 'ne'):
            new_height = orig_height - dy
        
        # Enforce minimum size based on component type
        if self._resizing_component.component_type == 'Text':
            new_width = max(50, new_width)
            new_height = max(20, new_height)
        else:  # Box
            new_width = max(50, new_width)
            new_height = max(50, new_height)
        
        # Calculate new center position to keep opposite corner fixed
        opp_x, opp_y = self._resize_opposite_corner
        half_w = new_width / 2
        half_h = new_height / 2
        
        # New center is offset from opposite corner by half the new size
        if self._resize_corner == 'nw':  # dragging NW, SE is fixed
            new_center_x = opp_x - half_w
            new_center_y = opp_y - half_h
        elif self._resize_corner == 'ne':  # dragging NE, SW is fixed
            new_center_x = opp_x + half_w
            new_center_y = opp_y - half_h
        elif self._resize_corner == 'sw':  # dragging SW, NE is fixed
            new_center_x = opp_x - half_w
            new_center_y = opp_y + half_h
        else:  # 'se' - dragging SE, NW is fixed
            new_center_x = opp_x + half_w
            new_center_y = opp_y + half_h
        
        # Update component properties
        self._resizing_component.properties['width'] = int(new_width)
        self._resizing_component.properties['height'] = int(new_height)
        self._resizing_component.position = (new_center_x, new_center_y)
        
        # Refresh canvas to show new size
        if self.design_canvas.current_page:
            self.design_canvas.set_page(self.design_canvas.current_page)
        
        # Draw alignment border AFTER re-render to ensure it appears on top
        zoom = self.design_canvas.zoom_level
        comp_x, comp_y = self._resizing_component.position
        canvas_comp_x, canvas_comp_y = self.design_canvas.world_to_canvas(comp_x, comp_y)
        
        half_w = (new_width * zoom) / 2
        half_h = (new_height * zoom) / 2
        
        x1 = canvas_comp_x - half_w
        y1 = canvas_comp_y - half_h
        x2 = canvas_comp_x + half_w
        y2 = canvas_comp_y + half_h
        
        # Remove old border if exists
        if self._resize_border:
            self.design_canvas.canvas.delete(self._resize_border)
        
        # Draw new border
        self._resize_border = self.design_canvas.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=VSCodeTheme.ACCENT_BLUE,
            width=2,
            dash=(5, 5),
            tags='resize_border'
        )
    
    def _finish_text_component_resize(self) -> None:
        """Finish resizing Text or Box component."""
        if not self._resizing_component:
            return
        
        # Store component reference before clearing state
        component = self._resizing_component
        
        # Remove alignment border
        if self._resize_border:
            self.design_canvas.canvas.delete(self._resize_border)
            self._resize_border = None
        
        # Capture undo checkpoint
        self._capture_undo_checkpoint()
        
        # Mark document as modified
        tab = self.file_tabs.get_active_tab()
        if tab:
            self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        # Reset cursor
        self.design_canvas.canvas.config(cursor="")
        
        # Clear resize state
        self._resizing_component = None
        self._resize_corner = None
        self._resize_start_pos = None
        self._resize_original_size = None
        self._resize_original_position = None
        self._resize_opposite_corner = None
        
        # Keep component selected
        if component:
            self.selected_components.add(component.component_id)
            self.design_canvas.set_component_selected(component.component_id, True)
            self.properties_panel.set_component(component)

    def _convert_waypoint_to_junction_and_complete_wire(self, waypoint_info: Tuple[str, str]) -> None:
        """Convert a clicked waypoint to a junction and complete current wire to it."""
        wire_id, waypoint_id = waypoint_info

        # Preconditions: design mode and currently drawing
        if self.simulation_mode or not self.wire_start_tab:
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

        # Resolve wire and waypoint
        host_wire = page.wires.get(wire_id)
        if not host_wire:
            return
        waypoint = host_wire.waypoints.get(waypoint_id)
        if not waypoint:
            return

        # Snapshot state before mutating the document
        self._capture_undo_checkpoint()

        # Create a new junction at waypoint position
        from core.wire import Junction, Wire, Waypoint
        junction_id = tab.document.id_manager.generate_id()
        junction = Junction(junction_id, (int(waypoint.position[0]), int(waypoint.position[1])))
        page.add_junction(junction)

        # Split waypoints around the clicked waypoint to preserve geometry
        # Keep those BEFORE on the host wire; move AFTER to the continuation wire
        waypoint_items = list(host_wire.waypoints.items())  # [(id, Waypoint)] in insertion order
        try:
            clicked_index = next(i for i, (wid, _) in enumerate(waypoint_items) if wid == waypoint_id)
        except StopIteration:
            clicked_index = None

        before_items = []
        after_items = []
        if clicked_index is not None:
            before_items = waypoint_items[:clicked_index]
            after_items = waypoint_items[clicked_index + 1:]

        # Rebuild host wire's waypoints with only the BEFORE group (preserve order)
        # This ensures the host wire path goes start → before_waypoints → junction
        host_wire.waypoints.clear()
        for wid, wp in before_items:
            host_wire.waypoints[wid] = wp

        # Split the host wire at the junction: host wire now ends at junction
        original_end = host_wire.end_tab_id
        host_wire.end_tab_id = junction_id

        # Continuation from junction to original end (if any)
        # Start at junction and route through after_waypoints to reach original endpoint
        if original_end:
            continuation_wire_id = tab.document.id_manager.generate_id()
            continuation_wire = Wire(continuation_wire_id, junction_id, original_end)
            # Move AFTER waypoints to the continuation wire to preserve routing from junction
            for wid, wp in after_items:
                continuation_wire.waypoints[wid] = wp
            page.add_wire(continuation_wire)

        # Complete the currently drawing wire to the new junction
        new_wire_id = tab.document.id_manager.generate_id()
        new_wire = Wire(new_wire_id, self.wire_start_tab, junction_id)
        if self.wire_temp_waypoints:
            for pos in self.wire_temp_waypoints:
                wp_id = tab.document.id_manager.generate_id()
                new_wp = Waypoint(wp_id, pos)
                new_wire.add_waypoint(new_wp)
        page.add_wire(new_wire)

        # Mark modified, clear drawing state, and re-render
        self.file_tabs.set_tab_modified(tab.tab_id, True)
        self._clear_wire_preview()
        self.wire_start_tab = None
        self.wire_temp_waypoints = []
        self.design_canvas.set_page(page)
        self.set_status("Converted waypoint to junction and connected wire.")

    def _handle_wire_selection(self, event, wire_id: str) -> None:
        """Handle clicking on a wire to select it (design mode only) or show info (simulation mode)."""
        print(f"_handle_wire_selection called: wire_id={wire_id}, simulation_mode={self.simulation_mode}")
        
        if self.simulation_mode:
            # In simulation mode, show wire VNET information
            print("Calling _show_wire_vnet_info")
            self._show_wire_vnet_info(wire_id)
            return

        ctrl_held = (event.state & 0x0004) != 0

        if ctrl_held:
            # Ctrl+Click toggles wire selection
            if wire_id in self.selected_wires:
                self.selected_wires.remove(wire_id)
                self.design_canvas.set_wire_selected(wire_id, False)
            else:
                self.selected_wires.add(wire_id)
                self.design_canvas.set_wire_selected(wire_id, True)
        else:
            # Regular click selects only this wire
            if (
                wire_id not in self.selected_wires
                or len(self.selected_wires) != 1
                or len(self.selected_components) != 0
            ):
                self._clear_selection()
                self.selected_wires.add(wire_id)
                self.design_canvas.set_wire_selected(wire_id, True)

        # Properties panel currently only supports components
        self.properties_panel.set_component(None)

        has_any_selection = len(self.selected_components) > 0 or len(self.selected_wires) > 0
        self.menu_bar.enable_edit_menu(has_selection=has_any_selection)

        if len(self.selected_wires) == 1 and len(self.selected_components) == 0:
            self.set_status(f"Selected wire ({wire_id})")
        elif len(self.selected_wires) > 1 and len(self.selected_components) == 0:
            self.set_status(f"Selected {len(self.selected_wires)} wires")
    
    def _show_wire_vnet_info(self, wire_id: str) -> None:
        """
        Show VNET information for a clicked wire in simulation mode.
        
        Args:
            wire_id: ID of the wire that was clicked
        """
        try:
            if not self.simulation_mode or not self.simulation_engine:
                print(f"Cannot show wire info: simulation_mode={self.simulation_mode}, engine={self.simulation_engine}")
                return
            
            # Get the active page and wire
            tab = self.file_tabs.get_active_tab()
            if not tab or not tab.document:
                print("No active tab or document")
                return
            
            active_page_id = self.page_tabs.get_active_page_id()
            if not active_page_id:
                print("No active page")
                return
            
            page = tab.document.get_page(active_page_id)
            if not page:
                print(f"Page not found: {active_page_id}")
                return
            
            wire = page.get_wire(wire_id)
            if not wire:
                print(f"Wire not found: {wire_id}")
                return
            
            print(f"Found wire: {wire_id}")
            
            # Get wire's connected tabs to find its VNET
            connected_tabs = wire.get_all_connected_tabs()
            if not connected_tabs:
                self.set_status("Wire has no connected tabs")
                print("Wire has no connected tabs")
                return
            
            print(f"Wire has {len(connected_tabs)} connected tabs: {connected_tabs}")
            
            # Get VNET for one of the wire's tabs
            first_tab_id = next(iter(connected_tabs))
            print(f"Looking up VNET for tab: {first_tab_id}")
            vnet = self.simulation_engine.vnet_manager.get_vnet_for_tab(first_tab_id)
            
            if not vnet:
                self.set_status("Wire is not connected to any VNET")
                print("VNET not found for tab")
                return
            
            print(f"Found VNET: {vnet.vnet_id} with {len(vnet.get_all_tabs())} tabs")
            
            # Check what's making this VNET HIGH
            if self.simulation_engine and hasattr(self.simulation_engine, 'bridge_manager'):
                # Check for bridges connecting to this VNET
                for bridge_id in vnet.get_all_bridges():
                    print(f"  VNET has bridge: {bridge_id}")
                    bridge = self.simulation_engine.bridge_manager.bridges.get(bridge_id)
                    if bridge:
                        print(f"    Bridge connects VNETs: {bridge.vnet_id1} <-> {bridge.vnet_id2}")
                        # Find the other VNET
                        other_vnet_id = bridge.vnet_id1 if bridge.vnet_id2 == vnet.vnet_id else bridge.vnet_id2
                        other_vnet = self.simulation_engine.vnet_manager.vnets.get(other_vnet_id)
                        if other_vnet:
                            from core.state import PinState
                            print(f"    Other VNET state: {other_vnet.state}")
                            if other_vnet.state == PinState.HIGH:
                                print(f"    ** This VNET is being driven via bridge from VNET {other_vnet_id} **")
            
            # Build VNET information dictionary
            vnet_info = self._build_vnet_info_dict(vnet, tab.document)
            
            print(f"Built VNET info with {len(vnet_info.get('components', []))} components")
            
            # If VNET is HIGH but no component is driving, check bridges
            from core.state import PinState
            if vnet.state == PinState.HIGH:
                has_driver = any(c.get('is_driving') for c in vnet_info.get('components', []))
                if not has_driver:
                    print("** VNET is HIGH but no direct driver found - checking bridges **")
                    if self.simulation_engine and hasattr(self.simulation_engine, 'bridge_manager'):
                        self._find_bridge_drivers(vnet, vnet_info, set())
            
            # Close existing dialog if any
            if self._wire_info_dialog and hasattr(self._wire_info_dialog, 'dialog'):
                try:
                    self._wire_info_dialog.dialog.destroy()
                except:
                    pass
                self._wire_info_dialog = None
            
            # Show dialog
            from gui.wire_info_dialog import WireInfoDialog
            print("Creating dialog...")
            self._wire_info_dialog = WireInfoDialog(self.root, wire_id, vnet_info)
            print("Dialog created")
            
        except Exception as e:
            print(f"Error showing wire VNET info: {e}")
            import traceback
            traceback.print_exc()
            self.set_status(f"Error: {e}")
    
    def _build_vnet_info_dict(self, vnet: VNET, document: Document) -> Dict[str, Any]:
        """
        Build a dictionary with VNET information for display.
        
        Args:
            vnet: VNET to get information about
            document: Document containing components
            
        Returns:
            Dictionary with VNET information
        """
        from core.state import PinState
        
        # Get VNET state
        state = vnet.state == PinState.HIGH
        
        # Collect component information for each tab in the VNET
        components_info = []
        seen_components = set()  # Track components we've already added
        
        all_tabs = vnet.get_all_tabs()
        print(f"VNET has {len(all_tabs)} tabs: {all_tabs}")
        
        # Check for links
        all_links = vnet.get_all_links()
        print(f"VNET has {len(all_links)} links: {all_links}")
        
        # Check for bridges
        all_bridges = vnet.get_all_bridges()
        print(f"VNET has {len(all_bridges)} bridges: {all_bridges}")
        
        for tab_id in all_tabs:
            print(f"Processing tab: {tab_id}")
            # Parse tab ID to get component ID
            # Tab ID format: component_id.pin_id.tab_id
            parts = tab_id.split('.')
            print(f"  Parts: {parts}, length: {len(parts)}")
            if len(parts) < 1:
                print(f"  Skipping - not enough parts")
                continue
            
            component_id = parts[0]
            print(f"  Component ID: {component_id}")
            
            # Skip if we've already processed this component
            if component_id in seen_components:
                print(f"  Skipping - already processed")
                continue
            
            seen_components.add(component_id)
            
            # Get component
            component = document.get_component(component_id)
            print(f"  Component found: {component}")
            if not component:
                print(f"  Skipping - component not found")
                continue
            
            # Get page information
            # Note: component.page_id might be outdated, so find the actual page containing this component
            page = None
            page_id = None
            for p in document.get_all_pages():
                if p.get_component(component_id):
                    page = p
                    page_id = p.page_id
                    break
            
            print(f"  Found component on page: {page_id if page else 'None'}")
            if page:
                print(f"  Page name: {page.name}")
            
            page_name = page.name if page else (component.page_id if hasattr(component, 'page_id') else 'Unknown')
            
            # Get component label
            label = component.properties.get('label', '')
            
            # Determine if component is driving the VNET
            # A component drives the VNET if any of its pins are in output mode and HIGH
            is_driving = self._is_component_driving_vnet(component, vnet)
            
            components_info.append({
                'page_id': page_id,
                'page_name': page_name,
                'component_id': component_id,
                'component_type': component.component_type,
                'label': label,
                'is_driving': is_driving
            })
        
        # Also add components connected via links
        for link_name in all_links:
            print(f"Processing link: {link_name}")
            linked_components = document.get_components_with_link_name(link_name)
            print(f"  Found {len(linked_components)} components with link '{link_name}'")
            
            for component in linked_components:
                component_id = component.component_id
                
                # Skip if we've already added this component via tabs
                if component_id in seen_components:
                    print(f"  Skipping {component_id} - already added via tabs")
                    continue
                
                seen_components.add(component_id)
                
                # Get page information
                page = None
                page_id = None
                for p in document.get_all_pages():
                    if p.get_component(component_id):
                        page = p
                        page_id = p.page_id
                        break
                
                page_name = page.name if page else (component.page_id if hasattr(component, 'page_id') else 'Unknown')
                
                # Get component label
                label = component.properties.get('label', '')
                
                # Determine if component is driving the VNET
                is_driving = self._is_component_driving_vnet(component, vnet)
                
                print(f"  Adding linked component: {component_id} on page {page_name}")
                
                components_info.append({
                    'page_id': page_id or 'Unknown',
                    'page_name': page_name,
                    'component_id': component_id,
                    'component_type': component.component_type,
                    'label': label,
                    'is_driving': is_driving
                })
        
        print(f"\n{'='*80}")
        print(f"=== RE-CHECKING ALL {len(components_info)} COMPONENTS FOR DRIVING STATUS ===")
        print(f"{'='*80}")
        # Re-check all components for driving status (in case we added better detection logic)
        for i, comp_info in enumerate(components_info):
            print(f"\n*** Re-checking component {i+1}/{len(components_info)}: {comp_info['component_id']} ({comp_info['component_type']}) ***")
            component = document.get_component(comp_info['component_id'])
            if component:
                print(f"  Component found, actual type={component.component_type}")
                if component.component_type == 'Diode':
                    print(f"  *** THIS IS A DIODE - SHOULD USE SPECIAL LOGIC ***")
                is_driving = self._is_component_driving_vnet(component, vnet)
                if is_driving != comp_info['is_driving']:
                    print(f"  *** UPDATED {comp_info['component_id']}: {comp_info['is_driving']} -> {is_driving} ***")
                    comp_info['is_driving'] = is_driving
                else:
                    print(f"  No change: is_driving={is_driving}")
            else:
                print(f"  *** ERROR: Component NOT found in document! ***")
        
        print(f"=== Re-check complete, returning vnet_info ===")
        return {
            'vnet_id': vnet.vnet_id,
            'state': state,
            'components': components_info
        }
    
    def _is_component_driving_vnet(self, component: Component, vnet: VNET) -> bool:
        """
        Determine if a component is driving the VNET (outputting HIGH).
        
        Args:
            component: Component to check
            vnet: VNET to check against
            
        Returns:
            True if component is driving the VNET
        """
        from core.state import PinState
        
        print(f"    Checking if {component.component_id} ({component.component_type}) is driving...")
        
        # VCC always drives HIGH
        if component.component_type == 'VCC':
            print(f"      VCC component - always DRIVING!")
            return True
        
        # For diodes, check if they're conducting by reading VNET states
        if component.component_type == 'Diode' and self.simulation_engine:
            pins_list = list(component.get_all_pins().values())
            print(f"      Diode has {len(pins_list)} pins")
            anode_high = False
            cathode_in_our_vnet = False
            
            for i, pin in enumerate(pins_list):
                print(f"        Pin {i} ({pin.pin_id}):")
                
                # Get VNET state for this pin
                pin_vnet = None
                pin_vnet_state = PinState.FLOAT
                if pin.tabs:
                    first_tab = next(iter(pin.tabs.values()))
                    pin_vnet = self.simulation_engine.vnet_manager.get_vnet_for_tab(first_tab.tab_id)
                    if pin_vnet:
                        pin_vnet_state = pin_vnet.state
                        print(f"          Pin VNET {pin_vnet.vnet_id}: state={pin_vnet_state}")
                
                # Check if this pin is in our target VNET
                in_target_vnet = any(vnet.has_tab(tab.tab_id) for tab in pin.tabs.values())
                
                if in_target_vnet:
                    print(f"          This is the CATHODE (in our target VNET)")
                    cathode_in_our_vnet = True
                else:
                    print(f"          This is the ANODE (not in our target VNET)")
                    if pin_vnet_state == PinState.HIGH:
                        print(f"          Anode VNET is HIGH!")
                        anode_high = True
            
            # Diode drives if anode is HIGH and cathode is in our VNET
            if anode_high and cathode_in_our_vnet:
                print(f"      *** DIODE IS DRIVING (anode HIGH -> cathode) ***")
                return True
            else:
                print(f"      Diode not driving (anode_high={anode_high}, cathode_in_vnet={cathode_in_our_vnet})")
        
        # For Link components, check if they're on a HIGH VNET (they conduct through the link)
        if component.component_type == 'Link' and self.simulation_engine:
            print(f"      Link component - checking VNET state...")
            for pin in component.get_all_pins().values():
                if pin.tabs:
                    first_tab = next(iter(pin.tabs.values()))
                    pin_vnet = self.simulation_engine.vnet_manager.get_vnet_for_tab(first_tab.tab_id)
                    if pin_vnet:
                        print(f"        Link pin VNET {pin_vnet.vnet_id}: state={pin_vnet.state}")
                        # Check if this link's VNET is HIGH and different from our target VNET
                        if pin_vnet.state == PinState.HIGH and pin_vnet.vnet_id != vnet.vnet_id:
                            print(f"        *** LINK IS DRIVING (from HIGH VNET {pin_vnet.vnet_id}) ***")
                            return True
        
        # Check each pin of the component
        for pin in component.get_all_pins().values():
            print(f"      Pin {pin.pin_id}: state={pin.state}")
            # Check if any tab of this pin is in the VNET
            has_tab_in_vnet = False
            for tab in pin.tabs.values():
                if vnet.has_tab(tab.tab_id):
                    has_tab_in_vnet = True
                    print(f"        Tab {tab.tab_id} is in VNET")
                    break
            
            if has_tab_in_vnet:
                # This pin is connected to the VNET
                # Check if the pin is outputting HIGH
                if pin.state == PinState.HIGH:
                    print(f"        Pin is HIGH - DRIVING!")
                    return True
                else:
                    print(f"        Pin state is {pin.state} - not driving")
                    
                    # Special case: Check if this component type is an output type
                    if component.component_type in ['Switch'] and self.simulation_engine:
                        # For switches, check their internal state
                        try:
                            if hasattr(component, 'is_on') and component.is_on:
                                print(f"        Component is ON - DRIVING!")
                                return True
                        except:
                            pass
        
        print(f"    Component is NOT driving")
        return False
    
    def _find_bridge_drivers(self, vnet: VNET, vnet_info: Dict, visited_vnets: set, depth: int = 0) -> None:
        """
        Recursively find components driving this VNET through bridges.
        
        Args:
            vnet: VNET to check
            vnet_info: VNET info dictionary to update
            visited_vnets: Set of already-visited VNET IDs
            depth: Recursion depth (for limiting search)
        """
        print(f"_find_bridge_drivers called: vnet_id={vnet.vnet_id}, depth={depth}")
        if depth > 5 or vnet.vnet_id in visited_vnets:
            print(f"  Skipping (depth={depth}, already_visited={vnet.vnet_id in visited_vnets})")
            return
        
        visited_vnets.add(vnet.vnet_id)
        indent = "  " * depth
        
        from core.state import PinState
        
        bridges = list(vnet.get_all_bridges())
        print(f"  VNET has {len(bridges)} bridges: {bridges}")
        
        # Check all bridges connected to this VNET
        for bridge_id in bridges:
            print(f"{indent}Checking bridge: {bridge_id}")
            if not hasattr(self.simulation_engine, 'bridge_manager'):
                continue
                
            bridge = self.simulation_engine.bridge_manager.bridges.get(bridge_id)
            if not bridge:
                print(f"{indent}  Bridge not found in manager")
                continue
            
            # Find the other VNET
            other_vnet_id = bridge.vnet_id1 if bridge.vnet_id2 == vnet.vnet_id else bridge.vnet_id2
            other_vnet = self.simulation_engine.vnet_manager.vnets.get(other_vnet_id)
            
            if not other_vnet:
                print(f"{indent}  Other VNET not found: {other_vnet_id}")
                continue
            
            print(f"{indent}  Other VNET {other_vnet_id}: state={other_vnet.state}")
            
            if other_vnet.state == PinState.HIGH:
                print(f"{indent}  ** Other VNET is HIGH - checking its components **")
                
                # Check components in the other VNET
                for tab_id in other_vnet.get_all_tabs():
                    parts = tab_id.split('.')
                    if len(parts) < 1:
                        continue
                    component_id = parts[0]
                    
                    tab = self.file_tabs.get_active_tab()
                    if not tab or not tab.document:
                        continue
                    
                    component = tab.document.get_component(component_id)
                    if not component:
                        continue
                    
                    # Check if this component is driving
                    for pin in component.get_all_pins().values():
                        for pin_tab in pin.tabs.values():
                            if other_vnet.has_tab(pin_tab.tab_id) and pin.state == PinState.HIGH:
                                print(f"{indent}    Found driver: {component_id} ({component.component_type}) via bridge!")
                                # Add note to vnet_info
                                if 'bridge_info' not in vnet_info:
                                    vnet_info['bridge_info'] = []
                                vnet_info['bridge_info'].append({
                                    'component_id': component_id,
                                    'component_type': component.component_type,
                                    'via_vnet': other_vnet_id,
                                    'via_bridge': bridge_id
                                })
                                return
                
                # Recursively check bridges on the other VNET
                self._find_bridge_drivers(other_vnet, vnet_info, visited_vnets, depth + 1)
    
    
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
        
        # Convert widget coordinates to world/model coordinates (unzoomed)
        canvas_x, canvas_y = self.design_canvas.screen_to_world(event.x, event.y)
        
        # Snap to grid
        grid_size = self.settings.get_grid_size()
        snap_size = grid_size // 2  # Snap to half-grid (10px for 20px grid)
        snapped_x = round(canvas_x / snap_size) * snap_size
        snapped_y = round(canvas_y / snap_size) * snap_size
        
        # Create component
        component_id = tab.document.id_manager.generate_id()
        
        # Use ComponentFactory to create component
        from components.factory import get_factory
        
        factory = get_factory()
        component = None
        
        try:
            component = factory.create_component(
                self.placement_component,
                component_id,
                page.page_id
            )
        except ValueError as e:
            self.set_status(f"Error creating component: {e}")
            return
        
        if component:
            # Snapshot state before mutating the document
            self._capture_undo_checkpoint()

            # Set position and rotation
            component.position = (snapped_x, snapped_y)
            component.rotation = self.placement_rotation
            
            # Add to page
            page.add_component(component)

            # Newly placed component becomes the active selection
            self._clear_selection()
            
            # Mark document as modified
            self.file_tabs.set_tab_modified(tab.tab_id, True)
            
            # Re-render components on canvas
            self.design_canvas.set_page(page)

            # Apply selection highlight (after re-render)
            self.selected_components.add(component_id)
            self.design_canvas.set_component_selected(component_id, True)
            self.properties_panel.set_component(component)
            self.menu_bar.enable_edit_menu(has_selection=True)
            
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
        # Handle Text/Box component resizing
        if self._resizing_component:
            self._update_text_component_resize(event)
            return
        
        # Get world coordinates first (needed for drag detection)
        canvas_x, canvas_y = self.design_canvas.screen_to_world(event.x, event.y)
        zoom = getattr(self.design_canvas, 'zoom_level', 1.0) or 1.0
        drag_threshold = 3.0 / zoom  # ~3 screen pixels

        # Junction click-vs-drag: if the user is holding Button-1 and moves enough,
        # treat it as a drag to move the junction.
        if self._pending_junction_drag and not self.dragging_junction:
            # Tk state bit for Button1 is 0x0100
            if (event.state & 0x0100) != 0:
                junction_id, start_x, start_y = self._pending_junction_drag
                if abs(canvas_x - start_x) >= drag_threshold or abs(canvas_y - start_y) >= drag_threshold:
                    self._pending_junction_drag = None
                    self._start_junction_drag(junction_id, start_x, start_y)
                    if self.dragging_junction:
                        self._update_junction_drag(canvas_x, canvas_y)
                    return

        # Simulation mode: drag Memory scrollbar thumb
        if self.simulation_mode and self._memory_scrollbar_renderer:
            # Only while Button-1 is held
            if (event.state & 0x0100) != 0:
                try:
                    zoom = getattr(self.design_canvas, 'zoom_level', 1.0) or 1.0
                    changed = bool(self._memory_scrollbar_renderer.handle_scrollbar_drag(
                        canvas_y * zoom,
                        self._memory_scrollbar_zoom
                    ))
                except Exception:
                    changed = False
                if changed:
                    self._update_simulation_visuals()
                return
        
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

        # If the user clicked a component (selection) but hasn't moved enough yet,
        # only enter drag mode once Button-1 is held and movement exceeds threshold.
        if self._pending_drag_start and not self.drag_start and not self.selection_start and not self.wire_start_tab:
            # Tk state bit for Button1 is 0x0100
            if (event.state & 0x0100) != 0:
                start_x, start_y = self._pending_drag_start
                delta_x = canvas_x - start_x
                delta_y = canvas_y - start_y
                if abs(delta_x) >= drag_threshold or abs(delta_y) >= drag_threshold:
                    page = self._pending_drag_page
                    self._pending_drag_start = None
                    self._pending_drag_page = None
                    if page:
                        self._start_drag(start_x, start_y, page)
                        self._update_drag(canvas_x, canvas_y)
                        return
        
        # Handle component dragging (check drag_start, not is_dragging)
        if self.drag_start:
            self._update_drag(canvas_x, canvas_y)
            return
        
        # Handle bounding box selection drawing
        if self.selection_start:
            # Draw selection box in canvas coords (zoomed)
            draw_x = canvas_x * zoom
            draw_y = canvas_y * zoom
            
            # Update or create selection box
            if self.selection_box:
                self.design_canvas.canvas.delete(self.selection_box)
            
            start_world_x, start_world_y = self.selection_start
            start_x = start_world_x * zoom
            start_y = start_world_y * zoom
            self.selection_box = self.design_canvas.canvas.create_rectangle(
                start_x, start_y, draw_x, draw_y,
                outline=VSCodeTheme.ACCENT_BLUE,
                width=2,
                dash=(5, 5)
            )
            return
        
        # Handle wire preview
        if not self.wire_start_tab:
            return
        
        # Draw wire preview in canvas coords (zoomed)
        cursor_x = canvas_x * zoom
        cursor_y = canvas_y * zoom
        
        # Clear old preview lines
        for line in self.wire_preview_lines:
            self.design_canvas.canvas.delete(line)
        self.wire_preview_lines = []
        
        # Get start position from tab
        start_pos = self._get_tab_canvas_position(self.wire_start_tab)
        if start_pos:
            start_pos = (start_pos[0] * zoom, start_pos[1] * zoom)
            # Build path: start -> waypoints -> cursor
            scaled_waypoints = [(wx * zoom, wy * zoom) for (wx, wy) in self.wire_temp_waypoints]
            path_points = [start_pos] + scaled_waypoints + [(cursor_x, cursor_y)]
            
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
            for wx, wy in scaled_waypoints:
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
        
        # Get world coordinates
        canvas_x, canvas_y = self.design_canvas.screen_to_world(event.x, event.y)
        
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
        
        # Check all components and their tabs
        for component in page.components.values():
            comp_x, comp_y = component.position
            rotation = getattr(component, 'rotation', 0) or 0
            flip_h = bool(getattr(component, 'properties', {}).get('flip_horizontal', False))
            flip_v = bool(getattr(component, 'properties', {}).get('flip_vertical', False))
            for pin in component.pins.values():
                # Memory uses internal per-bit bus pins that are intentionally hidden
                # from the user (renderer does not draw them). Exclude them from
                # tab hit-testing so wires can't accidentally connect to them.
                if getattr(component, 'component_type', None) == 'Memory':
                    pin_id = getattr(pin, 'pin_id', '')
                    if isinstance(pin_id, str) and ('.DATA_' in pin_id or '.ADDR_' in pin_id):
                        continue
                for tab_obj in pin.tabs.values():
                    tab_dx, tab_dy = tab_obj.relative_position

                    # Apply flip in local space (around component center) before rotation.
                    if flip_h:
                        tab_dx = -tab_dx
                    if flip_v:
                        tab_dy = -tab_dy

                    tab_x = comp_x + tab_dx
                    tab_y = comp_y + tab_dy
                    if rotation:
                        tab_x, tab_y = self._rotate_point(tab_x, tab_y, comp_x, comp_y, rotation)
                    
                    # x,y are world coordinates; keep a reasonable world hit radius.
                    hit_radius = VSCodeTheme.TAB_SIZE * 0.8  # Reduced radius for easier component selection
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
        rotation = getattr(component, 'rotation', 0) or 0
        flip_h = bool(getattr(component, 'properties', {}).get('flip_horizontal', False))
        flip_v = bool(getattr(component, 'properties', {}).get('flip_vertical', False))
        tab_dx, tab_dy = tab_obj.relative_position

        # Apply flip in local space (around component center) before rotation.
        if flip_h:
            tab_dx = -tab_dx
        if flip_v:
            tab_dy = -tab_dy

        x = comp_x + tab_dx
        y = comp_y + tab_dy
        if rotation:
            x, y = self._rotate_point(x, y, comp_x, comp_y, rotation)
        return (x, y)
    
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

        # Snapshot state before mutating the document
        self._capture_undo_checkpoint()
        
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

    def _create_junction_and_complete_wire(self, canvas_x: float, canvas_y: float, wire_id: str, segment_index: Optional[int] = None) -> None:
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

        # Snapshot state before mutating the document
        self._capture_undo_checkpoint()
        
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
        
        # Now split the clicked wire at the junction point.
        # Preserve waypoint routing by splitting the waypoint list at the clicked segment.
        original_end = clicked_wire.end_tab_id

        waypoint_items = list(clicked_wire.waypoints.items())
        waypoint_count = len(waypoint_items)

        if segment_index is None:
            # Fallback: determine closest segment on this wire
            start_pos = self._get_tab_canvas_position(clicked_wire.start_tab_id)
            end_pos = self._get_tab_canvas_position(original_end) if original_end else None
            if start_pos and (end_pos or clicked_wire.waypoints):
                path_points = [start_pos]
                for _, wp in waypoint_items:
                    path_points.append(wp.position)
                if end_pos:
                    path_points.append(end_pos)

                best_seg = 0
                best_dist = float('inf')
                for i in range(len(path_points) - 1):
                    x1, y1 = path_points[i]
                    x2, y2 = path_points[i + 1]
                    dist, _, _ = self._point_to_segment_distance_and_closest(canvas_x, canvas_y, x1, y1, x2, y2)
                    if dist < best_dist:
                        best_dist = dist
                        best_seg = i
                segment_index = best_seg
            else:
                segment_index = waypoint_count

        # Clamp segment index to valid range [0..waypoint_count]
        segment_index = max(0, min(int(segment_index), waypoint_count))

        before_items = waypoint_items[:segment_index]
        after_items = waypoint_items[segment_index:]

        # Modify the clicked wire to end at the new junction and keep the "before" waypoints
        clicked_wire.end_tab_id = junction_id
        clicked_wire.waypoints = dict(before_items)

        # Create a continuation wire from the junction to the original end point and move "after" waypoints
        if original_end:
            continuation_wire_id = tab.document.id_manager.generate_id()
            continuation_wire = Wire(continuation_wire_id, junction_id, original_end)
            for _, wp in after_items:
                continuation_wire.add_waypoint(wp)
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

        # Snapshot state before mutating the document
        self._capture_undo_checkpoint()
        
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
        
        hit = self._find_wire_hit_at_position(x, y)
        return hit[0] if hit else None

    def _find_wire_hit_at_position(self, x: float, y: float) -> Optional[Tuple[str, int, Tuple[float, float]]]:
        """Return the closest wire hit at (x, y) as (wire_id, segment_index, closest_point)."""
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return None

        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return None

        page = tab.document.get_page(active_page_id)
        if not page:
            return None

        zoom = getattr(self.design_canvas, 'zoom_level', 1.0) or 1.0
        hit_distance = 8.0 / zoom  # Keep hit tolerance ~constant in screen pixels
        best: Optional[Tuple[str, int, Tuple[float, float], float]] = None  # (wire_id, seg_index, (cx,cy), dist)

        for wire in page.wires.values():
            start_pos = self._get_tab_canvas_position(wire.start_tab_id)
            if not start_pos:
                continue

            end_pos = self._get_tab_canvas_position(wire.end_tab_id) if wire.end_tab_id else None
            if not end_pos and not wire.waypoints:
                continue

            path_points = [start_pos]
            for waypoint in wire.waypoints.values():
                path_points.append(waypoint.position)
            if end_pos:
                path_points.append(end_pos)

            for seg_index in range(len(path_points) - 1):
                x1, y1 = path_points[seg_index]
                x2, y2 = path_points[seg_index + 1]
                dist, cx, cy = self._point_to_segment_distance_and_closest(x, y, x1, y1, x2, y2)
                if dist <= hit_distance:
                    if best is None or dist < best[3]:
                        best = (wire.wire_id, seg_index, (cx, cy), dist)

        if not best:
            return None

        return (best[0], best[1], best[2])
    
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

    def _point_to_segment_distance_and_closest(self, px: float, py: float,
                                               x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float, float]:
        """Return (distance, closest_x, closest_y) from point to segment."""
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            dist = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
            return dist, x1, y1

        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        dist = ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
        return dist, closest_x, closest_y
    
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
        
        # Get world coordinates
        canvas_x, canvas_y = self.design_canvas.screen_to_world(event.x, event.y)
        
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
        
        zoom = getattr(self.design_canvas, 'zoom_level', 1.0) or 1.0
        hit_radius = 6.0 / zoom  # Keep hit tolerance ~constant in screen pixels
        
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
        
        zoom = getattr(self.design_canvas, 'zoom_level', 1.0) or 1.0
        hit_radius = 8.0 / zoom  # Keep hit tolerance ~constant in screen pixels
        
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
        
        # Get world coordinates (for selection box / dragging) and canvas coordinates
        # (for precise hit-testing against drawn shapes).
        canvas_x, canvas_y = self.design_canvas.screen_to_world(event.x, event.y)
        hit_canvas_x = self.design_canvas.canvas.canvasx(event.x)
        hit_canvas_y = self.design_canvas.canvas.canvasy(event.y)
        
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
        
        # Find component at click position using the actual drawn canvas items.
        # This avoids selecting a nearby component just because its bounding box overlaps.
        clicked_component = None
        try:
            items = self.design_canvas.canvas.find_overlapping(
                hit_canvas_x, hit_canvas_y, hit_canvas_x, hit_canvas_y
            )
        except Exception:
            items = ()

        if items:
            # Prefer the top-most rendered item.
            for item_id in reversed(items):
                try:
                    tags = set(self.design_canvas.canvas.gettags(item_id))
                except Exception:
                    continue

                # Only treat clicks on actual component body graphics as selection hits.
                # Labels and other non-body items should not steal selection.
                if 'component' not in tags:
                    continue

                comp_tag = next((t for t in tags if isinstance(t, str) and t.startswith('component_')), None)
                if not comp_tag:
                    continue

                comp_id = comp_tag[len('component_'):]
                candidate = page.components.get(comp_id)
                if candidate:
                    clicked_component = candidate
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

                # Do not start dragging on click; only start drag when the user
                # actually drags (mouse moves with Button-1 held).
                self._pending_drag_start = (canvas_x, canvas_y)
                self._pending_drag_page = page
            
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
                # Clicked on empty canvas: deselect everything (and allow box selection)
                if (
                    self.selected_components
                    or self.selected_wires
                    or self.selected_junctions
                    or self.selected_waypoints
                ):
                    self._clear_selection()

                # Start bounding box selection
                self.selection_start = (canvas_x, canvas_y)
                # Clear any pending component drag
                self._pending_drag_start = None
                self._pending_drag_page = None
            else:
                # Ctrl held but no component - do nothing
                pass
    
    def _clear_selection(self):
        """Clear all selected components and wires."""
        had_junction_or_waypoint_selection = bool(self.selected_junctions) or bool(self.selected_waypoints)

        for component_id in self.selected_components:
            self.design_canvas.set_component_selected(component_id, False)
        self.selected_components.clear()

        for wire_id in self.selected_wires:
            self.design_canvas.set_wire_selected(wire_id, False)
        self.selected_wires.clear()

        self.selected_junctions.clear()
        self.selected_waypoints.clear()

        # Redraw wires/junctions to remove selection markers
        if had_junction_or_waypoint_selection:
            self._redraw_canvas()

        self.properties_panel.set_component(None)
        self.menu_bar.enable_edit_menu(has_selection=False)
        self.set_status("Ready")
    
    def _on_canvas_release(self, event) -> None:
        """
        Handle mouse button release for bounding box selection, junction drag end, waypoint drag end, and component drag end.
        
        Args:
            event: Mouse release event
        """
        # Handle Text/Box component resize completion
        if self._resizing_component:
            self._finish_text_component_resize()
            return
        
        # In simulation mode, mouse-up releases pushbutton switches
        if self.simulation_mode:
            if self._memory_scrollbar_renderer:
                try:
                    self._memory_scrollbar_renderer.handle_scrollbar_release()
                except Exception:
                    pass
                self._memory_scrollbar_renderer = None
            self._handle_switch_release()
            return

        # If the user clicked a junction and released without dragging, start a wire from it.
        if self._pending_junction_drag and not self.dragging_junction and not self.wire_start_tab:
            junction_id, _, _ = self._pending_junction_drag
            self._pending_junction_drag = None
            self.wire_start_tab = junction_id
            self.set_status("Wire started. Click on a tab or junction to complete the wire.")
            return

        # Clear any pending junction click if it didn't become a drag.
        self._pending_junction_drag = None

        # If we never crossed the drag threshold, clear pending drag state
        self._pending_drag_start = None
        self._pending_drag_page = None

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

    def _handle_memory_scrollbar_interaction(self, canvas_x: float, canvas_y: float) -> bool:
        """Handle Memory scrollbar click/drag in simulation mode.

        Returns True if a scrollbar interaction was started/handled.
        """
        tab = self.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return False

        active_page_id = self.page_tabs.get_active_page_id()
        if not active_page_id:
            return False

        page = tab.document.get_page(active_page_id)
        if not page:
            return False

        zoom = getattr(self.design_canvas, 'zoom_level', 1.0)
        canvas_xz = canvas_x * zoom
        canvas_yz = canvas_y * zoom

        from gui.renderers.memory_renderer import MemoryRenderer

        for component in page.get_all_components():
            if component.component_type != "Memory":
                continue

            renderer = self.design_canvas.renderers.get(component.component_id)
            if not renderer or not isinstance(renderer, MemoryRenderer):
                continue

            target = renderer.on_click(canvas_xz, canvas_yz, zoom, simulation_mode=True)
            if target != 'scrollbar':
                continue

            handled = False
            try:
                handled = bool(renderer.handle_scrollbar_press(canvas_xz, canvas_yz, zoom))
            except Exception:
                handled = False

            if handled:
                self._memory_scrollbar_renderer = renderer
                self._memory_scrollbar_zoom = zoom
                self._update_simulation_visuals()
                return True

        return False

        # If we never crossed the drag threshold, clear pending drag state
        self._pending_drag_start = None
        self._pending_drag_page = None

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
        """Finalize bounding box selection by selecting all components, wires, junctions, and waypoints in the box."""
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
        
        # Get bounding box coordinates (canvas coords) and convert to world coords
        bbox = self.design_canvas.canvas.coords(self.selection_box)
        if len(bbox) != 4:
            return
        
        zoom = getattr(self.design_canvas, 'zoom_level', 1.0) or 1.0
        x1, y1, x2, y2 = bbox
        x1 /= zoom
        y1 /= zoom
        x2 /= zoom
        y2 /= zoom
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
        
        # Select all junctions inside the box
        for junction in page.junctions.values():
            jx, jy = junction.position
            if min_x <= jx <= max_x and min_y <= jy <= max_y:
                self.selected_junctions.add(junction.junction_id)
        
        # Select all wires and waypoints that are inside the box
        for wire in page.wires.values():
            # Check if any waypoint is in the box
            for waypoint in wire.waypoints.values():
                wx, wy = waypoint.position
                if min_x <= wx <= max_x and min_y <= wy <= max_y:
                    self.selected_waypoints.add((wire.wire_id, waypoint.waypoint_id))
            
            # Check if wire endpoints or segments are in the box
            # For simplicity, select wire if start or end point is in box
            start_pos = self._get_tab_canvas_position(wire.start_tab_id)
            end_pos = self._get_tab_canvas_position(wire.end_tab_id)
            
            wire_in_box = False
            if start_pos:
                sx, sy = start_pos
                if min_x <= sx <= max_x and min_y <= sy <= max_y:
                    wire_in_box = True
            
            if end_pos and not wire_in_box:
                ex, ey = end_pos
                if min_x <= ex <= max_x and min_y <= ey <= max_y:
                    wire_in_box = True
            
            if wire_in_box:
                self.selected_wires.add(wire.wire_id)
                self.design_canvas.set_wire_selected(wire.wire_id, True)
        
        # Redraw to show junction/waypoint selection
        if self.selected_junctions or self.selected_waypoints:
            self._redraw_canvas()
        
        # Update status and menu
        total_selected = (
            len(self.selected_components)
            + len(self.selected_wires)
            + len(self.selected_junctions)
            + len(self.selected_waypoints)
        )
        if total_selected > 0:
            self.menu_bar.enable_edit_menu(has_selection=True)
            self.set_status(
                f"Selected {len(self.selected_components)} component(s), {len(self.selected_wires)} wire(s), "
                f"{len(self.selected_junctions)} junction(s), {len(self.selected_waypoints)} waypoint(s)"
            )
        else:
            self.menu_bar.enable_edit_menu(has_selection=False)
            self.set_status("No items selected")
    
    # === Component Movement ===
    
    def _start_drag(self, canvas_x: float, canvas_y: float, page) -> None:
        """
        Start dragging selected components, junctions, and waypoints.
        
        Args:
            canvas_x: Starting canvas X coordinate
            canvas_y: Starting canvas Y coordinate
            page: Active page
        """
        # Block dragging in simulation mode
        if self.simulation_mode:
            return
        
        # Snap initial mouse position to 10px grid
        grid_size = self.settings.get_grid_size()
        snap_size = grid_size // 2  # 10px for 20px grid
        snapped_x = round(canvas_x / snap_size) * snap_size
        snapped_y = round(canvas_y / snap_size) * snap_size
        
        self.drag_start = (snapped_x, snapped_y)
        self.drag_components = {}
        self.drag_junctions = {}  # {junction_id: (original_x, original_y)}
        self.drag_waypoints = {}  # {(wire_id, waypoint_id): (original_x, original_y)}
        
        # Store original positions of all selected components
        for component_id in self.selected_components:
            component = page.components.get(component_id)
            if component:
                self.drag_components[component_id] = component.position
        
        # Store original positions of all selected junctions
        for junction_id in self.selected_junctions:
            junction = page.junctions.get(junction_id)
            if junction:
                self.drag_junctions[junction_id] = junction.position
        
        # Store original positions of all selected waypoints
        for wire_id, waypoint_id in self.selected_waypoints:
            wire = page.wires.get(wire_id)
            if wire:
                waypoint = wire.waypoints.get(waypoint_id)
                if waypoint:
                    self.drag_waypoints[(wire_id, waypoint_id)] = waypoint.position
    
    def _update_drag(self, canvas_x: float, canvas_y: float) -> None:
        """
        Update component positions during drag.
        
        Args:
            canvas_x: Current canvas X coordinate
            canvas_y: Current canvas Y coordinate
        """
        if not self.drag_start or not self.drag_components:
            return
        
        # Get grid size for snapping
        grid_size = self.settings.get_grid_size()
        snap_size = grid_size // 2  # 10px for 20px grid
        
        # Snap current mouse position to grid
        snapped_x = round(canvas_x / snap_size) * snap_size
        snapped_y = round(canvas_y / snap_size) * snap_size
        
        # Calculate drag delta from snapped positions
        start_x, start_y = self.drag_start
        delta_x = snapped_x - start_x
        delta_y = snapped_y - start_y
        
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
        
        # Update all dragged components - no individual snapping needed
        for component_id, original_pos in self.drag_components.items():
            component = page.components.get(component_id)
            if component:
                # Calculate new position from snapped delta
                new_x = original_pos[0] + delta_x
                new_y = original_pos[1] + delta_y
                
                # Update component position (no snapping)
                component.position = (new_x, new_y)
        
        # Update all dragged junctions
        if hasattr(self, 'drag_junctions'):
            for junction_id, original_pos in self.drag_junctions.items():
                junction = page.junctions.get(junction_id)
                if junction:
                    # Calculate new position from snapped delta
                    new_x = original_pos[0] + delta_x
                    new_y = original_pos[1] + delta_y
                    
                    # Update junction position (no snapping)
                    junction.position = (new_x, new_y)
        
        # Update all dragged waypoints
        if hasattr(self, 'drag_waypoints'):
            for (wire_id, waypoint_id), original_pos in self.drag_waypoints.items():
                wire = page.wires.get(wire_id)
                if wire:
                    waypoint = wire.waypoints.get(waypoint_id)
                    if waypoint:
                        # Calculate new position from snapped delta
                        new_x = original_pos[0] + delta_x
                        new_y = original_pos[1] + delta_y
                        
                        # Update waypoint position (no snapping)
                        waypoint.position = (new_x, new_y)
        
        # Re-render page to show updated positions
        self.design_canvas.set_page(page)
        
        # Draw alignment border for Text and Box components being dragged
        # (drawn AFTER re-render to ensure it appears on top)
        if len(self.drag_components) == 1:
            component_id = next(iter(self.drag_components))
            component = page.components.get(component_id)
            if component and component.component_type in ('Text', 'Box'):
                zoom = self.design_canvas.zoom_level
                comp_x, comp_y = component.position
                canvas_comp_x, canvas_comp_y = self.design_canvas.world_to_canvas(comp_x, comp_y)
                
                # Get dimensions based on component type
                if component.component_type == 'Text':
                    width = component.properties.get('width', 200)
                    height = component.properties.get('height', 40)
                else:  # Box
                    width = component.properties.get('width', 200)
                    height = component.properties.get('height', 150)
                
                half_w = (width * zoom) / 2
                half_h = (height * zoom) / 2
                
                x1 = canvas_comp_x - half_w
                y1 = canvas_comp_y - half_h
                x2 = canvas_comp_x + half_w
                y2 = canvas_comp_y + half_h
                
                # Remove old border if exists
                if self._drag_border:
                    self.design_canvas.canvas.delete(self._drag_border)
                
                # Draw new border
                self._drag_border = self.design_canvas.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline=VSCodeTheme.ACCENT_BLUE,
                    width=2,
                    dash=(5, 5),
                    tags='drag_border'
                )
        else:
            # Clear drag border if dragging multiple items
            if self._drag_border:
                self.design_canvas.canvas.delete(self._drag_border)
                self._drag_border = None
    
    def _end_drag(self) -> None:
        """End dragging operation."""
        # Remove drag alignment border
        if self._drag_border:
            self.design_canvas.canvas.delete(self._drag_border)
            self._drag_border = None
        
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
            
            # Re-apply selection highlight after drag
            for component_id in self.selected_components:
                self.design_canvas.set_component_selected(component_id, True)
            
            total_moved = len(self.selected_components) + len(self.selected_junctions) + len(self.selected_waypoints)
            self.set_status(f"Moved {total_moved} item(s)")
        
        # Reset drag state
        self.drag_start = None
        self.drag_components = {}
        if hasattr(self, 'drag_junctions'):
            self.drag_junctions = {}
        if hasattr(self, 'drag_waypoints'):
            self.drag_waypoints = {}
        self.is_dragging = False
    
    def _cancel_drag(self) -> None:
        """Cancel drag operation and restore original positions."""
        # Remove drag alignment border
        if self._drag_border:
            self.design_canvas.canvas.delete(self._drag_border)
            self._drag_border = None
        
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
        
        # Restore original positions of components
        for component_id, original_pos in self.drag_components.items():
            component = page.components.get(component_id)
            if component:
                component.position = original_pos
        
        # Restore original positions of junctions
        if hasattr(self, 'drag_junctions'):
            for junction_id, original_pos in self.drag_junctions.items():
                junction = page.junctions.get(junction_id)
                if junction:
                    junction.position = original_pos
        
        # Restore original positions of waypoints
        if hasattr(self, 'drag_waypoints'):
            for (wire_id, waypoint_id), original_pos in self.drag_waypoints.items():
                wire = page.wires.get(wire_id)
                if wire:
                    waypoint = wire.waypoints.get(waypoint_id)
                    if waypoint:
                        waypoint.position = original_pos
        
        # Re-render page
        self.design_canvas.set_page(page)
        
        # Reset drag state
        self.drag_start = None
        self.drag_components = {}
        if hasattr(self, 'drag_junctions'):
            self.drag_junctions = {}
        if hasattr(self, 'drag_waypoints'):
            self.drag_waypoints = {}
        self.is_dragging = False
        
        self.set_status("Drag cancelled")
    
    def _move_selected_components(self, dx: int, dy: int) -> None:
        """
        Move selected components, junctions, and waypoints by specified delta.
        
        Args:
            dx: Delta X (pixels)
            dy: Delta Y (pixels)
        """
        if not self.selected_components and not self.selected_junctions and not self.selected_waypoints:
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
        
        # Move all selected junctions
        for junction_id in self.selected_junctions:
            junction = page.junctions.get(junction_id)
            if junction:
                current_x, current_y = junction.position
                junction.position = (current_x + dx, current_y + dy)
        
        # Move all selected waypoints
        for wire_id, waypoint_id in self.selected_waypoints:
            wire = page.wires.get(wire_id)
            if wire:
                waypoint = wire.waypoints.get(waypoint_id)
                if waypoint:
                    current_x, current_y = waypoint.position
                    waypoint.position = (current_x + dx, current_y + dy)
        
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

    def _clipboard_has_items(self) -> bool:
        clip = getattr(self, 'clipboard', None)
        if not clip:
            return False
        if isinstance(clip, list):
            return len(clip) > 0
        if isinstance(clip, dict):
            return bool(clip.get('components') or clip.get('wires') or clip.get('junctions'))
        return False

    @staticmethod
    def _tab_pos_tuple(tab_dict) -> tuple[float, float]:
        if not isinstance(tab_dict, dict):
            return (0.0, 0.0)
        pos = tab_dict.get('position', {})
        if not isinstance(pos, dict):
            return (0.0, 0.0)
        try:
            return (float(pos.get('x', 0.0)), float(pos.get('y', 0.0)))
        except Exception:
            return (0.0, 0.0)

    def _build_tab_id_map(self, old_component_data: dict, new_component) -> dict[str, str]:
        """Map old tab_ids from serialized component -> new component tab_ids.

        Uses tab relative positions (dx,dy) to match.
        """
        mapping: dict[str, str] = {}
        if not isinstance(old_component_data, dict):
            return mapping

        old_pins = old_component_data.get('pins', [])
        if not isinstance(old_pins, list):
            return mapping

        # Build a lookup from new tab relative positions -> tab_id.
        new_pos_to_tab_id: dict[tuple[float, float], str] = {}
        try:
            for pin in getattr(new_component, 'pins', {}).values():
                for tab in getattr(pin, 'tabs', {}).values():
                    pos = getattr(tab, 'relative_position', (0.0, 0.0))
                    key = (round(float(pos[0]), 3), round(float(pos[1]), 3))
                    new_pos_to_tab_id.setdefault(key, tab.tab_id)
        except Exception:
            return mapping

        for old_pin in old_pins:
            if not isinstance(old_pin, dict):
                continue
            for old_tab in (old_pin.get('tabs', []) or []):
                if not isinstance(old_tab, dict):
                    continue
                old_tab_id = old_tab.get('tab_id')
                if not isinstance(old_tab_id, str) or not old_tab_id:
                    continue
                pos = self._tab_pos_tuple(old_tab)
                key = (round(float(pos[0]), 3), round(float(pos[1]), 3))
                new_tab_id = new_pos_to_tab_id.get(key)
                if new_tab_id:
                    mapping[old_tab_id] = str(new_tab_id)

        return mapping

    @staticmethod
    def _offset_point_dict(pos_dict: dict, dx: float, dy: float) -> None:
        if not isinstance(pos_dict, dict):
            return
        try:
            pos_dict['x'] = float(pos_dict.get('x', 0.0)) + dx
            pos_dict['y'] = float(pos_dict.get('y', 0.0)) + dy
        except Exception:
            return

    def _remap_wire_dict(self, wire_data: dict, *, id_manager, endpoint_map: dict[str, str], dx: float, dy: float) -> Optional[dict]:
        """Return a remapped+offset wire dict suitable for Wire.from_dict()."""
        if not isinstance(wire_data, dict):
            return None

        def map_endpoint(value: Optional[str]) -> Optional[str]:
            if value is None:
                return None
            if not isinstance(value, str):
                return None
            return endpoint_map.get(value)

        start_old = wire_data.get('start_tab_id')
        start_new = map_endpoint(start_old)
        if not start_new:
            return None

        end_old = wire_data.get('end_tab_id')
        end_new = None
        if end_old is not None:
            end_new = map_endpoint(end_old)
            if not end_new:
                return None

        new_wire: dict = {
            'wire_id': id_manager.generate_id(),
            'start_tab_id': start_new,
        }
        if end_old is not None:
            new_wire['end_tab_id'] = end_new

        # Waypoints: new IDs + offset positions
        waypoints = wire_data.get('waypoints', [])
        if isinstance(waypoints, list) and waypoints:
            new_wps = []
            for wp in waypoints:
                if not isinstance(wp, dict):
                    continue
                wp_new = {
                    'waypoint_id': id_manager.generate_id(),
                    'position': dict((wp.get('position') or {})),
                }
                self._offset_point_dict(wp_new['position'], dx, dy)
                new_wps.append(wp_new)
            if new_wps:
                new_wire['waypoints'] = new_wps

        # Junctions embedded inside wire (rare in current GUI). Remap IDs + recurse.
        junctions = wire_data.get('junctions', [])
        if isinstance(junctions, list) and junctions:
            new_juncs = []
            for j in junctions:
                if not isinstance(j, dict):
                    continue
                old_jid = j.get('junction_id')
                j_new_id = id_manager.generate_id()
                j_new = {
                    'junction_id': j_new_id,
                    'position': dict((j.get('position') or {})),
                }
                self._offset_point_dict(j_new['position'], dx, dy)

                # Recurse child wires
                child_wires = j.get('child_wires', [])
                if isinstance(child_wires, list) and child_wires:
                    extended_map = dict(endpoint_map)
                    if isinstance(old_jid, str):
                        extended_map[old_jid] = j_new_id

                    new_children = []
                    for cw in child_wires:
                        remapped = self._remap_wire_dict(
                            cw,
                            id_manager=id_manager,
                            endpoint_map=extended_map,
                            dx=dx,
                            dy=dy,
                        )
                        if remapped:
                            new_children.append(remapped)
                    if new_children:
                        j_new['child_wires'] = new_children

                new_juncs.append(j_new)
            if new_juncs:
                new_wire['junctions'] = new_juncs

        return new_wire
    
    def _copy_selected(self) -> None:
        """
        Copy selected items (components, wires, junctions) to clipboard.
        """
        has_any_selection = (
            bool(self.selected_components)
            or bool(self.selected_wires)
            or bool(self.selected_junctions)
            or bool(self.selected_waypoints)
        )
        if not has_any_selection:
            self.set_status("Nothing selected to copy")
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
        
        # Components
        components_payload = []
        for component_id in self.selected_components:
            component = page.components.get(component_id)
            if component:
                components_payload.append(component.to_dict())

        # Wires: include explicitly selected wires and any wires that own selected waypoints
        selected_wire_ids = set(self.selected_wires)
        for wire_id, waypoint_id in self.selected_waypoints:
            if wire_id:
                selected_wire_ids.add(wire_id)

        wires_payload = []
        for wire_id in selected_wire_ids:
            wire_obj = page.wires.get(wire_id)
            if wire_obj:
                wires_payload.append(wire_obj.to_dict())

        # Junctions
        junctions_payload = []
        for junction_id in self.selected_junctions:
            junction = page.junctions.get(junction_id)
            if junction:
                junctions_payload.append(junction.to_dict())

        self.clipboard = {
            'version': 1,
            'components': components_payload,
            'wires': wires_payload,
            'junctions': junctions_payload,
        }

        self.set_status(
            f"Copied {len(components_payload)} component(s), {len(wires_payload)} wire(s), {len(junctions_payload)} junction(s)"
        )
    
    def _cut_selected(self) -> None:
        """
        Cut selected items (copy + delete).
        """
        has_any_selection = (
            bool(self.selected_components)
            or bool(self.selected_wires)
            or bool(self.selected_junctions)
            or bool(self.selected_waypoints)
        )
        if not has_any_selection:
            self.set_status("Nothing selected to cut")
            return
        
        # Copy first
        self._copy_selected()
        
        # Then delete
        self._delete_selected()
        
        self.set_status("Cut selection")
    
    def _paste_clipboard(self, *, anchor_world: Optional[tuple[float, float]] = None) -> None:
        """
        Paste items from clipboard with new IDs and offset position.
        """
        if not self._clipboard_has_items():
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
        
        from components.factory import get_factory
        from core.wire import Wire, Junction

        # Snapshot state before mutating the document
        self._capture_undo_checkpoint()
        
        # Clear current selection
        self._clear_selection()

        # Default paste offset: 2 snap units right and down from original.
        # This keeps pasted items aligned with the configured snap/grid size.
        try:
            snap_size = int(self.settings.get_snap_size())
        except Exception:
            snap_size = 10
        if snap_size <= 0:
            snap_size = 10

        dx: float = float(2 * snap_size)
        dy: float = float(2 * snap_size)

        clip = self.clipboard
        # Backward compatibility: old clipboard stored just a list of component dicts
        if isinstance(clip, list):
            clip = {'components': clip, 'wires': [], 'junctions': []}
        if not isinstance(clip, dict):
            self.set_status("Clipboard format not recognized")
            return

        # If an anchor is provided (context-menu paste), compute dx/dy so the pasted
        # selection's origin (top-left of its bounding box) lands at the anchor.
        if anchor_world is not None:
            try:
                ax, ay = float(anchor_world[0]), float(anchor_world[1])
            except Exception:
                ax, ay = None, None

            if ax is not None and ay is not None:
                # Snap the anchor to the same snap grid used for placement.
                try:
                    ax = round(ax / snap_size) * snap_size
                    ay = round(ay / snap_size) * snap_size
                except Exception:
                    pass

                min_x = None
                min_y = None

                for component_data in (clip.get('components', []) or []):
                    if not isinstance(component_data, dict):
                        continue
                    position_data = component_data.get('position', {'x': 0, 'y': 0})
                    try:
                        if isinstance(position_data, dict):
                            x0 = float(position_data.get('x', 0.0))
                            y0 = float(position_data.get('y', 0.0))
                        else:
                            x0 = float(position_data[0])
                            y0 = float(position_data[1])
                    except Exception:
                        continue
                    min_x = x0 if min_x is None else min(min_x, x0)
                    min_y = y0 if min_y is None else min(min_y, y0)

                for junction_data in (clip.get('junctions', []) or []):
                    if not isinstance(junction_data, dict):
                        continue
                    pos = junction_data.get('position', {})
                    if not isinstance(pos, dict):
                        continue
                    try:
                        x0 = float(pos.get('x', 0.0))
                        y0 = float(pos.get('y', 0.0))
                    except Exception:
                        continue
                    min_x = x0 if min_x is None else min(min_x, x0)
                    min_y = y0 if min_y is None else min(min_y, y0)

                if min_x is not None and min_y is not None:
                    dx = ax - min_x
                    dy = ay - min_y

                    # Snap the delta so all pasted items stay aligned.
                    try:
                        dx = round(dx / snap_size) * snap_size
                        dy = round(dy / snap_size) * snap_size
                    except Exception:
                        pass

        factory = get_factory()
        id_manager = tab.document.id_manager

        # 1) Paste components first and build endpoint mapping for wire remap
        old_tab_to_new_tab: dict[str, str] = {}
        pasted_component_ids: list[str] = []

        for component_data in (clip.get('components', []) or []):
            if not isinstance(component_data, dict):
                continue

            component_type = component_data.get('component_type', '')
            if not isinstance(component_type, str) or not component_type:
                continue

            new_id = id_manager.generate_id()
            try:
                component = factory.create_component(component_type, new_id, active_page_id)
            except Exception:
                continue

            if isinstance(component_data.get('properties'), dict):
                component.properties = component_data['properties'].copy()
            if 'link_name' in component_data:
                component.link_name = component_data.get('link_name')
            if 'rotation' in component_data:
                try:
                    component.rotation = int(component_data.get('rotation', 0))
                except Exception:
                    pass

            position_data = component_data.get('position', {'x': 0, 'y': 0})
            if isinstance(position_data, dict):
                original_x = position_data.get('x', 0)
                original_y = position_data.get('y', 0)
            else:
                original_x, original_y = position_data
            component.position = (original_x + dx, original_y + dy)

            if hasattr(component, 'on_property_changed') and callable(getattr(component, 'on_property_changed')):
                try:
                    component.on_property_changed('number_of_pins')
                except Exception:
                    pass

            try:
                old_tab_to_new_tab.update(self._build_tab_id_map(component_data, component))
            except Exception:
                pass

            page.add_component(component)
            pasted_component_ids.append(new_id)
            self.selected_components.add(new_id)

        # 2) Paste junctions next and build junction ID mapping
        old_junc_to_new_junc: dict[str, str] = {}
        pasted_junction_ids: list[str] = []
        embedded_wire_dicts: list[dict] = []
        for junction_data in (clip.get('junctions', []) or []):
            if not isinstance(junction_data, dict):
                continue
            old_jid = junction_data.get('junction_id')
            if not isinstance(old_jid, str) or not old_jid:
                continue

            child_wires = junction_data.get('child_wires', [])
            if isinstance(child_wires, list) and child_wires:
                for cw in child_wires:
                    if isinstance(cw, dict):
                        embedded_wire_dicts.append(cw)

            pos = junction_data.get('position', {})
            if not isinstance(pos, dict):
                continue
            try:
                x = float(pos.get('x', 0.0)) + dx
                y = float(pos.get('y', 0.0)) + dy
            except Exception:
                x, y = 0.0, 0.0

            new_jid = id_manager.generate_id()
            junction = Junction(new_jid, (int(x), int(y)))
            page.add_junction(junction)
            old_junc_to_new_junc[old_jid] = new_jid
            pasted_junction_ids.append(new_jid)
            self.selected_junctions.add(new_jid)

        endpoint_map: dict[str, str] = {}
        endpoint_map.update(old_tab_to_new_tab)
        endpoint_map.update(old_junc_to_new_junc)

        # 3) Paste wires with endpoint remapping
        pasted_wire_ids: list[str] = []
        seen_source_wire_ids: set[str] = set()
        wire_sources = list(clip.get('wires', []) or []) + embedded_wire_dicts
        for wire_data in wire_sources:
            if isinstance(wire_data, dict):
                src_id = wire_data.get('wire_id')
                if isinstance(src_id, str) and src_id:
                    if src_id in seen_source_wire_ids:
                        continue
                    seen_source_wire_ids.add(src_id)
                remapped = self._remap_wire_dict(wire_data, id_manager=id_manager, endpoint_map=endpoint_map, dx=dx, dy=dy)
            if not remapped:
                continue
            try:
                wire_obj = Wire.from_dict(remapped)
            except Exception:
                continue
            page.add_wire(wire_obj)
            pasted_wire_ids.append(wire_obj.wire_id)
            self.selected_wires.add(wire_obj.wire_id)

            # Select all waypoints on pasted wires so they are visible/highlighted.
            try:
                for waypoint in getattr(wire_obj, 'waypoints', {}).values():
                    wid = getattr(waypoint, 'waypoint_id', None)
                    if wid:
                        self.selected_waypoints.add((wire_obj.wire_id, wid))
            except Exception:
                pass
        
        # Mark document as modified
        self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        # Re-render page
        self.design_canvas.set_page(page)

        # Re-apply component selection (wire/junction selection persists via sets)
        for cid in pasted_component_ids:
            try:
                self.design_canvas.set_component_selected(cid, True)
            except Exception:
                pass

        # Ensure pasted wires render in selected state immediately.
        for wid in pasted_wire_ids:
            try:
                self.design_canvas.set_wire_selected(wid, True)
            except Exception:
                pass
        
        # Update properties panel and menu
        if len(self.selected_components) == 1:
            component_id = next(iter(self.selected_components))
            component = page.components.get(component_id)
            if component:
                self.properties_panel.set_component(component)
        else:
            self.properties_panel.set_component(None)
        
        self.menu_bar.enable_edit_menu(
            has_selection=(
                len(self.selected_components) > 0
                or len(self.selected_wires) > 0
                or len(self.selected_junctions) > 0
                or len(self.selected_waypoints) > 0
            )
        )
        self.set_status(
            f"Pasted {len(pasted_component_ids)} component(s), {len(pasted_wire_ids)} wire(s), {len(pasted_junction_ids)} junction(s)"
        )
    
    def _delete_selected(self) -> None:
        """
        Delete selected components and connected wires.
        """
        # Block delete in simulation mode
        if self.simulation_mode:
            return
        
        if (
            not self.selected_components
            and not self.selected_wires
            and not self.selected_junctions
            and not self.selected_waypoints
        ):
            self.set_status("No items selected to delete")
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
        
        # Snapshot state before mutating the document
        self._capture_undo_checkpoint()
        
        def _tab_id_to_component_id(tab_id):
            if not tab_id:
                return None
            parts = str(tab_id).split('.')
            if len(parts) < 3:
                return None
            return parts[0]

        # Find wires connected to deleted components/junctions and include explicitly selected wires/waypoints
        wires_to_delete = set(self.selected_wires)

        # Waypoint selection implies wire deletion.
        for wire_id, waypoint_id in self.selected_waypoints:
            if wire_id:
                wires_to_delete.add(wire_id)

        # Junction selection implies deleting connected wires.
        if self.selected_junctions:
            for wire in page.wires.values():
                if wire.start_tab_id in self.selected_junctions or wire.end_tab_id in self.selected_junctions:
                    wires_to_delete.add(wire.wire_id)
        if self.selected_components:
            for wire in page.wires.values():
                start_component_id = _tab_id_to_component_id(wire.start_tab_id)
                end_component_id = _tab_id_to_component_id(wire.end_tab_id)

                if (start_component_id and start_component_id in self.selected_components) or (
                    end_component_id and end_component_id in self.selected_components
                ):
                    wires_to_delete.add(wire.wire_id)
        
        # Track junctions connected to wires being deleted (and explicitly selected junctions) to remove orphans later
        junctions_to_check = set(self.selected_junctions)
        for wire_id in wires_to_delete:
            wire_obj = page.wires.get(wire_id)
            if wire_obj:
                for endpoint in (wire_obj.start_tab_id, wire_obj.end_tab_id):
                    if endpoint and page.get_junction(endpoint):
                        junctions_to_check.add(endpoint)

        # Delete wires (do not delete junctions/components yet)
        for wire_id in wires_to_delete:
            page.remove_wire(wire_id)

        from core.wire import Wire, Waypoint

        def _junction_degree(junction_id: str) -> int:
            return sum(1 for w in page.wires.values() if w.start_tab_id == junction_id or w.end_tab_id == junction_id)

        def _collapse_degree_two_junction(junction_id: str) -> bool:
            """If junction has exactly two connected wires, remove junction and merge wires into one.

            Returns True if a collapse occurred.
            """
            connected_wires = [w for w in page.wires.values() if w.start_tab_id == junction_id or w.end_tab_id == junction_id]
            if len(connected_wires) != 2:
                return False

            junction = page.get_junction(junction_id)
            if not junction:
                return False

            w1, w2 = connected_wires

            def _other_endpoint(w: Wire) -> str:
                if w.start_tab_id == junction_id:
                    return w.end_tab_id
                return w.start_tab_id

            other1 = _other_endpoint(w1)
            other2 = _other_endpoint(w2)
            if not other1 or not other2 or other1 == other2:
                return False

            def _waypoints_in_direction(w: Wire, from_id: str, to_id: str) -> list:
                items = list(w.waypoints.values())
                if w.start_tab_id == from_id and w.end_tab_id == to_id:
                    return [wp.position for wp in items]
                if w.start_tab_id == to_id and w.end_tab_id == from_id:
                    return [wp.position for wp in reversed(items)]
                # Unexpected orientation; best effort
                return [wp.position for wp in items]

            # Build merged waypoint list: other1 -> junction -> other2
            merged_positions = []
            for pos in _waypoints_in_direction(w1, other1, junction_id):
                if not merged_positions or merged_positions[-1] != pos:
                    merged_positions.append(pos)

            if not merged_positions or merged_positions[-1] != junction.position:
                merged_positions.append(junction.position)

            for pos in _waypoints_in_direction(w2, junction_id, other2):
                if not merged_positions or merged_positions[-1] != pos:
                    merged_positions.append(pos)

            # Remove the two existing wires and the junction
            page.remove_wire(w1.wire_id)
            page.remove_wire(w2.wire_id)
            page.remove_junction(junction_id)

            # Create the replacement merged wire
            merged_wire_id = tab.document.id_manager.generate_id()
            merged_wire = Wire(merged_wire_id, other1, other2)
            for pos in merged_positions:
                waypoint_id = tab.document.id_manager.generate_id()
                merged_wire.add_waypoint(Waypoint(waypoint_id, (int(pos[0]), int(pos[1]))))
            page.add_wire(merged_wire)
            return True

        # Remove orphan junctions (degree 0) or collapse redundant junctions (degree 2)
        for junction_id in list(junctions_to_check):
            degree = _junction_degree(junction_id)
            if degree == 0:
                page.remove_junction(junction_id)
            elif degree == 2:
                _collapse_degree_two_junction(junction_id)
        
        # Delete components
        delete_components_count = len(self.selected_components)
        for component_id in list(self.selected_components):
            page.remove_component(component_id)
        
        # Clear selection
        self._clear_selection()
        
        # Mark document as modified
        self.file_tabs.set_tab_modified(tab.tab_id, True)
        
        # Re-render page
        self.design_canvas.set_page(page)
        
        self.set_status(
            f"Deleted {delete_components_count} component(s) and {len(wires_to_delete)} wire(s)"
        )

    
    def _clear_wire_preview(self) -> None:
        """Clear wire preview lines from canvas."""
        for line in self.wire_preview_lines:
            self.design_canvas.canvas.delete(line)
        self.wire_preview_lines = []

