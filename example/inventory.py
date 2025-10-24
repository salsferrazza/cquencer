from destination import Destination

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
            self.on_inventory(inv[2].decode('utf-8'), int(inv[1]))
        elif msg_type == "D":
            self.on_inventory_delta(inv[2].decode('utf-8'), int(inv[1]))
        
    def on_inventory(self, sku, level):
        self.inventory.add(sku, level)
        print(f"{sku} {level}")
    
    def on_inventory_delta(self, sku, delta):
        level = self.inventory.get(sku)
        self.inventory.apply(sku, delta)
        new_level = self.inventory.get(sku)
        print(f"{sku} {delta} {level} -> {new_level}")
