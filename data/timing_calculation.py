import re
from datetime import datetime

# Function to convert timestamps in [HH:MM:SS.SSS,mmm] format to total milliseconds
def timestamp_to_ms(timestamp):
    timestamp = timestamp.split(',')[0]  # Keeps only HH:MM:SS.SSS
    time_obj = datetime.strptime(timestamp, "%H:%M:%S.%f")
    total_ms = (time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second) * 1000 + int(time_obj.microsecond / 1000)
    return total_ms

# Initialize a list to store the time differences
differences = []

# Read the file
with open("data/ttyACM9.txt", "r") as file:
    lines = file.readlines()
    i = 0
    while i < len(lines) - 1:
        # Extract timestamp from the "jamming detected" line
        if "Jamming detected" in lines[i]:
            timestamp_match = re.search(r"\[(\d{2}:\d{2}:\d{2}\.\d{3},\d{3})\]", lines[i])
            if timestamp_match:
                jamming_timestamp = timestamp_match.group(1)
                jamming_ms = timestamp_to_ms(jamming_timestamp)

                # Find the next "Channel Hop Time" line
                i += 1
                while i < len(lines) and "Channel Hop Time" not in lines[i]:
                    i += 1

                # If a "Channel Hop Time" line is found, calculate the difference
                if i < len(lines):
                    hop_timestamp_match = re.search(r"\[(\d{2}:\d{2}:\d{2}\.\d{3},\d{3})\]", lines[i])
                    if hop_timestamp_match:
                        hop_timestamp = hop_timestamp_match.group(1)
                        hop_ms = timestamp_to_ms(hop_timestamp)

                        # Calculate and store the difference
                        differences.append(hop_ms - jamming_ms)

        i += 1

# Calculate the average difference
if differences:
    average_difference = sum(differences) / len(differences)
    print(f"Average time difference between jamming detection and channel hop: {average_difference} ms")
else:
    print("No valid pairs of jamming and hop timestamps found.")
