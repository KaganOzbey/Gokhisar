import platform
from serial.tools import list_ports

def get_serial_port():
    system = platform.system().lower()
    ports = list(list_ports.comports())

    if not ports:
        return None

    if "windows" in system:
        return ports[0].device

    for p in ports:
        if "ttyUSB" in p.device or "ttyACM" in p.device:
            return p.device

    return ports[0].device
