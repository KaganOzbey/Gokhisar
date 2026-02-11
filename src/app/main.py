from src.utils.serial_port import get_serial_port
from src.utils.paths import ROOT

def main():
    print("Project root:", ROOT)
    print("Serial port:", get_serial_port())

if __name__ == "__main__":
    main()
