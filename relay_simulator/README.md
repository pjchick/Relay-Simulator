# Relay Logic Simulator

A multi-threaded relay logic simulator with tkinter designer interface.

## Features

- Multi-threaded simulation engine for high performance
- Dirty-flag optimization for efficient circuit simulation
- Dynamic component loading architecture
- tkinter-based schematic designer
- Socket API for remote control and testing
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
git clone <repository-url>

# Install dependencies (minimal)
pip install -r requirements.txt
```

## Usage

### Designer Mode (GUI)
```bash
python main.py
```

### Standalone Engine (Socket Server)
```bash
python engine_server.py
```

### Test Scripts
```bash
python testing/test_socket_client.py
```

## Project Structure

```
relay_simulator/
├── main.py                  # Designer entry point
├── engine_server.py         # Standalone engine entry point
├── engine/                  # Engine API
├── core/                    # Core simulation classes
├── components/              # Component implementations
├── rendering/               # Canvas adapter
├── networking/              # Socket server
├── designer/                # tkinter GUI
├── testing/                 # Test scripts
└── examples/                # Example circuits
```

## Architecture

See `Architecture.md` for detailed architecture documentation.

## Development

See `ProjectPlan.md` for development roadmap and todo lists.

## License

TBD
