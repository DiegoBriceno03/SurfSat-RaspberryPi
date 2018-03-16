import matplotlib.pyplot as plt

current = []
voltage = []
with open('data.txt', 'r') as f:
	for line in f:
		c, v = line.split(', ')
		current.append(int(c, 16))
		voltage.append(int(v, 16))

plt.plot(range(len(current)), current, label="Current")
plt.plot(range(len(voltage)), voltage, label="Voltage")
plt.legend()
plt.savefig('data.png')
plt.show()
