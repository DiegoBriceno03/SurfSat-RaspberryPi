import pigpio

pi = pigpio.pi()
pi.set_mode(23, pigpio.OUTPUT)
pi.set_mode(27, pigpio.OUTPUT)
pi.write(23, 1)
pi.write(27, 1)
pi.stop()
