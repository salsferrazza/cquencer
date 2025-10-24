from inventory import InventoryDestination
from sender import Sender

class Warehouse(InventoryDestination):
    def __init__(self, group, port):
        super().__init__(group, port)
        self.sender = Sender(3001)

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
        if qty <= current_level:
            self.inventory.apply(sku, qty * -1)
            self.sender.send(" ".join(["D", str(qty * -1), sku]))

    def on_inventory_delta(self, sku, delta):
        # ignore message if it was sent by me, since local
        # inventory is already updated
        if self.last_sequence_number != self.sender.last_sequence_sent:
            super().on_inventory_delta(sku, delta)
