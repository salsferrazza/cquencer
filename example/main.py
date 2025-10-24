import sys
from warehouse import Warehouse
        
def main():
    dest = Warehouse(sys.argv[1], sys.argv[2])
    dest.listen()
    
if __name__ == "__main__":
    main()

