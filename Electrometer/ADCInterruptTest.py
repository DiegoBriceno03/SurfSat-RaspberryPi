import os
import sys
import time
import smbus
import pigpio

# Create data directory if it does not exist
if os.path.exists('data'):
	if not os.path.isdir('data'):
		print('Data directory is file and not directory. Please fix!')
		sys.exit(1)
else:
	os.makedirs('data')

pi = pigpio.pi()

CLOCK_PIN = 13
CLOCK_FREQ = 40
CLOCK_DUTY = 50

pi.set_mode(CLOCK_PIN, pigpio.ALT0)
pi.hardware_PWM(CLOCK_PIN, CLOCK_FREQ, CLOCK_DUTY*10000)

cb = None
cb1 = None

# Primary ADC with address 0x48, secondary ADC with address 0x49
# Addresses 0x48 (GND), 0x49 (VDD), 0x4A (SDA), 0x4B (SCL)
DEVICE_BUS = 1
DEVICE_INDEX = 0
DEVICE_ADDRS = [0x48, 0x49]
DEVICE_GPIOS = [24, 10]
DEVICE_ADDR = DEVICE_ADDRS[DEVICE_INDEX]
DEVICE_GPIO = DEVICE_GPIOS[DEVICE_INDEX]

sys.stdout.write('Initializing gpio ...')
pi.set_mode(DEVICE_GPIO, pigpio.INPUT)
pi.set_pull_up_down(DEVICE_GPIO, pigpio.PUD_UP)
print('done!')

sys.stdout.write('Initializing bus ... ')
bus = smbus.SMBus(DEVICE_BUS)
print('done!')

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

channel = 0
databuffer = []
firstrun = True

def init():
	global cb

	# Set Lo_thresh and Hi_thresh registers to enable conversion ready pin
	# Set most significant bit of Lo_thresh register to 0
	bus.write_i2c_block_data(DEVICE_ADDR, REG_LOW, [0x00, 0x00])
	# Set most significant bit of Hi_thresh register to 1
	bus.write_i2c_block_data(DEVICE_ADDR, REG_HIGH, [0x80, 0x00])
	# Initialize hardware sampling clock:
	cb = pi.callback(CLOCK_PIN, pigpio.RISING_EDGE, req_sample)

def req_sample(gpio, level, tick):
	global cb1, channel, databuffer, firstrun

	if pi.read(DEVICE_GPIO) == 1 and not firstrun: return
	elif firstrun: firstrun = False

	# Cycle through each of the four ADC input channels in series:
	# Generate bits to connect multiplexer to correct channel and generate configuration bytes:
	CONF_MUX = (1 << 2) | channel # 0b1XX
	config = [(CONF_OS << 7) | (CONF_MUX << 4) | (CONF_PGA << 1) | CONF_MODE, (CONF_DR << 5) | (CONF_COMP_MODE << 4) | (CONF_COMP_POL << 3) | (CONF_COMP_LAT << 2) | CONF_COMP_QUE]

	# Write configuration bytes to chip, wait for conversion to take place, and read in conversion bytes:
	bus.write_i2c_block_data(DEVICE_ADDR, REG_CONF, config)

	# Set up callback for conversion to complete:
	cb1 = pi.callback(DEVICE_GPIO, pigpio.FALLING_EDGE, read_sample)

def read_sample(gpio, level, tick):
	global cb1, channel, databuffer
	databuffer.append([tick, channel, bus.read_word_data(DEVICE_ADDR, REG_CONV)])
	channel = (channel + 1) % 4
	cb1.cancel()

fh = open('data/' + str(int(time.time())) + '.txt', 'w')

init()
while True:
	try:
		time.sleep(0.01)
		while len(databuffer) > 0:
			reading = databuffer.pop(0)

			# Swap order of bytes and convert out of two byte two's complement to integer length two's complement:
			datatc = reading[2]
			datatc = ((datatc & 0xFF00) >> 8) | ((datatc & 0x00FF) << 8)
			data = -(datatc & 0x8000) | (datatc & 0x7FFF)

			# Write received data bytes and processed ADC values to file and stdout:
			# At 4.096 V PGA setting, one bin has a value of 125 uV (4.096/0x7FFF), so fourth decimal place is uncertain.
			# Since the ADC saves space for negative values as well, the single ended range is only 15 bits (therefore 0x7FFF bins).
			datastr = '{0:d}, {1:d}, 0x{2:04X}, {3:+.4f}\n'.format(reading[0], reading[1], datatc, data*4.096/0x7FFF)
			fh.write(datastr)
			sys.stdout.write(datastr)
	except KeyboardInterrupt:
		fh.close()
		pi.stop()
		break
