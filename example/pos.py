import random
from inventory import InventoryDestination
from sender import SenderMixin

class PointOfSale(InventoryDestination, SenderMixin):
    def __init__(self, group, port, remote_port):
        print("pos init")
        super().__init__(group, port)
        self.remote_port = remote_port
        self.connect("localhost", remote_port)
        print("pos init done")
        
    def send_random_order(self):
        sku_count = len(self.inventory.get(sku=None))
        if sku_count > 0:
            sku = random.choice(self.inventory.get(sku=None))
            qty = random.randint(1, self.inventory.get(sku))
            self.send_order(sku, qty)        
        
    def generate_orders(self, limit):
        if limit == -1:
            while True:
                self.send_random_order()   
        elif limit > 0:
            while limit > 0:
                self.send_random_order()
                limit -= 1

    def send_order(self, sku, quantity):
        current_stock = self.inventory.get(sku)

        if current_stock is None:
            return False

        if quantity <= current_stock:
            self.sender.send(" ".join(["O", quantity, sku]))
            return True
        else:
            return False
