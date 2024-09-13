import serial
import serial.serialutil
import serial.tools.list_ports as ports_list
import re
import os
import sys
import glob
import time

available_ports = []
thread_device = None
NRF_PLATFORM = "Zephyr"
SLABS_PLATFORM = "EFR32"

NETWORK_KEY = "00112233445566778899aabbccddeeff"
PAN_ID = "0xabcd"
CHANNEL = "25"

SCAN_LENGTH = 250

FTD_TXPOWER = 0
MTD_TXPOWER = -20

DEBUG = False

class ot_device:
    def __init__(self, port):
        self.port = port  # COM Port
        self.serial = serial.Serial(self.port, 115200, timeout=0.1, write_timeout=1.0)
        self.platform = ""  # zephyr or efr32
        self.rloc = ""
        self.ipaddr = ""
        self.failed = False  # TODO do something with this flag
        self.rssi_dict = {str(i): "" for i in range(11, 27)}

    # Safely open port only if not open
    def open_port(self):
        if not self.serial.is_open:
            self.serial.open()

    # Safely close port only if open
    def close_port(self):
        if self.serial.is_open:
            self.serial.close()

    """
    Nordic boards seem to have an issue where the input buffer gets partially rewritten
     to when running commands in quick succession, specifically after the `ot ifconfig up`
     command where it leaves `ot ifcoot` in the input buffer.
    Probably an issue with the serial interface which I could fix, or I could just hit make
     it run the command, nothing happen because it's unknown and carry on.
    """

    def reset_buffer(self):
        self.serial.write(bytes("\r\n", "utf-8"))
        self.serial.read(1000)
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    # Run command and return formatted output
    def run_command(self, command):
        self.reset_buffer()
        if self.platform == NRF_PLATFORM:
            command = "ot " + command
        self.serial.write(bytes(command + "\r\n", "utf-8"))
        if DEBUG:
            print("\n" + command)
        return self.get_output()

    # Get output and format lines
    def get_output(self):
        self.serial.readline()
        res = self.serial.read(10000)
        if DEBUG:
            print(res.decode())
        return res.decode()

    def get_ip_addr(self):
        ipaddr_res = self.run_command("ipaddr").split("\n")
        for ipaddr in ipaddr_res:
            if ipaddr.strip()[-4:] == self.rloc:
                self.ipaddr = ipaddr.strip()
    
    def scan_network(self):
        scan = self.run_command("scan").split("\n")
        print(scan)
        
# Get available COM ports
def get_ports():
    ports_l = []
    if sys.platform.startswith("win"):
        ports = list(ports_list.comports())
        for port in ports:
            ports_l.append(port.name)
    elif sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
        ports_l = glob.glob("/dev/ttyACM*")
    else:
        print("No available ports found")
    if len(ports_l):
        print("\n" + str(len(ports_l)) + " serial connections found")
        if DEBUG:
            print(ports_l)
    return ports_l


def link_devices():
    print("Finding thread devices...")
    for port in available_ports:
        try:
            if os.path.exists(port) and int(re.findall(r"\d+", port)[0]) > 1:
                device = ot_device(port)
                platform = device.run_command("\r\nplatform")
                if "EFR32" in platform:
                    device.platform = SLABS_PLATFORM
                    thread_device = device
                platform = device.run_command("\r\not platform")
                if "Zephyr" in platform:
                    device.platform = NRF_PLATFORM
                    thread_device = device
        except serial.serialutil.SerialTimeoutException:
            pass # ignore devices that timeout