import time
import pigpio
import CCDR

pi = pigpio.pi()

ccdr = CCDR.CCDR(pi)

print("Pulsing heartbeat pin...")
pi.write(CCDR.PI_PIN_HEARTBEAT, 0)
time.sleep(0.5)
pi.write(CCDR.PI_PIN_HEARTBEAT, 1)
time.sleep(0.5)
pi.write(CCDR.PI_PIN_HEARTBEAT, 0)
time.sleep(0.5)
pi.write(CCDR.PI_PIN_HEARTBEAT, 1)
time.sleep(0.5)

print("Enabling/disabling Picoscope...")
ccdr.enable_picoscope(True)
time.sleep(1)
ccdr.enable_picoscope(False)
time.sleep(1)

print("Enabling/disabling electrometer...")
ccdr.enable_electrometer(True)
time.sleep(1)
ccdr.enable_electrometer(False)
time.sleep(1)

print("Resetting/enabling/disabling PLP...")
ccdr.reset_plp()
time.sleep(1)
ccdr.enable_plp(True)
time.sleep(1)
ccdr.enable_plp(False)

pi.stop()
