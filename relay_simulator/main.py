"""
Main entry point for the Relay Simulator Designer.
Launches the tkinter GUI with integrated simulation engine.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from designer.main_window import MainWindow
from engine.api import SimulationEngine


def main():
    """Launch the designer application"""
    print("Starting Relay Simulator Designer...")
    
    # Create simulation engine
    engine = SimulationEngine()
    
    # Create and run designer GUI
    app = MainWindow(engine)
    app.mainloop()


if __name__ == '__main__':
    main()
