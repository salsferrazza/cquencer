import sys
import socket
from netstring import Connection, NEED_DATA, CONNECTION_CLOSED, decode

class SenderMixin:

    last_sequence_sent = 0
    msgbuf = bytearray(21)

    def __del__(self):
        if hasattr(self, 'client_socket') and self.client_socket is not None:
            self.client_socket.close()
    
    def connect(self, host, remote_port):
        """Connects to the cquencer TCP port for sending unsequenced messages

        Parameters
        ----------
        host: 
            The host running cq
        remote_port : int
            The TCP listen port on the cq host
        """

        # for stream-based netstring processing
        self.conn = Connection()
        
        self.remote_port = remote_port
        self.host = host

        # TCP connection to the sequencer
        self.client_socket = socket.socket()
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Fixed: using the passed-in host rather than hardcoded "localhost"
        self.client_socket.connect((self.host, self.remote_port))
        

    def send(self, msg):
        """Sends an unsequenced message to cquencer

        Parameters
        ----------
        msg: 
            The message payload to be sequenced
        """
        
        # 1. Convert string to bytes (handles multi-byte UTF-8 correctly for length)
        msg_bytes = msg.encode('utf-8') if isinstance(msg, str) else msg
        
        # 2. Wrap in netstring framing: [length]:[data],
        netstring_msg = b"%d:%b," % (len(msg_bytes), msg_bytes)
        
        try:
            # 3. Send the netstring-encoded payload
            self.client_socket.sendall(netstring_msg)
            
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
