import sys
import socket

class Sender():
    def __init__(self, port):
        self.port = port
        self.host = socket.gethostname()
        self.client_socket = socket.socket()
        self.client_socket.connect(("localhost", self.port))
        self.last_sequence_sent = 0
        
    def send(self, msg):
        self.client_socket.sendall(msg.encode())
        bytes = self.client_socket.recv(21)
        resp = bytes.decode('utf-8')
        
        self.last_sequence_sent = int(resp)
        print(f"submitted #{self.last_sequence_sent}")
