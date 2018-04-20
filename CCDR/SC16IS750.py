import sys
import time
import smbus

# General Registers (Require LCR[7] = 0)
REG_RHR       = 0x00 # Receive Holding Register (R)
REG_THR       = 0x00 # Transmit Holding Register (W)
REG_IER       = 0x01 # Interrupt Enable Register (R/W)
REG_IIR       = 0x02 # Interrupt Identification Register (R)
REG_FCR       = 0x02 # FIFO Control Register (W)
REG_LCR       = 0x03 # Line Control Register (R/W)
REG_MCR       = 0x04 # Modem Control Register (R/W
REG_LSR       = 0x05 # Line Status Register (R)
REG_MSR       = 0x06 # Modem Status Register (R)
REG_SPR       = 0x07 # Scratchpad Register (R/W)
REG_TCR       = 0x06 # Transmission Control Register (R/W)
REG_TLR       = 0x07 # Trigger Level Register (R/W)
REG_TXLVL     = 0x08 # Transmit FIFO Level Register (R)
REG_RXLVL     = 0x09 # Receive FIFO Level Register (R)
REG_IODIR     = 0x0A # I/O Pin Direction Register (R/W)
REG_IOSTATE   = 0x0B # I/O Pin State Register (R)
REG_IOINTENA  = 0x0C # I/O Interrupt Enable Register (R/W)
REG_IOCONTROL = 0x0E # I/O Pin Control Register (R/W)
REG_EFCR      = 0x0F # Extra Features Register (R/W)

# Special Registers (Require LCR[7] = 1 and LCR != 0xBF)
REG_DLL       = 0x00 # Divisor Latch LSB Register (R/W)
REG_DLH       = 0x01 # Divisor Latch MSB Register (R/W)

# Enhanced Registers (Require LCR[7] = 1 and LCR = 0xBF)
REG_EFR       = 0x02 # Enhanced Feature Register (R/W)
REG_XON1      = 0x04 # XON1 Word Register (R/W)
REG_XON2      = 0x05 # XON2 Word Register (R/W)
REG_XOFF1     = 0x06 # XOFF1 Word Register (R/W)
REG_XOFF2     = 0x07 # XOFF2 Word Register (R/W)

# UART Port Data Bit Settings Enumeration
DATABITS_5    = 0x05
DATABITS_6    = 0x06
DATABITS_7    = 0x07
DATABITS_8    = 0x08

# UART Port Stop Bit Settings Enumeration
STOPBITS_1    = 0x01
STOPBITS_2    = 0x02

# UART Port Parity Settings Enumeration
PARITY_NONE   = 0x00
PARITY_ODD    = 0x01
PARITY_EVEN   = 0x02

# IER Register Interrupt Enable Enumeration
IER_RX_READY = 0x01
IER_TX_READY = 0x02
IER_RX_ERROR = 0x04
IER_MODEM    = 0x08
IER_SLEEP    = 0x10
IER_XOFF     = 0x20
IER_RTS      = 0x40
IER_CTS      = 0x80

# IIR Register Interrupt Status Enumeration
IIR_NONE       = 0x01 # Priority X
IIR_RX_ERROR   = 0x06 # Priority 1
IIR_RX_TIMEOUT = 0x0C # Priority 2
IIR_RX_READY   = 0x04 # Priority 2
IIR_TX_READY   = 0x02 # Priority 3
IIR_MODEM      = 0x00 # Priority 4
IIR_IO         = 0x30 # Priority 5
IIR_XOFF       = 0x10 # Priority 6
IIR_CTS_RTS    = 0x20 # Priority 7

# LSR Register Bits Enumeration
LSR_RX_DATA_AVAIL   = 0x01
LSR_OVERFLOW_ERROR  = 0x02
LSR_PARITY_ERROR    = 0x04
LSR_FRAMING_ERROR   = 0x08
LSR_BREAK_INTERRUPT = 0x10
LSR_THR_EMPTY       = 0x20
LSR_THR_TSR_EMPTY   = 0x40
LSR_FIFO_DATA_ERROR = 0x80

# LSR_FIFO_DATA_ERROR is valid for all data in FIFO
# LSR_BREAK_INTERRUPT, LSR_FRAMING_ERROR, and LSR_PARITY_ERROR are valid only for top byte in FIFO
# To check error for all RX bytes, must read LSR then read RHR and repeat for all data
REG_LSR_BITS = {
	LSR_RX_DATA_AVAIL:   "Data In Receiver",  LSR_OVERFLOW_ERROR:  "Overflow Error",
	LSR_PARITY_ERROR:    "Parity Error",      LSR_FRAMING_ERROR:   "Framing Error",
	LSR_BREAK_INTERRUPT: "Break Interrupt",   LSR_THR_EMPTY:       "THR Empty",
	LSR_THR_TSR_EMPTY:   "THR and TSR Empty", LSR_FIFO_DATA_ERROR: "FIFO Data Error"
}

# MSR Register Bits Enumeration
MSR_DELTA_CTS = 0x01
MSR_DELTA_DSR = 0x02
MSR_DELTA_RI  = 0x04
MSR_DELTA_CD  = 0x08
MSR_CTS       = 0x10
MSR_DSR       = 0x20
MSR_RI        = 0x40
MSR_CD        = 0x80

REG_MSR_BITS = {
	MSR_DELTA_CTS: "Delta CTS", MSR_DELTA_DSR: "Delta DSR",
	MSR_DELTA_RI:  "Delta RI",  MSR_DELTA_CD:  "Delta CD",
	MSR_CTS:       "CTS",       MSR_DSR:       "DSR",
	MSR_RI:        "RI",        MSR_CD:        "CD"
}

