"""
Standalone engine server entry point.
Runs simulation engine with socket server for remote access.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from engine.api import SimulationEngine
from networking.socket_server import SocketServer


def main():
    """Launch standalone engine with socket server"""
    print("Starting Relay Simulator Engine Server...")
    
    # Create simulation engine
    engine = SimulationEngine()
    
    # Create socket server
    server = SocketServer(engine, host='127.0.0.1', port=5000)
    
    print(f"Engine server listening on {server.host}:{server.port}")
    print("Press Ctrl+C to stop...")
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nStopping engine server...")
        server.stop()
        print("Engine server stopped.")


if __name__ == '__main__':
    main()
