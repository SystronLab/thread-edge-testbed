import matplotlib.pyplot as plt
import numpy as np

# Define the timescale
time_before = -5000  # Time before 0 (milliseconds)
time_after = 5000   # Time after signal goes high at 29374.295 ms (milliseconds)
time_low = 0  # Time when signal goes low
time_high = 29374.295  # Time when signal goes high again
total_time = np.linspace(time_before, time_high + time_after, 500)

# Create the signal array: 1 before time_low (signal high), 0 at time_low, and 1 after time_high (signal high)
signal = np.where(total_time < time_low, 1,  # High before time 0
                  np.where(total_time < time_high, 0, 1))  # Low at time 0 and high after time 29374.295 ms

# Plot the step graph
plt.step(total_time, signal, where='post')

# Adding labels and title
plt.xlabel('Time (ms)')
plt.ylabel('Packet Rate')
plt.title('Average packet receiving under a jamming attack')

# Show grid
plt.grid(True)

# Display the plot
plt.show()
