import sys

from inventory import InventoryDestination
from sender import SenderMixin
from time import sleep

class Warehouse(InventoryDestination, SenderMixin):
    def __init__(self, group, port, remote_port):
        self.file_path = "data/inventory.txt"
        print("warehouse init")
        self.remote_port = remote_port
        self.connect("localhost", remote_port)
        print("warehouse init done")
        super().__init__(group, port)
        sleep(5)
        print("submitting inventory")
        self.submit_inventory()
        

    def submit_inventory(self):
        try:
            with open(self.file_path, 'r') as file:
                for line in file:
                    self.send(line.strip())
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
            sys.exit(1)
            
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)
            
    def on_message(self, seq, msg):
        super().on_message(seq, msg)
        msg_fields = msg.split()
        msg_type = msg_fields[0].decode('utf-8')
        if msg_type == "O":
            qty = int(msg_fields[1])
            sku = msg_fields[2].decode('utf-8')
            self.on_order(sku, qty)

    def on_inventory_delta(self, sku, delta):
        # short circuit execution of this method, since
        # the warehouse is the sole source-of-truth
        # for inventory updates, and the local inventory
        # is being updated directly within on_order()
        # before the inventory detla message is sent to
        # the sequenced stream
        pass
    
    def on_order(self, sku, qty):
        current_level = self.inventory.get(sku)

        # Only send the network a decrement
        # if there exists sufficient inventory
        if current_level is not None:
            print(f"#{self.last_sequence_number} wants {qty} of {sku}, {current_level} are in stock")
            if current_level >= qty:
                self.inventory.apply(sku, qty * -1) # obviates call to on_inventory_delta()
                self.send(" ".join(["D", str(qty * -1), sku]))
            else:
                print(f"Insufficient inventory of {current_level} to fulflll {qty} of {sku}")
        else:
            print(f"unknown sku: {sku}")

