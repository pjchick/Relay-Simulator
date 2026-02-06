# Relay Simulator

A Python-based relay logic circuit simulator with a modern tkinter GUI designer and multi-threaded simulation engine. Design complex relay logic circuits, simulate their behavior in real-time, and interact with components through an intuitive visual interface.

![License](https://img.shields.io/badge/license-GNUv3-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

## Features

### 🎨 Visual Circuit Designer
- Intuitive drag-and-drop component placement
- Multi-page document support for complex designs
- Real-time visual feedback during simulation
- Grid-based canvas with snap-to-grid functionality
- Component properties panel for customization
- Undo/redo support for design operations
- Export/print circuit diagrams as PNG

### ⚡ High-Performance Simulation Engine
- Single-threaded mode (2x faster for circuits <2000 components)
- Multi-threaded mode for large-scale circuits (≥2000 components)
- Automatic mode selection based on circuit complexity
- Dirty-flag optimization for efficient simulation
- VNET-based electrical network resolution
- Support for 100's components per circuit
- Relay timing simulation with realistic delays

### 🔌 Component Library
- **Switches**: Toggle and pushbutton modes with configurable colors
- **Indicators**: LED indicators with multiple colors
- **Relays**: DPDT (Double-Pole Double-Throw) relays with realistic timing
- **Power Sources**: VCC (always HIGH) power components
- **Logic Elements**: Diodes, Bus components, Seven-segment displays
- **Memory**: RAM/ROM components with scrollable viewing
- **Utilities**: Text labels, Box containers, Clock generators
- **Cross-Page Links**: Connect circuits across multiple pages


### Prerequisites

- Python 3.10 or higher
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pjchick/Relay-Simulator.git
   cd "Relay Simulator"
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   
   **Windows (PowerShell):**
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   .venv\Scripts\activate.bat
   ```

4. **Install dependencies:**
   ```bash
   pip install -r relay_simulator/requirements.txt
   ```

### Running the Application

**GUI Designer Mode:**
```bash
python relay_simulator/app.py
```

## Usage

### Creating a Simple Circuit

1. Launch the application
2. Drag a Switch from the toolbox onto the canvas
3. Drag an Indicator (LED) onto the canvas
4. Click on a tab (connection point) on the switch, then click on a tab on the indicator to create a wire
5. Press **F5** to start the simulation
6. Click on the switch to toggle it and see the indicator light up!
7. Press **Shift+F5** to stop the simulation


### File Format

Circuits are saved in `.rsim` format (JSON-based):
- Supports multi-page documents
- Cross-page linking capabilities

Example files can be found in the `examples/` directory.

## Building Standalone Executable

To create a standalone Windows executable:

```bash
python build_exe.py
```

The executable will be created in `dist/RelaySimulator.exe`

See `BUILD_INSTRUCTIONS.md` for more details.

## Project Structure

```
relay_simulator/
├── app.py                      # Main application entry point
├── engine_server.py            # Standalone engine server
├── components/                 # Component implementations
│   ├── base.py                 # Component base class
│   ├── switch.py               # Switch component
│   ├── indicator.py            # Indicator component
│   ├── dpdt_relay.py           # DPDT Relay component
│   └── ...                     # Other components
├── core/                       # Core simulation classes
│   ├── document.py             # Document management
│   ├── vnet.py                 # Virtual network (VNET) system
│   ├── vnet_builder.py         # VNET construction algorithm
│   └── ...                     # Other core modules
├── gui/                        # GUI components
│   ├── main_window.py          # Main window
│   ├── canvas.py               # Design canvas
│   ├── toolbox.py              # Component toolbox
│   └── ...                     # Other GUI modules
├── simulation/                 # Simulation engines
│   ├── simulation_engine.py    # Single-threaded engine
│   ├── threaded_simulation_engine.py  # Multi-threaded engine
│   └── engine_factory.py       # Engine creation factory
├── networking/                 # Network/terminal interface
│   ├── socket_server.py        # Socket server
│   ├── command_parser.py       # Command parsing
│   └── simulator_commands.py   # Command implementations
└── fileio/                     # File I/O operations
    ├── document_loader.py      # Document loading/saving
    └── rsim_schema.py          # File format schema
```

## Documentation

- **[Architecture](docs/Architecture.md)**: Detailed system architecture
- **[Simulation Engine Usage](docs/SIMULATION_ENGINE_USAGE.md)**: Engine configuration guide
- **[RSIM File Format](docs/RSIM_FILE_FORMAT.md)**: File format specification
- **[Threading Analysis](docs/THREADING_BOTTLENECK_ANALYSIS.md)**: Performance analysis
- **[Project Status](docs/PROJECT_STATUS.md)**: Current development status

## Performance

Based on comprehensive profiling:

| Components | Single-threaded | Multi-threaded (4 threads) | Recommended Mode |
|------------|----------------|----------------------------|------------------|
| < 2000     | **2x faster**  | Slower due to overhead     | Single-threaded  |
| ≥ 2000     | Baseline       | Faster                     | Multi-threaded   |

The engine automatically selects the optimal mode based on circuit size (AUTO mode).


## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests (if applicable)
5. Submit a pull request

## License

This project is licensed under the GNUv3 License- see the LICENSE file for details.

## Contact

- **Repository**: [https://github.com/pjchick/Relay-Simulator](https://github.com/pjchick/Relay-Simulator)
- **Issues**: [https://github.com/pjchick/Relay-Simulator/issues](https://github.com/pjchick/Relay-Simulator/issues)

- **website**: https://chickfamily.net
- **mail**: peter@chickfamily.net
---

**Version**: 0.1.0  
**Last Updated**: January 2026
