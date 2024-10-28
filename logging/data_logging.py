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

MIN_PACKET_SIZE = 8
MAX_PACKET_SIZE = 32

class ot_device:
    def __init__(self, port):
        self.port = port  # COM Port
        self.serial = serial.Serial(self.port, 115200, timeout=0.5, write_timeout=1.0)
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
    log_bytes = bytes.fromhex(hex_log)
    
    # Define the struct format for a single 32-byte packetData
    packet_format = '>HHHBB24s'
    packet_size = struct.calcsize(packet_format)
    
    # Define constant sizes for fields
    HEADER_SIZE = 8  # for Message Log Format
    packets = []
    
    # Process each 32-byte packetData struct in the log
    for i in range(0, len(log_bytes), packet_size):
        if i + packet_size > len(log_bytes):  # Stop if remaining bytes are less than 32
            break
            
        # Extract the 32-byte packetData chunk
        packet_chunk = log_bytes[i:i + packet_size]
        
        # Unpack the packetData chunk
        unpacked_packet = struct.unpack(packet_format, packet_chunk)
        
        # Map unpacked values to packet fields
        device_id = unpacked_packet[0]
        device_functions = unpacked_packet[1]
        packet_count = unpacked_packet[2]
        device_type = unpacked_packet[3]
        data_len = unpacked_packet[4]
        data_bytes = unpacked_packet[5][:data_len]  # Only consider `dataLen` bytes of `data`
        
        # Determine log type identifier
        log_type_identifier = data_bytes[0:1].decode(errors='ignore') if data_bytes else None
        
        # Decode the `data` field based on the log type identifier
        message_data = {}
        
        if log_type_identifier == 'M' and len(data_bytes) >= HEADER_SIZE:
            # Message Log Format
            message_string = ""
            try:
                message_string = data_bytes[8:data_bytes.find(b'\x00', 8)].decode() if b'\x00' in data_bytes[8:] else ""
            except UnicodeDecodeError:
                message_string = "<Undecodable Message String>"
            
            message_data = {
                'logTypeIdentifier': 'M',
                'cpuTime': int.from_bytes(data_bytes[2:6], 'little'),
                'linkShortAddress': int.from_bytes(data_bytes[6:8], 'little'),
                'messageString': message_string
            }
        
        elif log_type_identifier == 'R' and len(data_bytes) >= 6:
            # Received Packet Format
            message_data = {
                'logTypeIdentifier': 'R',
                'deviceState': data_bytes[1],
                'cpuTime': int.from_bytes(data_bytes[2:6], 'little'),
                'receivedPacket': data_bytes[6:]  # Keep as bytes to avoid decoding issues
            }
        
        elif log_type_identifier == 'T' and len(data_bytes) >= 6:
            # Transmitted Packet Format
            message_data = {
                'logTypeIdentifier': 'T',
                'deviceState': data_bytes[1],
                'cpuTime': int.from_bytes(data_bytes[2:6], 'little'),
                'transmittedPacket': data_bytes[6:]  # Keep as bytes to avoid decoding issues
            }
        
        # Store packet data along with the parsed message log information
        packets.append({
            'deviceId': device_id,
            'deviceFunctions': device_functions,
            'packetCount': packet_count,
            'deviceType': device_type,
            'dataLen': data_len,
            'messageData': message_data
        })
    
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
        device.serial.write(bytes("testbed dumprawlog" + "\r\n", "ascii"))
        device.serial.readline()
        rawlog = device.serial.read(10000).decode()
        device.log = rawlog
        print(rawlog)

def parse_log():
    for device in thread_devices:
        print("\n" + device.port)
        log_array = device.log.split(' ')
        filtered_log_array = [string.strip() for string in log_array if len(string.strip()) == 2]
        filtered_log = ''.join(filtered_log_array)
        struct_data = decode_packets(filtered_log)
        for struct in struct_data:
            print(struct)
    
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