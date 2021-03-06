print("Loading matplotlib into RAM...")
import matplotlib.pyplot as plt
print("Opening 'data.txt'...")

runtime = []
current = []
voltage = []
with open('data.txt', 'r') as f:
	for line in f:
		t, v, c = line.split(', ')
		runtime.append(float(t))
		current.append(int(c, 16))
		voltage.append(int(v, 16))

print("Plotting voltage and current vs time...")
plt.figure(1)
plt.title("Langmuir Probe Data")
plt.xlabel("Time (s)")
plt.plot(runtime, voltage, label="Voltage (arb)")
plt.plot(runtime, current, label="Current (arb)")
plt.legend()
plt.savefig('CVvT.png', dpi=200)

print("Plotting current vs voltage...")
plt.figure(2)
plt.title("Langmuir Probe IV Curve")
plt.xlabel("Voltage (arb)")
plt.ylabel("Current (arb)")
plt.plot(voltage, current, '.')
plt.savefig('CvV.png', dpi=200)
