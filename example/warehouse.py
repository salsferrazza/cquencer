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

    def on_order(self, sku, qty):
        current_level = self.inventory.get(sku)
        if current_level is not None:
            if qty <= current_level:
                self.send(" ".join(["D", str(qty * -1), sku]))
            else:
                print(f"Insufficient inventory to fulflll {qty} of {sku}: {current_level}")
        else:
            print(f"unknown sku: {sku}")

