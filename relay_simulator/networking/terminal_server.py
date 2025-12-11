"""
Terminal Server for Relay Logic Simulator

Implements a TCP-based terminal server that allows remote control and monitoring
of the simulation engine via telnet or similar terminal clients.

Features:
- TCP socket server on configurable port (default: 5000)
- Multiple concurrent client connections
- Line-buffered input with echo support
- Control character handling (Ctrl+C, Ctrl+D)
- Graceful shutdown
- Thread-safe client management

Author: Cascade AI
Date: 2025-12-10
"""

import socket
import threading
import time
from typing import Optional, List, Callable, Dict
from dataclasses import dataclass
from enum import Enum


class ServerState(Enum):
    """Terminal server state enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ClientState(Enum):
    """Client connection state enumeration."""
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ClientConnection:
    """
    Represents a connected terminal client.
    
    Attributes:
        client_id: Unique identifier for this connection
        socket: Client socket object
        address: Client address tuple (host, port)
        state: Current connection state
        input_buffer: Buffer for incoming data
        thread: Thread handling this client
    """
    client_id: str
    socket: socket.socket
    address: tuple
    state: ClientState = ClientState.CONNECTED
    input_buffer: str = ""
    thread: Optional[threading.Thread] = None
    
    def send(self, text: str) -> bool:
        """
        Send text to client.
        
        Args:
            text: Text to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.socket.sendall(text.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error sending to client {self.client_id}: {e}")
            self.state = ClientState.ERROR
            return False
    
    def send_line(self, text: str) -> bool:
        """
        Send line with newline to client.
        
        Args:
            text: Text to send (newline will be added)
            
        Returns:
            True if successful, False otherwise
        """
        return self.send(text + "\r\n")
    
    def close(self):
        """Close the client connection."""
        try:
            self.socket.close()
        except:
            pass
        self.state = ClientState.DISCONNECTED


class TerminalServer:
    """
    TCP-based terminal server for relay simulator.
    
    Provides a telnet-compatible interface for controlling and monitoring
    the simulation engine. Supports multiple concurrent clients.
    
    Features:
    - Configurable port (default: 5000)
    - Multiple client connections
    - Line-buffered input
    - Echo support
    - Command callback system
    - Thread-safe operation
    
    Attributes:
        host: Server hostname/IP (default: '0.0.0.0')
        port: Server port (default: 5000)
        state: Current server state
        clients: List of connected clients
        server_socket: Main server socket
        accept_thread: Thread accepting new connections
        command_callback: Callback for processing commands
    """
    
    def __init__(
        self,
        host: str = '0.0.0.0',
        port: int = 5000,
        max_clients: int = 10,
        echo: bool = True
    ):
        """
        Initialize terminal server.
        
        Args:
            host: Host address to bind to (default: 0.0.0.0 - all interfaces)
            port: Port to listen on (default: 5000)
            max_clients: Maximum concurrent clients (default: 10)
            echo: Enable character echo (default: True)
        """
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.echo = echo
        
        # Server state
        self.state = ServerState.STOPPED
        self._state_lock = threading.RLock()
        
        # Client management
        self.clients: List[ClientConnection] = []
        self._clients_lock = threading.RLock()
        self._next_client_id = 1
        
        # Sockets and threads
        self.server_socket: Optional[socket.socket] = None
        self.accept_thread: Optional[threading.Thread] = None
        
        # Command callback
        self.command_callback: Optional[Callable[[str, ClientConnection], str]] = None
        
        # Statistics
        self.total_connections = 0
        self.total_commands = 0
        self.start_time: Optional[float] = None
    
    def set_command_callback(self, callback: Callable[[str, ClientConnection], str]):
        """
        Set callback function for processing commands.
        
        The callback will be called with (command_line, client) and should
        return a response string.
        
        Args:
            callback: Function to handle commands
        """
        self.command_callback = callback
    
    def start(self) -> bool:
        """
        Start the terminal server.
        
        Creates server socket, binds to port, and starts accepting connections.
        
        Returns:
            True if started successfully, False otherwise
        """
        with self._state_lock:
            if self.state == ServerState.RUNNING:
                print(f"Server already running on {self.host}:{self.port}")
                return True
            
            self.state = ServerState.STARTING
        
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to address
            self.server_socket.bind((self.host, self.port))
            
            # Listen for connections
            self.server_socket.listen(self.max_clients)
            
            # Start accept thread
            self.accept_thread = threading.Thread(
                target=self._accept_connections,
                name="TerminalServer-Accept",
                daemon=True
            )
            self.accept_thread.start()
            
            # Update state
            with self._state_lock:
                self.state = ServerState.RUNNING
                self.start_time = time.time()
            
            print(f"✓ Terminal server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"Failed to start server: {e}")
            with self._state_lock:
                self.state = ServerState.ERROR
            return False
    
    def stop(self) -> bool:
        """
        Stop the terminal server.
        
        Disconnects all clients and closes server socket.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        with self._state_lock:
            if self.state == ServerState.STOPPED:
                return True
            
            self.state = ServerState.STOPPING
        
        try:
            # Disconnect all clients
            with self._clients_lock:
                for client in self.clients[:]:  # Copy list to avoid modification during iteration
                    self._disconnect_client(client, "Server shutting down")
            
            # Close server socket
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            
            # Wait for accept thread
            if self.accept_thread and self.accept_thread.is_alive():
                self.accept_thread.join(timeout=2.0)
            
            with self._state_lock:
                self.state = ServerState.STOPPED
            
            print("✓ Terminal server stopped")
            return True
            
        except Exception as e:
            print(f"Error stopping server: {e}")
            with self._state_lock:
                self.state = ServerState.ERROR
            return False
    
    def _accept_connections(self):
        """Thread function to accept new client connections."""
        print(f"Accepting connections on {self.host}:{self.port}")
        
        while self.state == ServerState.RUNNING:
            try:
                # Set timeout to allow periodic state checking
                self.server_socket.settimeout(1.0)
                
                try:
                    client_socket, client_address = self.server_socket.accept()
                except socket.timeout:
                    continue
                
                # Check if we can accept more clients
                with self._clients_lock:
                    if len(self.clients) >= self.max_clients:
                        # Reject connection
                        try:
                            client_socket.sendall(b"Server full. Try again later.\r\n")
                            client_socket.close()
                        except:
                            pass
                        continue
                
                # Create client connection
                client = ClientConnection(
                    client_id=f"CLIENT_{self._next_client_id:03d}",
                    socket=client_socket,
                    address=client_address,
                    state=ClientState.CONNECTED
                )
                self._next_client_id += 1
                self.total_connections += 1
                
                # Add to clients list
                with self._clients_lock:
                    self.clients.append(client)
                
                # Start client handler thread
                client.thread = threading.Thread(
                    target=self._handle_client,
                    args=(client,),
                    name=f"Client-{client.client_id}",
                    daemon=True
                )
                client.thread.start()
                
                print(f"✓ Client connected: {client.client_id} from {client_address}")
                
            except Exception as e:
                if self.state == ServerState.RUNNING:
                    print(f"Error accepting connection: {e}")
    
    def _handle_client(self, client: ClientConnection):
        """
        Thread function to handle client communication.
        
        Args:
            client: ClientConnection object
        """
        try:
            # Send welcome message
            client.send_line("="*60)
            client.send_line("Relay Logic Simulator - Terminal Interface")
            client.send_line("="*60)
            client.send_line("")
            client.send_line(f"Connected as: {client.client_id}")
            client.send_line(f"Type 'help' for available commands")
            client.send_line("")
            client.send("relay> ")
            
            # Set socket timeout for receive
            client.socket.settimeout(0.1)
            
            # Main client loop
            while client.state == ClientState.CONNECTED and self.state == ServerState.RUNNING:
                try:
                    # Receive data
                    data = client.socket.recv(1024)
                    
                    if not data:
                        # Connection closed
                        break
                    
                    # Decode data
                    text = data.decode('utf-8', errors='replace')
                    
                    # Process each character
                    for char in text:
                        if self._process_character(client, char):
                            # Complete command received
                            self._process_command(client)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error handling client {client.client_id}: {e}")
                    break
            
        finally:
            self._disconnect_client(client, "Connection closed")
    
    def _process_character(self, client: ClientConnection, char: str) -> bool:
        """
        Process a single character from client input.
        
        Args:
            client: ClientConnection object
            char: Character to process
            
        Returns:
            True if complete line received, False otherwise
        """
        # Handle special characters
        if char == '\r' or char == '\n':
            # End of line
            if client.input_buffer.strip():  # Only process non-empty lines
                if self.echo:
                    client.send("\r\n")
                return True
            else:
                if self.echo:
                    client.send("\r\n")
                client.send("relay> ")
            return False
        
        elif char == '\x03':  # Ctrl+C
            client.send("^C\r\n")
            client.input_buffer = ""
            client.send("relay> ")
            return False
        
        elif char == '\x04':  # Ctrl+D (EOF)
            client.send("\r\nGoodbye!\r\n")
            client.state = ClientState.DISCONNECTED
            return False
        
        elif char == '\x7f' or char == '\x08':  # Backspace/Delete
            if client.input_buffer:
                client.input_buffer = client.input_buffer[:-1]
                if self.echo:
                    client.send("\x08 \x08")  # Backspace, space, backspace
            return False
        
        elif char == '\t':  # Tab - ignore for now (future: tab completion)
            return False
        
        else:
            # Regular character
            client.input_buffer += char
            if self.echo:
                client.send(char)
            return False
    
    def _process_command(self, client: ClientConnection):
        """
        Process a complete command line.
        
        Args:
            client: ClientConnection object
        """
        command_line = client.input_buffer.strip()
        client.input_buffer = ""
        
        self.total_commands += 1
        
        # Handle built-in commands
        if command_line.lower() in ('quit', 'exit', 'bye'):
            client.send_line("Goodbye!")
            client.state = ClientState.DISCONNECTED
            return
        
        # Call command callback if set
        if self.command_callback:
            try:
                response = self.command_callback(command_line, client)
                if response:
                    client.send_line(response)
            except Exception as e:
                client.send_line(f"Error: {e}")
        else:
            # No callback - echo command
            client.send_line(f"Command received: {command_line}")
            client.send_line("(No command processor configured)")
        
        # Send prompt
        client.send("relay> ")
    
    def _disconnect_client(self, client: ClientConnection, reason: str = ""):
        """
        Disconnect a client.
        
        Args:
            client: ClientConnection object
            reason: Reason for disconnection
        """
        try:
            if reason:
                client.send_line(f"\r\n{reason}")
            
            client.close()
            
            with self._clients_lock:
                if client in self.clients:
                    self.clients.remove(client)
            
            print(f"✓ Client disconnected: {client.client_id} ({reason})")
            
        except Exception as e:
            print(f"Error disconnecting client {client.client_id}: {e}")
    
    def broadcast(self, message: str):
        """
        Send message to all connected clients.
        
        Args:
            message: Message to broadcast
        """
        with self._clients_lock:
            for client in self.clients[:]:
                if client.state == ClientState.CONNECTED:
                    client.send_line(message)
    
    def get_status(self) -> Dict:
        """
        Get server status information.
        
        Returns:
            Dictionary with server status
        """
        with self._state_lock, self._clients_lock:
            uptime = time.time() - self.start_time if self.start_time else 0
            
            return {
                'state': self.state.value,
                'host': self.host,
                'port': self.port,
                'uptime': uptime,
                'connected_clients': len(self.clients),
                'max_clients': self.max_clients,
                'total_connections': self.total_connections,
                'total_commands': self.total_commands,
                'clients': [
                    {
                        'id': c.client_id,
                        'address': f"{c.address[0]}:{c.address[1]}",
                        'state': c.state.value
                    }
                    for c in self.clients
                ]
            }
    
    def print_status(self):
        """Print formatted server status."""
        status = self.get_status()
        
        print("\n" + "="*60)
        print("TERMINAL SERVER STATUS")
        print("="*60)
        print(f"State:              {status['state']}")
        print(f"Address:            {status['host']}:{status['port']}")
        print(f"Uptime:             {status['uptime']:.1f} seconds")
        print(f"Connected clients:  {status['connected_clients']}/{status['max_clients']}")
        print(f"Total connections:  {status['total_connections']}")
        print(f"Total commands:     {status['total_commands']}")
        
        if status['clients']:
            print("\nConnected Clients:")
            for client in status['clients']:
                print(f"  {client['id']:<15} {client['address']:<20} {client['state']}")
        
        print("="*60 + "\n")


# Convenience function
def create_terminal_server(
    port: int = 5000,
    command_callback: Optional[Callable] = None
) -> TerminalServer:
    """
    Create and start a terminal server.
    
    Args:
        port: Port to listen on (default: 5000)
        command_callback: Optional command handler function
        
    Returns:
        TerminalServer instance
        
    Example:
        def handle_command(cmd: str, client: ClientConnection) -> str:
            return f"You said: {cmd}"
        
        server = create_terminal_server(port=5000, command_callback=handle_command)
    """
    server = TerminalServer(port=port)
    if command_callback:
        server.set_command_callback(command_callback)
    return server
