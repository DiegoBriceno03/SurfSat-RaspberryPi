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
print("Oscilloscope Data Visualizer")
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
# each line as string split on comma delimiter to 
# generate two dimensional list. First index chooses
# row and second index chooses column.
data_str = []
with open(filename, 'rt') as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		data_str.append(row)

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
# associated index so most dominant frequency can be determined:
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
#plt.plot(f, abs(fftf), label="Filtered")
#plt.xlim(0,1e6)
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