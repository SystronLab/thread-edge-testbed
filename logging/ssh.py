import paramiko
import threading
import json
import pprint
import os

# List of Raspberry Pi IP addresses or hostnames and their login credentials
raspberry_pis = [
    {"host": "rpi5-1", "username": "pi", "password": "systron"},
    {"host": "rpi5-2", "username": "pi", "password": "systron"},
    {"host": "rpi5-3", "username": "pi", "password": "systron"},
    {"host": "rpi5-4", "username": "pi", "password": "systron"},
    {"host": "rpi5-5", "username": "pi", "password": "systron"},
]

# Define the local path to `ssh-code.py` in the same directory as this main script
local_script_path = os.path.join(os.path.dirname(__file__), 'ssh-code.py')

# Function to SSH into a Raspberry Pi, upload `ssh-code.py`, and execute it
def run_remote_code(pi_info, results):
    try:
        # Set up SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the Raspberry Pi
        ssh.connect(pi_info['host'], username=pi_info['username'], password=pi_info['password'])
        print(f"Connected to {pi_info['host']}")

        # Upload the Python script to the Pi
        sftp = ssh.open_sftp()
        remote_script_path = '/home/pi/ssh-code.py'  # Path on the Pi to store the script
        sftp.put(local_script_path, remote_script_path)
        sftp.close()

        # Run the uploaded script and capture output
        stdin, stdout, stderr = ssh.exec_command(f"python3 {remote_script_path}")

        # Fetch the output and error
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        # Print output for debugging purposes
        print(f"\nRaw output from {pi_info['host']}:\n{output}")

        if error:
            print(f"\nError from {pi_info['host']}:\n{error}")
        else:
            try:
                # Attempt to parse the JSON output
                data = json.loads(output)
                results[pi_info['host']] = data  # Store result in the shared dictionary
            except json.JSONDecodeError as e:
                print(f"JSON parsing error from {pi_info['host']}: {e}")
                print(f"Output that caused error:\n{output}")

    except Exception as e:
        print(f"Failed to connect to {pi_info['host']}: {e}")
    finally:
        ssh.close()

# Dictionary to store results from each Pi
results = {}

# Create a thread for each Raspberry Pi
threads = []
for pi in raspberry_pis:
    thread = threading.Thread(target=run_remote_code, args=(pi, results))
    threads.append(thread)
    thread.start()  # Start each thread

# Wait for all threads to complete
for thread in threads:
    thread.join()

# Print results from each Pi
print("\n")
pprint.pprint(results)
