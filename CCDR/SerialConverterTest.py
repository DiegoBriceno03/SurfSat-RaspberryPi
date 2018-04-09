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
print("REG_SPR:       %s 0x%02X" % chip.byte_write_verify(SC16IS750.REG_SPR, 0x81))

# Toggle divisor latch bit in LCR register and set appropriate DLH and DLL register values
print("REG_LCR:       %s 0x%02X" % chip.define_register_set(special = True))
print("REG_DLH/DLL:   %s 0x%04X" % chip.set_divisor_latch())
print("REG_LCR:       %s 0x%02X" % chip.define_register_set(special = False))
