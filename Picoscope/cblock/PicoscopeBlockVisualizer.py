import os
import sys
import csv
import numpy as np
import matplotlib.pyplot as plt
import pprint as pp

# Look in current working directory for files 
# ending with '.txt' and add them to a list:
files = []
for file in os.listdir("."):
    if file.endswith(".txt"):
        files.append(file)

# Print a menu with an enumerated list of 
# filenames detected and stored previously:
print()
print("Picoscope Data Visualizer")
print()
print("Choose number of file to parse or enter anything else to exit.")
print()
print(" 0) Exit program")
for i, file in enumerate(files):
	print(" "+str(i+1)+")", file)
print()

# Accept input from user and attempt to cast 
# the string into an integer. If it fails, set 
# the input to zero (option to exit program):
try: fi = int(input("Enter selection: "))
except: fi = 0

# If user enters any value not listed in the 
# menu, set the input to zero (exit program):
if fi > len(files) or fi < 0: fi = 0

# If the user input is null, exit the program.
# If the user input is valid, decrement it to
# convert to zero indexing for future use:
if fi is 0:
	print("Terminating program")
	sys.exit(0)
else: fi -= 1

# Extract filename chosen by user from files list:
filename = files[fi]
print("Selected", filename)
print()

data_str = []
with open(filename, 'rt') as csvfile:
	reader = csv.reader(csvfile)
	# Skip header information
	for i in range(6): next(reader)
	# Remove spaces and commas
	for row in reader:
		data_str.append(sum([item.split() for item in row], []))

# dictionary of {t:  {'ChX': {'ADC': (Min, Max), 'mV': (Min, Max)}}}

data_dict = {}
for r in data_str:
	data_dict[int(r[0])] = {
		r[ 1]: {'ADC': (int(r[ 5]), int(r[ 2])), 'mV': (int(r[ 7][:-2]), int(r[ 4][:-2]))},
		r[ 8]: {'ADC': (int(r[12]), int(r[ 9])), 'mV': (int(r[14][:-2]), int(r[11][:-2]))},
		r[15]: {'ADC': (int(r[19]), int(r[16])), 'mV': (int(r[21][:-2]), int(r[18][:-2]))},
		r[22]: {'ADC': (int(r[26]), int(r[23])), 'mV': (int(r[28][:-2]), int(r[25][:-2]))}	
	}

T = []
V = [[],[],[],[]]
for t, d in sorted(data_dict.items()):
	T.append(t)
	V[0].append(d['ChA']['mV'][1])
	V[1].append(d['ChB']['mV'][1])
	V[2].append(d['ChC']['mV'][1])
	V[3].append(d['ChD']['mV'][1])

plt.plot(T, V[0], label="Channel A")
plt.plot(T, V[1], label="Channel B")
plt.plot(T, V[2], label="Channel C")
plt.plot(T, V[3], label="Channel D")
plt.title("PicoScope Visualizer")
plt.xlabel("Time (ns)")
plt.ylabel("Voltage (mV)")
plt.xlim([0,T[-1]])
plt.legend()
plt.show()
	
sys.exit(0)

# The oscilloscope stores header information in the first 
# three columns of each row (row[0:3]). The data is stored 
# in the remaining columns of each row (row[3:]). Headers 
# are stored as a dictionary {"Name": ["Value", "Unit"]}
# with null rows removed. Data are converted to floating
# point values from strings. If these steps fail, the file 
# selected is probably the wrong format, so program exits.
headers = {}
data_flt = []
try:
	for row in data_str:
		if row[0]: headers[row[0]] = row[1:3]
		data_flt.append([float(v) for v in row[3:]])
except IndexError:
	print("Invalid file format!")
	print("Terminating program")
	sys.exit(1)

print("Detected headers:")
pp.pprint(headers)


# Data was parsed as a list of ordered pairs of time and 
# voltage, but to work with the data, it must be transposed 
# into two separate lists of time and voltage:
#   [[t1, v1],  ->  [[t1, t2],
#    [t2, v2]]       [v1, v2]]
# Zip makes quick work of this. Afterwards time is at index 
# 0 and voltage is at index 1. These two lists are then 
# converted to NumPy arrays so that FFT can be computed:
d = list(zip(*data_flt))
t = np.array(d[0])
sr = np.array(d[1])

# Compute the real FFT of the signal data and generate 
# frequency data from the time data given the sample interval
# returned in the headers of the selected file:
print()
print("Computing fast Fourier transform ...")
fftr = np.fft.rfft(sr)
f = np.fft.rfftfreq(t.shape[-1], float(headers["Sample Interval"][0]))

# Do a very crude peak detection by selecting the maximum 
# value in the FFT array. Map this maximum value back to the
# associated index so most dominant frequency can be determined.
# Remove first as last elements to avoid false detection:
i = np.argmax(abs(fftr[1:-1])) + 1
print("Primary peak detected:", i, f[i], abs(fftr)[i])

# Select a region around the dominant frequency and zero out the
# contributions from all higher frequencies to remove noise:
print("Removing noise from signal ...")
maxi = 2*i
print("Threshold frequency:", f[maxi])
fftf = np.copy(fftr)
fftf[maxi:] = 0

# Compute the inverse FFT to convert from frequency domain to 
# time domain after removing contributions to the signal from noise:
print("Computing inverse fast Fourier transform ...")
sf = np.fft.irfft(fftf)

# Create plot comparing raw and filtered FFT data:
print("Displaying signals and transforms ...")
plt.figure(1)
plt.title("Fast Fourier Transform")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.plot(f, abs(fftr), label="Raw")
plt.plot(f, abs(fftf), label="Filtered")
plt.legend()

# Create plot comparing raw and filtered signal data:
plt.figure(2)
plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
plt.title("Scope Signals")
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.plot(t, sr, label="Raw")
plt.plot(t, sf, label="Filtered")
plt.legend()

# Display all plots:
plt.show()