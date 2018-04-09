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
REG_IOSTATES  = 0x0B # I/O Pin States Register (R)
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

class SC16IS750:
	def __init__(self, addr = 0x48, bus = 1, baudrate = 9600, freq = 1843200):
		self.bus = smbus.SMBus(bus)
		self.addr = addr
		self.baudrate = baudrate
		self.freq = freq
		# Set delay to 2*Tclk as specified by datasheet (page 22 footnote 4)
		self.delay = 2.0/freq

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

	# Toggle which register set is used
	# If parameter is True, enable special register set, else use general set
	def define_register_set(self, special):
		oldvalue = self.byte_read(REG_LCR)
		if special: newvalue = oldvalue | 0x80
		else:       newvalue = oldvalue & 0x7F
		return self.byte_write_verify(REG_LCR, newvalue)

	# Write I2C byte to specified register and wait for value to be written
	def byte_write(self, reg, byte):
		self.bus.write_byte_data(self.addr, self.reg_conv(reg), byte)
		time.sleep(self.delay)

	# Read I2C byte from specified register
	# Return byte received from SMBus
	def byte_read(self, reg):
		return self.bus.read_byte_data(self.addr, self.reg_conv(reg))

	# Convert register address given in datasheet to actual address on chip
	def reg_conv(self, reg):
		return reg << 3
