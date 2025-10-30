import random
from sender import SenderMixin
from time import sleep

from inventory import InventoryDestination

class PointOfSale(InventoryDestination, SenderMixin):
    def __init__(self, group, port, remote_port):
        print("pos init")
        super().__init__(group, port)
        self.remote_port = remote_port
        self.connect("localhost", remote_port)
        print("pos init done")
        
    def send_random_order(self):
        sku_count = len(self.inventory.get(sku=None))
        print(f"sku count {sku_count}")
        if sku_count > 0:
            
            sku = random.choice(list(self.inventory.get(sku=None)))
            qty = random.randint(1, self.inventory.get(sku))
            self.send_order(sku, qty)        
        
    def generate_orders(self):
        print("generating orders")
        while True:
            self.send_random_order()
            sleep(3)
                
    def send_order(self, sku, quantity):
        current_stock = self.inventory.get(sku)

        if current_stock is None:
            return False

        if quantity <= current_stock:
            self.send(" ".join(["O", str(quantity), sku]))
            return True
        else:
            return False
