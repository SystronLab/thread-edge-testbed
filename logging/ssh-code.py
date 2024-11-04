import serial
import serial.serialutil
import serial.tools.list_ports as ports_list
import re
import os
import sys
import glob
import json
import time

available_ports = []
thread_devices = []

NRF_PLATFORM = 'Zephyr'
SLABS_PLATFORM = 'EFR32'

MIN_PACKET_SIZE = 8
MAX_PACKET_SIZE = 32

class ot_device:
    def __init__(self, port):
        self.port = port  # COM Port
        self.serial = serial.Serial(self.port, 115200, timeout=1.0, write_timeout=1.0)
        self.rloc = ''
        self.platform = ''
        self.log = ''

    def reset_buffer(self):
        self.serial.write(bytes('\r\n', 'utf-8'))
        self.serial.read(1000)
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    # Run command and return formatted output
    def run_command(self, command):
        self.reset_buffer()
        self.serial.write(bytes(command + '\r\n', 'utf-8'))
        return self.get_output()

    # Get output and format lines
    def get_output(self):
        self.serial.readline()
        res = self.serial.read(10000)
        return res.decode()
    
# Get available COM ports
def get_ports():
    ports_l = []
    if sys.platform.startswith('win'):
        ports = list(ports_list.comports())
        for port in ports:
            ports_l.append(port.name)
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports_l = glob.glob('/dev/ttyACM*')
    else:
        print('No available ports found')
    return ports_l

def link_devices():
    for port in available_ports:
        try:
            if os.path.exists(port):
                device = ot_device(port)
                platform = device.run_command('\r\nplatform')
                if 'EFR32' in platform:
                    device.platform = SLABS_PLATFORM
                    thread_devices.append(device)
                platform = device.run_command('\r\not platform')
                if 'Zephyr' in platform:
                    device.platform = NRF_PLATFORM
                    thread_devices.append(device)
        except serial.serialutil.SerialTimeoutException:
            pass # ignore devices that timeout

def rloc():
    for device in thread_devices:
        rloc = device.run_command('ot rloc16')
        device.rloc = rloc.split('\n')[0].strip()
        
def get_dump_log():
    for device in thread_devices:
        device.serial.write(bytes('testbed dumprawlog' + '\r\n', 'ascii'))
        device.serial.readline()
        rawlog = device.serial.read(10000).decode()
        device.log = rawlog
        
def format_log():
    log = {}
    for device in thread_devices:
        log_array = device.log.split(' ')
        filtered_log_array = [string.strip() for string in log_array if len(string.strip()) == 2]
        filtered_log = ''.join(filtered_log_array)
        log[device.rloc] = filtered_log
    return log

def setup_devices():
    # for device in thread_devices:
    #     device.run_command("kernel reboot cold")
    # time.sleep(10)
    i = 1
    for device in thread_devices:
        device.run_command("testbed setid " + str(i))
        device.rloc = i
        device.run_command("ot txpower -10")
        device.run_command("testbed enablecm")
        device.run_command("testbed packetlog off")
        device.run_command("testbed debug off")
        device.run_command("testbed clearlog")
        i += 1

log = {}
available_ports = get_ports()
print(available_ports)
link_devices()
setup_devices()
get_dump_log()
log = format_log()

print(json.dumps(log))