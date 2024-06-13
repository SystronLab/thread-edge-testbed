import time
import serial
import serial.serialutil
import serial.tools.list_ports as ports_list
import re
import os
import sys
import glob
from flask import Flask, request, jsonify

app = Flask(__name__)

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
        self.panid = ""
        self.network_key = ""
        self.channel = ""

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
    Probably an issue with the serial interface which I could fix, or I could just make
     it run the command, nothing happens because it's unknown and carry on.
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

    def get_ip_addr(self):
        ipaddr_res = self.run_command("ipaddr").split("\n")
        # print(ipaddr_res, self.rloc)
        for ipaddr in ipaddr_res:
            if ipaddr.strip()[-4:] == self.rloc:
                self.ipaddr = ipaddr.strip()


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


def link_devices(available_ports):
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
        print(f"{device.port:15}" + " | " + device.platform)


def config_devices(routers=1):
    router = False
    router_count = 0
    for device in thread_devices:
        device.run_command("dataset clear")
        if not router:
            router_count += 1
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
    network_state = []
    rloc()
    for device in thread_devices:
        device_state = []
        s = "unknown"
        state = device.run_command("state")
        if "child" in state:
            s = "child"
        elif "disabled" in state:
            s = "disabled"
        elif "detached" in state:
            s = "detached"
        elif "router" in state:
            s = "router"
        elif "leader" in state:
            s = "leader"
        device_state.append({"port": device.port})
        device_state.append({"state": s})
        device_state.append({"rloc": device.rloc})
        if extended:
            device.panid = device.run_command("dataset panid").split()[0]
            device.networkkey = device.run_command("dataset networkkey").split()[0]
            device.channel = device.run_command("dataset channel").split()[0]
            device.get_ip_addr()
            device_state.append({"panid": device.panid})
            device_state.append({"networkkey": device.networkkey})
            device_state.append({"channel": device.channel})
            device_state.append({"ipaddr": device.ipaddr})
        network_state.append(device_state)
    return network_state


def start_network():
    for device in thread_devices:
        device.run_command("ifconfig up")
        device.run_command("thread start")
        device.rloc = device.run_command("rloc16").split("\n")[0].strip()
        device.ipaddr = device.get_ip_addr()


def stop_network(full_stop=False):
    for device in thread_devices:
        device.run_command("thread stop")
        device.run_command("ifconfig down")
        if full_stop:
            device.close_port()


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
        rloc = device.run_command("rloc16")
        if DEBUG:
            print(device.port + " | " + rloc)
        device.rloc = rloc.split("\n")[0].strip()


@app.route("/config", methods=["GET", "POST"])
def config_route():
    start = time.time()
    if request.method == "GET":
        if len(thread_devices) == 0:
            return (
                jsonify(
                    isError=True,
                    message=f"Devices not started",
                    statusCode=400,
                    responseTime=time.time() - start,
                ),
                400,
            )
        else:
            config_devices(1)
            start_network()
            return (
                jsonify(
                    isError=False,
                    message=f"{len(thread_devices)} devices configured with 1 router",
                    statusCode=200,
                    responseTime=time.time() - start,
                ),
                200,
            )
    elif request.method == "POST":
        if len(thread_devices) == 0:
            return (
                jsonify(
                    isError=True,
                    message=f"Devices not started",
                    statusCode=400,
                    responseTime=time.time() - start,
                ),
                400,
            )
        else:
            routers = request.form.get("routers")
            config_devices(routers)
            start_network()
            return (
                jsonify(
                    isError=False,
                    message=f"{len(thread_devices)} devices configured with {routers} router{'s' if routers > 1 else ''}",
                    statusCode=200,
                    responseTime=time.time() - start,
                ),
                200,
            )


@app.route("/stop", methods=["GET"])
def stop_network_route():
    start = time.time()
    if request.method == "GET":
        stop_network()
        return (
            jsonify(
                isError=False,
                message="Network stopped",
                statusCode=200,
                responseTime=time.time() - start,
            ),
            200,
        )


@app.route("/state", methods=["GET"])
def state_route():
    start = time.time()
    if request.method == "GET":
        return (
            jsonify(
                isError=False,
                statusCode=200,
                data=get_network_state(True),
                responseTime=time.time() - start,
            ),
            200,
        )


@app.route("/start", methods=["GET"])
def start_route():
    start = time.time()
    if request.method == "GET":
        ports = get_ports()
        link_devices(ports)
        return (
            jsonify(
                isError=False,
                message=f"Serial Communication started with {len(thread_devices)} devices",
                statusCode=200,
                responseTime=time.time() - start,
            ),
            200,
        )
        
        
@app.route("/ping", methods=["GET"])
def ping_route():
    start = time.time()
    for device in thread_devices:
        device.get_ip_addr()
        # TODO: Format this section
        ping = ping_demo()
        for i, device in enumerate(thread_devices):
            print(f"{device.rloc:5}", end="")
            for rate in ping[i]:
                if rate == "-":
                    print(f"{rate:5}", end="")
                else:
                    print(f"{rate:5}", end="")
            print()

# def console():
#     cmd = ""
#     while True:
#         try:
#             cmd = input(">")
#             if "demo" in cmd.split()[0]:
#                 if "ping" in cmd:
#                     for device in thread_devices:
#                         device.get_ip_addr()
#                     ping = ping_demo()
#                     print("Drop Rate between Devices")
#                     print("     ", end="")
#                     for device in thread_devices:
#                         print(f"{device.rloc:4} ", end="")
#                     print()
#                     for i, device in enumerate(thread_devices):
#                         print(f"{device.rloc:5}", end="")
#                         for rate in ping[i]:
#                             if rate == "-":
#                                 print(f"{rate:5}", end="")
#                             else:
#                                 print(f"{rate:5}", end="")
#                         print()

#             elif "state" in cmd:
#                 print(get_network_state())

#             elif "start" in cmd:
#                 print("Starting thread network...")
#                 start_network()
#                 print(get_network_state(True))

#             elif "stop" in cmd:
#                 print("Stopping thread network...")
#                 stop_network()
#                 print(get_network_state())

#             elif "info" in cmd:
#                 print(get_network_state(True))

#             elif cmd == "quit":
#                 break

#             else:
#                 print("Unknown Command")
#         except KeyboardInterrupt:
#             break
#     stop_network(True)
