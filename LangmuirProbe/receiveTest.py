import sys, serial, time

# Open serial port object with specified parameters
ser = serial.Serial(port = "/dev/serial0", baudrate = 115200, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = 0)

# Check if port is open and, if not, exit
if ser.is_open:
    print("Opened port " + ser.port)
else:
    print("Error opening port " + ser.port)
    sys.exit(1)

# Take user input and encode string as bytes before transmit
#cmd = input("Serial command: ")
#ser.write(cmd.encode())

# Read one line of serial data and decode bytes to string
while True:
	data = ser.readline()
	print(["{0:x}".format(x) for x in data[:-1]])
	time.sleep(0.01)
