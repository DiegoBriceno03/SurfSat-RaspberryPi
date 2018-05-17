import sys
import time
import SC16IS750
import pigpio

# I2C bus identifier
I2C_BUS = 1

# Interrupt GPIO pins for communications chips
PIN_IRQ_WTC = 25 # BCM pin 25, header pin 22

# I2C addresses for communications chips
I2C_ADDR_WTC = 0x4C

# Crystal frequencies for communications chips
XTAL_FREQ_WTC = 11059200 # 1843200
 
# UART baudrates for communications chips
UART_BAUD_WTC = 115200

# UART databits for communications chips
UART_DATA_WTC = SC16IS750.LCR_DATABITS_8

# UART stopbits for communications chips
UART_STOP_WTC = SC16IS750.LCR_STOPBITS_1

# UART parities for communications chips
UART_PARITY_WTC = SC16IS750.LCR_PARITY_NONE

# Create buffer to store RX data
data = {"WTC": [], "PLP": []}

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

CALLBACK_FALLING  = 0
CALLBACK_RISING   = 1
CALLBACK_WATCHDOG = 2

# Define WTC interrupt service routine
def handle_comm_wtc(gpio, level, tick):

	# Verify correct GPIO caused the interrupt
	if gpio == PIN_IRQ_WTC: mult = 1
	else: return

	# Determine interrupt, error, and RX level statuses
	irq, lsr, lvl = chip_wtc.get_interrupt_status()

	# Return if interrupt was already serviced
	if irq == SC16IS750.IIR_NONE: return

	# Rapidly read RX FIFO data in byte multiples defined above and store
	block = chip_wtc.block_read(SC16IS750.REG_RHR, int(lvl/mult)*mult)
	data["WTC"].append([tick, irq, lsr, lvl, block])

# Initialize pigpio
pi = pigpio.pi()

# Set up IRQ pins as inputs
pi.set_mode(PIN_IRQ_WTC, pigpio.INPUT)

# Initialize SC16IS750 chips
chip_wtc = SC16IS750.SC16IS750(pi, I2C_BUS, I2C_ADDR_WTC, XTAL_FREQ_WTC, UART_BAUD_WTC, UART_DATA_WTC, UART_STOP_WTC, UART_PARITY_WTC)

# Reset TX and RX FIFOs
fcr = SC16IS750.FCR_TX_FIFO_RESET | SC16IS750.FCR_RX_FIFO_RESET
chip_wtc.byte_write(SC16IS750.REG_FCR, fcr)
time.sleep(2.0/XTAL_FREQ_WTC)

# Enable FIFOs and set RX FIFO trigger level
fcr = SC16IS750.FCR_FIFO_ENABLE | SC16IS750.FCR_RX_TRIGGER_56_BYTES
chip_wtc.byte_write(SC16IS750.REG_FCR, fcr)

# Define callbacks to handle RX from WTC and PLP comm chip
cb_wtc = pi.callback(PIN_IRQ_WTC, pigpio.FALLING_EDGE, handle_comm_wtc)

# Enable RX error and RX ready interrupts
ier = SC16IS750.IER_RX_ERROR | SC16IS750.IER_RX_READY
chip_wtc.byte_write_verify(SC16IS750.REG_IER, ier)

start = pi.get_current_tick()
print("[%08X] Waiting for data. Hit Ctrl+C to abort." % pigpio.tickDiff(start, pi.get_current_tick()))

# Send test block data
chip_wtc.block_write(SC16IS750.REG_THR, b'hello')

# Collect data and store in RAM until KeyboardInterrupt or timeout
while pigpio.tickDiff(start, pi.get_current_tick()) < 0x35A4E900:
	try:
		time.sleep(0.1)
		while len(data["WTC"]) > 0:
			tick, irq, lsr, num, block = values.pop(0)
			tick = pigpio.tickDiff(start, tick)
			sys.stdout.write("(Board: %s) (Tick: %d) (IRQ: 0x%02X %-10s) (LSR: 0x%02X) (Bytes: %02d/%02d):" % (board, tick, irq, INTERRUPTS.get(irq), lsr, len(block), num))
			for i in range(len(block)):
				sys.stdout.write(" 0x%02X" % data)
			sys.stdout.write("\n")
	except KeyboardInterrupt: break

# Disable watchdog timer and callback for PLP
cb_wtc.cancel()

# Close handle to serial converter chip and release pigpio object
chip_wtc.close()
pi.stop()
