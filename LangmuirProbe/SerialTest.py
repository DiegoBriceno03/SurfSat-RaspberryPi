import sys, serial

# Open serial port object with specified parameters
ser = serial.Serial(port = "/dev/serial0", baudrate = 115200, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = 0)

# Check if port is open and, if not, exit
if ser.is_open:
    print("Opened port " + ser.port)
else:
    print("Error opening port " + ser.port)
    sys.exit(1)

# Take user input and encode string as bytes before transmit
cmd = input("Serial command: ")
ser.write(bytes(cmd, encoding='UTF-8'))

# Read one line of serial data and decode bytes to string
data = ser.readline()
print(data)
