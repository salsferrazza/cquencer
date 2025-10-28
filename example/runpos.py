import sys
from inventory import InventoryDestination
from warehouse import Warehouse
from pos import PointOfSale
from concurrent.futures import ThreadPoolExecutor
        
def main():

    pos = PointOfSale(sys.argv[1], sys.argv[2], remote_port=3001)
        
    with ThreadPoolExecutor(max_workers=2) as posexec:
        posexec.submit(pos.listen())
        posexec.submit(pos.generate_orders(-1))

    
if __name__ == "__main__":
    main()

