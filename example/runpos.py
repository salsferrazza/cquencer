import signal
import sys
import json

from inventory import InventoryDestination
from pos import PointOfSale
from concurrent.futures import ThreadPoolExecutor
from time import sleep

NUM_POS = 10
WORKERS = NUM_POS * 2
pos_map = {}

def main():

    posexec = ThreadPoolExecutor(max_workers=WORKERS)

    i = 0
    while i < NUM_POS:
        pos = PointOfSale(sys.argv[1], sys.argv[2], remote_port=int(sys.argv[3]), pos_index=i)
        posexec.submit(pos.listen)
        pos_map[i] = pos
        i += 1


    print(str(pos_map.keys()))
    for pos in pos_map:
        posexec.submit(pos_map[pos].generate_orders)
        
if __name__ == "__main__":
    main()

