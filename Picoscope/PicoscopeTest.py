import picoscope.ps2000a as psdrv
import picoscope.picostatus as st

ps = psdrv.Device()
status = ps.open_unit()
print("Device status is %s." % (st.pico_tag(status)))

if status == st.pico_num("PICO_OK"):
	print("Device connected: %s %s" % (ps.info.variant_info, ps.info.batch_and_serial))
	print("Driver: %s" % ps.info.driver_version)
	print("Firmware: %s/%s" % (ps.info.firmware_version_1, ps.info.firmware_version_2))

ps.close_unit()

# POWER MEASUREMENTS FOR 2408B:
# Device connect:    0.035A   175mW
# Device opened:     0.522A  2610mW
# Device closed:     0.074A   370mW
# Device reconnect:  0.035A   175mW
