# SurfSat Pulsed Langmuir Probe Board


# Pulsed Langmuir Probe 15-pin Micro-D Pinout
# PIN	Signal	Type	Description	Comments

# 1		VIN		PWR		+6-28V Supply	-
# 2		VIN		PWR		+6-28V Supply	-
# 3		VBUS	Input	+5V				-
# 4		USB_P	I/O D.	USB Data +		-
# 5		USB_N	I/O D.	USB Data -		-
# 6		RESET	Input	Reset FPGA		3.3 V LVCMOS, active low
# 7		TxD		Output	COM1 Transmit	3.3 V LVCMOS, 4 mA drive, UART
# 8		RxD		Input	COM1 Receive	3.3 V LVCMOS, 4 mA drive, UART
# 9		ENABLE	Input	Board POWER		3.3 V, active high
# 10	GND		GND		GND Reference	-
# 11	GND		GND		GND Reference	-
# 12	GND		GND		GND Reference	-
# 13	GND		GND		GND Reference	-
# 14	SPARE	I/O		Spare GPIO		3.3 V LVCMOS, 4 mA drive
# 15	STATUS	Output	Data Valid		3.3 V LVCMOS, 4 mA drive

import sys
import serial
import RPi.GPIO as GPIO
import time
import binascii

LP_RESET_PIN = 11
LP_ENABLE_PIN = 13
LP_STATUS_PIN = 16

GPIO.setmode(GPIO.BOARD)

GPIO.setup(LP_RESET_PIN, GPIO.OUT)
GPIO.setup(LP_ENABLE_PIN, GPIO.OUT)
GPIO.setup(LP_STATUS_PIN, GPIO.IN)

print("Resetting FPGA...")
GPIO.output(LP_RESET_PIN, GPIO.LOW)
time.sleep(0.2)
GPIO.output(LP_RESET_PIN, GPIO.HIGH)
time.sleep(0.2)
print("Enabling board...")
GPIO.output(LP_ENABLE_PIN, GPIO.HIGH)
time.sleep(0.2)

# Defining serial
ser = serial.Serial(

	port="/dev/serial0",
	baudrate = 115200,
	parity = serial.PARITY_NONE,
	stopbits = serial.STOPBITS_ONE,
	bytesize = serial.EIGHTBITS,
	timeout = None

	)


# File.txt to save data
saveFile = open('data.txt','w')


# Abort program if serial port does not open
if not ser.is_open:
	#print("Failed to open serial port")
	sys.exit(1)


# Check LP_STATUS_PIN;  if bad status, abort
#if GPIO.input(LP_STATUS_PIN) == ???
#	print("Status check failed, disabling board and aborting program")
#	sys.stdout.flush()
#	GPIO.output(LP_ENABLE_PIN, GPIO.LOW)
#	sys.exit(1)


# PLP Command Byte - FIRST time sending the byte - START collecting continuous data
# science - science mode - single waveform - fixed bias - continuous - fast
# binary(11100101) - hex(E5)
# science - science mode - single waveform - swept bias - continuous - fast
# binary(11100001) - hex(E1)
# science - science mode - single waveform - fixed bias - continuous - slow
# binary(11100100) - hex(E4)
# science - science mode - single waveform - swept bias - continuous - slow
# binary(11100000) - hex(E0)
commandByte = b'\xE0'
print(commandByte)
ser.write(commandByte)

print("Saving data to \"data.txt\"")

# First four bytes should be header, but is garbage, so ignore.
header = ser.read(4)

starttime = time.time()
runtime = 0
while runtime < 1:
	try:
		runtime = time.time() - starttime
		data = ser.read(4)
		current = data[2] << 8 | data[3]
		voltage = data[0] << 8 | data[1]
		datastr = "{0:.6f}, {1:x}, {2:x}\n".format(runtime, voltage, current)
		if data is not b'':
			sys.stdout.write(datastr)
		#save data to file - must cast str() to read list into file, use NO str() if using print()
			saveFile.write(datastr)
	except KeyboardInterrupt:
		break

saveFile.close()

# PLP Command Byte - SECOND time sending the byte - STOP collecting continuous  data
# idle - science mode - single waveform - fixed bias - continuous - fast
# binary(01100101) - hex(65) - decimal (101)

#idleCommandByte = bytes([0x65])
idleCommandByte = b'\x65'
ser.write(idleCommandByte)

print("Disabling board...")
GPIO.output(LP_ENABLE_PIN, GPIO.LOW)

GPIO.cleanup()

