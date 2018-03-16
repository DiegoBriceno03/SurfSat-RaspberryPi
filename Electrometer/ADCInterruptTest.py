import os
import sys
import math
import time
import smbus
import threading
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

DELAY = 0.1

# Create data directory if it does not exist
if os.path.exists('data'):
	if not os.path.isdir('data'):
		print('Data directory is file and not directory. Please fix!')
		sys.exit(1)
else:
	os.makedirs('data')

# Primary ADC with address 0x48, secondary ADC with address 0x49
# Addresses 0x48 (GND), 0x49 (VDD), 0x4A (SDA), 0x4B (SCL)
DEVICE_BUS = 1
DEVICE_INDEX = 0
DEVICE_ADDRS = [0x48, 0x49]
DEVICE_GPIOS = [24, 10]
DEVICE_ADDR = DEVICE_ADDRS[DEVICE_INDEX]
DEVICE_GPIO = DEVICE_GPIOS[DEVICE_INDEX]

print('Initializing gpio ...')
GPIO.setup(DEVICE_GPIO, GPIO.IN, GPIO.PUD_UP)

print('Initializing bus ...')
bus = smbus.SMBus(DEVICE_BUS)

# Address pointer register (P)
# 07:02  Reserved[5:0]  Always write 0
# 01:00  P[1:0]         Register address pointer
#                         0b00: Conversion register
#                         0b01: Configuration register
#                         0b10: Low threshold register
#                         0b11: High threshold register
REG_CONV = 0x00  # 0b00
REG_CONF = 0x01  # 0b01
REG_LOW  = 0x02  # 0b02
REG_HIGH = 0x03  # 0b03

# Configuration register
# 15     OS             Operational status or single-shot start
# 14:12  MUX[2:0]       Input multiplexer configuration
# 11:09  PGA[2:0]       Programmable gain amplifier configuration
# 08     MODE           Device operating mode
# 07:05  DR[2:0]        Data rate
# 04     COMP_MODE      Comparator mode
# 03     COMP_POL       Comparator polarity
# 02     COMP_LAT       Latching comparator
# 01:00  COMP_QUE[1:0]  Comparator queue

# CONF_OS: 0b0 No Effect, 0b1 Start Single Conversion
CONF_OS = 0x01 # 0b1

# CONF_MUX: 0b100 AIN0, 0b101 AIN1, 0b110 AIN2, 0b111 AIN3
CONF_MUX = (1 << 2) | 0x00 # 0b1XX

# CONF_PGA: 0b000 6.144V, 0b001 4.096V, 0b010 2.048V, 0b011 1.024V,
#           0b100 0.512V, 0b101 0.256V, 0b110 0.256V, 0b111 0.256V
CONF_PGA = 0x01 # 0b001

# CONF_MODE: 0b0 Continuous, 0b1 Single-shot
CONF_MODE = 0x01 # 0b1

# CONF_DR: 0b000   8 SPS, 0b001  16 SPS, 0b010  32 SPS, 0b011  64 SPS,
#          0b100 128 SPS, 0b101 250 SPS, 0b110 475 SPS, 0b111 860 SPS
CONF_DR = 0x07 # 0b111

# CONF_COMP_MODE: 0b0 Traditional, 0b1 Window
CONF_COMP_MODE = 0x00 # 0b0

# CONF_COMP_POL: 0b0 Active low, 0b1 Active high
CONF_COMP_POL = 0x00 # 0b0

# CONF_COMP_LAT: 0b0 Nonlatching, 0b1 Latching
CONF_COMP_LAT = 0x00 # 0b0

# CONF_COMP_QUE: 0b00 After 1, 0b01 After 2, 0b10 After 4, 0b11 Disabled
CONF_COMP_QUE = 0x00 # 0b00

# Store program start time as zero point for measurements:
inittime = time.time()

dataready = False
databuffer = {'Time': 0, 'C0': '', 'C1': '', 'C2': '', 'C3': '', 'Error': False}

