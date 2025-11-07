import signal
import sys
from inventory import InventoryDestination
from warehouse import Warehouse
from pos import PointOfSale
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

def main():

    pos1 = PointOfSale(sys.argv[1], sys.argv[2], remote_port=3001)
    pos2 = PointOfSale(sys.argv[1], sys.argv[2], remote_port=3001)
    pos3 = PointOfSale(sys.argv[1], sys.argv[2], remote_port=3001)

    with ThreadPoolExecutor(max_workers=6) as whsexec:
        whsexec.submit(pos1.generate_orders)
        whsexec.submit(pos2.generate_orders)
        whsexec.submit(pos3.generate_orders)
        whsexec.submit(pos1.listen)
        whsexec.submit(pos2.listen)                        
        whsexec.submit(pos3.listen)

        
if __name__ == "__main__":
    main()

