# Pulsed Langmuir Probe Board

# 15-pin Micro-D Board Pinout
# PIN	Signal	Type	Description     Comments

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

# science - science mode - single waveform - swept bias - continuous - slow: binary(11100000) - hex(E0)
# science - science mode - single waveform - swept bias - continuous - fast: binary(11100001) - hex(E1)
# science - science mode - single waveform - swept bias - pulsed     - slow: binary(11100010) - hex(E2)
# science - science mode - single waveform - swept bias - pulsed     - fast: binary(11100011) - hex(E3)
# science - science mode - single waveform - fixed bias - continuous - slow: binary(11100100) - hex(E4)
# science - science mode - single waveform - fixed bias - continuous - fast: binary(11100101) - hex(E5)
# science - science mode - single waveform - fixed bias - pulsed     - slow: binary(11100110) - hex(E6)
# science - science mode - single waveform - fixed bias - pulsed     - fast: binary(11100111) - hex(E7)
# idle    - science mode - single waveform - fixed bias - continuous - fast: binary(01100101) - hex(65)

import sys
import serial
import RPi.GPIO as GPIO
import time

# a common class for all PLP board actions
class LangmuirProbe:

	def __init__(self, enable, status, reset, command, idle):
		self.enable = enable
		self.status = status
		self.reset  = reset
		self.command = command
		self.idle = idle
		self.bowl_of_serial()
		self.setup()

	#define serial (UART) and open port
	def bowl_of_serial(self):
		self.ser = serial.Serial(
			port="/dev/serial0",
			baudrate = 115200,
			parity = serial.PARITY_NONE,
			stopbits = serial.STOPBITS_ONE,
			bytesize = serial.EIGHTBITS,
			timeout = None
		)
		if not self.ser.is_open:
			#assumes board is NOT yet powered on
			sys.exit(1)

	#set mode on board to BOARD and setup pins
	def setup(self):
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.enable, GPIO.OUT)
		GPIO.setup(self.status, GPIO.IN)
		GPIO.setup(self.reset , GPIO.OUT)

	#helper function for other methods
	def disable_board(self):
		GPIO.output(self.enable, GPIO.LOW)

	#reset the FPGA and enable the board
	def reset_and_enable(self):
		GPIO.output(self.reset , GPIO.LOW)
		GPIO.output(self.reset , GPIO.HIGH)
		self.disable_board()
		GPIO.output(self.enable, GPIO.HIGH)

	#check status pin; if bad status, quit
	def check_status(self):
		#return true [3.3V] or false [0V]
		return (GPIO.input(self.status) == GPIO.HIGH)

	def write_command_byte(self):
		self.ser.write(self.command)

	def write_idle_byte(self):
		self.ser.write(self.idle)

	def clean_and_disable(self):
		self.disable_board()
		GPIO.cleanup()

if __name__ == "__main__":

	#label pins on py
	LP_ENABLE_PIN = 13
	LP_STATUS_PIN = 16
	LP_RESET_PIN = 11
	LP_CMD_BYTE = b'\xE0'
	LP_IDLE_BYTE = b'\x65'
	saveFile = open('data.txt','w')

	#create object
	myPLPboard = LangmuirProbe(LP_ENABLE_PIN, LP_STATUS_PIN, LP_RESET_PIN, LP_CMD_BYTE, LP_IDLE_BYTE)

	#run functions and receive data
	myPLPboard.reset_and_enable()

	# maybe make while not if status is active low
	while myPLPboard.check_status():
		# PLP command bytes - send once to START collecting data - send again to STOP collecting data
		myPLPboard.write_command_byte()
		garbage_value = ser.read(4)
		try:
			data = ser.read(4)
			current = data[2] << 8 | data[3]
			voltage = data[0] << 8 | data[1]
			datastr = "{0:.6f}, {1:x}, {2:x}\n".format(runtime, voltage, current)
			if data is not b'':
				saveFile.write(datastr)
		except KeyboardInterrupt:
			break

	saveFile.close()
	# PLP Command Byte - SECOND time sending the byte - STOP collecting continuous  data
	myPLPboard.write_idle_byte()
	myPLPboard.clean_and_disable()
