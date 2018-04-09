import smbus

# General Registers
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

# Special Registers
REG_DLL       = 0x00 # Divisor Latch LSB Register (R/W)
REG_DLH       = 0x01 # Divisor Latch MSB Register (R/W)
REG_EFR       = 0x02 # Enhanced Feature Register (R/W)
REG_XON1      = 0x04 # XON1 Word Register (R/W)
REG_XON2      = 0x05 # XON2 Word Register (R/W)
REG_XOFF1     = 0x06 # XOFF1 Word Register (R/W)
REG_XOFF2     = 0x07 # XOFF2 Word Register (R/W)

class SC16IS750:
	def __init__(self, addr, bus):
		self.bus = smbus.SMBus(bus)
		self.addr = addr
		
		self.byte_write(REG_IOCONTROL, 0x80)

	def scratchpad_test(self, byte):
		self.byte_write(REG_SPR, byte)
		data = self.byte_read(REG_SPR)
		print("%02X" % data)

	def byte_write(self, reg, byte):
		self.bus.write_byte_data(self.addr, self.reg_conv(reg), byte)

	def byte_read(self, reg):
		return self.bus.read_byte_data(self.addr, self.reg_conv(reg))
		
	def reg_conv(self, reg):
		return reg << 3
