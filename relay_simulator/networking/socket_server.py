"""
Socket server for remote access to simulation engine.
JSON-based protocol over TCP.
"""

import socket
import json
import threading
from typing import Dict, Any


class SocketServer:
    """
    Socket server for remote clients.
    Provides JSON-based API for controlling simulation.
    """
    
    def __init__(self, engine, host='127.0.0.1', port=5000):
        """
        Initialize socket server.
        
        Args:
            engine: SimulationEngine instance
            host: Host address to bind to
            port: Port number to listen on
        """
        self.engine = engine
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.running = False
        self._lock = threading.Lock()
    
    def start(self):
        """Start socket server (blocking)"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        self.running = True
        
        print(f"Socket server listening on {self.host}:{self.port}")
        
        # Accept connections
        while self.running:
            try:
                self.server_socket.settimeout(1.0)  # Timeout for checking running flag
                client_socket, address = self.server_socket.accept()
                print(f"Client connected from {address}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
    
    def stop(self):
        """Stop socket server"""
        self.running = False
        
        # Close all client connections
        with self._lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
    
    def _handle_client(self, client_socket, address):
        """
        Handle individual client connection.
        
        Args:
            client_socket: Client socket
            address: Client address
        """
        with self._lock:
            self.clients.append(client_socket)
        
        try:
            buffer = ""
            
            while self.running:
                # Receive data
                data = client_socket.recv(4096)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                
                # Process complete messages (newline-delimited)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line:
                        try:
                            # Parse command
                            command_data = json.loads(line)
                            
                            # Process command
                            response = self._process_command(command_data)
                            
                            # Send response
                            response_str = json.dumps(response) + '\n'
                            client_socket.send(response_str.encode('utf-8'))
                            
                        except json.JSONDecodeError as e:
                            error_response = {
                                'status': 'error',
                                'message': f'Invalid JSON: {e}'
                            }
                            client_socket.send(json.dumps(error_response).encode('utf-8') + b'\n')
                        
                        except Exception as e:
                            error_response = {
                                'status': 'error',
                                'message': f'Error processing command: {e}'
                            }
                            client_socket.send(json.dumps(error_response).encode('utf-8') + b'\n')
        
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        
        finally:
            with self._lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
            
            try:
                client_socket.close()
            except:
                pass
            
            print(f"Client {address} disconnected")
    
    def _process_command(self, command_data: Dict) -> Dict:
        """
        Process command from client.
        
        Args:
            command_data: Command dict with 'command', 'args', 'request_id'
            
        Returns:
            Response dict
        """
        command = command_data.get('command')
        args = command_data.get('args', {})
        request_id = command_data.get('request_id')
        
        # TODO: Implement command routing
        
        return {
            'status': 'error',
            'message': 'Not yet implemented',
            'request_id': request_id
        }
    
    def _broadcast_event(self, event_name: str, data: Dict):
        """
        Broadcast event to all connected clients.
        
        Args:
            event_name: Event name
            data: Event data
        """
        event_msg = {
            'event': event_name,
            'data': data
        }
        
        event_str = json.dumps(event_msg) + '\n'
        event_bytes = event_str.encode('utf-8')
        
        with self._lock:
            for client in self.clients[:]:  # Copy list to avoid modification during iteration
                try:
                    client.send(event_bytes)
                except Exception as e:
                    print(f"Error broadcasting to client: {e}")
                    # Remove failed client
                    if client in self.clients:
                        self.clients.remove(client)
