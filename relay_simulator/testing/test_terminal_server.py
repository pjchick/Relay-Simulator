"""
Tests for Terminal Server

Tests the TCP-based terminal server for relay simulator including:
- Server start/stop
- Client connections
- Message send/receive
- Command processing
- Multiple clients
- Error handling

Author: Cascade AI
Date: 2025-12-10
"""

import unittest
import socket
import time
import threading
from typing import Optional

from networking.terminal_server import (
    TerminalServer,
    ClientConnection,
    ServerState,
    ClientState,
    create_terminal_server
)


class TestTerminalServer(unittest.TestCase):
    """Test TerminalServer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use a high port to avoid conflicts
        self.test_port = 15000
        self.server: Optional[TerminalServer] = None
    
    def tearDown(self):
        """Clean up after tests."""
        if self.server and self.server.state == ServerState.RUNNING:
            self.server.stop()
            time.sleep(0.1)
    
    def test_server_creation(self):
        """Test server creation with default parameters."""
        server = TerminalServer(port=self.test_port)
        
        self.assertEqual(server.host, '0.0.0.0')
        self.assertEqual(server.port, self.test_port)
        self.assertEqual(server.max_clients, 10)
        self.assertEqual(server.echo, True)
        self.assertEqual(server.state, ServerState.STOPPED)
    
    def test_server_start_stop(self):
        """Test starting and stopping server."""
        self.server = TerminalServer(port=self.test_port)
        
        # Start server
        result = self.server.start()
        self.assertTrue(result)
        self.assertEqual(self.server.state, ServerState.RUNNING)
        
        # Wait a moment for thread to start
        time.sleep(0.1)
        
        # Stop server
        result = self.server.stop()
        self.assertTrue(result)
        self.assertEqual(self.server.state, ServerState.STOPPED)
    
    def test_server_double_start(self):
        """Test starting server twice."""
        self.server = TerminalServer(port=self.test_port)
        
        # Start once
        result1 = self.server.start()
        self.assertTrue(result1)
        
        # Start again (should succeed but not create new socket)
        result2 = self.server.start()
        self.assertTrue(result2)
        self.assertEqual(self.server.state, ServerState.RUNNING)
    
    def test_client_connection(self):
        """Test single client connection."""
        self.server = TerminalServer(port=self.test_port)
        self.server.start()
        time.sleep(0.1)
        
        # Connect client
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', self.test_port))
        time.sleep(0.2)
        
        # Check server has client
        self.assertEqual(len(self.server.clients), 1)
        self.assertEqual(self.server.total_connections, 1)
        
        # Receive welcome message
        data = client_socket.recv(4096)
        self.assertIn(b"Relay Logic Simulator", data)
        self.assertIn(b"relay>", data)
        
        # Close client
        client_socket.close()
        time.sleep(0.2)
        
        # Check client disconnected
        self.assertEqual(len(self.server.clients), 0)
    
    def test_send_receive_command(self):
        """Test sending and receiving commands."""
        self.server = TerminalServer(port=self.test_port)
        
        # Set up command callback
        received_commands = []
        def command_handler(cmd: str, client: ClientConnection) -> str:
            received_commands.append(cmd)
            return f"Echo: {cmd}"
        
        self.server.set_command_callback(command_handler)
        self.server.start()
        time.sleep(0.1)
        
        # Connect client
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', self.test_port))
        time.sleep(0.1)
        
        # Clear welcome message
        client_socket.recv(4096)
        
        # Send command
        client_socket.sendall(b"test command\r\n")
        time.sleep(0.1)
        
        # Receive response
        data = client_socket.recv(4096)
        
        # Check command was received
        self.assertEqual(len(received_commands), 1)
        self.assertEqual(received_commands[0], "test command")
        
        # Check response
        self.assertIn(b"Echo: test command", data)
        
        client_socket.close()
    
    def test_multiple_clients(self):
        """Test multiple concurrent clients."""
        self.server = TerminalServer(port=self.test_port, max_clients=3)
        self.server.start()
        time.sleep(0.1)
        
        # Connect 3 clients
        clients = []
        for i in range(3):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', self.test_port))
            clients.append(client)
            time.sleep(0.1)
        
        # Check all connected
        self.assertEqual(len(self.server.clients), 3)
        self.assertEqual(self.server.total_connections, 3)
        
        # Close all clients
        for client in clients:
            client.close()
        
        time.sleep(0.2)
        self.assertEqual(len(self.server.clients), 0)
    
    def test_max_clients_limit(self):
        """Test maximum client limit."""
        self.server = TerminalServer(port=self.test_port, max_clients=2)
        self.server.start()
        time.sleep(0.1)
        
        # Connect 2 clients (should succeed)
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect(('localhost', self.test_port))
        time.sleep(0.1)
        
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect(('localhost', self.test_port))
        time.sleep(0.1)
        
        self.assertEqual(len(self.server.clients), 2)
        
        # Connect 3rd client (should be rejected)
        client3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client3.connect(('localhost', self.test_port))
        time.sleep(0.1)
        
        # Should receive rejection message
        data = client3.recv(1024)
        self.assertIn(b"Server full", data)
        
        # Server should still have only 2 clients
        self.assertEqual(len(self.server.clients), 2)
        
        client1.close()
        client2.close()
        client3.close()
    
    def test_backspace_handling(self):
        """Test backspace character handling."""
        self.server = TerminalServer(port=self.test_port)
        
        received_commands = []
        def command_handler(cmd: str, client: ClientConnection) -> str:
            received_commands.append(cmd)
            return "OK"
        
        self.server.set_command_callback(command_handler)
        self.server.start()
        time.sleep(0.1)
        
        # Connect client
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', self.test_port))
        time.sleep(0.1)
        client_socket.recv(4096)  # Clear welcome
        
        # Send: "test" + backspace + backspace + "st\n"
        # Should result in "test"
        client_socket.sendall(b"test\x08\x08st\r\n")
        time.sleep(0.1)
        
        # Check command
        self.assertEqual(len(received_commands), 1)
        self.assertEqual(received_commands[0], "test")
        
        client_socket.close()
    
    def test_ctrl_c_handling(self):
        """Test Ctrl+C handling."""
        self.server = TerminalServer(port=self.test_port)
        self.server.start()
        time.sleep(0.1)
        
        # Connect client
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', self.test_port))
        time.sleep(0.1)
        client_socket.recv(4096)  # Clear welcome
        
        # Send Ctrl+C
        client_socket.sendall(b"test\x03")
        time.sleep(0.1)
        
        # Client should still be connected
        self.assertEqual(len(self.server.clients), 1)
        
        client_socket.close()
    
    def test_quit_command(self):
        """Test built-in quit command."""
        self.server = TerminalServer(port=self.test_port)
        self.server.start()
        time.sleep(0.1)
        
        # Connect client
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', self.test_port))
        time.sleep(0.1)
        client_socket.recv(4096)  # Clear welcome
        
        # Send quit command
        client_socket.sendall(b"quit\r\n")
        time.sleep(0.1)
        
        # Client should be disconnected
        self.assertEqual(len(self.server.clients), 0)
        
        client_socket.close()
    
    def test_broadcast(self):
        """Test broadcasting to all clients."""
        self.server = TerminalServer(port=self.test_port)
        self.server.start()
        time.sleep(0.1)
        
        # Connect 2 clients
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect(('localhost', self.test_port))
        time.sleep(0.1)
        
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect(('localhost', self.test_port))
        time.sleep(0.1)
        
        # Clear welcome messages
        client1.recv(4096)
        client2.recv(4096)
        
        # Broadcast message
        self.server.broadcast("Test broadcast message")
        time.sleep(0.1)
        
        # Both clients should receive
        data1 = client1.recv(1024)
        data2 = client2.recv(1024)
        
        self.assertIn(b"Test broadcast message", data1)
        self.assertIn(b"Test broadcast message", data2)
        
        client1.close()
        client2.close()
    
    def test_get_status(self):
        """Test get_status method."""
        self.server = TerminalServer(port=self.test_port)
        self.server.start()
        time.sleep(0.1)
        
        # Connect client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', self.test_port))
        time.sleep(0.1)
        
        # Get status
        status = self.server.get_status()
        
        self.assertEqual(status['state'], 'running')
        self.assertEqual(status['port'], self.test_port)
        self.assertEqual(status['connected_clients'], 1)
        self.assertEqual(status['total_connections'], 1)
        self.assertGreater(status['uptime'], 0)
        
        client.close()
    
    def test_echo_on_off(self):
        """Test echo enable/disable."""
        # Echo ON (default)
        server1 = TerminalServer(port=self.test_port, echo=True)
        server1.start()
        time.sleep(0.1)
        
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect(('localhost', self.test_port))
        time.sleep(0.1)
        client1.recv(4096)  # Clear welcome
        
        # Send character
        client1.sendall(b"a")
        time.sleep(0.1)
        
        # Should echo back
        data = client1.recv(1024)
        self.assertIn(b"a", data)
        
        client1.close()
        server1.stop()
        time.sleep(0.2)
        
        # Echo OFF
        server2 = TerminalServer(port=self.test_port, echo=False)
        server2.start()
        time.sleep(0.1)
        
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect(('localhost', self.test_port))
        time.sleep(0.1)
        client2.recv(4096)  # Clear welcome
        
        # Send character
        client2.sendall(b"a")
        time.sleep(0.1)
        
        # Should NOT echo (only prompt after command)
        client2.sendall(b"\r\n")
        time.sleep(0.1)
        data = client2.recv(1024)
        # Should have prompt but not the character echo
        self.assertIn(b"relay>", data)
        
        client2.close()
        server2.stop()


class TestConvenienceFunction(unittest.TestCase):
    """Test convenience function."""
    
    def test_create_terminal_server(self):
        """Test create_terminal_server function."""
        def handler(cmd: str, client: ClientConnection) -> str:
            return "OK"
        
        server = create_terminal_server(port=15001, command_callback=handler)
        
        self.assertIsNotNone(server)
        self.assertEqual(server.port, 15001)
        self.assertIsNotNone(server.command_callback)
        
        # Clean up (don't start server in this test)


class TestClientConnection(unittest.TestCase):
    """Test ClientConnection class."""
    
    def test_client_connection_creation(self):
        """Test creating ClientConnection."""
        # Create a dummy socket (not connected)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        client = ClientConnection(
            client_id="TEST_001",
            socket=sock,
            address=("127.0.0.1", 12345)
        )
        
        self.assertEqual(client.client_id, "TEST_001")
        self.assertEqual(client.state, ClientState.CONNECTED)
        self.assertEqual(client.input_buffer, "")
        
        sock.close()


if __name__ == '__main__':
    unittest.main()
