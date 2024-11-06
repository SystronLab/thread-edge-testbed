import matplotlib.pyplot as plt
import numpy as np

bars = ["5 Devices", "10 Devices", "15 Devices", "19 Devices"]

# Data for each bar
leader = np.array([33669.75, 33533.0625, 34174.1875, 33556.125])
min_device = np.array([3020.4375, 2234.625, 3229.25, 1865.875])
max_device = np.array([14210.3125, 21570.5, 27208.4375, 30740.9375])

# Standard deviations for min_device and max_device
min_device_std = np.array([3336.343147, 2843.102308, 3261.599694, 1805.362044])
max_device_std = np.array([5059.438015, 12929.87513, 14049.71079, 14670.26481])  

# Indices for bar positions
ind = np.arange(len(bars))
width = 0.35

# Plot bars with error bars and caps
p1 = plt.bar(ind, leader, width, color='#d62728', label="Leader")
p2 = plt.bar(ind, min_device, width, bottom=leader, yerr=min_device_std, color='#1f77b4', label="Minimum Device Time", capsize=5)
p3 = plt.bar(ind, max_device, width, bottom=leader + min_device, yerr=max_device_std, color='#ff7f0e', label="Maximum Device Time", capsize=5)


# Labels and title
plt.ylabel("Time (ms)")
plt.title("Timing of Devices Connecting to Thread Network")
plt.xticks(ind, bars)
plt.yticks(np.arange(0, 90000, 5000))

# Legend
plt.legend()

# Show plot
plt.show()
