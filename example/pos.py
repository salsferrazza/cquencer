from .inventory import InventoryDestination

class PointOfSale(InventoryDestination):
    def __init__(self, group, port):
        super().__init__(group, port)
        self.sender = Sender(3001)

    def send_order(self, sku, quantity):
        current_stock = self.inventory.get(sku)
        if quantity <= current_stock:
            self.sender.send(" ".join(["O", quantity, sku]))
            return True
        else:
            return False
