# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\repos\\Relay-Simulator\\relay_simulator\\app.py'],
    pathex=['D:\\repos\\Relay-Simulator\\relay_simulator'],
    binaries=[],
    datas=[('D:\\repos\\Relay-Simulator\\relay_simulator\\gui', 'gui'), ('D:\\repos\\Relay-Simulator\\relay_simulator\\components', 'components'), ('D:\\repos\\Relay-Simulator\\relay_simulator\\core', 'core'), ('D:\\repos\\Relay-Simulator\\relay_simulator\\engine', 'engine'), ('D:\\repos\\Relay-Simulator\\relay_simulator\\fileio', 'fileio'), ('D:\\repos\\Relay-Simulator\\relay_simulator\\simulation', 'simulation'), ('D:\\repos\\Relay-Simulator\\relay_simulator\\rendering', 'rendering')],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.font', 'tkinter.messagebox', 'tkinter.filedialog', 'tkinter.simpledialog', 'tkinter.colorchooser', 'PIL', 'PIL.ImageGrab', 'uuid', 'json', 'copy', 'typing', 'collections', 'diagnostics'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'pytest-cov'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RelaySimulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
