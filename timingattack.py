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

    def reset_buffer(self):
        self.serial.write(bytes("\r\n", "utf-8"))
        self.serial.read(1000)
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    def run_command(self, command):
        self.reset_buffer()
        if self.platform == NRF_PLATFORM:
            command = "ot " + command
        self.serial.write(bytes(command + "\r\n", "utf-8"))
        if DEBUG:
            print("\n" + command)
        return self.get_output()

    def get_output(self):
        self.serial.readline()
        res = self.serial.read(1000)
        if DEBUG:
            print(res.decode())
        return res.decode()

    def ping(self, address):
        # Timing measurement for each ping
        start_time = time.time()
        res = self.run_command("ping " + address)
        end_time = time.time()

        elapsed_time = end_time - start_time  # Calculate the response time
        print(f"Ping response time to {address}: {elapsed_time:.6f} seconds")

        try:
            drop_rate = float(
                re.findall("\d+\.\d+", res.split(" ")[res.split(" ").index("Packet") + 3])[0]
            )
            return elapsed_time, drop_rate
        except:
            return elapsed_time, "err"

    def get_ip_addr(self):
        ipaddr_res = self.run_command("ipaddr").split("\n")
        for ipaddr in ipaddr_res:
            if ipaddr.strip()[-4:] == self.rloc:
                self.ipaddr = ipaddr.strip()


# Function to link devices (same as before)
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


# Function to run the timing attack
def timing_attack_demo():
    timing_results = []
    for device in thread_devices:
        for receiver in thread_devices:
            if device != receiver:
                elapsed_time, drop_rate = device.ping(receiver.ipaddr)
                timing_results.append((device.port, receiver.port, elapsed_time, drop_rate))

    # Output results
    print("\nTiming Attack Results:")
    for result in timing_results:
        print(f"From {result[0]} to {result[1]}: {result[2]:.6f} seconds, Drop Rate: {result[3]}")

    # Analyze and identify anomalies
    analyze_timing(timing_results)


# Analyze timing results to detect potential timing anomalies
def analyze_timing(results):
    average_time = sum([res[2] for res in results]) / len(results)
    print(f"\nAverage Response Time: {average_time:.6f} seconds")

    anomalies = [res for res in results if abs(res[2] - average_time) > 0.01]  # Example threshold
    if anomalies:
        print("\nPotential Timing Anomalies Detected:")
        for anomaly in anomalies:
            print(f"From {anomaly[0]} to {anomaly[1]}: {anomaly[2]:.6f} seconds, Drop Rate: {anomaly[3]}")
    else:
        print("No significant timing anomalies detected.")


# Flask routes (modified to include timing attack)
@app.route("/timing_attack", methods=["GET"])
def timing_attack_route():
    start = time.time()
    timing_attack_demo()
    return (
        jsonify(
            isError=False,
            message="Timing attack executed and analyzed",
            statusCode=200,
            responseTime=time.time() - start,
        ),
        200,
    )


if __name__ == "__main__":
    ports = get_ports()
    link_devices(ports)
    timing_attack_demo()
