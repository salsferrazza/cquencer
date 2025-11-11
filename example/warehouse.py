from inventory import InventoryDestination
from sender import SenderMixin

class Warehouse(InventoryDestination, SenderMixin):
    def __init__(self, group, port, remote_port):
        print("warehouse init")
        self.remote_port = remote_port
        self.connect("localhost", remote_port)
        print("warehouse init done")
        super().__init__(group, port)
        
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
            print(f"{sku} wants: {qty}, has: {current_level}, enough? {current_level >= qty}")
            if current_level >= qty:
                self.inventory.apply(sku, qty * -1) # obviates call to on_inventory_delta
                self.send(" ".join(["D", str(qty * -1), sku]))
            else:
                print(f"Insufficient inventory to fulflll {qty} of {sku}: {current_level}")
        else:
            print(f"unknown sku: {sku}")

