import serial
import time
import serial.tools.list_ports as ports_list
import re
import os
import sys
import glob

available_ports = []
thread_devices = []
NRF_PLATFORM = "Zephyr"
SLABS_PLATFORM = "EFR32"

NETWORK_KEY = "00112233445566778899aabbccddeeff"
PAN_ID = "0xabcd"
CHANNEL = "15"

FTD_TXPOWER = 0
MTD_TXPOWER = -20


class ot_device:
    def __init__(self, port):
        self.port = port  # COM Port
        self.serial = serial.Serial(self.port, 115200, timeout=0.2, write_timeout=0.1)
        self.platform = ""  # zephyr or efr32
        self.rloc = ""
        self.ipaddr = ""
        self.failed = False  # TODO do something with this flag

    # Safely open port only if not open
    def open_port(self):
        if not self.serial.is_open:
            self.serial.open()

    # Safely close port only if open
    def close_port(self):
        if self.serial.is_open:
            self.serial.close()

    # Run command and wait 10ms and return formatted output
    def run_command(self, command):
        if self.platform == NRF_PLATFORM:
            command = "ot " + command
        self.serial.write(bytes(command + "\r\n", "utf-8"))
        time.sleep(0.1)
        self.serial.flush()
        return self.get_output()

    # Get output and format lines
    def get_output(self):
        self.serial.readline()
        res = self.serial.read(500)
        res = res.decode()
        return res

    def ping(self, address):
        res = self.run_command("ping " + address)
        res_arr = res.split(" ")
        try:
            drop_rate = float(
                re.findall("\d+\.\d+", res_arr[res_arr.index("Packet") + 3])[0]
            )
            return drop_rate
        except:
            return "error"
        
    def get_ip_addr(self):
        ipaddr_res = self.run_command("ipaddr").split('\n')
        address = [ip.strip() for ip in ipaddr_res if ":" in ip]
        extaddr = self.run_command("extaddr").split()[0]
        for ip in address:
            if ip[-15:].replace(':', '') == extaddr[-12:]:
                self.ipaddr = ip


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
    return ports_l


def link_devices():
    print("Finding thread devices...")
    for port in available_ports:
        if (
            os.path.exists(port) and int(re.findall(r"\d+", port)[0]) > 1
        ):  # TODO fix this - windows takes issue with os.path.exists it seems
            # if (int(re.findall(r'\d+', port)[0]) > 1):
            device = ot_device(port)
            platform = device.run_command("\r\nplatform")
            if "EFR32" in platform:
                device.platform = SLABS_PLATFORM
                thread_devices.append(device)
            platform = device.run_command("\r\not platform")
            if "Zephyr" in platform:
                device.platform = NRF_PLATFORM
                thread_devices.append(device)
    for device in thread_devices:
        print(device.port + " | " + device.platform)


def config_devices(routers=1):
    router = False
    router_count = 0
    for device in thread_devices:
        if not router:
            device.run_command("dataset init new")
            device.run_command("txpower " + str(FTD_TXPOWER))
            device.run_command("mode rdn")
            if router_count == routers:
                router = True
        else:
            device.run_command("txpower " + str(MTD_TXPOWER))
            device.run_command("mode rn")
        device.run_command("dataset channel " + CHANNEL)
        device.run_command("dataset networkkey " + NETWORK_KEY)
        device.run_command("dataset panid " + PAN_ID)
        device.run_command("dataset commit active")
        try:
            device.run_command("ifconfig up")
            device.rloc = re.findall(r"\d+", device.run_command("rloc16"))[0]
            device.failed = False
        except:
            device.failed = True


def get_network_state(extended=False):
    network_state = ""
    for device in thread_devices:
        s = "unknown"
        device_state = device.run_command("state")
        if "child" in device_state:
            s = "child"
        elif "disabled" in device_state:
            s = "disabled"
        elif "detached" in device_state:
            s = "detached"
        elif "router" in device_state:
            s = "router"
        elif "leader" in device_state:
            s = "leader"
        network_state += device.port + " | " + device.rloc + " | " + s
        if s == "unknown":
            print(device_state)
        if extended:
            panid = device.run_command("dataset panid")
            networkkey = device.run_command("dataset networkkey")
            channel = device.run_command("dataset channel")
            if device.ipaddr == "":
                device.get_ip_addr()
            network_state += (
                " | PAN ID: "
                + str(panid.split()[0])
                + " | Network Key: "
                + str(networkkey.split()[0])
                + " | Channel: "
                + str(channel.split()[0])
                + " | IP Address: "
                + device.ipaddr
            )
        network_state += "\n"
    return network_state[:-1]  # remove trailing carriage return


def start_network():
    for device in thread_devices:
        res = device.run_command("ifconfig up")
        res = device.run_command("thread start")
        ip = device.run_command("ipaddr")
        device.ipaddr = device.get_ip_addr()
        # TODO error handling - set failed flag to True if error


def stop_network():
    for device in thread_devices:
        res = device.run_command("thread stop")
        res = device.run_command("ifconfig down")
        # TODO error handling - set failed flag to True if error


# Get IP addresses of each device and state of each device
def ping_demo():
    res = "Sender | Receiver | Drop Rate\n"
    for device in thread_devices:
        for receiver in thread_devices:
            if device != receiver:
                drop_rate = device.ping(receiver.ipaddr)
                res += (
                    device.rloc + " | " + receiver.rloc + " | " + str(drop_rate) + "\n"
                )
    return res


def console():
    cmd = ""
    while cmd != "quit":
        try:
            cmd = input(">")

            if "demo" in cmd.split()[0]:
                if "ping" in cmd:
                    print(ping_demo())

            elif "config" in cmd:
                number = 1
                try:
                    number = int(re.findall(r"\d+", cmd)[0])
                except:
                    pass
                print("Configuring network with " + str(number) + " router...")
                config_devices(number)

            elif "state" in cmd:
                print(get_network_state())

            elif "start" in cmd:
                print("Starting thread network...")
                start_network()
                print(get_network_state())

            elif "stop" in cmd:
                print("Stopping thread network...")
                stop_network()
                print(get_network_state())
                
            elif "info" in cmd:
                print(get_network_state(True))

            else:
                print("Unknown Command")
        except KeyboardInterrupt:
            cmd = "quit"
    stop_network()


if __name__ == "__main__":
    available_ports = get_ports()
    link_devices()
    console()

'''
TODO:
 - format ping demo
'''