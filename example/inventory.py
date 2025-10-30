import traceback
from destination import Destination

class InventoryCollection():

    def __init__(self):
        self.inventory = {}

    def count(self):
        return len(self.inventory.keys())

    def skus(self):
        return list(self.inventory.keys())

    def get(self, sku):
        if sku is not None:
            return self.inventory.get(sku)

        return self.inventory.keys()
        
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

    def get_skus(self):
        return self.inventory.get(sku=None)
            
    def on_message(self, seq, msg):
        super().on_message(seq, msg)
        try:
            inv = msg.split()

            if len(inv) < 3:
                print(f"malformed message received: {msg}")
                return

            msg_type = inv[0].decode('utf-8')
            if msg_type == "I":
                self.on_inventory(inv[2].decode('utf-8'), int(inv[1]))
            elif msg_type == "D":
                self.on_inventory_delta(inv[2].decode('utf-8'), int(inv[1]))

        except Exception as exc:
            traceback.print_exc()
            print(f"msg {seq} was unparseable: {exc} {msg}")
        
    def on_inventory(self, sku, level):
        self.inventory.add(sku, level)
        print(f"{sku} {level}")
    
    def on_inventory_delta(self, sku, delta):
        level = self.inventory.get(sku)
        self.inventory.apply(sku, delta)
        new_level = self.inventory.get(sku)
        print(f"{sku} {level} {delta} -> {new_level}")
