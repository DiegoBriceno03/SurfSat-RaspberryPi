import sys
import time
import pigpio

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

# Section 8.1: Receive Holding Register (RHR)
# RHR is position zero of the 64 byte RX FIFO

# Section 8.2: Transmit Holding Register (THR)
# THR is position zero of the 64 byte TX FIFO

# Section 8.3: FIFO Control Register (FCR)
# TX trigger level may only be modified if EFR[4] is set
# TX and RX FIFO resets require two XTAL1 clocks
FCR_RX_TRIGGER_08_BYTES = 0x00 << 6
FCR_RX_TRIGGER_16_BYTES = 0x01 << 6
FCR_RX_TRIGGER_56_BYTES = 0x02 << 6
FCR_RX_TRIGGER_60_BYTES = 0x03 << 6
FCR_TX_TRIGGER_08_BYTES = 0x00 << 4
FCR_TX_TRIGGER_16_BYTES = 0x01 << 4
FCR_TX_TRIGGER_32_BYTES = 0x02 << 4
FCR_TX_TRIGGER_56_BYTES = 0x03 << 4
FCR_TX_FIFO_RESET       = 0x01 << 2
FCR_RX_FIFO_RESET       = 0x01 << 1
FCR_FIFO_ENABLE         = 0x01 << 0

# Section 8.4: Line Control Register (LCR)
LCR_DIVISOR_ENABLE = 0x01 << 7
LCR_BREAK_CONTROL  = 0x01 << 6
LCR_PARITY_NONE    = 0x00 << 3
LCR_PARITY_ODD     = 0x01 << 3
LCR_PARITY_EVEN    = 0x03 << 3
LCR_PARITY_HIGH    = 0x05 << 3
LCR_PARITY_LOW     = 0x07 << 3
LCR_STOPBITS_1     = 0x00 << 2
LCR_STOPBITS_2     = 0x01 << 2
LCR_DATABITS_5     = 0x00 << 0
LCR_DATABITS_6     = 0x01 << 0
LCR_DATABITS_7     = 0x02 << 0
LCR_DATABITS_8     = 0x03 << 0

# Section 8.5: Line Status Register (LSR)
LSR_RX_DATA_AVAIL   = 0x01 << 0
LSR_OVERFLOW_ERROR  = 0x01 << 1
LSR_PARITY_ERROR    = 0x01 << 2
LSR_FRAMING_ERROR   = 0x01 << 3
LSR_BREAK_INTERRUPT = 0x01 << 4
LSR_THR_EMPTY       = 0x01 << 5
LSR_THR_TSR_EMPTY   = 0x01 << 6
LSR_FIFO_DATA_ERROR = 0x01 << 7

# LSR_FIFO_DATA_ERROR is valid for all data in FIFO
# LSR_BREAK_INTERRUPT, LSR_FRAMING_ERROR, and LSR_PARITY_ERROR are valid only for top byte in FIFO
# To check error for all RX bytes, must read LSR then read RHR and repeat for all data
REG_LSR_BITS = {
	LSR_RX_DATA_AVAIL:   "Data In Receiver",  LSR_OVERFLOW_ERROR:  "Overflow Error",
	LSR_PARITY_ERROR:    "Parity Error",      LSR_FRAMING_ERROR:   "Framing Error",
	LSR_BREAK_INTERRUPT: "Break Interrupt",   LSR_THR_EMPTY:       "THR Empty",
	LSR_THR_TSR_EMPTY:   "THR and TSR Empty", LSR_FIFO_DATA_ERROR: "FIFO Data Error"
}

# Section 8.6: Modem Control Register (MCR)
# MCR[7:5] and MCR[2] can only be modified if EFR[4] is set
MCR_CLOCK_DIV_1 = 0x00 << 7
MCR_CLOCK_DIV_4 = 0x01 << 7
MCR_IRDA        = 0x01 << 6
MCR_XON_ANY     = 0x01 << 5
MCR_LOOPBACK    = 0x01 << 4
MCR_TCR_TLR     = 0x01 << 2
MCR_RTS         = 0x01 << 1
MCR_DTR         = 0x01 << 0 # Not available on 740 variant

