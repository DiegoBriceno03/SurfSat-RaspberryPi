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

# Bit 0 determines data collection speed
# 0: Slow
# 1: Fast
SPEED_SLOW = 0x00 << 0
SPEED_FAST = 0x01 << 0

# Bit 1 determines operational mode
# 0: Continuous
# 1: Pulsed
OPER_CONTINUOUS = 0x00 << 1
OPER_PULSED     = 0x01 << 1

# Bit 2 determines bias
# 0: Swept
# 1: Fixed
BIAS_SWEPT = 0x00 << 2
BIAS_FIXED = 0x01 << 2

# Bits 3 and 4 determine waveform type
# 00: Single
# 01: Pseudo-absolute
# 10: Pseudo-absolute, pulsed
# 11: Tech demo
WAVE_SINGLE                 = 0x00 << 3
WAVE_PSEUDO_ABSOLUTE        = 0x01 << 3
WAVE_PSEUDO_ABSOLUTE_PULSED = 0x02 << 3
WAVE_TECH_DEMO              = 0x03 << 3

# Bits 5 and 6 determine calibration status
# 00: Calibration mode, 50 Kohm
# 01: Calibration mode, 50 Mohm
# 1X: Science mode
CALIB_50K  = 0x00 << 5
CALIB_50M  = 0x01 << 5
CALIB_NONE = 0x02 << 5

# Bit 7 determines mode
# 0: Idle
# 1: Science
MODE_IDLE    = 0x00 << 7
MODE_SCIENCE = 0x01 << 7

class LangmuirProbe:
	def __init__(self, pin_reset, pin_enable, pin_status):
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

	def close(self):
		GPIO.cleanup()
		self.ser.close()

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
		# Always set second MSB to avoid calibration mode
		command_byte = command_byte | 0x40
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
