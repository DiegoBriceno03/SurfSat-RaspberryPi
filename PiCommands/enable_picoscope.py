import pigpio

pi = pigpio.pi()
pi.set_mode(17, pigpio.OUTPUT)
pi.write(17, 1)
pi.stop()
