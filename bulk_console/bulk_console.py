import serial
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

DEBUG = False


class ot_device:
    def __init__(self, port):
        self.port = port  # COM Port
        self.serial = serial.Serial(self.port, 115200, timeout=0.1, write_timeout=1.0)
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
        res = self.serial.read(1000)
        if DEBUG:
            print(res.decode())
        return res.decode()

    def ping(self, address):
        res = self.run_command("ping " + address)
        res_arr = res.split(" ")
        try:
            drop_rate = float(
                re.findall("\d+\.\d+", res_arr[res_arr.index("Packet") + 3])[0]
            )
            return drop_rate
        except:
            return "err"

    """
    The IP address is convoluted to resolve
    Multiple addresses are returned, and to find the correct one to ping
     the final 3 bytes must match the final 3 bytes of the extaddr.
    On top of that the addresses are in different formats so they also need
     to be flattened.
    """

    def get_ip_addr(self):
        ipaddr_res = self.run_command("ipaddr").split("\n")
        address = [ip.strip() for ip in ipaddr_res if ":" in ip]
        extaddr = self.run_command("extaddr").split()[0]
        if DEBUG:
            print(self.port + " | " + address + " | " + extaddr)
        for ip in address:
            if ip[-15:].replace(":", "") == extaddr[-12:]:
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
        if DEBUG:
            print(ports_l)
    return ports_l


def link_devices():
    print("Finding thread devices...")
    for port in available_ports:
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
            device.failed = False
        except:
            device.failed = True


def get_network_state(extended=False):
    network_state = ""
    rloc()
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
            device.get_ip_addr()
            network_info = ""
            network_info += (
                " | PAN ID: "
                + panid.split()[0]
                + " | Network Key: "
                + networkkey.split()[0]
                + " | Channel: "
                + channel.split()[0]
                + " | IP Address: "
                + str(device.ipaddr)
            )
            network_state += network_info
        network_state += "\n"
    return network_state[:-1]  # remove trailing carriage return


def start_network():
    for device in thread_devices:
        device.run_command("ifconfig up")
        device.run_command("thread start")
        device.run_command("ipaddr")
        device.ipaddr = device.get_ip_addr()


def stop_network():
    for device in thread_devices:
        device.run_command("thread stop")
        device.run_command("ifconfig down")


# Get IP addresses of each device and state of each device
def ping_demo():
    res = []
    for device in thread_devices:
        dev_res = []
        for receiver in thread_devices:
            if device == receiver:
                dev_res.append("-")
            else:
                dev_res.append(str(device.ping(receiver.ipaddr)))
        res.append(dev_res)
    return res


def rloc():
    for device in thread_devices:
        rloc = device.run_command("rloc16").split("\n")[0].strip()
        if DEBUG:
            print(device.port + " | " + rloc)
        device.rloc = rloc


def console():
    cmd = ""
    while cmd != "quit" or cmd != "hq":
        try:
            cmd = input(">")

            if "demo" in cmd.split()[0]:
                if "ping" in cmd:
                    for device in thread_devices:
                        device.get_ip_addr()
                    ping = ping_demo()
                    print("Drop Rate between Devices")
                    print("     ", end="")
                    for device in thread_devices:
                        print(f"{device.rloc:4} ", end="")
                    print()
                    for i, device in enumerate(thread_devices):
                        print(f"{device.rloc:5}", end="")
                        for rate in ping[i]:
                            if rate == "-":
                                print(f"{rate:5}", end="")
                            else:
                                print(f"{rate:5}", end="")
                        print()

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
    for device in thread_devices:
        device.close_port()


if __name__ == "__main__":
    available_ports = get_ports()
    link_devices()
    console()
