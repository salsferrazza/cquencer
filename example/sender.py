import sys
import socket
from netstring import Connection, NEED_DATA, CONNECTION_CLOSED, decode

class SenderMixin:

    last_sequence_sent = 0
    msgbuf = bytearray(21)
    
    def connect(self, host, remote_port):
        self.conn = Connection()
        self.port = remote_port
        self.host = host
        self.client_socket = socket.socket()
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        self.client_socket.connect(("localhost", self.port))
        

    def send(self, msg):
        self.client_socket.sendall(msg.encode())
        try: 
            res = self.conn.receive_data(self.client_socket.recv(1024))
            while res == NEED_DATA:
                print("need more data")
                res = self.conn.receive_data(self.client_socket.recv(1024))
            resp = self.conn.next_event()
            if isinstance(resp, bytes):
                self.last_sequence_sent = int(resp)
                print(f"submitted #{self.last_sequence_sent}")
            else:
                if resp == NEED_DATA:
                    print("need more data")
                elif resp == CONNECTION_CLOSED:
                    print("could not parse netstring")
                    self.connect(self.host, self.remote_port)
        except ValueError as ve:
            print(f"couldn't get sequence # response for {msg}: {ve}")
        except BrokenPipeError as bpe:
            print(f"got broken pipe, reconnecting")
            self.connect(self.host, self.remote_port)

