import signal
import sys
from inventory import InventoryDestination
from warehouse import Warehouse
from pos import PointOfSale
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

def main():

    pos1 = PointOfSale(sys.argv[1], sys.argv[2], remote_port=int(sys.argv[3])
    pos2 = PointOfSale(sys.argv[1], sys.argv[2], remote_port=int(sys.argv[3])
    pos3 = PointOfSale(sys.argv[1], sys.argv[2], remote_port=int(sys.argv[3])

    with ThreadPoolExecutor(max_workers=6) as posexec:
        posexec.submit(pos1.generate_orders)
        posexec.submit(pos2.generate_orders)
        posexec.submit(pos3.generate_orders)
        posexec.submit(pos1.listen)
        posexec.submit(pos2.listen)                        
        posexec.submit(pos3.listen)

        
if __name__ == "__main__":
    main()

