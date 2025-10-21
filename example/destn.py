import sys
import socket
import struct
from netstring import Connection

class Destination:

    def __init__(self, group, port):
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
        
    def listen(self):
        while True:
            # get the entire nested netstring
            self.conn.receive_data(self.sock.recv(10240))

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
        # this keeps the whole thing together
        if seq != expect:
            raise Exception(f"Sequence number mismatch got {seq} but expected {expect}") 

#        print(f"{seq}: {msg.decode('utf-8')}")
        
        self.messages_received += 1
        self.last_sequence_number = seq

class InventoryCollection():

    def __init__(self):
        self.inventory = {}

    def get(self, sku):
        return self.inventory[sku]
        
    def add(self, sku, stock_level):
        self.inventory[sku] = stock_level

    def remove(self, sku):
        self.inventory[sku] = None
        
    def apply(self, sku, delta):
        current_level = self.inventory[sku]
        self.inventory[sku] = current_level + delta

class InventoryDestination(Destination):
    def __init__(self, group, port):
        super().__init__(group, port)
        self.inventory = InventoryCollection()

    def on_message(self, seq, msg):
        super().on_message(seq, msg)
        inv = msg.split()
        msg_type = inv[0].decode('utf-8')
        if msg_type == "I":
            self.inventory.add(inv[2].decode('utf-8'), int(inv[1]))
            self.on_inventory(inv[2].decode('utf-8'), int(inv[1]))
        elif msg_type == "D":
            self.inventory.apply(inv[2].decode('utf-8'), int(inv[1]))
            self.on_inventory_delta(inv[2].decode('utf-8'), int(inv[1]))
        else:
            # unknown message type
            pass
        
    def on_inventory(self, sku, level):
        print(f"{sku} {level}")
    
    def on_inventory_delta(self, sku, delta):
        level = self.inventory.get(sku)
        print(f"{sku} {delta} {level}")
    
        
class PointOfSale(InventoryDestination):
    def on_message(self, seq, msg):
        super().on_message(seq, msg)

class Warehouse(InventoryDestination):
    def on_message(self, seq, msg):
        super().on_message(seq, msg)
        
def main():
    dest = InventoryDestination(sys.argv[1], sys.argv[2])
    dest.listen()
    
if __name__ == "__main__":
    main()
    
 
