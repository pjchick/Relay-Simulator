"""
Relay Simulator III - Application Entry Point

This is the main entry point for the Relay Simulator III GUI application.
Run this file to start the application.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """Main entry point for the application."""
    # Create and run the main window
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