class SC16IS750:

	def __init__(self, addr = 0x48, bus = 1, baudrate = 115200, freq = 1843200):
		self.bus = smbus.SMBus(bus)
		self.addr = addr
		self.baudrate = baudrate
		self.freq = freq
		self.delay = 0

	def print_register(self, reg, prefix):
		print("%s 0x%02X" % (prefix, self.byte_read(reg)))

	def print_registers(self):
		self.print_register(REG_RHR,       "0x00 REG_RHR:      ")
		self.print_register(REG_IER,       "0x01 REG_IER:      ")
		self.print_register(REG_IIR,       "0x02 REG_IIR:      ")
		self.print_register(REG_LCR,       "0x03 REG_LCR:      ")
		self.print_register(REG_MCR,       "0x04 REG_MCR:      ")
		self.print_register(REG_LSR,       "0x05 REG_LSR:      ")
		self.print_register(REG_MSR,       "0x06 REG_MSR:      ")
		self.print_register(REG_SPR,       "0x07 REG_SPR:      ")
		self.print_register(REG_TXLVL,     "0x08 REG_TXLVL:    ")
		self.print_register(REG_RXLVL,     "0x09 REG_RXLVL:    ")
		self.print_register(REG_IODIR,     "0x0A REG_IODIR:    ")
		self.print_register(REG_IOSTATE,   "0x0B REG_IOSTATE:  ")
		self.print_register(REG_IOINTENA,  "0x0C REG_IOINTENA: ")
		self.print_register(REG_IOCONTROL, "0x0E REG_IOCONTROL:")
		self.print_register(REG_EFCR,      "0x0F REG_EFCR:     ")

	def print_LSR(self):
		byte = self.byte_read(REG_LSR)
		sys.stdout.write("REG_LSR: 0x%02X" % byte)
		for bitmask, desc in sorted(REG_LSR_BITS.items()):
			if byte & bitmask: sys.stdout.write(", %s" % desc)
		print()

	def print_MSR(self):
		byte = self.byte_read(REG_MSR)
		sys.stdout.write("REG_MSR: 0x%02X" % byte)
		for bitmask, desc in sorted(REG_MSR_BITS.items()):
			if byte & bitmask: sys.stdout.write(", %s" % desc)
		print()

	def write_LCR(self, databits, stopbits, parity):
		lcr = 0x00

		# LCR[1:0]
		if   databits == DATABITS_5: lcr |= 0x00
		elif databits == DATABITS_6: lcr |= 0x01
		elif databits == DATABITS_7: lcr |= 0x02
		elif databits == DATABITS_8: lcr |= 0x03
		else: return False

		# LCR[2]
		if   stopbits == STOPBITS_1: lcr |= 0x00
		elif stopbits == STOPBITS_2: lcr |= 0x04
		else: return False

		# LCR[5:3]
		if   parity == PARITY_NONE: lcr |= 0x00
		elif parity == PARITY_ODD:  lcr |= 0x08
		elif parity == PARITY_EVEN: lcr |= 0x18
		else: return False

		success, value = self.byte_write_verify(REG_LCR, lcr)
		print("REG_LCR:       %s 0x%02X" % (success, value))
		return success

	# Compute required divider values for DLH and DLL registers
	# Return tuple indicating (boolean success, new values in registers)
	def set_divisor_latch(self, prescaler = 1):
		if prescaler not in [1, 4]: prescaler = 1
		div = round(self.freq/(prescaler*self.baudrate*16))
		dlh, dll = divmod(div, 0x100)
		dlhb, dlhv = self.byte_write_verify(REG_DLH, dlh)
		dllb, dllv = self.byte_write_verify(REG_DLL, dll)
		return (dlhb and dllb, (dlhv<<8)|dllv)

	# Write I2C byte to specified register and read it back
	# Return tuple indicating (boolean success, new value in register)
	def byte_write_verify(self, reg, byte):
		self.byte_write(reg, byte)
		value = self.byte_read(reg)
		return (value == byte, value)

	# Retreive interrupt status (IIR[5:0])
	def get_interrupt_status(self):
		# Read IIR register and zero out two MSBs
		return self.byte_read(REG_IIR) & 0x3F

	# Change single bit inside register
	def enable_register_bit(self, reg, bit, enable):
		if bit < 0 or bit > 7: return False
		if enable not in [True, False]: return False
		
		oldvalue = self.byte_read(reg)
		if enable: newvalue = oldvalue |  (0x01 << bit)
		else:      newvalue = oldvalue & ~(0x01 << bit)
		return self.byte_write_verify(REG_LCR, newvalue)

	# MCR[4]: True for local loopback enable, False for disable
	def enable_local_loopback(self, enable):
		return self.enable_register_bit(REG_MCR, 4, enable)

	# LCR[7]: True for special register set, False for general register set
	def define_register_set(self, special):
		return self.enable_register_bit(REG_LCR, 7, special)

	# Write I2C byte to specified register and wait for value to be written
	def byte_write(self, reg, byte):
		self.bus.write_byte_data(self.addr, self.reg_conv(reg), byte)
		time.sleep(self.delay)

	# Read I2C byte from specified register
	# Return byte received from SMBus
	def byte_read(self, reg):
		return self.bus.read_byte_data(self.addr, self.reg_conv(reg))

	# Read I2C block from specified register
	# FIFO is 64 bytes, but SMBus can only read 32 bytes at a time
	# Return block received from SMBus
	def block_read(self, reg, num):
		block = []
		while num > 32:
			block.extend(self.bus.read_i2c_block_data(self.addr, self.reg_conv(reg), 32))
			num -= 32
		block.extend(self.bus.read_i2c_block_data(self.addr, self.reg_conv(reg), num))
		return block

	# Convert register address given in datasheet to actual address on chip
	def reg_conv(self, reg):
		return reg << 3
