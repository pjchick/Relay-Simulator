"""
File Tab System for Multi-Document Support

Provides FileTabBar class for managing multiple open documents with
notebook-style tabs, including unsaved change tracking and tab switching.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Callable
from gui.theme import VSCodeTheme


class FileTab:
    """
    Represents a single file tab with state tracking.
    """
    
    def __init__(self, tab_id: str, filename: str, filepath: Optional[str] = None):
        """
        Initialize file tab.
        
        Args:
            tab_id: Unique tab identifier
            filename: Display name (e.g., "Untitled-1" or "circuit.rsim")
            filepath: Full file path (None for unsaved documents)
        """
        self.tab_id = tab_id
        self.filename = filename
        self.filepath = filepath
        self.is_modified = False
        self.document = None  # Will hold Document instance
        
    def get_display_name(self) -> str:
        """
        Get tab display name with modified indicator.
        
        Returns:
            str: Display name with * if modified
        """
        if self.is_modified:
            return f"{self.filename} *"
        return self.filename
    
    def set_modified(self, modified: bool) -> None:
        """
        Set modified state.
        
        Args:
            modified: True if document has unsaved changes
        """
        self.is_modified = modified


class FileTabBar:
    """
    Manages file tabs for multi-document support.
    
    Provides notebook-style tabs with:
    - Active tab highlighting
    - Close buttons on each tab
    - Modified indicator (*)
    - Tab switching (blocked during simulation)
    - New document creation
    """
    
    def __init__(self, parent: tk.Widget):
        """
        Initialize file tab bar.
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.tabs: Dict[str, FileTab] = {}
        self.tab_order: List[str] = []  # Maintains display order
        self.active_tab_id: Optional[str] = None
        self.next_untitled_number = 1
        self.is_simulation_running = False
        
        # Callbacks
        self.on_tab_switch: Optional[Callable[[str], None]] = None
        self.on_tab_close: Optional[Callable[[str], bool]] = None  # Returns True if closed
        self.on_tab_modified: Optional[Callable[[str, bool], None]] = None
        
        # Create UI
        self._create_widgets()
        
    def _create_widgets(self) -> None:
        """Create tab bar widgets."""
        # Container frame for tab bar
        self.frame = tk.Frame(self.parent, bg=VSCodeTheme.BG_SECONDARY, height=32)
        self.frame.pack(side=tk.TOP, fill=tk.X)
        self.frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Tab container (for individual tabs)
        self.tab_container = tk.Frame(self.frame, bg=VSCodeTheme.BG_SECONDARY)
        self.tab_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
    def add_tab(self, filename: str, filepath: Optional[str] = None, 
                document=None) -> str:
        """
        Add a new tab.
        
        Args:
            filename: Display filename
            filepath: Full file path (None for unsaved)
            document: Document instance
            
        Returns:
            str: Tab ID
        """
        # Generate unique tab ID
        tab_id = f"tab_{len(self.tabs)}_{filename}"
        
        # Create tab
        tab = FileTab(tab_id, filename, filepath)
        tab.document = document
        self.tabs[tab_id] = tab
        self.tab_order.append(tab_id)
        
        # Create tab widget
        self._create_tab_widget(tab_id)
        
        # Set as active if first tab
        if len(self.tabs) == 1:
            self.set_active_tab(tab_id)
        
        return tab_id
    
    def add_untitled_tab(self, document=None) -> str:
        """
        Add a new untitled tab.
        
        Args:
            document: Document instance
            
        Returns:
            str: Tab ID
        """
        filename = f"Untitled-{self.next_untitled_number}"
        self.next_untitled_number += 1
        return self.add_tab(filename, None, document)
    
    def _create_tab_widget(self, tab_id: str) -> None:
        """
        Create visual tab widget.
        
        Args:
            tab_id: Tab identifier
        """
        tab = self.tabs[tab_id]
        
        # Tab frame
        tab_frame = tk.Frame(
            self.tab_container,
            bg=VSCodeTheme.BG_SECONDARY,
            relief=tk.FLAT,
            borderwidth=0
        )
        tab_frame.pack(side=tk.LEFT, padx=1)
        
        # Inner content frame with padding
        content_frame = tk.Frame(
            tab_frame,
            bg=VSCodeTheme.BG_SECONDARY,
            padx=VSCodeTheme.PADDING_MEDIUM,
            pady=VSCodeTheme.PADDING_SMALL
        )
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tab label (filename)
        label = tk.Label(
            content_frame,
            text=tab.get_display_name(),
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_PRIMARY,
            font=VSCodeTheme.get_font(),
            cursor="hand2"
        )
        label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = tk.Label(
            content_frame,
            text="×",
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_SECONDARY,
            font=VSCodeTheme.get_font(size=12),
            cursor="hand2",
            padx=VSCodeTheme.PADDING_SMALL
        )
        close_btn.pack(side=tk.LEFT)
        
        # Store widget references
        tab_frame._tab_id = tab_id
        tab_frame._label = label
        tab_frame._close_btn = close_btn
        tab_frame._content_frame = content_frame
        
        # Bind events
        label.bind("<Button-1>", lambda e, tid=tab_id: self._on_tab_click(tid))
        close_btn.bind("<Button-1>", lambda e, tid=tab_id: self._on_close_click(tid))
        
        # Hover effects for close button
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=VSCodeTheme.FG_PRIMARY))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=VSCodeTheme.FG_SECONDARY))
        
        # Store frame reference on tab
        tab._frame = tab_frame
        
    def _on_tab_click(self, tab_id: str) -> None:
        """
        Handle tab click event.
        
        Args:
            tab_id: Tab identifier
        """
        if self.is_simulation_running:
            return  # Cannot switch tabs during simulation
        
        self.set_active_tab(tab_id)
        
    def _on_close_click(self, tab_id: str) -> None:
        """
        Handle close button click.
        
        Args:
            tab_id: Tab identifier
        """
        self.close_tab(tab_id)
        
    def set_active_tab(self, tab_id: str) -> None:
        """
        Set the active tab.
        
        Args:
            tab_id: Tab identifier
        """
        if tab_id not in self.tabs:
            return
        
        if self.is_simulation_running and self.active_tab_id != tab_id:
            return  # Cannot switch during simulation
        
        old_tab_id = self.active_tab_id
        self.active_tab_id = tab_id
        
        # Update visual appearance
        self._update_tab_appearance()
        
        # Notify callback
        if self.on_tab_switch and old_tab_id != tab_id:
            self.on_tab_switch(tab_id)
    
    def _update_tab_appearance(self) -> None:
        """Update visual appearance of all tabs."""
        for tid, tab in self.tabs.items():
            if not hasattr(tab, '_frame'):
                continue
            
            frame = tab._frame
            content_frame = frame._content_frame
            label = frame._label
            
            # Active tab highlighting
            if tid == self.active_tab_id:
                content_frame.config(bg=VSCodeTheme.BG_PRIMARY)
                label.config(bg=VSCodeTheme.BG_PRIMARY, fg=VSCodeTheme.FG_PRIMARY)
                frame._close_btn.config(bg=VSCodeTheme.BG_PRIMARY)
            else:
                content_frame.config(bg=VSCodeTheme.BG_SECONDARY)
                label.config(bg=VSCodeTheme.BG_SECONDARY, fg=VSCodeTheme.FG_SECONDARY)
                frame._close_btn.config(bg=VSCodeTheme.BG_SECONDARY)
            
            # Update text (in case modified state changed)
            label.config(text=tab.get_display_name())
    
    def close_tab(self, tab_id: str) -> bool:
        """
        Close a tab.
        
        Args:
            tab_id: Tab identifier
            
        Returns:
            bool: True if closed, False if cancelled
        """
        if tab_id not in self.tabs:
            return False
        
        # Call callback (returns True if can close)
        if self.on_tab_close:
            if not self.on_tab_close(tab_id):
                return False  # User cancelled
        
        # Remove tab
        tab = self.tabs[tab_id]
        self.tab_order.remove(tab_id)
        del self.tabs[tab_id]
        
        # Destroy widget
        if hasattr(tab, '_frame'):
            tab._frame.destroy()
        
        # If was active tab, activate another
        if self.active_tab_id == tab_id:
            if self.tab_order:
                # Activate previous tab in order, or first if none before
                idx = max(0, len(self.tab_order) - 1)
                self.set_active_tab(self.tab_order[idx])
            else:
                self.active_tab_id = None
        
        return True
    
    def get_active_tab(self) -> Optional[FileTab]:
        """
        Get the active tab.
        
        Returns:
            FileTab: Active tab or None
        """
        if self.active_tab_id:
            return self.tabs.get(self.active_tab_id)
        return None
    
    def get_tab(self, tab_id: str) -> Optional[FileTab]:
        """
        Get tab by ID.
        
        Args:
            tab_id: Tab identifier
            
        Returns:
            FileTab: Tab or None
        """
        return self.tabs.get(tab_id)
    
    def get_tab_by_filepath(self, filepath: str) -> Optional[FileTab]:
        """
        Get tab by file path.
        
        Args:
            filepath: File path
            
        Returns:
            FileTab: Tab or None
        """
        for tab in self.tabs.values():
            if tab.filepath == filepath:
                return tab
        return None
    
    def set_tab_modified(self, tab_id: str, modified: bool) -> None:
        """
        Set tab modified state.
        
        Args:
            tab_id: Tab identifier
            modified: Modified state
        """
        tab = self.tabs.get(tab_id)
        if tab:
            tab.set_modified(modified)
            self._update_tab_appearance()
            
            # Notify callback
            if self.on_tab_modified:
                self.on_tab_modified(tab_id, modified)
    
    def set_tab_filepath(self, tab_id: str, filepath: str, filename: str) -> None:
        """
        Set tab file path and name (after Save As).
        
        Args:
            tab_id: Tab identifier
            filepath: New file path
            filename: New filename
        """
        tab = self.tabs.get(tab_id)
        if tab:
            tab.filepath = filepath
            tab.filename = filename
            self._update_tab_appearance()
    
    def set_simulation_running(self, running: bool) -> None:
        """
        Set simulation running state (prevents tab switching).
        
        Args:
            running: True if simulation is running
        """
        self.is_simulation_running = running
    
    def get_tab_count(self) -> int:
        """
        Get number of open tabs.
        
        Returns:
            int: Tab count
        """
        return len(self.tabs)
    
    def has_unsaved_changes(self) -> bool:
        """
        Check if any tab has unsaved changes.
        
        Returns:
            bool: True if any tab is modified
        """
        return any(tab.is_modified for tab in self.tabs.values())
    
    def get_all_tabs(self) -> List[FileTab]:
        """
        Get all tabs in display order.
        
        Returns:
            list: List of FileTab instances
        """
        return [self.tabs[tab_id] for tab_id in self.tab_order if tab_id in self.tabs]
