"""
Settings Management for Relay Simulator III

Provides persistent settings storage and retrieval using JSON files.
Settings are stored in the user's home directory.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional, List


class Settings:
    """
    Application settings with persistent storage.
    
    Settings are stored in a JSON file in the user's home directory:
    ~/.relay_simulator/settings.json (Linux/Mac)
    %USERPROFILE%/.relay_simulator/settings.json (Windows)
    
    Default settings:
    - recent_documents: [] (list of file paths, max 10)
    - simulation_threading: "single" (options: "single", "multi")
    - default_canvas_width: 3000 (pixels)
    - default_canvas_height: 3000 (pixels)
    - canvas_grid_size: 20 (pixels)
    - canvas_snap_size: 10 (pixels)
    """
    
    # Default settings values
    DEFAULTS = {
        'recent_documents': [],
        'simulation_threading': 'single',
        'default_canvas_width': 3000,
        'default_canvas_height': 3000,
        'canvas_grid_size': 20,
        'canvas_snap_size': 10,
    }
    
    def __init__(self):
        """Initialize settings with defaults."""
        # Settings directory and file path
        self.settings_dir = Path.home() / '.relay_simulator'
        self.settings_file = self.settings_dir / 'settings.json'
        
        # Current settings (start with defaults) - deep copy to avoid shared references
        self._settings = {
            'recent_documents': [],
            'simulation_threading': 'single',
            'default_canvas_width': 3000,
            'default_canvas_height': 3000,
            'canvas_grid_size': 20,
            'canvas_snap_size': 10,
        }
        
        # Load settings from file if it exists
        self.load()
        
    def load(self) -> None:
        """
        Load settings from the JSON file.
        
        If the file doesn't exist or is invalid, default settings are used.
        """
        if not self.settings_file.exists():
            return
            
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                
            # Update settings with loaded values (keep defaults for missing keys)
            for key, value in loaded_settings.items():
                if key in self.DEFAULTS:
                    self._settings[key] = value
                    
        except (json.JSONDecodeError, IOError) as e:
            # If file is corrupted or unreadable, use defaults
            print(f"Warning: Could not load settings: {e}")
            self._settings = self.DEFAULTS.copy()
            
    def save(self) -> None:
        """
        Save settings to the JSON file.
        
        Creates the settings directory if it doesn't exist.
        """
        try:
            # Create settings directory if needed
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            
            # Write settings to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
                
        except IOError as e:
            print(f"Warning: Could not save settings: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: The setting key
            default: Default value to return if key doesn't exist
            
        Returns:
            The setting value, or default if key doesn't exist
        """
        return self._settings.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            key: The setting key
            value: The value to set
        """
        self._settings[key] = value
        
    def get_recent_documents(self) -> List[str]:
        """
        Get the list of recent documents.
        
        Returns:
            List of file paths (most recent first)
        """
        return self._settings.get('recent_documents', [])
        
    def add_recent_document(self, filepath: str) -> None:
        """
        Add a document to the recent documents list.
        
        Args:
            filepath: Full path to the document
        """
        recent = self.get_recent_documents()
        
        # Remove if already in list
        if filepath in recent:
            recent.remove(filepath)
            
        # Add to front
        recent.insert(0, filepath)
        
        # Limit to 10 items
        recent = recent[:10]
        
        # Update settings
        self.set('recent_documents', recent)
        
    def remove_recent_document(self, filepath: str) -> None:
        """
        Remove a document from the recent documents list.
        
        Args:
            filepath: Path to remove
        """
        recent = self.get_recent_documents()
        if filepath in recent:
            recent.remove(filepath)
            self.set('recent_documents', recent)
            
    def clear_recent_documents(self) -> None:
        """Clear all recent documents."""
        self.set('recent_documents', [])
        
    def get_simulation_threading(self) -> str:
        """
        Get the simulation threading mode.
        
        Returns:
            "single" or "multi"
        """
        return self._settings.get('simulation_threading', 'single')
        
    def set_simulation_threading(self, mode: str) -> None:
        """
        Set the simulation threading mode.
        
        Args:
            mode: "single" or "multi"
        """
        if mode not in ('single', 'multi'):
            raise ValueError(f"Invalid threading mode: {mode}. Must be 'single' or 'multi'")
        self.set('simulation_threading', mode)
        
    def get_canvas_size(self) -> tuple[int, int]:
        """
        Get the default canvas size.
        
        Returns:
            Tuple of (width, height) in pixels
        """
        width = self._settings.get('default_canvas_width', 3000)
        height = self._settings.get('default_canvas_height', 3000)
        return (width, height)
        
    def set_canvas_size(self, width: int, height: int) -> None:
        """
        Set the default canvas size.
        
        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        self.set('default_canvas_width', width)
        self.set('default_canvas_height', height)
        
    def get_grid_size(self) -> int:
        """
        Get the canvas grid size.
        
        Returns:
            Grid size in pixels
        """
        return self._settings.get('canvas_grid_size', 20)
        
    def set_grid_size(self, size: int) -> None:
        """
        Set the canvas grid size.
        
        Args:
            size: Grid size in pixels (must be positive)
        """
        if size <= 0:
            raise ValueError(f"Grid size must be positive, got {size}")
        self.set('canvas_grid_size', size)
        
    def get_snap_size(self) -> int:
        """
        Get the canvas snap size.
        
        Returns:
            Snap size in pixels
        """
        return self._settings.get('canvas_snap_size', 10)
        
    def set_snap_size(self, size: int) -> None:
        """
        Set the canvas snap size.
        
        Args:
            size: Snap size in pixels (must be positive)
        """
        if size <= 0:
            raise ValueError(f"Snap size must be positive, got {size}")
        self.set('canvas_snap_size', size)
        
    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        self._settings = self.DEFAULTS.copy()
