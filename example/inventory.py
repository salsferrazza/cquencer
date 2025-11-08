import pickle
import sys
import traceback
from destination import Destination
from sender import SenderMixin

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
        del self.inventory[sku]
        
    def apply(self, sku, delta):
        current_level = self.inventory.get(sku) or 0
        assert(current_level + delta >= 0)
        new_level = current_level + delta
        self.inventory[sku] = new_level
        return new_level
        
class InventoryDestination(Destination):
    def __init__(self, group, port):
        super().__init__(group, port)
        self.inventory = InventoryCollection()

    def trap(self, signum, frame):
        print(str(self.inventory.inventory))
        sys.exit(1)
        
    def get_skus(self):
        return self.inventory.get(sku=None)
            
    def on_message(self, seq, msg):
        super().on_message(seq, msg)
        try:
            inv = msg.split() # whitespace-delimited

            if len(inv) < 3:
                print(f"malformed message received: {msg}")
                return

            msg_type = inv[0].decode('utf-8')
            sku = inv[2].decode('utf-8')
            qty = int(inv[1])
            if msg_type == "I":
                self.on_inventory(sku, qty)
            elif msg_type == "D":
                self.on_inventory_delta(sku, qty)

        except Exception as exc:
            traceback.print_exc()
            print(f"msg {seq} was unparseable: {exc} {msg}")
        
    def take_snapshot(self):
        return pickle.dumps(self.inventory)

    def on_inventory(self, sku, level):
        self.inventory.add(sku, level)
        print(f"{sku} {level}")
        
    def on_inventory_delta(self, sku, delta):
        level = self.inventory.get(sku)
        if level is None:
            print(f"Ignoring delta on depleted SKU {sku}")
            return

        new_level = self.inventory.apply(sku, delta)
        print(f"#{self.last_sequence_number} {sku} {level} {delta} -> {new_level}")
        if new_level == 0:
            print(f"Removing depleted SKU {sku} from inventory")
            self.inventory.remove(sku)
