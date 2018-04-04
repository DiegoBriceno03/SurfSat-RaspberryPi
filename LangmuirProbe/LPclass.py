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

class LangmuirProbe:

	def define_constants(self):
		self.PLP_SPEED_SLOW = 0x00
		self.PLP_SPEED_FAST = 0x01

		self.PLP_OPER_CONTIN = 0x00 << 1
		self.PLP_OPER_PULSED = 0x01 << 1

		self.PLP_BIAS_SWEPT = 0x00 << 2
		self.PLP_BIAS_FIXED = 0x01 << 2

		self.PLP_MODE_IDLE = 0x00 << 7
		self.PLP_MODE_SCI  = 0x01 << 7

	def __init__(self, pin_reset, pin_enable, pin_status):
		self.define_constants()
		self.pin_reset = pin_reset
		self.pin_enable = pin_enable
		self.pin_status = pin_status
		self.setup_gpio()
		self.reset()
		self.enable()
		self.ser_init()

	def setup_gpio(self):
		print("Initializing GPIO...")
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.pin_reset, GPIO.OUT)
		GPIO.setup(self.pin_enable, GPIO.OUT)
		GPIO.setup(self.pin_status, GPIO.IN)

	def reset(self):
		print("Resetting FPGA...")
		GPIO.output(self.pin_reset, GPIO.LOW)
		time.sleep(0.1)
		GPIO.output(self.pin_reset, GPIO.HIGH)
		time.sleep(0.1)

	def enable(self):
		print("Enabling board...")
		GPIO.output(self.pin_enable, GPIO.HIGH)
		time.sleep(0.1)

	def disable(self):
		print("Disabling board...")
		GPIO.output(self.pin_enable, GPIO.LOW)
		time.sleep(0.1)

	def ser_init(self):
		print("Initializing serial port...")
		self.ser = serial.Serial(
			port="/dev/serial0",
			baudrate = 115200,
			parity = serial.PARITY_NONE,
			stopbits = serial.STOPBITS_ONE,
			bytesize = serial.EIGHTBITS,
			timeout = None
		)
		if not self.ser.is_open:
			print("Failed to open serial port!")
			sys.exit(1)

	def send_command_byte(self, command_byte):
		command_byte = command_byte | 0x60
		print("Sending command byte 0x%02X..." % command_byte)
		command_byte = bytes([command_byte])
		self.ser.write(command_byte)

	def read_data(self):
		data = self.ser.read(4)
		current = data[2] << 8 | data[3]
		voltage = data[0] << 8 | data[1]
		return (voltage, current)
		
	def check_status(self):
		# Check LP_STATUS_PIN; if bad status, abort
		if GPIO.input(self.pin_status) == GPIO.HIGH:
			print("Status check failed, disabling board!")
			self.disable()
			return False
		else: return True

if __name__ == "__main__":

	LP_RESET_PIN = 11
	LP_ENABLE_PIN = 13
	LP_STATUS_PIN = 16

	plp = LangmuirProbe(LP_RESET_PIN, LP_ENABLE_PIN, LP_STATUS_PIN)

	filename = 'data.txt'
	saveFile = open(filename, 'w')
	print("Saving data to '%s'..." % filename)

	plp.send_command_byte(plp.PLP_MODE_SCI | plp.PLP_BIAS_SWEPT | plp.PLP_OPER_PULSED | plp.PLP_SPEED_SLOW)

	totalruntime = 1
	print("Taking data for %d seconds..." % totalruntime)
	starttime = time.time()
	runtime = 0
	while runtime < totalruntime and plp.check_status():
		try:
			runtime = time.time() - starttime
			voltage, current = plp.read_data()
			datastr = "{0:.6f}, {1:x}, {2:x}\n".format(runtime, voltage, current)
			saveFile.write(datastr)
		except KeyboardInterrupt:
			break

	saveFile.close()

	plp.send_command_byte(plp.PLP_MODE_IDLE)

	plp.disable()
	GPIO.cleanup()
