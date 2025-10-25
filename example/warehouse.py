from inventory import InventoryDestination
from sender import SenderMixin

class Warehouse(InventoryDestination, SenderMixin):
    def __init__(self, group, port, remote_port):
        print("warehouse init")
        self.remote_port = remote_port
        self.connect("localhost", remote_port)
        print("warehosue init done")
        super().__init__(group, port)
        print(f"current sequence # is {self.last_sequence_number}")
        
    def on_message(self, seq, msg):
        print(f"warehouse on_message {seq}")
        super().on_message(seq, msg)
        msg_fields = msg.split()
        msg_type = msg_fields[0].decode('utf-8')
        if msg_type == "O":
            qty = int(msg_fields[1])
            sku = msg_fields[2].decode('utf-8')
            self.on_order(sku, qty)

    def on_order(self, sku, qty):
        current_level = self.inventory.get(sku)
        if qty <= current_level:
            self.inventory.apply(sku, qty * -1)
            self.send(" ".join(["D", str(qty * -1), sku]))

    def on_inventory_delta(self, sku, delta):
        # ignore message if it was sent by me, since local
        # inventory is already updated
        if self.last_sequence_number != self.last_sequence_sent:
            super().on_inventory_delta(sku, delta)
        else:
            print(f"ignoring #{self.last_sequence_number}")
