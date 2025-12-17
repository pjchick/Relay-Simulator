"""
Page tab bar for multi-page navigation within documents.

Provides tab-based navigation between pages within a document, with functionality
for adding, renaming, and deleting pages.
"""

import tkinter as tk
from typing import Callable, Optional, List
from gui.theme import VSCodeTheme
from core.document import Document
from core.page import Page


class PageTabBar:
    """
    Tab bar for navigating between pages within a document.
    
    Features:
    - Visual tabs for each page with active highlighting
    - Add page button (+)
    - Page renaming (double-click on tab)
    - Page deletion (close button on tabs, except first page)
    - Callbacks for page switching
    """
    
    def __init__(self, parent: tk.Widget):
        """
        Initialize the page tab bar.
        
        Args:
            parent: Parent tkinter widget
        """
        self.parent = parent
        self.current_document: Optional[Document] = None
        self.active_page_id: Optional[str] = None
        
        # Callbacks
        self.on_page_switch: Optional[Callable[[str], None]] = None
        self.on_page_added: Optional[Callable[[str], None]] = None
        self.on_page_deleted: Optional[Callable[[str], None]] = None
        self.on_page_renamed: Optional[Callable[[str, str], None]] = None
        self.on_pages_reordered: Optional[Callable[[List[str]], None]] = None

        # Drag-to-reorder state
        self._drag_page_id: Optional[str] = None
        self._drag_start_x_root: int = 0
        self._dragging: bool = False
        self._drag_grab_widget: Optional[tk.Widget] = None
        
        self._create_widgets()
        
    def _create_widgets(self) -> None:
        """Create the page tab bar widgets."""
        # Main frame for tab bar
        self.frame = tk.Frame(
            self.parent,
            bg=VSCodeTheme.BG_SECONDARY,
            height=35
        )
        self.frame.pack_propagate(False)
        
        # Container for tabs (scrollable if needed)
        self.tabs_container = tk.Frame(
            self.frame,
            bg=VSCodeTheme.BG_SECONDARY
        )
        self.tabs_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add page button
        self.add_button = tk.Button(
            self.frame,
            text="+",
            font=VSCodeTheme.get_font('normal'),
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_PRIMARY,
            activebackground=VSCodeTheme.BG_ACTIVE,
            activeforeground=VSCodeTheme.FG_PRIMARY,
            relief=tk.FLAT,
            padx=VSCodeTheme.PADDING_MEDIUM,
            command=self._on_add_page
        )
        self.add_button.pack(side=tk.RIGHT, padx=VSCodeTheme.PADDING_SMALL)
        
        # Dictionary to store tab widgets
        self.tab_widgets: dict[str, tk.Frame] = {}
        
    def pack(self, **kwargs) -> None:
        """Pack the page tab bar."""
        self.frame.pack(**kwargs)
        
    def set_document(self, document: Optional[Document]) -> None:
        """
        Set the current document and display its pages.
        
        Args:
            document: Document to display pages for, or None to clear
        """
        self.current_document = document
        self._refresh_tabs()
        
    def _refresh_tabs(self) -> None:
        """Refresh the tab display based on current document."""
        # Clear existing tabs
        for widget in self.tabs_container.winfo_children():
            widget.destroy()
        self.tab_widgets.clear()
        
        if not self.current_document:
            self.active_page_id = None
            return
            
        # Create tabs for each page
        pages = self.current_document.get_all_pages()
        for i, page in enumerate(pages):
            self._create_page_tab(page, is_first=(i == 0))
            
        # Check if current active_page_id is valid for this document
        page_ids = [p.page_id for p in pages]
        if self.active_page_id not in page_ids:
            # Reset to first page if current active is not in this document
            if pages:
                self.set_active_page(pages[0].page_id)
        else:
            # Re-activate the current page to update visual state
            if self.active_page_id:
                self.set_active_page(self.active_page_id)
            
    def _create_page_tab(self, page: Page, is_first: bool = False) -> None:
        """
        Create a tab widget for a page.
        
        Args:
            page: Page to create tab for
            is_first: Whether this is the first page (cannot be deleted)
        """
        # Tab frame
        tab_frame = tk.Frame(
            self.tabs_container,
            bg=VSCodeTheme.BG_SECONDARY,
            relief=tk.FLAT,
            borderwidth=1
        )
        tab_frame.pack(side=tk.LEFT, padx=1, pady=VSCodeTheme.PADDING_SMALL)
        
        # Page name label
        name_label = tk.Label(
            tab_frame,
            text=page.name,
            font=VSCodeTheme.get_font('normal'),
            bg=VSCodeTheme.BG_SECONDARY,
            fg=VSCodeTheme.FG_PRIMARY,
            padx=VSCodeTheme.PADDING_MEDIUM,
            pady=VSCodeTheme.PADDING_SMALL
        )
        name_label.pack(side=tk.LEFT)

        # Bind interactions
        tab_frame.bind('<ButtonPress-1>', lambda e: self._on_tab_press(e, page.page_id))
        tab_frame.bind('<B1-Motion>', self._on_tab_motion)
        tab_frame.bind('<ButtonRelease-1>', self._on_tab_release)

        name_label.bind('<ButtonPress-1>', lambda e: self._on_tab_press(e, page.page_id))
        name_label.bind('<B1-Motion>', self._on_tab_motion)
        name_label.bind('<ButtonRelease-1>', self._on_tab_release)

        # Double-click to rename
        name_label.bind('<Double-Button-1>', lambda e: self._start_rename(page.page_id))
        
        # Close button (only if not first page)
        if not is_first:
            close_btn = tk.Label(
                tab_frame,
                text="×",
                font=VSCodeTheme.get_font('normal'),
                bg=VSCodeTheme.BG_SECONDARY,
                fg=VSCodeTheme.FG_SECONDARY,
                padx=VSCodeTheme.PADDING_SMALL,
                cursor="hand2"
            )
            close_btn.pack(side=tk.RIGHT)
            close_btn.bind('<Button-1>', lambda e: self._on_delete_page(page.page_id))
            close_btn.bind('<Enter>', lambda e: close_btn.config(fg=VSCodeTheme.ACCENT_RED))
            close_btn.bind('<Leave>', lambda e: close_btn.config(fg=VSCodeTheme.FG_SECONDARY))
        
        # Store reference
        self.tab_widgets[page.page_id] = tab_frame

    def _on_tab_press(self, event, page_id: str) -> None:
        """Begin potential drag (or click) on a page tab."""
        if not self.current_document:
            return

        # Ensure we continue receiving motion/release events even if the
        # cursor leaves the label/frame during the drag.
        try:
            self._drag_grab_widget = event.widget
            self._drag_grab_widget.grab_set()
        except Exception:
            self._drag_grab_widget = None

        self._drag_page_id = page_id
        self._drag_start_x_root = int(getattr(event, 'x_root', 0))
        self._dragging = False

    def _on_tab_motion(self, event) -> None:
        """Track movement to decide if this becomes a drag."""
        if not self._drag_page_id:
            return
        dx = int(getattr(event, 'x_root', 0)) - self._drag_start_x_root
        if abs(dx) >= 6:
            self._dragging = True

    def _compute_drop_index(self, x_root: int, page_ids: List[str]) -> int:
        """Compute insertion index based on x_root compared to tab centers."""
        centers: List[float] = []
        for pid in page_ids:
            tab = self.tab_widgets.get(pid)
            if not tab:
                continue
            try:
                tab.update_idletasks()
                cx = tab.winfo_rootx() + (tab.winfo_width() / 2)
                centers.append(cx)
            except Exception:
                centers.append(float('inf'))

        # Default to end.
        for idx, center in enumerate(centers):
            if x_root < center:
                return idx
        return len(page_ids)

    def _on_tab_release(self, event) -> None:
        """Complete click or drag-to-reorder on release."""
        if not self.current_document:
            return

        if self._drag_grab_widget is not None:
            try:
                self._drag_grab_widget.grab_release()
            except Exception:
                pass
            self._drag_grab_widget = None

        page_id = self._drag_page_id
        dragging = self._dragging

        # Reset drag state early.
        self._drag_page_id = None
        self._dragging = False

        if not page_id:
            return

        if not dragging:
            # Treat as a normal click.
            self.set_active_page(page_id)
            return

        pages = self.current_document.get_all_pages()
        page_ids = [p.page_id for p in pages]
        if not page_ids or page_id not in page_ids:
            return

        # Do not allow moving before the first pinned page.
        try:
            from_index = page_ids.index(page_id)
        except ValueError:
            return

        x_root = int(getattr(event, 'x_root', 0))
        drop_index = self._compute_drop_index(x_root, page_ids)

        # Convert insertion index to final index after removal.
        new_index = drop_index
        if drop_index > from_index:
            new_index = drop_index - 1

        if self.current_document.move_page(page_id, new_index):
            # Refresh UI to reflect new order.
            active = self.active_page_id
            self._refresh_tabs()
            if active:
                self.set_active_page(active)

            if self.on_pages_reordered:
                self.on_pages_reordered([p.page_id for p in self.current_document.get_all_pages()])
        
    def set_active_page(self, page_id: str) -> None:
        """
        Set the active page and update visual state.
        
        Args:
            page_id: ID of page to activate
        """
        if not self.current_document:
            return
            
        # Verify page exists
        page = self.current_document.get_page(page_id)
        if not page:
            return
            
        # Update active page
        old_page_id = self.active_page_id
        self.active_page_id = page_id
        
        # Update tab colors
        for pid, tab_frame in self.tab_widgets.items():
            if pid == page_id:
                # Active tab
                tab_frame.config(bg=VSCodeTheme.BG_ACTIVE)
                for child in tab_frame.winfo_children():
                    child.config(bg=VSCodeTheme.BG_ACTIVE)
            else:
                # Inactive tab
                tab_frame.config(bg=VSCodeTheme.BG_SECONDARY)
                for child in tab_frame.winfo_children():
                    child.config(bg=VSCodeTheme.BG_SECONDARY)
                    
        # Trigger callback
        if self.on_page_switch and old_page_id != page_id:
            self.on_page_switch(page_id)
            
    def _on_add_page(self) -> None:
        """Handle add page button click."""
        if not self.current_document:
            return
            
        # Generate page name
        pages = self.current_document.get_all_pages()
        page_num = len(pages) + 1
        page_name = f"Page {page_num}"
        
        # Create new page
        new_page = self.current_document.create_page(page_name)
        
        # Refresh tabs
        self._refresh_tabs()
        
        # Set new page as active
        self.set_active_page(new_page.page_id)
        
        # Trigger callback
        if self.on_page_added:
            self.on_page_added(new_page.page_id)
            
    def _on_delete_page(self, page_id: str) -> None:
        """
        Handle page deletion.
        
        Args:
            page_id: ID of page to delete
        """
        if not self.current_document:
            return
            
        # Get page
        page = self.current_document.get_page(page_id)
        if not page:
            return
            
        # Don't delete first page
        pages = self.current_document.get_all_pages()
        if pages and pages[0].page_id == page_id:
            return
            
        # Confirm deletion
        from tkinter import messagebox
        result = messagebox.askyesno(
            "Delete Page",
            f"Delete page '{page.name}'?",
            parent=self.frame
        )
        
        if not result:
            return
            
        # If deleting active page, switch to another page first
        if page_id == self.active_page_id:
            # Find another page to activate
            for p in pages:
                if p.page_id != page_id:
                    self.set_active_page(p.page_id)
                    break
                    
        # Delete the page
        self.current_document.delete_page(page_id)
        
        # Refresh tabs
        self._refresh_tabs()
        
        # Trigger callback
        if self.on_page_deleted:
            self.on_page_deleted(page_id)
            
    def _start_rename(self, page_id: str) -> None:
        """
        Start renaming a page (show entry widget).
        
        Args:
            page_id: ID of page to rename
        """
        if not self.current_document:
            return
            
        page = self.current_document.get_page(page_id)
        if not page:
            return
            
        tab_frame = self.tab_widgets.get(page_id)
        if not tab_frame:
            return
            
        # Find the name label
        name_label = None
        for child in tab_frame.winfo_children():
            if isinstance(child, tk.Label) and child.cget('text') == page.name:
                name_label = child
                break
                
        if not name_label:
            return
            
        # Hide label, show entry
        name_label.pack_forget()
        
        # Create entry widget
        entry = tk.Entry(
            tab_frame,
            font=VSCodeTheme.get_font('normal'),
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            insertbackground=VSCodeTheme.FG_PRIMARY,
            width=15
        )
        entry.insert(0, page.name)
        entry.select_range(0, tk.END)
        entry.pack(side=tk.LEFT, padx=VSCodeTheme.PADDING_SMALL)
        entry.focus_set()
        
        def finish_rename(event=None):
            new_name = entry.get().strip()
            if new_name and new_name != page.name:
                # Update page name
                page.name = new_name
                
                # Trigger callback
                if self.on_page_renamed:
                    self.on_page_renamed(page_id, new_name)
                    
            # Refresh tabs
            self._refresh_tabs()
            
        def cancel_rename(event=None):
            # Just refresh tabs
            self._refresh_tabs()
            
        # Bind events
        entry.bind('<Return>', finish_rename)
        entry.bind('<Escape>', cancel_rename)
        entry.bind('<FocusOut>', finish_rename)
        
    def get_active_page_id(self) -> Optional[str]:
        """
        Get the currently active page ID.
        
        Returns:
            Active page ID, or None if no page active
        """
        return self.active_page_id
        
    def get_page_count(self) -> int:
        """
        Get the number of pages in the current document.
        
        Returns:
            Number of pages, or 0 if no document
        """
        if not self.current_document:
            return 0
        return len(self.current_document.get_all_pages())
