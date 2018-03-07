import os
import sys
import csv
import numpy as np
import matplotlib.pyplot as plt
import pprint as pp
from scipy.signal import argrelextrema

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

# Open the chosen file and use CSV reader to read 
# each line as string split on tab delimiter to 
# generate two dimensional list. First index chooses
# row and second index chooses column.
data_str = []
with open(filename, 'rt') as csvfile:
	reader = csv.reader(csvfile, delimiter="\t")
	for row in reader:
		data_str.append(row)
		
headers = []
data_flt = []
try:
	for i, row in enumerate(data_str):
		if i < 2: headers.append(row)
		elif i == 2: continue
		else: data_flt.append([float(v) for v in row])
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
t = np.array(d[0])*1e-9 # convert from ns to s
sr = np.array(d[1])

# Compute the real FFT of the signal data and generate 
# frequency data from the time data given the sample interval
# returned in the headers of the selected file:
print()
print("Computing fast Fourier transform ...")
fftr = np.fft.rfft(sr)
f = abs(np.fft.rfftfreq(t.shape[-1], np.mean(np.diff(t))))

# Better peak detection:
maxima = argrelextrema(fftr, np.greater)
z = sorted(list(zip(list(maxima[0]), [abs(v) for v in fftr[maxima]])), key=lambda x: x[1], reverse=True)

for i, v in enumerate(z[0:5]):
	print("Peak #" + str(i+1) + " detected: ", z[i][0], f[z[i][0]], z[i][1])

# Select a region around the dominant frequency and zero out the
# contributions from all higher frequencies to remove noise:
print("Removing noise from signal ...")
maxi = 2*z[i][0]
print("Threshold frequency:", f[maxi])
fftf = np.copy(fftr)
fftf[maxi:] = 0

# Compute the inverse FFT to convert from frequency domain to 
# time domain after removing contributions to the signal from noise:
print("Computing inverse fast Fourier transform ...")
sf = np.fft.irfft(fftf)

# Create plot comparing raw and filtered FFT data:
print("Displaying signals and transforms ...")
plt.figure(1, figsize=(20,11.25))
plt.title("Picoscope Fast Fourier Transform")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
for i in range(5):
	plt.text(f[z[i][0]], z[i][1], "{0:.1f}MHz".format(f[z[i][0]]*1e-6), bbox=dict(facecolor='red', alpha=0.5))
plt.plot(f, abs(fftr), label="Raw")
#plt.plot(f, abs(fftf), label="Filtered")
plt.xlim(0,f[5*z[i][0]])
plt.legend()
plt.savefig('FFT.png')

# Create plot comparing raw and filtered signal data:
plt.figure(2, figsize=(20,11.25))
plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
plt.title("Picoscope Signals")
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.plot(t, sr, label="Raw")
plt.plot(t, sf, label="Filtered")
plt.legend()
plt.savefig('Raw.png')

# Display all plots:
plt.show()