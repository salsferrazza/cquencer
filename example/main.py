import sys
from inventory import InventoryDestination
from warehouse import Warehouse
from pos import PointOfSale
from concurrent.futures import ThreadPoolExecutor
        
def main():

    warehouse = Warehouse(sys.argv[1], sys.argv[2], remote_port=3001)
        
    with ThreadPoolExecutor(max_workers=1) as whsexec:
        whsexec.submit(warehouse.listen())

    
if __name__ == "__main__":
    main()

