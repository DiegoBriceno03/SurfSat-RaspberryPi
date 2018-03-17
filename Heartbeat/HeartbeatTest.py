# Be sure to have pigpiod running as root to handle requests!

import pigpio

HEARTBEAT_PIN = 18
HEARTBEAT_FREQ = 1000
HEARTBEAT_DUTY = 50

pi = pigpio.pi()
pi.set_mode(HEARTBEAT_PIN, pigpio.OUTPUT)
pi.hardware_PWM(HEARTBEAT_PIN, HEARTBEAT_FREQ, HEARTBEAT_DUTY*10000)

while True:
	try: pass
	except KeyboardInterrupt: break

pi.stop()
