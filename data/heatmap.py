import matplotlib.pyplot as plt
import numpy as np

rssi_map = np.array([[-46, -48, -43, -41, -42], 
                     [-37, -38, -35, -36, -33], 
                     [-34, -36, -35, -33, -32], 
                     [-40, -37, -37, -36, -35]])

fig, ax = plt.subplots()
im = ax.imshow(rssi_map, interpolation="quadric")

plt.show()