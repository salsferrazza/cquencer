import sys
from inventory import InventoryDestination
from warehouse import Warehouse
from pos import PointOfSale
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

def main():

    pos = PointOfSale(sys.argv[1], sys.argv[2], remote_port=3001)

    order_thread = Thread(target = pos.generate_orders)
    order_thread.start()

    pos.listen()
        
if __name__ == "__main__":
    main()

