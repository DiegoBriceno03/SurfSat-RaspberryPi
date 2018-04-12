import sys
import time
import SC16IS750

DEVICE_BUS = 1
DEVICE_ADDR = 0x48
DEVICE_BAUD = 9600
XTAL_FREQ = 1843200

chip = SC16IS750.SC16IS750(DEVICE_ADDR, DEVICE_BUS, DEVICE_BAUD, XTAL_FREQ)

# Reset chip and handle exception thrown by NACK
try: chip.byte_write_verify(SC16IS750.REG_IOCONTROL, 0x01 << 3)
except OSError: print("REG_IOCONTROL: %s 0x00" % (chip.byte_read(SC16IS750.REG_IOCONTROL) == 0x00))

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

# Enable local loopback internally
#print("REG_MCR:       %s 0x%02X" % chip.enable_local_loopback(True))

# Enable RHR register interrupt
#chip.byte_write(SC16IS750.REG_IER, 0x01)

# Reset TX and RX FIFOs and disable FIFOs
chip.byte_write(SC16IS750.REG_FCR, 0x06)
time.sleep(2.0/XTAL_FREQ)

# Enable FIFOs
#chip.byte_write(SC16IS750.REG_FCR, 0x01)
#time.sleep(2.0/XTAL_FREQ)

#chip.print_IIR()
#chip.print_LSR()
#chip.print_MSR()

# Send alphabet and then newline and carriage return
delay = 1e-3
for i in range(0x41, 0x5B):
	chip.byte_write(SC16IS750.REG_THR, i)
	time.sleep(delay)
chip.byte_write(SC16IS750.REG_THR, 0x0A)
time.sleep(delay)
chip.byte_write(SC16IS750.REG_THR, 0x0D)
time.sleep(delay)

print()
print("Current status of registers:")
chip.print_registers()
print()

oldrxlvl = 0xFF
print("Waiting for data. Hit Ctrl+C to abort.")
while True:
	try: 
		status = chip.byte_read(SC16IS750.REG_LSR)
		newrxlvl = chip.byte_read(SC16IS750.REG_RXLVL)

		if newrxlvl != oldrxlvl:
			print("RXLVL: 0x%02X" % newrxlvl)
			oldrxlvl = newrxlvl

		# If LSB of LSR is high, then data available in RHR:
		if status & 0x01 == 1:
			char = chip.byte_read(SC16IS750.REG_RHR)
			print("0x%02X received!" % char)
		# If MSB of LSR is high, then FIFO data error detected:
		elif status & 0x80 == 1:
			print("FIFO data error detected!")

		time.sleep(0.001)
	except KeyboardInterrupt:
		break
