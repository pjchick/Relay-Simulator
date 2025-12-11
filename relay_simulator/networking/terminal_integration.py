"""
Terminal Server Integration

This module integrates the terminal server with the simulator command system,
providing a complete interactive terminal interface for the relay simulator.

Usage:
    server = create_integrated_terminal_server(port=5000)
    server.start()
    # Server now accepts commands from telnet clients
    server.stop()
"""

from typing import Optional
from networking.terminal_server import TerminalServer, ClientConnection
from networking.simulator_commands import create_simulator_context


def command_callback_handler(command_line: str, client: ClientConnection) -> str:
    """
    Command callback for terminal server.
    
    This function is called by the terminal server for each command entered.
    It parses the command and dispatches it to the appropriate handler.
    
    Args:
        command_line: Raw command line from client
        client: Client connection object
        
    Returns:
        Command response string
    """
    # Get context from client metadata (stored in client connection)
    # For now, we'll use a global context (could be per-client in future)
    if not hasattr(command_callback_handler, 'context'):
        command_callback_handler.context = create_simulator_context()
    
    context = command_callback_handler.context
    registry = context['registry']
    
    # Parse and execute command
    try:
        result = registry.parse_and_execute(command_line, context)
        return result if result else "OK"
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


def create_integrated_terminal_server(
    host: str = '0.0.0.0',
    port: int = 5000,
    max_clients: int = 10,
    echo: bool = True
) -> TerminalServer:
    """
    Create a terminal server with integrated simulator commands.
    
    Args:
        host: Host address to bind to
        port: Port to listen on
        max_clients: Maximum concurrent clients
        echo: Enable character echo
        
    Returns:
        Configured TerminalServer instance
    """
    server = TerminalServer(
        host=host,
        port=port,
        max_clients=max_clients,
        echo=echo
    )
    
    server.set_command_callback(command_callback_handler)
    
    return server


# Convenience function
create_simulator_terminal = create_integrated_terminal_server
