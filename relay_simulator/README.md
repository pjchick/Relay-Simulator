# Relay Logic Simulator

A multi-threaded relay logic simulator with tkinter designer interface.

## Features

- Multi-threaded simulation engine for high performance
- Dirty-flag optimization for efficient circuit simulation
- Dynamic component loading architecture
- tkinter-based schematic designer
- Support for 100+ components per circuit

## Components

Initial component set:
- Toggle Switch (with internal power)
- Indicator (LED)
- DPDT Relay (with realistic timing)
- VCC Power source

## Installation

```bash
# Clone repository
git clone https://github.com/pjchick/Relay-Simulator.git

# Install dependencies (minimal)
pip install -r requirements.txt
```

## Usage

### Designer Mode (GUI)
```bash
python app.py
```

## Project Structure

```
relay_simulator/
├── app.py                   # Designer entry point
├── engine/                  # Engine API
├── core/                    # Core simulation classes
├── components/              # Component implementations
├── rendering/               # Canvas adapter
├── gui/                     # tkinter GUI
├── testing/                 # Test scripts
└── examples/                # Example circuits
```

## Architecture

See `docs/Architecture.md` for detailed architecture documentation.

## Development

See project documentation for development information.

## License

GPLv3 License

