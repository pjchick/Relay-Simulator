"""
Logic Analyser Window for Relay Simulator

Provides a modeless window with classic logic analyser interface for monitoring
LINK states during simulation.
"""

import time
import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Dict, Any
from gui.theme import VSCodeTheme
from core.state import PinState


class Channel:
    """Represents a logic analyser channel."""
    
    def __init__(self, name: str = "", link_name: str = ""):
        """
        Initialize a channel.
        
        Args:
            name: Display name of the channel
            link_name: Name of the LINK to monitor
        """
        self.name = name
        self.link_name = link_name
        self.trace_data: List[tuple] = []  # List of (timestamp, state) tuples
        self.color = VSCodeTheme.ACCENT_GREEN


class LogicAnalyserWindow:
    """
    Logic Analyser window for monitoring LINK states.
    
    Provides a classic logic analyser interface with:
    - Multiple channels (add/remove)
    - Channel-to-LINK binding
    - Waveform display
    - Start/Stop/Clear controls
    """
    
    def __init__(self, parent: tk.Tk, main_window):
        """
        Initialize the Logic Analyser window.
        
        Args:
            parent: Parent window (root)
            main_window: Reference to MainWindow instance
        """
        self.parent = parent
        self.main_window = main_window
        self.channels: List[Channel] = []
        self.is_capturing = False
        self.start_time = 0.0
        self.sample_count = 0  # Track number of samples captured
        self.display_timer_id: Optional[str] = None  # Timer for display refresh
        self.display_refresh_ms = 100  # Refresh display every 100ms
        self.current_config_id: Optional[str] = None  # Currently selected configuration
        self.current_config_name: str = "Untitled Configuration"
        
        # Time base setting (seconds per division)
        self.time_base_seconds: float = 2.0  # Default: 2 seconds per division
        
        # Drag and drop state for channel reordering
        self.drag_channel_idx: Optional[int] = None  # Index of channel being dragged
        self.drag_start_y: Optional[int] = None  # Y position where drag started
        self.drag_indicator: Optional[tk.Frame] = None  # Visual indicator for drop position
        
        # Cursor state for time measurement (visible when stopped)
        self.cursor_x: Optional[int] = None  # X position of cursor in canvas coordinates
        self.cursor_visible = False  # Whether cursor is shown
        
        # Trigger configuration
        self.trigger_enabled = False  # Whether trigger mode is enabled
        self.trigger_link_name = ""  # Link name to monitor for trigger
        self.trigger_mode = "rising"  # "rising", "falling", or "change"
        self.waiting_for_trigger = False  # True when armed and waiting for trigger
        self.last_trigger_state: Optional[PinState] = None  # Last state of trigger signal
        
        # Create modeless dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Logic Analyser")
        self.window.geometry("900x600")
        
        # Ensure window is resizable and has native maximize/minimize buttons
        self.window.resizable(True, True)
        
        # Apply theme
        self.window.configure(bg=VSCodeTheme.BG_PRIMARY)
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._create_ui()
        
        # Load configurations from document or create default
        self._load_configurations()
    
    def _create_ui(self):
        """Create the user interface."""
        # Top toolbar with controls
        self._create_toolbar()
        
        # Main content area (horizontal split)
        content_frame = tk.Frame(
            self.window,
            bg=VSCodeTheme.BG_PRIMARY
        )
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel: Channel list
        self._create_channel_panel(content_frame)
        
        # Right panel: Waveform display
        self._create_waveform_panel(content_frame)
    
    def _create_toolbar(self):
        """Create the toolbar with control buttons."""
        toolbar = tk.Frame(
            self.window,
            bg=VSCodeTheme.BG_SECONDARY,
            height=VSCodeTheme.TOOLBAR_HEIGHT
        )
        toolbar.pack(side=tk.TOP, fill=tk.X)
        toolbar.pack_propagate(False)
        
        # Button style
        button_style = {
            'bg': VSCodeTheme.BUTTON_BG,
            'fg': VSCodeTheme.FG_PRIMARY,
            'font': (VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL),
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 15,
            'pady': 4
        }
        
        # Start button
        self.start_button = tk.Button(
            toolbar,
            text="▶ Start",
            command=self._on_start,
            **button_style
        )
        self.start_button.pack(side=tk.LEFT, padx=5, pady=4)
        
        # Stop button
        self.stop_button = tk.Button(
            toolbar,
            text="⏹ Stop",
            command=self._on_stop,
            state=tk.DISABLED,
            **button_style
        )
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=4)
        
        # Clear button
        self.clear_button = tk.Button(
            toolbar,
            text="🗑 Clear",
            command=self._on_clear,
            **button_style
        )
        self.clear_button.pack(side=tk.LEFT, padx=5, pady=4)
        
        # Trigger button
        self.trigger_button = tk.Button(
            toolbar,
            text="⚡ Trigger",
            command=self._on_trigger,
            **button_style
        )
        self.trigger_button.pack(side=tk.LEFT, padx=5, pady=4)
        
        # Separator
        separator = tk.Frame(toolbar, bg=VSCodeTheme.BORDER_DEFAULT, width=2)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Configuration selector label
        config_label = tk.Label(
            toolbar,
            text="Config:",
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_SMALL)
        )
        config_label.pack(side=tk.LEFT, padx=(10, 5))
        
        # Configuration dropdown
        self.config_var = tk.StringVar()
        self.config_dropdown = ttk.Combobox(
            toolbar,
            textvariable=self.config_var,
            state='readonly',
            width=20,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_SMALL)
        )
        self.config_dropdown.pack(side=tk.LEFT, padx=5)
        self.config_dropdown.bind('<<ComboboxSelected>>', self._on_config_selected)
        
        # Add config button
        add_config_btn = tk.Button(
            toolbar,
            text="+",
            command=self._add_new_config,
            bg=VSCodeTheme.BUTTON_BG,
            fg=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL),
            relief=tk.FLAT,
            cursor='hand2',
            width=2
        )
        add_config_btn.pack(side=tk.LEFT, padx=2)
        
        # Remove config button
        self.remove_config_btn = tk.Button(
            toolbar,
            text="−",
            command=self._remove_current_config,
            bg=VSCodeTheme.BUTTON_BG,
            fg=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL),
            relief=tk.FLAT,
            cursor='hand2',
            width=2
        )
        self.remove_config_btn.pack(side=tk.LEFT, padx=2)
        
        # Rename config button
        rename_config_btn = tk.Button(
            toolbar,
            text="✎",
            command=self._rename_current_config,
            bg=VSCodeTheme.BUTTON_BG,
            fg=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL),
            relief=tk.FLAT,
            cursor='hand2',
            width=2
        )
        rename_config_btn.pack(side=tk.LEFT, padx=2)
        
        # Separator
        separator2 = tk.Frame(toolbar, bg=VSCodeTheme.BORDER_DEFAULT, width=2)
        separator2.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Time base label
        time_base_label = tk.Label(
            toolbar,
            text="Time/Div:",
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_SMALL)
        )
        time_base_label.pack(side=tk.LEFT, padx=(10, 5))
        
        # Time base dropdown
        self.time_base_var = tk.StringVar(value="2s")
        self.time_base_dropdown = ttk.Combobox(
            toolbar,
            textvariable=self.time_base_var,
            state='readonly',
            width=8,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_SMALL),
            values=["1s", "2s", "5s", "10s"]
        )
        self.time_base_dropdown.pack(side=tk.LEFT, padx=5)
        self.time_base_dropdown.bind('<<ComboboxSelected>>', self._on_time_base_changed)
        
        # Separator
        separator3 = tk.Frame(toolbar, bg=VSCodeTheme.BORDER_DEFAULT, width=2)
        separator3.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Status label
        self.status_label = tk.Label(
            toolbar,
            text="Ready",
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_SMALL)
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
    
    def _create_channel_panel(self, parent):
        """Create the left panel with channel list."""
        panel = tk.Frame(
            parent,
            bg=VSCodeTheme.BG_SECONDARY,
            width=250
        )
        panel.pack(side=tk.LEFT, fill=tk.Y)
        panel.pack_propagate(False)
        
        # Header
        header = tk.Label(
            panel,
            text="CHANNELS",
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL, "bold"),
            anchor=tk.W,
            padx=10,
            pady=5
        )
        header.pack(fill=tk.X)
        
        # Scrollable channel list
        list_frame = tk.Frame(panel, bg=VSCodeTheme.BG_SECONDARY)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for scrolling
        self.channel_canvas = tk.Canvas(
            list_frame,
            bg=VSCodeTheme.BG_SECONDARY,
            highlightthickness=0
        )
        self.channel_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.channel_canvas.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.channel_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Frame inside canvas for channel widgets
        self.channel_list_frame = tk.Frame(
            self.channel_canvas,
            bg=VSCodeTheme.BG_SECONDARY
        )
        self.channel_canvas_window = self.channel_canvas.create_window(
            (0, 0),
            window=self.channel_list_frame,
            anchor=tk.NW
        )
        
        # Update scroll region when content changes
        def on_configure(event):
            self.channel_canvas.configure(scrollregion=self.channel_canvas.bbox("all"))
            self.channel_canvas.itemconfig(
                self.channel_canvas_window,
                width=self.channel_canvas.winfo_width()
            )
        
        self.channel_list_frame.bind('<Configure>', on_configure)
        self.channel_canvas.bind('<Configure>', on_configure)
        
        # Add/Remove buttons at bottom
        button_frame = tk.Frame(panel, bg=VSCodeTheme.BG_SECONDARY)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        button_style = {
            'bg': VSCodeTheme.BUTTON_BG,
            'fg': VSCodeTheme.FG_PRIMARY,
            'font': (VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_SMALL),
            'relief': tk.FLAT,
            'cursor': 'hand2'
        }
        
        add_button = tk.Button(
            button_frame,
            text="+ Add Channel",
            command=self._add_channel,
            **button_style
        )
        add_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        remove_button = tk.Button(
            button_frame,
            text="− Remove Selected",
            command=self._remove_selected_channel,
            **button_style
        )
        remove_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
    
    def _create_waveform_panel(self, parent):
        """Create the right panel with waveform display."""
        panel = tk.Frame(
            parent,
            bg=VSCodeTheme.BG_PRIMARY
        )
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Header
        header = tk.Label(
            panel,
            text="WAVEFORMS",
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL, "bold"),
            anchor=tk.W,
            padx=10,
            pady=5
        )
        header.pack(fill=tk.X)
        
        # Canvas frame with scrollbar
        canvas_frame = tk.Frame(panel, bg=VSCodeTheme.BG_PRIMARY)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Waveform canvas
        self.waveform_canvas = tk.Canvas(
            canvas_frame,
            bg=VSCodeTheme.BG_PRIMARY,
            highlightthickness=0
        )
        self.waveform_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Horizontal scrollbar
        h_scrollbar = tk.Scrollbar(
            canvas_frame,
            orient=tk.HORIZONTAL,
            command=self.waveform_canvas.xview
        )
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.waveform_canvas.configure(xscrollcommand=h_scrollbar.set)
        
        # Bind mouse events for cursor
        self.waveform_canvas.bind('<Motion>', self._on_mouse_move)
        self.waveform_canvas.bind('<Leave>', self._on_mouse_leave)
        
        # Draw initial grid and labels
        self._draw_waveforms()
    
    def _add_channel(self):
        """Add a new channel to the analyser."""
        channel = Channel(
            name=f"Channel {len(self.channels) + 1}",
            link_name=""
        )
        self.channels.append(channel)
        self._refresh_channel_list()
        self._draw_waveforms()
        self._save_current_configuration()
    
    def _remove_selected_channel(self):
        """Remove the currently selected channel."""
        # For now, remove the last channel
        # TODO: Implement proper selection tracking
        if self.channels:
            self.channels.pop()
            self._refresh_channel_list()
            self._draw_waveforms()
            self._save_current_configuration()
    
    def _refresh_channel_list(self):
        """Refresh the channel list display."""
        # Clear existing widgets
        for widget in self.channel_list_frame.winfo_children():
            widget.destroy()
        
        # Create widget for each channel
        for idx, channel in enumerate(self.channels):
            self._create_channel_widget(idx, channel)
    
    def _create_channel_widget(self, idx: int, channel: Channel):
        """
        Create a widget for a channel.
        
        Args:
            idx: Channel index
            channel: Channel object
        """
        frame = tk.Frame(
            self.channel_list_frame,
            bg=VSCodeTheme.BG_TERTIARY,
            relief=tk.FLAT,
            borderwidth=1
        )
        frame.pack(fill=tk.X, pady=2)
        
        # Make the frame draggable by binding to the frame and its children
        self._make_draggable(frame, idx)
        
        # Channel name
        name_label = tk.Label(
            frame,
            text=f"Channel {idx + 1}",
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL, "bold"),
            anchor=tk.W,
            cursor="hand2"  # Show draggable cursor
        )
        name_label.pack(fill=tk.X, padx=8, pady=(6, 2))
        self._make_draggable(name_label, idx)
        
        # LINK name label
        link_label = tk.Label(
            frame,
            text="LINK Name:",
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_SMALL),
            anchor=tk.W,
            cursor="hand2"  # Show draggable cursor
        )
        link_label.pack(fill=tk.X, padx=8, pady=(2, 0))
        self._make_draggable(link_label, idx)
        
        # LINK name entry
        link_entry = tk.Entry(
            frame,
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL),
            relief=tk.FLAT,
            insertbackground=VSCodeTheme.FG_PRIMARY
        )
        link_entry.pack(fill=tk.X, padx=8, pady=(0, 6))
        link_entry.insert(0, channel.link_name)
        
        # Bind change event
        link_entry.bind(
            '<FocusOut>',
            lambda e, ch=channel, entry=link_entry: self._on_link_name_changed(ch, entry.get())
        )
        link_entry.bind(
            '<Return>',
            lambda e, ch=channel, entry=link_entry: self._on_link_name_changed(ch, entry.get())
        )
    
    def _on_link_name_changed(self, channel: Channel, new_name: str):
        """Handle LINK name change for a channel."""
        channel.link_name = new_name.strip()
        self._save_current_configuration()
    
    def _make_draggable(self, widget, channel_idx: int):
        """
        Make a widget draggable for channel reordering.
        
        Args:
            widget: Widget to make draggable
            channel_idx: Index of the channel this widget belongs to
        """
        widget.bind('<Button-1>', lambda e: self._on_drag_start(e, channel_idx))
        widget.bind('<B1-Motion>', self._on_drag_motion)
        widget.bind('<ButtonRelease-1>', self._on_drag_end)
    
    def _on_drag_start(self, event, channel_idx: int):
        """Handle start of drag operation."""
        self.drag_channel_idx = channel_idx
        self.drag_start_y = event.y_root
        
        # Highlight the channel being dragged
        widgets = self.channel_list_frame.winfo_children()
        if channel_idx < len(widgets):
            widgets[channel_idx].configure(relief=tk.RAISED, borderwidth=2)
    
    def _on_drag_motion(self, event):
        """Handle drag motion to show drop position indicator."""
        if self.drag_channel_idx is None:
            return
        
        # Calculate which position the channel would be dropped at
        drop_idx = self._get_drop_index(event.y_root)
        
        # Remove old indicator
        if self.drag_indicator:
            self.drag_indicator.destroy()
            self.drag_indicator = None
        
        # Show drop position indicator
        if drop_idx is not None and drop_idx != self.drag_channel_idx and drop_idx != self.drag_channel_idx + 1:
            self.drag_indicator = tk.Frame(
                self.channel_list_frame,
                bg=VSCodeTheme.ACCENT_BLUE,
                height=3
            )
            
            # Insert indicator at the drop position
            widgets = self.channel_list_frame.winfo_children()
            if drop_idx < len(widgets):
                self.drag_indicator.pack(before=widgets[drop_idx], fill=tk.X)
            else:
                self.drag_indicator.pack(fill=tk.X)
    
    def _on_drag_end(self, event):
        """Handle end of drag operation - reorder channels."""
        if self.drag_channel_idx is None:
            return
        
        # Calculate drop position
        drop_idx = self._get_drop_index(event.y_root)
        
        # Remove highlight from dragged channel
        widgets = self.channel_list_frame.winfo_children()
        if self.drag_channel_idx < len(widgets):
            widgets[self.drag_channel_idx].configure(relief=tk.FLAT, borderwidth=1)
        
        # Remove drop indicator
        if self.drag_indicator:
            self.drag_indicator.destroy()
            self.drag_indicator = None
        
        # Perform reordering if valid drop position
        if drop_idx is not None and drop_idx != self.drag_channel_idx:
            # Adjust drop index if dragging downward
            if drop_idx > self.drag_channel_idx:
                drop_idx -= 1
            
            # Reorder the channels list
            channel = self.channels.pop(self.drag_channel_idx)
            self.channels.insert(drop_idx, channel)
            
            # Refresh display
            self._refresh_channel_list()
            self._draw_waveforms()
            self._save_current_configuration()
        
        # Reset drag state
        self.drag_channel_idx = None
        self.drag_start_y = None
    
    def _get_drop_index(self, y_root: int) -> Optional[int]:
        """
        Calculate the drop index based on mouse Y position.
        
        Args:
            y_root: Mouse Y position in root window coordinates
            
        Returns:
            Index where channel should be dropped, or None if invalid
        """
        widgets = self.channel_list_frame.winfo_children()
        
        # Find which channel widget the mouse is over
        for idx, widget in enumerate(widgets):
            if isinstance(widget, tk.Frame) and widget != self.drag_indicator:
                widget_y = widget.winfo_rooty()
                widget_height = widget.winfo_height()
                widget_mid = widget_y + widget_height / 2
                
                # If mouse is in top half of widget, drop before it
                # If in bottom half, drop after it
                if y_root < widget_mid:
                    return idx
                elif y_root < widget_y + widget_height:
                    return idx + 1
        
        # If mouse is below all widgets, drop at end
        if widgets and y_root > widgets[-1].winfo_rooty() + widgets[-1].winfo_height():
            return len(widgets)
        
        return None
    
    def _draw_waveforms(self):
        """Draw the waveform display with captured trace data."""
        self.waveform_canvas.delete("all")
        
        if not self.channels:
            # Show empty state message
            self.waveform_canvas.create_text(
                self.waveform_canvas.winfo_width() // 2,
                self.waveform_canvas.winfo_height() // 2,
                text="No channels added\nClick '+ Add Channel' to begin",
                fill=VSCodeTheme.FG_SECONDARY,
                font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_MEDIUM),
                justify=tk.CENTER
            )
            # Reset scroll region
            self.waveform_canvas.configure(scrollregion=(0, 0, 0, 0))
            return
        
        # Get canvas dimensions
        canvas_width = self.waveform_canvas.winfo_width() or 600
        canvas_height = self.waveform_canvas.winfo_height() or 400
        
        # Constants for rendering
        LABEL_WIDTH = 100  # Width reserved for channel labels
        TIME_AXIS_HEIGHT = 30  # Height reserved for time axis at bottom
        MARGIN = 10
        PIXELS_PER_DIVISION = 100  # Fixed pixels per time division
        # Calculate pixels per second based on time base setting
        PIXELS_PER_SECOND = PIXELS_PER_DIVISION / self.time_base_seconds
        CHANNEL_HEIGHT = 87  # Fixed height per channel to match left panel channel boxes
        
        # Waveform area dimensions
        waveform_height = canvas_height - TIME_AXIS_HEIGHT
        
        # Channel layout - use fixed height instead of dividing canvas
        channel_height = CHANNEL_HEIGHT
        
        # Determine time range from trace data or current elapsed time
        max_time = 0.0
        has_data = False
        for channel in self.channels:
            if channel.trace_data:
                has_data = True
                if channel.trace_data:
                    max_time = max(max_time, channel.trace_data[-1][0])
        
        # If capturing, extend time range to current elapsed time
        if self.is_capturing and self.start_time > 0:
            current_time = time.time() - self.start_time
            max_time = max(max_time, current_time)
            has_data = True  # Consider we have data if we're capturing
        
        # If no data, show placeholder
        if not has_data:
            y_mid = waveform_height // 2
            self.waveform_canvas.create_text(
                canvas_width // 2,
                y_mid,
                text="No trace data\nClick '▶ Start' to begin capturing",
                fill=VSCodeTheme.FG_SECONDARY,
                font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_MEDIUM),
                justify=tk.CENTER
            )
            # Reset scroll region
            self.waveform_canvas.configure(scrollregion=(0, 0, 0, 0))
            return
        
        # Calculate total waveform width based on fixed time scale
        waveform_width = max(LABEL_WIDTH + (max_time * PIXELS_PER_SECOND) + MARGIN, canvas_width)
        
        # Set canvas scroll region
        self.waveform_canvas.configure(scrollregion=(0, 0, waveform_width, canvas_height))
        
        # Auto-scroll to the right (latest data) during capture
        if self.is_capturing:
            self.waveform_canvas.xview_moveto(1.0)
        
        # Draw time axis
        self._draw_time_axis(LABEL_WIDTH, waveform_height, waveform_width - LABEL_WIDTH - MARGIN, max_time)
        
        # Draw each channel
        for idx, channel in enumerate(self.channels):
            y_base = idx * channel_height
            
            # Center of the entire channel area
            y_center = y_base + channel_height / 2
            
            # Compact waveform height to match label size (25 pixels total)
            WAVEFORM_HEIGHT = 25
            y_high = y_center - WAVEFORM_HEIGHT / 2
            y_low = y_center + WAVEFORM_HEIGHT / 2
            
            # Draw channel label (vertically centered in channel area)
            self.waveform_canvas.create_text(
                10,
                y_center,
                text=channel.link_name or f"CH{idx + 1}",
                fill=VSCodeTheme.FG_PRIMARY,
                font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_SMALL, "bold"),
                anchor=tk.W
            )
            
            # Draw state level labels (HIGH/FLOAT)
            self.waveform_canvas.create_text(
                LABEL_WIDTH - 5,
                y_high,
                text="H",
                fill=VSCodeTheme.FG_SECONDARY,
                font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_SMALL - 2),
                anchor=tk.E
            )
            self.waveform_canvas.create_text(
                LABEL_WIDTH - 5,
                y_low,
                text="F",
                fill=VSCodeTheme.FG_SECONDARY,
                font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_SMALL - 2),
                anchor=tk.E
            )
            
            # Draw horizontal separator
            if idx > 0:
                self.waveform_canvas.create_line(
                    LABEL_WIDTH, y_base,
                    waveform_width, y_base,
                    fill=VSCodeTheme.BORDER_DEFAULT,
                    width=1,
                    dash=(2, 2)
                )
            
            # Draw waveform trace
            if channel.trace_data:
                self._draw_channel_waveform(
                    channel,
                    LABEL_WIDTH,
                    y_high,
                    y_low,
                    PIXELS_PER_SECOND
                )
        
        # Draw cursor if visible (when stopped)
        if self.cursor_visible and self.cursor_x is not None:
            # Draw vertical line at cursor position
            self.waveform_canvas.create_line(
                self.cursor_x, 0,
                self.cursor_x, waveform_height,
                fill=VSCodeTheme.ACCENT_BLUE,
                width=2
            )
            
            # Calculate time at cursor position
            time_at_cursor = (self.cursor_x - LABEL_WIDTH) / PIXELS_PER_SECOND
            if time_at_cursor >= 0:
                # Format time nicely
                time_text = self._format_time(time_at_cursor)
                
                # Draw time label with background
                text_x = self.cursor_x + 5
                text_y = 5
                
                # Create text to measure its size
                text_id = self.waveform_canvas.create_text(
                    text_x, text_y,
                    text=time_text,
                    fill=VSCodeTheme.FG_PRIMARY,
                    font=(VSCodeTheme.FONT_FAMILY_MONO, VSCodeTheme.FONT_SIZE_SMALL, "bold"),
                    anchor=tk.NW
                )
                
                # Get text bounding box and draw background
                bbox = self.waveform_canvas.bbox(text_id)
                if bbox:
                    padding = 3
                    self.waveform_canvas.create_rectangle(
                        bbox[0] - padding, bbox[1] - padding,
                        bbox[2] + padding, bbox[3] + padding,
                        fill=VSCodeTheme.BG_TERTIARY,
                        outline=VSCodeTheme.ACCENT_BLUE,
                        width=1
                    )
                    # Redraw text on top of background
                    self.waveform_canvas.delete(text_id)
                    self.waveform_canvas.create_text(
                        text_x, text_y,
                        text=time_text,
                        fill=VSCodeTheme.FG_PRIMARY,
                        font=(VSCodeTheme.FONT_FAMILY_MONO, VSCodeTheme.FONT_SIZE_SMALL, "bold"),
                        anchor=tk.NW
                    )
    
    def _draw_channel_waveform(self, channel: Channel, x_offset: int, y_high: float, y_low: float, pixels_per_second: float):
        """
        Draw waveform trace for a single channel.
        
        Args:
            channel: Channel to draw
            x_offset: X offset for waveform start
            y_high: Y coordinate for HIGH state
            y_low: Y coordinate for FLOAT/LOW state
            pixels_per_second: Scale factor for time-to-pixels conversion
        """
        if not channel.trace_data:
            return
        
        # State-to-Y mapping
        def state_to_y(state):
            if state == PinState.HIGH:
                return y_high
            else:  # FLOAT or any other state
                return y_low
        
        # Draw waveform as connected line segments
        prev_x = None
        prev_y = None
        
        for timestamp, state in channel.trace_data:
            # Convert timestamp to X coordinate
            x = x_offset + (timestamp * pixels_per_second)
            y = state_to_y(state)
            
            if prev_x is not None:
                # Draw horizontal line at previous state
                self.waveform_canvas.create_line(
                    prev_x, prev_y,
                    x, prev_y,
                    fill=channel.color,
                    width=2
                )
                
                # Draw vertical transition if state changed
                if prev_y != y:
                    self.waveform_canvas.create_line(
                        x, prev_y,
                        x, y,
                        fill=channel.color,
                        width=2
                    )
            
            prev_x = x
            prev_y = y
        
        # If capturing, extend the last state to current time
        if self.is_capturing and self.start_time > 0 and prev_x is not None and prev_y is not None:
            current_time = time.time() - self.start_time
            current_x = x_offset + (current_time * pixels_per_second)
            
            # Draw horizontal line from last sample to current time
            self.waveform_canvas.create_line(
                prev_x, prev_y,
                current_x, prev_y,
                fill=channel.color,
                width=2
            )
    
    def _format_time(self, seconds: float) -> str:
        """
        Format time value for display.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted string (e.g., "1.234s", "123.4ms", "12.34μs")
        """
        if seconds >= 1.0:
            return f"{seconds:.3f}s"
        elif seconds >= 0.001:
            return f"{seconds * 1000:.3f}ms"
        elif seconds >= 0.000001:
            return f"{seconds * 1000000:.3f}μs"
        else:
            return f"{seconds * 1000000000:.3f}ns"
    
    def _draw_time_axis(self, x_offset: int, y_pos: float, width: float, max_time: float):
        """
        Draw time axis with markers and labels.
        
        Args:
            x_offset: X offset for axis start
            y_pos: Y position for axis
            width: Width of axis
            max_time: Maximum time value in seconds
        """
        # Draw axis line
        self.waveform_canvas.create_line(
            x_offset, y_pos,
            x_offset + width, y_pos,
            fill=VSCodeTheme.FG_SECONDARY,
            width=1
        )
        
        # Calculate nice time intervals
        if max_time <= 0:
            return
        
        # Determine interval (try to get 5-10 markers)
        intervals = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
        target_markers = 8
        interval = max_time / target_markers
        
        # Find closest interval
        chosen_interval = intervals[0]
        for candidate in intervals:
            if candidate >= interval:
                chosen_interval = candidate
                break
        else:
            chosen_interval = intervals[-1]
        
        # Draw markers
        time_marker = 0.0
        while time_marker <= max_time:
            x = x_offset + (time_marker / max_time) * width
            
            # Draw tick mark
            self.waveform_canvas.create_line(
                x, y_pos,
                x, y_pos + 5,
                fill=VSCodeTheme.FG_SECONDARY,
                width=1
            )
            
            # Draw time label
            if time_marker < 1.0:
                label = f"{time_marker * 1000:.0f}ms"
            else:
                label = f"{time_marker:.2f}s"
            
            self.waveform_canvas.create_text(
                x, y_pos + 15,
                text=label,
                fill=VSCodeTheme.FG_SECONDARY,
                font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_SMALL),
                anchor=tk.N
            )
            
            time_marker += chosen_interval
    
    def _on_mouse_move(self, event):
        """Handle mouse movement over waveform canvas."""
        # Only show cursor when not capturing (i.e., stopped with data)
        if not self.is_capturing:
            # Check if we have any trace data
            has_data = any(channel.trace_data for channel in self.channels)
            if has_data:
                self.cursor_x = self.waveform_canvas.canvasx(event.x)
                self.cursor_visible = True
                self._draw_waveforms()
    
    def _on_mouse_leave(self, event):
        """Handle mouse leaving waveform canvas."""
        if self.cursor_visible:
            self.cursor_visible = False
            self.cursor_x = None
            self._draw_waveforms()
    
    def _on_start(self):
        """Handle Start button click."""
        # Hide cursor when starting capture
        self.cursor_visible = False
        self.cursor_x = None
        
        # Check if simulation is running
        if not self.main_window.simulation_mode or not self.main_window.simulation_engine:
            from tkinter import messagebox
            messagebox.showwarning(
                "Simulation Not Running",
                "Please start simulation (F5) before capturing trace data.",
                parent=self.window
            )
            return
        
        # Check if we have channels
        if not self.channels:
            from tkinter import messagebox
            messagebox.showwarning(
                "No Channels",
                "Please add at least one channel before starting capture.",
                parent=self.window
            )
            return
        
        # Clear existing trace data
        for channel in self.channels:
            channel.trace_data.clear()
        
        # Start capturing
        self.is_capturing = True
        self.sample_count = 0
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.clear_button.config(state=tk.DISABLED)  # Disable clear during capture
        self.trigger_button.config(state=tk.DISABLED)  # Disable trigger during capture
        
        # Check if trigger mode is enabled
        if self.trigger_enabled and self.trigger_link_name:
            self.waiting_for_trigger = True
            self.last_trigger_state = None
            self.start_time = 0.0  # Don't start timer until trigger is detected
            self.status_label.config(text="Waiting for trigger...", fg=VSCodeTheme.ACCENT_ORANGE)
        else:
            self.waiting_for_trigger = False
            self.start_time = time.time()  # Start timer immediately
            self.status_label.config(text="Capturing...", fg=VSCodeTheme.ACCENT_GREEN)
        
        # Register callback with simulation engine to capture on stability
        if self.main_window.simulation_engine:
            self.main_window.simulation_engine.set_on_stable_callback(self._on_simulation_stable)
        
        # Start display refresh timer to keep waveforms scrolling
        self._start_display_timer()
        
        # Capture initial state at time 0 (only if not waiting for trigger)
        if not self.waiting_for_trigger:
            self._capture_sample(0.0)
    
    def _on_stop(self):
        """Handle Stop button click."""
        # Stop capturing
        self.is_capturing = False
        
        # Stop display refresh timer
        self._stop_display_timer()
        
        # Unregister callback from simulation engine
        if self.main_window.simulation_engine:
            self.main_window.simulation_engine.set_on_stable_callback(None)
        
        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.NORMAL)
        self.trigger_button.config(state=tk.NORMAL)
        self.waiting_for_trigger = False  # Re-enable clear
        
        # Display total trace duration
        if self.channels and self.channels[0].trace_data:
            duration = time.time() - self.start_time
            self.status_label.config(
                text=f"Stopped - {self.sample_count} samples ({duration:.2f}s)",
                fg=VSCodeTheme.FG_SECONDARY
            )
        else:
            self.status_label.config(text="Stopped", fg=VSCodeTheme.FG_SECONDARY)
        
        # Final waveform update
        self._draw_waveforms()
    
    def _on_clear(self):
        """Handle Clear button click."""
        # Don't allow clear during capture
        if self.is_capturing:
            return
        
        # Clear trace data from all channels
        for channel in self.channels:
            channel.trace_data.clear()
        
        self.start_time = 0.0
        self.sample_count = 0
        self._draw_waveforms()
        self.status_label.config(text="Cleared", fg=VSCodeTheme.FG_SECONDARY)
    
    def _on_trigger(self):
        """Handle Trigger button click - open trigger configuration dialog."""
        # Create trigger configuration dialog
        dialog = tk.Toplevel(self.window)
        dialog.title("Trigger Configuration")
        dialog.geometry("400x350")
        dialog.configure(bg=VSCodeTheme.BG_PRIMARY)
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Center dialog on parent window
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = tk.Frame(dialog, bg=VSCodeTheme.BG_PRIMARY, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Enable/Disable trigger checkbox
        trigger_var = tk.BooleanVar(value=self.trigger_enabled)
        enable_check = tk.Checkbutton(
            main_frame,
            text="Enable Trigger",
            variable=trigger_var,
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            selectcolor=VSCodeTheme.BG_TERTIARY,
            activebackground=VSCodeTheme.BG_PRIMARY,
            activeforeground=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL, "bold")
        )
        enable_check.pack(anchor=tk.W, pady=(0, 15))
        
        # Link name section
        link_frame = tk.Frame(main_frame, bg=VSCodeTheme.BG_PRIMARY)
        link_frame.pack(fill=tk.X, pady=(0, 15))
        
        link_label = tk.Label(
            link_frame,
            text="Trigger Link Name:",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL)
        )
        link_label.pack(anchor=tk.W, pady=(0, 5))
        
        link_entry = tk.Entry(
            link_frame,
            bg=VSCodeTheme.BG_TERTIARY,
            fg=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL),
            relief=tk.FLAT,
            insertbackground=VSCodeTheme.FG_PRIMARY
        )
        link_entry.pack(fill=tk.X)
        link_entry.insert(0, self.trigger_link_name)
        
        # Trigger mode section
        mode_frame = tk.Frame(main_frame, bg=VSCodeTheme.BG_PRIMARY)
        mode_frame.pack(fill=tk.X, pady=(0, 20))
        
        mode_label = tk.Label(
            mode_frame,
            text="Trigger Condition:",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL)
        )
        mode_label.pack(anchor=tk.W, pady=(0, 5))
        
        mode_var = tk.StringVar(value=self.trigger_mode)
        
        # Radio buttons for trigger modes
        rising_radio = tk.Radiobutton(
            mode_frame,
            text="Rising Edge (FLOAT → HIGH)",
            variable=mode_var,
            value="rising",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            selectcolor=VSCodeTheme.BG_TERTIARY,
            activebackground=VSCodeTheme.BG_PRIMARY,
            activeforeground=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL)
        )
        rising_radio.pack(anchor=tk.W, pady=2)
        
        falling_radio = tk.Radiobutton(
            mode_frame,
            text="Falling Edge (HIGH → FLOAT)",
            variable=mode_var,
            value="falling",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            selectcolor=VSCodeTheme.BG_TERTIARY,
            activebackground=VSCodeTheme.BG_PRIMARY,
            activeforeground=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL)
        )
        falling_radio.pack(anchor=tk.W, pady=2)
        
        change_radio = tk.Radiobutton(
            mode_frame,
            text="Any State Change",
            variable=mode_var,
            value="change",
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            selectcolor=VSCodeTheme.BG_TERTIARY,
            activebackground=VSCodeTheme.BG_PRIMARY,
            activeforeground=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL)
        )
        change_radio.pack(anchor=tk.W, pady=2)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=VSCodeTheme.BG_PRIMARY)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        def on_ok():
            self.trigger_enabled = trigger_var.get()
            self.trigger_link_name = link_entry.get().strip()
            self.trigger_mode = mode_var.get()
            
            # Update trigger button appearance to show if enabled
            if self.trigger_enabled and self.trigger_link_name:
                self.trigger_button.config(bg=VSCodeTheme.ACCENT_BLUE)
            else:
                self.trigger_button.config(bg=VSCodeTheme.BUTTON_BG)
            
            # Save trigger settings to current configuration
            self._save_current_configuration()
            
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ok_button = tk.Button(
            button_frame,
            text="OK",
            command=on_ok,
            bg=VSCodeTheme.BUTTON_BG,
            fg=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL),
            relief=tk.FLAT,
            cursor='hand2',
            padx=20,
            pady=5
        )
        ok_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=on_cancel,
            bg=VSCodeTheme.BUTTON_BG,
            fg=VSCodeTheme.FG_PRIMARY,
            font=(VSCodeTheme.FONT_FAMILY_UI, VSCodeTheme.FONT_SIZE_NORMAL),
            relief=tk.FLAT,
            cursor='hand2',
            padx=20,
            pady=5
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def _on_simulation_stable(self):
        """Callback when simulation reaches stable state - capture a sample."""
        # Only capture if still in capturing mode
        if not self.is_capturing:
            return
        
        # Stop if simulation has ended
        if not self.main_window.simulation_mode or not self.main_window.simulation_engine:
            self._on_stop()
            return
        
        # Calculate elapsed time and capture sample
        timestamp = time.time() - self.start_time
        self._capture_sample(timestamp)
    
    def _capture_sample(self, timestamp: float):
        """Capture state of all channels at the given timestamp.
        
        Args:
            timestamp: Time in seconds since capture started
        """
        # Get active document
        tab = self.main_window.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        # Get simulation engine
        engine = self.main_window.simulation_engine
        if not engine:
            return
        
        # If waiting for trigger, check trigger condition first
        if self.waiting_for_trigger:
            trigger_state = self._get_link_state(self.trigger_link_name, tab, engine)
            
            # Check if trigger condition is met
            trigger_detected = False
            if self.last_trigger_state is not None:
                if self.trigger_mode == "rising":
                    # Rising edge: FLOAT → HIGH
                    if self.last_trigger_state == PinState.FLOAT and trigger_state == PinState.HIGH:
                        trigger_detected = True
                elif self.trigger_mode == "falling":
                    # Falling edge: HIGH → FLOAT
                    if self.last_trigger_state == PinState.HIGH and trigger_state == PinState.FLOAT:
                        trigger_detected = True
                elif self.trigger_mode == "change":
                    # Any state change
                    if self.last_trigger_state != trigger_state:
                        trigger_detected = True
            
            self.last_trigger_state = trigger_state
            
            if trigger_detected:
                # Trigger condition met - start recording
                self.waiting_for_trigger = False
                self.start_time = time.time()  # Reset start time to trigger moment
                self.status_label.config(text="Triggered! Capturing...", fg=VSCodeTheme.ACCENT_GREEN)
                # Start with timestamp 0 from the trigger point
                timestamp = 0.0
            else:
                # Still waiting for trigger - don't record samples
                return
        
        # Capture state for each channel
        for channel in self.channels:
            if not channel.link_name:
                # No LINK name specified - record FLOAT
                channel.trace_data.append((timestamp, PinState.FLOAT))
                continue
            
            # Get state from the VNET
            state = self._get_link_state(channel.link_name, tab, engine)
            
            # Append trace data
            channel.trace_data.append((timestamp, state))
        
        # Update sample count
        self.sample_count += 1
        
        # Update status (display is updated by timer)
        self.status_label.config(
            text=f"Capturing... {self.sample_count} samples ({timestamp:.2f}s)",
            fg=VSCodeTheme.ACCENT_GREEN
        )
    
    def _get_link_state(self, link_name: str, tab, engine) -> PinState:
        """Get the current state of a link by name.
        
        Args:
            link_name: Name of the link to find
            tab: Active document tab
            engine: Simulation engine
            
        Returns:
            Current PinState of the link (HIGH or FLOAT)
        """
        if not link_name or not tab or not engine:
            return PinState.FLOAT
        
        # Find component with matching link_name across all pages
        target_component = None
        for page in tab.document.pages.values():
            for component in page.components.values():
                if (hasattr(component, 'link_name') and 
                    component.link_name == link_name):
                    target_component = component
                    break
            if target_component:
                break
        
        # Get state from the VNET that the component is connected to
        state = PinState.FLOAT  # Default to FLOAT
        
        if target_component:
            # Get a tab from the component to find its VNET
            tab_id = None
            
            # Try to get a tab from the component's pin(s)
            if hasattr(target_component, '_pin') and target_component._pin:
                # Single pin components (Clock, Link, Indicator, etc.)
                if hasattr(target_component._pin, 'tabs') and target_component._pin.tabs:
                    tab_id = next(iter(target_component._pin.tabs.keys()), None)
            elif hasattr(target_component, 'pins') and target_component.pins:
                # Multi-pin components - use first pin's first tab
                first_pin = next(iter(target_component.pins.values()), None)
                if first_pin and hasattr(first_pin, 'tabs') and first_pin.tabs:
                    tab_id = next(iter(first_pin.tabs.keys()), None)
            
            # If we found a tab, get the VNET state
            if tab_id and engine.vnet_manager:
                vnet = engine.vnet_manager.get_vnet_for_tab(tab_id)
                if vnet:
                    state = vnet.state
        
        return state
    
    def _start_display_timer(self):
        """Start the display refresh timer."""
        if self.display_timer_id is None:
            self._refresh_display()
    
    def _stop_display_timer(self):
        """Stop the display refresh timer."""
        if self.display_timer_id:
            try:
                self.window.after_cancel(self.display_timer_id)
            except Exception:
                pass
            self.display_timer_id = None
    
    def _refresh_display(self):
        """Refresh the waveform display periodically."""
        # Stop if no longer capturing
        if not self.is_capturing:
            self.display_timer_id = None
            return
        
        # Update the waveform display
        self._draw_waveforms()
        
        # Schedule next refresh
        self.display_timer_id = self.window.after(self.display_refresh_ms, self._refresh_display)
    
    # === Configuration Management ===
    
    def _load_configurations(self):
        """Load configurations from document and populate dropdown."""
        # Get active document
        tab = self.main_window.file_tabs.get_active_tab()
        if not tab or not tab.document:
            # No document - create a default config
            self._add_channel()
            return
        
        document = tab.document
        configs = document.get_all_logic_analyser_configs()
        
        if not configs:
            # No existing configs - create a default one
            config_id = document.id_manager.generate_id()
            document.add_logic_analyser_config(
                config_id,
                "Default Configuration",
                []
            )
            self.current_config_id = config_id
            self.current_config_name = "Default Configuration"
            self._add_channel()
        else:
            # Load first config
            first_config = configs[0]
            self.current_config_id = first_config['config_id']
            self.current_config_name = first_config['name']
            self._apply_configuration(first_config)
        
        self._refresh_config_dropdown()
    
    def _refresh_config_dropdown(self):
        """Refresh the configuration dropdown with current configs."""
        tab = self.main_window.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        configs = tab.document.get_all_logic_analyser_configs()
        config_names = [cfg['name'] for cfg in configs]
        
        self.config_dropdown['values'] = config_names
        if self.current_config_name in config_names:
            self.config_var.set(self.current_config_name)
        elif config_names:
            self.config_var.set(config_names[0])
        
        # Enable/disable remove button based on config count
        if len(configs) <= 1:
            self.remove_config_btn.config(state=tk.DISABLED)
        else:
            self.remove_config_btn.config(state=tk.NORMAL)
    
    def _save_current_configuration(self):
        """Save current channels to the active configuration."""
        tab = self.main_window.file_tabs.get_active_tab()
        if not tab or not tab.document or not self.current_config_id:
            return
        
        # Build channels list
        channels_data = []
        for channel in self.channels:
            channels_data.append({
                'name': channel.name,
                'link_name': channel.link_name,
                'color': channel.color
            })
        
        # Update configuration in document (including trigger settings)
        tab.document.update_logic_analyser_config(
            self.current_config_id,
            name=self.current_config_name,
            channels=channels_data,
            trigger_enabled=self.trigger_enabled,
            trigger_link_name=self.trigger_link_name,
            trigger_mode=self.trigger_mode
        )
    
    def _apply_configuration(self, config: dict):
        """Apply a configuration (load its channels)."""
        # Clear existing channels
        self.channels.clear()
        
        # Load channels from config
        for channel_data in config.get('channels', []):
            channel = Channel(
                name=channel_data.get('name', ''),
                link_name=channel_data.get('link_name', '')
            )
            channel.color = channel_data.get('color', VSCodeTheme.ACCENT_GREEN)
            self.channels.append(channel)
        
        # Load trigger settings from config
        self.trigger_enabled = config.get('trigger_enabled', False)
        self.trigger_link_name = config.get('trigger_link_name', '')
        self.trigger_mode = config.get('trigger_mode', 'rising')
        
        # Update trigger button appearance
        if self.trigger_enabled and self.trigger_link_name:
            self.trigger_button.config(bg=VSCodeTheme.ACCENT_BLUE)
        else:
            self.trigger_button.config(bg=VSCodeTheme.BUTTON_BG)
        
        # If no channels, add one default
        if not self.channels:
            self._add_channel()
        
        self._refresh_channel_list()
        self._draw_waveforms()
    
    def _on_config_selected(self, event):
        """Handle configuration selection from dropdown."""
        # Save current config before switching
        self._save_current_configuration()
        
        selected_name = self.config_var.get()
        
        tab = self.main_window.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        # Find config with this name
        configs = tab.document.get_all_logic_analyser_configs()
        for config in configs:
            if config['name'] == selected_name:
                self.current_config_id = config['config_id']
                self.current_config_name = config['name']
                self._apply_configuration(config)
                break
    
    def _on_time_base_changed(self, event):
        """Handle time base selection change."""
        # Parse the time base value (e.g., "2s" -> 2.0)
        value_str = self.time_base_var.get()
        try:
            # Remove the 's' suffix and convert to float
            self.time_base_seconds = float(value_str.rstrip('s'))
        except ValueError:
            # Default to 2 seconds if parsing fails
            self.time_base_seconds = 2.0
        
        # Redraw waveforms with new time scale
        self._draw_waveforms()
    
    def _add_new_config(self):
        """Add a new configuration."""
        from tkinter import simpledialog
        
        # Save current config first
        self._save_current_configuration()
        
        tab = self.main_window.file_tabs.get_active_tab()
        if not tab or not tab.document:
            return
        
        # Ask for config name
        name = simpledialog.askstring(
            "New Configuration",
            "Enter configuration name:",
            parent=self.window
        )
        
        if not name or not name.strip():
            return
        
        name = name.strip()
        
        # Create new config
        config_id = tab.document.id_manager.generate_id()
        tab.document.add_logic_analyser_config(
            config_id,
            name,
            []
        )
        
        # Switch to new config
        self.current_config_id = config_id
        self.current_config_name = name
        
        # Clear channels and add one default
        self.channels.clear()
        self._add_channel()
        
        # Reset trigger settings to defaults for new config
        self.trigger_enabled = False
        self.trigger_link_name = ''
        self.trigger_mode = 'rising'
        self.trigger_button.config(bg=VSCodeTheme.BUTTON_BG)
        
        self._refresh_config_dropdown()
        self._refresh_channel_list()
        self._draw_waveforms()
    
    def _remove_current_config(self):
        """Remove the current configuration."""
        from tkinter import messagebox
        
        tab = self.main_window.file_tabs.get_active_tab()
        if not tab or not tab.document or not self.current_config_id:
            return
        
        # Confirm deletion
        response = messagebox.askyesno(
            "Remove Configuration",
            f"Are you sure you want to remove '{self.current_config_name}'?",
            parent=self.window
        )
        
        if not response:
            return
        
        # Remove from document
        tab.document.remove_logic_analyser_config(self.current_config_id)
        
        # Switch to first remaining config
        configs = tab.document.get_all_logic_analyser_configs()
        if configs:
            first_config = configs[0]
            self.current_config_id = first_config['config_id']
            self.current_config_name = first_config['name']
            self._apply_configuration(first_config)
        else:
            # No configs left - create a default
            config_id = tab.document.id_manager.generate_id()
            tab.document.add_logic_analyser_config(
                config_id,
                "Default Configuration",
                []
            )
            self.current_config_id = config_id
            self.current_config_name = "Default Configuration"
            self.channels.clear()
            self._add_channel()
        
        self._refresh_config_dropdown()
    
    def _rename_current_config(self):
        """Rename the current configuration."""
        from tkinter import simpledialog
        
        tab = self.main_window.file_tabs.get_active_tab()
        if not tab or not tab.document or not self.current_config_id:
            return
        
        # Ask for new name
        new_name = simpledialog.askstring(
            "Rename Configuration",
            "Enter new name:",
            initialvalue=self.current_config_name,
            parent=self.window
        )
        
        if not new_name or not new_name.strip():
            return
        
        new_name = new_name.strip()
        
        # Update name in document
        tab.document.update_logic_analyser_config(
            self.current_config_id,
            name=new_name
        )
        
        self.current_config_name = new_name
        self._refresh_config_dropdown()
    
    def _on_close(self):
        """Handle window close event."""
        # Save current configuration before closing
        self._save_current_configuration()
        
        if self.is_capturing:
            self._on_stop()
        self.window.destroy()
    
    def show(self):
        """Show the window."""
        self.window.deiconify()
        self.window.lift()