failures = 0

def init():
	# Set Lo_thresh and Hi_thresh registers to enable conversion ready pin
	# Set most significant bit of Lo_thresh register to 0
	bus.write_i2c_block_data(DEVICE_ADDR, REG_LOW, [0x00, 0x00])
	# Set most significant bit of Hi_thresh register to 1
	bus.write_i2c_block_data(DEVICE_ADDR, REG_HIGH, [0x80, 0x00])

def sample():
	# Declare global storage variables:
	global dataready, databuffer, failures

	# Initialize countdown to next sample:
	threading.Timer(DELAY, sample).start()

	# Wait for buffer to be emptied:
	while dataready: pass

	# Clear error flag on data buffer:
	databuffer['Error'] = False

	# Record current sample time:
	databuffer['Time'] = time.time() - inittime

	# Cycle through each of the four ADC input channels in series:
	for channel in range(4):
		# Generate bits to connect multiplexer to correct channel and generate configuration bytes:
		CONF_MUX = (1 << 2) | channel # 0b1XX
		config = [(CONF_OS << 7) | (CONF_MUX << 4) | (CONF_PGA << 1) | CONF_MODE, (CONF_DR << 5) | (CONF_COMP_MODE << 4) | (CONF_COMP_POL << 3) | (CONF_COMP_LAT << 2) | CONF_COMP_QUE]

		# Write configuration bytes to chip, wait for conversion to take place, and read in conversion bytes:
		bus.write_i2c_block_data(DEVICE_ADDR, REG_CONF, config)

		# Wait for conversion to complete (either start based on signal from ADC or wait for timeout) and read in results:
		try:
			if GPIO.input(DEVICE_GPIO) == 0 or GPIO.wait_for_edge(DEVICE_GPIO, GPIO.FALLING, timeout=math.ceil(1000*(1/860.0+0.0001))) == DEVICE_GPIO: pass
			else:
				failures += 1
				databuffer['Error'] = True
				print('ADC not ready on channel ' + str(channel) + ', so waiting (' + str(failures) + ' total) ...')
		except RuntimeError:
			failures += 1
			databuffer['Error'] = True
			print('ADC not ready on channel ' + str(channel) + ' (' + str(failures) + ' total) ...')

		databuffer['C' + str(channel)] = bus.read_word_data(DEVICE_ADDR, REG_CONV)

	dataready = True

fh = open('data/' + str(int(inittime)) + '.txt', 'w')

init()
sample()

while True:
	try:
		time.sleep(0.01)
		if dataready:
			# Read off the buffer and let the thread know it is empty now:
			dataparse = databuffer
			dataready = False

			# Write elapsed time to file and stdout:
			datastr = 'Time: {0:.3f} s'.format(dataparse['Time'])
			fh.write(datastr)
			sys.stdout.write(datastr)
			for channel in range(4):
				# Swap order of bytes and convert out of two byte two's complement to integer length two's complement:
				datatc = dataparse['C' + str(channel)]
				datatc = ((datatc & 0xFF00) >> 8) | ((datatc & 0x00FF) << 8)
				data = -(datatc & 0x8000) | (datatc & 0x7FFF)

				# Write received data bytes and processed ADC values to file and stdout:
				# At 4.096 V PGA setting, one bin has a value of 125 uV (4.096/0x7FFF), so fourth decimal place is uncertain.
				# Since the ADC saves space for negative values as well, the single ended range is only 15 bits (therefore 0x7FFF bins).
				datastr = ', C' + str(channel) + ': 0x{0:04X} ({1:+.4f} V)'.format(datatc, data*4.096/0x7FFF)
				fh.write(datastr)
				sys.stdout.write(datastr)
			datastr = ' *\n' if dataparse['Error'] else '\n'
			fh.write(datastr)
			sys.stdout.write(datastr)
	except KeyboardInterrupt:
		fh.close()
		GPIO.cleanup()
		sys.exit(0)