import sys
import time
import SC16IS750
import pigpio

# I2C bus identifier
I2C_BUS = 1

# Interrupt GPIO pins for WTC and PLP comm chips
PIN_IRQ_WTC = 25 # BCM pin 25, header pin 22
PIN_IRQ_PLP = 11 # BCM pin 11, header pin 23

# I2C addresses for WTC and PLP comm chips
I2C_ADDR_WTC = 0x4C
I2C_ADDR_PLP = 0x4D

# UART baudrates for WTC and PLP comm chips
I2C_BAUD_WTC = 115200
I2C_BAUD_PLP = 115200

# Crystal frequency for comm chips
XTAL_FREQ = 1843200

data = []

INTERRUPTS = {
	SC16IS750.IIR_NONE:       "No Interrupt",
	SC16IS750.IIR_RX_ERROR:   "RX Error",
	SC16IS750.IIR_RX_TIMEOUT: "RX Timeout",
	SC16IS750.IIR_RX_READY:   "RX Ready",
	SC16IS750.IIR_TX_READY:   "TX Ready",
	SC16IS750.IIR_MODEM:      "Modem State Change",
	SC16IS750.IIR_IO:         "IO Pins State Change",
	SC16IS750.IIR_XOFF:       "Xoff Character Received",
	SC16IS750.IIR_CTS_RTS:    "CTS or RTS State Change"
}

def handle_comm(gpio, level, tick):

	#if   gpio == PIN_IRQ_WTC: board = "WTC"
	#elif gpio == PIN_IRQ_PLP: board = "PLP"
	#else:                     board = "UNK"

	irqstatus = chip.get_interrupt_status()
	sys.stdout.write("0x%02X: %s" % (irqstatus, INTERRUPTS.get(irqstatus, "Unknown Interrupt")))

	if   irqstatus == SC16IS750.IIR_RX_ERROR:
		lsr = chip.byte_read(SC16IS750.REG_LSR)
		if lsr & SC16IS750.LSR_OVERFLOW_ERROR:  sys.stdout.write(" (Overflow)")
		if lsr & SC16IS750.LSR_FIFO_DATA_ERROR: sys.stdout.write(" (FIFO Error)")
	elif irqstatus == SC16IS750.IIR_NONE:
		print()
		return

	num = chip.byte_read(SC16IS750.REG_RXLVL)
	sys.stdout.write(" %d" % num)
	block = chip.block_read(SC16IS750.REG_RHR, num)
	data.append([tick, block])
	print()

# Initialize pigpio
pi = pigpio.pi()

# Set up IRQ pins as inputs
pi.set_mode(PIN_IRQ_WTC, pigpio.INPUT)
pi.set_mode(PIN_IRQ_PLP, pigpio.INPUT)

# Initialize SC16IS750 chip
chip = SC16IS750.SC16IS750(pi, I2C_ADDR_WTC, I2C_BUS, I2C_BAUD_WTC, XTAL_FREQ)

# Reset chip and handle exception thrown by NACK
try: chip.byte_write_verify(SC16IS750.REG_IOCONTROL, 0x01 << 3)
#except OSError: print("REG_IOCONTROL: %s 0x00" % (chip.byte_read(SC16IS750.REG_IOCONTROL) == 0x00))
except pigpio.error as e:
	if e.value == pigpio.error_text(pigpio.PI_I2C_WRITE_FAILED):
		print("REG_IOCONTROL: %s 0x00" % (chip.byte_read(SC16IS750.REG_IOCONTROL) == 0x00))
	else:
		print("Error: %s" % e)
		sys.exit(1)

# Write some test patterns to the scratchpad and verify receipt
print("REG_SPR:       %s 0x%02X" % chip.byte_write_verify(SC16IS750.REG_SPR, 0xFF))
print("REG_SPR:       %s 0x%02X" % chip.byte_write_verify(SC16IS750.REG_SPR, 0xAA))
print("REG_SPR:       %s 0x%02X" % chip.byte_write_verify(SC16IS750.REG_SPR, 0x00))

# Define UART with 8 databits, 1 stopbit, and no parity
chip.write_LCR(SC16IS750.DATABITS_8, SC16IS750.STOPBITS_1, SC16IS750.PARITY_NONE)

# Toggle divisor latch bit in LCR register and set appropriate DLH and DLL register values
print("REG_LCR:       %s 0x%02X" % chip.define_register_set(special = True))
print("REG_DLH/DLL:   %s 0x%04X" % chip.set_divisor_latch())
print("REG_LCR:       %s 0x%02X" % chip.define_register_set(special = False))

# Enable interrupts
chip.byte_write(SC16IS750.REG_IER, SC16IS750.IER_RX_ERROR | SC16IS750.IER_RX_READY)

# Reset TX and RX FIFOs and disable FIFOs
chip.byte_write(SC16IS750.REG_FCR, 0x06)
time.sleep(2.0/XTAL_FREQ)

# Define callbacks to handle RX from WTC and PLP comm chips
cb1 = pi.callback(PIN_IRQ_WTC, pigpio.FALLING_EDGE, handle_comm)
#cb2 = pi.callback(PIN_IRQ_PLP, pigpio.FALLING_EDGE, handle_comm)

# Enable FIFOs
chip.byte_write(SC16IS750.REG_FCR, 0x01)
time.sleep(2.0/XTAL_FREQ)

# Send alphabet and then newline and carriage return
#for i in range(0x41, 0x5B):
#	chip.byte_write(SC16IS750.REG_THR, i)
#chip.byte_write(SC16IS750.REG_THR, 0x0A)
#chip.byte_write(SC16IS750.REG_THR, 0x0D)

print("Waiting for data. Hit Ctrl+C to abort.")

# Send MSB=1 to enable emulator, wait, then disable with MSB=0
chip.byte_write(SC16IS750.REG_THR, 0x80)
time.sleep(0.03)
chip.byte_write(SC16IS750.REG_THR, 0x00)

while True:
	try:
		print("Bytes available: %d" % chip.byte_read(SC16IS750.REG_RXLVL))
		while len(data) > 0:
			tick, block = data.pop(0)
			sys.stdout.write("%d (%d bytes):" % (tick, len(block)))
			for char in block:
				sys.stdout.write(" 0x%02X" % char)
			print()
		time.sleep(1)
	except KeyboardInterrupt:
		chip.close()
		pi.stop()
		break