# Section 8.7: Modem Status Register (MSR)
MSR_CD        = 0x01 << 7 # Not available on 740 variant
MSR_RI        = 0x01 << 6 # Not available on 740 variant
MSR_DSR       = 0x01 << 5 # Not available on 740 variant
MSR_CTS       = 0x01 << 4
MSR_DELTA_CD  = 0x01 << 3 # Not available on 740 variant
MSR_DELTA_RI  = 0x01 << 2 # Not available on 740 variant
MSR_DELTA_DSR = 0x01 << 1 # Not available on 740 variant
MSR_DELTA_CTS = 0x01 << 0

REG_MSR_BITS = {
	MSR_DELTA_CTS: "Delta CTS", MSR_DELTA_DSR: "Delta DSR",
	MSR_DELTA_RI:  "Delta RI",  MSR_DELTA_CD:  "Delta CD",
	MSR_CTS:       "CTS",       MSR_DSR:       "DSR",
	MSR_RI:        "RI",        MSR_CD:        "CD"
}

# Section 8.8: Scratch Pad Register (SPR)

# Section 8.9: Interrupt Enable Register (IIR)
# IER[7:4] can only be modified if EFR[4] is set
IER_CTS      = 0x01 << 7
IER_RTS      = 0x01 << 6
IER_XOFF     = 0x01 << 5
IER_SLEEP    = 0x01 << 4
IER_MODEM    = 0x01 << 3 # Not available on 740 variant
IER_RX_ERROR = 0x01 << 2
IER_TX_READY = 0x01 << 1
IER_RX_READY = 0x01 << 0

# Section 8.10: Interrupt Identification Register (IIR)
# Modem interrupt status must be read via MSR register
# GPIO interrupt status must be read via IOState register
IIR_FIFO_ENABLE = 0x80 # Mirrors FCR[0]
IIR_NONE        = 0x01 # Priority X
IIR_RX_ERROR    = 0x06 # Priority 1
IIR_RX_TIMEOUT  = 0x0C # Priority 2
IIR_RX_READY    = 0x04 # Priority 2
IIR_TX_READY    = 0x02 # Priority 3
IIR_MODEM       = 0x00 # Priority 4 # Not available on 740 variant
IIR_GPIO        = 0x30 # Priority 5 # Not available on 740 variant
IIR_XOFF        = 0x10 # Priority 6
IIR_CTS_RTS     = 0x20 # Priority 7

class SC16IS750:

	def __init__(self, pi, addr = 0x48, bus = 1, baudrate = 115200, freq = 1843200):
		self.pi = pi
		self.i2c = pi.i2c_open(bus, addr)
		self.addr = addr
		self.baudrate = baudrate
		self.freq = freq
		self.delay = 0

	def close(self):
		self.pi.i2c_close(self.i2c)

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
		self.pi.i2c_write_byte_data(self.i2c, self.reg_conv(reg), byte)
		time.sleep(self.delay)

	# Read I2C byte from specified register
	# Return byte received from SMBus
	def byte_read(self, reg):
		return self.pi.i2c_read_byte_data(self.i2c, self.reg_conv(reg))

	# Read I2C block from specified register
	# FIFO is 64 bytes, but SMBus can only read 32 bytes at a time
	# Return block received from SMBus
	def block_read(self, reg, num):
		block = []
		while num > 32:
			n, d = self.pi.i2c_read_i2c_block_data(self.i2c, self.reg_conv(reg), 32)
			block.extend(d)
			num -= n
		n, d = self.pi.i2c_read_i2c_block_data(self.i2c, self.reg_conv(reg), num)
		block.extend(d)
		num -= n
		if num != 0: print("ERROR")
		return block

	# Convert register address given in datasheet to actual address on chip
	def reg_conv(self, reg):
		return reg << 3
