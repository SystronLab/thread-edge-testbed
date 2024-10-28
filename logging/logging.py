import serial
import serial.serialutil
import serial.tools.list_ports as ports_list
import re
import os
import sys
import glob
import time
import struct

available_ports = []
thread_devices = []

NRF_PLATFORM = "Zephyr"
SLABS_PLATFORM = "EFR32"

DEBUG = False

class ot_device:
    def __init__(self, port):
        self.port = port  # COM Port
        self.serial = serial.Serial(self.port, 115200, timeout=0.1, write_timeout=1.0)
        self.rloc = ""
        self.platform = ""
        self.log = ""

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

def decode_packets(hex_log):
    # Convert hex string to bytes
    packet_bytes = bytes.fromhex(hex_log)
    
    # Define the struct format for a single 32-byte packetData struct
    struct_format = '>HHHBB24s'
    struct_size = struct.calcsize(struct_format)
    
    # Verify if the hex log length is a multiple of the struct size
    if len(packet_bytes) % struct_size != 0:
        raise ValueError("Hex log length is not a multiple of the expected struct size (32 bytes).")
    
    packets = []
    
    # Process each 32-byte chunk in the hex log
    for i in range(0, len(packet_bytes), struct_size):
        # Extract the 32-byte chunk
        packet_chunk = packet_bytes[i:i + struct_size]
        
        # Unpack the chunk
        unpacked_data = struct.unpack(struct_format, packet_chunk)
        
        # Map the unpacked data to struct fields
        packet_data = {
            'deviceId': unpacked_data[0],
            'deviceFunctions': unpacked_data[1],
            'packetCount': unpacked_data[2],
            'deviceType': unpacked_data[3],
            'dataLen': unpacked_data[4],
            'data': unpacked_data[5]
        }
        
        packets.append(packet_data)
    
    return packets


def link_devices():
    print("Finding thread devices...")
    for port in available_ports:
        try:
            if os.path.exists(port) and int(re.findall(r"\d+", port)[0]) > 1:
                device = ot_device(port)
                platform = device.run_command("\r\nplatform")
                if "EFR32" in platform:
                    device.platform = SLABS_PLATFORM
                    thread_devices.append(device)
                platform = device.run_command("\r\not platform")
                if "Zephyr" in platform:
                    device.platform = NRF_PLATFORM
                    thread_devices.append(device)
        except serial.serialutil.SerialTimeoutException:
            pass # ignore devices that timeout
            
    for device in thread_devices:
        print(f"{device.port:5}" + " | " + device.platform)

def rloc():
    for device in thread_devices:
        rloc = device.run_command("ot rloc16")
        if DEBUG:
            print(device.port + " | " + rloc)
        device.rloc = rloc.split("\n")[0].strip()        
 
def clear_logs():
    for device in thread_devices:
        device.run_command("testbed clearlog")
        
def get_dump_log():
    for device in thread_devices:
        device.serial.write(bytes("testbed dumprawlog" + "\r\n", "utf-8"))
        device.serial.readline()
        rawlog = device.serial.read(10000).decode()
        device.log = rawlog

def parse_log():
    for device in thread_devices:
        print("\n" + device.port)
        log_array = device.log.split(' ')
        filtered_log_array = [string.strip() for string in log_array if len(string.strip()) == 2]
        filtered_log = ''.join(filtered_log_array)
        struct_data = decode_packets(filtered_log)
        print(struct_data)
    
def console():
    try:
        while True:
            cmd = input(">")
            if cmd == "clear":
                clear_logs()
            if cmd == "log":
                get_dump_log()
                parse_log()
    except KeyboardInterrupt:
        pass
            

if __name__ == "__main__":
    available_ports = get_ports()
    link_devices()
    rloc()
    console()