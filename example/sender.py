import sys
import socket

class SenderMixin:

    last_sequence_sent = 0
    msgbuf = bytearray(21)
    
    def connect(self, host, remote_port):
        self.port = remote_port
        self.host = host
        self.client_socket = socket.socket()
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        self.client_socket.connect(("localhost", self.port))
        

    def send(self, msg):
        self.client_socket.sendall(msg.encode())

        try: 
            bytes = self.client_socket.recv(1024)
            resp = bytes.decode('utf-8')
            self.last_sequence_sent = int(resp)
            print(f"submitted #{self.last_sequence_sent}")
        except ValueError as ve:
            print(f"couldn't get sequence # response for {msg}: {ve}")
