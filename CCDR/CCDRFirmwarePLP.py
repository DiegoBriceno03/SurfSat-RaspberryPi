import sys
import time
import SC16IS750
import pigpio

filename = 'data.txt'

# I2C bus identifier
I2C_BUS = 1

# ENABLE and RESET GPIO pins for PLP board
PIN_PLP_RESET  = 23
PIN_PLP_ENABLE = 27

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
#def handle_comm_wtc(gpio, level, tick):

	# Verify correct GPIO caused the interrupt
	#if gpio == PIN_IRQ_WTC: mult = 1
	#else: return

	# Determine interrupt, error, and RX level statuses
	#irq, lsr, lvl = chip_wtc.get_interrupt_status()

	# Return if interrupt was already serviced
	#if irq == SC16IS750.IIR_NONE: return

	# Rapidly read RX FIFO data in byte multiples defined above and store
	#block = chip_wtc.block_read(SC16IS750.REG_RHR, int(lvl/mult)*mult)
	#data["WTC"].append([tick, irq, lsr, lvl, block])

# Define PLP interrupt service routine
def handle_comm_plp(gpio, level, tick):

	# Verify correct GPIO caused the interrupt
	if gpio == PIN_IRQ_PLP: mult = 4
	else: return

	# Handle watchdog interrupts first
	if level == CALLBACK_WATCHDOG:
		print("IRQ timeout, resetting FIFOs ...")
		reset_FIFO()
		return

	# Determine interrupt, error, and RX level statuses
	irq, lsr, lvl = chip_plp.get_interrupt_status()

	# Return if interrupt was already serviced
	#if irq == SC16IS750.IIR_NONE: return

	# If RX overflow error, data is unusable, so resynchronize
	if irq == SC16IS750.IIR_RX_ERROR:
		if lsr & SC16IS750.LSR_OVERFLOW_ERROR:
			reset_FIFO()
			data["PLP"].append([tick, irq, lsr, lvl, []])
			return

	# Rapidly read RX FIFO data in byte multiples defined above and store
	block = chip_plp.block_read(SC16IS750.REG_RHR, int(lvl/mult)*mult)
	data["PLP"].append([tick, irq, lsr, lvl, block])

def reset_FIFO():
	print("[%08X] Resetting FIFO ..." % pigpio.tickDiff(start, pi.get_current_tick()))

	# Reset TX and RX FIFOs
	fcr = SC16IS750.FCR_TX_FIFO_RESET | SC16IS750.FCR_RX_FIFO_RESET
	chip_plp.byte_write(SC16IS750.REG_FCR, fcr)
	time.sleep(2.0/XTAL_FREQ_WTC)

	# Enable FIFOs and set RX FIFO trigger level
	fcr = SC16IS750.FCR_FIFO_ENABLE | SC16IS750.FCR_RX_TRIGGER_56_BYTES
	chip_plp.byte_write(SC16IS750.REG_FCR, fcr)

# Initialize pigpio
pi = pigpio.pi()

# Set up PLP reset and enable signals
pi.set_mode(PIN_PLP_RESET,  pigpio.OUTPUT)
pi.set_mode(PIN_PLP_ENABLE, pigpio.OUTPUT)

pi.write(PIN_PLP_RESET,  1) # active low
pi.write(PIN_PLP_ENABLE, 1) # active high

# Set up IRQ pins as inputs
#pi.set_mode(PIN_IRQ_WTC, pigpio.INPUT)
pi.set_mode(PIN_IRQ_PLP, pigpio.INPUT)

# Initialize SC16IS750 chips
#chip_wtc = SC16IS750.SC16IS750(pi, I2C_BUS, I2C_ADDR_WTC, XTAL_FREQ_WTC, UART_BAUD_WTC, UART_DATA_WTC, UART_STOP_WTC, UART_PARITY_WTC)
chip_plp = SC16IS750.SC16IS750(pi, I2C_BUS, I2C_ADDR_PLP, XTAL_FREQ_PLP, UART_BAUD_PLP, UART_DATA_PLP, UART_STOP_PLP, UART_PARITY_PLP)

# Define callbacks to handle RX from WTC and PLP comm chip
#cb_wtc = pi.callback(PIN_IRQ_WTC, pigpio.FALLING_EDGE, handle_comm_wtc)
cb_plp = pi.callback(PIN_IRQ_PLP, pigpio.FALLING_EDGE, handle_comm_plp)

# Enable RX error and RX ready interrupts
ier = SC16IS750.IER_RX_ERROR | SC16IS750.IER_RX_READY
chip_plp.byte_write_verify(SC16IS750.REG_IER, ier)

start = pi.get_current_tick()
print("[%08X] Waiting for data. Hit Ctrl+C to abort." % pigpio.tickDiff(start, pi.get_current_tick()))

# Clear FIFOs and set watchdog
reset_FIFO()
pi.set_watchdog(PIN_IRQ_PLP, 1000)

# Enable emulator by sending byte with MSB set
chip_plp.byte_write(SC16IS750.REG_THR, 0x80)

# Collect data and store in RAM until KeyboardInterrupt or timeout
while pigpio.tickDiff(start, pi.get_current_tick()) < 0x35A4E900:
	try: time.sleep(0.5)
	except KeyboardInterrupt: break

# Disable watchdog timer and callback for PLP
pi.set_watchdog(PIN_IRQ_PLP, 0)
cb_plp.cancel()

# Disable emulator by sending byte with MSB unset
chip_plp.byte_write(SC16IS750.REG_THR, 0x00)

print("[%08X] Saving data to '%s' ..." % (pigpio.tickDiff(start, pi.get_current_tick()), filename))

# Close handle to serial converter chip and release pigpio object
chip_plp.close()
pi.stop()

# Write collected data from RAM to file
savefile = open(filename, 'w')
for board, values in data.items():
	if board == "PLP":
		while len(values) > 0:
			tick, irq, lsr, num, block = values.pop(0)
			tick = pigpio.tickDiff(start, tick)
			#sys.stdout.write("(Board: %s) (Tick: %d) (IRQ: 0x%02X %-10s) (LSR: 0x%02X) (Bytes: %02d/%02d):" % (board, tick, irq, INTERRUPTS.get(irq), lsr, len(block), num))
			savefile.write("%08X, %02X, %02X, %02X" % (tick, irq, lsr, int(len(block)/4)))
			data = 0
			for i in range(len(block)):
				if i % 4 == 0:
					#sys.stdout.write(" 0x")
					savefile.write(", ")
					data = 0
				data |= (block[i] << (3 - (i % 4)) * 8)
				if i % 4 == 3:
					#sys.stdout.write("%08X" % data)
					savefile.write("%08X" % data)
			#sys.stdout.write("\n")
			savefile.write("\n")

			#if lsr & SC16IS750.LSR_OVERFLOW_ERROR:
			#	raise ValueError("Fatal overflow error encountered.")
			#if lsr & SC16IS750.LSR_FIFO_DATA_ERROR:
			#	raise ValueError("Fatal FIFO data error encountered.")

savefile.close()
