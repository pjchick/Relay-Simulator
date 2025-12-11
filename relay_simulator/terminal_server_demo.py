"""
Terminal Server Demo

Demonstrates the terminal server with a simple command handler.
Run this script and connect via telnet to test the server.

Usage:
    python terminal_server_demo.py

Then connect with:
    telnet localhost 5000

Or on Windows PowerShell:
    Test-NetConnection localhost -Port 5000

Author: Cascade AI
Date: 2025-12-10
"""

import sys
import time
from networking.terminal_server import TerminalServer, ClientConnection


def demo_command_handler(command_line: str, client: ClientConnection) -> str:
    """
    Demo command handler that processes simple commands.
    
    Args:
        command_line: Command entered by user
        client: Client connection object
        
    Returns:
        Response string to send to client
    """
    # Split command and arguments
    parts = command_line.strip().split()
    if not parts:
        return ""
    
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    # Process commands
    if cmd == "help":
        return """
Available Commands:
  help              - Show this help message
  echo <text>       - Echo back the text
  time              - Show current time
  status            - Show server status
  hello             - Greet the user
  calc <expr>       - Simple calculator (e.g., calc 2+2)
  whoami            - Show client information
  quit/exit         - Disconnect from server
"""
    
    elif cmd == "echo":
        if args:
            return " ".join(args)
        else:
            return "Usage: echo <text>"
    
    elif cmd == "time":
        return f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    elif cmd == "status":
        # This is a demo - in real implementation, you'd access server stats
        return f"Server running, client {client.client_id} connected"
    
    elif cmd == "hello":
        return f"Hello, {client.client_id}!"
    
    elif cmd == "calc":
        if args:
            try:
                expr = " ".join(args)
                # Simple eval (UNSAFE in production! For demo only)
                result = eval(expr, {"__builtins__": {}}, {})
                return f"{expr} = {result}"
            except Exception as e:
                return f"Error: {e}"
        else:
            return "Usage: calc <expression>\nExample: calc 2+2"
    
    elif cmd == "whoami":
        return f"You are: {client.client_id}\nFrom: {client.address[0]}:{client.address[1]}\nState: {client.state.value}"
    
    else:
        return f"Unknown command: {cmd}\nType 'help' for available commands"


def main():
    """Main demo function."""
    print("="*60)
    print("RELAY SIMULATOR - TERMINAL SERVER DEMO")
    print("="*60)
    print()
    
    # Create server
    server = TerminalServer(
        host='0.0.0.0',
        port=5000,
        max_clients=5,
        echo=True
    )
    
    # Set command handler
    server.set_command_callback(demo_command_handler)
    
    # Start server
    print("Starting terminal server...")
    if not server.start():
        print("Failed to start server!")
        return 1
    
    print()
    print("Server started successfully!")
    print()
    print("Connect with:")
    print("  telnet localhost 5000")
    print()
    print("Or test with:")
    print("  python -c \"import socket; s=socket.socket(); s.connect(('localhost',5000)); print(s.recv(1024)); s.close()\"")
    print()
    print("Press Ctrl+C to stop server")
    print()
    
    try:
        # Keep running and print status periodically
        while True:
            time.sleep(5)
            
            # Print status
            status = server.get_status()
            print(f"[{time.strftime('%H:%M:%S')}] Status: {status['connected_clients']} clients, "
                  f"{status['total_commands']} commands processed")
            
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.stop()
        print("Server stopped. Goodbye!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
