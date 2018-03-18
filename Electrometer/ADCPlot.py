import os, glob
import matplotlib.pyplot as plt

T1 = []
C1 = []
T2 = []
C2 = []
T3 = []
C3 = []
T4 = []
C4 = []

filename = max(glob.glob('data/*'), key=os.path.getctime)
with open(filename, 'r') as f:
	for line in f:
		t, c, vr, vc = line.split(', ')
		if c == '0':
			T1.append(float(t))
			C1.append(float(vc))
		elif c == '1':
			T2.append(float(t))
			C2.append(float(vc))
		elif c == '2':
			T3.append(float(t))
			C3.append(float(vc))
		elif c == '3':
			T4.append(float(t))
			C4.append(float(vc))

plt.figure(1)
plt.title("Electrometer Data")
plt.xlabel("Time (us)")
plt.ylabel("Voltage (V)")
plt.plot(T1, C1, label="Channel 1")
plt.plot(T2, C2, label="Channel 2")
plt.plot(T3, C3, label="Channel 3")
plt.plot(T4, C4, label="Channel 4")
plt.legend()
plt.savefig('data.png', dpi=200)
