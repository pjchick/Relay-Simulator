"""
Build script to create Windows executable for Relay Simulator.

Usage:
    python build_exe.py

This will create a standalone .exe in the dist/ folder.
"""

import PyInstaller.__main__
import os
import sys

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build arguments for PyInstaller
args = [
    os.path.join(script_dir, 'relay_simulator', 'app.py'),  # Entry point
    '--name=RelaySimulator',  # Executable name
    '--onefile',  # Create a single executable file
    '--windowed',  # No console window (GUI app)
    '--clean',  # Clean PyInstaller cache
    
    # Add relay_simulator to Python path so imports work correctly
    '--paths=' + os.path.join(script_dir, 'relay_simulator'),
    
    # Add all the package directories
    '--add-data=' + os.path.join(script_dir, 'relay_simulator', 'gui') + os.pathsep + 'gui',
    '--add-data=' + os.path.join(script_dir, 'relay_simulator', 'components') + os.pathsep + 'components',
    '--add-data=' + os.path.join(script_dir, 'relay_simulator', 'core') + os.pathsep + 'core',
    '--add-data=' + os.path.join(script_dir, 'relay_simulator', 'engine') + os.pathsep + 'engine',
    '--add-data=' + os.path.join(script_dir, 'relay_simulator', 'fileio') + os.pathsep + 'fileio',
    '--add-data=' + os.path.join(script_dir, 'relay_simulator', 'simulation') + os.pathsep + 'simulation',
    '--add-data=' + os.path.join(script_dir, 'relay_simulator', 'rendering') + os.pathsep + 'rendering',
    
    # Hidden imports for dynamically loaded modules
    '--hidden-import=tkinter',
    '--hidden-import=tkinter.ttk',
    '--hidden-import=tkinter.font',
    '--hidden-import=tkinter.messagebox',
    '--hidden-import=tkinter.filedialog',
    '--hidden-import=tkinter.simpledialog',
    '--hidden-import=tkinter.colorchooser',
    '--hidden-import=PIL',
    '--hidden-import=PIL.ImageGrab',
    '--hidden-import=uuid',
    '--hidden-import=json',
    '--hidden-import=copy',
    '--hidden-import=typing',
    '--hidden-import=collections',
    '--hidden-import=diagnostics',
    
    # Exclude unnecessary packages to reduce size
    '--exclude-module=pytest',
    '--exclude-module=pytest-cov',
    
    # Output directory
    '--distpath=' + os.path.join(script_dir, 'dist'),
    '--workpath=' + os.path.join(script_dir, 'build'),
    '--specpath=' + os.path.join(script_dir, 'build'),
]

print("Building Relay Simulator executable...")
print("This may take a few minutes...")
print()

PyInstaller.__main__.run(args)

print()
print("Build complete!")
print(f"Executable location: {os.path.join(script_dir, 'dist', 'RelaySimulator.exe')}")
