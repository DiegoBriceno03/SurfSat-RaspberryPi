import sys

T = []
I = []
L = []
N = []
D = []
mismatch = 0
print("Parsing 'data.txt' ...")
with open('data.txt', 'r') as f:
	for line in f:
		values = line.split(', ')
		t = int(values[0], 16)
		i = int(values[1], 16)
		l = int(values[2], 16)
		n = int(values[3], 16)
		if n != len(values) - 4:
			print("Sample quantity mismatch detected at %08X" % t)
			mismatch += 1
		if n == 0:
			T.append(t)
			I.append(i)
			L.append(l)
			N.append(n)
			D.append(None)
		else:
			T.extend([int(values[0], 16)]*n)
			I.extend([int(values[1], 16)]*n)
			L.extend([int(values[2], 16)]*n)
			N.extend([int(values[3], 16)]*n)
			d = []
			for i in range(4, len(values)):
				d.append(int(values[i], 16))
			D.extend(d)

overflows = 0
discontin = 0
for i in range(len(T)):
	if I[i] == 0x06:
		try: sys.stdout.write("RX error causing %d missed samples detected: " % (D[i+1] - D[i-1] - 1))
		except TypeError: sys.stdout.write("RX error causing unknown missed samples detected: ")
		overflows += 1
	if I[i] != 0x0C and I[i] != 0x04 and I[i] != 0x01:
		if D[i] is None:
			print("0x%08X 0x%02X 0x%02X 0x%02X None" % (T[i], I[i], L[i], N[i]))
		else:
			print("0x%08X 0x%02X 0x%02X 0x%02X 0x%08X" % (T[i], I[i], L[i], N[i], D[i]))
	if i > 0:
		if D[i] is None or D[i-1] is None: pass
		elif (D[i] - D[i-1]) != 1:
			print("Discontinuity of %d samples with unknown cause detected at 0x%08X!" % (D[i] - D[i-1] - 1, T[i]))
			discontin += 1

print()
print("Packet mismatch: %d" % mismatch)
print("Receive errors:  %d" % overflows)
print("Discontinuities: %d" % discontin)
