import sys

from sender import SenderMixin
from time import sleep

class Lineload(SenderMixin):
    def __init__(self, remote_port):
        self.file_path = "data/inventory.txt"
        self.remote_port = remote_port
        self.connect("localhost", remote_port)

    def submit_inventory(self):
        try:
            with open(self.file_path, 'r') as file:
                for line in file:
                    self.send(line.strip())
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
            sys.exit(1)
            
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)
