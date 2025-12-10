"""
Main window for the tkinter designer.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class MainWindow(tk.Tk):
    """
    Main application window for the relay simulator designer.
    """
    
    def __init__(self, engine):
        """
        Initialize main window.
        
        Args:
            engine: SimulationEngine instance
        """
        super().__init__()
        
        self.engine = engine
        
        # Window setup
        self.title("Relay Simulator Designer")
        self.geometry("1200x800")
        
        # Register stable callback
        self.engine.register_stable_callback(self.on_simulation_stable)
        
        # Create UI
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()
        
        # Center window
        self._center_window()
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._on_new)
        file_menu.add_command(label="Open...", command=self._on_open)
        file_menu.add_command(label="Save", command=self._on_save)
        file_menu.add_command(label="Save As...", command=self._on_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Simulation menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        sim_menu.add_command(label="Start", command=self._on_start_sim)
        sim_menu.add_command(label="Stop", command=self._on_stop_sim)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._on_about)
    
    def _create_toolbar(self):
        """Create toolbar"""
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Simulation controls
        ttk.Button(toolbar, text="Start", command=self._on_start_sim).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Stop", command=self._on_stop_sim).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Status label
        self.sim_status_label = ttk.Label(toolbar, text="Simulation: Stopped")
        self.sim_status_label.pack(side=tk.LEFT, padx=10)
    
    def _create_main_area(self):
        """Create main content area"""
        main_frame = ttk.Frame(self)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas placeholder
        self.canvas = tk.Canvas(main_frame, bg='white', width=3000, height=3000)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # TODO: Add scrollbars
        # TODO: Implement canvas_view with adapter
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    # === Menu Handlers ===
    
    def _on_new(self):
        """Handle File > New"""
        messagebox.showinfo("Not Implemented", "New file functionality not yet implemented")
    
    def _on_open(self):
        """Handle File > Open"""
        messagebox.showinfo("Not Implemented", "Open file functionality not yet implemented")
    
    def _on_save(self):
        """Handle File > Save"""
        messagebox.showinfo("Not Implemented", "Save functionality not yet implemented")
    
    def _on_save_as(self):
        """Handle File > Save As"""
        messagebox.showinfo("Not Implemented", "Save As functionality not yet implemented")
    
    def _on_start_sim(self):
        """Handle start simulation"""
        result = self.engine.start_simulation()
        if result['success']:
            self.sim_status_label.config(text="Simulation: Running")
            self.status_bar.config(text="Simulation started")
        else:
            messagebox.showerror("Error", f"Failed to start simulation: {result['message']}")
    
    def _on_stop_sim(self):
        """Handle stop simulation"""
        result = self.engine.stop_simulation()
        if result['success']:
            self.sim_status_label.config(text="Simulation: Stopped")
            self.status_bar.config(text="Simulation stopped")
        else:
            messagebox.showerror("Error", f"Failed to stop simulation: {result['message']}")
    
    def _on_about(self):
        """Handle Help > About"""
        messagebox.showinfo(
            "About",
            "Relay Logic Simulator\nVersion 0.1.0\n\nMulti-threaded relay logic simulation engine"
        )
    
    # === Simulation Callback ===
    
    def on_simulation_stable(self, state_data):
        """
        Called by engine when simulation reaches stable state.
        Runs in simulation thread, need to marshal to GUI thread.
        
        Args:
            state_data: State data dict from engine
        """
        self.after(0, self._update_display, state_data)
    
    def _update_display(self, state_data):
        """
        Update display (runs in GUI thread).
        
        Args:
            state_data: State data dict
        """
        # TODO: Implement component rendering
        # TODO: Update statistics display
        
        stats = state_data.get('statistics', {})
        iterations = stats.get('iterations', 0)
        self.status_bar.config(text=f"Stable - {iterations} iterations")
