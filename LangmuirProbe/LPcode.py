#SurfSat Pulsed Langmuir Probe Board


#Pulsed Langmuir Probe 15-pin Micro-D Pinout
#PIN	Signal	Type	Description	Comments

#1	VIN	PWR	+6-28V Supply	-
#2	VIN	PWR	+6-28V Supply	-
#3	VBUS	Input	+5V		-
#4	USB_P	I/O D.	USB Data +	-
#5	USB_N	I/O D.	USB Data -	-
#6	RESET	Input	Reset FPGA	3.3 V LVCMOS, active low
#7	TxD	Output	COM1 Transmit	3.3 V LVCMOS, 4 mA drive, UART
#8	RxD	Input	COM1 Receive	3.3 V LVCMOS, 4 mA drive, UART
#9	ENABLE	Input	Board POWER	3.3 V, active high
#10	GND	GND	GND Reference	-
#11	GND	GND	GND Reference	-
#12	GND	GND	GND Reference	-
#13	GND	GND	GND Reference	-
#14	SPARE	I/O	Spare GPIO	3.3 V LVCMOS, 4 mA drive
#15	STATUS	Output	Data Valid	3.3 V LVCMOS, 4 mA drive

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
time.sleep(1.0)
GPIO.output(LP_RESET_PIN, GPIO.HIGH)
time.sleep(1.0)
print("Enabling board...")
GPIO.output(LP_ENABLE_PIN, GPIO.HIGH)
time.sleep(1.0)

#defining serial characteristics
ser = serial.Serial(

	port="/dev/serial0",
	baudrate = 115200,
	parity = serial.PARITY_NONE,
	stopbits = serial.STOPBITS_ONE,
	bytesize = serial.EIGHTBITS,
	timeout = 0

	)

saveFile = open('data.txt','w')
#abort if serial connect fails
if not ser.is_open:
	sys.exit(1)
	#print('failed to open serial port')

#RxD LP goes to 8 on Py

#checking status pin - if bad status, turn off and quit program
#GPIO.setup(LP_STATUS_PIN, GPIO.IN)
#if GPIO.input(LP_STATUS_PIN) == ???
#	print("Status check failed, powering off")
#	sys.stdout.flush()
#	GPIO.output(LP_ENABLE_PIN, GPIO.LOW)
#	sys.exit(1)

#PLP Command Byte - first time sending - START collecting continuous data
#science - science mode - single waveform - fixed bias - continuous - fast
#binary(11100101) - hex(E5) - decimal(229)

#commandByte = bytes([0xE5])
commandByte = b'\xE5'
print(commandByte)
ser.write(commandByte)

#receive data for 3 seconds
#t_end = time.time() + 60 / 20
print("Saving data to \"data.txt\"")
while True:
	try:
		data = ser.read(4)
		if data is not b'':
			print(data)
		#save data to file - must cast str() to read list into file, use NO str() if using print()
		saveFile.write(str(["{0:x}\n".format(x) for x in data[:-1]]))
	except KeyboardInterrupt:
		break

saveFile.close()

#PLP Command Byte - second time sending - STOP collecting data
#idleCommandByte = b'01100101'
#idleCommandByte = bytes([0x65])
idleCommandByte = b'\x65'
ser.write(idleCommandByte)

print("Disabling board...")
GPIO.output(LP_ENABLE_PIN, GPIO.LOW)

GPIO.cleanup()
#some testing stuff
#cmd = input("Serial command: ")
#ser.write(cmd.encode())

#data = ser.readline()
#print(data.decode())
