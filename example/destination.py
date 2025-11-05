import sys
import socket
import struct
from netstring import Connection

class Destination:
    def __init__(self, group, port):
        print("destination init")
        self.group = group
        self.port = port
        self.conn = Connection()
        self.messages_received = 0
        self.last_sequence_number = 0
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind((self.group, int(self.port)))
        mreq = struct.pack('4sl', socket.inet_aton(self.group), socket.INADDR_ANY)

        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print(f"current sequence # is {self.last_sequence_number}")
        print("destination init done")
        
    def listen(self):
        print("destination listening...")
        while True:
            # get the entire nested netstring
            self.conn.receive_data(self.sock.recv(1024))

            # feed both netstrings back into the conneciton
            self.conn.receive_data(self.conn.next_event())

            # pull the first child, which is the sequence number            
            seq = self.conn.next_event().decode('utf-8')

            # pull the second child, which is the submitted data
            payload = self.conn.next_event()
            
            # dispatch the event to the message handler
            self.on_message(int(seq), payload)

    def on_message(self, seq, msg): 
        expect = self.last_sequence_number + 1
        # without this check, everything falls apart
        if seq != expect:
            raise Exception(f"Sequence number mismatch got {seq} but expected {expect}") 

        self.messages_received += 1
        self.last_sequence_number = seq

