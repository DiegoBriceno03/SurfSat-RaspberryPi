import sys
import time
import math

filename = 'testdata.txt'
samples = 1024

with open(filename, 'w') as fh:
	fh.write("System: %s\n" % "Picoscope")
	fh.write("Status: %d\n" % 0)
	fh.write("Timestamp: %d\n" % (1e9*time.time()))
	fh.write("Timestep Units: %d\n" % 1) 
	fh.write("Timestep: %d\n" % 4)
	fh.write("Trigger: %d\n" % 2)
	fh.write("Channel A, Channel B, Channel C, Channel D\n")
	for i in range(samples):
		for j in range(4):
			fh.write("%d" % int(0x7F*math.sin(20*2*math.pi*i/samples + (j-2)*math.pi/4.0)+0x7F))
			if j % 4 == 3: fh.write("\n")
			else: fh.write(", ")
