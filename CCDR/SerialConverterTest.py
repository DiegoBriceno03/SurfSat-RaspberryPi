import sys
import time
import SC16IS750
import pigpio

# I2C bus identifier
I2C_BUS = 1

# Interrupt GPIO pins for communications chips
PIN_IRQ_WTC = 25 # BCM pin 25, header pin 22
PIN_IRQ_PLP = 11 # BCM pin 11, header pin 23

# I2C addresses for communications chips
I2C_ADDR_WTC = 0x4C
I2C_ADDR_PLP = 0x4D

# Crystal frequencies for communications chips
XTAL_FREQ_WTC = 1843200
XTAL_FREQ_PLP = 1843200
 
# UART baudrates for communications chips
UART_BAUD_WTC = 115200
UART_BAUD_PLP = 115200

# UART databits for communications chips
UART_DATA_WTC = SC16IS750.LCR_DATABITS_8
UART_DATA_PLP = SC16IS750.LCR_DATABITS_8

# UART stopbits for communications chips
UART_STOP_WTC = SC16IS750.LCR_STOPBITS_1
UART_STOP_PLP = SC16IS750.LCR_STOPBITS_1

# UART parities for communications chips
UART_PARITY_WTC = SC16IS750.LCR_PARITY_NONE
UART_PARITY_PLP = SC16IS750.LCR_PARITY_NONE

# Create buffer to store RX data
data = {"WTC": [], "PLP": [], "UNK": []}

# Define lookup table for interrupts
INTERRUPTS = {
	SC16IS750.IIR_NONE:       "No Interrupt",
	SC16IS750.IIR_RX_ERROR:   "RX Error",
	SC16IS750.IIR_RX_TIMEOUT: "RX Timeout",
	SC16IS750.IIR_RX_READY:   "RX Ready",
	SC16IS750.IIR_TX_READY:   "TX Ready",
	SC16IS750.IIR_MODEM:      "Modem State Change",
	SC16IS750.IIR_GPIO:       "IO Pins State Change",
	SC16IS750.IIR_XOFF:       "Xoff Character Received",
	SC16IS750.IIR_CTS_RTS:    "CTS or RTS State Change"
}

# Define common interrupt service routine
def handle_comm(gpio, level, tick):

	# Determine which chip generated the interrupt
	if   gpio == PIN_IRQ_WTC: board = "WTC"
	elif gpio == PIN_IRQ_PLP: board = "PLP"
	else:                     board = "UNK"

	# Determine which interrupt was triggered
	irq = chip_wtc.get_interrupt_status()

	lsr = None
	# Handle error states and false triggers first
	if irq == SC16IS750.IIR_RX_ERROR:
		lsr = chip_wtc.byte_read(SC16IS750.REG_LSR)
		if lsr & SC16IS750.LSR_OVERFLOW_ERROR:  pass
		if lsr & SC16IS750.LSR_FIFO_DATA_ERROR: pass
	elif irq == SC16IS750.IIR_NONE:
		return

	# Determine number of bytes in RX FIFO, read multiple of four bytes, and store
	avail = chip_wtc.byte_read(SC16IS750.REG_RXLVL)
	num = int(avail/4)*4
	block = chip_wtc.block_read(SC16IS750.REG_RHR, num)
	data[board].append([tick, irq, lsr, avail, block])

# Initialize pigpio
pi = pigpio.pi()

# Set up IRQ pins as inputs
pi.set_mode(PIN_IRQ_WTC, pigpio.INPUT)
pi.set_mode(PIN_IRQ_PLP, pigpio.INPUT)

# Initialize SC16IS750 chip
chip_wtc = SC16IS750.SC16IS750(pi, I2C_BUS, I2C_ADDR_WTC, XTAL_FREQ_WTC, UART_BAUD_WTC, UART_DATA_WTC, UART_STOP_WTC, UART_PARITY_WTC)

# Reset TX and RX FIFOs and disable FIFOs
fcr = SC16IS750.FCR_TX_FIFO_RESET | SC16IS750.FCR_RX_FIFO_RESET
chip_wtc.byte_write(SC16IS750.REG_FCR, fcr)
time.sleep(2.0/XTAL_FREQ_WTC)

# Define callbacks to handle RX from WTC and PLP comm chip
cb_wtc = pi.callback(PIN_IRQ_WTC, pigpio.FALLING_EDGE, handle_comm)
cb_plp = pi.callback(PIN_IRQ_PLP, pigpio.FALLING_EDGE, handle_comm)

# Enable RX error and RX ready interrupts
ier = SC16IS750.IER_RX_ERROR | SC16IS750.IER_RX_READY
chip_wtc.byte_write_verify(SC16IS750.REG_IER, ier)

# Enable FIFOs and set RX trigger level to 8 bytes
fcr = SC16IS750.FCR_FIFO_ENABLE | SC16IS750.FCR_RX_TRIGGER_08_BYTES
chip_wtc.byte_write(SC16IS750.REG_FCR, fcr)

print("Waiting for data. Hit Ctrl+C to abort.")

# Enable emulator by sending byte with MSB set
chip_wtc.byte_write(SC16IS750.REG_THR, 0x80)

while True:
	try:
		# Dump RX data from buffer to screen when available
		for board, values in data.items():
			while len(values) > 0:
				tick, irq, lsr, num, block = values.pop(0)
				sys.stdout.write("(Board: %s) (Tick: %d) (IRQ: 0x%02X %s)" % (board, tick, irq, INTERRUPTS.get(irq)))
				if lsr is not None: sys.stdout.write(" (LSR: 0x%02X)" % lsr)
				sys.stdout.write(" (Bytes: %02d/%02d):" % (len(block), num))
				for char in block:
					sys.stdout.write(" 0x%02X" % char)
				print()

				if lsr is not None:
					if lsr & SC16IS750.LSR_OVERFLOW_ERROR:
						raise ValueError("Fatal overflow error encountered.")
					if lsr & SC16IS750.LSR_FIFO_DATA_ERROR:
						raise ValueError("Fatal FIFO data error encountered.")
		time.sleep(0.1)
	except KeyboardInterrupt:
		# Disable emulator by sending byte with MSB unset
		chip_wtc.byte_write(SC16IS750.REG_THR, 0x00)
		chip_wtc.close()
		pi.stop()
		break
