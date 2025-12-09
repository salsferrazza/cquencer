import signal
import sys
from inventory import InventoryDestination
from pos import PointOfSale
from concurrent.futures import ThreadPoolExecutor

NUM_POS = 50
WORKERS = NUM_POS * 2

def main():

    posexec = ThreadPoolExecutor(max_workers=WORKERS)

    i = 0
    while i < NUM_POS:
        pos = PointOfSale(sys.argv[1], sys.argv[2], remote_port=int(sys.argv[3]))
        posexec.submit(pos.generate_orders)
        posexec.submit(pos.listen)
        i += 1

        
if __name__ == "__main__":
    main()

