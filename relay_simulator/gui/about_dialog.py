"""
About Dialog for Relay Simulator

Displays application version and build information.
"""

import tkinter as tk
from tkinter import ttk
from gui.theme import VSCodeTheme
from engine.version import get_build_info


class AboutDialog:
    """
    About dialog showing version and build information.
    """
    
    def __init__(self, parent):
        """
        Initialize the About dialog.
        
        Args:
            parent: Parent window
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("About Relay Simulator")
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Get build information
        build_info = get_build_info()
        
        # Configure dialog background
        self.dialog.configure(bg=VSCodeTheme.BG_PRIMARY)
        
        # Main frame with padding
        main_frame = tk.Frame(
            self.dialog,
            bg=VSCodeTheme.BG_PRIMARY,
            padx=30,
            pady=20
        )
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Application name
        app_name = tk.Label(
            main_frame,
            text="Relay Simulator",
            font=("Segoe UI", 18, "bold"),
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY
        )
        app_name.pack(pady=(0, 5))
        
        # Description
        description = tk.Label(
            main_frame,
            text=build_info['description'],
            font=VSCodeTheme.get_font('normal'),
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_SECONDARY
        )
        description.pack(pady=(0, 15))
        
        # Separator
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 15))
        
        # Info frame for version details
        info_frame = tk.Frame(main_frame, bg=VSCodeTheme.BG_PRIMARY)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # Version
        self._add_info_row(
            info_frame,
            "Version:",
            build_info['version']
        )
        
        # Build number (Git commit)
        if build_info['git_commit'] != 'unknown':
            build_label = build_info['git_commit']
            if build_info['git_dirty']:
                build_label += " (modified)"
            
            self._add_info_row(
                info_frame,
                "Build:",
                build_label
            )
        
        # Branch
        if build_info['git_branch'] != 'unknown':
            self._add_info_row(
                info_frame,
                "Branch:",
                build_info['git_branch']
            )
        
        # Commit date
        if build_info['git_date'] != 'unknown':
            # Format date nicely (just the date part)
            date_str = build_info['git_date'].split()[0] if build_info['git_date'] else 'unknown'
            self._add_info_row(
                info_frame,
                "Build Date:",
                date_str
            )
        
        # Full commit hash (in smaller font, selectable)
        if build_info['git_commit_full'] != 'unknown':
            commit_frame = tk.Frame(info_frame, bg=VSCodeTheme.BG_PRIMARY)
            commit_frame.pack(fill=tk.X, pady=(10, 0))
            
            commit_label = tk.Label(
                commit_frame,
                text="Commit:",
                font=VSCodeTheme.get_font('small'),
                bg=VSCodeTheme.BG_PRIMARY,
                fg=VSCodeTheme.FG_SECONDARY,
                anchor=tk.W
            )
            commit_label.pack(side=tk.LEFT)
            
            # Make commit hash selectable
            commit_entry = tk.Entry(
                commit_frame,
                font=('Courier New', 8),
                bg=VSCodeTheme.BG_SECONDARY,
                fg=VSCodeTheme.FG_PRIMARY,
                relief=tk.FLAT,
                borderwidth=0,
                width=45,
                readonlybackground=VSCodeTheme.BG_SECONDARY
            )
            commit_entry.insert(0, build_info['git_commit_full'])
            commit_entry.config(state='readonly')
            commit_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Separator
        separator2 = ttk.Separator(main_frame, orient='horizontal')
        separator2.pack(fill=tk.X, pady=(15, 15))
        
        # Author
        self._add_info_row(
            info_frame,
            "Author:",
            build_info['author']
        )
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg=VSCodeTheme.BG_PRIMARY)
        button_frame.pack(pady=(15, 0))
        
        # Close button
        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            bg=VSCodeTheme.ACCENT_BLUE,
            fg=VSCodeTheme.FG_BRIGHT,
            activebackground=VSCodeTheme.BG_ACTIVE,
            activeforeground=VSCodeTheme.FG_BRIGHT,
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2"
        )
        close_btn.pack()
        
        # Center dialog on parent
        self._center_on_parent(parent)
        
        # Focus the close button
        close_btn.focus_set()
        
        # Bind Escape key to close
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        self.dialog.bind('<Return>', lambda e: self.dialog.destroy())
    
    def _add_info_row(self, parent, label_text, value_text):
        """
        Add an information row to the dialog.
        
        Args:
            parent: Parent frame
            label_text: Label text
            value_text: Value text
        """
        row_frame = tk.Frame(parent, bg=VSCodeTheme.BG_PRIMARY)
        row_frame.pack(fill=tk.X, pady=2)
        
        label = tk.Label(
            row_frame,
            text=label_text,
            font=VSCodeTheme.get_font('normal'),
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_SECONDARY,
            width=12,
            anchor=tk.W
        )
        label.pack(side=tk.LEFT)
        
        value = tk.Label(
            row_frame,
            text=value_text,
            font=VSCodeTheme.get_font('normal'),
            bg=VSCodeTheme.BG_PRIMARY,
            fg=VSCodeTheme.FG_PRIMARY,
            anchor=tk.W
        )
        value.pack(side=tk.LEFT, padx=(10, 0))
    
    def _center_on_parent(self, parent):
        """
        Center the dialog on the parent window.
        
        Args:
            parent: Parent window
        """
        self.dialog.update_idletasks()
        
        # Get parent window position and size
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Set position
        self.dialog.geometry(f"+{x}+{y}")


def show_about_dialog(parent):
    """
    Show the About dialog.
    
    Args:
        parent: Parent window
    """
    AboutDialog(parent)
