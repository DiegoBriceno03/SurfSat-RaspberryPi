import sys
import time
import smbus
import threading

# Primary ADC with address 0x48, secondary ADC with address 0x49
# Addresses 0x48 (GND), 0x49 (VDD), 0x4A (SDA), 0x4B (SCL)
DEVICE_BUS = 1
addresses = [0x48, 0x49]

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
CONF_COMP_QUE = 0x03 # 0b11

# Store program start time as zero point for measurements:
inittime = time.time()

dataready = False
databuffer = {'time': 0, 'config': [], 'C0': [], 'C1': [], 'C2': [], 'C3': []}

def sample():
	# Initialize countdown to next sample:
	threading.Timer(0.1, sample).start()

	# Declare global storage variables:
	global dataready, databuffer

	# Record current sample time:
	databuffer['time'] = time.time() - inittime

	# Cycle through each of the four ADC input channels in series:
	for channel in range(4):
		# Generate bits to connect multiplexer to correct channel and generate configuration bytes:
		CONF_MUX = (1 << 2) | channel # 0b1XX
		config = [(CONF_OS << 7) | (CONF_MUX << 4) | (CONF_PGA << 1) | CONF_MODE, (CONF_DR << 5) | (CONF_COMP_MODE << 4) | (CONF_COMP_POL << 3) | (CONF_COMP_LAT << 2) | CONF_COMP_QUE]

		# Concatenate both configuration bytes and store value in buffer:
		databuffer['config'].append('0x{0:04X}'.format((config[0] << 8) | config[1]))

		# Alternate between two ADC chips on I2C bus:
		for address in addresses:
			# Write configuration bytes to chip, wait for conversion to take place, and read in conversion bytes:
			bus.write_i2c_block_data(address, REG_CONF, config)

		# Wait for conversion to complete and read in results:
		time.sleep(1/860.0+0.001)
		for address in addresses:
			datatc = bus.read_word_data(address, REG_CONV)

			# Swap order of bytes and convert out of two byte two's complement to integer length two's complement:
			datatc = ((datatc & 0xFF00) >> 8) | ((datatc & 0x00FF) << 8)
			data = -(datatc & 0x8000) | (datatc & 0x7FFF)

			# Store received data bytes and processed ADC values in buffer:
			# At 4.096 V PGA setting, one bin has a value of 125 uV (4.096/0x7FFF), so fourth decimal place is uncertain.
			# Since the ADC saves space for negative values as well, the single ended range is only 15 bits (therefore 0x7FFF bins).
			databuffer['C' + str(channel)].append('(0x{0:02X}): 0x{1:04X} ({2:+.4f} V)'.format(address, datatc, data*4.096/0x7FFF))

	dataready = True

sample()

while True:
	time.sleep(0.01)
	if dataready:
		dataparse = databuffer
		databuffer = {'time': 0, 'addr': [], 'config': [], 'C0': [], 'C1': [], 'C2': [], 'C3': []}
		dataready = False

		sys.stdout.write('Time: {0:.2f} s\n'.format(dataparse['time']))
		for channel in range(4):
			sys.stdout.write('  Channel: ' + str(channel))
			sys.stdout.write(', Config: ' + dataparse['config'][channel])
			for data in dataparse['C' + str(channel)]:
				sys.stdout.write(', Data ' + data)
			sys.stdout.write('\n')
