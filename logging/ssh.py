import paramiko
import threading

# List of Raspberry Pi IP addresses or hostnames and their login credentials
raspberry_pis = [
    {"host": "rpi5-1", "username": "pi", "password": "systron"},
    {"host": "rpi5-2", "username": "pi", "password": "systron"},
    {"host": "rpi5-3", "username": "pi", "password": "systron"},
    {"host": "rpi5-4", "username": "pi", "password": "systron"},
    {"host": "rpi5-5", "username": "pi", "password": "systron"},
]

# The Python code you want to execute on each Raspberry Pi
remote_code = """
import platform
print("Running on:", platform.node())
print("Hello from Raspberry Pi!")
"""

# Function to SSH into a Raspberry Pi and execute the code
def run_remote_code(pi_info):
    try:
        # Set up SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the Raspberry Pi
        ssh.connect(pi_info['host'], username=pi_info['username'], password=pi_info['password'])
        print(f"Connected to {pi_info['host']}")

        # Run the Python code remotely
        stdin, stdout, stderr = ssh.exec_command(f"python3 -c '{remote_code}'")
        
        # Fetch and print the output and errors
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        print(f"Output from {pi_info['host']}:\n{output}")
        if error:
            print(f"Error from {pi_info['host']}:\n{error}")

    except Exception as e:
        print(f"Failed to connect to {pi_info['host']}: {e}")
    finally:
        ssh.close()

# Create a thread for each Raspberry Pi
threads = []
for pi in raspberry_pis:
    thread = threading.Thread(target=run_remote_code, args=(pi,))
    threads.append(thread)
    thread.start()  # Start each thread

# Wait for all threads to complete
for thread in threads:
    thread.join()