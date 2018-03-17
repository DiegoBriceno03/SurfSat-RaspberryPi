# Be sure to have pigpiod running as root to handle requests!

import pigpio
import time

CLOCK_PIN = 13
CLOCK_FREQ = 10
CLOCK_DUTY = 50

pi = pigpio.pi()
pi.set_mode(CLOCK_PIN, pigpio.ALT0)
pi.hardware_PWM(CLOCK_PIN, CLOCK_FREQ, CLOCK_DUTY*10000)

def sample(gpio, level, tick):
	print(gpio, level, tick)

cb = pi.callback(CLOCK_PIN, pigpio.RISING_EDGE, sample)

while True:
	try: time.sleep(1000)
	except KeyboardInterrupt: break

pi.stop()
