"""
Settings Dialog for Relay Simulator III

Provides a dialog window for viewing and editing application settings.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from gui.theme import VSCodeTheme
from gui.settings import Settings


class SettingsDialog:
    """
    Settings dialog window.
    
    Allows the user to view and modify application settings including:
    - Simulation threading mode
    - Default canvas size
    - Grid size
    - Snap size
    
    Note: Recent documents are not editable in this dialog (managed via menu).
    """
    
    def __init__(self, parent: tk.Tk, settings: Settings):
        """
        Initialize the settings dialog.
        
        Args:
            parent: Parent window
            settings: Settings object to edit
        """
        self.parent = parent
        self.settings = settings
        self.result = None  # Will be True if OK, False if Cancel
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Set size and center
        dialog_width = 500
        dialog_height = 400
        x = parent.winfo_x() + (parent.winfo_width() - dialog_width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dialog_height) // 2
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Apply theme
        self.dialog.configure(bg=VSCodeTheme.BG_PRIMARY)
        
        # Variables for form fields
        self.threading_var = tk.StringVar(value=settings.get_simulation_threading())
        self.canvas_width_var = tk.IntVar(value=settings.get_canvas_size()[0])
        self.canvas_height_var = tk.IntVar(value=settings.get_canvas_size()[1])
        self.grid_size_var = tk.IntVar(value=settings.get_grid_size())
        self.snap_size_var = tk.IntVar(value=settings.get_snap_size())
        
        # Create UI
        self._create_widgets()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
    def _create_widgets(self) -> None:
        """Create the dialog widgets."""
        # Main container with padding
        main_frame = tk.Frame(
            self.dialog,
            bg=VSCodeTheme.BG_PRIMARY,
            padx=VSCodeTheme.PADDING_LARGE,
            pady=VSCodeTheme.PADDING_LARGE
        )
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Application Settings",
            font=VSCodeTheme.get_font('large', bold=True),
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_BRIGHT
        )
        title_label.pack(anchor=tk.W, pady=(0, VSCodeTheme.PADDING_MEDIUM))
        
        # Create a canvas and scrollbar for scrollable content
        canvas_container = tk.Frame(main_frame, bg=VSCodeTheme.BG_PRIMARY)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas = tk.Canvas(
            canvas_container,
            bg=VSCodeTheme.BG_PRIMARY,
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=canvas.yview)
        
        # Frame inside canvas for scrollable content
        scrollable_frame = tk.Frame(canvas, bg=VSCodeTheme.BG_PRIMARY)
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        
        # Configure canvas scrolling
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        scrollable_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        # Settings form (now inside scrollable_frame)
        form_frame = tk.Frame(scrollable_frame, bg=VSCodeTheme.BG_PRIMARY)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=VSCodeTheme.PADDING_SMALL)
        
        row = 0
        
        # Simulation Threading
        self._create_label(form_frame, "Simulation Threading:", row)
        threading_frame = tk.Frame(form_frame, bg=VSCodeTheme.BG_PRIMARY)
        threading_frame.grid(row=row, column=1, sticky=tk.W, pady=VSCodeTheme.PADDING_SMALL)
        
        tk.Radiobutton(
            threading_frame,
            text="Single Thread",
            variable=self.threading_var,
            value="single",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            selectcolor=VSCodeTheme.BG_TERTIARY,
            activebackground=VSCodeTheme.BG_PRIMARY,
            activeforeground=VSCodeTheme.FG_BRIGHT
        ).pack(side=tk.LEFT, padx=(0, VSCodeTheme.PADDING_MEDIUM))
        
        tk.Radiobutton(
            threading_frame,
            text="Multi-threaded",
            variable=self.threading_var,
            value="multi",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            selectcolor=VSCodeTheme.BG_TERTIARY,
            activebackground=VSCodeTheme.BG_PRIMARY,
            activeforeground=VSCodeTheme.FG_BRIGHT
        ).pack(side=tk.LEFT)
        
        row += 1
        
        # Separator
        separator1 = tk.Frame(form_frame, height=2, bg=VSCodeTheme.BORDER_SUBTLE)
        separator1.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=VSCodeTheme.PADDING_MEDIUM)
        row += 1
        
        # Canvas Size section
        canvas_header = tk.Label(
            form_frame,
            text="Default Canvas Size",
            font=VSCodeTheme.get_font('medium', bold=True),
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_BRIGHT
        )
        canvas_header.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(VSCodeTheme.PADDING_MEDIUM, VSCodeTheme.PADDING_SMALL))
        row += 1
        
        # Canvas Width
        self._create_label(form_frame, "Width (pixels):", row)
        self._create_spinbox(form_frame, self.canvas_width_var, 1000, 10000, row)
        row += 1
        
        # Canvas Height
        self._create_label(form_frame, "Height (pixels):", row)
        self._create_spinbox(form_frame, self.canvas_height_var, 1000, 10000, row)
        row += 1
        
        # Separator
        separator2 = tk.Frame(form_frame, height=2, bg=VSCodeTheme.BORDER_SUBTLE)
        separator2.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=VSCodeTheme.PADDING_MEDIUM)
        row += 1
        
        # Grid and Snap section
        grid_header = tk.Label(
            form_frame,
            text="Grid and Snap Settings",
            font=VSCodeTheme.get_font('medium', bold=True),
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_BRIGHT
        )
        grid_header.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(VSCodeTheme.PADDING_MEDIUM, VSCodeTheme.PADDING_SMALL))
        row += 1
        
        # Grid Size
        self._create_label(form_frame, "Grid Size (pixels):", row)
        self._create_spinbox(form_frame, self.grid_size_var, 5, 100, row)
        row += 1
        
        # Snap Size
        self._create_label(form_frame, "Snap Size (pixels):", row)
        self._create_spinbox(form_frame, self.snap_size_var, 1, 50, row)
        row += 1
        
        # Configure column weights
        form_frame.columnconfigure(0, weight=0)
        form_frame.columnconfigure(1, weight=1)
        
        # Separator between scrollable content and buttons
        separator = tk.Frame(main_frame, height=2, bg=VSCodeTheme.BORDER_SUBTLE)
        separator.pack(fill=tk.X, pady=(VSCodeTheme.PADDING_MEDIUM, VSCodeTheme.PADDING_SMALL))
        
        # Button frame at bottom (OUTSIDE scrollable area)
        button_frame = tk.Frame(main_frame, bg=VSCodeTheme.BG_PRIMARY)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Buttons
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_PRIMARY,
            activebackground=VSCodeTheme.BG_HOVER,
            relief=tk.FLAT,
            padx=VSCodeTheme.PADDING_LARGE,
            pady=VSCodeTheme.PADDING_SMALL
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(VSCodeTheme.PADDING_SMALL, 0))
        
        ok_btn = tk.Button(
            button_frame,
            text="OK",
            command=self._on_ok,
            bg=VSCodeTheme.ACCENT_BLUE,
            fg=VSCodeTheme.FG_BRIGHT,
            activebackground=VSCodeTheme.BG_ACTIVE,
            relief=tk.FLAT,
            padx=VSCodeTheme.PADDING_LARGE,
            pady=VSCodeTheme.PADDING_SMALL
        )
        ok_btn.pack(side=tk.RIGHT)
        
        # Reset button on left
        reset_btn = tk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._on_reset,
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_PRIMARY,
            activebackground=VSCodeTheme.BG_HOVER,
            relief=tk.FLAT,
            padx=VSCodeTheme.PADDING_LARGE,
            pady=VSCodeTheme.PADDING_SMALL
        )
        reset_btn.pack(side=tk.LEFT)
        
    def _create_label(self, parent: tk.Frame, text: str, row: int) -> None:
        """Create a form label."""
        label = tk.Label(
            parent,
            text=text,
            font=VSCodeTheme.get_font('normal'),
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            anchor=tk.W
        )
        label.grid(row=row, column=0, sticky=tk.W, pady=VSCodeTheme.PADDING_SMALL, padx=(0, VSCodeTheme.PADDING_MEDIUM))
        
    def _create_spinbox(self, parent: tk.Frame, variable: tk.IntVar, from_: int, to: int, row: int) -> None:
        """Create a spinbox input."""
        spinbox = tk.Spinbox(
            parent,
            from_=from_,
            to=to,
            textvariable=variable,
            width=10,
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_PRIMARY,
            insertbackground=VSCodeTheme.FG_PRIMARY,
            buttonbackground=VSCodeTheme.BG_TERTIARY,
            relief=tk.FLAT
        )
        spinbox.grid(row=row, column=1, sticky=tk.W, pady=VSCodeTheme.PADDING_SMALL)
        
    def _on_ok(self) -> None:
        """Handle OK button click."""
        # Validate inputs
        try:
            canvas_width = self.canvas_width_var.get()
            canvas_height = self.canvas_height_var.get()
            grid_size = self.grid_size_var.get()
            snap_size = self.snap_size_var.get()
            
            if canvas_width <= 0 or canvas_height <= 0:
                raise ValueError("Canvas size must be positive")
            if grid_size <= 0:
                raise ValueError("Grid size must be positive")
            if snap_size <= 0:
                raise ValueError("Snap size must be positive")
                
        except (tk.TclError, ValueError) as e:
            # Show error message
            from tkinter import messagebox
            messagebox.showerror(
                "Invalid Input",
                f"Please check your input values:\n{e}",
                parent=self.dialog
            )
            return
            
        # Save settings
        self.settings.set_simulation_threading(self.threading_var.get())
        self.settings.set_canvas_size(canvas_width, canvas_height)
        self.settings.set_grid_size(grid_size)
        self.settings.set_snap_size(snap_size)
        self.settings.save()
        
        # Close dialog
        self.result = True
        self.dialog.destroy()
        
    def _on_cancel(self) -> None:
        """Handle Cancel button click."""
        self.result = False
        self.dialog.destroy()
        
    def _on_reset(self) -> None:
        """Handle Reset to Defaults button click."""
        # Reset to default values
        defaults = Settings.DEFAULTS
        self.threading_var.set(defaults['simulation_threading'])
        self.canvas_width_var.set(defaults['default_canvas_width'])
        self.canvas_height_var.set(defaults['default_canvas_height'])
        self.grid_size_var.set(defaults['canvas_grid_size'])
        self.snap_size_var.set(defaults['canvas_snap_size'])
        
    def show(self) -> bool:
        """
        Show the dialog and wait for it to close.
        
        Returns:
            True if OK was clicked, False if Cancel was clicked
        """
        # Wait for dialog to close
        self.dialog.wait_window()
        return self.result if self.result is not None else False


def show_settings_dialog(parent: tk.Tk, settings: Settings) -> bool:
    """
    Show the settings dialog.
    
    Args:
        parent: Parent window
        settings: Settings object to edit
        
    Returns:
        True if settings were saved, False if cancelled
    """
    dialog = SettingsDialog(parent, settings)
    return dialog.show()
