import time
import LangmuirProbe as PLP

plp = PLP.LangmuirProbe(pin_reset = 11, pin_enable = 13, pin_status = 16)

plp.send_command_byte(PLP.MODE_SCI | PLP.BIAS_SWEPT | PLP.OPER_PULSED | PLP.SPEED_SLOW)

filename = 'data.txt'
saveFile = open(filename, 'w')
print("Saving data to '%s'..." % filename)

totalruntime = 1
print("Taking data for %d seconds..." % totalruntime)
starttime = time.time()
runtime = 0
while runtime < totalruntime and plp.check_status():
	try:
		runtime = time.time() - starttime
		voltage, current = plp.read_data()
		datastr = "{0:.6f}, {1:x}, {2:x}\n".format(runtime, voltage, current)
		saveFile.write(datastr)
	except KeyboardInterrupt:
		break

saveFile.close()

plp.send_command_byte(PLP.MODE_IDLE)
plp.disable()
plp.close()
