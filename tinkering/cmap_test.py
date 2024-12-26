import matplotlib.pyplot as plt
import numpy as np


def get_jet_rgb(value):
    return np.array(plt.cm.jet(value)[:3])


x = np.linspace(0, 1, 10000)

y = np.array([get_jet_rgb(xx) for xx in x])

# Plot the RGB components
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.plot(x, y[:, 0], "r", label="Red")
plt.plot(x, y[:, 1], "g", label="Green")
plt.plot(x, y[:, 2], "b", label="Blue")
plt.legend()
plt.xlabel("x (Normalized)")
plt.ylabel("RGB Intensity")
plt.title("Jet Colormap RGB Components")

plt.subplot(1, 2, 2)
gradient = np.linspace(0, 1, 256).reshape(1, -1)
plt.imshow(gradient, aspect="auto", cmap="jet")
plt.axis("off")
plt.title("Jet Colormap")
gg = y[:, 1] - (y[:, 0] + y[:, 2])
print(gg.shape)
# Find the max green value and corresponding x
max_green = np.max(gg)
max_green_index = np.argmax(gg)
max_green_x = x[max_green_index]

# Print the results
print(f"Max Green Value: {max_green}")
print(f"x value for Max Green: {max_green_x}")

# Show the combined plot
plt.tight_layout()
plt.show()
