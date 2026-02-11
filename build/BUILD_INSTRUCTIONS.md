# Building Relay Simulator as Windows Executable

This guide explains how to create a standalone Windows executable (.exe) for Relay Simulator.

## Prerequisites

1. **Python 3.8 or higher** installed
2. **Virtual environment** activated (recommended)
3. **PyInstaller** installed

## Step 1: Install PyInstaller

If you haven't already installed PyInstaller, run:

```powershell
pip install pyinstaller
```

## Step 2: Build the Executable

Run the build script:

```powershell
python build_exe.py
```

This will:
- Create a standalone executable in the `dist/` folder
- Include all necessary Python files and dependencies
- Create a single-file executable (no external DLLs needed)
- Set up the executable to run without showing a console window

## Step 3: Find Your Executable

After the build completes, you'll find:
- **Executable**: `dist\RelaySimulator.exe`

You can copy this .exe file anywhere and run it without Python installed.

## Build Options

### Option 1: Single File (Default)
The default `build_exe.py` creates a single .exe file. This is convenient for distribution but slightly slower to start.

### Option 2: Directory Build
For faster startup, you can modify `build_exe.py` and change:
```python
'--onefile',  # Remove this line
'--onedir',   # Add this line
```

This creates a folder with the .exe and supporting files.

## Troubleshooting

### Build fails with "Module not found"
- Make sure all dependencies are installed: `pip install -r relay_simulator/requirements.txt`
- Check that PyInstaller is installed: `pip install pyinstaller`

### Executable won't start
- Try running from command line to see error messages:
  ```powershell
  cd dist
  .\RelaySimulator.exe
  ```
- Check Windows Defender or antivirus - they sometimes flag PyInstaller executables

### Large executable size
- The .exe includes Python and all libraries (~50-100 MB is normal)
- For smaller size, use `--onedir` instead of `--onefile`

## Distribution

The executable in `dist/` is completely standalone and can be:
- Copied to other Windows computers (no Python installation needed)
- Distributed to users
- Run from any location

## Advanced: Custom Icon

To add a custom icon to the executable:

1. Create or obtain a `.ico` file
2. Add to `build_exe.py`:
   ```python
   '--icon=path/to/icon.ico',
   ```

## Advanced: Version Information

To add version information visible in Windows file properties, create a `version_info.txt` file and add to `build_exe.py`:
```python
'--version-file=version_info.txt',
```
